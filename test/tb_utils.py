
from enigma import Enigma as EnigmaPy
from random import randint

plain = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aliquam tempus justo ac
metus dignissim condimentum. Praesent consectetur dapibus nunc nec venenatis.
Nulla facilisi. Aenean vitae orci metus. Donec sed odio rutrum, pharetra neque
nec, facilisis nibh. Vestibulum justo lacus, faucibus sed purus eu, interdum
ultricies lorem. Nullam non ante sapien. Vivamus dictum consectetur lectus, sed
sollicitudin lorem volutpat et. Ut auctor libero non lorem blandit eleifend.
Quisque venenatis diam enim, id accumsan leo tincidunt sit amet. Nam ex nisi,
maximus nec arcu eget, hendrerit luctus mauris. Morbi et est molestie, feugiat
lacus in, hendrerit velit. Sed bibendum vulputate ullamcorper. Duis venenatis
odio sit amet vestibulum facilisis. Quisque tincidunt metus vel arcu blandit
euismod. Donec scelerisque blandit neque, sed lacinia nunc eleifend efficitur.

Morbi erat nunc, vulputate ac mi ut, accumsan tincidunt lectus. Nunc ullamcorper
vel justo quis tempus. Ut ultrices efficitur elementum. Nullam non justo ut enim
blandit feugiat. Curabitur a purus enim. Donec est eros, convallis sit amet
convallis non, iaculis in metus. Nulla consectetur eros eget ligula efficitur,
nec tincidunt lorem efficitur. Vivamus viverra sodales libero.

Integer iaculis accumsan vulputate. Morbi interdum mattis mattis. Nullam eget
orci a mi lacinia scelerisque eu ut velit. Sed vitae eros et sem malesuada
laoreet et at dui. Phasellus maximus arcu libero, eu sagittis turpis
sollicitudin et. Proin aliquam metus dui, vehicula rutrum velit placerat
consequat. Vivamus sollicitudin ex id eros congue, id vehicula orci feugiat.

Mauris dictum viverra bibendum. Integer sed turpis non tortor tempus posuere a
ac arcu. Donec ultricies ligula eget urna maximus placerat eget at quam. Aliquam
euismod accumsan justo ac ullamcorper. In eleifend est nec ornare maximus.
Aliquam mollis et quam vitae dapibus. Vestibulum suscipit faucibus libero.
Vestibulum auctor augue fermentum risus volutpat, ac rhoncus erat iaculis.
Quisque laoreet purus ultrices mauris lobortis, ut accumsan leo venenatis. Sed
est nibh, laoreet et turpis nec, dictum maximus nulla. Pellentesque a lorem sed
lacus consequat aliquet ac non nulla.

Donec eleifend laoreet nisi, quis dapibus purus faucibus et. Morbi consequat
erat nec ex sodales, eget venenatis lorem venenatis. Pellentesque id felis
lobortis, molestie turpis a, elementum massa. Curabitur in egestas augue, a
tincidunt ipsum. Fusce hendrerit vehicula ipsum, nec pellentesque elit fringilla
sit amet. In hac habitasse platea dictumst. Etiam hendrerit consequat ex vitae
molestie. Proin gravida suscipit nibh vel blandit.  """


def to_letter(a:int):
    return chr(a+65)

def to_val(c:str):
    assert len(c)==1
    return ord(c)-65

def rnd_int():
    return randint(0,25) 

def get_fixed_rotor_setting():

    rotors = [
        {'type': 'I',
         'start': to_letter(15),
         'ring': 18
        },
        {'type': 'II',
         'start': to_letter(5),
         'ring': 5 
        },
        { 'type': 'III',
         'start': to_letter(1),
         'ring':24 
        },
    ]
    # Plugboard
    return rotors
    
def get_fixed_plugboard_setting():
    plugboard = [ "AN", "DE", "ZB", "GX", "HQ"]
    return plugboard

def get_random_rotor_setting():

    # Create the golden results using the python simulator
    rotors = [
        {'type': 'I',
         'start': to_letter(rnd_int()),
         'ring': rnd_int(),
        },
        {'type': 'II',
         'start': to_letter(rnd_int()),
         'ring': rnd_int(), 
        },
        { 'type': 'III',
         'start': to_letter(rnd_int()),
         'ring': rnd_int(), 
        },
    ]
    
    return rotors

def get_random_plugboard_setting():
    # Plugboard
    plugboard = []
    for i in range(10):
        if randint(0,9) > 2:
            # with 70% probability
            a = to_letter(rnd_int())
            b = to_letter(rnd_int())
            plugboard.append(f'{a}{b}')
    return plugboard

def get_golden_cipher(rotors, plugboard, plain_text):
    my_enigma = EnigmaPy(
        [ list(x.values()) for x in rotors ],
        'B', # Reflector
        plugboard = plugboard
    )
    golden = my_enigma.process_message(plain_text)
    # Remove spaces from result
    golden = golden.replace(' ', '')
    return golden