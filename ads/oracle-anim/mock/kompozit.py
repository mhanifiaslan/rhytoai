"""Kanit kompoziti: siyah zeminli para still'i uygulamanin GERCEK ekran
goruntusu ustune SCREEN karisimiyla bindirilir — tepsi yok, mekan yok.
Uygulamada da ayni sey yapilacak: kare dizisi, canvas'a BlendMode.screen ile.
Kullanim: python kompozit.py <para.png> <ekran.png> <cikti.png>
"""
import sys
from PIL import Image, ImageChops, ImageFilter

para = Image.open(sys.argv[1]).convert("RGB")
ekran = Image.open(sys.argv[2]).convert("RGB")
W, H = ekran.size
# Kart bolgesi: telefon ekraninin ortasinda 16:9 bir cam panel gibi.
kw = int(W * 0.88); kh = int(kw * 9 / 16)
x0 = (W - kw) // 2; y0 = int(H * 0.30)
para = para.resize((kw, kh), Image.LANCZOS)
# Kenarlarda yumusak vinyet: paralar disindaki artik siyah/gri sizintilar
# screen'de zaten gorunmez, ama kenar yumusatma kartla kaynastirir.
maske = Image.new("L", (kw, kh), 255)
maske = maske.filter(ImageFilter.GaussianBlur(0))
zemin = ekran.crop((x0, y0, x0 + kw, y0 + kh))
karisik = ImageChops.screen(zemin, para)
ekran.paste(karisik, (x0, y0))
ekran.save(sys.argv[3])
print("yazildi", sys.argv[3], ekran.size)
