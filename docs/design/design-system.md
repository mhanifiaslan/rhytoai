# RythoAI Tasarım Sistemi — v3 "Mor Nebula"

> Önceki sürümler: v1 "Gök Atlası" (mürekkep/parşömen/altın gravür), v2 "Camdan
> Rasathane" (cam paneller). v3 bunların yerini alır: modern, canlı, mor-magenta
> bir uzay estetiği + her etkileşimde hareket + ses + motivasyon katmanı.

## 1. Konsept

İlham: koyu siyah-mor uzay zemini üzerinde yumuşak yuvarlak koyu kartlar,
mor→magenta degrade vurgular, renkli burç rozetleri, parlayan degrade merkez
AI butonu, modern sohbet balonları ve animasyonlu ilerleme çubukları.
Dil Türkçe; emoji bu sürümde serbesttir ama ölçülü kullanılır (rozet, çip,
başlık vurgusu).

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
3. **Atlas**: natal çark kartı → kişi kartı (ad, tarih, 🕐 saat, 📍 şehir) →
   "Gezegen Konumları" 2 sütunlu çip grid'i → "Kişilik Özellikleri" 5
   animasyonlu çubuk (element/nitelik dağılımından deterministik) → açılar
   (katlanır) → tam AI raporu.
4. **Kehanet**: ana ekrandan push edilir (`OracleScreen(initialTab: i)`);
   para animasyonu altın→magenta, yüz tarama çizgisi lila.
5. **Meclis**: kart akışı, ✨ beğeni patlaması + tick sesi, degrade FAB ve
   segmentler; DM'de v3 balon dili.
6. **Profil**: degrade halkalı avatar, burç renkli çipler, 🔥 Günlük Seri
   kartı, "Sesler" anahtarı, hukuk sayfaları.
7. **Onboarding/Login**: aynı dil; login'de e-posta + Google akışı korunur,
   nefes alan degrade ✦ küresi.

## 6. Hareket dili (flutter_animate)

- Kart girişleri: 70ms stagger ile fadeIn + slideY (easeOutCubic).
- Sayfa geçişleri: `FadeForwardsPageTransitionsBuilder`.
- Merkez AI butonu: sürekli scale 1.0→1.06 + glow pulse.
- Promo banner: hafif shimmer döngüsü.
- Beğeni: ✨ scale patlaması (elasticOut) + tick sesi.
- İlerleme çubukları: 800ms scaleX dolumu.
- Sohbet balonları: scale+slide easeOutBack.
- Butonlar: basınca scale 0.96 + `HapticFeedback.lightImpact`.
- Pull-to-refresh: magenta.
- Yıldız alanı: 3 katman parallax süzülme + göz kırpma; zodyak nefesi korunur.

## 7. Ses (`lib/core/sound.dart` + `tools/generate_sounds.py`)

numpy ile sentezlenen WAV'lar (`apps/mobile/assets/sounds/`):

| Ses | Karakter | Tetik |
|---|---|---|
| `message_send` | ~120ms yumuşak pop (700→900Hz) | Rytho/DM mesaj gönderme |
| `message_receive` | ~200ms iki tonlu ding (E6→G6) | Yanıt/yeni DM gelmesi |
| `cast` | ~350ms harmonikli chime | I Ching çekimi |
| `like` | ~60ms tick | Beğeni |

Ses seviyesi 0.3–0.5; Profil > Ayarlar > "Sesler" anahtarıyla kapatılır
(shared_preferences, varsayılan açık).

## 8. Motivasyon katmanı

- **Günlük seri**: `users/{uid}.lastSeenDaily` + `streakCount` (firestore.rules
  hasOnly listesine eklendi). Ana ekran açılışında `DailyStreak.touch` —
  ardışık günlerde artar, atlanınca 1'e döner. Rozet ana ekranda + Profil'de
  kart.
- **Kişisel nudge**: `core/motivation.dart` — burç → 3 afirmasyon; gün
  numarasıyla döngüsel seçim, günlük okuma kartının altında.
- **Premium upsell**: ana ekrandaki degrade banner ("Yıldızların ötesine geç ✨"
  → "Keşfet") Atlas'ın derin raporuna götürür; ödeme henüz yok.

## 9. Yapılmayacaklar

- Parşömen/altın gravür estetiğine dönüş yok; Cormorant/Spectral kullanılmaz.
- Saf siyah (#000) veya saf beyaz büyük yüzeyler yok.
- Emoji: rozet/çip/vurgu dışında gövde metinlerine serpiştirilmez.
- Blur yalnızca alt barda; kartlarda performans için düz dolgu.
