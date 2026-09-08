# "The Sage's Secret" — reklam üretim hattı

9:16 dikey, İngilizce. İki çıktı: **68,4 sn hikâye filmi**
(`rytho-reklam-v4.mp4`) ve tek başına yayınlanabilir **15 sn modern
reklam** (`rytho-modern-reklam-15s.mp4`).

## Bu klasörde ne versiyonlanır

Yalnız **üretici betikler** ve bu dosya. Medya git'e **girmez**: ölçülen
toplam 4,9 GB ve ham cihaz kayıtları gerçek doğum haritası taşıyor
(kişisel veri). Kurallar `.gitignore`'da. Çıktılar betiklerden yeniden
üretilebilir; nihai mp4'ler dış paylaşımla dağıtılır.

Gerekli ama versiyonlanmayan girdiler:
- `plates/` — cihazdan `adb screenrecord` ile alınmış GERÇEK arayüz
  kayıtları (Atlas çarkı, sohbet, gökyüzü). Çekim kuralları: cihazda
  animasyonlar AÇIK olmalı (`chart_wheel.dart` `MediaQuery.disableAnimations`
  okuyor — kapalıysa çark donmuş çıkar, sessiz başarısızlık), Atlas'taki
  üçlü segmente dokunmak süpürmeyi baştan oynatır, 60 fps kaydedilir.
- `fonts/` — **Sora** ve **Manrope**, Google Fonts'tan (SIL OFL 1.1).
  İndirilip buraya konur; OFL yeniden dağıtımda lisans metnini şart
  koştuğu için ikili dosyalar depoda tutulmuyor.
- `shots/`, `keyframes/`, `ses/` — Higgsfield çıktıları.

## Betikler

| Dosya | İş |
|---|---|
| `kompozit-pov.py` | Bilgenin gözünden plana gerçek arayüzü bindirir. Ekran dörtgeni göz kararıyla değil **ölçülür**: koyu bileşen flood-fill, kenarlara ayrı doğru fit, kesişim. Parmak parlaklık anahtarıyla camın üstünde kalır. |
| `kompozit-p16.py` / `-p16b.py` | Aynı boru hattının P16 (kilitli kamera) sürümleri. Arayüz dörtgene **germez** — önce dörtgenin oranına ortadan kırpar; v1'de telefonun "tablet gibi" durmasının sebebi buydu. |
| `goktasi.py` | Göktaşlarını temiz gökyüzü plakasına çizer. Modelin ürettiği göktaşları yukarı uçuyor ve gökyüzünde asılı kalıyordu; prompt'la iki denemede de düzelmedi. Yön (dy>0, 55-78° iniş), ömür (0,36-0,60 sn) ve iz burada açıkça kontrol ediliyor. **Kalıcı ders:** üretilen plandaki FİZİK hatası prompt'la düzelmez — plakayı temiz üret, olayı post'ta çiz. |
| `reklam.py` | 15 sn modern reklamın 360 karesini Pillow ile üretir. Palet `rytho_theme.dart`'tan, hareket eğrileri `web/assets/rytho.css`'ten (`--enter` easeOutCubic, `--pop` easeOutBack) — reklam uygulamanın kendi hareket dilini konuşur. |
| `denetim.py` | Kurguyu tarar, **parlak + düşük doygunluklu** kareleri bildirir: stüdyo zeminli referans sayfasının imzası. v2'de 40,5-41,0 sn'deki karakter turnaround kaçağını yakaladı. Her çıktıdan önce koşulur. |

## Tekrar aranmasın diye teknik notlar

- `-c copy` ile concat **AAC sınırlarını bozuyor** (382 çözme hatası).
  Doğrusu: video demuxer ile kopyalanır, ses AYRI `concat` filtresiyle
  tek WAV'a indirilir, sonra mikslenir. `.ts` üzerinden geçmek de
  düzeltmedi, süreyi 1,2 sn şişirdi.
- ffmpeg 8'de `-filter_complex_script` YOK; filtre dosyadan `-/filter:v dosya`
  ile okunur. `-vsync` de gitti, yerine `-fps_mode`.
- `shots/` iki çözünürlük ailesi taşır (1080×1920 ve 1076×1928); her
  segment `scale=…:force_original_aspect_ratio=increase,crop=1080:1920,
  fps=24,setsar=1` ile tekilleştirilir.
- Higgsfield'da **müzik üretilemez** (`generate_audio` yalnız konuşma);
  parça dış lisanslıdır.

## Dürüstlük kapısı

`docs/store-launch.md`'nin yasak dili reklama da uygulanır: sağlık
iddiası yok, kesin kehanet dili yok, **"NASA" asla** ("gerçek astronomik
efemeris verisi" denir). Telefon ekranındaki her görüntü gerçek uygulama
çıktısıdır — arayüz modele ürettirilmez.
