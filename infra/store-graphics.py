# -*- coding: utf-8 -*-
"""Play Console gorselleri: magaza simgesi + one cikan grafik (TR + EN).

Cikti: store/play/{app-icon-512,feature-graphic-tr,feature-graphic-en}.png

## Neden betik (elle Photoshop degil)

Magaza gorseli ile uygulamanin kendisi arasinda gorsel sapma olmamali:
isaret uygulamanin KENDI launcher varligindan (assets/icon/), palet
rytho_theme.dart'tan geliyor. Marka degisirse bu betik yeniden kosulur ve
uc dosya birden guncellenir - elle uretilen bir gorsel bunu garanti etmez.

Bagimlilik: Pillow + Montserrat (Windows'ta kurulu). Sora kurulu olmadigi
icin Montserrat kullaniliyor - Sora'nin geometrik karsiligi.

Kosum:  python infra/store-graphics.py
"""
import math
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CIKTI = os.path.join(KOK, "store", "play")
ISARET = os.path.join(KOK, "apps", "mobile", "assets", "icon")
FONT_DIZIN = r"C:\Windows\Fonts"

# --- Palet: apps/mobile/lib/theme/rytho_theme.dart ile BIREBIR -------------
PARCHMENT = (0xF4, 0xEF, 0xFA)
PARCH_DIM = (0xA9, 0x9E, 0xC2)
VIOLET = (0x7B, 0x2F, 0xF7)
MAGENTA = (0xE6, 0x4A, 0xCF)
LILAC = (0xB7, 0x9C, 0xFF)
GOLD = (0xFF, 0xC2, 0x4B)
INK = (0x0B, 0x07, 0x10)

W, H = 1024, 500          # Play "one cikan grafik" olcusu (sabit)
BOY, MX = 290, 88         # isaretin boyu ve sol payi


def _font(ad, boyut):
    return ImageFont.truetype(os.path.join(FONT_DIZIN, ad), boyut)


def _degrade(w, h, ust, alt):
    tab = Image.new("RGB", (1, h))
    px = tab.load()
    for y in range(h):
        t = y / (h - 1)
        px[0, y] = tuple(int(ust[i] + (alt[i] - ust[i]) * t) for i in range(3))
    return tab.resize((w, h), Image.BILINEAR)


def _isik(boyut, lekeler, bulanik):
    """Toplanan isik katmani.

    `screen` ile birlestirilir: karanligi karanlik birakip yalniz isik
    ekler. Duz `blend` denendi ve moru yikayip metin kontrastini
    dusurmustu - kozmik derinlik yerine leke veriyordu.
    """
    kat = Image.new("RGB", boyut, (0, 0, 0))
    d = ImageDraw.Draw(kat)
    for (cx, cy), r, renk, guc in lekeler:
        d.ellipse([cx - r, cy - r, cx + r, cy + r],
                  fill=tuple(int(c * guc) for c in renk))
    return kat.filter(ImageFilter.GaussianBlur(bulanik))


def _vinyet(im, guc):
    w, h = im.size
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).ellipse([-w * 0.22, -h * 0.55, w * 1.22, h * 1.55], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(w * 0.12)).point(
        lambda v: int(255 - (255 - v) * guc))
    return Image.composite(im, Image.new("RGB", (w, h), (0x08, 0x05, 0x0C)), m)


def _yildiz4(d, cx, cy, r, renk, alfa=255):
    """Ikondaki dort kollu yildiz - marka surekliligi icin ayni bicim."""
    ic = r * 0.26
    nokta = []
    for i in range(8):
        aci = math.pi / 2 * (i / 2) - math.pi / 2
        yc = r if i % 2 == 0 else ic
        nokta.append((cx + yc * math.cos(aci), cy + yc * math.sin(aci)))
    d.polygon(nokta, fill=(*renk, alfa))


def magaza_simgesi():
    """512x512 magaza simgesi = launcher ikonunun aynisi.

    Play magaza simgesinin telefondaki simgeyle ayni olmasini bekliyor;
    ayri bir gorsel cizmek marka kopmasi yaratirdi.
    """
    kaynak = Image.open(os.path.join(ISARET, "app_icon.png")).convert("RGBA")
    kucuk = kaynak.resize((512, 512), Image.LANCZOS)
    zemin = Image.new("RGB", (512, 512), INK)   # alfa ink uzerine duzlestirilir
    zemin.paste(kucuk, (0, 0), kucuk)
    yol = os.path.join(CIKTI, "app-icon-512.png")
    zemin.save(yol, "PNG", optimize=True)
    return yol


def one_cikan(dosya, baslik, satir1, satir2):
    my = (H - BOY) // 2
    ccx, ccy = MX + BOY / 2, my + BOY / 2       # isaretin merkezi
    x = MX + BOY + 70                            # metin blogunun sol kenari
    f_ad = _font("Montserrat-SemiBold.ttf", 78)
    f_alt = _font("Montserrat-Light.ttf", 27)

    im = _degrade(W, H, (0x0B, 0x07, 0x11), (0x16, 0x0A, 0x21))
    im = ImageChops.screen(im, _isik((W, H), [
        ((ccx, ccy), 250, VIOLET, 0.30),         # isaretin arkasindaki derinlik
        ((905, 70), 250, MAGENTA, 0.13),         # sag ust sicaklik
        ((660, 480), 200, VIOLET, 0.07),         # alt denge
    ], 62))
    im = _vinyet(im, 0.78).convert("RGBA")

    # Metin bolgesi yildizdan arindirilir: harflerin arasina dusen noktalar
    # noktalama isareti gibi okunuyor ve dizgiyi kirletiyordu.
    olcu = ImageDraw.Draw(im)
    sag = max(olcu.textbbox((x, 0), s, font=f)[2]
              for s, f in ((baslik, f_ad), (satir1, f_alt), (satir2, f_alt)))
    yasak = (x - 14, 150, sag + 16, 400)

    kat = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(kat)
    r = random.Random(11)                        # sabit tohum: ciktilar tekrarlanabilir
    for _ in range(190):
        sx, sy = r.uniform(0, W), r.uniform(0, H)
        if yasak[0] < sx < yasak[2] and yasak[1] < sy < yasak[3]:
            continue
        yc = r.choice([0.6, 0.7, 0.9, 1.0, 1.4])
        d.ellipse([sx - yc, sy - yc, sx + yc, sy + yc],
                  fill=(*PARCHMENT, int(r.uniform(30, 150))))

    # Cark halkalari isaretle ESMERKEZLI: ikondaki halkanin devami gibi
    # okunsun diye. Serbest yerlestirilmis bir yay "kayik cizgi" goruntusu
    # veriyordu.
    for yc, alfa, kalinlik in ((BOY * 0.86, 40, 2), (BOY * 1.55, 22, 1),
                               (BOY * 2.5, 13, 1)):
        d.ellipse([ccx - yc, ccy - yc, ccx + yc, ccy + yc],
                  outline=(*LILAC, alfa), width=kalinlik)
    for aci in (-31, 12, 47):                    # aci kirisleri (ikondaki dil)
        r0, r1 = BOY * 0.86, BOY * 2.5
        t = math.radians(aci)
        d.line([ccx + r0 * math.cos(t), ccy + r0 * math.sin(t),
                ccx + r1 * math.cos(t), ccy + r1 * math.sin(t)],
               fill=(*LILAC, 18), width=1)
    im = Image.alpha_composite(im, kat)

    # Isaret: once yumusak lila hale, sonra net beyaz
    mark = Image.open(os.path.join(ISARET, "app_icon_foreground.png")) \
        .convert("RGBA").resize((BOY, BOY), Image.LANCZOS)
    hale = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hale.paste(Image.new("RGBA", (BOY, BOY), (*LILAC, 165)), (MX, my), mark)
    im = Image.alpha_composite(im, hale.filter(ImageFilter.GaussianBlur(32)))
    net = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    net.paste(Image.new("RGBA", (BOY, BOY), (*PARCHMENT, 255)), (MX, my), mark)
    im = Image.alpha_composite(im, net)

    d = ImageDraw.Draw(im)
    ad_y = 168
    d.text((x, ad_y), baslik, font=f_ad, fill=(*PARCHMENT, 255))
    alt = d.textbbox((x, ad_y), baslik, font=f_ad)[3] + 30
    d.line([x + 1, alt, x + 44, alt], fill=(*GOLD, 215), width=2)
    _yildiz4(d, x + 62, alt, 7, GOLD, 240)
    d.text((x, alt + 26), satir1, font=f_alt, fill=(*PARCH_DIM, 255))
    d.text((x, alt + 64), satir2, font=f_alt, fill=(*PARCH_DIM, 255))

    yol = os.path.join(CIKTI, dosya)
    im.convert("RGB").save(yol, "PNG", optimize=True)
    return yol


if __name__ == "__main__":
    os.makedirs(CIKTI, exist_ok=True)
    uretilen = [
        magaza_simgesi(),
        one_cikan("feature-graphic-tr.png", "Rytho AI",
                  "Kişisel astroloji rehberin —", "gerçek gökyüzü hesabıyla."),
        one_cikan("feature-graphic-en.png", "Rytho AI",
                  "Your personal astrology guide,",
                  "powered by real sky calculations."),
    ]
    for yol in uretilen:
        with Image.open(yol) as im:
            print(f"{os.path.basename(yol)}: {im.size[0]}x{im.size[1]} "
                  f"{os.path.getsize(yol) / 1024:.0f} KB")
