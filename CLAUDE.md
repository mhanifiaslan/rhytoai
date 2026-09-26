# RythoAI — Claude için proje notları

Bu dosya her oturumda otomatik okunur. Amacı: **makineler arasında taşınmayan
bilgiyi** taşımak. Buradaki her madde ya ölçülerek bulundu ya da bir kez
canlıda zarar verdi; hiçbiri teorik değil.

Ürün: doğum haritanı bilen ve gökyüzünü her gün takip eden kişisel AI astrolog.
Flutter mobil + FastAPI backend (Cloud Run) + bağımlılıksız vanilla-JS admin
panel. Firebase projesi **`rhytoai`**, paket adı **`ai.rytho`**.

---

## 1. Yazım dili ve yorum doktrini

Kod içindeki **yorumlar, değişken/fonksiyon adları ve test adları TÜRKÇE**
yazılır. Kullanıcıya görünen metinler `l10n` üzerinden TR+EN.

Yorum **NE yaptığını değil NEDEN öyle olduğunu** anlatır. "Bu döngü listeyi
gezer" değersizdir; "bu kapı şu yüzden var, olmasaydı şu sessizce bozulurdu"
değerlidir. Bir yorumun gerekçesi yanlışsa yorum **kusurdur** — bu depoda iki
kez yanlış gerekçe düzeltildi.

**Ölçülmeyen söylenmez.** Ürünün çekirdek ilkesi: hesaplanmamış bir şey
kullanıcıya söylenmez, beyan edilmez, metne girmez. Tersi de geçerli —
**ölçülen, yanlış adla sunulmaz**.

---

## 2. Ortam (makineye bağlı — kendi makinende doğrula)

| Şey | Gereklilik |
|---|---|
| Python | **3.11 ŞART.** 3.12'de `pyswisseph` kurulmuyor. venv: `backend/.venv` |
| Flutter | `3.44.7 stable` / Dart `3.12.2`; pubspec `sdk: ^3.12.0` |
| JDK | 17 (Android Gradle) |
| Android SDK | **cmdline-tools kurulu olmalı** — eksikken AAB derlemesi yanıltıcı bir "strip" hatası veriyor |
| gcloud / firebase | her komutta proje bayrağı: `--project rhytoai` |

`gcloud`'un varsayılan projesi başka bir projeye düşerse elle çalıştırdığın
komutlar **sessizce yanlış projeye** gider. Bu bir kez yanlış bir "panelde hiç
admin yok" blocker'ı ürettirdi.

Betikler PowerShell (`.ps1`) ve macOS'ta `pwsh` ile koşar:
`brew install --cask powershell`.

---

## 3. Git'in TAŞIMADIĞI dosyalar

Yeni bir makineye geçerken bunlar elle kopyalanır. Biri eksikken derleme
**sessizce** bozuk çıkar:

| Dosya | Eksikse ne olur |
|---|---|
| `apps/mobile/dart_defines.local.json` | Paket RevenueCat anahtarsız çıkar; cihazda **tüm satın almalar** "kullanılamıyor" der. Derleme BAŞARILI görünür. |
| `apps/mobile/android/key.properties` | Yayın imzası kurulmaz. İçindeki `storeFile` mutlak yol — makineye göre düzeltilir. |
| Keystore (`rytho-upload.jks`) | **Yeri doldurulamaz.** Kaybolursa uygulama bir daha güncellenemez. |
| `backend/.env` | Yerel backend anahtarları. |

`google-services.json` git'te **var**. Segmentasyon modeli (16 MB) git'te yok
ama tek komutla iner (`apps/mobile/scripts/fetch_models.ps1`); **o dosya
yokken `flutter test` hiç başlamaz** ("Failed to build asset bundle").

---

## 4. Asla atlanmayan kapılar

**AAB ASLA düz `flutter build appbundle` ile üretilmez.** Her zaman
`infra/build-aab.ps1`. Betikte beş kapı var ve hepsi sessiz hatalar için:
RevenueCat anahtarı gerçekten pakette mi, `test_` önekli anahtar değil mi,
imza debug'a düşmüş mü, kullanılmayan izin geri gelmiş mi (mağaza listesinde
"Mikrofon" yazardı ve gizlilik metnimizi yalanlardı), kamera zorunlu mu.

Bir kez 1.5.0+17 düz komutla üretildi: derleme başarılı, testler yeşil, imza
doğru — kusur ancak mağaza ekranında görüldü.

**Dağıtım:** backend `infra/deploy-backend.ps1`, hosting
`firebase deploy --only hosting --project rhytoai`.

---

## 5. Tekrar eden tuzaklar

**Testler üretime yazabiliyordu.** `conftest.py`'de üç autouse pin var
(`kapi_hermetik`, `depolama_hermetik`, `firestore_hermetik`). Sebep ölçüldü:
üretimde `users/dev-user` dokümanı bulundu, içinde o gün yazılmış bir
`termsConsent` vardı — `RYTHO_DEV_MODE` varsayılanı `"1"` ve makinede ADC var.
Pin sonrası takım süresi **214 sn → 83 sn** düştü.
**Kural: dış dünyaya çıkan her yeni istemci için `conftest`'e ayrı pin.**

**Türkçe metin eşleştirme.** `str.lower()` Türkçe bilmez (`"İ".lower()` →
`"i" + U+0307`). Alt dizi eşleşmesi yanlış pozitif üretir: "il**iş**kimde"
içinde "iş" var; ham `feedback` araması `HapticFeedback`'e takılıyor; ham
`['reply']` sohbet cevabına takılıyor. Eşleşmeyi **kelime başına ya da dize
literaline** bağla.

**Bir şeyin YOKLUĞUNU arayan bekçi, onu ANLATAN yorumu görmemeli.** İki kez
patladı: build kapısı kendi manifest yorumuna takıldı, davet sayfası testi
kendi HTML yorumuna. Eşleşmeden **önce yorumları at**.

**PowerShell kaynak dosyaya DOKUNMAZ.** Windows'ta ANSI kod sayfası cp1254;
`Get-Content`/`Set-Content` UTF-8 kaynağı bozuyor (`GÖKYÜZÜ` → `GÃ–KYÃœZÃœ`)
ve `flutter analyze` bunu fark etmiyor. Satır düzenlemesi için Python
(`io.open(..., encoding='utf-8')`).

**`core.autocrlf=true`.** Dosyaların çoğu CRLF. İçeriği LF yazarsan tek
satırlık düzeltme 1000+ satırlık hayalet diff'e döner. Yazarken dosyanın
kendi satır sonunu koru.

**Riverpod:** `FutureProvider` varsayılan `isAutoDispose = false` — yutulan
bir hata **oturum boyunca** önbellekte kalır. Ayrıca `apiProvider`'ın
interceptor'larından `apiProvider`'ı izleyen bir sağlayıcıya dokunmak
`CircularDependencyError` fırlatır (bkz. bulgu B10).

---

## 6. Bugünkü durum (2026-09-25)

Dal: `yuz-okuma-cihaz-usti-olcum`. Sürüm **1.16.0+45**. Backend rev **00096**.

**Kapalı test yürüyor** (Alpha kanalı). 45 hem dahili hem kapalı testte.

⚠️ **Üretim yolundaki tek kritik madde: testçi sayısı.** Kontrol panelinde
"0 test kullanıcısı kayıtlı" görünüyordu — 12 testçi / 14 gün sayacı
testçiler **opt-in bağlantısını açana kadar başlamaz**. Listeye eklemek
yetmiyor.

**App Check zorlaması AÇILDI** (2026-09-26 08:50 UTC). Ölçülen durum:
`firestore.googleapis.com` **ENFORCED**, `identitytoolkit.googleapis.com`
**ENFORCED**, `firebasestorage.googleapis.com` **UNENFORCED** (kalan tek
servis; avatar yolu). Sorgu:
`GET firebaseappcheck.googleapis.com/v1/projects/rhytoai/services/{servis}`
— ADC ile çağırırken `x-goog-user-project: rhytoai` başlığı ŞART, yoksa
kota projesi hatası döner.

App Check 1.15.8+43'te eklendi, yani **43 öncesi derlemeler artık
çalışmıyor**. Açıldığı an üç hesap 43'ün altındaydı (`erkandndr@gmail.com`
sürümü bilinmiyor, `yhykbr1984@gmail.com` ve `mhanifiaslan@yandex.com`
41); sahibin kararı: yeniden kursunlar.

**Web yüzeyleri App Check kullanıyor** (2026-09-26, ölçüldü). Zorlama
açılınca panel girişi ve şifre sıfırlama sayfası TAMAMEN kapanmıştı —
mobilde App Check 43'ten beri vardı ama webde hiç yoktu. Ortak kurulum
`web/assets/appcheck.js`. Üç incelik:

- Sağlayıcı **reCAPTCHA ENTERPRISE**, v3 değil: klasik reCAPTCHA
  kullanımdan kalktı, Firebase Console o formu artık doldurtmuyor. v3
  Firebase'e GİZLİ anahtar verdiriyordu; Enterprise yalnız SİTE anahtarını
  alıyor (paylaşılan sır yok). Site anahtarı herkese açıktır, depoda durur.
- App Check **örnek başınadır**. Panel, giriş penceresini same-origin
  yapmak için ikinci bir Firebase örneği (`'yonetim'`) kuruyor; yalnız
  birini etkinleştirmek diğerinin isteklerini jetonsuz bırakır.
- reCAPTCHA anahtarının izinli alan adları arasında
  **`rhytoai.firebaseapp.com` ŞART** — `authDomain` o ve giriş işleyicisi
  orada çalışıyor. Aynı alan adı Browser API anahtarının referrer
  listesinde de olmalı.

Doğrulama (tarayıcıda, uçtan uca): panelde `signInWithEmailAndPassword`
→ `auth/invalid-credential`, şifre sayfasında `applyActionCode` →
`auth/invalid-action-code`. İkisi de **App Check hatası değil**, yani kapı
aşılıyor.

**API anahtarları kısıtlandı** (2026-09-26): Android anahtarı → paket
`ai.rytho` + Firebase'de kayıtlı 5 SHA-1; Browser anahtarı → `rytho.app`,
`www.rytho.app`, `rhytoai.web.app`, `rhytoai.firebaseapp.com`. Bot kapısı
buydu ve kapandığı ölçüldü: kısıtsız istek artık
`Requests from this Android client application <empty> are blocked`.

**Açık bulgular** (`docs/test-raporu.md`): **B9** silinen hesap "en iyi
çaba" aynalarıyla diriliyor (ölçüldü); **B10** 402 kapısı ve cüzdan
tazelemesi Riverpod halkasına çarpıyor (ölçüldü, uygulanmadı).

**Konsol borcu:** API anahtarlarında **uygulama kısıtlaması YOK**
(`Android key` ve `Browser key`, ölçüldü 2026-09-26) — anahtar APK'nın
içinde herkese açık ve izinli API'ler arasında `identitytoolkit` var, yani
bot kayıt yolu buradan geçiyor. Play Console ürün adları hâlâ uygulamanın sözlüğüne
uymuyor (makbuzda "1000 Jeton", uygulamada "1000 kredi") — girilecek tam
metin `docs/store-launch.md`'de tabloyla hazır.

**Mağaza görselleri bayat olabilir** — `store/play/` kareleri ham cihaz
yakalamalarından üretiliyor, yani koddaki metin düzeltmesi kareye
yansımaz. `shot-1-sky.png` düzeltilmiş bir kusuru göstermeye devam
ediyor. Kural: **piksel elle düzenlenmez**, ya kadraj ya yeniden yakalama.

### Play Console tuzakları (ölçüldü, gün kaybettirdi)

**"Reklam kimliği beyanı eksik" hatası ETKİN TÜM KANALLARA bakar.** İzni
44'te kaldırdık ama hata sürdü: **dahili test** hâlâ 41'deydi ve o pakette
AD_ID vardı. Kapalı testi temizlemek yetmedi. 10 saniyelik teşhis: formda
**Evet** → kaydet. Evet'te AD_ID'siz sürüm yalnız uyarılır, Hayır'da
AD_ID'li paket varsa **engellenir**; Evet'te gönder açılıp Hayır'da hata
dönüyorsa suçlu bir kanalda duran eski pakettir. Kod suçlanmadan önce bu
yapılır.

**Sürüm kodu uygulama genelinde benzersizdir, kanal başına değil.** Aynı
AAB'yi ikinci bir kanala **yükleyemezsin** ("sürüm kodu daha önce
kullanıldı"). Kanallar arası taşıma **yalnız yukarı** çalışır:
dahili → kapalı → üretim, "Sürümü yükselt" ile.

**Hedef kanalda taslak sürüm varsa yükseltme kapalı kalır**
("Kanalın zaten taslak bir sürümü var"). Ya taslağı sil, ya da taslağı
düzenleyip paketi **kitaplıktan** seç (yeniden yükleme değil, o yüzden
"kod kullanıldı" hatası vermez).

### Derleme ortamı tuzakları (2026-09-25)

**Flutter, JAVA_HOME'u değil Android Studio'nun JBR'sini kullanabiliyor.**
`JAVA_HOME` Adoptium 17'yi gösterirken derleme JBR **21** ile koşuyordu.
`flutter doctor -v` hangi Java'yı kullandığını söyler; sabitlemek için
`flutter config --jdk-dir="<jdk17 yolu>"`.

**Gradle'ın JVM'i çökebiliyor** (`EXCEPTION_ACCESS_VIOLATION`). Çökme
GC'de DEĞİL `MethodHandleNatives.resolve`'daydı ve hem JBR 21'de hem
Temurin 17'de tekrarladı — yani JDK satıcısı değildi. `flutter clean`
sonrası tekrarlamadı. Çökme günlüğü `apps/mobile/android/hs_err_pid*.log`;
**çöken iş parçacığına bak**, "GC" görünce bellek sanma.

## 7. iOS durumu

`apps/mobile/ios/` projesi **var** ve beklenenden ileride: bundle id
`ai.rytho`, Info.plist izin metinleri yazılı, `Runner.entitlements`'ta Apple
ile Giriş + associated-domains, `sign_in_with_apple` hem pakette hem
`auth_service.dart`'ta, `REVENUECAT_IOS_KEY` dart-define yuvası tanımlı,
`apple-app-site-association` canlıda.

**Eksikler (ölçüldü):** `GoogleService-Info.plist` yok · `Podfile` yok ·
entitlements'ta `aps-environment` yok (push iOS'ta çalışmaz) ·
`apple-app-site-association` içinde `TEAMID` **yer tutucu** ·
`associated-domains` hâlâ `rhytoai.web.app` diyor ama alan adı **`rytho.app`**'e
taşındı (davet bağlantıları iOS'ta açılmaz) · App Store Connect kaydı ve IAP
ürünleri yok (Play'dekilerden ayrı oluşturulur) · Info.plist izin metinleri
yalnız Türkçe.

iOS derlemesi/imzalaması/yüklemesi **yalnız macOS**'ta yapılabilir.

---

## 8. Belgeler

`docs/test-raporu.md` — senaryo listesi ve bulgular (B1…B10) ·
`docs/konsol-gorevleri.md` — Firebase/Play/Cloud konsol işleri ·
`docs/store-launch.md` — mağaza metni, yasak dil, görsel borçları ·
`docs/maliyet-calismasi.md` — birim maliyetler ve marj ·
`docs/ozellikler.md` — ücretsiz/Plus tarifesi (koddan sapmamalı) ·
`docs/design/design-system.md` — hareket ve tipografi doktrini.
