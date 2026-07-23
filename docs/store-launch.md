# Rytho Mağaza Yayın Rehberi

Bu doküman; Android imzalama, Play Console iç test, App Check ve mağaza
politika notları ile monetizasyon planını içerir. **Buradaki adımların çoğu
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
2. "Uygulama oluştur" → ad: Rytho, dil: Türkçe, tür: Uygulama, ücretsiz.
3. **Uygulama içeriği** bölümünü doldur:
   - Gizlilik politikası URL'si (docs/legal/gizlilik-politikasi.md bir web
     adresinde yayınlanmalı — örn. Firebase Hosting).
   - Veri güvenliği formu: konum yok; kişisel bilgi (ad, e-posta), doğum
     bilgisi, fotoğraf (işlenir, SAKLANMAZ) beyan et.
   - İçerik derecelendirmesi anketi: "fal/eğlence" içeriği işaretle.
4. **Test → İç test** → yeni sürüm oluştur → `.aab` yükle → test kullanıcısı
   e-postalarını ekle → yayınla. Test bağlantısı e-postayla gelir.
5. Play App Signing'i kabul et (Google imzalama anahtarını yönetir; senin
   ürettiğin anahtar "upload key" olur).

## 3. Firebase App Check (Play Integrity)

Kod tarafına SDK henüz EKLENMEDİ (bilinçli olarak); önce konsol hazırlığı:

1. Firebase Console → rhytoai → **App Check** → "Get started".
2. Android uygulaması (ai.rytho) için sağlayıcı: **Play Integrity** seç;
   Play Console'da uygulamanın yayınlanmış (en az iç test) olması gerekir.
3. SHA-256 imza parmak izlerini Firebase proje ayarlarına ekle
   (`keytool -list -v -keystore ...` çıktısındaki SHA-256).
4. Kod tarafı (konsol hazır olunca):
   - `flutter pub add firebase_app_check`
   - `main.dart` içinde `await FirebaseAppCheck.instance.activate(
     androidProvider: AndroidProvider.playIntegrity)` (Firebase.initializeApp
     sonrası).
5. Önce **izleme modunda** çalıştır (enforcement kapalı), metrikler temizse
   Firestore + backend için enforcement'ı aç.
6. Backend'in App Check token doğrulaması istenirse `firebase_admin` ile
   `app_check.verify_token` middleware'i eklenebilir (ayrı iş).

## 4. Mağaza politika notları

### Apple App Store — Kural 5.3.1 ve "fal" uygulamaları
- Apple, astroloji/fal uygulamalarını **4.3 (spam/kopya)** ve **5.6** başlıkları
  altında sık inceler; "burç uygulaması enflasyonu" nedeniyle ret riski vardır.
  Rytho'nun ayırt edici özellikleri (gerçek efemeris hesabı, BaZi + I Ching +
  yüz analizi sentezi, sosyal katman) inceleme notunda vurgulanmalı.
- **5.3.1** kumar/piyango kuralıdır: uygulamada gerçek para ödülü, bahis veya
  piyango ÇAĞRIŞIMI yapan hiçbir mekanik olmamalı (I Ching "para atma"
  animasyonu bir kehanet ritüelidir, kumar değildir — açıklamada netleştir).
- Yorumların "eğlence amaçlı" olduğu ibaresi hem uygulama içinde (mevcut)
  hem App Store açıklamasında yer almalı.
- iOS derlemesi macOS gerektirir; TestFlight için Apple Developer Program
  (99 USD/yıl) hesabı gerekir.

### Google Play — "fal/eğlence" kategorisi
- Kategori: **Yaşam Tarzı** veya **Eğlence** seç ("Fal" alt etiketi arama
  anahtar kelimeleriyle sağlanır).
- İçerik derecelendirmesinde "simya/fal/astroloji" içeriğini doğru beyan et;
  yanlış beyan kaldırma sebebidir.
- Veri güvenliği formunda yüz fotoğrafının **işlendiğini ama saklanmadığını**
  açıkça beyan et; bu, incelemede güçlü bir artıdır.
- Sosyal özellikler (UGC) nedeniyle: şikayet mekanizması, engelleme ve
  moderasyon zorunludur — **uygulamada mevcut** (Faz 4'te eklendi).

## 5. Monetizasyon planı (öneri — kod tarafı uygulanmadı)

RevenueCat ile abonelik altyapısı (Play Billing + StoreKit'i tek SDK'da
soyutlar, sunucu tarafı doğrulama ve deneme yönetimi hazır gelir):

| Katman | İçerik |
|---|---|
| **Ücretsiz** | Günlük okuma, temel natal harita, sınırlı sohbet (örn. 5 mesaj/gün), Meclis sosyal özellikleri |
| **Premium** (aylık/yıllık) | Sınırsız sohbet, derin raporlar (natal tam + BaZi tam), sinastri (kozmik uyum), yüz okuma |

Uygulama adımları (ileride):
1. RevenueCat hesabı → proje → Play Console API anahtarı bağla.
2. Play Console → Para kazanma → abonelik ürünleri: `rytho_premium_monthly`,
   `rytho_premium_yearly` (+7 gün deneme önerilir).
3. `flutter pub add purchases_flutter` → paywall ekranı → `entitlement`
   kontrolü ile premium uçları kilitle.
4. Backend'de kota: ücretsiz kullanıcıların sohbet/rapor sayısı zaten
   rate limiting ile sınırlı; premium ayrımı için Firestore'da
   `users/{uid}.premium` alanı + backend kontrolü eklenebilir.

## 6. Yayın öncesi kritik hatırlatmalar

- **Swiss Ephemeris ticari lisansı**: kerykeion/pyswisseph AGPLv3'tür; kapalı
  kaynak mağaza yayını ÖNCESİ Astrodienst AG'den ticari lisans alınmalı
  (~750 CHF, tek seferlik): https://www.astro.com/swisseph/
- Gizlilik politikası ve kullanım şartları bir web adresinde yayınlanmalı
  (mağaza formları URL ister) — Firebase Hosting önerilir.
- Cloud Run `--max-instances 3` ve rate limiting mevcut; lansman sonrası
  trafiğe göre gözden geçir.
