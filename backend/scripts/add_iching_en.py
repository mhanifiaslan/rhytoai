"""data/hexagrams.json dosyasina Ingilizce metinleri ekler (tek seferlik).

Heksagram yargisi ve imgesi yalnizca LLM prompt'una giriyor; Turkce metni
Ingilizce bir prompt'un icine koymak yorumun dilini ve tonunu bozuyordu.
Metinler birebir ceviri degil, klasik I Ching corpusuna sadik Ingilizce
karsiliklardir.

Calistirma:  .venv/Scripts/python.exe scripts/add_iching_en.py
"""
from __future__ import annotations

import io
import json
from pathlib import Path

VERI = Path(__file__).resolve().parent.parent / "data" / "hexagrams.json"

#: Trigram adlari ve elementleri. Element artik dilden bagimsiz anahtar.
TRIGRAM_EN = {
    "qian": ("Heaven", "metal"),
    "zhen": ("Thunder", "wood"),
    "kan": ("Water", "water"),
    "gen": ("Mountain", "earth"),
    "kun": ("Earth", "earth"),
    "xun": ("Wind", "wood"),
    "li": ("Fire", "fire"),
    "dui": ("Lake", "metal"),
}

#: numara -> (judgment_en, image_en)
HEXAGRAM_EN: dict[int, tuple[str, str]] = {
    1: ("Pure yang: supreme success, and gain for the one who perseveres. "
        "Move without pause, as the sky does; your creative force is at its height.",
        "Heaven moves with strength; the wise keep making themselves stronger."),
    2: ("Pure yin: acceptance and devotion bring gain. Do not lead — follow, "
        "and find the one who will show you the way.",
        "The nature of earth is devotion; the wise carry everything with a broad virtue."),
    3: ("The pain of birth: inside the chaos is the seed of growth. Do not rush, "
        "find helpers, build order one step at a time.",
        "Clouds and thunder; the wise move forward by ordering and sorting."),
    4: ("Inexperience is no disgrace; the will to learn is what is precious. "
        "Ask the right question sincerely, once, and take the answer seriously.",
        "A spring wells up at the foot of the mountain; the wise feed their character with resolve."),
    5: ("Waiting with confidence is not weakness but maturity. Wait inside the "
        "light; the great water is crossed when its time comes.",
        "Clouds rise into the sky; the wise eat, drink and wait in good cheer."),
    6: ("Even when you are right, do not push conflict to its end. Know how to "
        "stop halfway; do not begin great works with this energy.",
        "Heaven and water flow in opposite directions; the wise think a matter through at its start."),
    7: ("Discipline and a just cause: force only works through order. An "
        "experienced leader is needed; govern the many with fairness.",
        "Water in the middle of the earth; the wise increase their people through generosity."),
    8: ("A time of solidarity: people are gathering around a centre. If you are "
        "going to join, join without hesitation; the latecomer loses.",
        "Water over the earth; the ancient kings founded domains and bound friendships."),
    9: ("Small obstacles are cleared by fine adjustment. The storm has not yet "
        "broken; accumulate in small steps, invest in subtlety.",
        "Wind blows across the sky; the wise work on the finer grain of their nature."),
    10: ("Deal with a dangerous power through courtesy: you tread on the tiger's "
         "tail and it does not bite. Manners and grace are protection.",
         "Heaven above, lake below; the wise steady the will of the people by telling high from low."),
    11: ("Heaven and earth join: a time of harmony, prosperity and flow. The "
         "small departs, the great arrives; multiply the abundance by sharing it.",
         "Heaven and earth unite; the ruler completes nature's course and distributes it to the people."),
    12: ("Communication has broken; the channels are blocked. Withdraw and keep "
         "your values; do not take part in a bad season, wait it out with patience.",
         "Heaven and earth do not unite; the wise turn inward and conceal their virtue."),
    13: ("Fellowship formed in the open brings success. Unite around transparent "
         "shared aims, not behind closed doors.",
         "Fire together with heaven; the wise distinguish kinds yet bring people together."),
    14: ("A season of plenty and high achievement. Carry your power with humility; "
         "let your light warm everyone rather than turn to pride.",
         "Fire above heaven; the wise curb what is bad and honour what is good."),
    15: ("Modesty opens every door: the mountain knows how to stand below the "
         "earth. Reduce the excess, complete the lack, restore balance.",
         "Mountain within the earth; the wise take from the much, add to the little, and level the scales."),
    16: ("Enthusiasm sets people in motion. Lead at the right moment, with music "
         "and rhythm; break inertia with zeal.",
         "Thunder comes out of the earth; the ancient kings honoured virtue by making music."),
    17: ("Learn to adapt: to lead, first learn to follow. Do not resist the time "
         "and the circumstance — flexibility brings gain.",
         "Thunder in the middle of the lake; the wise withdraw to rest when evening comes."),
    18: ("What was neglected has decayed; it is time to repair. Take it on with "
         "courage: mending what has spoiled brings supreme success.",
         "Wind at the foot of the mountain; the wise revive the people and nourish their spirit."),
    19: ("Growth and rise are approaching; the window is open but not endless. "
         "Advance generously now, and do not forget the eighth month.",
         "Earth above the lake; the wise are inexhaustible in the will to teach, boundless in supporting people."),
    20: ("A time of observing and of being seen: look out from the tower, see "
         "widely. Let your inner seriousness be an example that steadies others.",
         "Wind blows over the earth; the ancient kings travelled the land, watched the people, and set the teaching."),
    21: ("The obstacle between is removed only by a decisive bite. Name the "
         "problem plainly, and cut through it with justice and clarity.",
         "Thunder and lightning; the ancient kings made penalties clear and proclaimed the laws."),
    22: ("Form and beauty matter, but they must carry substance. Ornament is "
         "enough for small matters; great decisions demand essence.",
         "Fire at the foot of the mountain; the wise light up daily affairs but do not dress up disputes."),
    23: ("A season of coming apart: this is not the moment to act. The structure "
         "is being stripped; protect what is sound and wait out the wave.",
         "The mountain rests on the earth; those above find safety only by making the foundation generous."),
    24: ("The turning point: the light is returning. A natural rebirth with no "
         "forcing; the return comes on the seventh day.",
         "Thunder within the earth; the ancient kings shut the gates at the solstice and rested."),
    25: ("Uncalculating, unexpectant honesty is the strongest protection. Act in "
         "accord with your instinct; cleverness brings misfortune.",
         "Thunder rolls beneath heaven; the ancient kings nourished all things in keeping with the season."),
    26: ("Great power is being reined in: energy is accumulating. Do not stay "
         "home, go out into the field; stored wisdom accomplishes great things.",
         "Mountain in the midst of heaven; the wise build character by learning the words and deeds of the past."),
    27: ("Look at what you are feeding: with what do you fill your body, your "
         "mind, your surroundings? Watch what comes out of your mouth and what goes in.",
         "Thunder at the foot of the mountain; the wise are careful in speech and measured in eating and drinking."),
    28: ("The ridgepole bends: you are at the limit of what you can carry. "
         "Extraordinary times demand extraordinary decisions; stand alone, without fear.",
         "The lake rises above the trees; the wise stand alone unafraid, withdraw from the world without sorrow."),
    29: ("Danger upon danger: do what water does, keep flowing. If the heart is "
         "true, the crossing is found every time.",
         "Water flows on without interruption; the wise walk in unbroken virtue and repeat the work of teaching."),
    30: ("Light shines by clinging to something: like your flame, cling to what "
         "is true. Clarity and attachment bring success.",
         "Brightness rises twice; the great person lights the four directions with their clarity."),
    31: ("Mutual attraction: hearts are open, influence runs both ways. "
         "Auspicious for courtship, marriage, partnership; sincerity is essential.",
         "Lake above the mountain; the wise influence people through the emptiness (the humility) of their acceptance."),
    32: ("Endurance brings success: hold principles that do not change within "
         "change. Persevere on your path, do not alter your course.",
         "Thunder and wind; the wise stand firm and do not change their direction."),
    33: ("An honourable retreat is strategy, not defeat. The small is growing "
         "stronger; keep your distance, withdraw with resolve rather than anger.",
         "Mountain beneath heaven; the wise keep the small person at bay with gravity, not with anger."),
    34: ("Power is at its peak; but true power is the kind joined to rightness. "
         "Use your force within the rules; avoid becoming the ram that butts the fence.",
         "Thunder above heaven; the wise take not one step on a path that does not accord with propriety."),
    35: ("The sun rises over the earth: quick and easy progress. Your visibility "
         "is growing; use your light generously.",
         "The sun comes out above the earth; the wise themselves brighten their own bright virtue."),
    36: ("A time to hide your light: keep the brightness within, be cautious "
         "outside. In a dark season, perseverance is possible through inner clarity.",
         "The light enters the earth; the wise live among the crowd, veil their light, and still shine."),
    37: ("The foundation is the hearth: the order of family and close circle "
         "comes first. If each keeps their role faithfully, the outside settles too.",
         "Wind comes out of fire; the wise have substance in their words and constancy in their conduct."),
    38: ("A season of opposites: great unity is not possible for now, but small "
         "matters can be reconciled. Do not turn difference into enmity.",
         "Fire above, lake below; the wise keep their individuality within fellowship."),
    39: ("The road is blocked: do not push stubbornly, turn to the southwest (the "
         "easier way, to allies). Obstruction is a call to look inward and re-aim.",
         "Water above the mountain; the wise turn back to themselves and shape their character."),
    40: ("The knot is loosening, the tension releasing. Forgive, let go, and "
         "return quickly to normal; do not leave the remaining matters hanging.",
         "Thunder and rain; the wise pardon mistakes and forgive offences."),
    41: ("A season of decrease: simplicity joined to sincerity is blessed. Even "
         "two bowls suffice for an offering; decrease below and nourish above.",
         "Lake at the foot of the mountain; the wise restrain their anger and limit their desires."),
    42: ("A wind of abundance is blowing: an auspicious moment for great "
         "undertakings, even for crossing the great water. Whoever shares the gain below multiplies it.",
         "Wind and thunder; seeing good, the wise turn toward it; seeing their fault, they correct it."),
    43: ("The last resistance is about to break: declare the truth openly, but do "
         "not reach for a weapon. Resolve yes, harshness no.",
         "The lake has risen to heaven; the wise distribute wealth downward and do not rest on their virtue."),
    44: ("An unexpected influence is seeping in: it is attractive, but do not let "
         "it grow. Set the limit while it is small; beware uncontrolled closeness.",
         "Wind beneath heaven; the ruler spreads his commands to the four directions."),
    45: ("People are gathering like water into a lake: a time of great assembly. "
         "There must be a genuine purpose at the centre; be prepared, keep even your weapons in order.",
         "Lake above the earth; the wise renew their weapons and make ready for the unforeseen."),
    46: ("The tree rises quietly through the soil: unshowy, cumulative growth. Do "
         "not shrink from those above you; advance toward the south (toward the light).",
         "The tree grows within the earth; the wise reach the high and the great by accumulating the small."),
    47: ("Resources are exhausted and your words carry little weight. Prove "
         "yourself by your bearing, not by talking; the great person keeps their cheer even in hardship.",
         "There is no water in the lake; the wise stake their life on their purpose."),
    48: ("The town changes, the well does not: the source at your core is open to "
         "all. Keep your well clean, keep your rope long, tend to your source.",
         "Water above the wood; the wise encourage the people at their work and call them to help one another."),
    49: ("Radical change is made only when its time has come and trust has been "
         "earned. A revolution made on its own day erases regret.",
         "Fire within the lake; the wise set the calendar in order and make the seasons clear."),
    50: ("The vessel of transformation: it is time to cook the raw into something "
         "of worth. Supreme success; nourish, offer, and turn it into culture.",
         "Fire above the wood; the wise steady their position through rightness."),
    51: ("The shock comes and rattles a hundred miles; but whoever is sound "
         "within does not spill a drop from the cup. Turn the tremor into waking.",
         "Thunder upon thunder; in fear and trembling the wise correct and examine themselves."),
    52: ("Stop when it is time to stop, move when it is time to move. When the "
         "back grows still the self disappears; stillness teaches the right moment for movement.",
         "Two mountains side by side; the wise do not let their thoughts stray beyond the present moment."),
    53: ("The wild goose nears the shore slowly: processes that advance step by "
         "step, like a betrothal, are blessed. Patient development gives lasting results.",
         "A tree upon the mountain; the wise dwell in noble character and improve the customs."),
    54: ("Relationships that begin from a secondary position ask for care. A step "
         "taken without thinking of the end stays barren; know your position, adjust your expectation.",
         "Thunder above the lake; by considering the end the wise understand the flaw in the beginning."),
    55: ("The moment of the peak: the sun stands at noon. Do not grieve, scatter "
         "your light over the world; abundance is brief, take it in fully.",
         "Thunder and lightning come together; the wise decide disputes and carry out punishments."),
    56: ("You are in a foreign land: neither arrogant nor fawning. The wanderer's "
         "strength is measured bearing and inner wholeness; success in small matters.",
         "Fire upon the mountain; the wise are clear and swift in punishment and do not drag out disputes."),
    57: ("Penetrate like the wind: not by a hard blow but by steady, gentle "
         "influence. Make your aim clear and consult the great person.",
         "Winds following one another; the wise spread their commands and carry out their affairs."),
    58: ("Joy that comes from within is contagious and makes people willing even "
         "for the hardest work. Seek grounded gladness, not surface amusement.",
         "Two lakes joined together; the wise work with friends and learn together."),
    59: ("Rigidity and selfishness are dissolving: wind scatters the foam on the "
         "water. Melt hardened factions in a shared sacred purpose.",
         "Wind blows over the water; the ancient kings made offerings and founded temples."),
    60: ("Limits set you free: the bamboo rises because of its joints. But do not "
         "insist on a limitation that turns bitter; find the sweet measure.",
         "Water above the lake; the wise set number and measure, and weigh virtue and right conduct."),
    61: ("Sincerity reaches even pigs and fishes: a bond made from the heart "
         "crosses every barrier. Understand without prejudice, build trust.",
         "Wind over the lake; the wise deliberate disputes and delay the execution (they show mercy)."),
    62: ("A little excess is right in small matters, not in great ones. The flying "
         "bird should glide down, not up: stay low, exceed with measure.",
         "Thunder upon the mountain; the wise go slightly too far in respect of conduct, in grief of mourning, in thrift of spending."),
    63: ("Everything is in its place: but balance is at its most fragile just "
         "here. Progress continues in small matters; the beginning is blessed, mind the end.",
         "Water above fire; the wise think of misfortune and take precautions in advance."),
    64: ("The crossing is nearly complete: but the fox wets its tail on the last "
         "step. The hope is great; take the final steps with the greatest care.",
         "Fire above the water; the wise carefully distinguish things and put everything in its place."),
}


def main() -> int:
    veri = json.load(io.open(VERI, encoding="utf-8"))

    for anahtar, trigram in veri["trigrams"].items():
        ad, element = TRIGRAM_EN[anahtar]
        trigram["name_en"] = ad
        trigram["element"] = element

    eksik = []
    for heksagram in veri["hexagrams"]:
        no = heksagram["number"]
        if no not in HEXAGRAM_EN:
            eksik.append(no)
            continue
        yargi, imge = HEXAGRAM_EN[no]
        heksagram["judgment_en"] = yargi
        heksagram["image_en"] = imge

    if eksik:
        raise SystemExit(f"Ingilizce metni olmayan heksagramlar: {eksik}")

    with io.open(VERI, "w", encoding="utf-8", newline="\n") as dosya:
        json.dump(veri, dosya, ensure_ascii=False, indent=2)
        dosya.write("\n")

    print(f"trigram: {len(veri['trigrams'])}, heksagram: {len(veri['hexagrams'])} guncellendi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
