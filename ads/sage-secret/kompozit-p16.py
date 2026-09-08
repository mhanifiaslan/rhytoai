# -*- coding: utf-8 -*-
"""P16 - bilgenin gozunden kitabin oyugundaki telefon; ekranda GERCEK
gok haritasi kendini ciziyor.

v1'den iki fark:
  * Bindirilen sey durgun ekran goruntusu DEGIL, video: Atlas carkinin
    kendini cizmesi (adb screenrecord, 60 fps). "Yapistirilmis ekran
    goruntusu" hissinin asil sebebi hareketsizlikti.
  * Arayuz dortgene GERILEREK oturtulmuyor: once dortgenin en-boy
    oranina gore ORTADAN KIRPILIYOR, sonra yerlestiriliyor. v1'de
    telefonun "tablet gibi" gorunmesinin sebebi bu orandi.

Dortgen olculdu (goz karariyla degil): esik altindaki koyu bileseninin
satir/sutun taramasiyla, kamera kilitli oldugu icin tek dortgen tum
kareler icin gecerli (ilk/son kare ortalama farki 1.09/255).
"""
import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

KOK = os.path.dirname(os.path.abspath(__file__))
PLAKA = os.path.join(KOK, 'frames', 'p16src')
UI = os.path.join(KOK, 'frames', 'p16ui')
CIKTI = os.path.join(KOK, 'frames', 'p16out')

# SOL-UST, SAG-UST, SAG-ALT, SOL-ALT  (3 px iceri alindi: cam kenari kalsin)
QUAD = [(408, 604), (663, 596), (658, 1186), (412, 1192)]
VIOLET = (0x7B, 0x2F, 0xF7)

UYANMA_BAS = 14      # kare: ekran bu kareye kadar mat siyah
UYANMA_SURE = 12     # kare: acilma rampasi
CIZIM_BAS = 26       # cark supurmesinin basladigi kare
CIZIM_BIT = 100      # supurmenin bittigi kare (sonrasi sabit tutulur)


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


def _hedef_oran():
    (x1, y1), (x2, y2), (x3, y3), (x4, y4) = QUAD
    w = ((x2 - x1) + (x3 - x4)) / 2
    h = ((y4 - y1) + (y3 - y2)) / 2
    return h / w


def hazirla(ui):
    """Dortgenin oranina ORTADAN kirp, sonra mum isigina uydur.

    Gerilme yok: telefon telefon gibi dursun.
    """
    ui = ui.convert('RGB')
    w, h = ui.size
    ui = ui.crop((0, 40, w, h - 30))          # durum/gezinme cubuklari
    w, h = ui.size
    hedef = _hedef_oran()
    if h / w > hedef:                          # cok uzun -> boydan kirp
        yeni_h = int(w * hedef)
        ust = (h - yeni_h) // 2
        ui = ui.crop((0, ust, w, ust + yeni_h))
    else:                                      # cok genis -> enden kirp
        yeni_w = int(h / hedef)
        sol = (w - yeni_w) // 2
        ui = ui.crop((sol, 0, sol + yeni_w, h))
    ui = ImageEnhance.Brightness(ui).enhance(0.90)
    ui = ImageEnhance.Color(ui).enhance(0.94)
    amber = Image.new('RGB', ui.size, (255, 176, 96))
    return Image.blend(ui, amber, 0.05)


def main():
    plakalar = sorted(os.listdir(PLAKA))
    uiler = sorted(a for a in os.listdir(UI) if a.endswith('.png'))
    os.makedirs(CIKTI, exist_ok=True)
    boyut = Image.open(os.path.join(PLAKA, plakalar[0])).size
    n = len(plakalar)
    nu = len(uiler)

    alan = Image.new('L', boyut, 0)
    ImageDraw.Draw(alan).polygon(QUAD, fill=255)
    alan = alan.filter(ImageFilter.GaussianBlur(1.0))

    onbellek = {}
    for i, ad in enumerate(plakalar):
        plaka = Image.open(os.path.join(PLAKA, ad)).convert('RGB')
        t = 0.0 if i < UYANMA_BAS else min(1.0, (i - UYANMA_BAS) / UYANMA_SURE)
        if t <= 0:
            plaka.save(os.path.join(CIKTI, ad)); continue

        # cark supurmesi: CIZIM_BAS..CIZIM_BIT arasinda yayilir, sonra donar
        if i <= CIZIM_BAS:
            ui_i = 0
        elif i >= CIZIM_BIT:
            ui_i = nu - 1
        else:
            ui_i = int((i - CIZIM_BAS) * (nu - 1) / (CIZIM_BIT - CIZIM_BAS))
        ui_i = max(0, min(nu - 1, ui_i))

        if ui_i not in onbellek:
            src = Image.open(os.path.join(UI, uiler[ui_i]))
            k = perspektif_katsayi(QUAD, hazirla(src).size)
            onbellek.clear()
            onbellek[ui_i] = hazirla(src).transform(
                boyut, Image.PERSPECTIVE, k, Image.BICUBIC)
        ui_w = onbellek[ui_i]

        maske = alan.point(lambda v: int(v * t))
        kat = Image.composite(ui_w, plaka, maske)

        # ekran isigi: ellere ve deriye mor sizinti
        hale = maske.filter(ImageFilter.GaussianBlur(64)).point(
            lambda v: int(v * 0.30 * t))
        kat = Image.composite(
            Image.blend(kat, Image.new('RGB', boyut, VIOLET), 0.28), kat, hale)
        kat.save(os.path.join(CIKTI, ad))
        if i % 25 == 0:
            print('  kare', i, '/', n)
    print('p16 kompozit bitti:', n, 'kare')


if __name__ == '__main__':
    main()
