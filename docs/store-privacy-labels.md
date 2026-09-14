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
| **Sohbet mesajları (konu arşivi)** | `users/{uid}/conversations/{id}/messages` — sunucu yazar; 30 gün kullanılmayan konu otomatik silinir; yanıt üretimi için Gemini'ye gider | Konuşmayı sürdürme + yanıt üretimi | Evet | Hayır |
| **Kullanıcı hafızası (damıtılmış olgular)** | `users/{uid}/private/memory` | Kişiselleştirme | Evet | Hayır |
| Abonelik durumu | `users/{uid}/private/subscription` — RevenueCat webhook'u | Yetkilendirme | Evet | Hayır |
| Token cüzdanı | `users/{uid}/private/wallet` — yalnızca sunucu yazar | Kullanım hakkı muhasebesi | Evet | Hayır |
| **Telefon numarası (isteğe bağlı)** | Firebase Auth (numara); `phoneHashes/{sha256}` + `users/{uid}/private/phone` (yalnızca özet) | Numara-hesap eşleşmesi; açılırsa rehber eşleşmesi | Evet | Hayır |
| **Rehber (isteğe bağlı, varsayılan KAPALI)** | SAKLANMAZ — numaralar cihazda SHA-256'lanır, özet listesi eşleştirme sonrası atılır; ad/soyad hiç okunmaz | Karşılıklı arkadaş önerisi | Hayır (geçici işleme) | Hayır |
| **Eklenen kişilerin doğum verisi (isteğe bağlı)** | `users/{uid}/people/{id}` — yalnızca sunucu yazar, yalnızca sahibi okur | Kullanıcının yakınlarının haritası ve ilişki ölçümü | Evet (ekleyene bağlı) | Hayır |
| **Eklenen kişilerin ADI** | **SAKLANMAZ** — etiket yalnızca cihazda (`SharedPreferences`); sunucuda yalnız ilişki türü (`partner`/`child`/…) durur | Arayüzde tanıma | — | Hayır |
| Cihaz tanımlayıcısı (rastgele, donanım DEĞİL) | `users/{uid}/private/device` | Tek cihaz kilidi (yalnızca aboneler) | Evet | Hayır |
| Bildirim kimliği (FCM token) | `users/{uid}.fcmToken` | Bildirim gönderimi | Evet | Hayır |
| Saat dilimi (IANA adı) | `users/{uid}.timezone` | Bildirimin yerel sabaha denk gelmesi | Evet | Hayır |
| Arayüz dili | `users/{uid}.language` | Bildirim dilinin seçimi | Evet | Hayır |
| **Yüz oranları (türetilmiş sayılar)** | `users/{uid}/private/firasa` — çekimden sonra | Firaset okuması | Evet | Hayır |
| Yüz okuma rızası | `users/{uid}.faceConsent` — yalnızca sunucu yazar | İspat kaydı (GDPR Md.7/1) | Evet | Hayır |
| Çökme kayıtları | Firebase Crashlytics | Kararlılık | Hayır (anonim) | Hayır |
| Kullanım olayları | Firebase Analytics | Ürün ölçümü | Evet | Hayır |
| **Günlük notları (serbest metin, isteğe bağlı)** | `users/{uid}/private/memory.diary` — kullanıcı "Günlüğüm"e yazar; yalnız kendi sohbet/okuma bağlamına girer, tek tek silinebilir | Yorumların yaşantıya bağlanması | Evet | Hayır |
| **AI kullanım telemetrisi (KENDİ sunucumuz — Analytics DEĞİL)** | `usageEvents` — uid + özellik adı + token sayıları + tahmini maliyet + gecikme; her LLM çağrısında (AP-turu) | Maliyet/kalite gözlemi, işletme paneli | Evet | Hayır |
| Jeton hareket defteri | `users/{uid}/private/wallet/ledger` — kredi/harcama/iade kayıtları (AP-turu debit dahil) | Bakiye izlenebilirliği, destek | Evet | Hayır |
| Platform adı ("android"/"ios") | `users/{uid}.platform` — cihaz kaydında sunucu yazar (AP4) | İstatistik kırılımı | Evet | Hayır |

> Sunucu-operasyon koleksiyonları `notifyRuns` (bildirim koşu sayıları)
> ve `adminAudit` (yönetici eylem izi) kullanıcı İÇERİĞİ taşımaz; audit
> kayıtları hedef uid + eylem parametresi tutar (destek/denetim amacı).

### Toplanmayanlar — açıkça

- **Konum.** Hiçbir konum izni istenmiyor. Saat dilimi cihazın bildirdiği
  IANA adıdır (`Europe/Istanbul`), koordinat değildir.
- **Rehber içeriği (ad/soyad, e-posta, notlar).** Rehber eşleşmesi (isteğe
  bağlı, varsayılan KAPALI) yalnızca telefon NUMARALARINI cihazda özetler;
  ad/soyad dahil başka hiçbir alan okunmaz, özet listesi eşleştirme sonrası
  atılır (yukarıdaki tabloya bakın). Ayar kapalıyken rehbere hiç erişilmez.
- **Yüz görüntüsü / fotoğraf.** Yüz okuma canlı kamerayla ya da galeriden
  seçilen fotoğrafla çalışır; iki yolda da görüntü cihazdan çıkmaz, buluta
  yüklenmez. Kamera yolunda fotoğraf hiç çekilmez, kare bellekte işlenip
  atılır; galeri yolunda uygulamaya verilen kopya bellekte işlenir ve işlem
  bitince silinir. Hem landmark tespiti (ML Kit) hem saç çizgisi ölçümü
  (MediaPipe Selfie Multiclass, cihaz üstü TFLite) yerelde çalışır.
  **Görüntü toplanmadığı için "Photos" ya da "Sensitive Info → biometric"
  beyan edilmez.**

  Sunucuya giden şey iki ondalığa yuvarlanmış ORANLARDIR (ör. `0.34`) ve bu
  sayılar kişiyi tanımaya yaramaz — GDPR Md.9 anlamında "benzersiz
  tanımlamaya izin veren" işleme değildir. Yine de ürün bunu **ayrı ve açık
  rıza** ile çalıştırır; temkinli taraf budur.

  Yüz tanıma, kimlik doğrulama veya kişi eşleştirme YAPILMAZ.
- **Ödeme bilgisi.** Satın alma mağaza tarafından yürütülür; kart bilgisi
  uygulamaya hiç ulaşmaz.
- **Takvim, mikrofon.** Hiç erişilmez. Kamera YALNIZCA yüz okuma sırasında
  ve yalnızca canlı önizleme için kullanılır; kayıt yapılmaz. Galeriye
  erişim yalnızca kullanıcı yüz okuma için fotoğraf SEÇTİĞİNDE, sistem
  seçicisi üzerinden olur; galeri taranmaz.
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
| Personal info | Other info (yüz oranları — türetilmiş sayılar) | Evet | Hayır | Hayır | Uygulama işlevi |
| Messages | Other in-app messages (günlük notları — kullanıcı yazar, yalnız kendi bağlamında) | Evet | **Evet** (Google — Gemini, sohbet bağlamı olarak) | Hayır | Uygulama işlevi |
| App activity | Other user-generated content? HAYIR — kullanıcılar-arası içerik yok (tepkiler kapalı küme) | — | — | — | — |
| Device or other IDs | Device or other IDs (rastgele cihaz kimliği + AD_ID izni: firebase_analytics bağımlılığından gelir) | Evet | Hayır | Hayır | Analitik, tek cihaz kilidi |
| Personal info | Phone number | Evet | Hayır | Hayır | Hesap doğrulama; isteğe bağlı rehber eşleşmesi (sunucuda ham numara DEĞİL, SHA-256 özeti) |
| **Photos and videos** | **Photos** | **Evet** | Hayır | Hayır | **Profil fotoğrafı: kullanıcı galeriden seçerse Cloud Storage'a YÜKLENİR** (yüz okumadan farklı — orada görüntü hiç yüklenmez) |
| Messages | Other in-app messages (uygulama içi geri bildirim — kullanıcının yazdığı serbest metin + ekran adı/sürüm/platform) | Evet | Hayır | Hayır | Uygulama işlevi, destek |
| App activity | App interactions (yapay zeka kullanım kaydı: özellik, model, kelime birimi, süre — SORU/CEVAP METNİ YOK) | Evet | Hayır | Hayır | Analitik, maliyet takibi |
| App activity | App interactions (telefon doğrulama denemeleri: aşama, ülke kodu, maskeli numara) | Evet | Hayır | Hayır | Uygulama işlevi, teşhis |

> **Yüz okuma neden "Photos and videos" altında DEĞİL — ama profil
> fotoğrafı ALTINDA:** Play bu kategoriyi uygulamanın fotoğraf/video
> *topladığı* durumlar için istiyor.
>
> *Yüz okuma:* kamerayı yalnızca canlı önizleme için kullanıyor; kare
> çekilmiyor, saklanmıyor, gönderilmiyor. Toplanan şey görüntüden
> TÜRETİLMİŞ sayılar, o yüzden "Personal info → Other info" doğru kategori.
>
> *Profil fotoğrafı AYRI BİR AKIŞTIR ve toplanır.* Kapalı test denetiminde
> (2026-09-14) bulundu: `avatar_editor.dart` galeriden seçilen fotoğrafı
> kırpıp `FirebaseStorage` `avatars/{uid}/avatar.png` yoluna YÜKLÜYOR ve
> URL'yi `users/{uid}.photoUrl` + `publicProfiles`'a yazıyor. Bu, Play'in
> "Photos and videos → Photos" tanımına birebir uyuyor. Formu doldururken
> bu satır İŞARETLENMELİ — "yüz okuma fotoğraf toplamıyor" cümlesi bu
> akışı kapsamaz.
>
> Aynı sebeple Apple tarafında "Sensitive Info → biometric data" da
> işaretlenmiyor: gönderilen sayılar kişiyi tanımaya yaramıyor.
>
> **Değişirse:** görüntü herhangi bir sebeple sunucuya gitmeye başlarsa bu
> beyanın ikisi de yanlış olur ve düzeltilmesi ŞART. Bunu kod tarafında
> `apps/mobile/test/legal_texts_test.dart` bekçiliyor: politika "diske
> yazılmaz" derken kodda fotoğraf çağrısı olmadığını doğruluyor.

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

- KULLANICILAR ARASI içerik paylaşımı: **hayır** — diğer kullanıcılara
  serbest metin gösterilmez (tepkiler 12'lik kapalı küme —
  `core/friends.dart kReactions`). Kullanıcının KENDİNE yazdığı serbest
  metin VARDIR (sohbet + günlük) ve §1'de beyanlıdır; "hiç serbest metin
  yok" cümlesi kurulMAZ.
- Kullanıcılar arası etkileşim: **evet, sınırlı** — yalnızca sabit tepki kümesi (12)
- Konum paylaşımı: **hayır**
- Dijital satın alma: **evet** (abonelik)

### Çocuk verisi duruşu (P-turu)

Kullanıcı "çocuğum" türünde bir kişi ekleyebiliyor. Bu, uygulamayı
**çocuklara yönelik yapmaz** ve Families programına sokmaz:

- Çocuk için hesap açılmaz, oturum yoktur, bildirim gönderilmez, hiçbir
  şekilde uygulamanın kullanıcısı olmaz.
- Veriyi giren ve gören taraf yalnızca ebeveyn/veli olan yetişkin
  kullanıcıdır; kayıt onun hesabının altında ve yalnız ona açıktır.
- Uygulamanın hedef kitlesi 13+/12+ olarak kalır; mağaza formundaki
  "hedef yaş grubu" beyanı DEĞİŞMEZ.
- Toplanan alan yalnızca doğum tarihi/saati/şehri ve yakınlık türüdür;
  **ad sunucuya hiç gitmez** (etiket cihazda kalır).

---

## 6. Değiştirmeden önce

Bu dosya kodun aynası. Aşağıdakilerden biri değişirse beyanı güncelleyin:

- `infra/firestore.rules` — `users/{uid}` alan listesi
- `backend/services/memory_service.py` — `CATEGORIES` + diary
- `apps/mobile/lib/core/notifications.dart` — profile yazılan alanlar
- `backend/main.py` — kayıtlı router listesi
- `backend/services/usage_service.py` — AI telemetri alanları (uid'li!)
- `backend/api/account.py` — diary uçları
- `backend/api/admin.py` + `services/admin_service.py` — adminAudit ve
  panelin gördüğü kullanıcı alanları
- `backend/core/wallet.py` — ledger türleri
- `apps/mobile/lib/features/face/` — yüz okuma; görüntünün cihazdan
  çıkmadığının kaynağı. `face_capture_screen.dart` fotoğraf ÇEKMİYOR;
  `face_segmentation.dart` modeli cihazda çalıştırıyor
- `apps/mobile/lib/features/profile/legal_texts.dart` — gizlilik politikası

**Yayın öncesi bir hukukçuya baktırın.** Buradaki tablo mühendislik
envanteridir, hukuki görüş değildir.
