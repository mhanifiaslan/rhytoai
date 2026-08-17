# Rytho Mağaza Yayın Rehberi

Bu doküman; Android imzalama, Play Console iç test, App Check, mağaza
politika notları, monetizasyon ve bildirim altyapısını içerir. **Buradaki adımların çoğu
konsol/hesap işlemi gerektirir ve uygulama sahibi tarafından yapılmalıdır.**

## 1. Android imzalama anahtarı

Yükleme anahtarını üret (bir kez; dosyayı ASLA repoya koyma, yedeğini al):

```powershell
keytool -genkey -v -keystore c:\keys\rytho-upload.jks -storetype JKS `
  -keyalg RSA -keysize 2048 -validity 10000 -alias rytho-upload
```

`apps/mobile/android/key.properties` oluştur (bu dosya .gitignore'da olmalı):

```properties
storePassword=<parola>
keyPassword=<parola>
keyAlias=rytho-upload
storeFile=c:/keys/rytho-upload.jks
```

`app/build.gradle.kts` release bloğunu imzalama yapılandırmasına bağla
(şu an debug anahtarıyla imzalanıyor — yayın öncesi değiştirilmeli):

```kotlin
signingConfigs {
    create("release") {
        val props = java.util.Properties()
        file("../key.properties").inputStream().use { props.load(it) }
        keyAlias = props.getProperty("keyAlias")
        keyPassword = props.getProperty("keyPassword")
        storeFile = file(props.getProperty("storeFile"))
        storePassword = props.getProperty("storePassword")
    }
}
buildTypes {
    release {
        signingConfig = signingConfigs.getByName("release")
    }
}
```

App Bundle üretimi: `flutter build appbundle --release`

## 2. Play Console iç test adımları

1. https://play.google.com/console → geliştirici hesabı aç (25 USD, tek sefer).
2. "Uygulama oluştur" → ad: Rytho, dil: Türkçe, tür: Uygulama, ücretsiz
   (uygulama içi satın alma var).
3. **Uygulama içeriği** bölümü:
   - Gizlilik politikası URL'si. Metin uygulama içinde
     (`apps/mobile/lib/features/profile/legal_texts.dart`) ama mağaza bir URL
     ister — bir web adresinde yayınlanmalı (Firebase Hosting yeterli).
   - **Veri güvenliği formu:** `docs/store-privacy-labels.md` §3'teki tabloyu
     birebir gir. Konum yok, biyometrik veri yok, rehber erişimi yok.
   - İçerik derecelendirmesi anketi: Teen/13+ hedefleniyor
     (`docs/store-privacy-labels.md` §5).
4. **Test → İç test** → yeni sürüm → `.aab` yükle → test kullanıcısı
   e-postalarını ekle → yayınla.
5. Play App Signing'i kabul et (Google imzalama anahtarını yönetir; senin
   ürettiğin anahtar "upload key" olur).

## 3. Firebase App Check (Play Integrity)

Kod tarafına SDK henüz **eklenmedi** (bilinçli); önce konsol hazırlığı:

1. Firebase Console → rhytoai → **App Check** → "Get started".
2. Android uygulaması (`ai.rytho`) için sağlayıcı: **Play Integrity**.
   Play Console'da uygulamanın en az iç teste çıkmış olması gerekir.
3. SHA-256 imza parmak izlerini Firebase proje ayarlarına ekle
   (`keytool -list -v -keystore ...` çıktısından).
4. Kod tarafı (konsol hazır olunca):
   - `flutter pub add firebase_app_check`
   - `main.dart` içinde `Firebase.initializeApp()` sonrası
     `await FirebaseAppCheck.instance.activate(
     androidProvider: AndroidProvider.playIntegrity)`
5. Önce **izleme modunda** çalıştır; metrikler temizse Firestore ve backend
   için enforcement'ı aç.
6. Backend doğrulaması istenirse `firebase_admin.app_check.verify_token`
   ile bir middleware eklenebilir (ayrı iş).

## 4. Mağaza politika notları

Ayrıntılı savunma ve inceleme notu: **`docs/store-review-notes.md`**.
Burada yalnızca konsol tarafını ilgilendiren özet var.

### Apple App Store

| Kural | Durum |
|---|---|
| **4.3 — Spam / duplicate** | En yüksek risk. Ayırt edici unsurlar ve kanıtları `store-review-notes.md` §2'de; inceleme notu §3'te kopyalanabilir hâlde. |
| **5.1.1(v) — Hesap silme** | Karşılanıyor: Profil → Hesabı sil. |
| **1.2 — UGC** | Uygulanmıyor: kullanıcılar arası **serbest metin yok**, yalnızca sekiz maddelik kapalı tepki kümesi. |
| **5.3.1 — Kumar/piyango** | Uygulanmıyor. I Ching para atma animasyonu bir kehanet ritüelidir; ödül, bahis veya şans oyunu mekaniği yok. Açıklamada netleştir. |
| **3.1.1 — Uygulama içi satın alma** | Tek aylık abonelik, harici ödeme bağlantısı yok. |

- iOS derlemesi macOS gerektirir; TestFlight için Apple Developer Program
  (99 USD/yıl).
- Mağaza açıklamasında **sağlık iddiası ("iyileştirir", "şifa") ve kesin
  kehanet dili kullanılmamalı.**

### Google Play

- Kategori: **Yaşam Tarzı** veya **Eğlence**.
- İçerik derecelendirmesinde astroloji/fal içeriğini doğru beyan et; yanlış
  beyan kaldırma sebebidir.
- Sosyal özellik beyanı: kullanıcılar arası etkileşim **var ama sınırlı**
  (sabit tepki kümesi), kullanıcı üretimi içerik paylaşımı **yok**. Şikayet
  ve engelleme akışları yine de mevcut (`apps/mobile/lib/core/safety.dart`).
- Veri güvenliği formunda **hesap silmenin uygulama içinden yapılabildiğini**
  işaretle — Play bunu ayrıca soruyor.

## 5. Monetizasyon (uygulandı — Revize R1: abonelik + token)

Altyapı **kodda mevcut**: RevenueCat (`purchases_flutter`) + webhook ile
sunucu tarafı yetkilendirme + token cüzdanı (`backend/core/wallet.py`).

| Katman | İçerik |
|---|---|
| **Ücretsiz** | Burç yorumu (günlük/haftalık/aylık), gerçek gökyüzü, günde 5 sohbet mesajı, doğum haritası çarkı ve yerleşimleri, arkadaş listesi, seri ve hazır tepkiler, **1 kişi ekleme** (harita + ilişki ÖLÇÜMÜ; yorum kilitli) |
| **Rytho+** (yalnızca aylık) | Kişiye özel günlük okuma + **10 kişi kontenjanı** (eş, çocuk, yakın) + **aylık 300 token** hakkı. Token'la: sohbet (1), I Ching (2), ikili dinamik (3), natal/BaZi/sinastri/yüz okuma (5). Aylık hak dönem sonunda yenilenir, DEVRETMEZ. |
> **Not (1.7.0):** ücretsiz katmandan "günde 1 I Ching çekimi" SİLİNDİ — kod `require_plus("iching")` diyor, yani İ Ching Rytho+ içinde. Mağaza metninin koda uymayan tek satırı buydu.

| **Token paketleri** (consumable) | `rytho_tokens_small` 100 · `rytho_tokens_medium` 300 · `rytho_tokens_large` 1000. Tekrar tekrar alınabilir, bakiye aya DEVREDER, abonelik şartı yok (ücretsiz kullanıcı sohbet/I Ching taşması için kullanabilir). |

Kurallar:
- Token yalnızca **yeni üretimde** düşer; önbellekten tekrar okuma ücretsiz.
- LLM yanıt üretemezse bedel iade edilir.
- Kilit sunucuda: 402 + (token bitiminde) `X-Paywall-Reason: tokens` başlığı;
  istemci başlığa göre paywall ya da token mağazası açar.
- `RYTHO_TOKENS_ENFORCE=0` (varsayılan): kuru çalışma — harcama loglanır ama
  reddedilmez. Eski sürümler yayılınca `1` yapılır.

### Kalan konsol işleri — uygulama sahibinin

1. **App Store Connect** ve **Play Console**'da abonelik ürününü oluştur:
   önerilen kimlik `rytho_plus_monthly`, **3 gün ücretsiz deneme**.
2. Aynı konsollarda ÜÇ **consumable** ürün oluştur — kimlikler birebir:
   `rytho_tokens_small`, `rytho_tokens_medium`, `rytho_tokens_large`
   (önerilen fiyatlar: $1,99 / $4,99 / $12,99). RevenueCat'te bu ürünleri
   içeri aktar; entitlement'a BAĞLAMA (consumable — webhook cüzdana yükler).
3. RevenueCat panelinde abonelik ürününü `RhytoAI Pro` yetkisine bağla.
   Yetki kimliği koddaki `RYTHO_PLUS_ENTITLEMENT` ile birebir aynı olmalı;
   farklıysa satın alma sonrası yetki açılmaz.
4. RevenueCat webhook'unu şu adrese kur:
   `https://<cloud-run-url>/api/v1/billing/revenuecat`
   Authorization başlığına Secret Manager'daki `REVENUECAT_WEBHOOK_SECRET`
   değerini yaz. Anahtar tanımsızken uç 503 döner ve **hiçbir kullanıcı abone
   olarak işaretlenemez** — bu bilinçli.
5. `test_` önekli RevenueCat anahtarlarını gerçek anahtarlarla değiştir
   (`apps/mobile/dart_defines.local.json`; dosya .gitignore'da).

> RevenueCat **TRANSFER** olayı işleniyor: kullanıcı oturum açmadan satın alma
> yaparsa kayıt anonim kimliğe gider, sonradan giriş yapınca devredilir.
> Devir işlenmeseydi ödeme yapmış kullanıcı kilitli kalırdı.

## 6. Bildirim altyapısı (uygulandı)

Cloud Scheduler saatte bir toplu gönderim ucunu tetikler; kime gideceğine
sunucu karar verir (yerel saat + sessiz saat + tercih + tekrar koruması).

Kurulum tek komut:

```powershell
cd infra
./create-scheduler.ps1
./deploy-backend.ps1
```

Betik gizli anahtarı üretir, servis hesabına okuma izni verir ve iki saatlik
işi kurar. **Anahtarı döndürmek için:** `$env:RYTHO_ROTATE_SCHEDULER_SECRET=1`
ile çalıştır.

Duman testi (yayın sonrası "gerçekten gidiyor mu"):

```powershell
$A = gcloud secrets versions access latest --secret NOTIFY_SCHEDULER_SECRET --project rhytoai
curl -X POST -H "Authorization: $A" "<url>/api/v1/notify/run?type=daily&dry_run=true"
```

`dry_run` hiçbir şey göndermez ve kaydetmez; kime gideceğini ve neden
atlandığını döner. Gerçek bir test gönderimi için `force=true` (hedef saati
atlar) ve gerekirse `ignore_dedupe=true` eklenir. **Sessiz saat ve kullanıcı
tercihi hiçbir bayrakla atlanmaz.**

## 7. Yayın öncesi kritik hatırlatmalar

- **Swiss Ephemeris ticari lisansı**: kerykeion/pyswisseph AGPLv3'tür; kapalı
  kaynak mağaza yayını ÖNCESİ Astrodienst AG'den ticari lisans alınmalı
  (~750 CHF, tek seferlik): https://www.astro.com/swisseph/
  Kod bu maddeyi kapatamaz; lisans satın alınmadan checklist işareti
  konulmamalı.
- Hukuki metinler bir web adresinde yayınlanmalı (mağaza formları URL ister).
- Hukuki metinler **bir hukukçuya baktırılmalı** — mühendislik taslağıdır.
- `app/build.gradle.kts` release bloğu hâlâ **debug anahtarıyla** imzalıyor;
  §1'deki yapılandırmaya geçilmeli.
- Cloud Run `--max-instances 3`; lansman trafiğine göre gözden geçir.
- Tam kontrol listesi: `docs/production-checklist.md`
