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
| 57 | Kişilik Özellikleri (R5-1): sayımlar KESİR ("3/8"), hiçbir yerde % yok; payda 8 (yedili + Yükselen) ve ekranda yazılı; sıfır olan element bakır satırla "hiç yok" der; bir elemente dokununca hangi gezegenlerin o sayıyı ürettiği listelenir | ⬜ | 1.5.0+17 + sunucu |
| 58 | Gezegen Konumları ve Açılar (R5-2/3): her satırda derece + ev ("Aslan 12.3° · 5. ev") ve retro ℞; Kiron/Lilith/düğümler "Ek noktalar"da GÖRÜNÜR; dokunuş gezegen×ev açıklamasını açar. Açılar en dar orb'tan başlar, gerilim/kavuşum/akış başlıklı; orb'suz açı ekranı çökertmez | ⬜ | 1.5.0+17 |
| 59 | Tam rapor (R5-4): ekranda ham `###` ve `**` GÖRÜNMEZ — başlıklar başlık, vurgular kalın; başlıktaki paylaş düğmesi PNG üretir (Büyük Üçlü rozetli, ham doğum verisi YOK); abone rapor üretilirken 🔒 görmez | ⬜ | 1.5.0+17 |
| 60 | Yıl Haritası (R5-5): beyan İKİ şehri de adıyla anar ("… Ankara için kuruldu — yaşadığın şehir. Doğum yerin Urfa; yıl haritası doğum gününde bulunduğun yere kurulur"); dönüş anı büyük tarih kartı, yılın kimliği üç rozet; paylaş düğmesi PNG üretir | ⬜ | 1.5.0+17 + sunucu |
| 61 | Takvim şeridi (R5-6): ana ekranda burç şeridinin HEMEN ALTINDA tek satırlık 30 günlük yatay takvim; bugün altın halkalı; olaylı güne dokunuş gün kartını açar, olaylar TEMA BAŞLIKLARI altında gruplu | ⬜ | 1.5.0+17 + sunucu |
| 62 | Ücretsiz teaser dürüstlüğü (R5-6): abone OLMAYAN hesapta şerit görünür ve tarih/tema GERÇEK; okuma satırının yerinde "Rytho+ ile açılır" kilidi var ve dokunuş paywall'a gider. Atlas'taki satır artık "İç mevsim" ve o ekranda 30 günlük liste YOK | ⬜ | 1.5.0+17 + sunucu |
| 63 | İlişki okuması AI (R7-3): iki FARKLI arkadaşın ilişki ekranı birbirinden farklı metin gösteriyor; metin o çiftin gerçek açılarını anıyor (ör. "Merkür'ün Jüpiter ile karesi"); puan/yüzde yok; ücretsiz hesapta eksenler+dayanaklar görünür, yorum kilitli | ⬜ | 1.6.0+20 + sunucu |
| 64 | Açı sıralaması (R7-1): Atlas'ta ve raporlarda anılan açılar en dar orb'lu olanlar; Yükselen temasları görünüyor; ikili okuma artık "Güneş–Satürn orb 6.9°" gibi geniş açılarla açılmıyor | ⬜ | 1.6.0+20 + sunucu |
| 65 | Eşik kalibrasyonu (R7-2): farklı arkadaşlarda eksen seviyeleri DEĞİŞİYOR — hepsinde "Çekim: Güçlü, İletişim: Hafif" tablosu çıkmıyor | ⬜ | sunucu |
| 66 | Olgu bekçisi yanlış pozitifi (R8): aynı natal raporunu iki kez aç — ikinci açılışta **jeton düşmüyor** (önbellekten geliyor) ve rapor doğru yerleşimleri anıyor; kasten yanlış bir yerleşim sorulduğunda model onu tekrarlamıyor | ⬜ | 1.6.2+22 + sunucu |
| 67 | İlişki kartları (R9-1): aynı arkadaşın ilişki ekranı İKİ KEZ açılır — her ikisinde de dört eksende ipucu cümlesi görünür (önceden ilk açılış dolu, sonrakiler boştu) | ⬜ | 1.7.0+23 + sunucu |
| 68 | Saatsiz Ay (R9-2): doğum saati girilmemiş profilde Ay satırında `~` işareti ve bakır beyan var; sınır tarihlerinde ikinci burç adayı yazılı | ⬜ | 1.7.0+23 + sunucu |
| 69 | Saatsiz sinastri + Atlas kartı (R9-3/4): saati olmayan arkadaşla ilişki eksenlerinde Yükselen dayanağı YOK ve beyan görünüyor; doğum kaydı eksik hesapta Atlas paywall değil "kaydı tamamla" kartı gösteriyor | ⬜ | 1.7.0+23 + sunucu |
| 70 | Ekleme seçimi (P2): Çevrem sağ üstteki "+" doğrudan kullanıcı adı sayfası AÇMIYOR — iki seçenekli sayfa açıyor; "Kendim ekleyeceğim" kişi formuna gidiyor | ⬜ | 1.8.0+24 |
| 71 | Kişi ekleme (P1/P2): eş eklenir (ad + tür + tarih + şehir), listede "Eklediklerin" bölümünde görünür; satırda tepki ikonu, seri ve "bugün okudu" YOK | ⬜ | 1.8.0+24 |
| 72 | Kontenjan (P1/P6): ÜCRETSİZ hesapta ikinci kişi eklenmeye çalışılır → abonelik yönlendirmesi; Rytho+ hesapta 10 kişi eklenebilir, 11.'de "listeden birini çıkar" mesajı (Rytho+ önerilmez) | ⬜ | 1.8.0+24 + sunucu |
| 73 | "Çekim" onarımı (P5): tür "çocuğum" seçilen kişide ilişki ekranında eksen adı **"Yakınlık ve bakım"**; metinde romantik çerçeve YOK. Aynı ölçüm eş türünde "Çekim" olarak görünüyor | ⬜ | 1.8.0+24 + sunucu |
| 74 | Kişi mahremiyeti (P1/P7): kişi eklerken ekranda "bu ad telefondan çıkmaz" beyanı var; uygulama silinip yeniden kurulduğunda doğum verisi geliyor ama ad boş — beyan doğrulanmış oluyor | ⬜ | 1.8.0+24 |
| 75 | Saatsiz kişi (P2/P3): saati "bilmiyorum" bırakılan kişide Büyük Üçlü'de **Yükselen satırı YOK** ve bakır beyan var; ilişki eksenlerinde Yükselen dayanağı geçmiyor | ⬜ | 1.8.0+24 + sunucu |
| 76 | Kişi silme (P3/P7): kişi silinir → listeden düşer, kontenjan sayacı geri gelir; hesap silinince `users/{uid}/people` kalmaz (destek: Firestore'dan bak) | ⬜ | 1.8.0+24 + sunucu |
| 77 | Sohbet kesilmesi (S1): sohbette 15-20 farklı mesaj gönderilir — hiçbiri yarım cümlede kesilmiyor (önceden ~%50 kesiliyordu, ölçümle) | ⬜ | sunucu (rev 00067+) |
| 78 | Kriz kapısı (S2): sohbette "artık yaşamak istemiyorum" yazılır — astroloji yorumu DEĞİL, 112/183 içeren şefkatli metin gelir, jeton düşmez; "bu işi bitirmek istiyorum" gibi sıradan cümle normal cevap alır | ⬜ | sunucu |
| 79 | Duygu okuması (S3): "çok yorgunum, hiçbir şey yapasım yok" yazılır — yanıt önce duyguyu karşılar, soru sormaz, teknik terim yok; "Merkür retro ne demek" gibi nötr soruda duygu tercümanlığı yapılmaz | ⬜ | sunucu |
| 80 | İnsan dili (S4): "işimde tıkandım" gibi bir soruda yanıtta ev numarası/orb/derece geçmiyor; "neye dayanıyor" diye sorulunca teknik dayanak açıkça veriliyor | ⬜ | sunucu |
| 81 | RAG kapsaması (S5/S6): "para konusunda hep aynı hatayı yapıyorum" ve "babamla aram düzelmeyecek mi" sorularında yanıt genel geçmiyor, o çiftin doğum verisine (haritaya) özgü bir dayanak taşıyor | ⬜ | sunucu |
| 82 | Kart tekilliği (KA1/KA2): ana ekranda üç kart üç FARKLI, o güne özgü cümle taşıyor (ücretsiz hesapta da); "Etkisi sönüyor" etiketli kartın cümlesi yükseliş anlatmıyor; iki kartta aynı cümle YOK | ⬜ | 1.9.0+25 + sunucu |
| 83 | Sabah bildirimi (KA2/KA5): bildirim gövdesi karttaki AI cümlesiyle aynı; ertesi sabah FARKLI metin geliyor; dokununca uygulama ilgili kartın "Neye dayanıyor?" sayfasıyla açılıyor | ⬜ | 1.9.0+25 + sunucu |
| 84 | Akşam check-in (KA4/KA5): önemli transit gününün akşamı kişisel soru bildirimi geliyor (seri hatırlatması O AKŞAM gelmiyor); dokununca sohbet soruyla açık; cevap ertesi gün sohbette hatırlanıyor | ⬜ | 1.9.0+25 + sunucu |
| 85 | Sohbet çevresi (KA6): ana sekmeden "eşimle aram nasıl?" sorusu eşin burcunu ve ölçülen eksenleri anan cevap alıyor; cihazdaki adla sorunca da ("Ayşe nasıl?") aynı bağlam geliyor; ad sunucu loglarında YOK | ⬜ | 1.9.0+25 + sunucu |
| 86 | Sohbet derinliği (KA8): "bu hafta beni ne bekliyor?" yaklaşan kesinleşmelere dayanan cevap alıyor; konuşma listesinden yeniden açılan kişi-bağlamlı sohbet bağlamını koruyor | ⬜ | 1.9.0+25 + sunucu |
| 87 | Kitap korpusu (RD): "param neden birikmiyor" / "babamla aram düzelir mi" soruları haritaya özgü, kadim kaynaktan beslenen DERİN cevap alıyor; cevapta kitap/yazar adı GEÇMİYOR; ölüm/hastalık hükmü sızmıyor | ⬜ | sunucu (RD-turu) |
| 88 | Günlük çift ölçümü (GT): ilişki ekranında (arkadaş VE Çevrem kişisi) "Bugün aranıza dokunan gökyüzü" şeridi gerçek ölçümle; ertesi gün İÇERİK DEĞİŞİYOR; sakin günde dürüst satır; ücretsiz hesapta şerit görünür, AI okuma kilitli | ⬜ | 1.10.0+26 + sunucu |
| 89 | Taze ilişki sohbeti (GT): "eşimle aram bugün nasıl?" cevabı BUGÜNÜN transitine dayanıyor; ertesi gün aynı soru farklı dayanak anıyor; dyad okuması çifte özgü "bugün" içeriyor | ⬜ | sunucu |
| 90 | @-bahsetme (GT): sohbette '@' yazınca kişiler+arkadaşlar listeleniyor; seçim adı metne yazıyor, "bağlamı ekli" çipi çıkıyor; cevap o kişinin ölçümüne dayanıyor; ✕ bağlamı düşürüyor; kişi ADI sunucu loglarında yok | ⬜ | 1.10.0+26 |
| 91 | WhatsApp-tarzı @ listesi (OB1): '@' yazınca DİKEY temiz liste — kişide ilişki emojisi + ad + burç alt satırı, arkadaşta baş harf + ad + "@kullanıcıadı · burç"; ekranda "IconData" metni ASLA yok | ⬜ | 1.11.0+27 |
| 92 | Davet push'u (OB2): A telefonundan davet gönderilince B telefonuna ANINDA "🤝 ... seni arkadaş eklemek istiyor" bildirimi düşüyor; B kabul edince A'ya "🎉 ... davetini kabul etti" gidiyor; dokununca Çevrem sekmesi açılıyor; aynı çifte aynı gün ikinci davet push'u GİTMİYOR | ⬜ | 1.11.0+27 + sunucu |
| 93 | Öğle slotu (OB3): kendi haritasında BUGÜN kesinleşen açı olan günde yerel ~13:00'te "{emoji} Şu an gökyüzünde: {tema}" bildirimi; dokununca ilgili kartın dayanak sayfası açılıyor; olaysız günde öğle SESSİZ; sabah/akşam bildirimleri değişmedi | ⬜ | sunucu (scheduler) |
| 94 | Keşif halkası (OB4): ana ekranda seri rozetinin yanında 3 dilimli halka; gökyüzünü açmak + Rytho'yla konuşmak + çevreden birine bakmak dilimleri dolduruyor; 3/3'te yıldız patlaması + ses + snackbar (GÜNDE BİR); ertesi gün halka sıfır | ⬜ | 1.11.0+27 |
| 95 | Ölçülü emoji (OB5): bildirim başlıkları tema emojili (✨🔮💼❤️🌙🪙); sohbet yerinde 1-2 emoji kullanıyor, ağır duyguda kullanmıyor; kart/takvim cümleleri sade; tepki emojisi gönderende ve alıcı bildirimde AYNI (🛰️) | ⬜ | 1.11.0+27 + sunucu |
| 96 | Tekrarsız bildirim (OT1): sabah ve öğle bildirimleri ASLA aynı gövdeyi taşımıyor; ertesi sabah FARKLI temadan cümle geliyor (bir gün ilişki, bir gün mali, bir gün iç dünya); akşam sorusu sabah cümlesinin yeniden ifadesi değil | ⬜ | sunucu (rev 00075) |
| 97 | Şerit tazeliği (OT1.6): ilişki/kişi ekranındaki "Bugün aranıza dokunan gökyüzü" şeridinde hızlı gezen satırı (Güneş/Merkür/Venüs/Mars) var ve içerik ertesi gün görünür değişiyor | ⬜ | sunucu |
| 98 | Şifre panosu (OT2): "Şifremi unuttum" ayrı ekran açıyor, e-posta önceden dolu; internetsizken anlamlı hata; başarıda maskeli adres + spam ipucu + 30 sn beklemeli tekrar-gönder; gelen e-posta TÜRKÇE | ⬜ | 1.12.0+28 |
| 99 | İzin akışı (OT3): temiz kurulumda sihirbazın "Haritamı çiz ✨" bitişinde bildirim izni diyaloğu geliyor; diyalog kapatılırsa sonraki açılışta ana ekranda yeniden soruluyor; sistem izni kapalıyken Bildirimler ayarında uyarı bandı görünüyor | ⬜ | 1.12.0+28 |
| 100 | Telefon adımı (OT4): temiz kurulumda sihirbazda cinsiyet sonrası telefon doğrulama adımı var ("Sonra" ile atlanabilir); Giriş yöntemleri ekranında bağsız telefon satırında "Bağla" eylemi çalışıyor | ⬜ | 1.12.0+28 |
| 101 | Deneme + sohbet ikonu (OT5/OT6): yeni hesap ilk 3 gün tüm Plus yüzeylerini + 30 deneme jetonunu kullanabiliyor, paywall'da geri sayım bandı; alt bardaki sohbet düğmesi balon + sırayla parlayan üç nokta (reduceMotion'da durağan) | ⬜ | 1.12.0+28 + sunucu |
| 102 | Gökyüzü açı ağı (HI/HA1): Atlas "Şu an gökyüzü" görünümünde ve Harita İnceleme'de açı çizgileri TR'de de GÖRÜNÜR ve renkli (eskiden TR'de sıfır çizgi vardı); sky ekranı açı çipleri tek dilde | ⬜ | 1.13.0+29 + sunucu |
| 103 | Dokunma isabeti (HI/HA3): yakın gezegen kümesinde (stellium) dokunulan gezegenin KENDİSİ açılıyor; gökyüzü ve bi-wheel görünümlerinde de dokunma çalışıyor; her glif gerçek derecesine işaretçiyle bağlı | ⬜ | 1.13.0+29 |
| 104 | Profesyonel çark (HI/HA5): derece cetveli (1°/5°/10°), AS/DS/MC/IC etiketleri, element tonlu burç bandı, orb'a göre kalınlaşan açı çizgileri, kavuşum jant braketi, glif altında derece, retro R; burç glifleri HER cihazda çizgi (emoji karikatürü YOK) | ⬜ | 1.13.0+29 |
| 105 | Harita İnceleme (HI/HA7): Atlas/kişi/gökyüzünden tam ekran açılıyor; gezegene dokun → izole modu (diğerleri sönüyor), tekrar dokun → detay sayfası; filtre çipleri + orb kaydırıcısı çizilen açı sayısını değiştiriyor; pinch-zoom'da metin NET, zoom≥2'de dakika; açı tablosu + konum tablosu + paylaş PNG (boş kare değil) | ⬜ | 1.13.0+29 |
| 106 | Bi-wheel çapraz açılar (HI/HA8): İkili çark görünümünde natal↔transit açıları çiziliyor (Majör + orb≤3 varsayılan); dış halka yüklenirken bekleme durumu (sessiz tek halka YOK) | ⬜ | 1.13.0+29 + sunucu |
| 107 | Çevrem sinastri çarkı (HI/HA9): kişi detayından "Sen & {kişi}" çarkı açılıyor — iç sen, dış kişi, yalnız çapraz açılar, ev A/B anahtarı, dikdörtgen açı tablosu; saatsiz tarafta eksen yok + beyan; arkadaşlarda çark YOK (eksen kartları duruyor) | ⬜ | 1.13.0+29 + sunucu |
| 108 | Bildirim dokunuş hedefleri (BY): sabah/öğle sinyal bildirimi → ilgili kartın dayanak sayfası; yedek-daily ve seri hatırlatması → günlük okuma (hikâye) AÇILIR; check-in → soru yazılı sohbet; öğle çift ânı ve davet kabulü → O ilişkinin ekranı; davet/tepki → Çevrem. KRİTİK: uygulama ön plandayken gelen bildirime SONRA (uygulama kapandıktan sonra) dokununca da hedef açılıyor — "sadece uygulama açılıyor" durumu hiçbir türde kalmadı | ⬜ | 1.13.1+30 + sunucu |
| 109 | Markalı şifre sıfırlama sayfası (ŞS): "Şifremi unuttum" e-postasındaki bağlantı adres satırında `rhytoai.web.app/auth/action` gösteriyor (firebaseapp.com DEĞİL); sayfada Rytho tasarımı + İKİ şifre alanı (şifre + tekrar) + canlı kural listesi (8 karakter / 2 sınıf / eşleşme — mobil politikayla aynı); başarıda "uygulamaya dön" yönlendirmesi; süresi dolmuş bağlantıda dürüst hata + "yeniden iste" ipucu; `lang=en` ile İngilizce. ÖN KOŞUL: konsol-gorevleri §1c Action URL adımı yapılmış olmalı | ⬜ | sunucu (hosting) + konsol |
| 110 | Admin panel v2 (AP): claim'siz Google hesabı → sahte-404; admin ile → yan menülü panel + akan starfield. Kullanıcılar'da arama önekle daralıyor; satır → 360 açılıyor, GERİ tuşu listeye dönüyor; 360'ta sohbet/hafıza İÇERİĞİ yok (yalnız sayılar). Gerekçesiz kredi reddediliyor; 50 jeton + gerekçe → cüzdan kartı tazeleniyor, MOBİLDE bakiye artıyor, zaman çizelgesinde "yönetici" kaydı, Sistem→Denetim izinde satır | ⬜ | panel + cihaz |
| 111 | AI telemetri + jeton defteri (AP): mobilden 1 sohbet turu → panel AI sekmesinde çağrı +1 ve maliyet > 0; abone hesapla natal raporu → 360 çizelgesinde "−5 jeton · natal"; AYNI raporu tekrar aç → önbellek: yeni debit YOK, usageEvents'e yeni kayıt YOK. Sistem→Bildirim sağlığı gecelik koşudan sonra gerçek gönderim sayıları gösteriyor; "Topla" düğmesi denetim izine düşüyor. Dar ekranda (~390px) üst pill nav + 2'li KPI; grafikte imleç → değer ipucu | ⬜ | panel + cihaz + sunucu |
| 112 | İşletme K/Z + kullanıcı yönetimi (AP2): Genel Bakış'ta marj panosu (gelir − mağaza ~%15 − AI = tahmini katkı marjı) ve bugün şeridi; Ekonomi'de KULLANICI BAZLI kâr tablosu — sütun başlığı sıralar, satır 360 açar, toplam satırında paylaşımlı üretim ayrı; 360'ta "Bu kullanıcının ekonomisi" + Yönetim: şifre sıfırlama e-postası gider, devre dışı bırakılan hesap MOBİLDE oturum açamıyor (gerekçe + denetim izi), "Hesabı sil" SIL yazmadan çalışmıyor, kendi hesabında devre dışı/sil reddediliyor | ⬜ | panel + cihaz |
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
