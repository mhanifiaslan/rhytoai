# -*- coding: utf-8 -*-
"""Kilitli plakadaki telefon ekranina GERCEK Rytho arayuzunu bindirir.

Neden boyle:
  * Kamera kilitli oldugu icin ekran dortgeni sabit -> kare kare takip YOK.
  * Parmak camin USTUNDE: plakadaki parlak pikseller korunur, koyu (ekran)
    pikseller arayuzle degistirilir. Basit parlaklik anahtari; ekran neredeyse
    saf siyah oldugu icin guvenilir.
  * Ekran dokunustan SONRA yanar - hem teknik olarak kolay hem anlatiya uygun.
"""
import os, sys
from PIL import Image, ImageFilter

PLAKA_KARE = 'frames/plaka_src'
CIKTI_KARE = 'frames/plaka_out'
# Ekran dortgeni (plaka koordinatlari): SOL-UST, SAG-UST, SAG-ALT, SOL-ALT
QUAD = [(302, 670), (721, 658), (717, 1350), (297, 1362)]
VIOLET = (0x7B, 0x2F, 0xF7)


def perspektif_katsayi(hedef, kaynak_boyut):
    """Pillow PERSPECTIVE katsayilari: cikti -> girdi eslemesi."""
    w, h = kaynak_boyut
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    A, B = [], []
    for (x, y), (u, v) in zip(hedef, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    # Gauss elemesi (numpy yok)
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
    """Durum/gezinme cubugunu kirp, mum isigina uydur.

    Ham arayuz olduğu gibi bindiginde 'yapistirilmis' duruyor: ekran
    cevredeki sahneden parlak ve soguk kaliyor. Sahnenin anahtar isigi
    sicak mum; ekran da o ortamda bir miktar sonup isinmali.
    """
    ui = ui.convert('RGB')
    w, h = ui.size
    ui = ui.crop((0, int(h * 0.050), w, int(h * 0.958)))      # cubuklar disari
    from PIL import ImageEnhance
    ui = ImageEnhance.Brightness(ui).enhance(0.82)
    ui = ImageEnhance.Color(ui).enhance(0.88)
    amber = Image.new('RGB', ui.size, (255, 176, 96))
    return Image.blend(ui, amber, 0.07)


def warp(ui, boyut):
    ui = hazirla(ui)
    k = perspektif_katsayi(QUAD, ui.size)
    return ui.transform(boyut, Image.PERSPECTIVE, k, Image.BICUBIC)


def quad_maske(boyut):
    from PIL import ImageDraw
    m = Image.new('L', boyut, 0)
    ImageDraw.Draw(m).polygon(QUAD, fill=255)
    return m.filter(ImageFilter.GaussianBlur(1.2))


def main():
    ui = Image.open(sys.argv[1])
    kareler = sorted(os.listdir(PLAKA_KARE))
    os.makedirs(CIKTI_KARE, exist_ok=True)
    n = len(kareler)
    ilk = Image.open(os.path.join(PLAKA_KARE, kareler[0]))
    boyut = ilk.size
    ui_w = warp(ui, boyut)
    alan = quad_maske(boyut)

    yanma_bas = int(n * 0.42)      # dokunustan sonra
    yanma_sure = max(1, int(n * 0.18))

    for i, ad in enumerate(kareler):
        plaka = Image.open(os.path.join(PLAKA_KARE, ad)).convert('RGB')
        t = 0.0 if i < yanma_bas else min(1.0, (i - yanma_bas) / yanma_sure)
        if t <= 0:
            plaka.save(os.path.join(CIKTI_KARE, ad)); continue

        # Parmak anahtari: plakada KOYU olan yerler ekran, aydinlik olan parmak
        gri = plaka.convert('L')
        ekran = gri.point(lambda v: 255 if v < 60 else (0 if v > 95 else int((95 - v) * 255 / 35)))
        maske = Image.composite(ekran, Image.new('L', boyut, 0), alan)
        maske = maske.filter(ImageFilter.GaussianBlur(0.8))
        maske = maske.point(lambda v: int(v * t))

        kat = Image.composite(ui_w, plaka, maske)

        # Ekran isigi: cevredeki kagida ve sakala mor sizinti
        parlak = Image.new('RGB', boyut, VIOLET)
        hale = maske.filter(ImageFilter.GaussianBlur(70)).point(lambda v: int(v * 0.30 * t))
        kat = Image.composite(Image.blend(kat, parlak, 0.35), kat, hale)
        kat.save(os.path.join(CIKTI_KARE, ad))
    print('kompozit bitti:', n, 'kare')


if __name__ == '__main__':
    main()
