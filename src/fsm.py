
from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out
#from amaranth.lib.coding import Decoder
from amaranth.lib.enum import Enum

class Cmd(Enum, shape=unsigned(3)):
    NOP = 0
    LOAD_START = 1
    LOAD_RING = 2
    RESET = 3
    ENCRYPT = 4
    
class Control(wiring.Component):

    cmd: In(3)
    is_at_turnover: In(3)

    
    ready: Out(1)  # Signal if the FSM is ready to input
    en: Out(3)   #  enables for each of the rotors
    load_start: Out(1)
    load_ring: Out(1)
    inc: Out(3) # TODO: DO I really need separate inc signals??


    def __init__(self):
        super().__init__()

    def elaborate(self, platform):
        m = Module()
        active = Signal(2)  # Active block
        inc = Signal(3, init=0)
        double_step = Signal(1)  # Flag

        #dmux_en = m.submodules.dmux_en = Decoder(4)

        # Connect the demuxers to assign the load signals to the 
        # different rotors
        m.d.comb += [
            #dmux_en.i.eq(active),
            #self.en.eq(dmux_en.o[1:4]),

            self.inc.eq(inc)
        ]

        with m.Switch(active):

            with m.Case(1):
                m.d.comb += self.en.eq(0b001)
            with m.Case(2):
                m.d.comb += self.en.eq(0b010)
            with m.Case(3):
                m.d.comb += self.en.eq(0b100)
            with m.Default():
                m.d.comb += self.en.eq(0b000)


        with m.FSM():
            with m.State("Initial"):
                m.d.sync += active.eq(0)
                m.next = "Get command"

            with m.State("Get command"):
                m.d.comb += [
                    self.ready.eq(1),
                    self.load_start.eq(0),
                    self.load_ring.eq(0),
                ]
                m.d.sync += [
                    active.eq(0),
                    inc.eq(0),
                ]

                with m.Switch(self.cmd):
                    with m.Case(Cmd.RESET):
                        # TODO: figure out how to reset
                        m.next = "Initial"
                    with m.Case(Cmd.LOAD_START):
                        m.next = "Load start"
                    with m.Case(Cmd.LOAD_RING):
                        m.next = "Load ring"
                    with m.Case(Cmd.ENCRYPT):
                        m.next = "Inc Rotor 0"
                    with m.Default():
                        m.next = "Get command"
            
            with m.State("Load start"):
                m.d.comb += self.load_start.eq(1)
                with m.If(active==3):
                    m.d.sync += active.eq(0)
                    m.next = "Get command"
                with m.Else():
                    m.d.sync += active.eq(active+1)
                    m.next = "Load start"

            with m.State("Load ring"):
                m.d.comb += self.load_ring.eq(1)
                with m.If(active==3):
                    m.d.sync += active.eq(0)
                    m.next = "Get command"
                with m.Else():
                    m.d.sync += active.eq(active+1)
                    m.next = "Load ring"

            with m.State("Inc Rotor 0"):
                # For rotor zero, increment it before processing
                m.d.sync += [
                    active.eq(1),
                    inc[0].eq(1),
                ]
                with m.If(self.is_at_turnover[0]):
                    m.next = "Inc Rotor 1"
                with m.Elif(double_step):
                    m.next = "Inc Rotor 1"
                with m.Else():
                    m.next = "Delay 2"

            with m.State("Inc Rotor 1"):
                m.d.sync += [
                    active.eq(2),
                    inc[0].eq(0),
                    inc[1].eq(1),
                ]
                m.next = "Delay"  # Have to wait an extra cycle for counter to inc and capture turnover flag

            with m.State("Delay"):
                m.d.sync += inc.eq(0)
                m.next = "Check Rotor 1 Turnover"
            
            with m.State("Check Rotor 1 Turnover"):
                m.d.sync += [
                    inc.eq(0),
                ]
                with m.If(self.is_at_turnover[1]):
                    # to marking this Rotor 1 for a double step
                    # The next character input will cause Rotor 0, 1, and 2 to inc before outptuting the code
                    m.d.sync += double_step.eq(True)
                    m.next = "Delay 2"
                with m.Elif(double_step):
                    m.next = "Inc Rotor 2"
                with m.Else():
                    m.next = "Delay 2"

            with m.State("Inc Rotor 2"):
                m.d.sync += [
                    double_step.eq(False),
                    active.eq(3),
                    inc[0].eq(0),
                    inc[1].eq(0),
                    inc[2].eq(1),
                ]
                m.next = "Delay 2"


            with m.State("Delay 2"):
                m.d.sync += [
                    active.eq(0),
                    inc.eq(0),
                ]
                m.next = "Delay 3"

            with m.State("Delay 3"):
                m.next = "Get command"

        return m

                    


                