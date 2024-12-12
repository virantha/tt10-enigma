#      -- 0 --
#     |       |
#     5       1
#     |       |
#      -- 6 --
#     |       |
#     4       2
#     |       |
#      -- 3 --


from amaranth import Module, Signal, Const, Array, Mux, unsigned
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out


class SevenSegmentAlpha(wiring.Component):

    din: In(5)   # The letter A-Z (0-25)
    dout: Out(8) # The uo_out to drive the 7-segment display, 
                 # uo_out[7] is the dot which we blink ~2Hz

    def __init__(self):
        self.create_table()
        super().__init__()
    
    def create_table(self):
        """
         _           _  _  _           _     _        _  _     _                    _
        |_||_  _  _||_ |_ |  |_||    ||_ |      _  _ |_||_| _ |_ |_    | || ||_ |_| _|
        | ||_||_ |_||_ |  |_|| ||  |_|| ||_ | || ||_||    ||   _||_ |_|  | _   | _||_
        """
        self.letters = {
            'A': 0b1110111,
            'B': 0b1111100,
            'C': 0b1011000,
            'D': 0b1011110,
            'E': 0b1111001,
            'F': 0b1110001,
            'G': 0b0111101,
            'H': 0b1110110,
            'I': 0b0110000,
            'J': 0b0011110,
            'K': 0b1110101,
            'L': 0b0111000,
            'M': 0b0010101,
            'N': 0b1010100,
            'O': 0b1011100,
            'P': 0b1110011,
            'Q': 0b1100111,
            'R': 0b1010000,
            'S': 0b1101101,
            'T': 0b1111000,
            'U': 0b0011100,
            'V': 0b0100110,
            'W': 0b0101010,
            'X': 0b1100100,
            'Y': 0b1101110,
            'Z': 0b1011011,
        }

        self.letters_map = Array(list(self.letters.values()))

    def elaborate(self, platform):
        m = Module()

        # 7-segment decoder
        m.d.comb += self.dout[0:7].eq(self.letters_map[self.din])

        m.d.comb += self.dout[7].eq(0)

        return m


    # Debug functions to print out segments on screen
    def _get_str(self, disp:int):
        str_locations = [1,6,10,9,8,4,5]
        segments = list(" _ \n|_|\n|_|")
        binary = f'{disp:07b}'[::-1]
        for i in range(7):
            if(binary[i]=='0'):
                segments[str_locations[i]]=' '
        return ''.join(segments)

    def emit(self, my_word=None):
        if not my_word:
            # Cycle through letters
            for letter, disp in self.letters.items():
                print(f"{letter=}")
                print (self._get_str(disp))
        else:
            letter_disp = []
            for letter in my_word:
                str_repr = self._get_str(self.letters[letter])
                letter_disp.append(str_repr.splitlines())
                print(str_repr)
            for disp in zip(*letter_disp):
                print(''.join(disp))

if __name__=='__main__':
     m = SevenSegmentAlpha()
     m.emit()
     m.emit("HELLO")
     m.emit("EXIT")
     m.emit("CLOCK")
     m.emit("WOLVES")
     m.emit("ABCDEFGHIJKLMNOPQRSTUVWXYZ")




