from amaranth import Const, Cat, unsigned
from amaranth.sim import Simulator

from src.top import Enigma
from src.fsm import Cmd
from .enigma import Enigma as EnigmaPy

dut = Enigma()

plain = ' Lorem ipsum dolor sit amet, consectetur adipiscing elit. '
plain = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse ut convallis augue, vitae tincidunt tortor. Morbi euismod Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse ut convallis augue, vitae tincidunt tortor. Morbi euismod'
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

cipher = 'ILFDFARUBDONVISRUKOZQMNDIYCOUHRLAWBRMPYLAZNYNGR'
cipher = 'ILFDFARUBDONVISRUKOZQMNDIYCOUHRLAWBRMPYLAZNYNGRMNWXXWSRNMWNHNHCPFKHNYGFXPGZGOILEBYIMOYZCXCLHBECKHCNSOLZPLSCATLSBNIBSXEQVDUYIZLBNAVQZSKJMNPUZWGCXQFTLVJKNKABNKCAXBIPJNNAJRZPCXMXMRMOWNPWZTUCWPRTZCOPIIXJKCQSHVBKZBSRC'
cipher = 'ILFDFARUBDONVISRUKOZQMNDIYCOUHRLAWBRMPYLAZNYNGRHZRJREZMPSXNZDGTQTRZYHWFTWVNACCPJLAYTOXYVCAAZREZINTILISILXKMHRVUQMKOQIPPMQPHYMEBTLICFDMWGQJQWOZMNAQTMIIAGBPRGXCTCFSLJFBZZDRGLFWNFMUUCPWBQDEZSFPDCXJINBYXSMVGNVZOAPMYBRZMWPBVAYCIWEAAAGMQWZOOXLKNEJNJTNOTOYIZPQYRTWSWBGRGBZEVBNVEHLCMOYFEIVYVVQVJMDLUJPFTLJDBZFSXCGIVFXMSBGZYAKKQNAICKRLBXVQPGDLVZXSZHLBVYBKNFFUXXZOMDVAZZUKFKZAQWNRATNVHXPISNYZBJALAGMICMFLTELWHLQHYFSONCJSSCAJCUHLWCLDPCIUQWGBEYSXWPKWVJRWQYSCBDYSIBLLIPEITRTBGYWRCJRIIVMAWDGVIUPHFJDZEIVNRYEUUXSVYUDUJVOUIXKBNIWDWAVMBZWNORIZMTMBJUYSWMEDVWUULFVOSJNVYBTKRKNJZMEZUNAUKZUTDHJUGTIEFZMKNEEZVOFURABZXZLGNSOQSEGMHDOUMUDYXEFCFAENFTYVDBVNAUPHDRXJRMQQLUPHKPLBTUCQLRZEAFFGLABXJTRUFSDBSLOMJKBJLJRRFVIWUJSVETVSKVBGNILJXUYZTPWDLCBUXUKXMUVPPDVQORGVKOAXFOHIGKSJBCZRLVEGPBIVHZNKHVVRANETZNDXESNTKJWXKBKYRJMFRSAUMLCCWJEAFGDIVBLESQJQNAKCPHONTRQPWDEQKZMFOFPFESXWWOZQORYQPAXQEAIFESUQVJBCVDSBPNAZUDHMRBYIBBSXZCDZFIXTFGUYYPYKKRKVNVGZJWGBSZCKUBNINANETSFHQMJPJHWCHXODDVMLOUZFVLDAUQZFQUBOLQUSUQRQFKOYUZUJWXPGJCZNKKDOBSZDNUCKHBLRWJYWPZYOTJCFBKOHWZOJUVWRJFUERNAIVWUJGFBVVPDIWDJQYFHRQZQKNHLUKYTVJVYMEHFGNDAGHSQUTNYCUKHJITRUKCDYJJANHBABHDNPWMQAOAZBSHAHAFWLRJYDBHECFAOAZVYYBYESJQDYIIWJFGNVJRHWZWWNGPRQWFFNDVQMQJTTFSJFSXXKYXCPQPWWUUTZELKWDIEORLXRMQYDARWZAHPOZRBZBXHQJTRSBCNWQLMJRFBLAIYGRDYDWRPWLNENZBZGLIXRGUAWGRHMHVZQVDOXABXVZLDHPLTAAVRMSHNICOMNRPAJCUEPUTEIAKZTFNUVOHQBYHDORJDCJNXYZTLPONGQKTOMEZPTIQSKBYUKHINOQBPZBZWZEWSRIZOFMCTVKDSAAORLVJODMBPPGULENTFYMJIBVLZUEPEQTDYMEFPJFPRYFOGSMTMJIFMMSLLTFMIHUPOQRTDRRSXMTUUYFEYDVTKBYUSUEHUMPHSTFLAIVPTWQNETWFDFJGENGMBBJFTEWIAFHLCLNOLTNPHOXBISKNSHITMLRYLQRJZKQPOTJMATIEUDMUEOCHVWTSQLMNKOIZYKKRNDTQOPKTSMVMWWJEQQECXAHVMGDWGUQHVSQMPWAXOAKMOQVEIJBUAAFBEJWXFYKNPVCGVTAYKPHVETIJRWXFMKFQGAROKPVHUNGMOSAWPHOAJVYDAQXCVOHKHYETSEPCFWMWCJECXZYNCFYODGRJMSDFLYWDPFFYJGSBZLZKBFPFSEQOHUKWFXHTBNKMKYQJNSOFHZHSPNBCUSMPGPIHBQOXFWCUNHWNPMONMUCAVWFSUGKOVRXSANPDROSLVWLLXTMRUEKUYBRDTFMBMUCMIFXHQNTGMWHYRUNYWGOSGHXSHUJXTVTCTMKPSNIXUJIGRXFCBEPZDSXKJUMUWFIAYGSALRMGQPFAABVUHHBGIOPMDIJPPICDPJSXBVLBVNTVVSRVIZPKWBMKTYFTHNNXULFYVDYHEZJVTUFJNTZWCROSTJCOUHQIFBGDDCHEQBVBVFPDCFWTYQPZXAKNDIKMFWDNQKWFCNXYUXPPEGPFNFQZJLWBBTVDLNZGRPNMRJALABORXTGYLLKRIEAPGTMHHTAHMXAJDPEKHWXJAGRNXKURHKCCHAWXTTMUCCTLG'

# I=E, II=Y, III=R (ring setting)
# I=5, II=8, III=19 (start position)
cipher = 'GCOSNVFXGFJVKRMICESOMEBYHOJEFTJIBBZYKDUMWAWDYORROQCDWSGXXVNXAODXJDHWRRHQSEFOHZNBOTZIQZEFIRTJISYJVOZLSYPZVPYOJEDQTZDCHWMOHPBYPEXKWSOCDFQGPKQTORQRGVLDXBCNTDFJBHQUHQPLDFAOUWUHEWITQLQCYRYMKDZTVPWHNHTANUDKLIONAECTTUZSVEIWHSDNEYRNEXTPPVLOEAEFHMNLFIIHNTPGOZWCVEWWMJAPSCLWWFXDVTUNBLTXYYEEYMVJZGLMKAVRSEYLGDDEUMLZNXULHGQNLYLFSHZDCSNXJGLPYCABVYXCJXYQCQARGFLKGBQXGANINDIDQSDGCJEJQQBEJYPHQJYGOYREHQWVYWPILAOOMLQFPZUBGNAHXWIHXIFTZBZWWVUXZHTSPGTMHILEJKXKRZMTBTBQKLASWFUWQXDVRHWNYPOUFHFFVCHVLBBAMBCEUEUBFVUPAHXEQDDTQYVZBQPCPLCAZSFJPFANNAFBLFMWJVHOJTDDVKGNPNDHZPEHQNZVGUGQKXNJGURKHODJHBNLDNJHZSZBDWMZSCVNMRPYQUPSAXQDCAAHRPCUIHELTVQIKRURWXLAQDZANMETUMVJPMQSUOIBHRGZAWFYJLIHUUNJHVZAKXMHDRQCCOJUAXIYKKJAUTDSIGGEVYNRWMZLRHGXKEPBPVAQORZSHLYCFBVMMBHTSBXVZYRLTRGBXYUDYQDEMQHFHBOAJFAIYBXXBSXRPRKQAUTMYIHKBTLCVZSREHSXVXEZCICOGJUAHHRXIWNHAEMNVXLRUJSEOIVURTJGDODIOJWZAYVXZGOMASKNBTTPINTDNBWHPHZBDBNZJDDXYPRTRWXHDRSWMMKFKYVNGANWJNAPJQEWORPDCZRVAKTQZFOBFJWAOWJYVOBGZHWFZDRQBKLAJKEYBOCSLKKQQZLSYEVYVNBLGCMLRLASLQHEJIFUQNVNFNAEPMXRENHKKFFUPPNXQJYKROZHOJEGMQBLLNBXSEORLHGIBJKPGGJDDOJNGHBYNRUNZZLCRDYPIUXSJSVIWYCIVJBXALNZFKAVDSOUCHLNIDFGEWNIQGLVIUKFEQKZCDMLQCLUVUPRQTCSFLHKJJITRXWKRKRGJMRCNCUCUYBNDWWOUJRLBEIBXZETDQJIZUIKXRIHDNYEYVGFTCFDPBMJXGDQXRHZGTFOUHWBVVZIVJVXHWYRYTOITNHXIBIYZGZFLMXWSLMIJKUEPFDRIYWXOYXZRUVTEQMGKPRYBRSVKCBUTVLKSORXEPTFNMCOUJOIBRKEHYZXBKHFNXPOOURFJNCIXRKXIZPHIRWVSVRJBYBJLFEDSLMPNTCUWIUBUAVTILUYXQGRRQMXFQTWFXHRNWUGCVJQDLDUHYRVRQGBHYZBKQWPTVERVIEZXAMQTBOAGXPSBGPBNGXUKLCQNSBARDVYOQHTJWSXQIAQWSKIWYMYXTKYTAYBREOOEOESMAJLWSPCKIDYBNSQLRNFZQTEKALUKZFYJPSPNLGCYPBNGWKLTRGOCCQCBUXJOHGPYQTSXGHYRFAMVXTBVWESDXPMZGTTZDWKDXYVUNVSQJFXEWAYUNBSRCJNFRYMXXSSKTKLTYZDFRCLSAIDQKHJQVOSKRRJXFHMSBYQJEZBDWKGIOVFGUSDVYUNHUGYWODBVYIZCMSXDIQGLEEEHXWDDDIOAOVPVAVLKMKICXEJIPHULVWLEVXTJLUHMHLMDKWOQPDIUFUUSMEHFNVEUNZCLSNCYVOBYUSBKEZDWNGFGTSUABJVPQESRTGSQYWQQGQOUBLVYYGHAPJHTFUYCGYEPUVJNZQJMDDWQDGULNPGVTUQUSKVHRWDDILAWPKIKVHUOENYDCIFIFHSHULEZSDZFGRNLHREDZJCPOOQMJZEZXPGVMEONFFQQPCNAIRQDXXSXZEEBQCRXFIIFPWPXOBAGLWVWXZRNAHBBCUBSWBIOFLOQFJULRTALUTCGCCMSBTWPSYKGWKQHLXRURDYICJJZURROGOUTYPGWJHKDWOEMQPDCNSCTBMMCHCANJFRFIXYKPUZQDUNWDGOZLAFNKUNAMBQTOPCGNECDLEFYVJMKHTBPLQMCOBLEJJZAGIKYILYAXCBWKEHRHKJDMLPNGKTNBTVJGLXQ'

# I=A, II=A, III=A (ring setting)
# I=1, II=1, III=5 (start position)
cipher = 'PLOCQJKRSAEMONHIJHMDKJVESEIRCWKVJIYMZCNTKMTRFCMPPNCVKWZAKGAXOYLPPNNBQOPECFTFJUWQLTLHFRCNKUAQDIFNEHWEDNRYLIYADOYMKMFDOVKHVUPLDKLIYMFRZAHOYEGECZQZPQWSAYTGWYXWTGPCKQVKZGXFETNUMGVMKNQOZLUZGLUGMZHVEATXDGBHONYVESSHNDPKGCCYLWSOWKDHMBZSBHITPBZPHSZMNTZRUQNQZAZTEJGBJFRIWXCXNFHCPJUAVSMQATLRSUXSDWCRGNPQTFYWSOPFCFHZIERXZNMVAORVOESNEKBJMMLZVJKYAJWLFEISVXKLXGZYVQXUDWUVZDUTQEQKVWDQDAXYBYRPMXTJULCKRFVSKNWYSIUHKAIDZLLBMZUGKZJSLVWJBAXIPPVGDBNQULIZQEMACWGXWLAUCLUKHKVOHRYUNLGWBGDMQQLKQXNTCQXGIGOQREDWZWOMHKCFSEOXRDOPVHGOCIATHJWABFSORHFYOJLIMURALWFVEFNXLVHGUZQMWATBTBPUJMRKTVZEFXVJAYTIBKAPRAGYLCRZWKVMUDRZNCGHMTTQJJARNBUOEVFGHAPZGWLVARJKCOKFEWQJXEFEXFGOGKYYJSCQXAKKUPDVRAJZBFYELQLNDMMGFRSZRJMRGGRJITAFPSQPDZNVVJZJGGQEIRLUSDHZLOOCYKBNVPTSZUWTNQFUNMCDFPGNSHKKMOWQNURGKJKSAJIQGHLGJHDEZUGLUNHYWVHQTNBSWURBOICQNDZVNEHFKDNIPJZSLUCHZYDMKKDKOGWXKCIYPBBVJDKNRLTWQEILZCLXHIGLQNNBBIVUQNEJWDNNAFHINHFVMBQSWQGHVRDWZACEGAQAWPJYCDCTAJPLDLIYCIXYYYSTILFRYAUXFJEUUOVLWDCYMSDZZHBZBRPXBYDPAHQGLCZQCIQNREMPXBJXVNHYYOZOYCECCYLRSBPUVOPYLVXUIBOEWZCTGPGCTMJPDYZLULLGZGLYSJVWXMMBTRXZSWZEURCOAVGTLYPNSTAUWLFZUBVIVXGXGLQVWHUSYSYTKJDNVQFBUKHAGQYEWAZHEUZTEHWSXYSXDOIVYCGYHRNLJZXNYEFAFOQEZGQCCADLXKJZWXSDGOKNNZWWCBQNFDRNEQOGWGWKMNGSXYBNJCZIZLPZCMDUSVIXWGETTKDJZOTOCCBTCHCJTIBMACGPBORVVHXLKNSEVGSLNJXAFMXQEQUDLRZAQJPCXZTJZVBHZGBSAMZPVQWLTDOAGIZMXOMLVVIFTZOIOAKJEUWJBPINRZISYENZQRZSDHPBAEPMNWOOLZNEYHWHOMTRWTUMQVWHCNZGKSGTAKYXIMUUWJZHSQPSLWPPUILLOZVJZAJUFONOUBPAUSZAYDVFXJICRNHWOGUSKJHXRRTPRUCSQRYRXVXNQJKPNIPCLXVXAZEPMOVZJLRZRLXBYHYXAZDXLYABGWBAAFACDLFWANJZZQTJPKTGSLAMSHZJXESROXNZMKUTWIXAKBQVMFRTTTWZGZGNPRPHEJSEWIYZKYSNYHDVPAWIRSOZUJDUGONAMPATIVTFHCCYZHPQJXLWKVZVFHADQPBAYYQYWYJAQKOKBGRKYBZIAPCHXWBXBTERFSDEDZUWLKHBXNOHTUMKNZSLXMSITGLGOBBRWGTIGDCMRZPOAASRLAJGFWVREGPKCRHFVYVUWTEUTZELKZUTQORVOJDKZSFQCPPWJQCSRSOVSDQXOPYNPMAHLGLDTUEBXWVBHXFNUOEOOJMHQHMWPSNDBSKVQPPUZCVKCDXUMZYZOGKWEPBIUFYSXDZVCEVNEQEHIGLIEUBQVQGMCDSQHLXHEWMFYAIVAVEAFPWVSJPOWBIKJRJDWAKXLZRKDFGRTEMBATSQYGECHMSPAWVMJOBGOVDCBIMXHARRBUYUKMZMTOQQKVXOVNTULGRMCPDUYUOOBEHKTQTTYJULSXFOULFWGYYTTFJYWMZNOKFUDMLKFDYZXAINWBSKBJKEXXASWINSCSOZXIWCMMUZECETDAYNATDCNWUZEUVEQNUKXUBQUHXFPMYVEVNFGKLRQFBNFHTCRBXBDOQNUEYSSZBFVRNEQOSQNBKJLZKGAKTGAAQRJKGWTDYEVAETBIUCLYIJTUQBL'

async def clk(clk_ctx, cycles:int=1):
    for i in range(cycles):
        await clk_ctx.tick()

async def ready(clk_ctx):
    await clk_ctx.tick()
    while clk_ctx.get(dut.fsm.ready)==0:
        await clk_ctx.tick()

async def bench(ctx):

    def to_letter(a:int):
        return chr(a+65)

    # Create the golden results using the python simulator
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
    def to_val(c:str):
        assert len(c)==1
        return ord(c)-65

    my_enigma = EnigmaPy(
        [ list(x.values()) for x in rotors ],
        'B', # Reflector
        plugboard = [ ('A', 'N')]
    )
    golden = my_enigma.process_message(plain)
    # Remove spaces from result
    golden = golden.replace(' ', '')

    await ready(ctx)

    cmd = Const(Cmd.LOAD_START)
    val = Const(to_val(rotors[0]['start']), unsigned(5))
    ctx.set(dut.ui_in, Cat(val,cmd) )     # Rotor 0
    
    await ready(ctx)

    val = Const(to_val(rotors[1]['start']), unsigned(5))  # Rotor 1
    ctx.set(dut.ui_in, Cat(val,cmd) )     

    await ready(ctx)

    val = Const(to_val(rotors[2]['start']), unsigned(5))  # Rotor 2
    ctx.set(dut.ui_in, Cat(val,cmd) )     

    await ready(ctx)
    
    cmd = Const(Cmd.LOAD_RING)
    val = Const(rotors[0]['ring'], unsigned(5))
    ctx.set(dut.ui_in, Cat(val,cmd) )    

    await ready(ctx)

    val = Const(rotors[1]['ring'], unsigned(5))
    ctx.set(dut.ui_in, Cat(val,cmd) )    

    await ready(ctx)
    val = Const(rotors[2]['ring'], unsigned(5))
    ctx.set(dut.ui_in, Cat(val,cmd) )    

    await ready(ctx)

    # #ctx.set(dut.ui_in, 0b01001011)
    # cmd = Const(Cmd.ENCRYPT)
    # val = Const(11, unsigned(5))
    # ctx.set(dut.ui_in, Cat(val,cmd) )    
    # await ready(ctx)

    # val = Const(14, unsigned(5))
    # ctx.set(dut.ui_in, Cat(val,cmd) )    
    # await ready(ctx)

    # val = Const(17, unsigned(5))
    # ctx.set(dut.ui_in, Cat(val,cmd) )    
    # await ready(ctx)

    # val = Const(4, unsigned(5))
    # ctx.set(dut.ui_in, Cat(val,cmd) )    
    # await ready(ctx)

    # ctx.set(dut.ui_in, 0b000000000 )
    i=0
    for c in plain:
        c = c.upper()
        if c >= 'A' and c <= 'Z':
            input_val = ord(c)-65
            val = Const(input_val, unsigned(5))
            cmd = Const(Cmd.ENCRYPT)
            ctx.set(dut.ui_in, Cat(val,cmd) )    
            await ready(ctx)
            await clk(ctx)

            #cipher_val = ord(cipher[i]) - 65
            golden_val = ord(golden[i]) - 65
            out_val = ctx.get(dut.uo_out[0:5])

            print(f'Round {i}: Input {c} (0x{input_val:x} / {input_val}) -> {golden[i]} (0x{golden_val:x} / {golden_val}) expected, actual 0x{out_val:x} / {out_val}')
            #if not cipher_val == out_val: break
            assert golden_val==out_val, f'Round {i}: Input {c} ({input_val}) -> {golden[i]} ({golden_val}), actual {out_val}'
            i+=1

    #ctx.set(dut.rst, 1)

    # Set all rotors
    # ctx.set(dut.r0.en, 0)
    # ctx.set(dut.r1.en, 0)
    # ctx.set(dut.r2.en, 0)
    # ctx.set(dut.ref.en, 0)

    # ctx.set(dut.r0.inc, 0)
    # ctx.set(dut.r1.inc, 0)
    # ctx.set(dut.r2.inc, 0)
    # ctx.set(dut.ref.inc, 0)

    # ctx.set(dut.r0.load_start, 0)
    # ctx.set(dut.r1.load_start, 0)
    # ctx.set(dut.r2.load_start, 0)
    # ctx.set(dut.ref.load_start, 0)

    # ctx.set(dut.r0.load_ring, 0)
    # ctx.set(dut.r1.load_ring, 0)
    # ctx.set(dut.r2.load_ring, 0)
    # ctx.set(dut.r2.load_ring, 0)

    # await clk(ctx, 2)

    # ctx.set(dut.rst, 0)
    

    # # Start the first round
    # ctx.set(dut.r0.inc, 1)
    # ctx.set(dut.r0.en, 1)
    # i=0
    # for c in plain:
    #     c = c.upper()
    #     if c >= 'A' and c <= 'Z':
    #         input_val = ord(c)-65
    #         ctx.set(dut.ui_in, input_val)
    #         await clk(ctx)
    #         cipher_val = ord(cipher[i]) - 65
    #         out_val = ctx.get(dut.r0.right_out)

    #         assert cipher_val==out_val, f'Round {i}: Input {c} ({input_val}) -> {cipher[i]} ({out_val}), actual {out_val}'
    #         i+=1

    #await clk(ctx, 10)
    print(f'Checked against: \n{golden}')
    print('Test passed!')


sim = Simulator(dut)
sim.add_clock(100e-6)
sim.add_testbench(bench)
with sim.write_vcd("output/enigma.vcd"):
    sim.run()
