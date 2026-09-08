# -*- coding: utf-8 -*-
"""POV planinda (bilgenin kendi eli, telefon dikey) ekrana gercek Rytho
arayuzunu bindirir.

kompozit.py'nin ayni mantigi; iki fark:
  * Dortgen ekran KENARLARINDAN olculdu (maske kenarlarina dogru fit),
    goz karariyla degil: ustte/altta/solda/sagda ayri dogru fit edilip
    kesistirildi. Kamera kilitli oldugu icin tek dortgen tum kareler icin
    gecerli (ilk/son kare farki 0.98/255).
  * Ekran plan basinda YANIYOR (bir onceki planda kitaptaki telefon kapali;
    burasi 'uyanma' ani) - kisa rampa, sonra sabit.
"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

KAYNAK = 'frames/pov_src'
CIKTI = 'frames/pov_out'
QUAD = [(343, 176), (802, 194), (718, 1150), (271, 1131)]
VIOLET = (0x7B, 0x2F, 0xF7)


def perspektif_katsayi(hedef, kaynak_boyut):
    w, h = kaynak_boyut
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    A, B = [], []
    for (x, y), (u, v) in zip(hedef, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    n = 8
    for i in range(n):
        p = max(range(i, n), key=lambda r: abs(A[r][i]))
        A[i], A[p] = A[p], A[i]; B[i], B[p] = B[p], B[i]
        pv = A[i][i]
        for j in range(i, n): A[i][j] /= pv
        B[i] /= pv
        for r in range(n):
            if r == i: continue
            f = A[r][i]
            if f == 0: continue
            for j in range(i, n): A[r][j] -= f * A[i][j]
            B[r] -= f * B[i]
    return B


def hazirla(ui):
    """Durum/gezinme cubugunu kirp, mum isigina uydur."""
    ui = ui.convert('RGB')
    w, h = ui.size
    ui = ui.crop((0, int(h * 0.050), w, int(h * 0.958)))
    ui = ImageEnhance.Brightness(ui).enhance(0.86)
    ui = ImageEnhance.Color(ui).enhance(0.90)
    amber = Image.new('RGB', ui.size, (255, 176, 96))
    return Image.blend(ui, amber, 0.06)


def main():
    ui = Image.open(sys.argv[1])
    kareler = sorted(os.listdir(KAYNAK))
    os.makedirs(CIKTI, exist_ok=True)
    boyut = Image.open(os.path.join(KAYNAK, kareler[0])).size
    ui_w = hazirla(ui).transform(
        boyut, Image.PERSPECTIVE, perspektif_katsayi(QUAD, hazirla(ui).size),
        Image.BICUBIC)
    alan = Image.new('L', boyut, 0)
    ImageDraw.Draw(alan).polygon(QUAD, fill=255)
    alan = alan.filter(ImageFilter.GaussianBlur(1.2))

    n = len(kareler)
    bas, sure = int(n * 0.06), max(1, int(n * 0.16))
    for i, ad in enumerate(kareler):
        plaka = Image.open(os.path.join(KAYNAK, ad)).convert('RGB')
        t = 0.0 if i < bas else min(1.0, (i - bas) / sure)
        if t <= 0:
            plaka.save(os.path.join(CIKTI, ad)); continue
        gri = plaka.convert('L')
        # Koyu = cam, aydinlik = basparmak -> parmak camin USTUNDE kalir
        ekran = gri.point(lambda v: 255 if v < 55 else (0 if v > 95 else int((95 - v) * 255 / 40)))
        maske = Image.composite(ekran, Image.new('L', boyut, 0), alan)
        maske = maske.filter(ImageFilter.GaussianBlur(0.8)).point(lambda v: int(v * t))
        kat = Image.composite(ui_w, plaka, maske)
        hale = maske.filter(ImageFilter.GaussianBlur(70)).point(lambda v: int(v * 0.26 * t))
        kat = Image.composite(Image.blend(kat, Image.new('RGB', boyut, VIOLET), 0.30), kat, hale)
        kat.save(os.path.join(CIKTI, ad))
    print('pov kompozit bitti:', n, 'kare')


if __name__ == '__main__':
    main()
