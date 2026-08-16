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
| 31 | Rehber kartları: ayar kapalı → "aç" kartı; telefon doğrusuz → "doğrula" kartı; boş → bilgi metni; iki taraf hazırsa eşleşme listesi | ⬜ | 1.0.0+6 |
| 32 | Dürtme: aynı ekranda art arda 2-3 dürtme (geri git-gel gerekmeden) | ⬜ | 1.0.0+6 |
| 33 | Zorunlu güncelleme: RYTHO_MIN_BUILD=999 → kapı ekranı + Play düğmesi; 0 → normal açılış (Claude sunucudan açar/kapar) | ⬜ | 1.0.0+6 |
| 34 | Giriş yöntemleri: Google hesabına şifre ata → çık → e-posta+şifreyle gir; e-posta hesabına Google bağla | ⬜ | 1.0.0+6 |
| 35 | Genel burç yorumunda mizaç/safravi YOK; arkadaş ekle→kabul et akışı ve kullanıcı adıyla arama hâlâ çalışıyor (kural sıkılaştırması regresyonu) | ⬜ | sunucu (rev 00050) |
| 36 | Rehber ekranı: Arkadaşlar'da tek kompakt "Rehberinden arkadaş bul" satırı → tam ekran; aktif kişiler üstte / pasifler altta alfabetik; arama süzer; pasifte "Davet et" → paylaş menüsü (WhatsApp/SMS/mail) davet linkiyle; zaten-arkadaş "Arkadaşın" | ⬜ | 1.0.0+8 |
| 37 | Rehberde arkadaş sınıflandırması (J): telefonu doğrulu arkadaş (ayarı kapalı olsa da) "Uygulamada → Arkadaşın" görünür, davet çıkmaz; doğrusuz arkadaş "Rytho'da görünmüyor" bölümünde dipnotla | ⬜ | 1.0.0+8 + sunucu |
| 38 | İlk abonelikte bakiye ANINDA 300 görünür (K2); paywall'da "Sınırsız sohbet" YOK, "Ayda 300 jeton" var (K3) | ⬜ | 1.0.0+9 |
| 39 | Jeton zorlaması (K5): bakiye 0'a düşünce ücretli iş 402 → jeton mağazası açılır; allowance önce, purchased sonra harcanır | ⬜ | sunucu |
| 40 | Sinyaller (R2-S): ana ekranda en fazla 3 sinyal kartı (tema + başlık cümlesi + varsa abone yorumu); karta dokununca "Neden?" alt-sayfası ölçülmüş dayanağı gösterir (gezen, natal nokta+burç+ev, açı, orb, kesinleşme); alt-sayfadaki "Rytho'ya sor" sohbeti ön-dolu soruyla açar; seri rozeti artık "Bugün senin için" başlığında; sabah bildirimi 1 numaralı sinyal cümlesini taşır | ⬜ | 1.1.0+10 + sunucu |
| 42 | İlişki eksenleri (R2-L1): arkadaş detayında "İlişkiyi incele" → dört eksen (İletişim/Duygusal dil/Çekim/Ortak zemin), her birinde seviye+ton çipi ve gündelik dil cümlesi; **sayısal uyum puanı YOK**; "Bu eksenin dayanağı" açılınca gerçek açılar+orb görünür; "Rytho'ya sor" sohbeti eksen bağlamıyla açar; arkadaşın doğum kaydı yoksa dürüst mesaj | ⬜ | 1.2.0+13 + sunucu |
| 43 | Ücretsiz temel harita (R2-F1): abone OLMAYAN hesapta Atlas'ta çark + Kişilik + Gezegenler + Açılar açık; yalnız "Tam rapor" satırı 🔒 ve dokununca paywall; altta "çarkın ücretsiz" notu | ⬜ | 1.2.0+13 |
| 44 | Atlas dili (R2-I1): üç bölüm — Bana dair / Zaman / Diğer sistemler; "Yıl Haritası" yerine "Doğum gününden doğum gününe" (alt satırda teknik ad), "İç Takvim" yerine "Önündeki günler"; karo ızgarası yerine okunur satırlar | ⬜ | 1.2.0+13 |
| 45 | Kredi dili (R2-F2): "jeton/token" ibaresi arayüzde YOK — "AI kredisi/kredi"; sohbette bakiye çipi her mesajda animasyonla düşmüyor, bakiye 30'un altına inince bakır renge dönüyor; bedeller ve 402→mağaza akışı aynı | ⬜ | 1.2.0+13 |
| 46 | 90 günlük zaman çizgisi (R2-Z1): İç Takvim "Önündeki 90 gün" başlıklı; kesinleşme satırlarında tema ikonu; satıra dokununca "Bu tarih neden önemli?" sayfası gündelik cümle + teknik dayanak gösterir; retro istasyon satırları bilgi satırı olarak kalır | ⬜ | 1.3.0+14 + sunucu |
| 47 | Günlüğüm (R2-G1): Profil → Günlüğüm; tek satır giriş + isteğe bağlı tema çipi; kayıt listede tarihle görünür; tek tek silinebilir; sohbette "son ayda ne oldu?" sorusu günlük kayıtlarını hesaba katar | ⬜ | 1.3.0+14 + sunucu |
| 48 | Dürüstlük (R2-D1): sohbette "benim Nakshatra'm ne?" sorusuna Rytho hesaplamadığını dürüstçe söyler, uydurma Vedik yorum ÜRETMEZ; DST geçiş saatinde doğum kaydı (ör. 28 Mart 2021 01:30 Londra) haritayı düşürmez | ⬜ | sunucu |
| 49 | İçgörü teklemesi yok (R3-2): Gökyüzü'nde genel burç kartı YOK — genel yorum yalnız hikâye halkasında; "Bugünün İçgörüsü" kişiye özel okuma (abone değilse kilitli kart) | ⬜ | 1.4.0+15 |
| 50 | Üç görünümlü çark (R3-3): Atlas'ta Haritam / Şu an gökyüzü / İkili çark segmenti; "Şu an" evsiz + dürüstlük notu; ikili çarkta dış halkada lila transit glifleri; "Şu An Gökyüzünde" özeti çarkın altında | ⬜ | 1.4.0+15 |
| 51 | Slim arkadaşlar (R3-4): SEN kartı tek satır (@ad + seri + düzenle/davet/Günlüğüm ikonları, seri anahtarı yalnız Gizlilik'te); arkadaş satırı ince (avatar+ad+durum+⚡+🪐); ⚡ → kart açılmadan tepki sayfası, seçim anında gider + karşı cihazda bildirim; 12 tepki (yeni: 🤗🍀☕🫶) | ⬜ | 1.4.0+15 + rules + sunucu |
| 52 | Profil grupları (R3-5): Doğum ve kimlik / Hesap / Tercihler / Rytho+ başlıkları; hesap silme Profil dibinde DEĞİL, Hesap ekranının içinde; Günlüğüm satırı profilden kalktı (SEN kartında) | ⬜ | 1.4.0+15 |
| 53 | "Neye dayanıyor?" tutarlılığı (R3-1): sayfa, KARTTAKİ cümleyle açılır (abone yorumu dahil); teknik cümle "Ölçüm" satırında; takvim günü sayfası aynı düzende | ⬜ | 1.4.0+15 |
| 54 | Sinyal sorusu (R4-1): sinyal sayfasından "Rytho'ya sor" → sohbete KARTTAKİ cümle + dayanağı birlikte gider; cevap o cümleyi açar, "başka konu" hissi yok | ⬜ | 1.4.1+16 |
| 55 | İlişki sohbeti (R4-2): eksen kartından ya da arkadaş detayındaki "X hakkında Rytho'ya sor"dan açılan sohbette cevap İKİ KİŞİYE özel — ölçülen eksen/dayanak açı anılır, genel burç cevabı yok; takip sorusunda bağlam korunur; arkadaş olmayan uid ile bağlam sessizce atlanır | ⬜ | 1.4.1+16 + sunucu |
| 56 | Günlük hızlı girişi (R4-3): Gökyüzü akışının sonunda 📓 kartı; tek cümle yaz → kaydet → "Rytho bunu hatırlayacak" onayı + son giriş tarihi güncellenir; sohbette "dün ne yazmıştım?" hatırlanır | ⬜ | 1.4.1+16 |
| 41 | Sinyal dili (R2-S6): kart yüzeyinde gezegen/açı/orb ADI GEÇMEZ — büyük tema başlığı (💼 Kariyer) + gündelik dil cümlesi + sağ üstte zamanlama ("18 Ağustos günü netleşiyor"); teknik satır yalnız "Neye dayanıyor?" sayfasının başında; burç şeridi HER ZAMAN selamlamanın hemen altında (hiçbir bölüm onu aşağı itmez); sabah bildirimi başlığı "Bugün: İlişkiler" | ⬜ | 1.1.1+12 + sunucu |

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

### B5 — "Abonelik alındı ama sürekli Rytho+ istiyor" (hata değil)
- Gözlenen: 3 test hesabında da satın almadan ~30 dk sonra kilitler
  geri geldi.
- Açıklama: lisanslı test aboneliklerinde Google saati hızlandırır —
  aylık plan ~5 dk'da yenilenir, birkaç yenilemeden sonra kendiliğinden
  sona erer. Loglarda tam yaşam döngüsü doğrulandı: INITIAL_PURCHASE →
  RENEWAL'lar → CANCELLATION → EXPIRATION, hepsi DOĞRU uid ile
  (kimlik düzeltmesi sahada kanıtlandı). Üretimde döngü gerçek
  takvimle işler.
- Sonuç: M4 ödeme doğrulaması TAMAMLANDI (senaryo 18-19-24 ✅).
  Özellik testi için seçenek: süresi dolunca yeniden satın alma ya da
  geçici RYTHO_FORCE_PLUS=1 (kapalı test öncesi kaldırılır).

### K1 — Kapsam değişikliği: İching Rytho+ kapısında (2026-08-12)
- Kullanıcı kararı: BaZi gibi İching de tam premium. Günde 1 ücretsiz
  çekim kalktı (geri istenirse reports.py'de tek değişiklik — commit
  91577b1 yorumunda tarif). Atlas'ta 4 kehanet karosu da kilit rozetli.

### B7 — Genel burç yorumunda uydurma mizaç ("ölçülmeyen söylenmez" ihlali)
- Gözlenen: Gökyüzü'ndeki genel burç kartlarında "safravi" gibi mizaç
  hükümleri — kişiye özel veri olmadan.
- Kök neden: RAG tohumu 'temperament' korpustaki burç→mizaç tablosunu
  genel yoruma taşıyordu + prompt "mizacıyla çarpıştır" diye emrediyordu.
  Ayrıca mizaç v1'de hiçbir yerde HESAPLANMIYOR.
- Durum: düzeltildi (4ca85b9, rev 00050) — yeni 'horoscope' tohumu
  (gökyüzü/arketip), prompt'a negatif kısıt, korpus tabloları "unsur
  baskınlığı, yalnız kişisel analizde" çerçevesine alındı, embeddings
  yenilendi, kirli 20 önbellek dokümanı silindi. Bekçi testler eklendi
  (tr+en, sorgu+prompt). İleri iş: elementten gerçek mizaç hesabı.

### B8 — Arkadaşlık durumu tek taraflı uydurulabiliyordu (yetki açığı)
- Kullanıcı şüphesi "başka kişi sorgulanınca veri sızıyor" — tarama
  sonucu: ham doğum verisi/telefon/e-posta HİÇBİR yoldan sızmıyor;
  ama arkadaşlık 'accepted' durumu tek taraflı yazılabiliyordu →
  arkadaş olmayan biri hakkında ikili okuma + onaysız dürtme mümkündü.
- Durum: düzeltildi (4ca85b9) — are_friends ÇİFT taraflı doğrular;
  firestore.rules'ta accepted yalnız gerçek davet kabulüyle yazılır;
  publicProfiles/usernames koleksiyon LİSTELEME kapatıldı (enumeration).
  Kurallar + backend deploy edildi (rev 00050). Cihaz regresyonu: arkadaş
  ekle/kabul + kullanıcı adı arama çalışmalı (senaryo 35).

## 2. tur kapsamı

- RYTHO_TOKENS_ENFORCE=1 → jeton tükenme/yetersiz bakiye UX'i
- Bulgu düzeltmeleri → 1.0.0+4
- Telefon adımı sorunsuzsa varsayılanın kalıcı açılması
  (onboarding_wizard.dart)
