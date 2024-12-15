
from amaranth import Signal, Module
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out
from .rotor import Rotor, Reflector_B
from .fsm import Control, Cmd
from .plugboard import Plugboard
from .lcd import SevenSegmentAlpha

class Enigma(wiring.Component):
    ui_in: In(8)
    uo_out: Out(8)  # Display port

    uio_out: Out(6) 

    # Let's put a debug port to look at the output of the rotor before going into the plugboard
    #debug_out: Out(5)
    #debug_pen: Out(1)

    def __init__(self):

        self.rotor = Rotor()
        self.reflector = Reflector_B()
        self.fsm = Control() 
        self.plugboard = Plugboard()
        self.lcd = SevenSegmentAlpha()
        super().__init__()


    def elaborate(self, platform):
        m = Module()
        m.submodules.r = r = self.rotor
        m.submodules.ref = ref = self.reflector
        m.submodules.fsm = fsm = self.fsm
        m.submodules.plugboard = plugboard = self.plugboard
        # Display decoder
        m.submodules.lcd = lcd = self.lcd

        #right_out_ff1 = Signal(5)
        ready = Signal(1)

        right_in = self.ui_in[0:5]
        cmd      = self.ui_in[5:8]
        #right_out_ff1 = self.uio_out[0:5]
        ready     = self.uio_out[5]

        # Connect LCD
        m.d.comb += [
            lcd.din.eq(self.uio_out[0:5]),
            self.uo_out.eq(lcd.dout)
        ]

        # DEBUG PORT
        # m.d.comb += [
        #     self.debug_out.eq(r.dout),
        #     self.debug_pen.eq(fsm.plugboard_en)
        # ]
        m.d.comb += [
            # Plugboard traversal
            plugboard.in_rtol.eq(right_in),
            plugboard.in_ltor.eq(r.dout),

            plugboard.enable.eq(fsm.plugboard_en),
            # Plugboard setting
            plugboard.wr_data.eq(right_in),
            plugboard.wr_data_en.eq(fsm.plugboard_wr_data),
            plugboard.wr_addr_en.eq(fsm.plugboard_wr_addr),
        ]

        with m.If(fsm.result_ready & (cmd==Cmd.SCRAMBLE)):
        #with m.If(fsm.result_ready): # Adding Cmd.SCRAMBLE to this saves 2% area???
            # Hold the output of the enigma encoder stable until next scramble command
            m.d.sync += self.uio_out[0:5].eq(plugboard.out)
         
        m.d.comb += [
            # The right to left path
            r.din.eq(plugboard.out),

            ref.din.eq(r.dout),

            
            # Loop back, left to right
            r.reflector_in.eq(ref.dout),

            # Connect up the control FSM
            r.en.eq(fsm.en),
            r.load_start.eq(fsm.load_start),
            r.load_ring.eq(fsm.load_ring),
            r.inc.eq(fsm.inc),
            r.ltor.eq(fsm.is_ltor),
            plugboard.is_ltor.eq(fsm.is_ltor),
            r.din_sel.eq(fsm.din_sel),

            fsm.is_at_turnover.eq(r.is_at_turnover),
            r.load_rotor_type.eq(fsm.set_rotors),
            fsm.cmd.eq(cmd),
            ready.eq(fsm.ready),

        ]
        return m 

if __name__=='__main__':
    from amaranth.back import verilog
    enigma = Enigma()
    filename = 'src/am_top.v'
    with open(filename, 'w') as f:
        f.write(verilog.convert(enigma))
        print(f'Wrote {filename}')
