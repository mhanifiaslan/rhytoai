"""RythoAI v3 UI sesleri — numpy ile kisa, yumusak WAV'lar sentezler.

Kullanim (repo kokunden):
    backend/.venv/Scripts/python tools/generate_sounds.py

Ciktilar apps/mobile/assets/sounds/ altina yazilir:
    message_send.wav     kisa yumusak "pop"  (~120ms, 700->900Hz sweep)
    message_receive.wav  iki tonlu nazik "ding" (~200ms)
    cast.wav             mistik kisa "chime" (~350ms, harmonikli)
    like.wav             cok kisa "tick"
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


if __name__ == "__main__":
    message_send()
    message_receive()
    cast()
    like()
    print("Tum sesler uretildi.")
