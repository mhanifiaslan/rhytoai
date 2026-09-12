# Kehanet sahnesi varlıkları — İching paraları + BaZi luopan

BaZi bekleme sahnesi (`bazi_tab.dart`, `StagedWaiting.visual`) için **alfa
kanallı animasyonlu WebP** kare dizisi (oynatıcı `widgets/frame_sequence.dart`,
dart:ui codec + Ticker; video eklentisi yok) ve İ Ching paraları için **iki
alfa PNG doku** (`widgets/coin_toss.dart` hareketi kodla sürer).

## PZ2 — paralar kare dizisinden koda (kullanıcı hükmü)

Kare-dizisi paralar cihazda reddedildi: *"saçma sapan hareket ediyorlar, ne
estetik var ne loop animasyonu, aşırı büyükler."* Üç kusur da yapısaldı —
hareketi model üretince boyut, döngü dikişi ve iniş pozu kontrol
edilemiyor. Yeni kurgu: **doku still + kod hareketi.**

- `stills/coin_face_raw.png` / `coin_back_raw.png`: `nano_banana_pro`
  (nano_banana_2'ye düşüyor), 1:1, "EXACT TOP-DOWN ORTHOGRAPHIC VIEW …
  PURE BLACK background", referans `black-rest3.png` + logo (2 kredi/adet).
- `coin_face.py`: siyah→alfa (build.py doktrini), sınır kutusu, kare tuval,
  256² LANCZOS → `apps/mobile/assets/anim/coin_face.png` (~106 KB) ve
  `coin_back.png` (~94 KB). Eski beş WebP (≈3 MB) silindi.
- Hareket `coin_toss.dart`'ta: dikişsiz hava döngüsü (2,6 s, frekanslar tam
  kat), 820 ms atış (kalkış → yerçekimi düşüşü → temasta foley → tek sönen
  sekme), hedef yüz kesin (0 / π), 40 lp para. Kanıt kareleri:
  `RYTHO_KANIT_DIR=<klasör> flutter test test/coin_toss_kanit_test.dart`.

## Kurgu (revize — kullanıcı kararı)

İlk taslak paraları obsidyen bir tepsi üstünde, opak klip olarak kartın
içinde oynatıyordu. Kullanıcı hükmü: *"masa/mekân uygulamanın tasarımıyla
uzaktan yakından alakalı değil; video mu seyrettireceksin?"* — haklıydı.
Yeni kurgu:

- Klipler Higgsfield'da **saf siyah zeminde** üretilir: yalnız paralar
  (BaZi için yalnız luopan), tepsi/masa/zemin YOK.
- `build.py` siyahı **alfaya** çevirir: `a = max(r,g,b)`, renk `rgb·255/a`
  (unpremultiply). Flutter çizerken premultiply edince özgün renk geri
  gelir; siyah `a=0` ile tamamen kaybolur. Bu, `screen` karışımının alfa
  eşdeğeridir ama katman/BackdropFilter fark etmeksizin her yerde çalışır.
- Uygulamada `AnimStage` yalnız 16:9 oranı sabitler; zemin, kart, vinyet
  ÇİZMEZ. Paralar uygulamanın kendi yıldızlı zemininin ve cam panelin
  üstünde durur — eski 2D disklerin yerinde, aynı rolde, 3D ve gerçekçi.

## Varlıklar (`apps/mobile/assets/anim/`)

| Dosya | İçerik | Kaynak |
|---|---|---|
| `coin_face.png` | logo yüzü, üstten, alfa, 256² | `stills/coin_face_raw.png` → `coin_face.py` |
| `coin_back.png` | düz arka yüz (iç halka), alfa, 256² | `stills/coin_back_raw.png` → `coin_face.py` |
| `bazi_wait.webp` | bronz luopan halkaları döner, ibre titrer (döngü, 2,5 s @16 fps) | `raw/bluopan.mp4` → `build.py` |

k = satır değeri − 6 (`landingVariants`); logo yüzü = "yazı" (3) — hangi
paraların logo göstereceği `coinsLogoUp(toss, k)` ile atıştan atışa döner.
Bütçe: doku ≤150 KB, klip ≤1 MB, toplam ≤2 MB (`test/anim_assets_test.dart`).
Eski `coins_air` / `coins_land_k` klipleri ve `raw/*air*`, `raw/*land*`
kaynakları yalnız tarih: PZ2'den sonra kullanılmıyor.

## Üretim adımları (Higgsfield MCP, `mode: std` — starter planda pro kapalı)

1. Logo referansı: `assets/brand/rytho_logo_512.png` → `media_upload`.
2. Usta still (`nano_banana_pro`, 16:9): üç antika altın para, logo
   **kabartma** (halka, kuyruklu yıldız izi, 4 uçlu parıltı, hilal,
   noktalar), "no letters, no Chinese characters". **Kapı: kullanıcı onayı.**
3. Türevler (aynı model, usta still `image_references`): `rest_k` (k para
   ters yüz), `air` (paralar havada), hepsi **"PURE SOLID BLACK background,
   NO tray, NO surface, NO reflections, NO shadows"**. Luopan aynı şekilde.
4. Video (`kling3_0 std`, 3 s, `sound:on` inişlerde): `start_image=air`,
   `end_image=rest_k`. ⚠️ İki ders: (a) "bounces once" yazınca model klibin
   ortasında paraları YENİDEN zıplatıyor — "come to rest within the first
   second and REMAIN COMPLETELY STILL" gerekir; (b) "land on an invisible
   glass plane" yazınca model **görünür bir cam levha** çiziyor — yüzeyden
   hiç söz etme: "decelerate as if caught by an invisible force and settle
   flat". Döngüler: `start_image == end_image`, `sound:off`.
5. `../../backend/.venv/Scripts/python.exe ads/oracle-anim/build.py` —
   kareleri çıkarır, durulma anını kare farkından bulur (durulma + 0,25 s
   kesim, 0,9 s'ye yeniden zamanlar), kenar bandı parlaklığıyla cam/masa
   artefaktını ölçer, alfa'ya çevirir, WebP yazar, boyutları raporlar.
6. `flutter test test/anim_assets_test.dart` + cihazda reduceMotion
   açık/kapalı kontrol.

Ses: `assets/sounds/coin_land.wav` bugün `tools/generate_sounds.py`
sentezi; kling foley'i (`raw/cland3.mp4` ses kanalı) daha iyiyse kesilip
konur ve `sound.dart` başlık notu güncellenir.

## Versiyonlanmayanlar

`raw/`, `stills/`, `out/`, `mock/` ve tüm png/mp4/wav/webp çıktıları
`.gitignore`'da — kişisel veri taşımıyorlar ama büyükler ve `build.py` ile
yeniden üretilebilirler. Kalıcı olan bu README ve `build.py`.
