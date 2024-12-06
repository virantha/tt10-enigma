
from amaranth import Module, Signal, unsigned
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out
from amaranth.lib.enum import Enum
from .rotor2 import Din

class Cmd(Enum, shape=unsigned(3)):
    NOP = 0
    LOAD_START = 1
    LOAD_RING = 2
    RESET = 3
    ENCRYPT = 4
    LOAD_PLUG_ADDR = 5
    LOAD_PLUG_DATA = 6

class En(Enum, shape=unsigned(2)):
    # Just to make sure I'm picking the proper rotor (rotor 0 = 1, rotor 1 = 2, rotor 2 = 3)
    NONE = 0
    ROTOR0 = 1
    ROTOR1 = 2
    ROTOR2 = 3

    
class Control(wiring.Component):

    cmd: In(3)
    is_at_turnover: In(3)
    
    ready: Out(1)  # Signal if the FSM is ready to input
    result_ready: Out(1)  # Signal if the FSM has a cipher value ready
    en: Out(3)   #  enables for each of the rotors
    load_start: Out(1)
    load_ring: Out(1)
    inc: Out(1) # 
    is_ltor: Out(1)
    din_sel: Out(2) # To Rotor to determin where it takes its input

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
                    self.plugboard_en.eq(1),
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
                    with m.Case(Cmd.LOAD_PLUG_ADDR):
                        m.next = "Load plug addr"
                    with m.Case(Cmd.LOAD_PLUG_DATA):
                        m.next = "Load plug data"
                    with m.Case(Cmd.ENCRYPT):
                        m.next = "Encrypt"
                    with m.Default():
                        m.next = "Get command"
            
            with m.State("Load plug addr"):
                m.d.comb += self.plugboard_wr_addr.eq(1)
                m.next = "Get command"
            
            with m.State("Load plug data"):
                m.d.comb += self.plugboard_wr_data.eq(1)
                m.next = "Delay"

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

            with m.State("Encrypt"):
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
                ]
                m.next = "Rotor 2"

            with m.State("Rotor 2"):
                m.d.comb += [
                    din_sel.eq(Din.DOUT),
                    active.eq(3),   # Activate rotor 2 on next edge
                ]
                m.next = "Rotor 2 back"
            
            with m.State("Rotor 2 back"):
                m.d.comb += [
                    din_sel.eq(Din.REF),  # Get reflected input
                    active.eq(3),   # Activate rotor 2 on next edge going left to right
                    is_ltor.eq(1),
                ]
                m.next = "Rotor 1 back"

            with m.State("Rotor 1 back"):
                m.d.comb += [
                    din_sel.eq(Din.DOUT),  # Get Rotor 2 output
                    active.eq(2),   # Activate rotor 1 on next edge going left to right
                    is_ltor.eq(1),
                ]
                m.next = "Rotor 0 back"

            with m.State("Rotor 0 back"):
                m.d.comb += [
                    din_sel.eq(Din.DOUT),  # Get Rotor 2 output
                    active.eq(1),   # Activate rotor 0 on next edge going left to right
                    is_ltor.eq(1),
                    self.plugboard_en.eq(1),
                ]
                m.next = "Delay"

            with m.State("Delay"):
                m.d.comb += [
                    self.plugboard_en.eq(1),
                    self.result_ready.eq(1)
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
                

            # with m.State("Inc Rotor 0"):
            #     # For rotor zero, increment it before processing
            #     # The increment is enabled in the previous state, so 
            #     # in this state, we already have the proper rotor 0 setting
            #     m.d.comb += [
            #         active.eq(cnt),
            #         self.plugboard_en.eq(1)
            #     ]
            #     with m.If(self.is_at_turnover[0] | double_step):
            #         m.next = "Inc Rotor 1"
            #         m.d.sync += [
            #             cnt.eq(2),
            #             inc.eq(1),
            #         ]
            #     with m.Else():
            #         m.next = "Delay"

            # with m.State("Rotor 1"):
            #     m.d.comb += [
            #         active.eq(cnt),
            #         self.plugboard_en.eq(1)
            #     ]



            # with m.State("Inc Rotor 1"):
            #     m.d.comb += [
            #         active.eq(cnt),
            #         self.plugboard_en.eq(1)
            #     ]
            #     m.d.sync += [
            #         cnt.eq(2),
            #         inc.eq(0),
            #     ]
            #     m.next = "Check Rotor 1 Turnover"  

            # with m.State("Check Rotor 1 Turnover"):
            #     m.d.comb += [
            #         self.plugboard_en.eq(1)
            #     ]
            #     m.d.sync += [
            #         inc.eq(0),
            #     ]
            #     with m.If(self.is_at_turnover[1]):
            #         # to marking this Rotor 1 for a double step
            #         # The next character input will cause Rotor 0, 1, and 2 to inc before outptuting the code
            #         m.d.sync += double_step.eq(True)
            #         m.next = "Delay"
            #     with m.Elif(double_step):
            #         m.d.sync += [
            #             cnt.eq(3),
            #             inc.eq(1),
            #         ]
            #         m.next = "Inc Rotor 2"
            #     with m.Else():
            #         m.next = "Delay"

            # with m.State("Inc Rotor 2"):
            #     m.d.comb += [
            #         active.eq(cnt),
            #         self.plugboard_en.eq(1)
            #     ]
            #     m.d.sync += [
            #         double_step.eq(False),
            #         cnt.eq(0),
            #         inc.eq(0),
            #         # TODO:
            #         self.is_rtol.eq(0),
            #     ]
            #     m.next = "Delay"

            # with m.State("Delay"):
            #     m.d.comb += [
            #         self.plugboard_en.eq(1),
            #         self.result_ready.eq(1)
            #     ]
            #     m.next = "Get command"
        return m

                    


                