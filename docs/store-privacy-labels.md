# Gizlilik Etiketleri — App Privacy ve Data Safety

Bu tablo **koddan çıkarıldı**, tahminle doldurulmadı. Her satırın yanında
verinin nerede toplandığı yazıyor; beyanı değiştirmeden önce o dosyaya bakın.

> Yanlış beyan, eksik beyandan daha büyük bir sorundur: mağaza beyanı ile
> uygulamanın davranışı ayrışırsa bu, uygulamanın kaldırılma sebebidir.
> Kod değişirse **bu dosya da değişmeli**.

**Toplanan hiçbir veri reklam veya izleme (tracking) amacıyla kullanılmıyor.**
Üçüncü taraf reklam SDK'sı yok, veri satışı yok, veri komisyonculuğu yok.

---

## 1. Toplanan veriler

| Veri | Nerede | Amaç | Kullanıcıya bağlı | Zorunlu |
|---|---|---|---|---|
| E-posta adresi | Firebase Auth (Google ile veya e-posta) | Hesap kimliği | Evet | Evet |
| Ad / görünen ad | `users/{uid}.displayName` | Hesap, arkadaş listesinde görünürlük | Evet | Evet |
| Profil fotoğrafı (URL) | `users/{uid}.photoUrl` — Google hesabından | Arayüz | Evet | Hayır |
| **Doğum tarihi, saati ve şehri** | `users/{uid}` — onboarding | Natal harita, BaZi ve günlük okuma hesabı | Evet | Evet |
| Cinsiyet | `users/{uid}.gender` | BaZi şans sütunu yönü (yöntem gereği) | Evet | Evet |
| Kullanıcı adı | `usernames/{username}` | Arkadaş ekleme | Evet | Hayır |
| Arkadaşlıklar | `users/{uid}/friends` | Arkadaş katmanı | Evet | Hayır |
| Hazır tepkiler | `users/{uid}/nudges` | Arkadaş etkileşimi (kapalı küme, serbest metin yok) | Evet | Hayır |
| Günlük seri | `users/{uid}.streakCount`, `lastSeenDaily` | Alışkanlık takibi | Evet | Hayır |
| **Sohbet mesajları** | Yalnızca istek anında Gemini'ye gider | Yanıt üretimi | Evet | Hayır |
| **Kullanıcı hafızası (damıtılmış olgular)** | `users/{uid}/private/memory` | Kişiselleştirme | Evet | Hayır |
| Abonelik durumu | `users/{uid}/private/subscription` — RevenueCat webhook'u | Yetkilendirme | Evet | Hayır |
| Bildirim kimliği (FCM token) | `users/{uid}.fcmToken` | Bildirim gönderimi | Evet | Hayır |
| Saat dilimi (IANA adı) | `users/{uid}.timezone` | Bildirimin yerel sabaha denk gelmesi | Evet | Hayır |
| Arayüz dili | `users/{uid}.language` | Bildirim dilinin seçimi | Evet | Hayır |
| Çökme kayıtları | Firebase Crashlytics | Kararlılık | Hayır (anonim) | Hayır |
| Kullanım olayları | Firebase Analytics | Ürün ölçümü | Evet | Hayır |

### Toplanmayanlar — açıkça

- **Konum.** Hiçbir konum izni istenmiyor. Saat dilimi cihazın bildirdiği
  IANA adıdır (`Europe/Istanbul`), koordinat değildir.
- **Rehber / kişiler.** İzin istenmiyor, erişilmiyor. Arkadaş ekleme yalnızca
  kullanıcı adı ve davet bağlantısıyla.
- **Biyometrik veri.** Yüz analizi v1 kapsamı dışında; uç kaydı yapılmıyor
  (`backend/main.py` — `face_reading` router'ı bilinçli olarak kayıtlı değil).
  **Her iki konsolda da biyometrik beyanı YAPILMAMALIDIR.**
- **Ödeme bilgisi.** Satın alma mağaza tarafından yürütülür; kart bilgisi
  uygulamaya hiç ulaşmaz.
- **Kişi rehberi, takvim, mikrofon, kamera, fotoğraf galerisi.**
- **Ham sohbet transkripti saklanmaz.** Saklanan şey kapalı bir kategori
  kümesine oturan kısa olgulardır (`backend/services/memory_service.py`,
  `CATEGORIES`). Sağlık/tanı/ilaç bilgisi bilinçli olarak tutulmaz.

---

## 2. Apple — App Privacy (App Store Connect)

Her madde için "Bu veriyi topluyor musunuz?" → aşağıdaki gibi işaretleyin.
**"Used for Tracking" hiçbir maddede işaretlenmez.**

### Data Linked to You

| App Privacy kategorisi | İşaretlenecek türler | Amaç |
|---|---|---|
| Contact Info | Email Address, Name | App Functionality |
| Sensitive Info | *(bkz. not)* | App Functionality |
| User Content | Other User Content — sohbet mesajları ve damıtılmış olgular | App Functionality, Personalization |
| Identifiers | User ID | App Functionality |
| Usage Data | Product Interaction | Analytics |
| Purchases | Purchase History — yalnızca abonelik durumu | App Functionality |
| Other Data | Doğum tarihi/saati/yeri, saat dilimi, dil | App Functionality, Personalization |

> **Sensitive Info notu:** Apple bu kategoriyi ırk, cinsel yönelim, gebelik,
> din, siyasi görüş, biyometrik ve sağlık verisi için tanımlıyor. Uygulama
> bunların hiçbirini toplamıyor. **Cinsiyet** alanı BaZi hesabında yön
> belirlemek için isteniyor; Apple'ın "Sensitive Info" tanımına girmiyor ancak
> beyanda "Other Data" altında açıklanması dürüst olan yoldur.
>
> **Doğum tarihi ayrı bir hassasiyet taşır** (kimlik doğrulama sorularında
> kullanılır). Bu yüzden Firestore'da `users/{uid}` dokümanı yalnızca
> sahibine okunabilir ve arkadaşlar bu dokümanı hiç göremez
> (`infra/firestore.rules`).

### Data Not Linked to You

| Kategori | Tür |
|---|---|
| Diagnostics | Crash Data, Performance Data (Crashlytics) |

---

## 3. Google Play — Data Safety

| Bölüm | Cevap |
|---|---|
| Veri toplanıyor mu? | Evet |
| Veri paylaşılıyor mu (üçüncü taraflara)? | Evet — yalnızca işleyiciler; aşağıya bakın |
| Aktarımda şifreleniyor mu? | Evet (HTTPS/TLS) |
| Kullanıcı silme talep edebilir mi? | **Evet — uygulama içinden** (Profil → Hesabı sil) |

### Toplanan veri türleri

| Play kategorisi | Tür | Toplanıyor | Paylaşılıyor | Zorunlu | Amaç |
|---|---|---|---|---|---|
| Personal info | Name | Evet | Hayır | Evet | Uygulama işlevi |
| Personal info | Email address | Evet | Hayır | Evet | Uygulama işlevi, hesap yönetimi |
| Personal info | User IDs | Evet | Hayır | Evet | Uygulama işlevi |
| Personal info | Other info (doğum verisi, cinsiyet, saat dilimi) | Evet | Hayır | Evet | Uygulama işlevi, kişiselleştirme |
| Messages | Other in-app messages | Evet | **Evet** (Google — Gemini) | Hayır | Uygulama işlevi |
| App activity | App interactions | Evet | Hayır | Hayır | Analitik |
| App info & performance | Crash logs, Diagnostics | Evet | Hayır | Hayır | Analitik |
| Financial info | Purchase history | Evet | Hayır | Hayır | Uygulama işlevi |

> **"Messages" satırındaki paylaşım kutusu neden işaretli:** Sohbet mesajı
> yanıt üretmek için Google'ın Gemini API'sine gönderiliyor. Bu bir işleyici
> ilişkisi; yine de Play, uygulama dışına giden veriyi "paylaşım" sayıyor.
> İşaretlememek eksik beyan olurdu.

### Güvenlik uygulamaları

- [x] Veri aktarımda şifreleniyor
- [x] Kullanıcı verisinin silinmesini talep edebiliyor (uygulama içinden)
- [ ] Bağımsız güvenlik denetiminden geçildi — **hayır**, işaretlemeyin

---

## 4. Alt işleyiciler (her iki konsolda da beyan edilir)

| Sağlayıcı | Hizmet | İşlenen veri |
|---|---|---|
| Google LLC | Firebase Auth, Cloud Firestore, Cloud Run, Cloud Storage, FCM, Crashlytics, Analytics | Hesap, profil, doğum verisi, hafıza, bildirim kimliği |
| Google LLC | Gemini API | Sohbet mesajı, türetilmiş harita konumları, hafıza bağlamı |
| RevenueCat, Inc. | Abonelik yönetimi | Kullanıcı kimliği, abonelik durumu |

Veri **AB ve Türkiye dışına aktarılıyor** (Google Cloud `us-central1`).
Gizlilik politikasında yazılı.

---

## 5. Yaş derecelendirmesi

| Mağaza | Hedef | Gerekçe |
|---|---|---|
| App Store | **12+** | "Infrequent/Mild Horror or Fear Themes" **hayır**; astroloji/fal içeriği için 12+ güvenli taraf. Şiddet, cinsellik, kumar, alkol içeriği yok. |
| Google Play | **Teen / 13+** | Kullanım şartlarındaki 13 yaş sınırıyla tutarlı. Kullanıcılar arası **serbest metin yok** (kapalı tepki kümesi) — bu, sosyal özellik beyanını basitleştirir. |

Her iki formda da:

- Kullanıcı üretimi içerik paylaşımı: **hayır** (serbest metin yok)
- Kullanıcılar arası etkileşim: **evet, sınırlı** — yalnızca sabit tepki kümesi
- Konum paylaşımı: **hayır**
- Dijital satın alma: **evet** (abonelik)

---

## 6. Değiştirmeden önce

Bu dosya kodun aynası. Aşağıdakilerden biri değişirse beyanı güncelleyin:

- `infra/firestore.rules` — `users/{uid}` alan listesi
- `backend/services/memory_service.py` — `CATEGORIES`
- `apps/mobile/lib/core/notifications.dart` — profile yazılan alanlar
- `backend/main.py` — kayıtlı router listesi (özellikle `face_reading`)
- `apps/mobile/lib/features/profile/legal_texts.dart` — gizlilik politikası

**Yayın öncesi bir hukukçuya baktırın.** Buradaki tablo mühendislik
envanteridir, hukuki görüş değildir.
