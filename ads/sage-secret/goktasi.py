# -*- coding: utf-8 -*-
"""Temiz gokyuzu plakasina GERCEKCI goktasi bindirir.

Neden model degil de burasi:
  Uretilen planlarda goktaslari (a) yukari dogru ucuyordu, (b) 3 saniye
  boyunca gokyuzunde ASILI kaliyordu. Ikisi de fizige aykiri ve modele
  tarifle duzelttirilemedi. Burada uc sey acikca kontrol ediliyor:
    * YON  - hepsi ufka dogru INIYOR (dy > 0, dik acilar)
    * OMUR - 0.3-0.6 sn; gercek goktasi bir anlik olaydir
    * IZ   - bas parlak, kuyruk arkada kalir ve soner (once cizilen
             cizgi degil, HAREKETLE olusan iz)

Karisim `screen`: gokyuzunu karartmadan yalniz isik ekler.

Kosum:  python goktasi.py <kaynak_dizin> <cikti_dizin> [ufuk_orani]
"""
import math
import os
import random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

FPS = 24


def yumusat(v):
    """0..1 -> giris/cikis zarfi (hizli parla, yavas son)."""
    if v < 0.12:
        return v / 0.12
    if v > 0.62:
        return max(0.0, 1 - (v - 0.62) / 0.38)
    return 1.0


def goktaslari(n_kare, W, H, ufuk, tohum=7):
    """Determinist goktasi listesi. Hepsi ASAGI iner."""
    r = random.Random(tohum)
    liste = []
    # (dogum orani, omur sn, parlaklik, kalinlik)
    sablon = [
        (0.02, 0.50, 1.00, 5.0),
        (0.13, 0.42, 0.80, 3.6),
        (0.25, 0.58, 1.00, 6.0),   # parlak (atesTopu)
        (0.32, 0.36, 0.68, 3.0),
        (0.45, 0.46, 0.90, 4.4),
        (0.56, 0.40, 0.78, 3.4),
        (0.64, 0.60, 1.00, 6.4),   # parlak (atesTopu)
        (0.77, 0.38, 0.72, 3.2),
    ]
    for oran, omur, parlak, kalin in sablon:
        # dik inis: 55-78 derece, ekranin ustunden baslar
        aci = math.radians(r.uniform(55, 78)) * r.choice([1, -1])
        dx, dy = math.sin(aci), math.cos(aci)      # dy hep pozitif -> ASAGI
        x0 = r.uniform(-0.15, 1.15) * W
        y0 = r.uniform(-0.10, 0.16) * H
        yol = r.uniform(0.50, 0.82) * H            # kat edilen mesafe
        liste.append(dict(
            b=int(oran * n_kare), L=max(4, int(omur * FPS)),
            x0=x0, y0=y0, dx=dx, dy=dy, yol=yol,
            parlak=parlak, kalin=kalin,
            iz=r.uniform(0.22, 0.34)))             # kuyruk / yol orani
    return liste


def kare_ciz(W, H, ufuk, mets, i):
    kat = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(kat)
    cizildi = False
    for m in mets:
        u = (i - m['b']) / m['L']
        if u < 0 or u > 1:
            continue
        zarf = yumusat(u)
        if zarf <= 0:
            continue
        bas_x = m['x0'] + m['dx'] * m['yol'] * u
        bas_y = m['y0'] + m['dy'] * m['yol'] * u
        if bas_y > ufuk:                            # ufkun altina inmez
            continue
        kuyruk = m['yol'] * m['iz'] * min(1.0, u * 3.5)
        son_x = bas_x - m['dx'] * kuyruk
        son_y = bas_y - m['dy'] * kuyruk
        # kuyruk parcali cizilir: uca dogru soner ve incelir
        N = 22
        for k in range(N):
            t0, t1 = k / N, (k + 1) / N
            ax = bas_x + (son_x - bas_x) * t0
            ay = bas_y + (son_y - bas_y) * t0
            bx = bas_x + (son_x - bas_x) * t1
            by = bas_y + (son_y - bas_y) * t1
            g = (1 - t0) ** 2.2
            d.line([ax, ay, bx, by],
                   fill=int(255 * g * zarf * m['parlak']),
                   width=max(1, int(m['kalin'] * (1 - t0 * 0.75))))
        # bas: kucuk parlak nokta
        rr = m['kalin'] * 1.5
        d.ellipse([bas_x - rr, bas_y - rr, bas_x + rr, bas_y + rr],
                  fill=int(255 * zarf * m['parlak']))
        cizildi = True
    if not cizildi:
        return None
    net = kat.filter(ImageFilter.GaussianBlur(1.1))
    hale = kat.filter(ImageFilter.GaussianBlur(18)).point(lambda v: min(255, int(v * 0.85)))
    return ImageChops.lighter(net, hale)


def main():
    kaynak, cikti = sys.argv[1], sys.argv[2]
    ufuk_orani = float(sys.argv[3]) if len(sys.argv) > 3 else 0.60
    os.makedirs(cikti, exist_ok=True)
    kareler = sorted(a for a in os.listdir(kaynak) if a.endswith('.png'))
    W, H = Image.open(os.path.join(kaynak, kareler[0])).size
    ufuk = H * ufuk_orani
    mets = goktaslari(len(kareler), W, H, ufuk)
    # hafif sicak-beyaz ton: saf beyaz cizik "cizim" gibi duruyor
    renk = (255, 246, 226)
    for i, ad in enumerate(kareler):
        plaka = Image.open(os.path.join(kaynak, ad)).convert('RGB')
        maske = kare_ciz(W, H, ufuk, mets, i)
        if maske is None:
            plaka.save(os.path.join(cikti, ad)); continue
        isik = Image.new('RGB', (W, H), (0, 0, 0))
        isik.paste(Image.new('RGB', (W, H), renk), (0, 0), maske)
        plaka = ImageChops.screen(plaka, isik)
        plaka.save(os.path.join(cikti, ad))
    print('goktasi bindirildi:', len(kareler), 'kare,', len(mets), 'goktasi')


if __name__ == '__main__':
    main()
