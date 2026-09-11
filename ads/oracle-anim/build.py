"""Kehanet sahnesi varlik hatti (PBZ, revize): SIYAH zeminli kliplerden
ALFA'li animasyonlu WebP uretir — tepsi/mekan yok, uygulamanin kendi
zemininin ustune normal (srcOver) cizilir.

Siyah -> alfa donusumu: a = max(r,g,b); renk = rgb*255/a (unpremultiply).
Flutter cizerken premultiply edince (renk*a) ozgun rgb geri gelir; siyah
zemin a=0 ile tamamen kaybolur. Bu, screen karisiminin alfa esdegeridir ve
katman/BackdropFilter fark etmeksizin her yerde calisir.

Kullanim (repo kokunden):  python ads/oracle-anim/build.py
Girdi: ads/oracle-anim/raw/{bair,cland0..3,bluopan}.mp4
Cikti: apps/mobile/assets/anim/*.webp  (+ olcum raporu)
"""
from __future__ import annotations
import os, subprocess, sys, tempfile, shutil
from pathlib import Path
import numpy as np
from PIL import Image

FFMPEG = r"C:\Users\pv\Downloads\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"
KOK = Path(__file__).resolve().parents[2]
RAW = Path(__file__).resolve().parent / "raw"
OUT = KOK / "apps" / "mobile" / "assets" / "anim"
W, H = 640, 360     # butce: klip <=1 MB; 720x405 lossy alfa ile 1,1-1,5 MB cikti
INIS_SURE = 0.9      # her inis klibi (sn)
INIS_FPS = 18
DONGU_HIZ = 2.0      # dongu klipleri 2x hizli (hareket yavas uretildi)

def kareler(mp4: Path, fps: int | None = None) -> list[np.ndarray]:
    tmp = Path(tempfile.mkdtemp())
    vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
    if fps: vf = f"fps={fps}," + vf
    subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-i", str(mp4),
                    "-vf", vf, str(tmp / "k%04d.png")], check=True)
    arr = [np.asarray(Image.open(p).convert("RGB")).astype(np.float32)
           for p in sorted(tmp.glob("k*.png"))]
    shutil.rmtree(tmp, ignore_errors=True)
    return arr

def siyah_to_alfa(rgb: np.ndarray) -> Image.Image:
    a = rgb.max(axis=2)                       # 0..255
    # gurultu tabani: cok koyu pikseller (<=6) tamamen seffaf
    a = np.where(a <= 6, 0, a)
    with np.errstate(divide="ignore", invalid="ignore"):
        renk = np.where(a[..., None] > 0, rgb * 255.0 / a[..., None], 0)
    renk = np.clip(renk, 0, 255).astype(np.uint8)
    out = np.dstack([renk, a.astype(np.uint8)])
    return Image.fromarray(out, "RGBA")

def kenar_kirliligi(rgb: np.ndarray) -> float:
    """Kenar bandinin ortalama parlakligi — cam/masa artefakt dedektoru."""
    b = 12
    band = np.concatenate([rgb[:b].reshape(-1, 3), rgb[-b:].reshape(-1, 3),
                           rgb[:, :b].reshape(-1, 3), rgb[:, -b:].reshape(-1, 3)])
    return float(band.mean())

def durulma_indeksi(frames: list[np.ndarray], esik: float = 1.4) -> int:
    """Ardisik kare farki esigin altina kalici olarak dustugu ilk kare."""
    g = [f.mean(axis=2) for f in frames]
    fark = [np.abs(g[i + 1] - g[i]).mean() for i in range(len(g) - 1)]
    for i in range(len(fark)):
        if all(d < esik for d in fark[i:]):
            return i
    return len(frames) - 1

def yaz(frames_rgba: list[Image.Image], ms: int, hedef: Path, q: int = 75):
    # alpha_quality: alfa duzlemi de kayipli — varsayilan kayipsiz alfa dosyayi ikiye katliyordu.
    frames_rgba[0].save(hedef, format="WEBP", save_all=True, append_images=frames_rgba[1:],
                        duration=ms, loop=0, lossless=False, quality=q, alpha_quality=70,
                        method=4, exact=False)
    return hedef.stat().st_size

def secim(frames, n):
    idx = np.linspace(0, len(frames) - 1, n).round().astype(int)
    return [frames[i] for i in idx]

def inis(ad: str, k: int):
    f = kareler(RAW / ad, fps=24)
    kir = max(kenar_kirliligi(x) for x in f)
    dur = durulma_indeksi(f)
    kes = min(len(f), dur + int(0.25 * 24))          # durulma + 0,25 sn nefes
    kes = max(kes, 24)                                # en az 1 sn ham
    # Hep 0. kareden baslar (havadaki dongunun son karesiyle ayni poz ->
    # sicrama yok) ve durulmus halde biter. Hiz en cok 2x: gec duruluyorsa
    # klip 0,9 sn yerine 1,2 sn'ye kadar uzar.
    sure = min(1.2, max(INIS_SURE, kes / 24 / 2.0))
    sec = secim(f[:kes], int(round(sure * INIS_FPS)))
    boyut = yaz([siyah_to_alfa(x) for x in sec], int(1000 / INIS_FPS), OUT / f"coins_land_{k}.webp")
    print(f"coins_land_{k}: ham {len(f)} kare, durulma {dur/24:.2f}s, kesim {kes/24:.2f}s -> "
          f"{len(sec)} kare / {sure:.2f}s ({kes/24/sure:.1f}x), kenar kirliligi max {kir:.1f}/255, {boyut/1024:.0f} KB")

def dongu(ad: str, hedef: str, fps: int):
    f = kareler(RAW / ad)                            # kaynak 24 fps
    kir = max(kenar_kirliligi(x) for x in f)
    n = int(len(f) / DONGU_HIZ * fps / 24)
    sec = secim(f, n)
    boyut = yaz([siyah_to_alfa(x) for x in sec], int(1000 / fps), OUT / f"{hedef}.webp")
    print(f"{hedef}: ham {len(f)} kare -> {n} kare @{fps}fps ({n/fps:.2f}s), "
          f"kenar kirliligi max {kir:.1f}/255, {boyut/1024:.0f} KB")

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    # Istege bagli suzgec: `build.py coins_land_1 bazi_wait` yalniz onlari uretir.
    istenen = set(sys.argv[1:])
    def sec_mi(ad: str) -> bool:
        return not istenen or ad in istenen
    if sec_mi("coins_air"):
        dongu("bair.mp4", "coins_air", 16)
    for k, ad in [(3, "cland3.mp4"), (2, "cland2.mp4"), (1, "cland1.mp4"), (0, "cland0.mp4")]:
        if sec_mi(f"coins_land_{k}"):
            inis(ad, k)
    if sec_mi("bazi_wait"):
        dongu("bluopan.mp4", "bazi_wait", 10)
    toplam = sum(p.stat().st_size for p in OUT.glob("*.webp"))
    print(f"TOPLAM {toplam/1024/1024:.2f} MB")
