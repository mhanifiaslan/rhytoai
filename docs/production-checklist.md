# Üretim Yayın Kontrol Listesi

Bu liste **v1 kapsamına** göre yazıldı. Kapsam dışı bırakılanlar burada da
yok: yüz okuma, gönderi akışı, birebir mesajlaşma, takip ilişkileri.
Gerekçeler: `docs/store-review-notes.md`.

İşaretli maddeler **kodda doğrulanabilir**. İşaretsiz olanların çoğu
konsol/hesap işlemi gerektirir ve uygulama sahibinin işidir.

---

## 1. Lisans ve hukuk

- [ ] **Swiss Ephemeris ticari lisansı** — kerykeion/pyswisseph AGPLv3.
      Kapalı kaynak mağaza yayını öncesi Astrodienst AG'den ticari lisans
      alınmalı (~750 CHF, tek seferlik): https://www.astro.com/swisseph/
      **→ Yayından önce zorunlu, uygulama sahibinin işi.**
- [x] Gizlilik politikası ve kullanım şartları **iki dilde, uygulama içinde**
      (`apps/mobile/lib/features/profile/legal_texts.dart`; Profil → Hakkında
      ve satın alma ekranından erişilebilir)
- [x] Metinler gerçek ürünü anlatıyor: bildirim katmanı, kullanıcı hafızası,
      abonelik ve arkadaş katmanı yazılı; kaldırılan özellikler (yüz analizi,
      gönderi, DM) metinlerden çıkarıldı
- [ ] **Hukukçu incelemesi** — metinler mühendislik taslağıdır; KVKK/GDPR
      açısından yayın öncesi gözden geçirilmeli
- [ ] Hukuki metinleri bir web adresinde yayınla (mağaza formları URL ister;
      Firebase Hosting yeterli)
- [x] Gizlilik etiketleri beyanı hazır (`docs/store-privacy-labels.md`)
- [ ] Beyan iki konsola girildi

## 2. Güvenlik

- [x] Firebase Auth ID token doğrulaması (üretimde `RYTHO_DEV_MODE=0`;
      401 canlıda doğrulandı)
- [x] Firestore kuralları deploy edildi. `users/{uid}` **yalnızca sahibine
      okunabilir** (doğum verisi içerir); arkadaşların gördüğü alanlar ayrı
      `publicProfiles/{uid}` kartında
- [x] `users/{uid}/private/**` istemciye tamamen kapalı (hafıza, abonelik,
      bildirim gönderim kaydı) — yalnızca Admin SDK erişir
- [x] Gemini anahtarı, RevenueCat webhook anahtarı ve bildirim zamanlayıcı
      anahtarı Secret Manager'da
- [x] Rate limiting (`backend/core/ratelimit.py`) — LLM uçları 10/dk,
      diğerleri 60/dk
- [x] Ham istisna metni kullanıcıya sızmıyor (`core/messages.py`); güvenlik
      başlıkları yayında
- [x] Toplu bildirim ucu yalnızca paylaşılan zamanlayıcı anahtarıyla çalışıyor
- [ ] Firebase App Check (Play Integrity) — **konsol tarafı uygulama
      sahibinde**; adımlar `docs/store-launch.md` §3
- [ ] Cloud Run soğuk başlatma / maliyet dengesi gözden geçir

## 3. Hesap ve veri hakları

- [x] **Uygulama içi hesap silme** (Apple 5.1.1(v) / Play zorunluluğu) —
      Profil → Hesabı sil. Ne silineceği ve ne silinmeyeceği yazılı, yazarak
      onay isteniyor
- [x] Silme tüm yayılımı kapsıyor: alt koleksiyonlar, **karşı taraftaki
      arkadaşlık kayıtları**, gönderilen tepkiler, kullanıcı adı rezervasyonu,
      herkese açık kart, kişiye özel yapay zeka üretimleri, Firebase kimliği
      (`backend/services/account_service.py`)
- [x] Şikayet kayıtları bilinçli olarak korunuyor (başkalarının güvenliği) —
      gizlilik metninde ve silme onayında yazılı

## 4. Ürün ilkeleri (kodda korunuyor)

- [x] Hiçbir gök verisi uydurulmuyor; her konum Swiss Ephemeris ile hesaplanıyor
- [x] Yasak alan kapısı (sağlık/hamilelik/ölüm/finans) **iki dilde** çalışıyor
      ve modele hiç gitmiyor
- [x] Persona yağcılık yapmıyor; testle korunuyor
- [x] Kullanıcılar arası **serbest metin yok** — kapalı tepki kümesi
- [x] Kalıcı uyum skoru yok; ikili dinamik günlük

## 5. Birim ekonomi

- [x] Ücretsiz katman paylaşımlı önbellekten okuyor: burç yorumu dil × burç ×
      dönem başına tek LLM çağrısı
- [x] Bildirim metni burç başına üretiliyor — günde en fazla 24 çağrı,
      kullanıcı sayısından bağımsız
- [x] Kişiye özel uçlar abonelik veya günlük kotayla korunuyor
      (`backend/core/entitlements.py`)
- [ ] Önbellek isabet oranını canlıda izle (maliyet öngörüsü buna bağlı)

## 6. Çok dillilik

- [x] TR + EN: arayüz, backend yorumları, hata metinleri, bildirimler
- [x] Hesap motorları dilden bağımsız anahtar döndürüyor; ad isteğin dilinde
      çözülüyor
- [x] Dil sızıntısı muhafızı (`backend/tests/test_language_isolation.py`)
- [x] Mobil sabit metin tarayıcısı (`apps/mobile/tool/scan_hardcoded_strings.py`)

## 7. Bildirimler

- [x] Cloud Scheduler → saatlik toplu gönderim; yerel saat, sessiz saat,
      tercih ve tekrar koruması
- [x] Yüksek öncelikli Android kanalı; uygulama ön plandayken de gösteriliyor
- [x] Saat dilimi ve dil profile yazılıyor (`flutter_timezone`)
- [x] Geçersiz token ilk başarısız gönderimde temizleniyor
- [x] Cihazda gerçek push doğrulandı
- [ ] Canlıda ilk gerçek sabah gönderimini izle (log: `api.notify`)

## 8. Kalite

- [x] Crashlytics bağlı (debug/web'de devre dışı)
- [x] Backend test takımı — 300+ test
- [ ] **Analytics olay şeması bayat**: `apps/mobile/lib/core/analytics.dart`
      hâlâ kaldırılmış özelliklerin olaylarını taşıyor (`post_published`,
      `user_followed`, `channel_subscribed`, `face_analyzed`). Temizlenmeli;
      yerine bildirim ve abonelik olayları eklenmeli
- [ ] iOS derlemesi (macOS gerektirir) + TestFlight
- [ ] Android imzalama anahtarı üret, Play Console iç test kanalı
      (adımlar: `docs/store-launch.md` §1-2)
- [ ] Yük testi: rapor uçları LLM'e bağlı

## 9. Monetizasyon

- [x] Freemium abonelik, **yalnızca aylık** (RevenueCat)
- [x] Satın alma ekranında: plan adı, fiyat, deneme koşulu, otomatik yenileme
      ve iptal bilgisi, Gizlilik ve Şartlar bağlantıları, içgörü ibaresi
- [x] Paywall ilk değerden sonra açılıyor; abone olmayan kullanıcı için
      kilitli uçlara istek atılmıyor
- [x] RevenueCat kimliği Firebase oturumuna bağlı; TRANSFER olayı işleniyor
- [ ] **Gerçek mağaza ürünleri ve 3 gün deneme** — App Store Connect / Play
      Console tarafı, uygulama sahibinin işi
- [ ] `test_` önekli RevenueCat anahtarları gerçek anahtarlarla değiştirildi

## 10. Mağaza inceleme

- [ ] Test hesabı hazır (onboarding tamam + Rytho+ yetkisi)
- [ ] İnceleme notu yapıştırıldı (`docs/store-review-notes.md` §3)
- [ ] Ekran görüntülerinde gerçek harita/gökyüzü görünüyor — 4.3 savunmasının
      görsel karşılığı
- [ ] Yaş derecelendirmesi: App Store 12+, Play Teen
- [ ] Mağaza açıklamasında sağlık iddiası veya kesin kehanet dili yok

## 11. Henüz yapılmamış ürün işleri

- [ ] Dışa paylaşım kartı (günlük yorumun görsel hâli) — Faz 5 artığı
- [ ] Davet bağlantısı deep-link'i (Firebase Dynamic Links kapandı; yaklaşım
      seçilmedi)
- [ ] Rehber eşleştirme — kendi turunda, varsayılan kapalı (bkz. plan)

## 12. Davet baglantisi (App Links / Universal Links)

- [x] Firebase Hosting yayinda: `https://rhytoai.web.app`
- [x] `/.well-known/assetlinks.json` (Android dogrulama) — 200, JSON tipi
- [x] `/i/{kullanici}` karsilama sayfasi (uygulama kurulu degilse magazaya)
- [x] Manifest intent-filter + `android:autoVerify="true"`
- [x] Uygulama baglantiyi yakaliyor, kullanici adi arkadas ekleme kutusuna
      doluyor; gecersiz ad reddediliyor
- [ ] **Release imza parmak izi eklenmeli.** `web/.well-known/assetlinks.json`
      su an DEBUG anahtarinin SHA-256'sini tasiyor. Yayin anahtari
      uretildikten sonra onun parmak izi eklenmeli (ikisi birden durabilir),
      yoksa magazadan inen uygulamada baglanti dogrulanmaz.
      `keytool -list -v -keystore <yol> -alias <alias>`
- [ ] **iOS Team ID eklenmeli.** `web/.well-known/apple-app-site-association`
      icindeki `TEAMID.ai.rytho` gercek Team ID ile degistirilmeli
      (Apple Developer hesabi gerekiyor).
- [ ] Kendi alan adi alinirsa: `core/deep_links.dart` icindeki `kInviteHost`,
      `AndroidManifest.xml` icindeki `android:host` ve Firebase Hosting
      ozel alan adi ayari birlikte guncellenir.
