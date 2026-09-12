# RythoAI Tasarım Sistemi — v3 "Mor Nebula"

> Önceki sürümler: v1 "Gök Atlası" (mürekkep/parşömen/altın gravür), v2 "Camdan
> Rasathane" (cam paneller). v3 bunların yerini alır: modern, canlı, mor-magenta
> bir uzay estetiği + her etkileşimde hareket + ses + motivasyon katmanı.

## 1. Konsept

İlham: koyu siyah-mor uzay zemini üzerinde yumuşak yuvarlak koyu kartlar,
mor→magenta degrade vurgular, renkli burç rozetleri, parlayan degrade merkez
AI butonu, modern sohbet balonları ve animasyonlu ilerleme çubukları.
Dil Türkçe; emoji bu sürümde serbesttir ama ölçülü kullanılır. OB-turu
doktrini: **bildirim başlıkları** tema emojisi taşır (💼❤️🌙🪙 —
`prompts.THEME_EMOJIS` = mobil `kThemeIcons`), **sohbet** yerinde 1-2
emoji kullanabilir (ağır duygu anlarında hiç), **kart/rapor gövdeleri**
sade kalır.

İşaret doktrini (OT5): **merkez sohbet düğmesi** = balon biçimli kap +
sırayla parlayan "yazıyor" noktaları (`widgets/chat_bubble_icon.dart`);
**✦** satır içi "Rytho'ya sor" işaretidir (7+ CTA) ve merkeze geri
dönmez — iki işaretin işi ayrıldı, ikisi de tekil kaldı.

## 2. Renk paleti (`lib/theme/rytho_theme.dart` → `RythoColors`)

Token adları v1/v2'den korunur (ekran dosyaları kırılmasın diye); değerler v3'tür.

| Token | Değer | Kullanım |
|---|---|---|
| `ink` | `#0B0710` | Zemin degrade üst ucu (uzay siyahı) |
| `inkDeep` | `#14091E` | Zemin degrade alt ucu (mor derinlik) |
| `inkLight` | `#1C1326` | Kart yüzeyi |
| `inkLighter` | `#271A36` | Yükseltilmiş yüzey, giriş alanları |
| `parchment` | `#F4EFFA` | Ana metin (beyaz-lila) |
| `parchmentDim` | `#A99EC2` | İkincil metin |
| `violet` | `#7B2FF7` | Birincil degrade başlangıcı |
| `purple` | `#B02EFF` | Birincil degrade ortası |
| `magenta` / `copper` | `#E64ACF` | Degrade ucu; retro/uyarı vurgusu |
| `lilac` | `#B79CFF` | İkincil vurgu: çizgiler, ikonlar, mono metin |
| `gold` | `#FFC24B` | ✨ yıldız/puan/seri vurgusu |
| `goldBright` | `#FFD98A` | Parlak yıldız vurgusu |
| `celadon` | `#7FD8A4` | Olumlu |
| `madder` | `#FF6B81` | Hata |
| `line` | `#2C1F40` | Ayraçlar |
| `glassFill` | `#1C1326` @90% | Kart dolgusu |
| `glassStroke` | `#FFFFFF` @6% | Kart konturu (1px) |
| `goldGlow` | `#7B2FF7` @33% | Mor glow (CTA/aktif) |
| `magentaGlow` | `#E64ACF` @40% | Merkez AI butonu glow'u |

- **Birincil degrade** `primaryGradient`: `violet → purple → magenta`
  (sol üst → sağ alt). CTA butonları, promo banner, aktif segmentler,
  AI balonları, merkez buton.
- **Zemin** `backgroundGradient`: `ink → inkDeep` dikey; üzerine beyaz-lila
  yıldız alanı (`StarfieldBackground`) ve ekranın üstünde %3-4 opaklıkta dev
  zodyak çarkı filigranı.
- **Burç renkleri** `signColors[12]`: her burcun kendi çip rengi
  (Koç kızıl, Boğa yeşil, ... Balık mavi-mor).

## 3. Tipografi (`RythoText`)

| Rol | Font | Ağırlık |
|---|---|---|
| `display` — başlıklar | Sora | 600–700 |
| `body` — gövde | Manrope | 400–600 |
| `label` — buton/etiket | Manrope | 700, +0.8 aralık |
| `mono` — astronomik veri | JetBrains Mono | 400 |

Cormorant/Spectral tamamen kalktı.

## 4. Bileşenler

- **`GlassPanel`** (widgets/glass.dart): koyu mor kart, 22px köşe, 1px %6 beyaz
  kontur, üst kenar ışığı. Blur varsayılan kapalı (performans).
- **`CosmicDock`**: ince koyu saydam alt bar; 4 outline ikon
  (Gökyüzü, Atlas, Meclis, Profil) + ORTADA yukarı taşan degrade dairesel
  **AI butonu** (✦) — sürekli yumuşak glow pulse (scale 1.0→1.06), Rytho
  sohbetini açar.
- **`GoldButton`** (adı tarihsel): degrade dolgulu CTA; basınca scale 0.96 +
  haptic; busy'de `AstrolabeSpinner`.
- **`GlassSegments`**: aktif segment degrade dolgulu.
- **`ZodiacChip`** (widgets/nebula_widgets.dart): renkli degrade daire içinde
  burç glifi + ad; seçiliyken renkli glow.
- **`PromoBanner`**: degrade motivasyon/upsell banner'ı; 2.4sn'de bir hafif
  shimmer; Atlas'ın derin raporuna götürür.
- **`GradientProgressBar`**: 800ms'de dolan degrade ilerleme çubuğu
  (kişilik özellikleri).
- **`TypingDots`**: Rytho yanıt beklerken degrade balonda üç nokta dalgası.
- **`StreakBadge`**: 🔥 + gün sayısı (günlük seri).
- **`SuggestionChip` / `InfoChip`**: yuvarlak koyu çipler, ince parlak kontur.
- **`Pressable`**: her dokunuşta scale 0.96 + haptic sarmalayıcısı.
- **`NatalWheel`**: lila halkalar, beyaz glifler, magenta sert açılar /
  lila uyumlu açılar / altın kavuşum; sweep kurulum animasyonu korunur.

## 5. Ekran yerleşimleri

1. **Gökyüzü (ana)**: avatar + saate göre selamlama + sohbet ikonu; 12 burçlu
   yatay çip şeridi (kullanıcının burcu önde/seçili); degrade promo banner;
   "Bugünün İçgörüsü" (TypewriterText + burca özel nudge kutusu); "Kehanet
   Araçları" karuseli (I Ching 🪙, BaZi 🀄, Yüz 🔮, Sinastri 💞); "Şu An
   Gökyüzünde" kartı (zodyak çemberi, Ay evresi, retro çipleri, açı çipleri).
2. **Rytho AI sohbeti**: kullanıcı sağda BEYAZ balon (koyu metin), Rytho solda
   mor degrade balon (beyaz metin); öneri çipleri; "+" ve degrade gönder
   butonu; yazıyor animasyonu; balonlar easeOutBack ile girer.
3. **Atlas**: natal çark kartı (üç görünüm: haritam / şu an / ikili çark) →
   kişi kartı (ad, tarih, 🕐 saat, 📍 şehir) → detay ekranlarına giden
   dizin satırları → tam AI raporu.
   Detay ekranlarının dili (R5): **ölçüleni göster, dokun-açıkla.**
   - *Kişilik Özellikleri*: sunucunun kanonik element/nitelik sayımı
     **kesir** olarak (`3/8`) — yüzde DEĞİL. Payda sabittir: geleneksel
     yedili + Yükselen. Sıfır sayım bakır bir satırla açıkça söylenir
     ("eksik element anlamlı bir ifadedir"); dokunuş, o sayıyı hangi
     gezegenlerin ürettiğini listeler. *(Eski tasarım burada beş animasyonlu
     çubuk çiziyordu; yüzdeler istemcide `30 + 10·sayım` ile üretiliyordu,
     dört elementin toplamı 260 ediyordu ve sıfır sayım %30 görünüyordu —
     kaldırıldı.)*
   - *Gezegen Konumları*: `☉ Güneş — Aslan 12.3° · 5. ev` (+ ℞); dokunuş
     gezegen doğası × ev alanı açıklamasını açar.
   - *Açılar*: en dar orb önce, gerilim/kavuşum/akış başlıklarıyla gruplu.
4. **Kehanet**: ana ekrandan push edilir (`OracleScreen(initialTab: i)`);
   para animasyonu altın→magenta, yüz tarama çizgisi lila.
5. **Meclis**: kart akışı, ✨ beğeni patlaması + tick sesi, degrade FAB ve
   segmentler; DM'de v3 balon dili.
6. **Profil**: degrade halkalı avatar, burç renkli çipler, 🔥 Günlük Seri
   kartı, "Sesler" anahtarı, hukuk sayfaları.
7. **Onboarding/Login**: aynı dil; login'de e-posta + Google akışı korunur,
   nefes alan degrade ✦ küresi.

## 6. Hareket dili (flutter_animate + `lib/widgets/motion.dart`, R12)

Token'lar (`RythoMotion`): süreler `fast 160 / base 260 / slow 380 /
slower 600 / stagger 70`; eğriler `enter (easeOutCubic, giriş-kayma)`,
`pop (easeOutBack, rozet-balon-kutlama)`, `settle (easeOut, dokunuş)`.
Yeni kod çıplak süre/eğri yazmaz; eski ekranlar dokunuldukça geçer.

| Desen | Araç | Nerede |
|---|---|---|
| Kademeli giriş | `RythoReveal(index)` — stagger×index + fadeIn(slow) + slideY(enter) | onboarding, okuma sayfası, boş durumlar, listeler |
| Uzun bekleyiş | `StagedWaiting(stages, visual:)` — varsayılan usturlap; `visual:` sahneyi değiştirir (BaZi: bronz luopan kare dizisi `AnimStage(FrameSequence('bazi_wait'))`, PBZ) + sırayla değişen, SONDA DURAN aşama metinleri; yüzde çubuğu yasak | yüz okuma, natal, BaZi (luopan), onboarding kaydı |
| İçerik açılışı | `FadeThroughRoute` — eski sayfa ~90ms, gelen fade+scale 0.96→1; Hero bilerek yok | kart→okuma, kilit→paywall |
| Kutlama | `StarBurst` — Starfield boyacısından tek atış parçacık; asla döngü | satın alma, streak, tepki |
| İskelet | `SkeletonPanel` — GlassPanel hacmi + shimmer 1200ms | profil, konu listesi |
| Morph | `AnimatedSwitcher(base)` sabit hücrede kimlik değişimi | dots→balon, atış-güdümlü reveal → heksagram (her iniş bir çizgi, `CastScene`; sabit stagger YOK), spinner→kart |
| Para atışı (PZ2) | `CoinToss` — üç 40 lp para, dokusu gerçek (Higgsfield still, alfa PNG), hareketi KOD: havada dikişsiz döngü (tüm frekanslar 2,6 s periyodun tam katı), yanıtla o anki açıdan kesintisiz iniş (820 ms, easeOutCubic yavaşlama, tek sönen sekme), her atışta tam k para logo yüzüyle iner; foley temas anında | yalnız İching çekimi. Kare-dizisi klipleri (dev görüntü, döngü dikişi, rastgele iniş pozu) bu yüzden kaldırıldı |
| Dokunuş | `Pressable` scale 0.96 + lightImpact | tüm basılabilirler |
| Sürekli nefes | yalnız dock merkez butonu + yıldız alanı + usturlap | başka yerde YASAK — çok nefes ekranı ucuzlatır. Tek istisna: bekleme sahneleri (`FrameSequence` luopan döngüsü, `CoinToss` hava döngüsü) yalnız `_busy`/loading sırasında monte edilir, sonuçla sökülür |

**Reduce-motion:** `reduceMotion(context)` tek kapı — sürekli animatörler
tek karede durur, girişler hiç kurulmaz, kutlamalar çizilmez. Yeni animasyon
eklerken bu kapıdan geçmeyen hareket PR'dan dönmeli.

**Test kuralı:** sonsuz repeat içeren ağaçta `pumpAndSettle` YASAK —
süreli `tester.pump(...)` adımları.

**Kare dizileri (PBZ):** `FrameSequence` — animasyonlu WebP, `dart:ui`
codec + Ticker, video eklentisi YOK (`lib/widgets/frame_sequence.dart`).
Klipler SAF SİYAH zeminde üretilir, `ads/oracle-anim/build.py` siyahı ALFA'ya çevirir; `AnimStage` yalnız 16:9 oranı sabitler, zemin/kart çizmez — sahne uygulamanın kendi yıldızlı zemininin üstünde durur (tepsi/mekân/"video penceresi" YOK). Bugün tek kare-dizisi BaZi luopan'ıdır.

**Kod sürümlü 3D (PZ2):** hareketi model üretmişse boyut, döngü ve iniş pozu kontrol edilemez — İching paraları bu yüzden `CoinToss`'a taşındı: doku still (`ads/oracle-anim/coin_face.py` siyah→alfa, 256², ~100 KB), hareket kinematik (`coinAirbornePose`/`coinLandingPose`, testli). Kural: uygulama içi bir öğe "3D/gerçekçi" olacaksa ÖNCE "doku still + kod hareketi" denenir; kare dizisi ancak hareketin kendisi üretilmek zorundaysa (luopan gibi organik döngü).
içinde; chroma-key yok. Reduce-motion'da SON kare statik, `onDone` hemen,
`onLoop` hiç. Kesme yalnız döngü sınırında (`onLoop`) — iniş klipleri
havadaki ilk kareden başlar, sıçrama yok. Varlık bütçesi: klip ≤1 MB,
toplam ≤5 MB (`test/anim_assets_test.dart` zorlar; aşarsa 640×400 / q75).
Üretim hattı `ads/oracle-anim/README.md`.

**Bilinçli sükûnet:** ayar/hukuk sayfaları, biyometrik rıza formu, paywall
fiyat metinleri, hesap silme — bu yüzeylerde süs animasyonu yok; sükûnet de
tasarım.

## 7. Ses (`lib/core/sound.dart` + `tools/generate_sounds.py`)

numpy ile sentezlenen WAV'lar (`apps/mobile/assets/sounds/`):

| Ses | Karakter | Tetik |
|---|---|---|
| `message_send` | ~120ms yumuşak pop (700→900Hz) | Rytho/DM mesaj gönderme |
| `message_receive` | ~200ms iki tonlu ding (E6→G6) | Yanıt/yeni DM gelmesi |
| `cast` | ~350ms harmonikli chime | I Ching çekimi |
| `like` | ~60ms tick | Beğeni |
| `success` | ~280ms C6-E6-G6 arpej | Başarı anları (R12-C1) |
| `streak` | ~180ms parlak tık + beşli | Günlük seri artışı (R12-C1) |
| `purchase` | ~450ms dolu çift vuruş (cast ailesi) | Satın alma kutlaması (R12-C1) |
| `coin_land` | ~300ms inharmonik metalik clink, ikinci sönük temas (para bir kez seker) | Her para inişi — altı kez, atışın TEMAS anında (`CoinToss.onContact`, PZ2); reduceMotion'da yalnız ilk inişte |

Ses seviyesi 0.3–0.5; Profil > Ayarlar > "Sesler" anahtarıyla kapatılır
(shared_preferences, varsayılan açık).

## 8. Motivasyon katmanı

- **Günlük seri**: `users/{uid}.lastSeenDaily` + `streakCount` (firestore.rules
  hasOnly listesine eklendi). Ana ekran açılışında `DailyStreak.touch` —
  ardışık günlerde artar, atlanınca 1'e döner. Rozet ana ekranda + Profil'de
  kart.
- **Günlük keşif halkası (OB4)**: `core/discovery.dart` — üç dilimli
  26px halka (`_DiscoveryRing`, sky_screen), dilimler: gökyüzünü aç ·
  Rytho ile konuş · çevrenden birine bak. Tamamen cihaz-yerel
  (SharedPreferences `discovery-state` = "gün:mask"); 3/3'te günde bir
  kez StarBurst + `SoundFx.success` + snackbar. Rozet/XP bilinçli yok
  (kullanıcı kararı, v1).
- **Hazır tepkiler**: arkadaş satırından iki dokunuşla; emoji kümesi üç
  yerde birebir aynı (mobil `kReactions`, backend `REACTION_EMOJIS`,
  firestore.rules) ve testle sabitli.

  Not: eski "burç → 3 afirmasyon" nudge'ı kaldırılalı çok oldu —
  `core/motivation.dart` artık yalnız seri takibi.
- **Premium upsell**: satış mesajı `PlusLockedCard`'da, yani kullanıcının
  kilitli içeriğe baktığı yerde yaşar (banner yok).

## 8b. Harita çarkı doktrini (HI-turu)

Tek çark sistemi (`lib/widgets/chart/`): natal, gökyüzü, bi-wheel ve
Çevrem sinastrisi AYNI `ChartData → WheelLayout → RythoWheelPainter`
zincirinden geçer; `ChartInspectorScreen` tam ekran inceleme yüzeyidir.

- **Geometri tek kaynak:** çizim ve dokunma isabeti AYNI `WheelLayout`
  nesnesini tüketir — iki ayrı hesap yasak (eski çarkın "Venüs'e dokun,
  Merkür açılsın" kusuru bu ayrışmadan doğdu).
- **Yön sözleşmesi:** Yükselen saat 9'da, boylam saat yönünün tersine;
  evsiz düzende 0° Koç solda. SERBEST DÖNDÜRME YOK.
- **Derece cetveli** 1°/5°/10° kendi bandında — profesyonel çarkın bir
  numaralı işareti. AC/MC eksenleri kalın + AS/DS/MC/IC etiketli.
- **Açı paleti** (chart_palette.dart): karşıt #FF5C7A · kare #FF8A5C ·
  üçgen #5AC8FA · altmışlık #7FD8A4 · kavuşum altın · minör gri. Renk
  TEK anlam taşır; sert/yumuşak/minör ayrımı AYRICA çizgi stiliyle
  (düz/ince/kesik) verilir — renk körlüğünde de okunur. Orb daraldıkça
  çizgi kalınlaşır (0.6+1.6·sıkılık).
- **Kavuşum kiriş DEĞİLDİR:** jant braketi + nokta olarak çizilir.
- **Yelpaze dürüstlüğü:** stellium'da glifler açısal yayılır ama her
  glif gerçek derecesine İŞARETÇİ çizgisiyle bağlı kalır.
- **Bi-wheel/sinastri:** iç halka HER ZAMAN natal/kullanıcı; evler iç
  haritanındır; dış halka kendi ince cetvelini taşır; yalnız ÇAPRAZ
  açılar çizilir; LEJANT halkaları adlandırır ("İç: sen — Dış: X").
- **Glif stratejisi:** ♈-♓ + ⚹⚷⚸ VEKTÖR path (wheel_glyphs.dart) —
  U+2648-2653 Android'de renkli emojiye dönüyor; gezegenler güvenli
  metin kümesi (☉☽☿…), retro "R" harfi (℞ fontu güvenilmez).
- **Ölçülmeyen söylenmez:** saatsizde ev/eksen çizilmez + beyan; transit
  gezegene ev iddia edilmez (Greenwich artefaktı istemcide atılır);
  arkadaş sinastri çarkı yok (Çevrem v1 — kullanıcı kararı).
- **Etkileşim:** dokun→izole modu (diğerleri %30'a söner), tekrar
  dokun→ortak alt-sayfa ailesi; pinch-zoom 1-4x KENDİ durumuyla
  (InteractiveViewer yasak: raster bulanıklığı); zoom ≥2'de
  derece-dakika açılır; reduceMotion süpürmeyi keser.

## 9. Yapılmayacaklar

- Parşömen/altın gravür estetiğine dönüş yok; Cormorant/Spectral kullanılmaz.
- Saf siyah (#000) veya saf beyaz büyük yüzeyler yok.
- Emoji: kart/rapor GÖVDE metinlerine serpiştirilmez (bildirim başlığı
  ve sohbetteki ölçülü kullanım §1'deki doktrinle serbesttir).
- Blur yalnızca alt barda; kartlarda performans için düz dolgu.

## 10. Admin paneli dili (AD-turu, `web/rytho-admin`)

Aynı kozmik zemin, **işletme masası yoğunluğunda**. Mock kapısı (G0)
1440 ve 390 px'te kullanıcı onayıyla geçti; kurallar:

- **Tipografi:** Sora yalnız sayfa başlığı (22) ve KPI/hero değerlerinde
  (26/34, tabular); gövde Manrope 13,5–14; sayılar JetBrains Mono.
  Küçük etiketler (12 px, uppercase, +1 px izleme) `--parchment-mid`
  (= parchment %70 + parchment-dim); `--parchment-dim` yalnız ≥12 px.
- **Yüzeyler:** zemin `--ink` + yıldız alanı (`starfield.js`,
  reduced-motion'da statik). Kart `--yuzey` (ink-light %92) + `--cizgi`
  (line %80), köşe `--r-md` (16); `--r-card` (22) yalnız modal/sheet.
  `body{overflow-x:clip}` — site CSS'inin `hidden`ı yapışkanı bozar;
  site `section` dolgusu panelde sıfırlanır (bölüm = kart).
- **Vurgu tek:** `--gold` aktif sekme çizgisi, altın KPI, aktif aralık
  çipi; `--violet` %14 zemin aktif menü/metrik çipi; `--celadon`/`--madder`
  yalnız anlam (pozitif/hata, delta pilleri, dikkat noktaları);
  `--lilac` odak halkası, bağlantı, nötr grafik çizgisi; `--magenta`
  hero çizgi. Çıplak hex yok; türetim `color-mix()`.
- **Kabuk:** sol menü 240 px → 72 px ikon rayı (`title` + `aria-label`);
  <1080 çekmece (odak tuzağı, perde). Üst çubuk: kırıntı (mobilde
  yalnız son parça), Ctrl K komut paleti (mobilde yalnız ikon), dikkat
  zili (sayaç), avatar + rol rozeti (Sahip/Destek).
- **Sayfa deseni:** başlık + alt satır + sağda birincil eylemler; bant
  (bilgi/uyarı/hata) başlığın hemen altında; KPI ızgarası
  (auto-fit ≥176 px, delta pili nowrap, kıvılcım sağ-üst); modül =
  başlık satırı (sol h2 + alt yazı, sağ kontrol çipleri `.adm-cip`).
- **Veri tablosu (`veriTablosu`):** yapışkan başlık, sıralanır başlık
  DÜĞMELERİ (`aria-sort`), ilk hücre bağlantı (`role=link`), ↑/↓ satır
  gezintisi, cursor "Daha fazla", yoğunluk anahtarı; sayılar sağa
  hizalı mono; boş/hata/iskelet satırları.
- **Eylem disiplini:** hiçbir `confirm()`/`prompt()`/`alert()`. Her yazım
  modal/sheet'te gerekçe alanıyla; yıkıcılarda yazılı onay ("SIL"),
  `--madder` düğme; sonuç toast (aria-live). Rol'e kapalı eylem
  GİZLENMEZ, `disabled` + "Yalnız sahip" ipucuyla görünür.
- **Grafikler:** çizgi/alan, çubuk, yığın, halka, kıvılcım; klavye
  (←/→) ve dokunma ipucu; sr-only veri tablosu; boş durum METİN.
  "Veri yok" tuvale çizilmez.
- **Hedefler ve odak:** etkileşimli her şey ≥44 px; `:focus-visible`
  lila halka; rota değişimi `aria-live` ile duyurulur, h1 odaklanır.
- **Yapılmayacaklar:** açık tema (bilinçli yok), inline `style=`,
  tabloda 100'den uzun sayfasız liste, canlı tarama tetikleyen
  panel açılışı (panel rollup okur; canlı tarama yalnız sahibin
  "yeniden hesapla"sında).
