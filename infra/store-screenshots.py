# -*- coding: utf-8 -*-
"""Play ekran goruntuleri: ham cihaz karesi -> 1080x1920 (9:16) magaza karesi.

Play "16:9 veya 9:16" istiyor; telefon 1080x2392 (9:20) cekiyor, oldugu gibi
yuklenirse REDDEDILIYOR. Bu yuzden ham kare kirpilip marka zeminine oturur.
"""
import os
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

KOK=r"D:\antigravityprojects\astroaiproject"; HAM=KOK+r"\store\play\raw"; CIK=KOK+r"\store\play"
F=r"C:\Windows\Fonts"
PARCHMENT=(0xF4,0xEF,0xFA); VIOLET=(0x7B,0x2F,0xF7); MAGENTA=(0xE6,0x4A,0xCF); LILAC=(0xB7,0x9C,0xFF)
W,H=1080,1920

def degrade(w,h,u,a):
    t=Image.new("RGB",(1,h)); p=t.load()
    for y in range(h):
        k=y/(h-1); p[0,y]=tuple(int(u[i]+(a[i]-u[i])*k) for i in range(3))
    return t.resize((w,h),Image.BILINEAR)

def isik(bo,lk,bl):
    kat=Image.new("RGB",bo,(0,0,0)); d=ImageDraw.Draw(kat)
    for (cx,cy),r,c,g in lk: d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=tuple(int(v*g) for v in c))
    return kat.filter(ImageFilter.GaussianBlur(bl))

def yuvarlat(im,r):
    m=Image.new("L",im.size,0)
    ImageDraw.Draw(m).rounded_rectangle([0,0,im.size[0]-1,im.size[1]-1],r,fill=255)
    im=im.convert("RGBA"); im.putalpha(m); return im

def kare(ham,kirp,baslik,cikti):
    im=degrade(W,H,(0x0B,0x07,0x11),(0x17,0x0A,0x22))
    im=ImageChops.screen(im,isik((W,H),[((540,260),400,VIOLET,0.22),
                                        ((940,1780),360,MAGENTA,0.09)],120)).convert("RGBA")
    s=Image.open(os.path.join(HAM,ham)).convert("RGB").crop(kirp)
    # Kullanilabilir alan: baslik altindan alt paya kadar
    ust,alt_pay=270,70
    en_boy=H-ust-alt_pay
    gen=920; boy=int(s.height*gen/s.width)
    if boy>en_boy:                       # cok uzunsa yukseklige gore olcekle
        boy=en_boy; gen=int(s.width*boy/s.height)
    s=yuvarlat(s.resize((gen,boy),Image.LANCZOS),32)
    x=(W-gen)//2; y=ust+(en_boy-boy)//2
    h=Image.new("RGBA",(W,H),(0,0,0,0))
    h.paste(Image.new("RGBA",s.size,(*LILAC,115)),(x,y),s)
    im=Image.alpha_composite(im,h.filter(ImageFilter.GaussianBlur(40)))
    im.paste(s,(x,y),s)
    d=ImageDraw.Draw(im)
    d.rounded_rectangle([x,y,x+gen-1,y+boy-1],32,outline=(*LILAC,65),width=2)
    f=ImageFont.truetype(f"{F}\Montserrat-SemiBold.ttf",56)
    tw=d.textbbox((0,0),baslik,font=f)[2]
    d.text(((W-tw)//2,140),baslik,font=f,fill=(*PARCHMENT,255))
    yol=os.path.join(CIK,cikti); im.convert("RGB").save(yol,"PNG",optimize=True); return yol

if __name__=="__main__":
    for ham,kirp,bas,cik in [
        ("01-sky-anonim.png",    (0,100,1080,1280), "Today, from your own chart", "shot-1-sky.png"),
        ("02-atlas.png",         (0,300,1080,1440), "Your birth chart, computed", "shot-2-chart.png"),
        ("03-gokyuzu.png",       (0,240,1080,1880), "The sky right now",          "shot-3-live.png"),
        # Kadraj 240'tan 470'e indi (2026-09-18). Ust kenardaki kullanici adi
        # karti seri rozetini tasiyordu ve o rozet "1 days" yaziyordu: Ingilizce
        # ARB'de streakDays duz "{count} days"ti, tekil dali yoktu. Hata ICU
        # plural'a gecilerek kodda duzeldi ama BU KARE ham cihaz yakalamasi,
        # yani metin piksele gomulu -- kompoziti yeniden uretmek duzeltmiyor.
        # Pikseli ELLE DUZENLEMEK secenek degil: magaza karesi gercek bir
        # yakalama olmali. Cozum cerceveleme: rozet kadraj disinda kaliyor ve
        # karenin asil konusu (arkadas listesi) one cikiyor. Duzeltilmis
        # buildle yeni cihaz yakalamasi alindiginda 240'a donulebilir.
        ("04-cevrem-anonim.png", (0,470,1080,2040), "The people close to you",    "shot-4-circle.png"),
        ("05-sohbet-anonim.png", (0,130,1080,1812), "It knows your chart",        "shot-5-chat.png"),
    ]:
        p=kare(ham,kirp,bas,cik)
        with Image.open(p) as i: print(f"{cik}: {i.size[0]}x{i.size[1]} {os.path.getsize(p)//1024} KB")
