from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out
#from amaranth.lib.coding import Decoder
from amaranth.lib.enum import Enum
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

    in_ltor : In(5)
    out_ltor: Out(5)

    in_rtol : In(5)
    out_rtol: Out(5)

    wr_data: In(5)    # Used for both wr_addr and wr_data
    wr_data_en: In(1)
    wr_addr_en: In(1)

    def __init__(self):
        super().__init__()

    def elaborate(self, platform):
        m = Module()
    
        m.submodules.memory = memory = \
            Memory(shape=unsigned(5), depth=26, 
                init=[  0, 1,2,3,4,5,6,7,8,9,10,11,12, 13,
                        14,15,16,17,18,19,20,21,22,23,24,25
                    ]
            )
        # 2 asynchronous read ports
        rd_port_rtol = memory.read_port(domain="comb")
        rd_port_ltor = memory.read_port(domain="comb")

        # 1 synchronous write port
        wr_port = memory.write_port()

        # The internal counter to keep track of write address when 
        # setting the plugboard
        cnt = Signal(5)

        # Plugboard traversal
        m.d.comb += [
            rd_port_rtol.addr.eq(self.in_rtol),
            rd_port_ltor.addr.eq(self.in_ltor),
            self.out_rtol.eq(rd_port_rtol.data),
            self.out_ltor.eq(rd_port_ltor.data),
        ]
        
        # Writing to the Plugboard (setting the pairs)
        m.d.comb += wr_port.en.eq(self.wr_data_en)
        m.d.comb += wr_port.addr.eq(cnt)
        m.d.comb += wr_port.data.eq(self.wr_data)

        with m.If(self.wr_addr_en):
            m.d.sync += cnt.eq(self.wr_data)
        return m
