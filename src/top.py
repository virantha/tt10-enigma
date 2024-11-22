
from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out
from .rotor import Rotor_I, Rotor_II, Rotor_III, Reflector_B
from .fsm import Control, Cmd

class Enigma(wiring.Component):
    ui_in: In(8)
    uo_out: Out(6)

    def __init__(self):

        # The rotors
        rotors = { 'I': Rotor_I,
                   'II': Rotor_II,
                   'III': Rotor_III,
        }
        # The reflectors
        reflectors = { 'A': None,
                       'B': Reflector_B,
        }
        my_rotors = ['I', 'II', 'III'] # Right to left
        self.rotors = [rotors[r]() for r in my_rotors]
        self.reflector = reflectors['B']()
        self.fsm = Control() 
        super().__init__()


    def elaborate(self, platform):
        m = Module()
        m.submodules.r0 = self.r0 = r0 = self.rotors[0]
        m.submodules.r1 = self.r1 = r1 = self.rotors[1]
        m.submodules.r2 = self.r2 = r2 = self.rotors[2]
        m.submodules.ref = self.ref = ref  = self.reflector
        m.submodules.fsm = fsm = self.fsm

        right_out     = Signal(5)
        right_out_ff1 = Signal(5)
        right_out_ff2 = Signal(5)
        ready = Signal(1)

        right_in = self.ui_in[0:5]
        cmd      = self.ui_in[5:8]
        right_out_ff2 = self.uo_out[0:5]
        ready     = self.uo_out[5]

        # Delay the output data by one cycle to line up with the ready signal
        m.d.sync += [
            right_out_ff1.eq(right_out)
        ]
        with m.If(ready & (cmd==Cmd.ENCRYPT)):
            m.d.sync += right_out_ff2.eq(right_out_ff1)
         
        m.d.comb += [
            # The right to left path
            r0.right_in.eq(right_in),
            r1.right_in.eq(r0.left_out),
            r2.right_in.eq(r1.left_out),

            ref.right_in.eq(r2.left_out),
            
            # Loop back, left to right
            # (Reflector's left_in to right_out path is not used)
            r2.left_in.eq(ref.left_out),
            r1.left_in.eq(r2.right_out),
            r0.left_in.eq(r1.right_out),

            right_out.eq(r0.right_out) ,


            # Connect up the control FSM

            r0.en.eq(fsm.en[0]),
            r1.en.eq(fsm.en[1]),
            r2.en.eq(fsm.en[2]),
            ref.en.eq(0),

            r0.load_start.eq(fsm.load_start),
            r1.load_start.eq(fsm.load_start),
            r2.load_start.eq(fsm.load_start),
            ref.load_start.eq(0),

            r0.load_ring.eq(fsm.load_ring),
            r1.load_ring.eq(fsm.load_ring),
            r2.load_ring.eq(fsm.load_ring),
            ref.load_ring.eq(0),

            r0.inc.eq(fsm.inc[0]),
            r1.inc.eq(fsm.inc[1]),
            r2.inc.eq(fsm.inc[2]),
            ref.inc.eq(0),

            fsm.is_at_turnover[0].eq(r0.is_at_turnover),
            fsm.is_at_turnover[1].eq(r1.is_at_turnover),
            fsm.is_at_turnover[2].eq(r2.is_at_turnover),
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
