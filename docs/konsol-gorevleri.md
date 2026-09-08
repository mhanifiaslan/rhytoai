# Konsol görevleri — senin yapman gerekenler (Revize R9)

Bu dosya, Revize 2 turunda kodun DIŞINDA kalan ve konsollardan elle
yapılması gereken işlerin adım adım listesi. Her bölümün başında hangi
özelliğin buna bağlı olduğu yazıyor: yapılmadan o özellik üretimde
çalışmaz.

Sunucu tarafı hazır ve yayında: cüzdan uçları, webhook'un paket/iade
işleme sırası, tek cihaz kilidi, telefon eşleme, rehber eşleşmesi, sohbet
arşivi + gece 03:20 temizlik cron'u (`rytho-cleanup`) ve `aiCache` TTL
politikası kuruldu. Aşağıdakiler sende.

## 0. KAPALI TEST SIRASI (KT-turu, 2026-08-30) — buradan yürü

Kod tarafı hazır (KT commit'i): jeton zorlaması canlı, deneme ekonomisi
onarıldı, hukuk sayfaları + veri-silme sayfası yayında, AAB kapıları
sertleşti. SENİN sıran (sıra ÖNEMLİ — 1 yapılmadan AAB üretme):

> **Tıkla-tıkla sürüm (kullanıcı için):** aynı sıra, ekran adları ve
> kopyalanabilir değerlerle birlikte artifact olarak yayınlandı
> (2026-08-30). Bu bölüm mühendislik kaydıdır; oradaki metinler
> (mağaza açıklamaları, sürüm notu) buradan türetildi.

0. ~~Firebase'e Play imzası~~ **DOĞRULANDI — ZATEN TAM (2026-08-30):**
   `firebase apps:android:sha:list` ile canlı liste okundu; Play App
   Signing'in HEM SHA-1'i (9e12f5f1…) HEM SHA-256'sı (ffef27a1… —
   assetlinks'tekiyle birebir) kayıtlı (B1 onarımında, 2026-08-12).
   Denetimdeki "eksik" işareti yereldeki bayat google-services.json'dan
   kaynaklanan yanlış alarmdı — dosyayı yenilemek isteğe bağlı hijyen,
   işlev için gerekmez (mağaza paketinde Google girişi + SMS çalışıyor).
1. **Play↔RevenueCat servis kimliği DOĞRULA** (RevenueCat → Project
   settings → Apps → Service Credentials "valid" mi). B2'de kurulmuştu;
   yeniden yüklenirse **36 saate kadar** yayılma penceresi var —
   "Invalid credentials" o pencerede NORMALDİR, anahtar yenilenmez.
   Bu yüzden sıranın başında: saat işlerken diğer adımlar sürebilir.
2. **Ürünler** (§2): Play'de 3 tek-seferlik ürün + `rytho_plus_monthly`
   abonelik (base plan `monthly`, **OFFER/DENEME EKLENMEZ** — KT kararı:
   deneme sunucuda; 3+3 çakışması ve otomatik-ücretlendirme beklentisi
   yaratma). Hepsi **Activate** edilmeli, yoksa RevenueCat import'u boş
   döner. Not: Play'de "consumable" kutusu YOK — tüketilebilirlik
   istemci tarafında (RevenueCat SDK) hallediliyor.
   **KDV tuzağı:** Play girilen fiyata %20 ekler. Alıcının ₺59,99/
   ₺155,99/₺419,99 görmesi için girilecek: ₺49,99 / ₺129,99 / ₺349,99.
   Abonelikte ₺149,99 girilir → ₺179,99 görünür (B3 kararı).
3. **RevenueCat**: ürünleri import et → `RhytoAI Pro` yetkisine
   **yalnız** aboneliği bağla (jeton paketleri yetkisiz) → **OFFERING
   KUR**: `default` teklifi + `$rc_monthly` paketi + Current işaretle.
   **Offering olmadan paywall BOŞ açılır** — `subscription.dart:184`
   `Purchases.getOfferings()` → `offerings.current` okuyor. Jeton
   paketleri `getProducts(kTokenPackIds)` ile doğrudan çekiliyor,
   onlar için Offering GEREKMEZ (`wallet.dart:95-101`).
4. **Webhook** (§2c): kuruluysa yalnız **Environment** alanını kontrol
   et — sandbox DA seçili olmalı, yoksa kapalı testteki satın almalar
   hiç düşmez. Authorization = secret'ın HAM değeri (Bearer YOK;
   `billing.py:174` `compare_digest` birebir eşitlik arıyor).
5. **License testing**: Play Console **hesap seviyesi** → Settings →
   License testing → testçi e-postaları. Üç şart birden: hesap bu
   listede + kapalı test testçi listesinde + opt-in bağlantısını açmış.
   Yenileme hızlanır (aylık ≈ 5 dk, en fazla 6 yenileme).
6. **Uygulama içeriği** (Policy and programs → App content) — 10 form,
   kapalı testte hepsi ZORUNLU. Veri güvenliği `store-privacy-labels.md`
   §3'ten satır satır; **veri silme URL'si Data safety formunun İÇİNDE**
   (`…/legal/hesap-silme.html`); **AD_ID AYRI bir bölüm** → "Evet,
   yalnız Analytics" (firebase_analytics izni merge ediyor; "hayır"
   dersen AAB yüklemesi hata verir); Health apps formu herkese zorunlu
   (→ "sağlıkla ilgili değil"); hedef kitle 13+; reklam yok.
7. **Mağaza kaydı**: görseller (512 ikon · 1024×500 · ≥2 ekran
   görüntüsü, GERÇEK harita/gökyüzü verisiyle) + kısa/uzun açıklama
   (artifact'te hazır metin; "iyileştirir/tedavi/şifa" ve kesin kehanet
   dili YASAK).
8. **Kapalı test kanalı**: Test and release → Testing → Closed testing →
   Create track → AAB yükle → sürüm notu → Start rollout → testçi
   listesi → **opt-in bağlantısı** (yalnız sürüm Published olunca çıkar).
   **12 testçi / 14 gün kuralı:** 13 Kasım 2023 sonrası açılmış KİŞİSEL
   hesaplar için ÜRETİME çıkış şartı (kapalı testi engellemez) — testçi
   listesini 12+ kurmak baştan zaman kazandırır.
9. **Doğrulama**: ilk gerçek satın almada webhook'u panel → Sistem
   (Denetim izi) ve Ekonomi sekmesinden gör (test-raporu B2 kapanışı);
   senaryo 113-115'i koş. Yanlış ürün kimliği `billing.unknown_pack`
   olarak denetim izine düşer.
10. **Hukuk onayı** (bir hukukçuya metinler) + **Swiss Ephemeris lisans
    kararı** — kapalı test de dağıtımdır (production-checklist şartı).

---

## 1. Firebase: Telefon sağlayıcısını aç (R2 — SMS doğrulama)

**DURUM (2026-08-07): DÖRT ADIM DA TAMAMLANDI** — Phone sağlayıcısı
açık, SMS region policy'de Türkiye, Blaze aktif, **SHA-256 eklendi**
(debug anahtarı `4E:29:8B:F0:...:DF:70`; Phone Auth Android'de Play
Integrity doğrulaması için SHA-256 ister — yalnız SHA-1 yetmez).

Kalan işler:
- ~~Sihirbazın telefon adımını açmak~~ **YAPILDI (OT4, 1.12.0+28):**
  `RYTHO_PHONE_STEP` bayrağı silindi; adım herkese görünür ve "Sonra"
  ile atlanabilir.
- **Play'e yüklerken**: Play App Signing'in mağaza imza anahtarının
  SHA-256'sı da Firebase'e eklenmeli (Play Console → Setup → App
  integrity → App signing key certificate) — yoksa mağazadan inen
  sürümde SMS düşer (W10/yayın turu).
- İstersen **Phone numbers for testing** bölümüne kendi numaranı sabit
  bir kodla ekle — mağaza incelemesi için de işe yarar.

Not: SMS gönderimi Blaze planında ücretlidir (Türkiye ~0,01-0,05 USD/SMS).

## 1a. Firebase: SMS teşhisi (SMS-turu, 2026-09-08 canlı olayı)

**Olay:** bir kullanıcı kayıt sihirbazının telefon adımında SMS alamadı.
Ölçüldü (Cloud Monitoring): `SendVerificationCode` **200** döndü, SMS
`region TR / +90 / tier 2` olarak **faturalandı**, `blocked_sms_count`
**0**, kota aşımı yok, Blaze açık, App Check zorlanmıyor. Yani kopma
Google'dan SONRA — **operatör teslimatı**. Google teslim makbuzu
yayınlamıyor, o hop bizden görünmüyor.

Asıl sorun teşhisin ZOR olmasıydı. Sırasıyla:

- [ ] **Auth istek günlüğünü AÇ** — Firebase Console → Authentication →
      Settings → *User activity / request logging* (Identity Platform
      `monitoring.requestLogging`). **Şu an KAPALI**: Cloud Logging'de tek
      satır auth kaydı yok, teşhis Monitoring metriklerinden dolaylı
      yapıldı. Açıldıktan sonra doğrula:
      `gcloud logging read 'protoPayload.serviceName="identitytoolkit.googleapis.com"' --project=rhytoai`
      artık satır dönmeli. **Bu listedeki en yüksek kaldıraçlı madde.**
- [ ] **Test numarasını gözden geçir** — Authentication → Sign-in method →
      Phone → *Phone numbers for testing*: `+905542732455` → `356625`
      kayıtlı. Gerçek görünümlü bir TR numarası; o numaraya **asla SMS
      gitmez**. Seninse kalsın, değilse sil.
- [ ] **SMS bölge listesi kararı** — şu an `allowlistOnly: ["TR"]`.
      Uygulamadaki ülke seçici tüm dünyayı sunuyordu; istemciye
      `_smsBolgeleri = {'TR'}` kapısı kondu (boşa gönderim + boşa ücret
      olmasın). **Listeyi konsolda genişletirsen `phone_verify_screen.dart`
      içindeki kümeyi de güncelle** — iki yer aynı gerçeği söylemeli.
- [ ] **(İsteğe bağlı)** Daha çok ülkeye açılmadan önce reCAPTCHA
      Enterprise'ı etkinleştir (SMS toll-fraud koruması). Şu an kapalı.

⚠️ `gcloud config` aktif projesi **`xanthixai`** — telefon/SMS ile ilgili
her komutta `--project=rhytoai` şart, yoksa sessizce yanlış projeye
bakılır.

Kod tarafında kapatılanlar (aynı tur): tekrar gönderme jetonu artık
saklanıyor ve 60 sn geri sayımlı "Kodu tekrar gönder" düğmesi var
(eskiden tek çare "numarayı değiştir"di — o YENİ doğrulama başlatır ve
Firebase'in kötüye kullanım korumasını tetikler); `verifyPhoneNumber`
try/catch'e alındı (sonsuz spinner); `00532…` gibi girişler artık doğru
derleniyor; her deneme maskeli olarak `phoneAttempts`'e yazılıp panelde
Kullanıcı 360'ta görünüyor.

## 1b. Firebase: e-posta şablon dili (OT2 — şifre sıfırlama)

Kod tarafı hazır (1.12.0+28): uygulama `setLanguageCode` ile Firebase'e
kullanıcının dilini bildiriyor ve şifre panosu gerçek hataları
gösteriyor. Konsolda ELLE doğrulanacak tek şey:

- Firebase Console → Authentication → Templates → **Password reset**
  (ve **Email address verification**): şablonların Türkçe sürümü var mı,
  gönderen adı "Rytho" mu bak; gerekirse şablon metnini Türkçeleştir.
  `setLanguageCode` yalnız Firebase'in HAZIR dil şablonları arasından
  seçim yapar — özel metin yazdıysan dil başına ayrı düzenlenir.

## 1c. Firebase: e-posta eylem URL'i → markalı sayfa (ŞS — şifre sayfası)

**DURUM: BEKLİYOR — alan adı alınınca yapılacak (kullanıcı kararı,
2026-08-29).** Alan adı alındığı gün sıra: Customize domain → DNS
doğrulaması → aşağıdaki 1-2. adımlar.

Kod tarafı hazır ve YAYINDA: `https://rhytoai.web.app/auth/action`
markalı eylem sayfası deploy edildi (şifre + tekrar, canlı kural
listesi, mobil `validatePassword` ile birebir aynı politika, TR/EN,
`verifyEmail`/`recoverEmail` modları da karşılanıyor). Bağlantının
Firebase'in varsayılan `rhytoai.firebaseapp.com` sayfası yerine BURAYA
düşmesi için konsolda TEK elle adım gerekiyor (CLI/API'den yapılamıyor):

**ENGEL TESPİT EDİLDİ (2026-08-29):** hem konsol ("An error occurred
updating action URL") hem Identity Toolkit API'si
(`PATCH .../config?updateMask=notification.sendEmail.callbackUri`)
aynı sunucu hatasını veriyor: **`EMAIL_TEMPLATE_UPDATE_NOT_ALLOWED`
(400)**. Bu, Firebase'in kimlik-avı önleme kısıtı: e-posta şablonu
özelleştirmesi (Action URL dahil) alan adı sahipliği kanıtlanmadan
bu projede kapalı. Belgelenmemiş; hata koduyla ölçüldü.

Kilidi açan yol: **Templates → kalem → "Customize domain"** akışıyla
kendi alan adını DNS kayıtlarıyla (TXT/CNAME) doğrulamak (≤24 saat).
Alan adı henüz yok (W10'da zaten planlıydı); alınıp doğrulanınca:

1. Templates → Password reset → **Customize action URL** →
   `https://rhytoai.web.app/auth/action` → Save. (Tüm şablonlara
   birden uygulanır; `mode`/`oobCode`/`lang` parametrelerini Firebase
   ekler.) Konsol yine reddederse API komutu bu dosyanın geçmişinde.
2. Doğrulama: "Şifremi unuttum" e-postasındaki bağlantı
   `rhytoai.web.app/auth/action` açmalı — iki şifre alanı + Rytho
   tasarımı (test-raporu senaryo 109).

Alternatif (paralel yürütülebilir): Firebase Support'a talep —
proje `rhytoai`, Blaze, hata kodu `EMAIL_TEMPLATE_UPDATE_NOT_ALLOWED`,
istenen Action URL. Bu adım yapılana kadar eski `firebaseapp.com`
tek-input sayfası görünmeye devam eder (akış ÇALIŞIYOR — kilit yalnız
görünüm/güven tarafında). Markalı sayfa yayında ve hazır bekliyor.

## 2. RevenueCat: 3 token paketi + entitlement adı (R1 — token ekonomisi)

Yapılmadan: Token mağazası ekranı paketleri listeleyemez ("ürün
bulunamadı") ve satın alma yapılamaz. Sunucudaki miktarlar SABİT:
`small=100 · medium=300 · large=1000` token — mağazadaki ürün kimlikleri
birebir şu olmalı:

    rytho_tokens_small
    rytho_tokens_medium
    rytho_tokens_large

### 2a. Play Console

1. play.google.com/console → uygulama → **Para kazanma → Ürünler →
   Uygulama içi ürünler → Ürün oluştur**.
2. Ürün kimliği: `rytho_tokens_small` · ad: "100 Token" ·
   fiyat önerisi: $1.99 karşılığı.
3. Aynısını `rytho_tokens_medium` ("300 Token", ~$4.99) ve
   `rytho_tokens_large` ("1000 Token", ~$12.99) için tekrarla.
4. Üçünü de **Etkinleştir**.

### 2b. App Store Connect

1. appstoreconnect.apple.com → uygulama → **Uygulama İçi Satın Almalar**.
2. **+ → Sarf Edilebilir (Consumable)** — Product ID'ler yukarıdakiyle
   BİREBİR aynı olmalı. Üç ürünü de oluştur, fiyat basamaklarını seç,
   yerelleştirilmiş ad/açıklama gir.

### 2c. RevenueCat paneli

1. app.revenuecat.com → proje → **Products** → **+ New** ile üç ürünü de
   ekle ve ilgili mağaza ürünlerine bağla.
2. Bu üç ürünü HİÇBİR entitlement'a BAĞLAMA: bunlar aboneliğe değil
   cüzdana gidiyor; krediyi webhook'taki `NON_RENEWING_PURCHASE` olayı
   ürün kimliğinden veriyor.
3. **Entitlement kimliği: `RhytoAI Pro`** (M1'de ÇÖZÜLDÜ, 2026-08-07):
   mobil kodun varsayılanı panele hizalandı — dart-define'sız derleme
   de artık `RhytoAI Pro` yetkisine bakar. Panelde kimliği DEĞİŞTİRME;
   abonelik ürünü (`rytho_plus_monthly`) bu entitlement'a bağlanır.
4. **Webhook** (kuruluysa atla): Project settings → Integrations →
   Webhooks → URL:
   `https://rytho-backend-770582338651.us-central1.run.app/api/v1/billing/revenuecat`
   Authorization başlığına Secret Manager'daki
   `REVENUECAT_WEBHOOK_SECRET` değerini yaz.

## 3. Gerçek RevenueCat API anahtarları (#17 — yayın öncesi şart)

`dart_defines.local.json` hâlâ `test_` anahtarları taşıyorsa gerçek satın
alma çalışmaz:

1. RevenueCat → **Project settings → API keys**.
2. **Public app-specific API keys** bölümünden Google (goog_...) ve
   Apple (appl_...) anahtarlarını kopyala.
3. `apps/mobile/dart_defines.local.json` içinde
   `REVENUECAT_ANDROID_KEY` ve `REVENUECAT_IOS_KEY` değerlerini değiştir.
   (Dosya gitignore'da; anahtarlar repoya girmez.)

## 3b. Test kilidi: RYTHO_FORCE_PLUS — **KALDIRILDI (2026-08-07, M3)**

R10'da verilen `RYTHO_FORCE_PLUS=1` üretimden kaldırıldı (rev 00046):
`/billing/status` artık GERÇEK abonelik durumunu döner; paywall gerçek
haliyle görünür. Test hesabına Rytho+ gerektiğinde yol: Play lisanslı
test hesabıyla ücretsiz satın alma (iç test kanalı).

Tekrar gerekirse (yalnız geçici test için):
`gcloud run services update rytho-backend --region us-central1
--project rhytoai --update-env-vars RYTHO_FORCE_PLUS=1` — ama bir
sonraki `deploy-backend.ps1` çalışması bunu sessizce siler (betikteki
--set-env-vars uyarısına bak).

Kapanış listesinde kalan: `RYTHO_TOKENS_ENFORCE` hâlâ 0 (jeton
harcaması kuru çalışma) — M4 gözlemi bitince 1 yapılacak ve
deploy-backend.ps1'e kalıcı yazılacak.

## 3c. Web sitesi + gizli admin paneli (W0–W9 ile kuruldu)

- **Tanıtım sitesi:** https://rhytoai.web.app (TR) + /en/ (EN). Hukuki
  metinler: /legal/gizlilik.html · /legal/kullanim.html (+ EN) — mağaza
  formlarına bu URL'ler verilecek. **Yayın öncesi hukuk metinlerine insan
  onayı gerekiyor** (mühendislik taslağı).
- **Admin paneli:** https://rhytoai.web.app/rytho-admin — sitede link YOK,
  arama motorlarına kapalı. Google ile girilir; yetki `admin:true` custom
  claim'inden gelir (aslan.mh@gmail.com'a basıldı). Yeni admin eklemek:
  `backend/.venv/Scripts/python tools/set_admin.py --email <eposta>`
  (claim ≤1 saat / çıkış-giriş sonrası yansır).
  **TUZAK (2026-08-29'da yaşandı):** claim Firebase Auth KULLANICI
  kaydında yaşar — mobilde "Hesabı sil" testi yapıp hesabı yeniden
  kurarsan claim SİLİNİR ve panel seni sahte-404'e atar ("giriş
  yapamıyorum" gibi görünür). Çözüm: set_admin.py ile yeniden bas.
- **Panel girişi OAuth adımı (AP onarımı, 2026-08-29):** Chrome COOP'u
  çapraz-origin popup'ı kırdığı için panel `authDomain` artık
  `rhytoai.web.app` (same-origin işleyici). Bunun çalışması için OAuth
  web istemcisine web.app işleyicisi eklendi (Console'dan elle —
  API'si yok): Cloud Console → APIs & Services → Credentials →
  "Web client (auto created by Google Service)" → Authorized redirect
  URIs'e `https://rhytoai.web.app/__/auth/handler`, Authorized
  JavaScript origins'e `https://rhytoai.web.app`. Yapılmazsa Google
  "Hata 400: redirect_uri_mismatch" verir. İleride ÖZEL alan adı
  bağlanırsa aynı adım o alan için tekrarlanır (app.js'te uygunluk
  bekçisi var — yalnız varsayılan Hosting alanlarında devrede).
- **Panel v2 (AP-turu, 2026-08-29):** baştan tasarlandı — yan menü + 6
  bölüm: Genel Bakış (KPI + eğriler), Kullanıcılar (aramalı liste +
  Kullanıcı 360: abonelik/cüzdan/kullanım/bildirim + zaman çizelgesi +
  ZORUNLU gerekçeli elle jeton kredisi), Ekonomi (gelir + jeton akışı +
  salt-okur bedel tablosu), AI Kullanımı (çağrı/token/maliyet
  telemetrisi), Ortaklar (+pasifleştir), Sistem (bildirim sağlığı +
  denetim izi). Yeni sunucu koleksiyonları: `usageEvents` (LLM çağrısı
  başına token/maliyet), `notifyRuns` (koşu sonuçları), `adminAudit`
  (yazan admin eylemleri), cüzdan defterine `debit`/`spend_refund`/
  `admin` kayıtları. Yeni uçlar `/admin/users*`, `/admin/usage`,
  `/admin/notify-runs`, `/admin/audit`. İndeks: usageEvents(uid,at)
  composite + ledger.at collection-group override (deploy edildi).
  Mahremiyet çizgisi: panel sohbet/hafıza İÇERİĞİNİ ve fcmToken
  değerini ASLA görmez — yalnız sayılar.
- **Panel v2.1 (AP2, aynı gün):** işletme K/Z katmanı + kullanıcı
  yönetimi. `/admin/economics` kullanıcı bazlı gelir/AI-maliyet/marj
  (marj = gelir × 0,85 − AI, "tahmini" etiketli); Genel Bakış'ta marj
  panosu + bugün şeridi + sayaç/çizim animasyonları; Ekonomi'de
  sıralanabilir K/Z tablosu. Yönetim eylemleri (hepsi gerekçeli +
  denetim izli): hesap devre dışı bırak/aç (`/admin/users/{uid}/disable`
  — token'lar revoke edilir), hesabı sil (`DELETE /admin/users/{uid}`,
  yazılı "SIL" onayı, mobil silme borusunun aynısı), şifre sıfırlama
  e-postası (istemci SDK). Kendi hesabında devre dışı/sil YASAK.
  Girişte e-posta+şifre formu da var (yetki yine claim'den).
- **İstatistikler:** her gece 02:40 UTC `rytho-stats` işi `adminStats/`
  dokümanını üretir; panel Genel Bakış'tan "Topla" ile elle de tetiklenir.
- **Ortak kodları:** panel > Ortaklar: ortak ekle → kod üret (bonus jeton +
  kullanım limiti). Her hesapta TEK kod. Kod girildikten SONRAKİ
  satın almalar ortağa atfedilir; hakediş = atfedilen brüt × pay yüzdesi.
  **Mağaza fiyat indirimi buradan yapılamaz** — gerekiyorsa RevenueCat
  Offering / Play promo kodu konsoldan elle.
  **NOT (2026-08-07, A2):** mobil girişler KALDIRILDI (Profil satırı +
  paywall linki + dialog) — jeton-bonusu modeli şimdilik kullanılmıyor.
  Backend (`/billing/redeem-code`, partner_service) ve panel Ortaklar
  ekranı çalışır durumda DURUYOR; ileride farklı bir ödül/atıf modeli
  tasarlanırsa zemin hazır, yalnız mobil arayüz yeniden kurulur.
- **Deploy komutları:** site `firebase deploy --only hosting` · indeksler
  `firebase deploy --only firestore:indexes` · backend infra/deploy betiği.
- Alan adı bağlanınca: Hosting'e özel alan adı + deep_links.dart
  `kInviteHost` + AndroidManifest host + sitemap/canonical/OG URL'leri
  (bkz. plan W10).

## 4. Mağaza veri güvenliği formları (R2/R3/R4/R5 sonrası güncelleme)

Yapılmadan: form ile uygulamanın gerçek davranışı çelişir; iki mağaza da
bunu tespit ederse yayından kaldırma sebebi.

Tek doğru kaynak repo'da hazır: **`docs/store-privacy-labels.md`** —
satır satır bu dosyadan aktar. Bu turda DEĞİŞEN beyanlar:

- **Telefon numarası** (isteğe bağlı): App functionality; ham numara
  saklanmaz, yalnızca SHA-256 özeti.
- **Rehber**: yalnızca ayar AÇIKKEN, yalnızca numara özetleri, sunucuda
  SAKLANMAZ (geçici işleme). Ad/soyad okunmaz.
- **Sohbet arşivi**: konuşmalar artık hesapta saklanıyor (30 gün
  kullanılmayan silinir) — "Messages" beyanı güncellenmeli.
- **Galeriden yüz okuma**: görüntü toplanmıyor (cihazda işlenir,
  kopya silinir) — "Photos" beyanı YİNE GEREKMEZ; sadece açıklama
  metinlerinde galeri yolunun geçtiğinden emin ol.

Adımlar:
1. Play Console → **Politika → Uygulama içeriği → Veri güvenliği** →
   formu yukarıdaki değişikliklerle güncelle → gönder.
2. App Store Connect → **Uygulama Gizliliği** → aynı güncellemeler.

## 5. Kuruldu — dokunman gerekmiyor (kayıt için)

- `aiCache.expiresAt` Firestore TTL politikası (gcloud ile kuruldu;
  konsoldan görmek istersen: Firestore → TTL sekmesi).
- `rytho-cleanup` Cloud Scheduler işi (her gece 03:20 UTC, 30 günlük
  konuşma temizliği) — elle tetiklendi ve doğrulandı.
- `rytho-notify-daily` / `rytho-notify-streak` işleri güncellendi.
- Backend revizyon 00027 yayında; Firestore kuralları ve collection-group
  indeksi deploy edildi.
