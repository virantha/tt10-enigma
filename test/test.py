# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.types import LogicArray
from cocotb.clock import Clock
from cocotb.binary import BinaryValue
from cocotb.triggers import ClockCycles, RisingEdge, FallingEdge, Edge, ReadOnly, NextTimeStep
from random import randint
from fsm import Cmd
from tb_utils import *

async def ready(dut):
    #await RisingEdge(dut.user_project.enigma.fsm.ready) 
    await ClockCycles(dut.clk,1)
    rdy = dut.user_project.enigma.ready
    if not rdy:
        await FallingEdge(rdy)
    #await ReadOnly()
    #await NextTimeStep()
    #while dut.user_project.enigma.ready.value==0:
        #await ClockCycles(dut.clk, 1)
    await RisingEdge(dut.user_project.enigma.ready)

async def reset(dut):
    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

def get_ui_in(cmd, val):
    cmd = BinaryValue(value=cmd, n_bits=3, bigEndian=False) 
    val = BinaryValue(value=val, n_bits=5, bigEndian=False)
    ui_in = BinaryValue(cmd.binstr + val.binstr, n_bits=8)
    return ui_in

@cocotb.test()
async def test_load(dut):
    dut._log.info("Start")
    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    await reset(dut)
    
    await ready(dut)

    start_vals = []
    for i in range(3):
        start_vals.append([randint(0,26) for i in range(10)])

    rotor = dut.user_project.enigma.r 
    
    rdy = dut.user_project.enigma.ready
    prev_r2 = None
    for r0, r1, r2 in zip(*start_vals):

        cmd = 1
        val = get_ui_in(cmd,r0)
        dut.ui_in.value = val
        dut._log.info(f"Rotor 0: BINARY VALUE {val}")
        
        await ready(dut)
        if prev_r2:
            assert rotor.cnts_debug2.value == prev_r2

        val = get_ui_in(cmd,r1)
        dut.ui_in.value = val
        dut._log.info(f"Rotor 1: BINARY VALUE {val}")
        await ready(dut)
        assert rotor.cnts_debug0.value == r0


        val = get_ui_in(cmd,r2)
        dut.ui_in.value = val
        dut._log.info(f"Rotor 2: BINARY VALUE {val}")
        await ready(dut)
        assert rotor.cnts_debug1.value == r1
        prev_r2 = r2

        #assert rotor_cnt[rotor].cnt.value==start_val

async def set_plugboard_setting(dut, a,b):
    dut._log.info(f"Setting plugboard {a} -> {b}")

    cmd = Cmd.LOAD_PLUG_ADDR.value
    val = to_val(a)
    dut.ui_in.value = get_ui_in(cmd, val) 
    await ready(dut)

    cmd = Cmd.LOAD_PLUG_DATA.value
    val = to_val(b)
    dut.ui_in.value = get_ui_in(cmd, val) 
    await ready(dut)

    return

async def set_rotor_setting(dut, rotor_num, letter_setting):
    cmd = Cmd.LOAD_START.value
    val = to_val(letter_setting)
    dut.ui_in.value = get_ui_in(cmd, val) 
    await ready(dut)

async def set_ring_setting(dut, rotor_num, val:int):
    cmd = Cmd.LOAD_RING.value
    dut.ui_in.value = get_ui_in(cmd, val) 
    await ready(dut)

def iter_plain_text(plain):
    for c in plain:
        c = c.upper()
        if c >= 'A' and c <= 'Z':
            input_val = ord(c)-65
            yield c, input_val


async def run_cipher(dut, rotors, plugboard, plain):
    golden = get_golden_cipher(rotors, plugboard, plain)

    # Reset the plugboard
    for i in range(26):
        await set_plugboard_setting(dut, to_letter(i), to_letter(i))

    for a,b in plugboard:
        await set_plugboard_setting(dut, a, b)
        await set_plugboard_setting(dut, b, a)

    for rotor_num, rotor in enumerate(rotors):
        await set_rotor_setting(dut, rotor_num, rotor['start'])

    for rotor_num, rotor in enumerate(rotors):
        await set_ring_setting(dut, rotor_num, rotor['ring'])

    # Encrypt and compare against the expected value
    for i, (input_char, val) in enumerate(iter_plain_text(plain)):
        cmd = Cmd.ENCRYPT.value
        dut.ui_in.value = get_ui_in(cmd, val)
        await ready(dut)

        cmd = Cmd.NOP.value
        dut.ui_in.value = get_ui_in(cmd, val)
        await ClockCycles(dut.clk,3)


        golden_val = ord(golden[i]) - 65

        out_val = LogicArray(dut.uo_out.value)[4:]

        input_val = val
        #dut._log.info(f'{golden_val:0b}, {out_val}, {out_val.integer}')
        log_msg = f'Round {i}: Input {input_char} (0x{input_val:x} / {input_val}) -> {golden[i]} (0x{golden_val:x} / {golden_val}) expected, actual 0x{out_val.integer:x} / {out_val.integer}'
        #dut._log.info(log_msg)
        assert golden_val==out_val.integer, log_msg

@cocotb.test()
async def test_enigma_fixed(dut):
    dut._log.info("Start")
    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    await reset(dut)
    
    await ready(dut)

    # Create a randomized Enigma settings
    rotors = get_fixed_rotor_setting()
    plugboard = get_fixed_plugboard_setting()

    await run_cipher(dut, rotors, plugboard, plain)



@cocotb.test()
async def test_enigma_randomx10(dut):
    dut._log.info("Start")
    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    for i in range(10):
        await reset(dut)
        await ready(dut)
        random_text = [chr(randint(0,25)+65) for count in range(3000)]
        random_text = ''.join(random_text)

        # Create a randomized Enigma settings
        rotors = get_random_rotor_setting()
        plugboard = get_random_plugboard_setting()
        await run_cipher(dut, rotors, plugboard, random_text)

    # golden = get_golden_cipher(rotors, plugboard, plain)

    # # Reset the plugboard
    # for i in range(26):
    #     await set_plugboard_setting(dut, to_letter(i), to_letter(i))

    # for a,b in plugboard:
    #     await set_plugboard_setting(dut, a, b)
    #     await set_plugboard_setting(dut, b, a)

    # for rotor_num, rotor in enumerate(rotors):
    #     await set_rotor_setting(dut, rotor_num, rotor['start'])

    # for rotor_num, rotor in enumerate(rotors):
    #     await set_ring_setting(dut, rotor_num, rotor['ring'])

    # # Encrypt and compare against the expected value
    # for i, (input_char, val) in enumerate(iter_plain_text(plain)):
    #     cmd = Cmd.ENCRYPT.value
    #     dut.ui_in.value = get_ui_in(cmd, val)
    #     await ready(dut)

    #     cmd = Cmd.NOP.value
    #     dut.ui_in.value = get_ui_in(cmd, val)
    #     await ClockCycles(dut.clk,3)


    #     golden_val = ord(golden[i]) - 65

    #     out_val = LogicArray(dut.uo_out.value)[4:]

    #     input_val = val
    #     #dut._log.info(f'{golden_val:0b}, {out_val}, {out_val.integer}')
    #     log_msg = f'Round {i}: Input {input_char} (0x{input_val:x} / {input_val}) -> {golden[i]} (0x{golden_val:x} / {golden_val}) expected, actual 0x{out_val.integer:x} / {out_val.integer}'
    #     dut._log.info(log_msg)
    #     assert golden_val==out_val.integer, log_msg

