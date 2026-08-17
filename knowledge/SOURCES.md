# Korpus kaynakları ve lisans kaydı

Bu dosya bilgi tabanındaki her metnin nereden geldiğini ve hangi hakla
kullanıldığını kaydeder. **Ticari bir üründe bu kayıt hukuki savunmanın
kendisidir**; "internetten buldum" savunulabilir bir konum değil.

Korpusa yeni bir dosya eklemeden önce buraya künyesi yazılır.

---

## Temel kural: eser kamu malı olsa bile ÇEVİRİSİ ayrı telif taşır

Bu, astroloji/kadim metin korpusunda en kolay düşülen tuzak. Metnin kendisinin
yüzlerce yıllık olması hiçbir şey ifade etmiyor; kullandığın **baskı ve
çevirmen** belirleyici.

| Eser | Güvenli sürüm | Kullanılamayacak sürüm |
|---|---|---|
| Ptolemaios, *Tetrabiblos* | J.M. Ashmand çevirisi, 1822 — kamu malı | F.E. Robbins, 1940 (Loeb) — telifli |
| *I Ching* | Legge çevirisi, 1882 — kamu malı | Wilhelm/Baynes — telifli |
| Erzurumlu İbrahim Hakkı, *Marifetname* (1757) | Özgün metin kamu malı | Modern transkripsiyon/sadeleştirmeler — transkribe edenin telifi |

Aynı mantık modern Türkçe astroloji kitapları, blog yazıları ve ansiklopedi
maddeleri için de geçerli: **korpusa girmezler.**

Güvenli zemin üçe iner:

1. Telif süresi dolmuş özgün metinler,
2. Telif süresi dolmuş çeviriler,
3. Kaynaklardan okuyup **kendi yazdığımız** sentez (telif bize ait).

---

## Kayıtlı kaynaklar

### Rytho özgün sentezi (mevcut korpus)

| Dosya | Dil | Durum |
|---|---|---|
| `corpus/tr/cin_metafizigi.md` | tr | Rytho özgün metni |
| `corpus/tr/ilmi_nucum.md` | tr | Rytho özgün metni |
| `corpus/tr/bazi_doktrin.md` | tr | Rytho özgün metni (2026-08-04) |
| `corpus/tr/iching_doktrin.md` | tr | Rytho özgün metni (2026-08-04, İ7) |
| `corpus/en/chinese_metaphysics.md` | en | Rytho özgün metni |
| `corpus/en/islamic_astrology.md` | en | Rytho özgün metni |
| `corpus/en/bazi_doctrine.md` | en | Rytho özgün metni (2026-08-04) |
| `corpus/en/iching_doctrine.md` | en | Rytho özgün metni + işaretli kısa Legge alıntıları (kamu malı; 2026-08-04, İ7) |
| `corpus/tr/tahmin_doktrin.md` | tr | Rytho özgün metni (2026-08-05, T4) |
| `corpus/en/prediction_doctrine.md` | en | Rytho özgün metni (2026-08-05, T4) |

Bunlar kamu malı kaynaklardan ve genel alan bilgisinden yazılmış özet
metinlerdir; hiçbir telifli eserden alıntı içermez. Telif RythoAI'ye aittir.

### I Ching veri dosyası — `backend/data/hexagrams.json` ✅ (2026-08-04, Revize İ1)

| Alan | Değer |
|---|---|
| `judgment_tr/en`, `image_tr/en`, adlar | **Rytho özgün metni** — birebir çeviri değil, klasik korpusa sadık aktarım (üretici betik: `backend/scripts/add_iching_en.py`; bu kayıtla geriye dönük tescil edildi) |
| `lines_en` (384 yao + 2 "tüm çizgiler") | **James Legge, *The Yî King*** (Sacred Books of the East XVI, 1882/1899) — **kamu malı**. Dijital nüsha: Internet Sacred Text Archive `sacred-texts.com/ich/ic01..ic64.htm`; ham HTML `knowledge/raw/legge/` altında saklı. Project Gutenberg'de müstakil nüsha YOK (#25501 Çince orijinal çıktı). Aktaran betik: `backend/scripts/ingest_legge_yao.py` — OCR onarımları ("S."→5, "T he"→The, numarasız çizgi) betikte belgeli |
| `lines_tr` (384 yao + 2) | **Rytho aktarımı** — kamu malı Legge metni okunarak, cümle aktarılmadan Rytho Türkçesiyle yazıldı (Tetrabiblos TR emsali). Betik: `backend/scripts/add_iching_lines_tr.py`. Telif RythoAI'ye aittir |
| Trigram `family/attribute/direction` | Klasik Shuo Gua geleneğinin tartışmasız çekirdeği; betik: `backend/scripts/add_trigram_attrs.py` |

> Wilhelm/Baynes, Özşahin çevirisi ve Alfred Huang **telifli** — hiçbirinden
> cümle alınmadı, alınamaz (bkz. satır 20'deki tuzak tablosu).

### Doğum kapıları — `backend/data/birth_gates.json` ✅ (2026-08-04, Revize İ8)

64 kapının doğum-karakteri pasajları (TR+EN) — **Rytho özgün metni**;
heksagram doktrininden (yao verisi + iching doktrin dosyaları) yazıldı.
Çark DİZİLİMİ olgu-veridir (`birth_hexagram_service.GATE_ORDER`); **Gene
Keys ve Human Design literatüründen tek cümle yoktur** — ikisi de telifli.
Üretici betik: `backend/scripts/add_birth_gates.py` (tamlık kapılı).
Telif RythoAI'ye aittir.

> **Tahmin doktrin dosyaları hakkında (2026-08-05, T4):** Zamanın üç
> ölçeği, güneş dönüşü okuma yöntemi, progres Ay lunasyon döngüsü, solar
> arc yılları, transit applying/exact/separating doktrini ve tahmin
> dilinin etiği; tahmin motorunun (T1-T3) hesapladığı kavramların YORUM
> zeminidir. Teknikler (gün-yıl kuralı, güneş dönüşü, solar arc) kamu
> malı yöntemlerdir; metin hiçbir modern kaynaktan — astro-seek ve
> astro.com dahil — cümle almaz, genel alan bilgisinden sentezlendi.
> Telif RythoAI'ye aittir.

> **BaZi doktrin dosyaları hakkında (2026-08-04, Revize B7):** Sütun
> sarayları, On Tanrı aileleri, gizli kökler, ay komutu/güç hükmü, yararlı
> element, mevsim-iklim ayarı ve beş Shen Sha bölümleri; motorun (B0-B5)
> hesapladığı kavramların YORUM zeminidir. Esin kaynakları klasik BaZi
> külliyatıdır — *Di Tian Sui*, *Zi Ping Zhen Quan*, *San Ming Tong Hui*,
> *Qiong Tong Bao Jian* (hepsi kamu malı Çince klasikler) — ancak metin
> hiçbir MODERN çeviriden cümle almaz: modern İngilizce çeviriler telifli
> olduğu için "kapat ve kendi cümlenle yaz" disipliniyle, genel alan
> bilgisinden sentezlendi. Telif RythoAI'ye aittir.

> `corpus/tr/kiyafetname_marifetname.md` ve `corpus/en/temperaments_physiognomy.md`
> **kaldırıldı** (2026-08-02): yerlerini aşağıdaki Marifetname aktarımı aldı.
> İkisi de aynı zemini yüzeysel biçimde kapsıyordu; bırakılsalardı aynı
> konuda iki ayrı parça getirilir ve pasaj bütçesi boşa harcanırdı.

### Tetrabiblos — `corpus/en/tetrabiblos.md` ✅ (2026-08-01)

| Alan | Değer |
|---|---|
| Eser | *Tetrabiblos* (Τετράβιβλος), Klaudios Ptolemaios, ~MS 2. yüzyıl |
| Çeviri | **J. M. Ashmand, 1822** |
| Dijital nüsha | Project Gutenberg eBook **#70850**, `70850.txt.utf-8` (552.667 bayt) |
| Lisans | Kamu malı. PG beyanı: "Public domain in the USA". 1822 basımı bir çeviri için koruma süresi TR/AB'de de dolmuş durumda |
| Dönüştüren | `backend/scripts/ingest_tetrabiblos.py` — kapsam kararları kod içinde |
| Kapsam | 26 bölüm: Kitap I (gezegen/burç doğaları, üçgenler, açı doktrini, evler), Kitap III (yükselen, mizaç, aklın niteliği), Kitap IV (rütbe, meslek, evlilik, dostluk, yolculuk) |
| Türkçe | `corpus/tr/tetrabiblos.md` — **Rytho aktarımı** (aşağıya bkz.) |

### Tetrabiblos Türkçe aktarımı — `corpus/tr/tetrabiblos.md` ✅

Kamu malı bir Türkçe *Tetrabiblos* çevirisi **yok**. Bu dosya birebir çeviri
değil, kamu malı Ashmand metninden doktrini koruyarak yapılmış **Rytho
aktarımıdır**; telif RythoAI'ye aittir (`license: rytho-original`,
`based_on:` alanında kaynak künyesi).

Neden aktarım, çeviri değil:

- Makine çevirisi hukuken sorunsuz olurdu (Ashmand kamu malı) ama kalite ve
  ton tutmaz — 1822 İngilizcesi doğrudan çevrildiğinde okunmaz hâle gelir.
- Aktarım tonu kontrol etmemizi sağlıyor: Batlamyus'un ahlaki hükümleri
  yumuşatılmadan ama aşağılayıcı dil taşınmadan verildi.

**Doktrin birliği korundu.** İngilizce kullanıcı Batlamyus, Türkçe kullanıcı
Marifetname okusaydı aynı soruya iki farklı gelenekten cevap alırlardı. Her
iki dil de aynı doktrini taşıyor. TR aktarımı EN ile aynı konu başlıklarını
kapsar: mevsimler, eril/dişil burçlar, emreden/itaat eden, bakan burçlar,
bağlantısız (inconjunct), yüzler/arabalar, rütbe talihi dahil. Birebir
çeviri değildir; 1822 düzyazısı yoğunlaştırılmıştır.

**PG başlık/altlığı ayıklandı.** O metin Project Gutenberg'in paketlediği
e-kitaba ve markasına ait, alttaki 1822 çevirisine değil.

**Dipnotlar korpusa alınmadı.** Ashmand'ın dipnotları çevirmenin kendi
yorumunu taşıyor ve sık sık başka kaynaklardan alıntı yapıyor (Placidus,
Cooper çevirisi); telif durumları ayrı bir soru, riske girilmedi.

#### Kapsam dışı bırakılanlar (30 bölüm)

Üç gerekçeyle; hepsi betikte tek tek kayıtlı:

1. **Yasak alan (ürün ilkesi).** Ömür süresi, ölüm biçimi, prorogasyon,
   bedenin ve aklın hastalıkları, gebe kalma, cinsiyet kestirimi, servet.
   Bunları korpusa almak güvenlik kapısını **arkadan delmek** olurdu: kapı
   kullanıcının sorusunu süzüyor, ama masum bir soruya getirilen "ölüm süresi"
   pasajı cevabı oraya sürükleyebilir. Savunma iki katmanlı.
2. **Temellendirilemez.** Sabit yıldızlar, takımyıldızlar, sınırlar (terms),
   derece hükümdarlıkları — uygulama bunları hesaplamıyor. Karşılığı olmayan
   bir konum hakkında pasaj döndürmek "gök verisi uydurulmaz" ilkesiyle
   çelişir.
3. **Ürünle ilgisiz.** Kitap II bütünüyle ülke/iklim/tutulma astrolojisi;
   kişisel okuma yapan bir uygulamanın arama uzayını kirletir.

#### Ton uyarısı

Ptolemaios'un karakter tarifleri bugünün ölçüsüyle **çok serttir** — kaynakta
"thoroughly depraved", "assassins", "treacherous" gibi ahlaki hükümler geçiyor.
Bunlar geleneğin sesi, kullanıcı hakkında hüküm değil. Persona (`WHISPER_RAG`)
modele bu ayrımı açıkça söylüyor: kaynağın ahlaki yargısı aktarılmaz, altındaki
gözlem alınır. Ürünün "yağcılık yok" ilkesi **zor olanı söylemektir, birini
aşağılamak değil**.

> Doktrin birliği notu: İngilizce kullanıcı Ptolemaios, Türkçe kullanıcı
> Marifetname okusaydı aynı soruya iki farklı gelenekten cevap alırlardı. Bu
> yüzden ilk kitap iki dile de aynı doktrini taşıyor. Marifetname kendi
> turunda, iki dile birden eklenecek.

---

### Servet ve Aile doktrinleri — `corpus/{tr,en}/{servet,aile,wealth,family}_doktrin*.md` ✅ (2026-08-18, S-turu)

| Alan | Değer |
|---|---|
| Kaynak | Tetrabiblos IV.2 "The Fortune of Wealth", IV.5 "The Parents", IV.6 "Brothers and Sisters", IV.9 "Children" — Ashmand 1822, kamu malı |
| Neden ayrı dosya | Bu dört bölüm `en/tetrabiblos.md`'e HİÇ alınmamıştı — ölçüldü, kapı da (`_TOPIC_TRIGGERS`) para/aile konusu tanımıyordu (bkz. S-turu bulgu 3) |
| Yöntem | **İkisi de Rytho aktarımı** (`license: rytho-original`) — EN dahil, çünkü ham kaynak `Parents`/`Siblings`/`Children` bölümlerinde ölüm/kaza/doğurganlık kehaneti taşıyor ve bunlar aktarılamaz |
| Kapsam dışı bırakılan | Kardeş sayısı/cinsiyeti tahmini, ebeveyn ölüm şekli/zamanı, çocuk sağlığı/doğurganlık/yaşam süresi (hamilelik güvenlik kapısıyla aynı ilke), servet miktarı/zamanlaması |
| Yapısal eşleşme | TR ve EN aynı üç-dört alt başlığı taşır (Şans Noktası/gezegen kapıları; Baba-Anne/Kardeşler/Çocuklar) — çift dilli RAG'in "aynı soruya aynı derinlik" ilkesi korunur |

## Marifetname — `corpus/{tr,en}/marifetname.md` ✅ (2026-08-02)

| Alan | Değer |
|---|---|
| Eser | *Marifetname*, Erzurumlu İbrahim Hakkı, 1757 |
| Özgün eser | **Kamu malı** (telif süresi çoktan dolmuş) |
| Korpustaki metin | **Rytho aktarımı** — `license: rytho-original` |
| Kapsam | Dört unsur, ahlat-ı erbaa (mizaç), burç–ay–mevsim eşlemesi, yedi gezegenin tabiatı ve sa'd/nahs, **günlerin ve saatlerin yöneticileri**, **ayın menzilleri**, feleklerin düzeni, firaset yöntemi, yüz/ses/duruş belirtileri, firasetin sınırı |

### Neden aktarım, alıntı değil

Elimizdeki nüsha (370 sayfalık PDF, 2014'te web'e konmuş) **modern bir Türkçe
aktarım**. İçinde:

- Yayıncı yok, çevirmen/sadeleştiren adı yok, telif notu yok
- Dosya üst verisindeki yazar alanı bir site adı

**Telif notunun yokluğu kamu malı olduğu anlamına gelmez.** Özgün eser (1757)
kamu malı, ama o modern aktarımı yapan kişinin hakkı vardır. Bu, Ashmand
(kamu malı) ile Robbins (telifli) ayrımının aynısı. Bu yüzden bu PDF'ten
**cümle aktarılmadı**; doktrin okunup metin sıfırdan yazıldı. Fikir ve
doktrin telifle korunmaz, ifade korunur.

Daha temiz zemin isteniyorsa: Osmanlıca özgün metin ya da telif süresi dolmuş
eski bir baskı bulunup künyesi buraya yazılmalı.

### Kapsam dışı bırakılanlar ve gerekçeleri

Kaynak metnin kıyafetname bölümü olduğu gibi alınamazdı.

**1. Irk, ten ve göz rengine dayalı karakter hükümleri — ALINMADI.**
Kaynakta ten rengi ve göz rengine göre zekâ, sağlık ve güvenilirlik atfeden
ifadeler var. Yüz okuma özelliği aktif edildiğinde bu pasajlar kullanıcının
yüzüne bakan bir sistem tarafından getirilebilir hâle gelir ve uygulama ten
rengine göre karakter hükmü verir. Sonuç: App Store 1.1.1 / Play ayrımcı
içerik ihlali, AB AI Act tarafında biyometrik çıkarımın ırkla korele çıktı
üretmesi, ve tek bir ekran görüntüsüyle ürünün bitmesi.

**2. Cinsel organ ve meme tariflerine dayalı karakter/şehvet hükümleri —
ALINMADI.** Kaynağın ilgili bölümünün yarısı bu; mağazada yayınlanacak bir
uygulamanın korpusunda getirilebilir metin olamaz.

**3. İlahiyat, tasavvuf şiiri ve anatomi bölümleri — ALINMADI.** Ürünün
yaptığı iş değil; arama uzayını kirletir.

Bu, Tetrabiblos'ta uygulanan kuralın aynısı: **korpus bir güvenlik
yüzeyidir.** Kapı kullanıcının sorusunu süzer, ama masum bir soruya getirilen
pasaj cevabı istenmeyen yere sürükleyebilir.

### Alınan ama dikkat isteyen kısım

Yüz hatlarının mizaç karşılıkları korpusa **belirti** olarak girdi, hüküm
olarak değil. Ayrıca geleneğin kendi koyduğu sınır ayrı bir bölüm olarak
yazıldı ("Firasetin Sınırı"): tek belirti hüküm vermez, belirti eğilimdir
kader değildir, ve bilmenin amacı ayıklamak değil dengelemektir. Yüz okuma
özelliği geldiğinde personanın dayanacağı zemin burasıdır.

### Motor tarafı: hesaplanır hâle getirildi (2026-08-02)

Korpusa girip motorda karşılığı olmayan bilgi, modelin dayanaksız konuşmasına
davetiyedir. Marifetname'nin iki somut katkısı bu yüzden hesaplandı:

| Bilgi | Nereden | Notu |
|---|---|---|
| **Günün yöneticisi** | Kullanıcının **yerel** tarihi | Gökyüzü yükü UTC'de hesaplanıp paylaşıldığı için oraya gömülmedi; saat dilimi farkı olan kullanıcıya yanlış gün gösterirdi |
| **Ayın menzili** (1–28) | Ay'ın boylamı | Konumdan bağımsız, paylaşımlı yükte duruyor |

Bilinen sınır: gelenekte **gün, gün doğumunda başlar**, gece yarısında değil.
Kullanıcının enlemi elimizde olmadığı için takvim günü kullanılıyor; fark
yalnızca gece yarısı ile gün doğumu arasındaki saatlerde ortaya çıkıyor.
**Saat yöneticisi** aynı sebeple henüz hesaplanmıyor — gün doğumu/batımı
gerekiyor, o da konum istiyor.

> **Hatırlatma:** korpusun hazır olması özelliğin yayınlanabilir olması
> demek değil. Yüz okuma bir dönem v1 dışı bırakılmıştı çünkü görüntü
> sunucuya gidiyordu (GDPR Md.9 / KVKK md.6 / BIPA). Şimdi tamamen cihaz
> üstünde: görüntü telefondan çıkmaz; açık rıza ve hukuki metinler
> `docs/store-privacy-labels.md` ve gizlilik politikasında.

---

### Efemeris veri dosyaları — `backend/ephe/*.se1` ✅ (2026-08-05, T0)

| Alan | Değer |
|---|---|
| Dosyalar | `sepl_18.se1` (gezegenler 1800-2400), `semo_18.se1` (Ay) |
| Kaynak | Astrodienst resmi dağıtımı — github.com/aloistr/swisseph, `ephe/` |
| Neden | kerykeion paketi bu iki dosyayı taşımıyor; yokluklarında Swiss Ephemeris sessizce Moshier analitik hesabına düşüyor ve 1800 öncesi doğumlarda Chiron/Lilith kayboluyordu (bkz. `backend/core/ephemeris.py`) |
| Lisans | Swiss Ephemeris veri dosyaları — lisans yönetimi ürün sahibinde (ticari lisans süreci ayrıca yürütülüyor) |
| Doğrulama | `tests/test_astro_engine.py::TestEfemerisVerisi` + almanak altın vektörleri (USNO ekinoks/gündönümü, 2020 büyük kavuşumu, 2019 Ay tutulması, 2023 Merkür retrosu) |

## Gazetteer verisi (2026-08-07, O1)

| Alan | Değer |
|---|---|
| Dosyalar | `backend/data/gazetteer.json`, `apps/mobile/assets/data/cities.json`, `apps/mobile/assets/data/countries.json` |
| Kaynak | GeoNames (geonames.org) — `cities15000.zip`, `admin1CodesASCII.txt`, `countryInfo.txt` dump'ları |
| Lisans | **CC-BY 4.0** — atıf zorunlu; uygulama içi atıf hukuk sayfasında (legal_texts.dart), dosya meta'sında kaynak satırı |
| Üretici | `backend/scripts/build_gazetteer.py` (doğrulamalı: 81 TR ili + Türkçe egzonimler + eski gazetteer anahtarları assert edilir; ham dump'lar `backend/data/raw/` altında, git dışı) |
| Neden | Eski elle yazılmış sözlük 81 ilin yalnız 33'ünü tanıyordu; çözülemeyen şehir sessizce İstanbul'a düşüyordu. Kullanıcı kararı: dump indirilip kendi veritabanımıza alınır — API/ağ bağımlılığı yok |
| Doğrulama | `tests/test_geo_service.py` |

## Korpus dosyası künye biçimi

Kitap kaynaklı dosyalar başlarında künye taşır. `rag_service` bunu okur ve her
parçaya iliştirir; atıf gösterimi ve lisans denetimi buna bağlı.

```markdown
---
book: Tetrabiblos
author: Claudius Ptolemaeus
translator: J.M. Ashmand (1822)
license: public-domain
source: <kullanılan dijital nüshanın künyesi>
---

# Tetrabiblos

## Of the Influence of the Planets
...
```

Kendi yazdığımız sentez dosyalarında künye isteğe bağlıdır (yokluğu
"Rytho özgün metni" anlamına gelir), ama `license: rytho-original` yazmak
tercih edilir.

---

## Kullanım biçimi

Korpus parçaları LLM prompt'una **bağlam** olarak giriyor, kullanıcıya doğrudan
gösterilmiyor. Persona modele kaynağı blok halinde aktarmamasını, en fazla tek
bir ilgili ayrıntıyı kendi cümlesine sindirmesini söylüyor.

Bu, telif açısından alıntı yapmaktan farklı bir kullanım; yine de kamu malı
olmayan metinlerin korpusa girmemesi kuralı **değişmez**.
