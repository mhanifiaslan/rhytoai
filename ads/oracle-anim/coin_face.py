"""Para yüzü dokusu: siyah zeminli still → alfa PNG (PZ2).

Kullanım (numpy'lı backend venv'i ile):
    backend/.venv/Scripts/python.exe ads/oracle-anim/coin_face.py \
        raw/face.png apps/mobile/assets/anim/coin_face.png [--size 256]

build.py ile aynı doktrin: alfa = max(r,g,b); renk unpremultiply
(rgb*255/a) ki yarı saydam kenar koyulaşmasın. Sonra paranın sınır kutusu
bulunur, kare tuvale ortalanır, LANCZOS ile küçültülür. Widget dokuyu
`drawImageRect` ile yüz dikdörtgenine gerer; kare ve tam ortalı olması
şart — aksi hâlde takla atarken para "kayar".
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def siyah_alfa(rgb: np.ndarray) -> np.ndarray:
    """(h,w,3) uint8 → (h,w,4) uint8; siyah → saydam, renk unpremultiply."""
    r = rgb.astype(np.float32)
    a = r.max(axis=2)
    a_safe = np.where(a > 0, a, 1.0)
    renk = np.clip(r * 255.0 / a_safe[..., None], 0, 255)
    return np.dstack([renk, a]).astype(np.uint8)


def kirp_ve_karele(rgba: np.ndarray, esik: int = 12, pay: float = 0.04
                   ) -> np.ndarray:
    """Alfa sınır kutusunu bul, kare tuvale ortala (pay kadar boşluk)."""
    a = rgba[..., 3]
    ys, xs = np.where(a > esik)
    if len(xs) == 0:
        raise SystemExit("Görüntüde para yok (alfa eşiği altında)")
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    w, h = x1 - x0, y1 - y0
    kenar = int(max(w, h) * (1 + 2 * pay))
    tuval = np.zeros((kenar, kenar, 4), dtype=np.uint8)
    ox, oy = (kenar - w) // 2, (kenar - h) // 2
    tuval[oy:oy + h, ox:ox + w] = rgba[y0:y1, x0:x1]
    return tuval


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("kaynak")
    ap.add_argument("hedef")
    ap.add_argument("--size", type=int, default=256)
    args = ap.parse_args()

    img = Image.open(args.kaynak).convert("RGB")
    rgba = siyah_alfa(np.asarray(img))
    kare = kirp_ve_karele(rgba)
    out = Image.fromarray(kare, "RGBA").resize(
        (args.size, args.size), Image.LANCZOS)
    Path(args.hedef).parent.mkdir(parents=True, exist_ok=True)
    out.save(args.hedef, "PNG", optimize=True)
    boyut = Path(args.hedef).stat().st_size
    print(f"{args.hedef}: {args.size}x{args.size}, {boyut / 1024:.0f} KB")


if __name__ == "__main__":
    main()
