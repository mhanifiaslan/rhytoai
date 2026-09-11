"""RythoAI v3 UI sesleri — numpy ile kisa, yumusak WAV'lar sentezler.

Kullanim (repo kokunden):
    backend/.venv/Scripts/python tools/generate_sounds.py

Ciktilar apps/mobile/assets/sounds/ altina yazilir:
    message_send.wav     kisa yumusak "pop"  (~120ms, 700->900Hz sweep)
    message_receive.wav  iki tonlu nazik "ding" (~200ms)
    cast.wav             mistik kisa "chime" (~350ms, harmonikli)
    like.wav             cok kisa "tick"
    success.wav          C6-E6-G6 arpej (~280ms) — onboarding/basari ani
    streak.wav           parlak tik + besli (~180ms) — seri artisi
    purchase.wav         dolu chime, cast ailesinden (~450ms) — satin alma
    coin_land.wav        para inisi "clink" (<=400ms, PBZ) — kaynak once
                         tools/sounds_src/coin_land_foley.wav (Higgsfield
                         kling klibinden kesilmis GERCEK metal temasi, kendi
                         hesabimizin uretimi); dosya yoksa sentez yedegi
    coin_land.wav        metalik "clink" (~300ms, inharmonik) — para inisi (PBZ)

Hepsi in-house sentez (R12-C1): dis kaynak/lisans kaydi gerekmez.
"""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

SAMPLE_RATE = 44100
OUT_DIR = Path(__file__).resolve().parent.parent / "apps" / "mobile" / "assets" / "sounds"


def _envelope(n: int, attack: float = 0.005, decay: float = 6.0) -> np.ndarray:
    """Hizli atak + ustel sonum; kenarlarda tik olmasin diye kisa fade."""
    t = np.linspace(0, 1, n, endpoint=False)
    attack_n = max(int(SAMPLE_RATE * attack), 8)
    env = np.exp(-decay * t)
    env[:attack_n] *= np.linspace(0, 1, attack_n)
    env[-64:] *= np.linspace(1, 0, 64)
    return env


def _write(name: str, signal: np.ndarray, peak: float = 0.55) -> None:
    signal = signal / (np.max(np.abs(signal)) or 1.0) * peak
    data = (signal * 32767).astype(np.int16)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(data.tobytes())
    print(f"yazildi: {path} ({len(data) / SAMPLE_RATE * 1000:.0f} ms)")


def message_send() -> None:
    """700->900Hz sinus sweep + hizli sonum = yumusak 'pop'."""
    dur = 0.12
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    freq = np.linspace(700, 900, n)
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    sig = np.sin(phase) * _envelope(n, decay=9.0)
    _write("message_send.wav", sig, peak=0.5)


def message_receive() -> None:
    """Iki tonlu nazik 'ding': E6 ardindan G6, hafif bindirmeli."""
    dur = 0.2
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    tone1 = np.sin(2 * np.pi * 1318.5 * t) * _envelope(n, decay=10.0)
    # Ikinci ton 70ms gecikmeli baslar
    delay = int(SAMPLE_RATE * 0.07)
    tone2 = np.zeros(n)
    n2 = n - delay
    t2 = np.linspace(0, n2 / SAMPLE_RATE, n2, endpoint=False)
    tone2[delay:] = np.sin(2 * np.pi * 1568.0 * t2) * _envelope(n2, decay=8.0)
    _write("message_receive.wav", tone1 * 0.8 + tone2, peak=0.45)


def cast() -> None:
    """Mistik chime: temel + 2.7x ve 4.2x inharmonik ustler (can hissi)."""
    dur = 0.35
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    base = 660.0
    sig = (
        1.0 * np.sin(2 * np.pi * base * t)
        + 0.55 * np.sin(2 * np.pi * base * 2.7 * t)
        + 0.3 * np.sin(2 * np.pi * base * 4.2 * t)
    ) * _envelope(n, decay=7.0)
    # Hafif parildama: yavas tremolo
    sig *= 1.0 + 0.12 * np.sin(2 * np.pi * 9 * t)
    _write("cast.wav", sig, peak=0.5)


def like() -> None:
    """Cok kisa 'tick': yuksek frekansli, aninda sonen."""
    dur = 0.06
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    sig = np.sin(2 * np.pi * 2200 * t) * _envelope(n, attack=0.001, decay=16.0)
    _write("like.wav", sig, peak=0.4)


def success() -> None:
    """C6-E6-G6 arpej: majör üçlü, 60ms arayla — 'oldu' hissi."""
    dur = 0.28
    n = int(SAMPLE_RATE * dur)
    sig = np.zeros(n)
    for i, freq in enumerate([1046.5, 1318.5, 1568.0]):
        delay = int(SAMPLE_RATE * 0.06 * i)
        m = n - delay
        t = np.linspace(0, m / SAMPLE_RATE, m, endpoint=False)
        sig[delay:] += np.sin(2 * np.pi * freq * t) * _envelope(m, decay=9.0)
    _write("success.wav", sig, peak=0.45)


def streak() -> None:
    """Parlak tik + besli (G6->D7): kisa, oyunlu 'seri buyudu' isareti."""
    dur = 0.18
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    tik = np.sin(2 * np.pi * 1568.0 * t) * _envelope(n, attack=0.001, decay=14.0)
    delay = int(SAMPLE_RATE * 0.05)
    besli = np.zeros(n)
    m = n - delay
    t2 = np.linspace(0, m / SAMPLE_RATE, m, endpoint=False)
    besli[delay:] = np.sin(2 * np.pi * 2349.3 * t2) * _envelope(m, decay=11.0)
    _write("streak.wav", tik * 0.9 + besli * 0.7, peak=0.4)


def purchase() -> None:
    """Satin alma: cast ailesinden daha dolu, cift vurus 'chime'."""
    dur = 0.45
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    base = 660.0
    vurus1 = (
        1.0 * np.sin(2 * np.pi * base * t)
        + 0.55 * np.sin(2 * np.pi * base * 2.7 * t)
        + 0.3 * np.sin(2 * np.pi * base * 4.2 * t)
    ) * _envelope(n, decay=6.0)
    # Ikinci vurus: besli yukaridan (E6 civari), 140ms gecikmeli
    delay = int(SAMPLE_RATE * 0.14)
    m = n - delay
    t2 = np.linspace(0, m / SAMPLE_RATE, m, endpoint=False)
    vurus2 = np.zeros(n)
    vurus2[delay:] = (
        1.0 * np.sin(2 * np.pi * base * 1.5 * t2)
        + 0.4 * np.sin(2 * np.pi * base * 1.5 * 2.7 * t2)
    ) * _envelope(m, decay=6.0)
    sig = vurus1 + 0.8 * vurus2
    sig *= 1.0 + 0.1 * np.sin(2 * np.pi * 8 * t)
    _write("purchase.wav", sig, peak=0.5)


FOLEY_DIR = Path(__file__).resolve().parent / "sounds_src"


def _foley(name: str, peak: float) -> bool:
    """Kaynak klasorunde gercek kayit varsa onu normalize edip yazar."""
    src = FOLEY_DIR / name
    if not src.exists():
        return False
    with wave.open(str(src), "rb") as f:
        assert f.getnchannels() == 1 and f.getframerate() == SAMPLE_RATE, src
        data = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16)
    sig = data.astype(np.float64) / 32768.0
    sig[-64:] *= np.linspace(1, 0, 64)
    _write(name.replace("_foley", ""), sig, peak=peak)
    return True


def coin_land() -> None:
    """Para inisi (PBZ). Once GERCEK foley: tools/sounds_src/coin_land_foley.wav
    (kling3_0 inis klibinin ses kanalindan kesildi, 380 ms, kendi uretimimiz).
    Dosya yoksa asagidaki sentez yedegi calisir.

    Sentez: metalik 'clink' — Can degil para — yuksek, ince,
    cabuk sonen inharmonik parsiyeller (1 / 1.53 / 2.19 / 2.94 / 3.76) +
    atakta 2 ms metal temasi gurultusu; 90 ms sonra daha sonuk ikinci temas
    (para bir kez seker). Toplam 300 ms (<=400 ms), deterministik."""
    if _foley("coin_land_foley.wav", peak=0.45):
        return
    dur = 0.30
    n = int(SAMPLE_RATE * dur)
    base = 2350.0
    rng = np.random.default_rng(7)

    def temas(m: int, guc: float) -> np.ndarray:
        tt = np.linspace(0, m / SAMPLE_RATE, m, endpoint=False)
        sig = np.zeros(m)
        for oran, agirlik, sonum in (
            (1.0, 1.0, 9.0),
            (1.53, 0.6, 12.0),
            (2.19, 0.45, 15.0),
            (2.94, 0.3, 18.0),
            (3.76, 0.18, 22.0),
        ):
            sig += agirlik * np.sin(2 * np.pi * base * oran * tt) * _envelope(
                m, attack=0.001, decay=sonum
            )
        k = int(SAMPLE_RATE * 0.002)
        sig[:k] += rng.uniform(-1, 1, k) * 0.5 * np.linspace(1, 0, k)
        return sig * guc

    sig = temas(n, 1.0)
    delay = int(SAMPLE_RATE * 0.09)
    sig[delay:] += temas(n - delay, 0.45)
    _write("coin_land.wav", sig, peak=0.45)


if __name__ == "__main__":
    message_send()
    message_receive()
    cast()
    like()
    success()
    streak()
    purchase()
    coin_land()
    print("Tum sesler uretildi.")
