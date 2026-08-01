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
| `corpus/tr/kiyafetname_marifetname.md` | tr | Rytho özgün metni |
| `corpus/en/chinese_metaphysics.md` | en | Rytho özgün metni |
| `corpus/en/islamic_astrology.md` | en | Rytho özgün metni |
| `corpus/en/temperaments_physiognomy.md` | en | Rytho özgün metni |

Bunlar kamu malı kaynaklardan ve genel alan bilgisinden yazılmış özet
metinlerdir; hiçbir telifli eserden alıntı içermez. Telif RythoAI'ye aittir.

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
iki dil de aynı doktrini taşıyor.

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
