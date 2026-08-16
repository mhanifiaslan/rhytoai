# Rytho — Nedir, Neyi Nasıl Yapar

> Bu belge **koddan çıkarıldı**, pazarlama metninden değil. Her iddianın
> arkasında çalışan bir hesap var; olmayanlar en sonda "İddia
> edilemeyecekler" başlığında açıkça listelendi.
> Sürüm: 1.0.0+9 · Tarih: 2026-08-13

---

## 1. Tek cümleyle

**Rytho, gerçek gökyüzü hesabı üzerine kurulmuş kişisel bir kendini tanıma
uygulamasıdır:** Swiss Ephemeris ile senin doğum anını hesaplar, dört ayrı
kadim sistemden (Batı astrolojisi, BaZi, İ Ching, firaset) okuma üretir ve
bunları yapay zekâyla senin diline çevirir — **ölçemediğini söylemez.**

Rakiplerden ayrıldığı yer özellik sayısı değil, **dürüstlük mimarisi**:
doğum saatin yoksa Yükselen'i uydurmaz, hesabın nasıl çıktığını gösterir,
ilişkiler için kalıcı "uyum puanı" vermez.

---

## 2. Dört sekme, dört soru

| Sekme | Cevapladığı soru |
|---|---|
| ☾ **Gökyüzü** | "Bugün ne var?" — burç yorumu + canlı gökyüzü + kişisel günlük okuma |
| ⊙ **Atlas** | "Ben kimim?" — doğum haritan, BaZi'n, kehanet araçların |
| ✦ **Sohbet** (ortadaki buton) | "Aklımdakini sorayım" — haritanı bilen AI |
| ⚭ **Arkadaşlar** | "Yakınlarımla ne paylaşırım?" — seri, dürtme, günlük ikili okuma |
| ☺ **Profil** | Doğum kaydı, abonelik, gizlilik, dil, bildirimler |

---

## 3. Gökyüzü — bugünün katmanı

**Ücretsiz olanlar (her zaman açık):**
- **Günlük burç yorumu** — 12 burç için günlük/haftalık/aylık. Hikâye
  okuyucusunda tam ekran, otomatik ilerleme (süre metnin uzunluğundan
  hesaplanır), yatay kaydırmayla burçlar arası geçiş.
- **Paylaşım kartı** — burç, tarih, yorumdan alıntı, ay evresi. Doğum
  verisi karta asla girmez.
- **"Şu an"** — canlı zodyak çarkı, **ay evresi ve gerçek aydınlanma
  oranı** (Swiss Ephemeris `pheno_ut`; lineer yaklaşım kullanılmıyor),
  retro gezegenler, güncel açılar, NASA JPL Horizons'tan gezegen-Dünya
  uzaklıkları.
- **Günlük seri (🔥)** — her gün okumanı açınca büyür; büyüdüğü an kutlama
  (kıvılcım + ses). Sıfırlanma **kutlanmaz** — ceza mekaniği yok.

**Rytho+ ile:**
- **Kişiye özel günlük okuma** — genel burç yorumu her Kova için aynıdır;
  bu, senin natal haritanı bugünün gökyüzüyle çarpıştırır (Ay, Yükselen,
  transitler dahil).

---

## 4. Atlas — haritanın katmanı

### Doğum haritası (Rytho+)
- **14 nokta:** 10 gezegen + Chiron + Lilith + Kuzey/Güney Ay Düğümü.
  Her biri için burç, derece, ev, retro durumu, **deklinasyon** ve hız.
- **12 ev + Yükselen**, dokunulabilir natal çark.
- **Açılar** — yalnız liste değil, **yaklaşıyor mu ayrılıyor mu** bilgisiyle
  (yaklaşan açı güçlenir, ayrılan söner).
- **Deklinasyon açıları** (paralel / kontra-paralel, ±0,5° orb) — tüketici
  uygulamalarında nadiren bulunur.
- Element/nitelik dengesi, **stellium** tespiti.
- **Tam rapor:** 400-500 kelimelik derin AI okuması.

### Zaman katmanı (Rytho+)
- **🌞 Yıl Haritası (Solar Return)** — güneş dönüşü haritası; yılın tonu.
  **Relocation destekli:** yaşadığın şehri girersen harita oraya kurulur
  (dönüş anı değişmez, evler/ASC değişir).
- **🌗 İç Takvim** — ikincil progresyon (gün-yıl kuralı): progres Ay'ın
  burcu ve evi, sonraki burç değişimi, progres lunasyon fazı; **solar arc**
  kesinleşmeleri kapalı formda çözülür. Üstüne **30 günlük transit
  takvimi**: kesinleşme günü altın, yaklaşan lila, ayrılan soluk; retro
  istasyonları da işaretli.

### Kehanet araçları (dördü de Rytho+)

**🀄 BaZi — Dört Sütun.** Projedeki en özgün mühendislik; hazır kütüphane
yok, sıfırdan yazıldı:
- Dört sütun (Li Chun yıl sınırı, güneş boylamı ay sınırı, 60'lık gün
  döngüsü, geç-Zi ekolü).
- **Gerçek Güneş Zamanı** — boylam düzeltmesi + Zaman Denklemi. İstanbul'da
  ~60-80 dakikalık fark, doğumların yaklaşık üçte birinde **saat dalını
  değiştiriyor.** Kullanıcıya "13:30 → 12:22 (−68 dk)" diye gösterilir.
- Gizli kökler (藏干) ağırlıklı, her biri kendi On Tanrı'sıyla.
- **Day Master gücü** — ay komutu, kökler, gövdeler, yakınlık; hükmün
  **puan dökümü API'de görünür** (LLM'e sordurulmaz: aynı harita iki gün
  iki farklı hüküm alırdı).
- Şans sütunları (Da Yun) + **takvim yılları** ("1993-2003"), yıllık sütun
  (Liu Nian), **5 Shen Sha yıldızı** (her bulgu hangi kuraldan geldiğini
  taşır), Kong Wang.

**🪙 İ Ching — Değişimler Kitabı.**
- İki çekim yöntemi **gerçek olasılıklarıyla**: madeni para ve
  civanperçemi (yarrow'un asimetrik dağılımı doğru uygulanmış).
- Rastgelelik `secrets` (kriptografik), `random` değil.
- Hareketli çizgiler → dönüşen heksagram, **hu gua** (nükleer heksagram).
- **Liu Yao / Najia**: altı akraba, Shi/Ying çizgileri, saray ataması
  tablodan değil **kuraldan** üretilir (64 desen tek kuraldan çıkar).
- 64 heksagram × 384 yao pasajı, iki dilde.
- Niyetsiz sorular ("test", "asdf") çekim hakkını harcamadan geri çevrilir.

**☯ Doğum Kapısı.** Doğum anındaki Güneş'in 64 kapılı çarktaki yeri —
çekim değil, kalıcı kimlik katmanı. Saat bilinmiyorsa kapı sınırı
aşılıyorsa **iki aday da bildirilir**.

**👁️ Yüz Okuma (Firaset).**
- **Fotoğraf sunucuya hiç gitmez.** Tespit cihazda (Google ML Kit + TFLite
  segmentasyon); sunucuya yalnız **oranlar** gider, kare bellekte işlenip
  atılır, diske yazılmaz.
- Ölçülenler: San Ting üç bölge oranı, çene/elmacık, ağız genişliği, dudak
  dolgunluğu, göz aralığı, simetri + **hareketlilik**.
- **Belirti üretir, hüküm değil** ("geniş alın" — "zeki" değil).
- Ten rengi (etnisite ölçerdi) ve ses perdesi (cinsiyete bağlı) **bilinçli
  olarak reddedildi**.
- Ayrı, sürümlü, geri alınabilir **biyometrik rıza**; rıza geri alınınca
  üretilmiş okumalar silinir.

---

## 5. Sohbet — haritanı bilen AI

- Konu bazlı arşiv (kaldığın yerden devam / yeni konu / kaydırarak sil);
  kullanılmayan konu 30 gün sonra silinir.
- **Üç katmanlı hafıza:** (1) damıtılmış olgular — kapalı 7 kategori,
  **sağlık bilinçli olarak dışarıda**; (2) ham arşiv; (3) her turda
  haritanın "fısıltısı" (natal + transit + gökyüzü + abonede BaZi).
- **Akıllı arama:** korpus taraması senin cümlenle değil, **konu + senin
  haritanın o konuyla ilgili faktörleriyle** yapılır. "İşimle ilgili ne
  yapmalıyım?" sorusu şuna dönüşür: *"Mesleğin niteliği, statü. Satürn:
  Oğlak (10. ev) · Mars: Boğa. Güneş Kare Mars. Transit Satürn → Güneş."*
- Öneri çipleri: Kariyer · Aşk hayatı · Bu ay ne getiriyor · Para ve iş ·
  Bağlanma.
- **Güvenlik kapısı:** sağlık, hamilelik, ölüm, finans tavsiyesi soruları
  LLM'e hiç gitmez — ama "annem hasta, üzgünüm" gibi paylaşımlar
  engellenmez (iki işaret birlikte aranır: yasak konu **ve** cevap talebi).
  Dil değiştirerek kapı aşılamaz.

---

## 6. Arkadaşlar — serbest metinsiz sosyal katman

> **Tasarım kuralı: yazı kutusu yok.** Görünen her şey türetilmiş veridir.
> Bu, moderasyon yükünü sıfıra yakın tutar ve tacizi yapısal olarak
> imkânsızlaştırır.

- **Kullanıcı adı** (@ad) — sonradan değiştirilebilir, davet bağlantısıyla
  paylaşılır.
- **Rehber eşleşmesi** — numaralar **cihazda** hash'lenir, rehber adları
  cihazdan çıkmaz, sunucu hash listesini **saklamaz**; eşleşme
  **karşılıklıdır** (ikiniz de açmışsanız görünürsünüz). Varsayılan kapalı.
  Rehber ekranı: üstte "Uygulamada" (arkadaş ekle), altta davet edilebilir
  kişiler; arama Türkçe karakter duyarlı.
- **Hazır tepkiler / dürtme** — 8 sabit tepki (Seri 🔥, Aklımdasın, Parla,
  Devam et, Tebrikler, Aynı frekans, İyi geceler, Bugüne bak). Gönderince
  yıldız patlaması + karşı tarafa bildirim.
- **Günlük ikili okuma (dyad)** — arkadaşınla aranızdaki **bugüne özgü**
  dinamik; iki taraf da aynı metni görür. **Kalıcı uyum puanı bilinçli
  olarak yoktur** — skor hesaplanabiliyor ama kasten gösterilmiyor:
  "geri alınamaz bir damga gerçek ilişkilere zarar verir."
- Seri görünürlüğü kullanıcının kontrolünde; güvenlik menüsünde
  arkadaşlıktan çıkarma, engelleme, şikâyet.

---

## 7. Profil ve hesap

Doğum kaydı düzeltme · yaşanan şehir (Yıl Haritası için) · kullanıcı adı ·
**giriş yöntemleri** (Google/Apple hesabına şifre ekleme, şifreli hesaba
Google bağlama) · bildirimler (günlük okuma, seri hatırlatıcı, arkadaş
tepkileri + **sessiz saatler** 22:00-08:00) · gizlilik anahtarları · **dil
(TR/EN)** — arayüz ve AI yorumlarının dili birlikte değişir · ses efektleri
· abonelik ve jetonlar · avatar düzenleyici (sürükle-yakınlaştır) ·
**hesap silme** (ne silinip ne silinmeyeceği tek tek yazılır, yazarak onay).

**Onboarding — "Yıldız Yolu" sihirbazı:** 6 adım, adım başına tek soru;
takımyıldız ilerleme çubuğu her adımda bir yıldız yakar. Doğum saati için
**"Bilmiyorum" birinci sınıf seçenektir** ve sonucu dürüstçe açıklanır.
Sonunda "Büyük Üçlü" perdesi (Güneş/Ay/Yükselen açılışı).

---

## 8. Ücretsiz vs Rytho+

| Ücretsiz (hep açık) | Rytho+ |
|---|---|
| Günlük burç yorumu + hikâye + paylaşım kartı | Kişiye özel günlük okuma |
| Canlı gökyüzü ("Şu an") | Doğum haritası + tam rapor + 6 detay ekranı |
| Günlük seri | Yıl Haritası (solar return) |
| Arkadaşlar katmanının **tamamı** | İç Takvim (progresyon + transit) |
| Profil, doğum kaydı, avatar, bildirimler, dil | BaZi · İ Ching · Doğum Kapısı · Yüz Okuma |
| Sohbet (jeton ekonomisiyle) | Arkadaşla günlük ikili okuma |

**Jeton ekonomisi:** Rytho+ ayda **300 jeton** verir (devretmez); satın
alınan paketler (100/300/1000) **hiç yanmaz**. Bedeller: sohbet 1 · İ Ching
2 · ikili okuma 3 · derin raporlar 5. Kilitli ekranda ücretli uca **istek
bile atılmaz** — kart gösterilir, ödeme ekranı ancak dokununca açılır.

---

## 9. "Ölçülmeyen söylenmez" — dört somut kanıt

Bunlar pazarlama cümlesi değil, kodda çalışan davranışlar:

1. **Doğum saatin yoksa Yıl Haritası'nın Yükseleni hiç üretilmez** —
   yaklaşık bir değer uydurup göstermek yerine o satır yoktur.
2. **Day Master gücünün puan dökümü** API'de döner — "neden güçlü"
   sorusunun cevabı her an gösterilebilir.
3. **Her Shen Sha bulgusu hangi kuraldan geldiğini taşır** — "model
   uydurdu mu?" sorusunun cevabı çıktının içindedir.
4. **İlişki uyum skoru hesaplanır ama kasten gizlenir.**

Ayrıca motor bir varsayım yaptığında **beyan eder**: şehir çözülemediyse
"Yükselen yaklaşık", BaZi'de sütun birleşmeleri hesaba katılmıyorsa
"kapsam dışı", şans dönemi başlangıcı saatsizse "±4 ay belirsizlik".

---

## 10. Gizlilik duruşu (mağaza formu için de geçerli)

| Veri | Durum |
|---|---|
| Yüz görüntüsü | **Sunucuya hiç gitmez** — cihazda işlenir, oranlar gider, kare silinir |
| Telefon numarası | Ham hâli **saklanmaz** — yalnız SHA-256 özeti |
| Rehber | **Saklanmaz** — eşleştir, dön, at; loga yalnız adet |
| Doğum verisi | Başka kullanıcıya **asla** gitmez (ikili okumada bile sunucuda kalır) |
| Sohbet arşivi | 30 gün; istemci yazamaz, yalnız sunucu yazar |
| Hesap silme | Karşı taraftaki arkadaşlık kayıtları dahil temizlenir (şikâyet kayıtları hariç — gerekçesi gizlilik metninde) |
| Tek cihaz kilidi | Yalnız abonelerde; devralma onayla |

---

## 11. Teknik omurga

- **Efemeris:** Swiss Ephemeris (`sepl_18.se1` + `semo_18.se1`, 1800-2400),
  kerykeion 5.12.9 / pyswisseph 2.10.3.2 — sürümler sabit.
- **Konum:** offline GeoNames şehir veritabanı (~34 bin şehir) — ağa
  bağımlı değil, deterministik.
- **AI:** Google Gemini (flash), RAG korpusu **232 parça / ~191 KB**:
  Ptolemaios *Tetrabiblos* (Ashmand 1822 çevirisi, kamu malı), Erzurumlu
  İbrahim Hakkı *Marifetname* (Rytho aktarımı), Legge'nin 384 yao metni
  (kamu malı) + altı özgün doktrin dosyası.
- **Telif kuralı:** eser kamu malı olsa bile **çevirisi ayrı telif taşır**
  — bu yüzden Ashmand/Legge kullanılır, Robbins/Wilhelm-Baynes kullanılmaz.
- **Sunucu:** FastAPI + Cloud Run; Firestore; RevenueCat + Google Play.

---

## 12. ⚠️ İddia EDİLEMEYECEKLER (mağaza metni yazarken dikkat)

Bunlar şu an kodda **yok**; yazılırsa yanlış beyan olur ve ürünün kendi
ilkesini çiğner:

1. **Vedik astroloji / Nakshatra / Dasha** — hesaplanmıyor. *(✅ R2-D1:
   persona, README ve korpustaki iddialar temizlendi; persona artık
   sorulursa "hesaplanmıyor" diye cevap veriyor. Bekçi test:
   test_honesty.py — geri gelemez.)*
2. **"NASA verisiyle hesaplıyoruz"** — NASA yalnızca gezegen uzaklığı
   göstergesi için; tüm konum/açı hesabı Swiss Ephemeris.
3. **"Yüzlerce kadim kitap"** — korpus 232 parça; dürüst tarif: *seçilmiş
   kamu malı klasikler + özgün doktrin sentezi*.
4. **"Gerçek Güneş Zamanı kullanıyoruz"** — yalnız **BaZi** için doğru;
   Batı haritasında standart saat dilimi kullanılıyor.
5. **Natal relocation** — yok (relocation yalnız Yıl Haritası'nda).
6. **BaZi'de sütun birleşmeleri (he/sanhe/chong)** — hesaplanmıyor (motor
   bunu zaten beyan ediyor).
7. **"Bilimsel ölçüm"** (firaset için) — eşikler kalibrasyon sabitidir,
   nüfus normu değil.

---

## 12b. Pazarlama dil kılavuzu (R2-D1 — bağlayıcı)

Mağaza metni, web sitesi, tanıtım görseli, basın cümlesi — nerede olursa
olsun:

| ❌ Yazılamaz | ✅ Doğrusu |
|---|---|
| "NASA destekli / NASA onaylı astroloji" | "Astronomik efemeris verileriyle hesaplanan gökyüzü konumları" |
| "NASA verisiyle hesaplıyoruz" | "Konum/açı hesabı Swiss Ephemeris; gezegen uzaklık göstergesi NASA JPL Horizons" |
| "Uyum puanınız 82" | "İlişkinin nerede kolaylaştığını, nerede emek istediğini ölçer — puan vermez" |
| "Geleceğinizi söyler" | "Eğilimleri ve zaman pencerelerini gösterir; kesin tarihli kehanet yapmaz" |
| "Sınırsız AI" | "Ayda 300 AI kredisi" (ölçülü ve dürüst) |
| "Yüzlerce kadim kitap" | "Seçilmiş kamu malı klasikler + özgün doktrin sentezi" |
| "Bilimsel yüz analizi" | "Cihaz üstü geometrik ölçüm + firaset geleneği yorumu" |

Gerekçe: NASA verisi kullanmak NASA'nın astrolojiyi doğruladığı anlamına
gelmez (Co-Star bile aynı veriyi pazarlıyor — fark yaratmaz, risk
yaratır). Rytho'nun farkı veri kaynağı değil, ZİNCİRİN kendisi: gerçek
hesap → kişisel harita → ölçülmüş transit → kaynaklı yorum → dayanağını
gösteren arayüz.

---

## 13. Konumlandırma önerisi (mağaza/tanıtım için)

> **"Yıldızlar herkese aynı. Sen değilsin."**
>
> Rytho, doğum anını gerçek gökyüzü hesabıyla çözer; dört kadim sistemin
> okumasını tek bir sese dönüştürür. Ölçebildiğini söyler, ölçemediğini
> söylemez — doğum saatini bilmiyorsan Yükselen'ini uydurmaz, ilişkilerine
> puan vermez, sana yalnızca duymak istediğini anlatmaz.
