from amaranth import Signal, Module, unsigned, Mux, Instance, Array, ClockSignal
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out
from amaranth.lib.memory import Memory

class Switch2x2(wiring.Component):
    a: In(2)
    addr: In(1)

    out: Out(2)

    scan_in: In(1)
    scan_en: In(2)
    scan_out: Out(1)

    def __init__(self):
        self.swap = Signal(1) # State bit
        super().__init__()

    def elaborate(self, platform):
        m = module()

        sel = Signal(1)
        in1 = Signal(1)

        m.d.comb += [
            self.scan_out.eq(self.swap), # Scan out
            sel.eq(Mux2(self.swap, ~self.addr, self.addr)),
            in1.eq(self.a[0] | self.a[1])
        ]

        with m.If(self.sel):
            self.out[1].eq(in1)
            self.out[0].eq(0)
        with m.Else():
            self.out[0].eq(in1)
            self.out[1].eq(0)

        m.d.comb += self.out[0].eq()

        with m.If(self.scan_en):
            m.d.sync += self.swap.eq(self.scan_in)
        
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

    en: In(1)    # If this is low, then the in just gets passed to the out
    in_ltor : In(5)
    out_ltor: Out(5)

    in_rtol : In(5)
    out_rtol: Out(5)

    wr_data: In(5)    # Used for both wr_addr and wr_data
    wr_data_out:  Out(5) # End of scain chain
    wr_data_en: In(1)
    wr_addr_en: In(1)

    def __init__(self):
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


        # chain the input to the output for now for the write
        # for i in range(9):
        #     for j in range(5):
        #         m.d.comb += bits[i+1][j].d.eq(bits[i][j].q)
        # for j in range(5):
        #     m.d.comb += bits[0][j].d.eq(self.wr_data[j])
        #     m.d.comb += self.wr_data_out[j].eq(bits[9][j].q)
        
        # Make the write like a wordline/bitline
        wl = [Signal(1) for i in range(26)]
        for i in range(26):
            for j in range(5):
                m.d.comb += bits[i][j].d.eq(self.wr_data[j])
                m.d.comb += bits[i][j].en.eq(wl[i])

        cnt = Signal(5)
        with m.If(self.wr_data_en):
            for i in range(26):
                m.d.comb+= wl[i].eq(cnt==i)

            # with m.Switch(cnt):
            #     with m.Case(0):
            #         m.d.comb+=wl[0].eq(1)
            #     with m.Case(1):
            #         m.d.comb+=wl[1].eq(1)
            #     with m.Case(2):
            #         m.d.comb+=wl[2].eq(1)
            #     with m.Case(3):
            #         m.d.comb+=wl[3].eq(1)
            #     with m.Case(4):
            #         m.d.comb+=wl[4].eq(1)
            #     with m.Case(5):
            #         m.d.comb+=wl[5].eq(1)
            #     with m.Case(6):
            #         m.d.comb+=wl[6].eq(1)
            #     with m.Case(7):
            #         m.d.comb+=wl[7].eq(1)
            #     with m.Case(8):
            #         m.d.comb+=wl[8].eq(1)

        m.d.comb += [
            # First and second read port
            self.out_rtol.eq(
                Mux(self.en, mem[self.in_rtol], self.in_rtol),
            ),
            self.out_ltor.eq(
                Mux(self.en, mem[self.in_ltor], self.in_ltor),
            ),
        ]
        
        with m.If(self.wr_addr_en):
            m.d.sync += cnt.eq(self.wr_data)
        
        return m


if __name__=='__main__':
    from amaranth.back import verilog
    pb = Plugboard()
    filename = 'src/am_pb.v'
    with open(filename, 'w') as f:
        f.write(verilog.convert(pb))
        print(f'Wrote {filename}')

