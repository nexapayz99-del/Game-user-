"""Small starter dictionary. Extend with reviewed words for your game."""
from collections import defaultdict
import random

_RAW_WORDS = """
ant ape arm art ash ask bad bag ban bar bat bed bee beg bet bid big bin bit
box boy bus but buy cab can cap car cat cow cup cut dad day den dew did dig
dim dip dog dot dry due ear eat egg ego elf end era eye fan far fat fed fee
few fig fin fit fix fly fog for fox fun gap gas gel gem get god gum gun guy
gym had ham has hat hay hen her hid him hip his hit hog hop hot how hub hug
ice ill ink inn ion jam jar jaw jet job jog joy key kid kit lab lad lag lap
law lay leg let lid lie lip lit log lot low mad man map mat max may men met
mix mob mom mud mug nap net new nod nor not now nut oak oar odd off oil old
one opt orb ore our out owl own pad pal pan par pat paw pay pea pen pet pie
pig pin pit pod pop pot pub pug pun pup put rag ram ran rap rat raw ray red
ref rib rid rig rim rip rob rod rot row rub rug rum run sad sag sap sat saw
say sea see set sew she shy sin sip sir sit six ski sky sly sob son sun tag
tan tap tar tea ten the tie tin tip toe ton too top toy try tub tug two use
van vat vet via vie vow war was wax way web wed wet who why wig win wit wow
yak yam yap yes yet you zip zoo
able acid aged also apex area army atom away baby back bake ball band bank
base bath beam bear beat been beer bell belt best bias bike bill bird blow
blue boat body bomb bond bone book boom born boss both bowl bulk burn bush
busy cake call calm came camp card care case cash cast cave cell chat chef
chip city clay club coal coat code cold come cook cool cope copy cost crew
crop dark data date dawn days dead deal dear debt deep deny desk dial diet
disc dish disk does done door dose down draw drew drop dual dust duty each
earn ease east easy edge else even ever evil exam face fact fail fair fall
farm fast fate fear feed feel feet fell felt file fill film find fine fire
firm fish five flat flow food foot form four free from fuel full fund gain
game gate gave gear gene gift girl give glad goal goes gold golf gone good
gray grew grow gulf hair half hall hand hang hard harm hate have head heal
hear heat held hell help here hero high hill hint hire hold hole holy home
hope host hour huge hung hunt hurt idea inch into iron item jack jail join
joke jump just keen keep kept kick kill kind king knee knew know lack lady
lake land lane last late lead leaf lean left lend less life lift like line
link lion list live load loan lock logo long look lord lose loss lost love
luck made mail main make male many mark mass mate math meal mean meat meet
menu mere mess mile milk mind mine miss mode mood moon more most move much
must name navy near neat neck need news next nice nine none noon nose note
okay once only open oral over pace pack page paid pain pair pale palm park
part pass past path peak pick pink pipe plan play plot plug plus poem poet
pool poor port post pull pure push race rail rain rank rare rate read real
rear rent rest rice rich ride ring rise risk road rock role roll roof room
root rose rule rush safe said sail sake sale salt same sand save seat seed
seek seem seen self sell send sent sept ship shoe shop shot show shut sick
side sign silk sing sink site size skin skip slow snow soft soil sold sole
some song soon sort soul spot star stay step stop such suit sure take tale
talk tall tank tape task team tear tell tend term test text than that them
then they thin this thus tick tide tied time tiny told toll tone took tool
tour town tree trip true tube tune turn twin type unit upon used user vary
vast very view vote wage wait wake walk wall want warm wash wave ways weak
wear week well went were west what when whom wide wife wild will wind wine
wing wire wise wish with wolf wood word work yard yeah year your zero zone
about above actor acute admit adopt adult after again agent agree ahead alarm
album alert alien alike alive allow alone along alter among anger angle angry
apart apple apply arena argue arise array aside asset audio audit avoid award
aware badly baker bases basic basis beach began begin being below bench bible
birth black blame blank blind block blood board boost booth bound brain brand
bread break breed brief bring broad broke brown build built buyer cable camel
candy carry catch cause chain chair chart chase cheap check chest chief child
china choir civil claim class clean clear clerk click climb clock close coach
coast could count court cover craft crash cream crime cross crowd crown curve
cycle daily dance dated dealt death debut delay depth doing doubt dozen draft
drama dream dress drink drive eager early earth eight elite empty enemy enjoy
enter entry equal error event every exact exist extra faith false fancy fault
favor feast fence fewer field fifth fifty fight final first fixed flash fleet
floor focus force forth forty forum found frame frank fraud fresh front fruit
fully funny giant given glass globe glory going grace grade grand grant grass
great green greet grief gross group grown guard guess guest guide habit happy
heart heavy hence hobby horse hotel house human humor ideal image imply index
inner input issue joint judge known label labor large laser later laugh layer
learn least leave legal level light limit local logic loose lower lucky lunch
magic major maker march match maybe mayor meant media metal might minor minus
mixed model money month moral motor mount mouse mouth movie music needs never
newly night noise north noted novel nurse occur ocean offer often order other
ought outer owner paint panel paper party peace phase phone photo piano piece
pilot pitch place plain plane plant plate point pound power press price pride
prime print prior prize proof proud prove queen quick quiet quite radio raise
range rapid ratio reach react ready realm reply right rival river rough round
route royal rural scale scene scope score sense serve seven shall shape share
sharp sheet shelf shell shift shine shirt shock shoot short shown sight since
skill sleep slice slide small smart smile smoke solid solve sorry sound south
space spare speak speed spend spent split spoke sport staff stage stake stand
start state steam steel stick still stock stone stood store storm story strip
study stuff style sugar suite super sweet table taken taste teach teeth thank
their theme there these thick thing think third those three threw tight times
tired title today topic total touch tough tower track trade train treat trend
trial tried truck truly trust truth twice under union unity until upper upset
urban usage usual valid value video virus visit vital voice waste watch water
wheel where which while white whole whose woman women world worry worse worst
worth would write wrong wrote young youth
"""

WORDS_BY_LENGTH = defaultdict(list)
for item in _RAW_WORDS.split():
    word = item.strip().lower()
    if word.isalpha() and word not in WORDS_BY_LENGTH[len(word)]:
        WORDS_BY_LENGTH[len(word)].append(word)

def choose_word(length: int) -> str | None:
    """Return a random word of the requested length, or None if unavailable."""
    words = WORDS_BY_LENGTH.get(length, [])
    return random.choice(words) if words else None
