import random

HEXAGRAMS = {
    1: "Qian (The Creative) - Heaven over Heaven. Absolute yang, strong, creative action.",
    2: "Kun (The Receptive) - Earth over Earth. Absolute yin, devotion, yielding, receptive.",
    11: "Tai (Peace) - Earth over Heaven. Harmony, prosperity, things flowing smoothly.",
    12: "Pi (Standstill) - Heaven over Earth. Stagnation, lack of communication.",
    63: "Ji Ji (After Completion) - Water over Fire. Everything is in its proper place.",
    64: "Wei Ji (Before Completion) - Fire over Water. Potential, transition, not yet finished."
}

def cast_iching(question: str):
    # I Ching traditionally uses 3 coins or yarrow stalks.
    # A simple simulation: pick a random hexagram from 1 to 64
    hexagram_num = random.choice(list(HEXAGRAMS.keys()))
    hexagram_reading = HEXAGRAMS.get(hexagram_num, f"Hexagram {hexagram_num} - Wisdom awaits.")
    
    return {
        "question": question,
        "hexagram_number": hexagram_num,
        "reading": hexagram_reading
    }
