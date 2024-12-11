from amaranth import Signal, Module, unsigned, Mux, Instance, Array, ClockSignal
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out
from amaranth.lib.memory import Memory

from src.defines import PLUG_LIMIT

class Latch(wiring.Component):

    d: In(1)
    q: Out(1)      
    en: In(1)

    def elaborate(self, platform):
        
        return Instance("d_latch",
                        i_d = self.d,
                        i_clk = self.en,
                        o_q = self.q,
        
        )
        # if True:
        #     return Instance("sky130_fd_sc_hd__dlxtp",
        #                 i_D = self.d,
        #                 i_GATE = ClockSignal(),
        #                 o_Q = self.q,
        #     )

class Plugboard(wiring.Component):
    """In the ENIGMA, the plugboard allowed up to 10 keys to be swapped with a different key.

       So, for example, if a wire was plugged into A and N, that would swap A and N coming into
       the machine right after the keyboard, and again (if the generated cipher character was an
       A or an N) before going into the lamp board.

       We implement this essentially as a 26-entry register file.  In the case where there
       are no wires in the plugboard (no swaps), each entry equals its address. ( 0->0, 1->1, etc)

       IF want to implement the AN plug, then we write 13(N) to address 0(A), and write 0 to 
       address 13.

       The forward path from the keyboard is one read port, and the reverse coming out of the
       machine is another read port.
    """

    enable: In(1)    # If this is low, then the in just gets passed to the out
    
    # Mux between the "left to right" or "right to path" side
    is_ltor: In(1)
    in_ltor : In(5)
    in_rtol : In(5)

    out: Out(5)

    wr_data: In(5)    # Used for both wr_addr and wr_data
    wr_data_en: In(1)
    wr_addr_en: In(1)

    def __init__(self):
        self.plug_limiter = Signal(5)  # Counter to keep track of plugs
        super().__init__()

    def elaborate(self, platform):
        m = Module()
    
        # Array of 5 columns of 32-rows 
        self.mem = mem = Array([Signal(5) for i in range(26)])

        bits = [[0]*5 for i in range(26)]
        for i in range(26):
            for j in range(5):
                m.submodules[f'bits_{i}_{j}'] = bits[i][j] = Latch()
                # Connect the memory signals
                m.d.comb += mem[i][j].eq(bits[i][j].q)

        # Make the write like a wordline/bitline
        wl = [Signal(1) for i in range(26)]
        for i in range(26):
            for j in range(5):
                m.d.comb += bits[i][j].d.eq(self.wr_data[j])
                m.d.comb += bits[i][j].en.eq(wl[i])

        addr = Signal(5)
        read = Signal(5)

        # Counter to store address to write to
        cnt = Signal(5)
        with m.If(self.wr_addr_en):
            m.d.sync += cnt.eq(self.wr_data)

        # Artificial plug wire limiter to meet key length requirements 
        # for tinytapeout 
        # Only allow a new plug if plug count < 2*limit
        # to account for two ends of the wire
        allow_plug = Signal(1)
        m.d.comb += allow_plug.eq((self.plug_limiter>>1) < (PLUG_LIMIT))

        with m.If(self.wr_data_en & (cnt!=self.wr_data)):
            with m.If(allow_plug):
                m.d.sync += self.plug_limiter.eq(self.plug_limiter+1)

        # Only allow a write to the plugboard if allow_plug is true
        with m.If(self.wr_data_en & allow_plug):
            for i in range(26):
                m.d.comb+= wl[i].eq(cnt==i)



        with m.If(self.is_ltor):
            m.d.comb += addr.eq(self.in_ltor)
        with m.Else():
            m.d.comb += addr.eq(self.in_rtol)

        m.d.comb += [ 
            read.eq( mem[addr] ),
            self.out.eq( Mux(self.enable, read, addr) )
        ]

        return m


if __name__=='__main__':
    from amaranth.back import verilog
    pb = Plugboard()
    filename = 'src/am_pb.v'
    with open(filename, 'w') as f:
        f.write(verilog.convert(pb))
        print(f'Wrote {filename}')

