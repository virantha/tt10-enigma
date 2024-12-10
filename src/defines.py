from amaranth import unsigned
from amaranth.lib.enum import Enum

Rotors = {
    'I': 0,
    'II': 1, 
    'III': 2,
    'IV': 3,
    'V': 4,
}
class Cmd(Enum, shape=unsigned(3)):
    NOP = 0
    LOAD_START = 1
    LOAD_RING = 2
    RESET = 3
    ENCRYPT = 4
    LOAD_PLUG_ADDR = 5
    LOAD_PLUG_DATA = 6
    SET_ROTORS = 7

class En(Enum, shape=unsigned(2)):
    # Just to make sure I'm picking the proper rotor (rotor 0 = 1, rotor 1 = 2, rotor 2 = 3)
    NONE = 0
    ROTOR0 = 1
    ROTOR1 = 2
    ROTOR2 = 3