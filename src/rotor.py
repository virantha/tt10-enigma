from amaranth import Module, Signal, Const, Array, Mux, unsigned
from amaranth.lib.enum import Enum
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out
from src.defines import Rotors

class Din(Enum, shape=unsigned(2)):
    DIN = 0
    DOUT = 1
    REF = 2 

class Rotor (wiring.Component):

    din: In(5)
    dout: Out(5)

    reflector_in: In(5) # Input from the reflector that is muxed in when din_sel=2

    is_at_turnover: Out(3)   # bit_i is high if rotor_i is at the turnover letter
    en: In(3)                # One-hot signal to enable one of the 3 rotors
    
    # Configuration signals
    load_start: In(1)
    load_ring: In(1)
    load_rotor_type: In(1)

    # Command the selected rotor to incrementt
    inc: In(1)
    
    # When coming back from the reflector, this bit is high
    ltor: In(1)  # False if right to left (the ingress path)

    # Select the input the rotor should operate on (ingress from plugboard, last rotor output, or reflector output)
    din_sel: In(2) # 0=din, 1=dout, 2=reflector

    N = 3  # Number of rotor slots 

    def __init__(self):
        N = self.N
        self.cnts = Array([Signal(5) for i in range(N)])   # Registers for each of the rotors (as well as start position)
        self.ring_settings = Array([Signal(5) for i in range(N)])

        self.generate_wirings()

        super().__init__()

    def generate_wirings(self):
        from test.enigma import Enigma
        _wirings = []
        _turnovers = []

        for rotor_type in Rotors:
            # Gather up the wiring and turnover positions from the golden model
            rotor_class = Enigma.ROTORS[rotor_type]
            _wirings.append(rotor_class.wiring)
            _turnovers.append(rotor_class.turnover)

        wiring_list_right_to_left = []
        wiring_list_left_to_right = []
        for w in _wirings:
            mapping = [ord(c)-65 for c in w]
            mapping_ltor = [0]*26
            for i, c in enumerate(w):
                mapping_ltor[ord(c)-65] = i

            wiring_list_right_to_left.append(Array(mapping)) # right_to_left mapping
            wiring_list_left_to_right.append(Array(mapping_ltor))

        self.Wiring_right_to_left = Array(wiring_list_right_to_left)
        self.Wiring_left_to_right = Array(wiring_list_left_to_right)
        
        self.turnovers = Array([Const(ord(t)-65) for t in _turnovers])

    def elaborate(self, platform):
        m = Module()
        N = self.N

        cnt_ring_combined = Signal(5)
        ring_setting = Signal(5)
        cnt = Signal(5)
        muxed_din = Signal(5)
        right_ptr = Signal(5)
        wiring_rtol = Signal(5)
        wiring_ltor = Signal(5)

        # Picking the rotor for each slot
        self.slot = Array([Signal(3, init=0), Signal(3,init=1), Signal(3, init=2)]) # Choose from one of 8 rotor types for each of the 3 slots
        
        # Pull out the array for debug
        cnts_debug0 = Signal(5)
        cnts_debug1 = Signal(5)
        cnts_debug2 = Signal(5)
        m.d.comb+= cnts_debug0.eq(self.cnts[0]) 
        m.d.comb+= cnts_debug1.eq(self.cnts[1]) 
        m.d.comb+= cnts_debug2.eq(self.cnts[2]) 
        #Mux on the inputs
        with m.Switch(self.din_sel):
            with m.Case(1):
                m.d.comb += muxed_din.eq(self.dout)
            with m.Case(2):
                m.d.comb += muxed_din.eq(self.reflector_in)
            with m.Default():
                m.d.comb += muxed_din.eq(self.din)
        

        cnt_eq_25 = Signal(1)

        with m.Switch(self.en):
            for one_hot, rotor in [(0b001, 0), (0b010,1), (0b100, 2)]:
                with m.Case(one_hot):
                    m.d.comb += [
                        ring_setting.eq(self.ring_settings[rotor]),
                        cnt.eq(self.cnts[rotor]),
                        cnt_eq_25.eq(cnt==25),
                        wiring_rtol.eq(self.Wiring_right_to_left[self.slot[rotor]][right_ptr]),
                        wiring_ltor.eq(self.Wiring_left_to_right[self.slot[rotor]][right_ptr]),
                    ]
                    with m.If(self.load_start):
                        m.d.sync += self.cnts[rotor].eq(muxed_din)
                    with m.Elif(self.load_ring):
                        m.d.sync += self.ring_settings[rotor].eq(muxed_din)
                    with m.Elif(self.load_rotor_type):
                        m.d.sync += self.slot[rotor].eq(muxed_din[0:3])
                    with m.Elif(self.inc):
                        # PULL OUT COMPARISON HERE??
                        with m.If(cnt_eq_25):
                            m.d.sync += self.cnts[rotor].eq(0)
                        with m.Else():
                            m.d.sync += self.cnts[rotor].eq(cnt+1)
            with m.Default():
                m.d.comb += [
                    ring_setting.eq(0),
                    cnt.eq(0)
                ]

        with m.If(ring_setting > cnt):
            m.d.comb += cnt_ring_combined.eq(26-(ring_setting-cnt))
        with m.Else():
            m.d.comb += cnt_ring_combined.eq(cnt-ring_setting)

        # Calculate turnover.  
        for i in range(N):
            #m.d.comb += self.is_at_turnover[i].eq(self.cnts[i] == self.turnovers[i])
            m.d.comb += self.is_at_turnover[i].eq(self.cnts[i] == self.turnovers[self.slot[i]])

        # Convert absolute entry (right) to relative contact point on
        # the rotor by adding its rotation (cnt).
        # "data" will then be the output of the wiring pattern based on right_ptr

        def add_mod_26(sum_signal, a,b):
            s = Signal(6)
            s_m_26 = Signal(6)
            s_ge_26 = Signal(1)
            m.d.comb += [
                s.eq (a+b),
                #s_ge_26.eq ( (s[5]==1) | (s[0:5]>=26)),
                s_ge_26.eq ( s>=26),
                s_m_26.eq ( s - 26),
                sum_signal.eq (Mux (s_ge_26, s_m_26[0:5], s[0:5]))
            ]

        def sub_mod_26(sum_signal, a,b):
            s = Signal(6)
            a_ext = Signal(6)
            b_ext = Signal(6)
            diff_plus_26 = Signal(6)

            m.d.comb += [
                a_ext.eq (a),
                b_ext.eq (b),
                s.eq( a_ext - b_ext),
                diff_plus_26.eq(s+26),
                # If MSB is 1, that's underflow
                sum_signal.eq(Mux(s[5], diff_plus_26[0:5], s[0:5])),
            ] 

        add_mod_26(right_ptr, muxed_din, cnt_ring_combined)
        
        # right to left traversal
        swizz_minus_cnt_ring = Signal(5)
        sub_mod_26(swizz_minus_cnt_ring, wiring_rtol, cnt_ring_combined)

        # left to right traversal
        swizz_l_minus_cnt_ring = Signal(5)
        sub_mod_26(swizz_l_minus_cnt_ring, wiring_ltor, cnt_ring_combined)

        m.d.sync += self.dout.eq(
            Mux(self.ltor,
                swizz_l_minus_cnt_ring,
                swizz_minus_cnt_ring,))

        return m
            

class Reflector_B(wiring.Component):
    wiring = 'YRUHQSLDPXNGOKMIEBFZCWVJAT'

    din: In(5)
    dout: Out(5)

    def elaborate(self, platform):
        m = Module()

        mapping = [ord(c)-65 for c in self.wiring]

        Wiring = Array(mapping) # right_to_left mapping
        
        m.d.comb += self.dout.eq(Wiring[self.din])

        return m


if __name__=='__main__':
    from amaranth.back import verilog
    top = Rotor()
    with open('am_rotor.v', 'w') as f:
        f.write(verilog.convert(top))