#from itertools import batched 
"""
    Each wheel is basically pairs of mappings

    1 <-> 4
    2 <-> 22 

    etc

    First, we need to find input position signal comes in on (contact point)
    Then, we need to find the offsetted position on the wheel to find which pair is connected


"""

letter_to_num = {chr(i): i - ord('A') for i in range(ord('A'), ord('Z') + 1)}  # Map letter to num
num_to_letter = lambda x: chr(x+65)  # noqa: E731
def rotate_left(l, num):
    num = num % len(l)
    return l[num:]+l[:num]

class Rotor:
    base = 'ABC'
    def __init__(self, place, start_pos:str='A', ring_setting:int = 0):
        self.name = self.__class__.__name__
        self.place = place

        # Set the starting offset
        self.start_pos = letter_to_num[start_pos]

        self.ring_setting = ring_setting

        # Adjust wiring for ring_setting.  We're basically rotating the wiring connected to the right side of the rotor
        #self.wiring_ring=self.wiring
        self.wiring_ring = rotate_left(self.wiring, -ring_setting)

        # Generate dicts for both a R->L and L->R lookup
        self.right_to_left = [letter_to_num[x] for x in self.wiring_ring]

        self.left_to_right = [0]* 26
        for i, letter in enumerate(self.wiring_ring):
            self.left_to_right[letter_to_num[letter]] = i
        self.ptr = (self.start_pos) % 26

    def inc(self):
        at_turnover = self.is_at_turnover()
        self.ptr = (self.ptr + 1) % 26
        return at_turnover
    
    def is_at_turnover(self):
        return num_to_letter(self.ptr) == self.turnover

    def rtol(self, right:int ):
        
        # "right" is the absolute position (0-25) that the input
        # is arriving on.  However, the dial has rotated by self.ptr
        # tics, so we need to add these two to get the actual number
        # that is at the location of the input
        contact_point = (right + self.ptr) % 26

        # Now, figure out where on the rotor the exit point is based
        # on the wiring pattern inside the rotor
        result = self.right_to_left[contact_point]

        # Then, again, we need to adjust for the rotor's rotation and
        # subtract its tics of rotation to get the absolute contact 
        # point the signal is going to exit from on the left
        result = result - self.ptr
        
        # If the ring setting is used, then the right side of the rotor
        # with the wiring pattern has been futher shifted wrt to the left side
        # of the rotor.  Therefore, we need to add in that extra offset
        # as well, to get the final exit point.
        result = result + self.ring_setting
        result = result % 26

        self.message(right, result, r_to_l=True)
        return result

    def ltor(self, left:int ):
        # The right side of the rotor including wiring has rotated by the ring setting
        # But the left side contacts do not rotate.  Therefore we need to subtract out the ring setting
        # to model the fact that the wiring pattern has rotated with respect to the left contacts, so we follow the proper wire going from the left
        # side to the right
        contact_point = (left + self.ptr - self.ring_setting) % 26
        
        # Find the exit point on the right side wrt to the rotor through
        # the wiring pattern
        result = self.left_to_right[contact_point]
        # Adjust for the rotation of the rotor. This is the absolute exit
        # point
        result = result - self.ptr #+ self.ring_setting
        
        result = result % 26

        self.message(left, result, r_to_l=False)
        return result

    def message(self, in_offset, out_offset, r_to_l):
        out_letter = chr(out_offset+65)
        in_letter = chr(in_offset+65)
        if r_to_l:
            print(f'\t[{self.place}] - {self.name}: {self.ptr} => {out_offset}({out_letter})<-{in_offset}({in_letter})')
        else:
            print(f'\t[{self.place}] - {self.name}: {self.ptr} => {in_offset}({in_letter})->{out_offset}({out_letter})')



class Rotor_I(Rotor): 
    wiring = 'EKMFLGDQVZNTOWYHXUSPAIBRCJ'
    turnover = 'Q'
    

class Rotor_II(Rotor): 
    wiring = 'AJDKSIRUXBLHWTMCQGZNPYFVOE'
    turnover = 'E'

class Rotor_III(Rotor): 
    wiring = 'BDFHJLCPRTXVZNYEIWGAKMUSQO'
    turnover = 'V'

class Reflector_B(Rotor):
    wiring = 'YRUHQSLDPXNGOKMIEBFZCWVJAT'


class Enigma:

    ROTORS = { 
        'I': Rotor_I,
        'II': Rotor_II,
        'III': Rotor_III,
    }
    REFLECTORS = { 
        'A': None,
        'B': Reflector_B,
    }

    def __init__(self, rotors:list[str], reflector:str):
        """ rotors are 0 (rightmost) to 2 (leftmost)
        """
        self.rotors = [self.ROTORS[rotor](i, start_pos, ring_setting) for i,(rotor, start_pos, ring_setting) in enumerate(rotors)]
        self.num_rotors = len(self.rotors)
        self.reflector = self.REFLECTORS[reflector](3)

        self.next_is_double_step = False


    def cipher(self, letter):
        # Convert letter from keyboard to its number
        start = letter_to_num[letter]  # Left side of keyboard interface (ETW)

        turnover = self.rotors[0].inc()
        if turnover: # First wheel went over
            self.rotors[1].inc()
            if self.rotors[1].is_at_turnover():
                self.next_is_double_step = True
        elif self.next_is_double_step:
            print("DOING DOUBLE STEP")
            turnover = self.rotors[1].inc() # Do the double step
            assert turnover
            self.next_is_double_step = False
            self.rotors[2].inc()
        
        l = start
        for rotor in self.rotors:
            l = rotor.rtol(l)
        l = self.reflector.rtol(l)
        for rotor in self.rotors[::-1]:
            l = rotor.ltor(l)
        end = num_to_letter(l)
        print(f'Cipher {letter} -> {end}')
        return end


    def process_message(self, message:str):
        """Convert a string into cipher text.
           Eliminate white space 
        """
        output_list = []
        for i, c in enumerate(message):
            c = c.upper()
            if c >= "A" and c <= "Z":
                print(f'{i} ', end='')
                t = self.cipher(c)
                output_list.append(t)
        print(f'Plaintext: {message}')
        print(f'Output:    ')
        #for chunk in batched(output_list, 5):
            #print(f'{"".join(chunk)} ', end='')
        print()
        output = ''.join(output_list)
        print(output)
        return output




if __name__ == '__main__':
    e = Enigma([('I', 'A', 1), ('II', 'A', 0), ('III', 'A',0 )], 'B')
    e.process_message(' Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse ut convallis augue, vitae tincidunt tortor. Morbi euismod Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse ut convallis augue, vitae tincidunt tortor. Morbi euismod')
    # rot = [Rotor_I(i) for i in range(3)]
    # reflector = Reflector_B(3)
    # rot[0].inc()
    # l = rot[0].rtol(0)
    # l = rot[1].rtol(l)
    # l = rot[2].rtol(l)

    # l = reflector.rtol(l)
    # l = rot[2].ltor(l)
    # l = rot[1].ltor(l)
    # l = rot[0].ltor(l)

    # rot[0].inc()
