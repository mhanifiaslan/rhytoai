# -*- coding: utf-8 -*-
"""Kurguda KACAK REFERANS KARESI var mi?

Neden: v2'de karakter turnaround sayfasi (beyaz studyo zemini) ve
elemenet kitap referansi kurguya sizdi. Ikisi de ayni imzayi tasiyor:
film boyunca her sey mum/mesale isikli KOYU bir sahne iken referans
kareleri PARLAK ve DUSUK DOYGUNLUKLU bir zemine oturuyor.

Bu betik filmi tarar ve o imzayi tasiyan kareleri bildirir. Goz
denetimi yerine gecmez ama ayni sinif hatanin bir daha sessizce
gecmesini engeller.

Kosum:  python denetim.py <film.mp4> [esik]
"""
import os
import subprocess
import sys
import tempfile

FF = r"C:\Users\pv\Downloads\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"
ESIK_PARLAK = 150.0   # ortalama parlaklik (0-255)
ESIK_DOYGUN = 40.0    # ortalama doygunluk; studyo zemini cok dusuk kalir


def main():
    film = sys.argv[1]
    fps = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
    from PIL import Image, ImageStat
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([FF, '-y', '-v', 'error', '-i', film,
                        '-vf', f'fps={fps},scale=160:-1',
                        os.path.join(tmp, '%05d.png')], check=True)
        kareler = sorted(os.listdir(tmp))
        suphe = []
        for i, ad in enumerate(kareler):
            im = Image.open(os.path.join(tmp, ad)).convert('RGB')
            parlak = ImageStat.Stat(im.convert('L')).mean[0]
            doygun = ImageStat.Stat(im.convert('HSV').getchannel('S')).mean[0]
            if parlak > ESIK_PARLAK and doygun < ESIK_DOYGUN:
                suphe.append((i / fps, round(parlak, 1), round(doygun, 1)))
        print(f'{len(kareler)} kare tarandi ({fps} fps)')
        if not suphe:
            print('TEMIZ: kacak referans karesi imzasi yok.')
            return 0
        print(f'SUPHELI {len(suphe)} kare:')
        for t, p, d in suphe:
            print(f'  {t:6.2f} sn  parlaklik={p:5.1f} doygunluk={d:5.1f}')
        return 1


if __name__ == '__main__':
    sys.exit(main())
