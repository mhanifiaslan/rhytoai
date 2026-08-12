# İç Test Bulgu Raporu — Rytho AI 1.0.0+3

> Amaç: üretim öncesi iç test turunda bulunan eksik/hataların tek yerde
> izlenmesi. Bu dosya kapalı test bitiminde Play'in "üretim erişimi
> başvurusu" sorularına da kaynaklık edecek (ne test edildi, ne bulundu,
> ne düzeltildi).
>
> Test sürümü: 1.0.0+3 (telefon adımı AÇIK — RYTHO_PHONE_STEP=true).
> Kanal: Play iç test. Jeton harcaması 1. turda kuru çalışma
> (RYTHO_TOKENS_ENFORCE=0); 2. turda açılacak.

## Bulgu formatı

Her bulgu şu kalıpla eklenir (Claude işler, kullanıcı serbest yazar):

```
### B<numara> — <kısa başlık>
- Ekran/akış: <nerede>
- Adımlar: <ne yapıldı>
- Beklenen: <ne olmalıydı>
- Gözlenen: <ne oldu> (+ ekran görüntüsü varsa)
- Önem: kritik / yüksek / orta / düşük
- Durum: açık / düzeltildi (sürüm) / yineleyemedik / kapsam dışı
```

Önem tanımları: **kritik** = akış tamamen tıkanıyor veya para/veri
kaybı; **yüksek** = yanlış bilgi ya da temel özellik bozuk; **orta** =
rahatsız edici ama dolanma yolu var; **düşük** = cila.

---

## Senaryo listesi (Faz 2 — her satır işaretlenecek)

| # | Senaryo | Durum | Not |
|---|---------|-------|-----|
| 1 | Play iç test linkinden kurulum (eski sürüm kaldırıldıktan sonra) | ⬜ | |
| 2 | Google ile giriş (yeni hesap) | ✅ | 2026-08-12: gerçek Play imzası kaydedilince açıldı (B1/B4 kök nedeni) |
| 3 | Sihirbaz: doğum tarihi/saati adımları | ⬜ | |
| 4 | Sihirbaz: şehir arama (listede olan) | ⬜ | |
| 5 | Sihirbaz: şehir arama (listede OLMAYAN — elle kaydet) | ⬜ | |
| 6 | Sihirbaz: telefon doğrulama — sessiz SMS (reCAPTCHA görünmemeli) | ⬜ | |
| 7 | Sihirbaz: telefon adımını atlama | ⬜ | |
| 8 | Sihirbaz: rıza onayı + izinler + final (Büyük Üçlü) | ⬜ | |
| 9 | Doğum haritası raporu açılıyor, içerik tutarlı | ⬜ | |
| 10 | Günlük yorum | ⬜ | |
| 11 | Sohbet (birkaç mesaj; jeton düşümü kuru çalışmada) | ⬜ | |
| 12 | Yıl Haritası (Zaman katmanı) | ⬜ | |
| 13 | İç Takvim | ⬜ | |
| 14 | Ana ekranda jeton hapı görünür, dokununca Abonelik ekranı | ⬜ | |
| 15 | Avatara dokununca Profil sekmesi | ⬜ | |
| 16 | Profil fotoğrafı değiştirme (konumlandır/büyüt) | ⬜ | |
| 17 | Paywall: "3 gün ücretsiz, sonra ₺149,99" ibaresi | ⬜ | |
| 18 | Abonelik satın alma (lisanslı test — ücret çıkmamalı) | ⬜ | |
| 19 | Satın alma sonrası ≤15 sn Rytho+ açık | ⬜ | |
| 20 | Abonelik ekranı plan kartı (Aylık Rytho+, yenilenme tarihi) | ⬜ | |
| 21 | Jeton paketi (küçük) → bakiye +100 | ⬜ | |
| 22 | Jeton mağazasında ₺ fiyatlar | ⬜ | |
| 23 | "Yönet" → Play abonelik sayfası | ⬜ | |
| 24 | Play'den iptal → "Sona erme: {tarih}" görünümü | ⬜ | |
| 25 | Davet linki: rhytoai.web.app/i/... uygulamayı açıyor | ⬜ | |
| 26 | Bildirim izni + günlük bildirim gelişi | ⬜ | |
| 27 | Dil EN'e çevrilince ekranlar (sihirbaz + paywall + abonelik) | ⬜ | |
| 28 | Hesap silme akışı | ⬜ | |
| 29 | Cihaz devralma: B cihazında giriş → "bu cihazda kullan?" sorusu → Taşı → A düşer → A'da yeniden giriş → soru A'da çıkar (döngü yok) | ⬜ | 1.0.0+5 |
| 30 | İching/BaZi: abonesizde kilit kartı + Atlas karo rozetleri; abonede çekim (2/5 jeton) | ⬜ | 1.0.0+5 |

Sunucu tarafı (Claude doğrular): webhook logları, revenueEvents,
users/{uid}/private/subscription, cüzdan dokümanı, Crashlytics.

---

## Bulgular

### B1 — Google giriş hatası kullanıcıya yol göstermiyor
- Ekran/akış: Giriş ekranı, "Google ile devam et"
- Adımlar: Play iç test kurulumunda Google girişi denendi; cihazdaki
  hesabın oturumu bayat olduğu için GMS `[16] Account reauth failed`
  döndürdü (logcat ile doğrulandı; SHA/OAuth yapılandırması temiz).
- Beklenen: Kullanıcıya ne yapacağını söyleyen mesaj ("Google
  hesabınızın yeniden doğrulanması gerekiyor — telefonunuzun
  Ayarlar → Google bölümünden doğrulayıp tekrar deneyin").
- Gözlenen: Genel "bir şeyler ters gitti" mesajı; kullanıcı çıkmaza
  giriyor.
- KÖK NEDEN (KESİN, 2026-08-12): `[16]` üst katman maskesiymiş;
  altında `[8] UNREGISTERED_ON_API_CONSOLE`. Play Console'dan
  kopyalanan imza SHA'ları (klasik/kuantum) mağazadan inen APK'nın
  GERÇEK imzasıyla eşleşmiyordu — iki gün yanlış parmak izleri
  kayıtlıydı. Gerçek imza cihazdaki APK'dan okundu (adb pull +
  apksigner): SHA-1 9E:12:F5:F1...CD:E8:40. Firebase'e eklendi +
  assetlinks güncellendi. Ders: imza SHA'sının tek güvenilir
  kaynağı cihazdaki APK'dır; logcat'te gerçek neden
  `GetTokenResponseHandler` satırında.
- Önem: orta (nadir ama tıkayıcı; mesaj iyileştirmesi ucuz)
- Durum: düzeltildi (kod: 858cc49; 1.0.0+4 ile dağıtılacak) —
  reauth hatasına özel l10n mesajı + bilinmeyen sosyal giriş
  hatalarına Crashlytics kaydı

### B2 — Satın alma doğrulaması: Play izin yayılması bekleniyor
- Ekran/akış: Paywall + jeton mağazası (Feyza'nın cihazı, lisanslı test)
- Gözlenen: Play satın almayı tamamlıyor; RevenueCat makbuzu
  doğrulayamadığı için kayıt/entitlement/webhook oluşmuyor; kilit
  açılmıyor. Kimlik bağlama (Purchases.logIn=uid) ÇALIŞIYOR
  (RC last_seen güncelleniyor).
- Kök neden: servis hesabında "Uygulama bilgilerini görüntüleme"
  izni satın alma DENEMELERİNDEN SONRA verildi; ürün listeleme hemen
  düzeldi (Published), makbuz doğrulama yetkisi Google'ın 36 saate
  kadar sürebilen yayılma penceresinde.
- Durum: açık — yarın "Satın alımları geri yükle" ile yeniden
  denenecek; sunucudan RC subscriber + webhook teyidi yapılacak.

### B3 — Fiyat ₺179,99 görünüyor (KDV)
- Gözlenen: Paywall ₺179,99 gösteriyor; karar ₺149,99 idi.
  Neden: Play, girilen fiyata %20 KDV ekliyor (149,99×1,2).
- Öneri: temel plan fiyatını ₺124,99 yap → alıcı ₺149,99 görür.
- Durum: KAPANDI (2026-08-12) — kullanıcı kararı: fiyatlar OLDUĞU
  GİBİ kalıyor (₺179,99 görünür fiyat); ileride artırılabilir.

### B4 — Cihaz devralma sorusu hiç çıkmıyor, çakışma ekranı döngüde
- Ekran/akış: "Aboneliğin başka bir cihazda" ekranı → yeniden giriş
- Gözlenen: Ekran "girişte devralmak isteyip istemediğin sorulacak"
  diyor ama soru hiç çıkmıyor; giriş → aynı ekran döngüsü.
- Kök neden: `device_claim.dart` — "soruldu" bayrağı dialog
  gösterilmeden yanıyor ve hiçbir yol sıfırlamıyordu; ayrıca abonelik
  durumu yüklenmeden senkron okunup erken çıkılıyordu (soru ilk
  denemede de sorulmuyordu).
- Durum: düzeltildi (91577b1, 1.0.0+5) — bayrak yalnız dialog
  gösterilince yanar, çıkış yolları sıfırlar, abonelik ön-kontrolü
  kaldırıldı (sunucu `claimed:false` zaten döner). Cihaz testi bekliyor.

### K1 — Kapsam değişikliği: İching Rytho+ kapısında (2026-08-12)
- Kullanıcı kararı: BaZi gibi İching de tam premium. Günde 1 ücretsiz
  çekim kalktı (geri istenirse reports.py'de tek değişiklik — commit
  91577b1 yorumunda tarif). Atlas'ta 4 kehanet karosu da kilit rozetli.

## 2. tur kapsamı

- RYTHO_TOKENS_ENFORCE=1 → jeton tükenme/yetersiz bakiye UX'i
- Bulgu düzeltmeleri → 1.0.0+4
- Telefon adımı sorunsuzsa varsayılanın kalıcı açılması
  (onboarding_wizard.dart)
