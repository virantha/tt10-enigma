from amaranth import Signal, Module, unsigned, Mux
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out
from amaranth.lib.memory import Memory

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
    

        self.a = a = [Signal(5) for i in range(10)] 
        self.b = b = [Signal(5) for i in range(10)] 
        
        self.rtol = rtol = [Signal(5) for i in range(21)]
        ltor = [Signal(5) for i in range(21)]

        m.d.comb+= [
            rtol[0].eq(self.in_rtol),
            self.out_rtol.eq(rtol[20]),
            #self.out_rtol.eq(
                #Mux(self.en, rtol[20], self.in_rtol) ),

            ltor[0].eq(self.in_ltor),

            self.out_ltor.eq(ltor[20]),
            #self.out_ltor.eq(
                #Mux(self.en, ltor[20], self.in_ltor)),

            self.wr_data_out.eq(b[9])
        ]

        for i in range(0,10):
            m.d.comb += rtol[i+1].eq   ( Mux( a[i]==rtol[i], b[i], rtol[i]) )
            m.d.comb += rtol[i+10+1].eq( Mux( b[i]==rtol[i], a[i], rtol[i+10]))

            m.d.comb += ltor[i+1].eq   ( Mux( a[i]==ltor[i], b[i], ltor[i]) )
            m.d.comb += ltor[i+10+1].eq( Mux( b[i]==ltor[i], a[i], ltor[i+10]) )


        # Now create the writable flops in scan chain
        with m.If(self.wr_data_en):
            for i in range(9):
                m.d.sync += self.a[i+1].eq(self.a[i])
                m.d.sync += self.b[i+1].eq(self.b[i])
            m.d.sync += b[0].eq(a[9])
            m.d.sync += a[0].eq(self.wr_data)

        
        return m


if __name__=='__main__':
    from amaranth.back import verilog
    pb = Plugboard()
    filename = 'src/am_pb.v'
    with open(filename, 'w') as f:
        f.write(verilog.convert(pb))
        print(f'Wrote {filename}')

