from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out

class Rotor (wiring.Component):

    right_in: In(5)
    left_out: Out(5)

    left_in: In(5)
    right_out: Out(5)

    is_at_turnover: Out(1)
    en: In(1)
    load_start: In(1)
    load_ring: In(1)
    inc: In(1)

    def __init__(self):
        self.wiring = self._wiring
        self.cnt = Signal(5)
        self.right_ptr = Signal(5)
        self.rtol_swizzle = Signal(5)
        self.ring_setting = Signal(5)
        self.turnover = Const(ord(self._turnover)-65)

        self.left_ptr = Signal(5)
        super().__init__()

    def elaborate(self, platform):
        m = Module()

        cnt_ring_combined = Signal(5)
        with m.If(self.ring_setting > self.cnt):
            m.d.comb += cnt_ring_combined.eq(26-(self.ring_setting-self.cnt))
        with m.Else():
            m.d.comb += cnt_ring_combined.eq(self.cnt-self.ring_setting)

        with m.If(self.en):
            with m.If(self.load_start):
                m.d.sync += self.cnt.eq(self.right_in)
            with m.Elif(self.load_ring):
                m.d.sync += self.ring_setting.eq(self.right_in)
            with m.Elif(self.inc):
                with m.If(self.cnt==25):
                    m.d.sync += self.cnt.eq(0)
                with m.Else():
                    m.d.sync += self.cnt.eq(self.cnt+1)

                #m.d.sync += self.cnt.eq((self.cnt+1) % 26)

        mapping = [ord(c)-65 for c in self.wiring]
        mapping_ltor = [0]*26
        for i, c in enumerate(self.wiring):
            mapping_ltor[ord(c)-65] = i

        Wiring = Array(mapping) # right_to_left mapping
        Wiring_left_to_right = Array(mapping_ltor)
        
        # Calculate turnover
        m.d.comb += self.is_at_turnover.eq(self.cnt == self.turnover)

        # Convert absolute entry (right) to relative contact point on
        # the rotor by adding its rotation (cnt).
        # "data" will then be the output of the wiring pattern based on right_ptr

        m.d.comb += self.right_ptr.eq((cnt_ring_combined + self.right_in ) %26)
        
        # Convert the "data" which is the contact point on the left side
        # of the rotor (Wiring[right_ptr]), to an absolute position by subtracting out
        # the rotation of the rotor (cnt).  Thereore, "left" will be the
        # absolute position the signal will enter the next rotor to the left.

        m.d.comb += self.rtol_swizzle.eq(Wiring[self.right_ptr])
        m.d.comb += self.left_out.eq(
            Mux( self.load_start | self.load_ring, 
                 self.right_in, 
                (self.rtol_swizzle-(cnt_ring_combined))%26))

        # Left to right
        m.d.comb += self.left_ptr.eq((self.left_in + cnt_ring_combined)%26)
        m.d.comb += self.right_out.eq((Wiring_left_to_right[self.left_ptr] - (cnt_ring_combined)) % 26)

        return m
            

class Rotor_I(Rotor):
    _wiring = 'EKMFLGDQVZNTOWYHXUSPAIBRCJ'
    _turnover = 'Q'
class Rotor_II(Rotor):
    _wiring = 'AJDKSIRUXBLHWTMCQGZNPYFVOE'
    _turnover = 'E'
class Rotor_III(Rotor):
    _wiring = 'BDFHJLCPRTXVZNYEIWGAKMUSQO'
    _turnover = 'V'

class Reflector_B(Rotor):
    _wiring = 'YRUHQSLDPXNGOKMIEBFZCWVJAT'
    _turnover = 'Z'

    """Remove unnecessary logic from Rotor code to make the area smaller

        - No left to right path
        - No counter (since we never increment this)
        - Ring_setting is always 0
        
    """

    def elaborate(self, platform):
        m = Module()

        mapping = [ord(c)-65 for c in self.wiring]

        Wiring = Array(mapping) # right_to_left mapping
        
        m.d.comb += self.right_ptr.eq(self.right_in)
        
        # Convert the "data" which is the contact point on the left side
        # of the rotor (Wiring[right_ptr]), to an absolute position by subtracting out
        # the rotation of the rotor (cnt).  Thereore, "left" will be the
        # absolute position the signal will enter the next rotor to the left.
        m.d.comb += self.left_out.eq(Wiring[self.right_ptr])

        # Tie off unused outputs
        m.d.comb += [
            self.right_out.eq(0),
            self.is_at_turnover.eq(0),
            self.rtol_swizzle.eq(0),
            self.cnt.eq(0),
            self.left_ptr.eq(0),
        ]
        return m


if __name__=='__main__':
    from amaranth.back import verilog
    top = Rotor()
    with open('am_rotor.v', 'w') as f:
        f.write(verilog.convert(top))