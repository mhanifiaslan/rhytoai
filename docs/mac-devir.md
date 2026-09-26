# Mac'e devir ve iOS başlangıcı

Bu belge, depoyu bir Mac'e taşıyıp iOS sürecini başlatmak içindir. Her
madde ya ölçülerek bulundu ya da bir kez zarar verdi. Windows makinesinde
**her şey çalışıyor**; buradaki listede yazanlar Mac'te *ek olarak* gereken
şeyler.

Ölçüm tarihi: **2026-09-26**. Dal: `yuz-okuma-cihaz-usti-olcum`.
Uzak depo: `https://github.com/mhanifiaslan/rhytoai.git`

---

## 1. Mac'e kurulacaklar

| Araç | Sürüm | Not |
|---|---|---|
| Xcode | güncel | **Yalnız macOS**. `xcode-select --install` yetmez, tam Xcode gerekir |
| CocoaPods | güncel | `sudo gem install cocoapods` ya da `brew install cocoapods` |
| Flutter | **3.44.7 stable** (Dart 3.12.2) | `pubspec` `sdk: ^3.12.0`. Farklı minör sürüm kilit dosyasını oynatır |
| Python | **3.11 ŞART** | 3.12'de `pyswisseph` kurulmuyor. venv: `backend/.venv` |
| JDK | 17 | Android tarafını Mac'te de derleyeceksen |
| PowerShell | `brew install --cask powershell` | `infra/*.ps1` betikleri `pwsh` ile koşar |
| gcloud + firebase CLI | güncel | Her komutta `--project rhytoai` |

Xcode'u kurduktan sonra bir kez aç ve lisansı kabul et; aksi hâlde
`pod install` anlaşılmaz bir hatayla düşer.

---

## 2. Git'in TAŞIMADIĞI dosyalar — elle kopyalanır

Bunlar `.gitignore`'da. Biri eksikken derleme **sessizce** bozuk çıkar:
komut başarılı olur, kusur ancak cihazda ya da mağazada görülür.

| Dosya | Eksikse ne olur |
|---|---|
| `apps/mobile/dart_defines.local.json` | Paket RevenueCat anahtarsız çıkar; cihazda **tüm satın almalar** "kullanılamıyor" der. **Derleme BAŞARILI görünür.** |
| `apps/mobile/android/key.properties` | Yayın imzası kurulmaz. İçindeki `storeFile` **mutlak yol** — Mac'teki keystore yoluna göre düzeltilir |
| Keystore (`rytho-upload.jks`) | **Yeri doldurulamaz.** Kaybolursa uygulama bir daha güncellenemez. Güvenli bir yoldan taşı, e-postayla değil |
| `backend/.env` | Yerel backend anahtarları. Örneği git'te: `backend/.env.example` |

`google-services.json` git'te **var** — onu taşıma. Segmentasyon modeli
(16 MB) git'te yok ama tek komutla iner:
`apps/mobile/scripts/fetch_models.ps1` (pwsh ile). **O dosya yokken
`flutter test` hiç başlamaz** ("Failed to build asset bundle").

`dart_defines.local.json` taşındıktan sonra **içindeki
`REVENUECAT_IOS_KEY` değerini kontrol et** — şu an `test_` önekli, yani
RevenueCat Test Store anahtarı, App Store anahtarı değil (madde 6.7).

---

## 3. Klonlama ve ilk koşu

```bash
git clone https://github.com/mhanifiaslan/rhytoai.git
cd rhytoai
git checkout yuz-okuma-cihaz-usti-olcum
```

Sonra 2. bölümdeki dosyaları yerlerine koy. Ardından:

```bash
cd apps/mobile
flutter pub get
pwsh scripts/fetch_models.ps1     # segmentasyon modeli (16 MB)
flutter analyze                   # beklenen: No issues found
flutter test                      # beklenen: 574 test geçer
```

Backend:

```bash
cd backend
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q     # beklenen: 1590 test geçer
```

Betikler macOS'a hazır (ölçüldü): `infra/deploy-backend.ps1` venv düzenini
iki platformda da buluyor (`Scripts/python.exe` → `bin/python`),
`infra/build-aab.ps1` flutter'ı önce PATH'ten arıyor. Ama
`infra/store-screenshots.py`, `infra/store-graphics.py` ve `ads/` altındaki
betikler **sabit Windows yolu taşıyor** (`D:\...`, `C:\Windows\Fonts`,
ffmpeg yolu) — bunlar mağaza görseli ve reklam üretimi içindir, derleme
yolunda değildir; Mac'te kullanılacaksa yolları parametreleştirilmeli.

---

## 4. iOS: sıralı yol haritası

Sıra **bağımlılık sırasıdır**, önem sırası değil. Her adım bir öncekini
gerektiriyor; atlanırsa sonraki adım anlaşılmaz bir hatayla düşer.

### 4.1 — Apple Developer Program üyeliği · **SEN**
Yıllık ücretli. Bunsuz ne imzalama ne TestFlight ne App Store Connect var.
Üyelikten çıkan **Team ID** (10 karakter) üç yerde birden lazım: Xcode
imzalama, `apple-app-site-association`, ve entitlements profili.

### 4.2 — Firebase'de iOS uygulaması kaydı · **SEN**
Firebase Console → proje `rhytoai` → iOS uygulaması ekle, bundle
`ai.rytho`. Çıkan **`GoogleService-Info.plist`**'i indir.

⚠️ Dosyayı `apps/mobile/ios/Runner/` altına kopyalamak **YETMEZ**.
`project.pbxproj`'de dosya referansı ve Copy Bundle Resources girdisi yok
(ölçüldü: `grep GoogleService project.pbxproj` hiçbir şey dönmüyor), yani
pakete girmez. Xcode'da Runner hedefine **sürükleyerek** ekle ve "Copy
items if needed" + Runner target işaretli olsun.

Bunsuz uygulama **ilk karede çöker**: `main.dart:78` `Firebase.initializeApp()`
seçeneksiz çağrılıyor ve depoda `firebase_options.dart` yok, yani
yapılandırmanın tek kaynağı bu dosya.

### 4.3 — Google ile giriş · **SEN (plist geldikten sonra)**
`GoogleService-Info.plist` içindeki **`REVERSED_CLIENT_ID`** değeri
`Info.plist`'e `CFBundleURLTypes` olarak yazılır, ayrıca `GIDClientID`
eklenir. Şu an ikisi de yok (ölçüldü). Bunlar olmadan Google girişi iOS'ta
açılmaz — geri dönüş URL'si kaydedilmemiş olur.

Ek olarak `main.dart:133` `GoogleSignIn.instance.initialize` yalnız
`serverClientId` geçiyor; iOS `clientId` de ister. Plist gelince bu satır
güncellenecek.

### 4.4 — İmzalama · **SEN (Xcode'da)**
`project.pbxproj`'de `DEVELOPMENT_TEAM` anahtarı **hiç yok** ve Runner
hedefinde `CODE_SIGN_STYLE` yok; imza kimliği eski biçimde
(`"CODE_SIGN_IDENTITY[sdk=iphoneos*]" = "iPhone Developer"`). Xcode'da
Runner → Signing & Capabilities → Team seç; Xcode gerekli anahtarları
kendisi yazar. **Bunu Xcode'a yaptır**, elle pbxproj düzenleme.

### 4.5 — Yetenekler (Capabilities) · **SEN (Xcode'da)**
Apple Developer portalında App ID üzerinde de **açık olmalı**, yalnız
entitlements dosyası yetmez:
- **Sign in with Apple** (App Store Guideline 4.8 gereği zorunlu)
- **Push Notifications**
- **Associated Domains**

Depo tarafı hazır: `Runner.entitlements` (Debug/Profile) ve
`RunnerRelease.entitlements` (Release) ikisi de yazıldı ve `pbxproj`
Release bloğu ikincisine bakıyor.

⚠️ İkisi **yalnız `aps-environment` değerinde** farklı: `development` ve
`production`. Bu ayrım bilinçli ve sessiz bir tuzağı kapatıyor — tek dosya
kullanılıp `development` kalsaydı üretim paketi **sandbox** APNs jetonu
alır, sunucu üretim APNs'ine gönderir ve bildirim hiçbir yere düşmezdi:
TestFlight'ta çalışır, mağazada ölür. Dosyalardan biri değişirse
**diğeri de aynı şekilde değişmeli**.

### 4.6 — APNs anahtarı · **SEN**
Apple Developer → Keys → yeni **APNs Auth Key** (.p8) oluştur, Firebase
Console → Project Settings → Cloud Messaging → iOS bölümüne yükle
(Key ID + Team ID ile birlikte). Bunsuz FCM iOS'a bildirim gönderemez.

### 4.7 — RevenueCat iOS anahtarı ve IAP ürünleri · **SEN**
`dart_defines.local.json`'daki `REVENUECAT_IOS_KEY` şu an
`test_...` önekli — **RevenueCat Test Store** anahtarı, satın almaları
simüle eder. Gerçek App Store anahtarı `appl_...` ile başlar.

App Store Connect'te ürünler **Play'dekilerden ayrı** oluşturulur. Kimlikler
kodda sabit, **değiştirme**:
`rytho_plus_monthly` · `rytho_tokens_small` · `rytho_tokens_medium` ·
`rytho_tokens_large`. Görünen adlar `docs/store-launch.md`'de tabloyla hazır.
RevenueCat'te abonelik `RhytoAI Pro` entitlement'ına bağlanır (paketler
bağlanmaz) — panel adıyla **birebir** aynı olmalı.

### 4.8 — `apple-app-site-association` · **SEN (Team ID gelince)**
`web/.well-known/apple-app-site-association` içinde
`"appID": "TEAMID.ai.rytho"` — **`TEAMID` yer tutucu**. Gerçek Team ID
yazılıp `firebase deploy --only hosting --project rhytoai` ile yayınlanır.
Bunsuz davet bağlantıları iOS'ta uygulamayı açmaz, tarayıcıya düşer.

Entitlements tarafı hazır: `applinks:rytho.app` **ve**
`applinks:rhytoai.web.app` ikisi de yazılı (sahadaki eski davet bağlantıları
ikincisini taşıyor).

### 4.9 — App Store Connect kaydı ve `APPSTORE_APP_ID` · **SEN**
Kayıt açılınca **sayısal uygulama kimliği** doğar. Onu
`dart_defines.local.json`'a `APPSTORE_APP_ID` olarak yaz.

Boş bırakılırsa zorunlu güncelleme ekranı iOS'ta mağaza düğmesi
**göstermez** ve dürüst bir mesaj verir. Bu bilinçli: uydurma bir kimlikle
kurulan bağlantı mağazada "uygulama bulunamadı" açar ve kullanıcı o
ekranda gerçekten kilitli kalır (bekçi:
`test/force_update_screen_test.dart`).

---

## 5. Depo tarafında BİTMİŞ olanlar

Mac'te bunları yeniden yapma, yapıldı ve testten geçti:

- **`ios/Podfile`** yazıldı, `platform :ios, '15.5'` **açık**. Flutter'ın
  şablonunda bu satır yorumlu gelir ve o yüzden `pod install` şu hatayla
  düşerdi: *"platform of the target Runner (iOS 13.0) is not compatible
  with google_mlkit_face_detection which has a minimum requirement of
  iOS 15.5"*. 15.5 keyfî değil, paketlerin dayattığı taban.
- **Deployment target 15.5** — `pbxproj`'de üç yapılandırmada da.
- **App Check Apple sağlayıcısı** — `main.dart` artık `providerApple`
  geçiyor (`AppleAppAttestProvider`, debug'da `AppleDebugProvider`).
  Zorlama 2026-09-26'da açıldığı için bu olmadan iOS paketi Firestore ve
  Auth'a **hiç bağlanamazdı**.
- **`aps-environment`** + `UIBackgroundModes/remote-notification` (4.5).
- **`ITSAppUsesNonExemptEncryption = false`** — yoksa App Store Connect
  her TestFlight yüklemesinde ihracat sorusunu yeniden sorar.
- **`STRIP_STYLE = non-global`** — `tflite_flutter` README'sinin uyardığı
  arşiv kusuru: Xcode sembolleri soyunca `flutter build ipa` sonrası
  çalışma anında "symbol not found" ile patlıyor.
- **Zorunlu güncelleme ve abonelik yönetimi** artık platforma göre dallanıyor.
- **Mağaza metinleri nötr** — dört kullanıcı dizesi "Google Play" yazmıyor
  artık. Türkçe ek uyumu yüzünden yer tutucu kullanılamadı ("Play'**de**"
  ama "App Store'**da**"), bu yüzden mağaza adı metinden çıkarıldı.

---

## 6. Bitmemiş, Mac'te yapılacak kod işleri

- **`en.lproj/InfoPlist.strings` bağlanmalı.** Dosya
  `apps/mobile/ios/Runner/en.lproj/` altında **hazır** ama Xcode projesine
  bağlı değil: Copy Bundle Resources'ta yok ve `knownRegions` yalnız
  `(en, Base)`. Windows'tan pbxproj'e variant-group cerrahisi yapmak
  projeyi hiç açılmaz hâle getirebilirdi, o yüzden yapılmadı.
  Xcode'da: Info.plist seç → File Inspector → Localize → Türkçe ekle.
  Şu an `developmentRegion = en` ama Info.plist metinleri **Türkçe**, yani
  İngilizce cihaz Türkçe izin diyaloğu görüyor. Türkiye-öncelikli
  lansmanda kabul edilebilir; **dünyaya açılmadan önce** düzeltilmeli.
- **`AppDelegate.swift`'te bildirim delegesi.** `flutter_local_notifications`
  22.2.0 README'si (iOS setup) `UNUserNotificationCenter.current().delegate`
  atamasını istiyor; şu an yok. **Körlemesine eklenmedi**, çünkü
  `firebase_messaging` de aynı delegeyi sahipleniyor ve hangisinin
  kazandığı ancak **cihazda** ölçülebilir. Mac'te gerçek cihazla
  doğrulanarak eklenmeli — "ölçülmeyen söylenmez".
- **`main.dart:133` `GoogleSignIn` `clientId`** — 4.3'e bağlı.

---

## 7. macOS'a özgü tuzaklar

- **`pod install` Xcode lisansı kabul edilmeden düşer.** Xcode'u bir kez
  aç, lisansı kabul et.
- **`flutter build ipa` yalnız macOS'ta çalışır** — imzalama ve arşivleme
  Apple araçlarına bağlı. Windows'tan iOS paketi üretilemez.
- **Simülatörde çalışmayan iki şey var:** TFLite (tflite_flutter README'si
  söylüyor) ve App Attest. İkisi de **gerçek cihaz** ister. Yüz okuma ve
  App Check'i simülatörde test etmeye çalışma.
- **`gcloud`'un varsayılan projesi kayabiliyor.** Her komutta
  `--project rhytoai` yaz; yoksa komutlar **sessizce yanlış projeye**
  gider. Bu bir kez yanlış bir "panelde hiç admin yok" blocker'ı ürettirdi.
- **Satır sonları.** Depoda `core.autocrlf` Windows tarafında etkin ve
  dosyaların bir kısmı CRLF (ör. `ios/Runner/Info.plist`,
  `AppDelegate.swift`), çoğu LF. Düzenlerken **dosyanın kendi satır
  sonunu koru**, yoksa tek satırlık bir düzeltme 1000 satırlık hayalet
  diff'e döner.

---

## 8. Mac'teki Claude'a söylenecek ilk şey

`CLAUDE.md` her oturumda otomatik okunuyor, yani temel bilgi zaten
yüklenir. Bu belgeyi ayrıca göstermek gerekir:

> Bu depoyu Windows'tan yeni taşıdım, iOS sürecini başlatacağız.
> `docs/mac-devir.md`'yi oku — Mac kurulumu ve iOS yol haritası orada.
> Önce 3. bölümdeki doğrulamayı koş (`flutter analyze`, `flutter test`,
> `pytest`) ve bana sonucu söyle; beklenen değerler belgede yazılı.
> Sonra 4. bölümdeki sırayı takip edeceğiz, ben hesap işlerini yapacağım.

**Hiçbir şeyi hatırladığını sanma, ölç.** Bu depoda notların bayatladığı
iki kez yakalandı ve ikisi de yanlış yöne saatler harcattı.
