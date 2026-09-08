# -*- coding: utf-8 -*-
"""Modern Rytho reklami (son bolum) - kare kare uretici.

Neden kare kare Pillow:
  Bu bolum tek basina yayinlanabilir bir reklam olmali. Slayt gosterisi
  hissini kiran sey hareketin KENDISI: her ogenin girisi/cikisi ustuste
  biniyor, hicbir kare durgun degil. ffmpeg filtreleriyle bu koreografi
  okunaksiz olurdu; burada her karenin zamani acikca hesaplaniyor.

Marka sozlesmesi:
  * Palet apps/mobile/lib/theme/rytho_theme.dart ile birebir.
  * Tipografi uygulamanin GERCEK yuzu: Sora (baslik) + Manrope (govde).
    Magaza grafiklerindeki Montserrat vekildi; reklamin derdi tam olarak
    markali durmak oldugu icin burada vekil kullanilmiyor.
  * Hareket egrileri web/assets/rytho.css'ten: --enter easeOutCubic,
    --pop easeOutBack. Reklam uygulamanin kendi hareket dilini konusuyor.
  * Ekrandaki her arayuz GERCEK cihaz kaydi (adb screenrecord). Uydurma
    arayuz yok - "ekrandaki cevap gercek uygulama ciktisidir" kurali.

Kosum:  python reklam.py            (once hazirlik.sh ile kareler cikarilir)
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

KOK = os.path.dirname(os.path.abspath(__file__))
IS = os.path.join(KOK, 'reklam')
CIKTI = os.path.join(IS, 'out')

W, H = 1080, 1920
FPS = 24
SURE = 15.0
N = int(SURE * FPS)

# --- Palet: rytho_theme.dart ------------------------------------------
INK = (0x0B, 0x07, 0x10)
INK_DEEP = (0x14, 0x09, 0x1E)
PARCHMENT = (0xF4, 0xEF, 0xFA)
PARCH_DIM = (0xA9, 0x9E, 0xC2)
VIOLET = (0x7B, 0x2F, 0xF7)
PURPLE = (0xB0, 0x2E, 0xFF)
MAGENTA = (0xE6, 0x4A, 0xCF)
LILAC = (0xB7, 0x9C, 0xFF)
GOLD = (0xFF, 0xC2, 0x4B)

SORA = os.path.join(KOK, 'fonts', 'Sora.ttf')
MANROPE = os.path.join(KOK, 'fonts', 'Manrope.ttf')


def font(yol, boyut, varyant='SemiBold'):
    f = ImageFont.truetype(yol, boyut)
    try:
        f.set_variation_by_name(varyant)
    except Exception:
        pass
    return f


# --- Hareket egrileri: web/assets/rytho.css ---------------------------
def gir(t):
    """--enter, easeOutCubic."""
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def pop(t):
    """--pop, easeOutBack."""
    t = max(0.0, min(1.0, t))
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def aralik(t, bas, bit):
    """[bas, bit] penceresinde 0->1 ilerleme."""
    if bit <= bas:
        return 1.0 if t >= bit else 0.0
    return max(0.0, min(1.0, (t - bas) / (bit - bas)))


def kare_dizi(dizin):
    if not os.path.isdir(dizin):
        return []
    return [os.path.join(dizin, a) for a in sorted(os.listdir(dizin))
            if a.endswith('.png')]


class Kaynak:
    """Onceden cikarilmis PNG dizisi; istenen kareyi olcekli dondurur."""

    def __init__(self, dizin, boy=None, kirp=None):
        self.yollar = kare_dizi(dizin)
        self.boy = boy
        self.kirp = kirp
        self._onbellek = {}

    def __len__(self):
        return len(self.yollar)

    def al(self, i):
        if not self.yollar:
            return None
        i = max(0, min(len(self.yollar) - 1, i))
        if i in self._onbellek:
            return self._onbellek[i]
        im = Image.open(self.yollar[i]).convert('RGB')
        if self.kirp:
            im = im.crop(self.kirp)
        if self.boy:
            im = im.resize(self.boy, Image.LANCZOS)
        if len(self._onbellek) > 80:
            self._onbellek.clear()
        self._onbellek[i] = im
        return im


def yuvarlat(im, r):
    m = Image.new('L', im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width - 1, im.height - 1],
                                        radius=r, fill=255)
    out = im.convert('RGBA')
    out.putalpha(m)
    return out


def yildiz4(d, cx, cy, r, renk, alfa=255):
    """Ikondaki dort kollu yildiz - marka surekliligi."""
    ic = r * 0.26
    p = []
    for i in range(8):
        aci = math.pi / 2 * (i / 2) - math.pi / 2
        yc = r if i % 2 == 0 else ic
        p.append((cx + yc * math.cos(aci), cy + yc * math.sin(aci)))
    d.polygon(p, fill=(*renk, int(alfa)))


def zemin(bg, i, t):
    """Nebula plakasi + degrade + vinyet. Plaka yoksa yordamsal yildiz alani."""
    if len(bg):
        im = bg.al(i % len(bg)).copy()
        im = Image.blend(im, Image.new('RGB', (W, H), INK), 0.30)
    else:
        im = Image.new('RGB', (W, H), INK)
        d = ImageDraw.Draw(im)
        for y in range(0, H, 4):
            k = y / H
            d.rectangle([0, y, W, y + 4], fill=tuple(
                int(INK[j] + (INK_DEEP[j] - INK[j]) * k) for j in range(3)))
    # merkez sicaklik
    hale = Image.new('RGB', (W, H), (0, 0, 0))
    hd = ImageDraw.Draw(hale)
    r = 520 + 40 * math.sin(t * 0.7)
    hd.ellipse([W / 2 - r, H * 0.42 - r, W / 2 + r, H * 0.42 + r],
               fill=tuple(int(c * 0.22) for c in VIOLET))
    hale = hale.filter(ImageFilter.GaussianBlur(180))
    from PIL import ImageChops
    im = ImageChops.screen(im, hale)
    # vinyet
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).ellipse([-W * 0.30, -H * 0.18, W * 1.30, H * 1.18], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(240)).point(lambda v: int(255 - (255 - v) * 0.85))
    return Image.composite(im, Image.new('RGB', (W, H), (6, 4, 9)), m)


def isaret_kur(kat, t, mark):
    """0.0-2.2 sn: isik noktasi -> yorunge halkasi cizilir -> isaret belirir."""
    d = ImageDraw.Draw(kat)
    cx, cy = W / 2, H * 0.40

    # 1) isik noktasi
    a0 = aralik(t, 0.10, 0.55)
    if a0 > 0:
        r = 4 + 26 * gir(a0)
        for k, al in ((r * 3.2, 40), (r * 1.8, 90), (r, 230)):
            d.ellipse([cx - k, cy - k, cx + k, cy + k],
                      fill=(*PARCHMENT, int(al * a0)))

    # 2) yorunge halkasi kendini cizer
    a1 = aralik(t, 0.45, 1.35)
    if a1 > 0:
        R = 232
        yay = 360 * gir(a1)
        d.arc([cx - R, cy - R, cx + R, cy + R], -90, -90 + yay,
              fill=(*LILAC, 190), width=3)
        # halka uzerindeki dugumler
        for j, ac in enumerate((-90, 30, 150)):
            ap = aralik(t, 0.75 + j * 0.10, 1.05 + j * 0.10)
            if ap > 0:
                rr = 9 * pop(ap)
                nx = cx + R * math.cos(math.radians(ac))
                ny = cy + R * math.sin(math.radians(ac))
                d.ellipse([nx - rr, ny - rr, nx + rr, ny + rr],
                          fill=(*PARCHMENT, 235))

    # 3) isaret
    a2 = aralik(t, 1.20, 2.05)
    if a2 > 0 and mark is not None:
        e = gir(a2)
        boy = int(300 * (0.86 + 0.14 * e))
        m = mark.resize((boy, boy), Image.LANCZOS)
        x, y = int(cx - boy / 2), int(cy - boy / 2)
        hale = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        hale.paste(Image.new('RGBA', (boy, boy), (*LILAC, int(150 * e))), (x, y), m)
        kat.alpha_composite(hale.filter(ImageFilter.GaussianBlur(34)))
        net = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        net.paste(Image.new('RGBA', (boy, boy), (*PARCHMENT, int(255 * e))), (x, y), m)
        kat.alpha_composite(net)
    return kat


def kelime_isareti(kat, t):
    """2.05-4.60 sn: RYTHO AI harf harf; altinda altin cizgi + yildiz."""
    a = aralik(t, 2.05, 3.10)
    if a <= 0:
        return
    d = ImageDraw.Draw(kat)
    f = font(SORA, 108, 'Bold')
    metin = 'RYTHO AI'
    tam = d.textlength(metin, font=f)
    x0 = (W - tam) / 2
    y0 = H * 0.53
    n = len(metin)
    for i, ch in enumerate(metin):
        ai = aralik(a, i / (n + 3), (i + 3) / (n + 3))
        if ai <= 0:
            continue
        e = gir(ai)
        dx = d.textlength(metin[:i], font=f)
        d.text((x0 + dx, y0 + 26 * (1 - e)), ch, font=f,
               fill=(*PARCHMENT, int(255 * e)))

    ac = aralik(t, 3.00, 3.55)
    if ac > 0:
        e = gir(ac)
        cy = y0 + 150
        L = 120 * e
        d.line([W / 2 - 40 - L, cy, W / 2 - 40, cy], fill=(*GOLD, 210), width=2)
        d.line([W / 2 + 40, cy, W / 2 + 40 + L, cy], fill=(*GOLD, 210), width=2)
        yildiz4(d, W / 2, cy, 11 * pop(ac), GOLD, 240)

    at = aralik(t, 3.35, 3.95)
    if at > 0:
        e = gir(at)
        fb = font(MANROPE, 40, 'Medium')
        s = 'Astrology, computed.'
        w = d.textlength(s, font=fb)
        d.text(((W - w) / 2, y0 + 190 + 16 * (1 - e)), s, font=fb,
               fill=(*PARCH_DIM, int(235 * e)))


def kart(kat, t, kaynak, kare_i, bas, bit, etiket):
    """Gercek arayuz kaydi: yuvarlatilmis kart, paralaks giris/cikis.

    Giris ve cikis pencereleri bilerek UST USTE biniyor (bir sonraki kart
    oncekinin cikisi bitmeden giriyor) - "slayt" hissini kiran sey bu.
    """
    if not len(kaynak):
        return
    ag = 0.55   # giris suresi
    ac = 0.55   # cikis suresi
    if t < bas - ag or t > bit + ac:
        return
    gi = aralik(t, bas - ag, bas + 0.10)
    ci = aralik(t, bit, bit + ac)
    e = gir(gi)
    alfa = int(255 * e * (1 - gir(ci)))
    if alfa <= 2:
        return

    im = kaynak.al(kare_i)
    if im is None:
        return
    kw = im.width
    kh = im.height
    # paralaks: yukaridan gelir, cikarken yukari suzulur
    ilerleme = aralik(t, bas - ag, bit + ac)
    y = int(H * 0.335 + 90 * (1 - e) - 70 * ilerleme)
    x = int((W - kw) / 2)

    kutu = yuvarlat(im, 34)
    # mor hale
    hale = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    hale.paste(Image.new('RGBA', (kw, kh), (*VIOLET, int(150 * e))), (x, y), kutu)
    kat.alpha_composite(hale.filter(ImageFilter.GaussianBlur(60)))
    # kartin kendisi
    tmp = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    tmp.paste(kutu, (x, y), kutu)
    if alfa < 255:
        al = tmp.getchannel('A').point(lambda v: int(v * alfa / 255))
        tmp.putalpha(al)
    kat.alpha_composite(tmp)
    # ince lila kenar
    d = ImageDraw.Draw(kat)
    d.rounded_rectangle([x, y, x + kw - 1, y + kh - 1], radius=34,
                        outline=(*LILAC, int(90 * e * (1 - gir(ci)))), width=2)

    # etiket
    ae = aralik(t, bas - 0.15, bas + 0.35)
    if ae > 0:
        ee = gir(ae) * (1 - gir(ci))
        f = font(SORA, 58, 'SemiBold')
        w = d.textlength(etiket, font=f)
        ey = y + kh + 54
        yildiz4(d, (W - w) / 2 - 34, ey + 30, 9, GOLD, int(230 * ee))
        d.text(((W - w) / 2, ey + 14 * (1 - gir(ae))), etiket, font=f,
               fill=(*PARCHMENT, int(255 * ee)))


def kapanis(kat, t, mark):
    """11.8-15.0 sn: isaret geri doner, slogan, magaza satiri."""
    a = aralik(t, 11.75, 12.60)
    if a <= 0:
        return
    d = ImageDraw.Draw(kat)
    cx, cy = W / 2, H * 0.42
    e = gir(a)
    if mark is not None:
        boy = int(250 * (0.90 + 0.10 * e))
        m = mark.resize((boy, boy), Image.LANCZOS)
        x, y = int(cx - boy / 2), int(cy - boy / 2)
        hale = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        hale.paste(Image.new('RGBA', (boy, boy), (*LILAC, int(140 * e))), (x, y), m)
        kat.alpha_composite(hale.filter(ImageFilter.GaussianBlur(30)))
        net = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        net.paste(Image.new('RGBA', (boy, boy), (*PARCHMENT, int(255 * e))), (x, y), m)
        kat.alpha_composite(net)

    aw = aralik(t, 12.15, 12.85)
    if aw > 0:
        ew = gir(aw)
        f = font(SORA, 92, 'Bold')
        s = 'RYTHO AI'
        w = d.textlength(s, font=f)
        d.text(((W - w) / 2, cy + 175 + 18 * (1 - ew)), s, font=f,
               fill=(*PARCHMENT, int(255 * ew)))

    ar = aralik(t, 12.65, 13.20)
    if ar > 0:
        er = gir(ar)
        ly = cy + 320
        L = 110 * er
        d.line([W / 2 - 38 - L, ly, W / 2 - 38, ly], fill=(*GOLD, 210), width=2)
        d.line([W / 2 + 38, ly, W / 2 + 38 + L, ly], fill=(*GOLD, 210), width=2)
        yildiz4(d, W / 2, ly, 11 * pop(ar), GOLD, 240)

    asl = aralik(t, 12.95, 13.70)
    if asl > 0:
        es = gir(asl)
        f = font(SORA, 66, 'SemiBold')
        s = 'Ask the sky.'
        w = d.textlength(s, font=f)
        d.text(((W - w) / 2, cy + 372 + 16 * (1 - es)), s, font=f,
               fill=(*GOLD, int(250 * es)))

    am = aralik(t, 13.55, 14.20)
    if am > 0:
        em = gir(am)
        f = font(MANROPE, 38, 'Medium')
        s = 'Now on Google Play'
        w = d.textlength(s, font=f)
        d.text(((W - w) / 2, cy + 486), s, font=f,
               fill=(*PARCH_DIM, int(225 * em)))


def main():
    os.makedirs(CIKTI, exist_ok=True)
    bg = Kaynak(os.path.join(IS, 'bg'), boy=(W, H))
    cark = Kaynak(os.path.join(IS, 'cark'))
    sohbet = Kaynak(os.path.join(IS, 'sohbet'))
    gok = Kaynak(os.path.join(IS, 'gok'))
    mark = None
    yol = os.path.join(os.path.dirname(KOK), '..', 'apps', 'mobile',
                       'assets', 'icon', 'app_icon_foreground.png')
    yol = os.path.normpath(yol)
    if os.path.exists(yol):
        mark = Image.open(yol).convert('RGBA').getchannel('A')

    print('kaynaklar: bg=%d cark=%d sohbet=%d gok=%d' %
          (len(bg), len(cark), len(sohbet), len(gok)))

    for i in range(N):
        t = i / FPS
        im = zemin(bg, i, t).convert('RGBA')
        kat = Image.new('RGBA', (W, H), (0, 0, 0, 0))

        # Acilis kimligi AYRI katmanda: ilk kart girmeden once topluca
        # sonuyor. (Tek katmanda cizilseydi kapanistaki kelime isaretiyle
        # ust uste binerdi - ilk denemede oyle oldu.)
        giris = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        isaret_kur(giris, t, mark)
        kelime_isareti(giris, t)
        cik = 1 - gir(aralik(t, 4.05, 4.70))
        if cik <= 0.004:
            giris = None
        elif cik < 1:
            giris.putalpha(giris.getchannel('A').point(lambda v: int(v * cik)))
        if giris is not None:
            kat.alpha_composite(giris)
        # Cark karti: gercek supurme kaydi, yavaslatilmis
        kart(kat, t, cark, int((t - 4.55) * FPS * 0.62), 4.55, 7.05,
             'Your real chart')
        kart(kat, t, sohbet, int((t - 7.30) * FPS), 7.30, 9.75,
             'Ask anything')
        kart(kat, t, gok, int((t - 10.00) * FPS), 10.00, 11.55,
             'Every single day')
        kapanis(kat, t, mark)

        im.alpha_composite(kat)
        # acilis ve kapanista siyaha yumusama
        f0 = aralik(t, 0.0, 0.35)
        f1 = 1 - aralik(t, SURE - 0.45, SURE)
        k = min(f0, f1)
        if k < 1:
            im = Image.blend(Image.new('RGBA', (W, H), (0, 0, 0, 255)), im, k)
        im.convert('RGB').save(os.path.join(CIKTI, '%04d.png' % i))
        if i % 40 == 0:
            print('  kare', i, '/', N)
    print('bitti:', N, 'kare')


if __name__ == '__main__':
    main()
