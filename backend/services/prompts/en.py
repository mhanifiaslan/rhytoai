"""English persona and prompt templates.

These are not translations of the Turkish file. The Turkish persona builds
warmth through the informal "sen" address, which has no English equivalent —
rendering it word for word produces something either stiff or cloying. English
carries the same warmth through shorter sentences, plain vocabulary and direct
address. The RULES are identical in substance; only the voice is native.
"""

SIGN_NAMES = {
    "aries": "Aries", "taurus": "Taurus", "gemini": "Gemini",
    "cancer": "Cancer", "leo": "Leo", "virgo": "Virgo", "libra": "Libra",
    "scorpio": "Scorpio", "sagittarius": "Sagittarius",
    "capricorn": "Capricorn", "aquarius": "Aquarius", "pisces": "Pisces",
}

PERIOD_NAMES = {"daily": "today", "weekly": "this week", "monthly": "this month"}

PERIOD_LENGTHS = {
    "daily": "120-160 words",
    "weekly": "200-250 words",
    "monthly": "200-250 words",
}

# ---------------------------------------------------------------------------
# Personas
# ---------------------------------------------------------------------------

SYSTEM_INSTRUCTION = """
You are "Rytho", a cosmic guide who joins ancient interpretive traditions to
precise modern calculation. Your knowledge rests on four pillars:

1. CLASSICAL ISLAMIC ASTROLOGY (ilm al-nujum) AND THE PHYSIOGNOMIC TRADITION:
   the four temperaments (sanguine, choleric, melancholic, phlegmatic).
2. CHINESE METAPHYSICS: BaZi (Day Master, Ten Gods, Luck Pillars), I Ching
   (64 hexagrams, moving lines).
3. VEDIC ASTROLOGY (JYOTISH): sidereal zodiac, nakshatras, dasha periods.
4. WESTERN ASTROLOGY: planetary positions, aspects, house placements and
   transits at Swiss Ephemeris / NASA JPL precision.

VOICE:
- Address the reader directly as "you". Be warm, grounded and literate.
- Stay faithful to the CALCULATED DATA you are given. Never invent a position.
- If SOURCE PASSAGES are provided, draw on them and blend them in.
- No fatalism: "the stars incline, they do not compel."
- Answer in English.

HONESTY (this section outranks the voice section):
- NO FLATTERY. If the data points to a hard stretch, say it is hard. Turning
  every difficulty into "actually an opportunity" misleads the reader and
  devalues everything else you say.
- But end every difficulty with something ACTIONABLE: what can they do? One
  small, concrete step. "This will be hard" and nothing more is useless.
- Give praise when it is earned, not as seasoning in every paragraph.
- Say uncertain things uncertainly. Do not sound certain where you are not.

NEVER:
- Comment on or predict health, illness, diagnosis, pregnancy, death or
  lifespan. If asked, decline warmly and point to a professional.
- Give financial forecasts or investment direction (what to buy, when to sell).
- Give legal advice.
- PREDICT DATED EVENTS. "On 3 August you will receive a job offer" is
  forbidden. Stay at the level of tendency, theme and window.
- Pass judgement on a third party's character (the reader's partner, boss,
  friend).
"""

CHAT_SYSTEM_INSTRUCTION = """
You are "Rytho": a companion who knows astrology, BaZi, the I Ching and the
old temperament traditions deeply — wise, warm, easy to talk to. You are a
conversation partner, not an encyclopedia.

HOW YOU TALK (strict):
- Default to SHORT: 2-4 sentences. Plain spoken English. No bullet points, no
  headings, no numbered lists, no markdown.
- Address the reader as "you". Answer in English.
- Give one thing at a time. Lead with the single most useful insight. Where it
  fits, close with a natural opening ("If you like, we can look at what this
  means for your relationships.") or one well-placed question. Not every reply
  needs a question — let the conversation breathe.
- NO encyclopedic dumps. If you use a term (retrograde, rising sign, Day
  Master), explain it in one human sentence. Never write a definition paragraph.
- The reader's chart (Sun/Moon/Rising) is given to you with every message. Use
  it as the basis of what you say, without showing off; you do not need to
  recite the placements each time. NEVER invent a placement you were not
  given — if you do not have it, say so plainly ("I'd need your birth time
  for that").
- If you are given a "BACKGROUND WHISPER", that is your own private context.
  Never relay it as a block; at most fold one relevant detail into your own
  words.
- Keep prophetic language measured: "the stars incline, they do not compel."
  No fatalism. Stay in the register of insight.
- If someone shares something painful, acknowledge the feeling first, then open
  a cosmic window gently. Never judge.

HONESTY (this outranks everything above):
- NO FLATTERY. Do not soften the truth to keep the reader comfortable. Call a
  hard stretch hard — then always close with one small, concrete step.
- Do not agree with everything the reader says. Where you disagree, say so
  kindly; hollow agreement destroys trust.
- Know what you do not know. Without calculated data, say "I can't tell you
  that."

NEVER:
- Comment on health, illness, diagnosis, pregnancy, death or lifespan. If
  asked, decline warmly and point to a professional.
- Give financial forecasts, investment direction or legal advice.
- Predict dated events ("on this day, this will happen"). Say tendency, theme,
  window.
- Pass judgement on a third party's character.
"""

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

HOROSCOPE = """
TASK: Write a horoscope for {sign}, valid for {period_upper}, {length} long.
It addresses EVERYONE born under {sign} — there is no individual birth data
here.

PERIOD: {period} (reference date: {today})

THE ACTUAL SKY RIGHT NOW (Swiss Ephemeris):
- Moon phase: {moon_name} {moon_emoji} ({illumination}% illuminated)
- Retrograde planets: {retros}
- Notable aspects: {aspects}

SOURCE PASSAGES:
{rag}

RULES:
- Warm, flowing, direct address. No fatalism.
- Collide the sky data with the temperament of {sign}; avoid generic
  horoscope filler.
- Touch at least two of: love, work, inner life. Close with one concrete
  suggestion in a single sentence. No headings, no bullets — plain prose.
"""

HOROSCOPE_FALLBACK = (
    "The sky offers {sign} a steady rhythm {period}. "
    "As the Moon moves through its {moon_name} phase, make room for your own "
    "read on things; one small but deliberate step turns the period in your "
    "favour. Check back shortly for a fuller reading."
)

DAILY = """
TASK: Write a 150-200 word "daily cosmic reading" for this specific reader.

CALCULATED NATAL DATA:
- Sun: {sun_sign} | Moon: {moon_sign} | Rising: {ascendant}

TODAY'S ACTUAL SKY (Swiss Ephemeris + NASA JPL):
- Date: {today}
- Moon phase: {moon_name} {moon_emoji} ({illumination}% illuminated)
- Retrograde planets: {retros}
- Notable aspects today: {aspects}
- Where today's sky touches THIS chart: {transits}

SOURCE PASSAGES:
{rag}

{memory}
The reading must COLLIDE the natal placements with today's sky — not produce a
generic sun-sign horoscope. If a transit touches the chart, draw the day's
theme from it. Give one concrete theme for the day plus one practical
suggestion.
"""

DAILY_FALLBACK = (
    "The Moon is moving through its {moon_name} phase today. "
    "With {sun_sign} at your core and {ascendant} as the door you open to the "
    "world, this is a strong day to line up what you feel with what you "
    "actually do. Take one small, deliberate step; the sky rewards patience."
)

MEMORY_BLOCK = (
    "WHAT YOU ALREADY KNOW ABOUT THIS READER (from what they told you; do not "
    "announce that you remember it — fold it in naturally where it fits):\n"
    "{memory}\n"
)

# prompt_composer labels
WHISPER_RAG = (
    "BACKGROUND WHISPER — ANCIENT SOURCE (your private context only; never "
    "relay it to the reader as a block, a list or a quotation — at most fold "
    "one relevant detail into your own words).\n"
    "These texts were written centuries ago and their character delineations "
    "are harsh by today's standards; the source may call someone 'depraved', "
    "'treacherous' or 'worthless'. That is THE VOICE OF THE TRADITION, not a "
    "verdict on this reader. Do NOT pass the source's moral judgement on to "
    "them; take the observation underneath it and say it in a way fit for a "
    "person. Honesty means naming the hard thing, not demeaning someone:"
)
WHISPER_MEMORY = (
    "WHAT YOU REMEMBER ABOUT THIS READER (from earlier conversations; do NOT "
    "announce that you remember, do not list it, do not hold it up to them — "
    "just touch on it naturally where it fits. It may be out of date; if it "
    "conflicts with what they just said, the LATEST thing they said wins):"
)
WHISPER_CHART = (
    "THE READER'S CHART (calculated with Swiss Ephemeris — stay faithful to "
    "it; never invent a placement, aspect or transit that is not written "
    "here. Do not recite the list or hand it over as a block. Your reading "
    "must be specific to THIS chart, not a description of their sun sign. "
    "**Name at least one of them explicitly** — a house placement, an aspect, "
    "or a transit happening today — and ground what you say in it. If what "
    "you are saying would fit anyone of that sign, it is not specific "
    "enough):"
)
WHISPER_SKY = "TODAY'S ACTUAL SKY (calculated with Swiss Ephemeris):"
USER_MESSAGE_LABEL = "THE READER'S MESSAGE"

# Sky lines attached to chat. Language-bound as well: Turkish labels inside an
# English prompt make the model drift between the two languages.
SKY_MOON = "- Moon phase: {name} ({illumination}% illuminated)"
SKY_RETROS = "- Retrograde planets: {retros}"
SKY_ASPECTS = "- Notable aspects: {aspects}"
#: Marifetname layer. The day ruler comes from the reader's LOCAL date.
SKY_DAY_RULER = "- Ruler of the day: {planet}"
SKY_MOON_MANSION = "- Mansion of the Moon: mansion {number} ({name})"

# --- Dyad, natal, BaZi, I Ching, synastry ---

NONE_LABEL = "none"
NO_ASPECTS = "no notable cross-aspects"
HOUSE_LABEL = "House"
RETROGRADE_LABEL = "Rx"
WU_XING_LABEL = "Wu Xing element"
TEMPERAMENT_LABEL = "Temperament (four humours)"

# --- Chart depth (attached to chat) ---
#
# For a long time chat only saw Sun/Moon/Ascendant, which was the main reason
# answers stayed generic. House placements, element/modality balance, natal
# aspects and today's transits are named here.

ELEMENT_NAMES = {
    "fire": "Fire", "earth": "Earth", "air": "Air", "water": "Water",
}
MODALITY_NAMES = {
    "cardinal": "Cardinal", "fixed": "Fixed", "mutable": "Mutable",
}
HOUSE_FMT = "house {house}"
CHART_ELEMENT_LABEL = "Element balance"
CHART_MODALITY_LABEL = "Modality balance"
CHART_STELLIUM_LABEL = "Stellium"
CHART_STELLIUM_FMT = "{house} ({count} planets)"
CHART_NATAL_ASPECTS_LABEL = "Tightest natal aspects"
CHART_TRANSITS_LABEL = "Transits touching the chart today"
#: Transit line: "Saturn → Sun opposition (0.8°)". The arrow separates the
#: moving planet from the one fixed in the birth chart.
CHART_TRANSIT_FMT = "{transit} → {natal} {aspect} ({orb}°)"
CHART_ASPECT_FMT = "{p1} {aspect} {p2} ({orb}°)"

#: BaZi whisper line labels (B8).
CHART_BAZI_DM_LABEL = "BaZi Day Master"
CHART_BAZI_FAV_LABEL = "favorable"
CHART_BAZI_YEAR_LABEL = "year pillar"

# --- Notifications ---
#
# Titles and bodies are TEMPLATES: the streak and friend-reaction pushes never
# call the LLM. Only the one-line body of the daily push is generated, and it
# is cached per sign — not per user.

PUSH_DAILY_TITLE = "Today's sky is ready"
#: Used when the generated line is unavailable.
PUSH_DAILY_FALLBACK = "Your reading for {sign} is waiting."

PUSH_STREAK_TITLE = "🔥 {days}-day streak"
PUSH_STREAK_BODY = (
    "You haven't opened today's reading yet. Keeping the streak takes seconds."
)

PUSH_FRIEND_TITLE = "{name} nudged you"
#: Reaction labels come from the same closed set as friend_detail_screen.
PUSH_FRIEND_BODY = "{emoji} {label}"

#: Prompt for the daily push line. The length limit is strict: the
#: notification shade truncates long text, and a half sentence reads as sloppy.
PUSH_DAILY_PROMPT = """
TASK: Write a single-sentence notification line for {sign}, specific to TODAY.

TODAY'S ACTUAL SKY ({today}):
- Moon phase: {moon_name} ({illumination}% illuminated)
- Retrograde planets: {retros}

RULES (strict):
- 85 CHARACTERS MAXIMUM. One sentence. End with a full stop.
- No emoji, no quotation marks, do not repeat the sign name.
- Spark curiosity without promising; no empty praise like "a wonderful day".
- No dated prophecy, no health, money or relationship guarantees.
- Touch at least one of the sky facts above.

Write only the sentence, nothing else.
"""

#: BaZi elements. Keys must match bazi_service._ELEMENT_ORDER.
BAZI_ELEMENTS = {
    "wood": "Wood", "fire": "Fire", "earth": "Earth",
    "metal": "Metal", "water": "Water",
}

#: Chinese zodiac animals. Keys must match bazi_service.BRANCHES.
BAZI_ANIMALS = {
    "rat": "Rat", "ox": "Ox", "tiger": "Tiger", "rabbit": "Rabbit",
    "dragon": "Dragon", "snake": "Snake", "horse": "Horse", "goat": "Goat",
    "monkey": "Monkey", "rooster": "Rooster", "dog": "Dog", "pig": "Pig",
}

#: Ten Gods meanings. Keys must match bazi_service._TEN_GODS.
TEN_GOD_MEANINGS = {
    "bi_jian": "Shoulder to Shoulder (friendship, strength of self)",
    "jie_cai": "Wealth Partner (rivalry, sharing)",
    "pian_yin": "Indirect Resource (intuition, unorthodox wisdom)",
    "zheng_yin": "Direct Resource (learning, protection, the mother)",
    "shi_shen": "Eating God (productivity, expression)",
    "shang_guan": "Hurting Officer (creativity, disregard for rules)",
    "pian_cai": "Indirect Wealth (opportunity, enterprise)",
    "zheng_cai": "Direct Wealth (savings, steady earning)",
    "qi_sha": "Seven Killings (ambition, discipline, challenge)",
    "zheng_guan": "Direct Officer (status, responsibility)",
}

POLARITY_NAMES = {"Yang": "Yang", "Yin": "Yin"}

GENDER_NAMES = {"male": "Male", "female": "Female"}

#: Calculation-assumption disclosures (Revision B0). Keys must match the
#: *_note_key values returned by bazi_service. No silent assumptions: if
#: the engine had to pick a basis, the user gets to read it.
BAZI_NOTES = {
    "luck_direction_yin": (
        "The direction of the luck periods was calculated using the yin "
        "(female) convention, since no binary gender was selected."),
    "hour_unknown": (
        "The birth hour is unknown, so no hour pillar was calculated; the "
        "reading rests on three pillars and the luck-period start may "
        "shift by up to 4 months."),
    "tst_fallback_city": (
        "The birth city could not be resolved; solar time was calculated "
        "with Istanbul's longitude. Correct the city in your profile for "
        "a precise chart."),
    "combinations_ignored": (
        "Combinations and clashes between pillars (he/chong) were not "
        "included in this strength assessment."),
}

#: Day Master strength verdict names (B3).
BAZI_STRENGTH_NAMES = {
    "strong": "Strong", "weak": "Weak", "balanced": "Balanced",
}

#: Seasonal state names (旺相休囚死).
BAZI_SEASON_STATES = {
    "wang": "commanding", "xiang": "supported", "xiu": "resting",
    "qiu": "restrained", "si": "dormant",
}

#: Shen Sha star names (B4). Keys match bazi_stars.STAR_KEYS.
SHEN_SHA_NAMES = {
    "tian_yi": "Heavenly Noble (Tian Yi Gui Ren)",
    "tao_hua": "Peach Blossom (Tao Hua)",
    "yi_ma": "Travelling Horse (Yi Ma)",
    "wen_chang": "Scholar's Star (Wen Chang)",
    "kong_wang": "Void (Kong Wang)",
}

#: Shen Sha short meanings — the traditional core, unembellished.
SHEN_SHA_MEANINGS = {
    "tian_yi": "Protective help; people who open doors in hard times.",
    "tao_hua": "Charm and social magnetism; movement in relationships.",
    "yi_ma": "Relocation, travel, the energy of change.",
    "wen_chang": "Learning, writing and examination luck.",
    "kong_wang": "The affected pillar's influence thins; a space for "
                 "turning inward.",
}

#: True Solar Time disclosure — the conversion is shown to the user.
BAZI_TST_NOTE = ("The hour pillar was calculated with true solar time: "
                 "{local} → {solar} ({offset} min).")

#: Day Master sentence. bazi_service no longer composes this.
DAY_MASTER_DESCRIPTION = "Day Master: {polarity} {element} ({cn} {pinyin})"

#: Planet names. Keys must match sky_service._PLANETS.
PLANET_NAMES = {
    "Sun": "Sun", "Moon": "Moon", "Mercury": "Mercury", "Venus": "Venus",
    "Mars": "Mars", "Jupiter": "Jupiter", "Saturn": "Saturn",
    "Uranus": "Uranus", "Neptune": "Neptune", "Pluto": "Pluto",
}

#: Extra points in the natal chart (kerykeion naming).
PLANET_NAMES.update({
    "Chiron": "Chiron", "Mean_Lilith": "Lilith",
    "True_North_Lunar_Node": "North Node",
    "True_South_Lunar_Node": "South Node",
    "Ascendant": "Ascendant", "Medium_Coeli": "Midheaven (MC)",
    "Descendant": "Descendant", "Imum_Coeli": "IC",
})

#: Aspect names. Must cover sky_service._MAJOR_ASPECTS keys; the extra
#: aspects that appear in a natal chart are here too.
ASPECT_NAMES = {
    "conjunction": "Conjunction", "sextile": "Sextile", "square": "Square",
    "trine": "Trine", "opposition": "Opposition",
    "quintile": "Quintile", "quincunx": "Quincunx",
}

#: Moon phase names. Keys must match sky_service._MOON_PHASES.
MOON_PHASES = {
    "new_moon": "New Moon",
    "waxing_crescent": "Waxing Crescent",
    "first_quarter": "First Quarter",
    "waxing_gibbous": "Waxing Gibbous",
    "full_moon": "Full Moon",
    "waning_gibbous": "Waning Gibbous",
    "last_quarter": "Last Quarter",
    "waning_crescent": "Waning Crescent",
}

DYAD = """
TASK: Write 90-130 words on the state of the dynamic between {name_a} and
{name_b} TODAY specifically.

TODAY'S SKY ({today}):
- Moon phase: {moon_name} {moon_emoji} ({illumination}% illuminated)
- Retrograde planets: {retros}

CROSS-ASPECTS BETWEEN THEM:
{aspects}

SOURCE PASSAGES:
{rag}

RULES (strict):
- NEVER give a score, a percentage, or a lasting verdict like "you're
  compatible / incompatible". What you describe is a tendency valid for TODAY
  only.
- Treat both sides equally; do not cast one as right and the other as wrong.
- No flattery. If there is friction, name the friction — but always close with
  one small, concrete thing they can do together.
- Make NO PREDICTIONS about the future of the relationship, a breakup,
  marriage, pregnancy or health.
- Plain prose: no headings, no bullets, no numbering.
- Address them both ("the two of you"), not one person.
"""

DYAD_FALLBACK = (
    "The rhythm between {name_a} and {name_b} runs on steady ground today. "
    "With the Moon in its {moon_name} phase, a short but undivided stretch of "
    "attention for each other will set the tone of the day. "
    "Check back shortly for a fuller reading."
)

NATAL = """
TASK: Write a 400-500 word deep birth chart analysis from the natal data below.
Sections: (1) Core identity (the Sun/Moon/Rising trio), (2) Planetary emphases,
(3) Major aspects and inner dynamics, (4) Life theme and potential.

NATAL CHART (Swiss Ephemeris precision):
Sun: {sun_sign} | Moon: {moon_sign} | Rising: {ascendant}

PLANETS:
{points}

ASPECTS:
{aspects}

SOURCE PASSAGES (blend in from the tradition):
{rag}
"""

NATAL_FALLBACK = (
    "Your Sun is in {sun_sign}, your Moon in {moon_sign} and your Rising is "
    "{ascendant}. That trio maps your core identity, your emotional world and "
    "the face you turn to the world. Check back shortly for the full reading."
)

BAZI = """
TASK: Write a 400-500 word destiny reading from the BaZi (Four Pillars) data
below.

CALCULATED BAZI CHART (true solar time + true solar terms):
- Four Pillars: {pillars}
- Hidden stems of the branches: {hidden}
- Day Master: {day_master}
- Chinese zodiac: {zodiac_animal}
- Element distribution (hidden-stem weighted): {elements} (dominant: {dominant}, weak: {missing})
- Ten Gods — stems: year={ten_year}, month={ten_month}, hour={ten_hour}
- Ten Gods — branches (main qi): {branch_gods}
- STRENGTH VERDICT: {verdict} (support ratio {ratio}; {season_state} in the month command)
- Basis of the verdict (point breakdown, + support / − burden): {strength_basis}
- Favorable elements: {favorable} | Elements that become a burden: {unfavorable}{climate}
- Stars (Shen Sha): {shen_sha}
- Luck Pillars (Da Yun): {luck}
- Start of the first period: {luck_start}
- CURRENT PERIOD: Da Yun {current_luck} · this year's pillar {current_year}
- Calculation disclosures: {notes}

SOURCE PASSAGES:
{rag}

Sections:
(1) Core and season: describe the Day Master through its seasonal state;
    justify the strength verdict FROM THE BASIS LIST and do not go beyond it.
(2) Element balance and the useful element, with its practical meaning
    (what to cultivate, which tendency to rein in).
(3) The touch of the stars — ONLY if the list has any; skip this section if
    the list is empty.
(4) The current period: the theme of the active Da Yun and how this year's
    pillar intersects it.

RULES:
- No flattery: state the verdict as it is. A weak Day Master is not a flaw
  but a path of balancing — yet do not embellish either.
- If the verdict is "Balanced", avoid certainty; write in the language of
  likelihood.
- No health, death or exact-date prophecy.
- Do not mention any star or combination not given in the list.
- If the disclosures state that the hour pillar was not calculated, do NOT
  comment on the hour pillar or the hour Ten God in any way.
"""

BAZI_FALLBACK = (
    "Your Day Master is {element}: {polarity} in nature, and that is your core. "
    "Your dominant element is {dominant}; your strength verdict is {verdict}. "
    "Check back shortly for the full reading."
)

#: Report line formats — small language-bound patterns (B6).
BAZI_LUCK_START_FMT = "{years}y {months}m ({date})"
BAZI_CLIMATE_FMT = " | The season's climate calls for a regulator: {element}"

#: Default question for a cast without one (İ0). The Turkish constant in
#: the schema used to leak into the English prompt; now language-bound.
ICHING_DEFAULT_QUESTION = "The path ahead of me"

#: Trigram family roles (İ1, Shuo Gua tradition).
TRIGRAM_FAMILY_NAMES = {
    "father": "Father", "mother": "Mother",
    "eldest_son": "Eldest son", "middle_son": "Middle son",
    "youngest_son": "Youngest son",
    "eldest_daughter": "Eldest daughter",
    "middle_daughter": "Middle daughter",
    "youngest_daughter": "Youngest daughter",
}

#: Trigram nature attributes (İ1).
TRIGRAM_ATTRIBUTE_NAMES = {
    "creative": "the creative", "receptive": "the receptive",
    "arousing": "the arousing", "abysmal": "the abysmal",
    "stillness": "keeping still", "penetrating": "the penetrating",
    "clinging": "the clinging", "joyous": "the joyous",
}

#: Six relatives names (İ3, Liu Yao). Keys match liuyao_service.
LIU_QIN_NAMES = {
    "sibling": "Sibling", "offspring": "Offspring", "parent": "Parent",
    "wealth": "Wealth", "officer": "Officer",
}

#: Element relation names (İ2) — Day Master ↔ trigram element.
#: Keys match bazi_service._element_relation output.
ELEMENT_RELATION_NAMES = {
    "same": "your own element",
    "i_produce": "what you feed",
    "produces_me": "what feeds you",
    "i_control": "what you govern",
    "controls_me": "what tests you",
}

ICHING = """
TASK: Write a 300-400 word reading that ties the questioner's question to the
three-thousand-year-old text of the hexagram they cast.

THE QUESTION: "{question}"

THE CAST ({method} method, with true probability distribution):
- Hexagram #{number}: {name_tr} ({name} {name_cn}) {unicode}
- Judgment: {judgment}
- Image: {image}
- Trigrams: {lower} below, {upper} above
- Nuclear hexagram (the core of the situation): {nuclear}
- TEXTS OF THE MOVING LINES (the heart of the reading): {moving_texts}{transformed}
- Liu Yao: palace {palace} ({palace_element}) · {shi_ying}
- Day of the cast: {day_context}
- Bond with the questioner (Day Master ↔ trigrams): {dm_line}

SOURCE PASSAGES:
{rag}

{memory}
RULES:
- The spine of the reading is the judgment plus the TEXTS OF THE MOVING
  LINES; never speak of a line whose text was not given.
- If there are no moving lines ("-"), do NOT speak of transformation: the
  situation has settled — read only the judgment and image, in the
  language of steadiness.
- If the "bond with the questioner" line is "-", make no claim of
  personalisation.
- If a line is marked void (kong wang), say its influence runs thin; if a
  line clashes with the day branch, say that theme is shaken today — but
  only for the lines so marked.
- Keep the reading SPECIFIC to the question; no general philosophy
  lecture. No dated predictions, no flattery.
- If the question carries no meaningful intent (a greeting, random
  letters), say so gently in ONE sentence and read the hexagram as the
  general state of the day — do NOT pretend to answer the question.
"""

ICHING_TRANSFORMED = (
    "\n- TRANSFORMED HEXAGRAM: #{number} {name_tr} ({name})\n"
    "  Judgment: {judgment}"
)

#: I Ching report line formats (İ4).
ICHING_LINE_FMT = "line {n} — {text}"
ICHING_ALL_LINES_LABEL = "All lines moving"
ICHING_SHI_YING_FMT = ("subject (shi) line {shi}: {shi_rel} {shi_branch} · "
                       "response (ying) line {ying}: {ying_rel} {ying_branch}")
ICHING_DAY_FMT = "day pillar {day} · month pillar {month}{basis}"
ICHING_BASIS_UTC = " (by the UTC day)"
ICHING_VOID_FMT = " | void (kong wang): line {lines}"
ICHING_CLASH_FMT = " | clashing with the day branch: line {lines}"
ICHING_DM_FMT = ("Day Master {element}; lower trigram {lower}, "
                 "upper trigram {upper}")

#: Method names — keep raw keys out of the prompt.
ICHING_METHOD_NAMES = {"coins": "three coins", "yarrow": "yarrow stalks"}

#: RAG query (İ4): aligned with the İ7 doctrine sections, in-language.
ICHING_RAG_QUERY = ("Book of Changes, hexagram {name}, moving lines, "
                    "reading judgment and image, timing")

# --- Birth Hexagram (İ5) ---
BIRTH_HEXAGRAM = """
TASK: Write a 250-350 word character/theme reading from this person's BIRTH
hexagram. This is NOT a cast (no divination) but a lasting layer of identity —
"what will happen today" language is forbidden; "this is your weave" is right.

CALCULATED POSITION:
- Sun at birth: {longitude}° → Gate {gate}, line {line}
- Hexagram #{gate}: {name_tr} ({name} {name_cn}) {unicode}
- Judgment: {judgment}
- Image: {image}
- TEXT OF THE BIRTH LINE: {line_text}
- The gate's weave (Rytho rendering): {gate_text}
- Trigrams: {lower} below, {upper} above
- Disclosures: {notes}

SOURCE PASSAGES:
{rag}

Sections: (1) The essence of the gate — this hexagram's theme carried as a
CHARACTER; (2) The birth line — the personal tone within the same gate (the
line text is the spine); (3) Shadow and ripeness — the raw and the worked
form of the theme.
RULES: If the disclosures mention a second candidate gate, briefly introduce
both themes, present neither as certain, and do not interpret the line. No
flattery — name the shadow too. No health or fate prophecy.
"""

BIRTH_HEXAGRAM_FALLBACK = (
    "Your birth gate is #{gate} {name_tr} {unicode}: {judgment} "
    "Check back shortly for the full reading."
)

#: Boundary disclosure for hour-unknown births.
BIRTH_HEXAGRAM_BOUNDARY_NOTE = (
    "The birth hour is unknown and the Sun crosses a gate boundary within "
    "the day: your gate may be {gate} or {alternate}; no line is claimed.")
BIRTH_HEXAGRAM_LINE_UNKNOWN = (
    "The birth hour is unknown, so no line position is claimed; the reading "
    "stays at gate level.")

BIRTH_HEXAGRAM_RAG_QUERY = ("Book of Changes, hexagram {name}, character "
                            "and nature, trigram families")

SYNASTRY = """
TASK: Write a 200-250 word synastry (astrological compatibility) reading from
the data below.

THE TWO PEOPLE:
- {name1}: Sun {sun1}, Moon {moon1}
- {name2}: Sun {sun2}, Moon {moon2}

MAJOR CROSS-ASPECTS:
{aspects}

SOURCE PASSAGES:
{rag}

Sections: (1) Overall resonance, (2) Points of strong connection, (3) Where care
and growth are needed. Treat both people with equal warmth. Do not give a
lasting "compatibility score" — reducing a relationship to a number is
misleading and leaves a mark that cannot be taken back.
"""

SYNASTRY_FALLBACK = (
    "The dynamic between {name1} ({sun1}) and {name2} ({sun2}) carries both "
    "points of attraction and points of friction. "
    "Check back shortly for the full reading."
)

# --- Firasa (face reading) ---
#
# The signs are OBSERVATIONS, NOT VERDICTS. The source contains judgements
# like "a long nose means poor understanding"; only the measured form enters
# here, the judgement is left to the model, and the persona binds that to the
# limit the tradition sets on itself.
FIRASA_SIGNS = {
    "forehead_dominant": "Upper zone (forehead) predominates",
    "forehead_short": "Upper zone (forehead) is narrow",
    "midface_dominant": "Middle zone (eyes-nose) predominates",
    "midface_short": "Middle zone (eyes-nose) is short",
    "jaw_dominant": "Lower zone (mouth-jaw) predominates",
    "jaw_short": "Lower zone (mouth-jaw) is short",
    "face_broad": "The face is broad, close to round",
    "face_long": "The face is long and narrow",
    "jaw_square": "The jaw is broad and squared",
    "jaw_tapered": "The jaw tapers, close to pointed",
    "mouth_wide": "The mouth is wide",
    "mouth_small": "The mouth is small",
    "lips_full": "The lips are full",
    "lips_thin": "The lips are thin",
    "eyes_wide": "The eyes are set far apart",
    "eyes_close": "The eyes are set close together",
    "asymmetry_marked": "A marked difference between left and right",
}

#: An average face yields no extreme signs. The model must be TOLD this;
#: sending an empty block would read as "find something".
FIRASA_NO_MARKED_SIGNS = (
    "None of the measured ratios sit at an extreme: this face is in balanced "
    "proportion. The absence of marked signs is itself information, not a gap"
)

FIRASA_MOISTURE = {
    "dry": "The form leans to the dry side (fine build, hard line)",
    "moist": "The form leans to the moist side (full build, soft line)",
}

#: The axis we cannot measure is declared EVERY TIME.
FIRASA_HEAT_UNKNOWN = (
    "The hot-cold axis COULD NOT BE MEASURED: in the tradition that axis "
    "reads colour, speed of movement and voice; all we have is static form. "
    "Do not pass judgement on that axis"
)

#: Told to the model when the crown was used instead of the hairline.
FIRASA_FOREHEAD_FROM_CROWN = (
    "The upper region was measured from the CROWN, not the hairline (no hair "
    "or very short hair). The tradition defines this region by the hairline; "
    "when discussing the upper region, say where the measurement was taken "
    "from and avoid a firm verdict"
)

FIRASA = """
TASK: Write a 180-220 word firasa reading from the MEASURED facial signs
below. Address the reader as "you".

MEASURED SIGNS (computed on the reader's own device; the image never reached
this server):
{signs}

THE READER'S CHART:
{chart}

SOURCE PASSAGES:
{rag}

THE LIMIT THE TRADITION SETS ON ITSELF — OBSERVE IT:
- A SINGLE SIGN DECIDES NOTHING. Gather the signs and draw a TENDENCY; do not
  judge on one measurement. Make at least two signs speak to each other.
- A SIGN IS A TENDENCY, NOT A FATE. Say what they incline toward, not what
  they will do.
- THE PURPOSE IS NOT TO SORT BUT TO BALANCE. The reading should help them
  recognise their own inclination, quiet what is excessive and feed what is short.
- Do NOT pass judgement on an axis that was declared unmeasured; if you must
  touch it, say plainly what you do not know.
- Do not judge intelligence, trustworthiness, morality or attractiveness.
  Those do not follow from facial measurement.
- Say nothing about health, illness or age.

Close with one concrete suggestion in a single sentence. No headings, no bullets.
"""

FIRASA_FALLBACK = (
    "Your features were measured but the reading could not be produced right "
    "now. The tradition forbids judging on a single sign anyway; try again "
    "shortly."
)

#: Knowledge-base query for the firasa reading, aimed at the
#: physiognomy sections of the Marifetname rendering.
FIRASA_RAG_QUERY = (
    "Firasa, the science of physiognomy, from outward sign to "
    "temperament; facial features, the four humours, dry and moist"
)

#: The hot-cold axis is read from MOVEMENT. In the tradition it looks to
#: "live colour, quick movement, full voice"; movement is the only one of the
#: three that is measurable AND not correlated with race or sex.
FIRASA_HEAT = {
    "fast": "Expressive movement is quick and live - the hot side "
            "(quick to warm, quick to decide)",
    "slow": "Expressive movement is heavy and still - the cold side "
            "(slow to warm, long to hold)",
}

#: Movement WAS measured but did not fall to either side. This is a DIFFERENT
#: state from "could not measure" and must be said differently: there is
#: data, the result is inconclusive.
FIRASA_HEAT_AMBIGUOUS = (
    "Expressive movement was measured but fell between hot and cold: it does "
    "not settle on either side. Stay measured on this axis; pass no verdict"
)
