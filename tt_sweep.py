#!/usr/bin/env python3

import itertools
import json
import os
import shutil
import subprocess
import time
import re
from datetime import datetime
from pathlib import Path
import csv
import threading

class RunMonitor(threading.Thread):
    """
    A separate thread that monitors the `runs_dir` and prints out any new subdirectories
    in sorted order. If it sees a directory ending with '-detailedrouting', it parses
    openroad-detailedrouting.log for new lines containing 'optimization iteration' or 'Completing'.
    """
    def __init__(self, runs_dir: Path, stop_event: threading.Event, poll_interval: float = 3.0):
        super().__init__()
        self.runs_dir = runs_dir
        self.stop_event = stop_event
        self.poll_interval = poll_interval
        self.known_subdirs = set()
        # Track file offsets so we only read new lines each iteration
        self.log_file_offsets = {}

    def run(self):
        while not self.stop_event.is_set():
            time.sleep(self.poll_interval)
            self.check_subdirectories()

    def check_subdirectories(self):
        if not self.runs_dir.exists():
            return
        
        # Collect and sort subdirectories by name
        all_subdirs = [p for p in self.runs_dir.iterdir() if p.is_dir()]
        all_subdirs_sorted = sorted(all_subdirs, key=lambda x: x.name)
        
        # Create a set of subdir names for comparison
        current_subdir_names = {p.name for p in all_subdirs_sorted}
        new_subdirs = current_subdir_names - self.known_subdirs
        
        # Print any newly discovered subdirectories in sorted order
        for p in all_subdirs_sorted:
            if p.name in new_subdirs:
                print(f"[Monitor] Step: {p.name}")
                
            # If directory ends with '-detailedrouting', tail-read the log file
            if p.name.endswith("-detailedrouting"):
                log_file_path = p / "openroad-detailedrouting.log"
                if log_file_path.exists():
                    # Get last known file offset (default=0 if new)
                    last_offset = self.log_file_offsets.get(log_file_path, 0)
                    current_offset = last_offset
                    
                    # Open the log in binary mode for precise offset
                    with open(log_file_path, 'rb') as logf:
                        # Move to the last known offset
                        logf.seek(last_offset)
                        # Read any newly appended lines
                        for line_bytes in logf:
                            line = line_bytes.decode(errors='replace')
                            current_offset = logf.tell()
                            if ("optimization iteration" in line) or ("Completing" in line):
                                print(f"[Monitor] {line.strip()}")
                    
                    # Store the updated offset
                    self.log_file_offsets[log_file_path] = current_offset

        # Update known subdirs
        self.known_subdirs = current_subdir_names


class ParamSweepRunner:
    """
    Object-Oriented approach to running a parameter sweep for hardware synthesis.
    This version doesn't hardcode CSV columns. Instead, each run accumulates a dictionary
    of summary data (any key/value pairs). Once all runs complete, we write them
    all at once to a CSV, using the union of keys as columns.
    """

    def __init__(
        self,
        parameters: dict,
        default_json_file: Path,
        out_json_file: Path,
        synthesis_cmd: list,
        runs_dir: Path = Path("runs"),
        archive_dir: Path = Path("archive"),
        summary_csv_path: Path = Path("summary.csv"),
        max_time: int = 3600  # seconds
    ):
        """
        :param parameters: Dictionary of param_name -> list of possible values
        :param default_json_file: Path to default config JSON
        :param out_json_file: Path to write per-run JSON
        :param synthesis_cmd: Command to run the synthesis as a list (e.g. ["python3", "./tt/tt_tool.py", "--harden"])
        :param runs_dir: Directory where runs output is generated
        :param archive_dir: Root directory to archive each run
        :param summary_csv_path: CSV file for summary
        :param max_time: Maximum time (seconds) allowed for each run, else kill.
        """
        self.parameters = parameters
        self.default_json_file = default_json_file
        self.out_json_file = out_json_file
        self.synthesis_cmd = synthesis_cmd
        self.runs_dir = runs_dir
        self.archive_dir = archive_dir
        self.summary_csv_path = summary_csv_path
        self.max_time = max_time

        # Expand the param dict to all combinations
        self.parameter_keys = list(parameters.keys())
        self.all_combinations = list(itertools.product(*parameters.values()))

        # We'll collect all run summaries here (one dictionary per run)
        self.all_summaries = []

    def load_default_params(self):
        """Loads the default JSON once and returns it as a dict."""
        with open(self.default_json_file, 'r') as f:
            return json.load(f)

    def start_monitor(self):
        """
        Creates and starts a background thread to monitor the runs/ directory.
        Returns the threading.Event so we can stop it afterwards.
        """
        stop_event = threading.Event()
        monitor = RunMonitor(self.runs_dir, stop_event)
        monitor.start()
        return stop_event, monitor

    def run_all(self):
        """Runs the entire parameter sweep."""
        print("========================================================")
        print(" Parameter Sweep Script (Dynamic CSV Version)")
        print("--------------------------------------------------------")
        print(f" Default JSON file: {self.default_json_file}")
        print(f" Number of runs to generate: {len(self.all_combinations)}")
        print(f" Max run time (seconds): {self.max_time}")
        print("========================================================\n")

        default_params = self.load_default_params()

        for run_index, combo in enumerate(self.all_combinations, start=1):
            current_params = dict(zip(self.parameter_keys, combo))
            summary_data = self.run_single(default_params, current_params, run_index)
            self.all_summaries.append(summary_data)
            # Append to summaries.csv
            with open(self.summary_csv_path, mode='a', newline='', encoding='utf-8') as summary_csv:
                writer = csv.writer(summary_csv)
                writer.writerow(summary_data.values())

        # After all runs complete, write them once to CSV
        self.write_all_summaries_to_csv()

        print("\nAll runs have completed. Summary CSV is saved at:", self.summary_csv_path)

    def run_single(self, default_params, current_params, run_index):
        """
        Execute one run given the default_params, a dict of current_params,
        and a run index. We do the following:
          - Print run banner
          - Generate run JSON
          - Start directory monitoring
          - Launch synthesis with max_time limit
          - Parse logs and metrics
          - Return a dictionary with summary data
          - Archive results
        """
        print("========================================================")
        print(f" Starting run {run_index}/{len(self.all_combinations)} ")
        print("--------------------------------------------------------")
        for k, v in current_params.items():
            print(f"  {k}: {v}")
        print("========================================================\n")

        # Create a copy of the default JSON and override parameters
        run_json = dict(default_params)  # or .copy()
        run_json.update(current_params)

        # Write out the new JSON file
        with open(self.out_json_file, 'w') as f:
            json.dump(run_json, f, indent=2)

        # Start monitoring the runs/ directory in the background
        stop_event, monitor_thread = self.start_monitor()

        # Run the synthesis command with a timeout
        start_time = time.time()
        try:
            stdout_path = self.runs_dir / "harden.log"
            stderr_path = self.runs_dir / "harden_err.log"
            with open(stdout_path, "w") as out_f, open(stderr_path, "w") as err_f:
                proc_result = subprocess.run(
                    self.synthesis_cmd,
                    stdout=out_f,
                    stderr=err_f,
                    text=False,
                    check=False,
                    timeout=self.max_time  # Kill after specified time
                )
                stdout_text = None
                stderr_text = None
                ret_code = proc_result.returncode
        except subprocess.TimeoutExpired as e:
            # If the process times out, forcibly kill it
            print(f"ERROR: Run {run_index} timed out after {self.max_time} seconds.")
            # Let's kill the processes
            os.system('killall -9 .openroad-wrapper')
            os.system('killall -9 .openlane-wrapper')
            stdout_text = "TIMEOUT"
            stderr_text = str(e)
            ret_code = -1

        end_time = time.time()
        stop_event.set()
        monitor_thread.join()

        # Compute time in H:M:S
        elapsed_secs = end_time - start_time
        hours, remainder = divmod(elapsed_secs, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_elapsed_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

        # Parse stat.log
        num_wires = None
        num_cells = None
        stat_files = list(self.runs_dir.glob("*-yosys-synthesis/reports/stat.log"))
        if stat_files:
            stat_file = stat_files[0]
            with open(stat_file, 'r') as sf:
                for line in sf:
                    if "Number of wires:" in line:
                        num_wires = line.split(":")[-1].strip()
                    elif "Number of cells:" in line:
                        num_cells = line.split(":")[-1].strip()

        # Parse metrics.csv
        metrics_path = self.runs_dir / "final/metrics.csv"
        collected_metrics = {
            "timed_out": stdout_text=='TIMEOUT',
            "design__max_slew_violation__count": None,
            "design__max_fanout_violation__count": None,
            "design__max_cap_violation__count": None,
            "flow__errors__count": None,
            "antenna__violating__nets": None,
            "antenna__violating__pins": None,
            "route__antenna_violation__count": None,
            "route__wirelength__max": None,
            "timing__setup__ws": None, 
            "timing__hold__ws": None, 
            "design__xor_difference__count": None,
            "magic__drc_error__count": None,
            "klayout__drc_error__count": None,
            "magic__illegal_overlap__count": None,
            "design__lvs_device_difference__count": None,
            "design__lvs_net_difference__count": None,
            "design__lvs_property_fail__count": None,
            "design__lvs_error__count": None,
            "design__lvs_unmatched_device__count": None,
            "design__lvs_unmatched_net__count": None,
            "design__lvs_unmatched_pin__count": None,
            "timing__setup_vio__count": None,
            "timing__hold_vio__count": None,
            "timing__hold_r2r_vio__count": None,
            "design__instance__utilization": None,
            "magic__illegal_overlap__count": None,


        }
        if metrics_path.exists():
            with open(metrics_path, 'r') as mf:
                reader = csv.reader(mf)
                for row in reader:
                    if len(row) < 2:
                        continue
                    key = row[0].strip()
                    val = row[1].strip()
                    if key in collected_metrics:
                        collected_metrics[key] = val

        # Unfortunately, metrics.csv is not written on a fatal failure like drc or lvs

        if collected_metrics['antenna__violating__nets'] is not None:
            antenna_passed = True if int(collected_metrics["antenna__violating__nets"])==0 and int(collected_metrics["antenna__violating__pins"])==0 else False
        else: 
            antenna_passed = False
        if collected_metrics['magic__drc_error__count'] is not None:
            drc_passed = True if int(collected_metrics["magic__drc_error__count"])==0 and int(collected_metrics["klayout__drc_error__count"])==0 else False
        else:
            drc_passed = False
        if collected_metrics['design__lvs_error__count'] is not None:
            lvs_passed = True if int(collected_metrics["design__lvs_error__count"])==0 else False
        else:
            lvs_passed = False
        

        summary_data = {
            "timestamp": datetime.now().isoformat(),
            "run_index": run_index,
            **current_params,
            "time_elapsed": time_elapsed_str,
            "ret_code": ret_code,
            "antenna_passed": antenna_passed,
            "drc_passed": drc_passed,
            "lvs_passed": lvs_passed,
            "num_wires": num_wires,
            "num_cells": num_cells,
            "worst_antenna_ratio": self.get_worst_antenna_ratio(),
            "worst_slew": self.get_worst_slew(),
            **collected_metrics
        }

        self.pretty_print_summary(summary_data)
        self.print_run_end_banner(run_index, ret_code, antenna_passed, drc_passed, lvs_passed)
        self.archive_run(run_index, current_params)

        return summary_data

    def get_worst_antenna_ratio(self):
        violations = [0]
        antenna_dir = list(self.runs_dir.glob('*-checkantennas-*'))
        if len(antenna_dir)>0:
            with open(antenna_dir[0] / "reports/antenna_summary.rpt" ) as f:
                for line in f.readlines():
                    if line.startswith('│'):
                        parts = line.split('│')
                        val = float(parts[1])
                        violations.append(val)
            violations.sort()
        return violations[-1]

    def get_worst_slew(self):
        
        corners = ['max_ss_100C_1v60', 'nom_ss_100C_1v60', 'min_ss_100C_1v60']
        violations = [0]
        for corner in corners:
            corner_dir = list(self.runs_dir.glob('*-stapostpnr*'))
            if len(corner_dir)>0:
                with open(corner_dir[0] / Path(corner) / 'checks.rpt') as f:
                    content=f.read()
                # Extract the max slew section
                max_slew_section = re.search(r'max slew\n(.*?)\n\n', content, re.DOTALL)
                if not max_slew_section:
                    continue

                # Find all violation values
                vals = re.findall(r'-\d+\.\d{6}', max_slew_section.group(1))
                
                if not vals:
                    continue
                violations += vals
                # Find the worst case violation
        worst_case_violation = min(map(float, violations))
        return worst_case_violation

    def pretty_print_summary(self, summary_data: dict):
        """Pretty-print a summary after each run."""
        run_index = summary_data.get("run_index", -1)
        print(f"--------- RUN {run_index} SUMMARY ---------")
        for k, v in summary_data.items():
            print(f"{k} = {v}")
        print("-------------------------------------------\n")

    def print_run_end_banner(self, run_index, ret_code, antenna_passed, drc_passed, lvs_passed):
        """Print a concluding banner for each run."""
        status_str = (
            f"RetCode={ret_code}, "
            f"Antenna={'PASS' if antenna_passed else 'FAIL'}, "
            f"DRC={'PASS' if drc_passed else 'FAIL'}, "
            f"LVS={'PASS' if lvs_passed else 'FAIL'}"
        )
        print("========================================================")
        print(f" Finished run {run_index}/{len(self.all_combinations)} -- {status_str}")
        print("========================================================\n")

    def archive_run(self, run_index, current_params: dict):
        """Archives the `runs/` directory into a subdirectory of `archive/`."""
        combo_str = "_".join(f"{k}-{v}" for k, v in current_params.items())
        archive_subdir = self.archive_dir / f"run_{run_index}"

        if not archive_subdir.exists():
            archive_subdir.mkdir(parents=True, exist_ok=True)

        if self.runs_dir.exists():
            for item in self.runs_dir.iterdir():
                dest = archive_subdir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)

    def write_all_summaries_to_csv(self):
        """
        Writes a single CSV for all runs using the union of keys from each run's summary_data.
        This means you can add new fields anytime without manually editing a header list.
        """
        if not self.all_summaries:
            print("No runs to summarize; CSV not written.")
            return
        
        # Gather the union of all dictionary keys across runs
        all_keys = set()
        for summary in self.all_summaries:
            all_keys.update(summary.keys())
        # Sort them for a consistent column order
        #fieldnames = sorted(all_keys)
        #fieldnames = all_keys
        fieldnames = list(self.all_summaries[0].keys())

        with open(self.summary_csv_path, mode='w', newline='', encoding='utf-8') as summary_csv:
            writer = csv.DictWriter(summary_csv, fieldnames=fieldnames)
            writer.writeheader()
            for summary in self.all_summaries:
                writer.writerow(summary)


def main():
    # Example usage
    parameters = {
        "MAX_TRANSITION_CONSTRAINT": [0.7, 0.75, 1.0],
        "DESIGN_REPAIR_MAX_WIRE_LENGTH": [75, 100, 150],
        "PL_TARGET_DENSITY_PCT": [87],
        "DIODE_ON_PORTS": ["none"],
        "HEURISTIC_ANTENNA_THRESHOLD": [80,100,150],
        "GPL_CELL_PADDING": [0],
        "DPL_CELL_PADDING": [0],
        "SYNTH_STRATEGY": ["AREA 0", "AREA 1", "AREA 2"]
    }

    default_json_file = Path("src/config.json.template")
    out_json_file = Path("src/config.json")
    synthesis_cmd = ["../ttsetup/env/bin/python", "./tt/tt_tool.py", "--harden", "--openlane2"]

    runner = ParamSweepRunner(
        parameters=parameters,
        default_json_file=default_json_file,
        out_json_file=out_json_file,
        synthesis_cmd=synthesis_cmd,
        runs_dir=Path("runs/wokwi"),
        archive_dir=Path("archive"),
        summary_csv_path=Path("summary.csv"),
        max_time=25*60  # e.g., 20 minutes maximum per run
    )
    runner.run_all()


if __name__ == "__main__":
    main()
