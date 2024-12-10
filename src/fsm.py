
from amaranth import Module, Signal, unsigned
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out
from amaranth.lib.enum import Enum
from .rotor import Din
from .defines import Cmd, En

    
class Control(wiring.Component):

    cmd: In(3)
    is_at_turnover: In(3)
    
    ready: Out(1)  # Signal if the FSM is ready to input
    result_ready: Out(1)  # Signal if the FSM has a cipher value ready
    en: Out(3)   #  enables for each of the rotors
    load_start: Out(1)
    load_ring: Out(1)
    set_rotors: Out(1)
    inc: Out(1) # 
    is_ltor: Out(1)
    din_sel: Out(2) # To Rotor to determine where it takes its input

    plugboard_wr_addr: Out(1)
    plugboard_wr_data: Out(1)
    plugboard_en:  Out(1)


    def __init__(self):
        super().__init__()

    def elaborate(self, platform):
        m = Module()
        cnt = Signal(2)   # Counter to keep track of the rotor to activate 1-3 (0 is none)
        active = Signal(2)  # Active block
        inc = Signal(1, init=0)
        double_step = Signal(1)  # Flag

        is_ltor = self.is_ltor
        din_sel = self.din_sel
        inc     = self.inc

        # Convert the "active" rotor slot binary value to an one-hot enable
        with m.Switch(active):
            with m.Case(1):  # Enable Rotor slot 0
                m.d.comb += self.en.eq(0b001)
            with m.Case(2):  # Enable Rotor slot 1
                m.d.comb += self.en.eq(0b010)
            with m.Case(3):  # Enable Rotor slot 2
                m.d.comb += self.en.eq(0b100)
            with m.Default():
                m.d.comb += self.en.eq(0b000)

        with m.FSM():
            with m.State("Initial"):
                m.d.comb += [
                    inc.eq(0),
                    din_sel.eq(Din.DIN),
                    is_ltor.eq (0),
                    self.load_start.eq(0),
                    self.load_ring.eq(0),
                ]
                m.d.sync += [
                    cnt.eq(0),
                    double_step.eq(0),
                ]
                m.next = "Get command"

            with m.State("Get command"):
                m.d.comb += [
                    self.ready.eq(1),
                    self.plugboard_en.eq(0),
                ]

                with m.Switch(self.cmd):
                    with m.Case(Cmd.RESET):
                        # TODO: figure out how to reset
                        m.next = "Initial"
                    with m.Case(Cmd.LOAD_START):
                        m.d.sync += cnt.eq(cnt+1)
                        m.next = "Load start"
                    with m.Case(Cmd.LOAD_RING):
                        m.d.sync += cnt.eq(cnt+1)
                        m.next = "Load ring"
                    with m.Case(Cmd.SET_ROTORS):
                        m.d.sync += cnt.eq(cnt+1)
                        m.next = "Set rotors"
                    with m.Case(Cmd.LOAD_PLUG_ADDR):
                        m.next = "Load plug addr"
                    with m.Case(Cmd.LOAD_PLUG_DATA):
                        m.next = "Load plug data"
                    with m.Case(Cmd.SCRAMBLE):
                        m.next = "Scramble"
                    with m.Default():
                        m.next = "Get command"
            
            with m.State("Load plug addr"):
                m.d.comb += self.plugboard_wr_addr.eq(1)
                m.next = "Delay plug"
            
            with m.State("Load plug data"):
                m.d.comb += self.plugboard_wr_data.eq(1)
                m.next = "Delay plug"


            with m.State("Delay plug"):
                m.d.comb += [
                ]
                m.next = "Get command"

            with m.State("Load start"):
                m.d.comb += [ 
                    self.load_start.eq(1),
                    active.eq(cnt),
                ]
                with m.If(cnt == En.ROTOR2):
                    m.d.sync += cnt.eq(En.NONE)
                    m.next = "Get command"
                with m.Else():
                    m.next = "Get command"

            with m.State("Load ring"):
                m.d.comb += [
                    self.load_ring.eq(1),
                    active.eq(cnt)
                ]
                with m.If(cnt == En.ROTOR2):
                    m.d.sync += cnt.eq(En.NONE)

                m.next = "Get command"

            with m.State("Set rotors"):
                m.d.comb += [
                    self.set_rotors.eq(1),
                    active.eq(cnt)
                ]
                with m.If(cnt == En.ROTOR2):
                    m.d.sync += cnt.eq(En.NONE)
                m.next = "Get command"

            with m.State("Scramble"):
                m.d.comb += [
                    # Always increment rotor as we go into rotor calc in next state
                    active.eq(1),
                    inc.eq(1),
                    self.plugboard_en.eq(1),
                ]
                # Check if at turnover in this cycle before incrementing in next cycle
                with m.If(double_step):
                    m.next = "Inc Rotor 1"
                with m.Elif(self.is_at_turnover[0]):
                    m.next = "Inc Rotor 1"
                with m.Else():
                    m.next = "Rotor 0"

            with m.State("Rotor 0"):
                m.d.comb += [
                    din_sel.eq(Din.DIN),
                    active.eq(1),
                    self.plugboard_en.eq(1),
                ]
                m.next = "Rotor 1"

            with m.State("Rotor 1"):
                m.d.comb += [
                    din_sel.eq(Din.DOUT),
                    active.eq(2),   # Activate rotor 1 on next edge
                    self.plugboard_en.eq(1),
                ]
                m.next = "Rotor 2"

            with m.State("Rotor 2"):
                m.d.comb += [
                    din_sel.eq(Din.DOUT),
                    active.eq(3),   # Activate rotor 2 on next edge
                    self.plugboard_en.eq(1),
                ]
                m.next = "Rotor 2 back"
            
            with m.State("Rotor 2 back"):
                m.d.comb += [
                    din_sel.eq(Din.REF),  # Get reflected input
                    active.eq(3),   # Activate rotor 2 on next edge going left to right
                    is_ltor.eq(1),
                    self.plugboard_en.eq(1),
                ]
                m.next = "Rotor 1 back"

            with m.State("Rotor 1 back"):
                m.d.comb += [
                    din_sel.eq(Din.DOUT),  # Get Rotor 2 output
                    active.eq(2),   # Activate rotor 1 on next edge going left to right
                    is_ltor.eq(1),
                    self.plugboard_en.eq(1),
                ]
                m.next = "Rotor 0 back"

            with m.State("Rotor 0 back"):
                m.d.comb += [
                    din_sel.eq(Din.DOUT),  # Get Rotor 1 output
                    active.eq(1),   # Activate rotor 0 on next edge going left to right
                    is_ltor.eq(1),
                    self.plugboard_en.eq(1),
                ]
                m.next = "Delay"

            with m.State("Delay"):
                m.d.comb += [
                    self.plugboard_en.eq(1),
                    is_ltor.eq(1),
                    self.result_ready.eq(1)  # Keep plugboard and is_ltor stable until we flop the pb output using result_ready
                ]
                m.next = "Delay 2"

            with m.State("Delay 2"):
                m.d.comb += [
                    self.plugboard_en.eq(1),
                    is_ltor.eq(1),
                ]
                m.next = "Get command"

            # The portion of the state machine for handling the double stepping
            with m.State("Inc Rotor 1"):
                m.d.comb += [
                    active.eq(2), # Activate rotor 1 on next edge
                    inc.eq(1),    # Increment it
                ]
                m.next = "Check turnover"

            with m.State("Check turnover"):
                with m.If(double_step):
                    m.next = "Inc Rotor 2"
                with m.Elif(self.is_at_turnover[1]):
                    m.next = "Activate double step"
                with m.Else():
                    m.next = "Rotor 0"
            
            with m.State("Inc Rotor 2"):
                m.d.comb += [
                    active.eq(3),  # Activate rotor 2
                    inc.eq(1),
                ]
                m.d.sync += [
                    double_step.eq(0)
                ]
                m.next = "Rotor 0"
            
            with m.State("Activate double step"):
                # Moore machine, otherwise we could probably eliminate states
                m.d.sync += [
                    double_step.eq(1)
                ]
                m.next = "Rotor 0"
                

        return m

                    


                