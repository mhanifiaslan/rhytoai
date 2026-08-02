# Derinleştirme planı — jenerik cevap sorununu kökten kapatma

**Durum:** Faz A–E tamamlandı (2026-08-01).

Bu plan tek bir şikâyeti hedefliyor: *"cevaplar jenerik."* O şikâyetin üç ayrı
teknik sebebi var ve üçü de ayrı ayrı ölçüldü. Sırayla kapatılıyorlar.

---

## Ölçülen başlangıç noktası

| Ne | Değişiklik öncesi | Sonrası / hedef |
|---|---|---|
| Sohbetin bildiği harita | Güneş, Ay, Yükselen (3 alan, ~80 karakter) | 7 gezegen + ev + element/nitelik dengesi + 4 açı + bugünkü transitler (~640 karakter) |
| Korpus büyüklüğü | dil başına ~9 KB, 12–13 parça | ~500 KB, ~700–900 parça |
| Ortalama parça boyu | 653 (TR) / 770 (EN) karakter | 900–1.100 karakter, üst sınırlı |
| Sohbete enjekte edilen kaynak | en fazla 560 karakter (2 × 280) | ölçüme dayalı, aşağıda |
| Arama modu | vektör (korpus küçükken) | vektör, ölçülebilir |

Üç darboğaz:

1. **Kişiselleştirme girdisi** — en zayıfı ve en ucuz düzeltileni. Bir astroloğu
   spesifik yapan şey "Satürn yedinci evinden geçiyor" diyebilmesidir. Swiss
   Ephemeris bunu zaten hesaplıyordu; sohbet katmanına hiç taşınmıyordu.
2. **Korpus** — bir kitap değil, broşür. Dil başına ~1.400 kelime.
3. **Enjeksiyon bütçesi** — korpus 100 kat büyüse bile sohbete 560 karakter
   giriyorsa fark görünmez.

---

## Faz A — Harita derinliği ✅ (bu turda yapıldı)

`backend/services/chart_context.py`. Sohbet artık şunu görüyor:

```
- Güneş: Aslan (12. ev) · Ay: Boğa (9. ev) · Yükselen: Başak
- Merkür: Başak (1. ev) · Venüs: Aslan (11. ev) · Mars: Boğa (9. ev) · ...
- Element dengesi: Ateş 2, Toprak 5, Hava 0, Su 1
- Nitelik dengesi: Öncü 2, Sabit 4, Değişken 2
- Doğum haritasının en sıkı açıları: Güneş Kare Mars (0.5°) · ...
- Bugün haritasına dokunan transitler: Merkür → Satürn Karşıt (0.0°) · ...
```

Korunan kurallar:

- **Uydurma yok.** Doğum tarihi veya şehri eksikse harita hesaplanmaz;
  `birth_kwargs`'ın varsayılanıyla (2000-01-01, Istanbul) üretilen haritayı
  "senin haritan" diye sunmak veri uydurmaktır. O durumda eski sığ özete
  düşülür.
- **Ham doğum verisi prompt'a girmez** — sadece türetilmiş konumlar. Testle
  korunuyor.
- **Dilden bağımsız hesap.** Sayımlar burç adından değil anahtarından yapılır;
  adlandırma tek aşamada, isteğin dilinde. Dil izolasyonu bekçisi bu yüzeyi de
  kapsıyor.
- **LLM maliyeti yok**, yalnızca efemeris. Natal olgular uzun ömürlü, transit
  olgular günlük önbellekli.

Yol boyunca çıkan iki gerçek kusur:

- `house` alanı tamsayı değil `"Twelfth_House"` metni geliyordu; ev satırı ve
  yığılma sayımı **sessizce** boş kalıyordu (hata yok, sadece derinlik yok).
- Transitleri salt orb'a göre sıralamak listeyi her gün Merkür'e boğuyordu.
  Merkür günde ~1° yol aldığı için daima birine çok dar bir açı yapar; oysa
  dönemi işaretleyen aylarca aynı noktada duran Satürn/Plüton'dur. Sıralama
  artık önce yavaş gezenleri veriyor.

---

## Faz B — RAG'i gerçek kitaba hazırlamak (kitaptan ÖNCE)

Mevcut hat 12 parça için yazıldı ve 900 parçada birkaç yerden birden kırılır.
Kitabı önce koyup sonra düzeltmek, her düzeltmede korpusun tamamını yeniden
vektörlemek demek. Altyapı önce gelmeli.

### B1. Boyut sınırlı parçalama + üst veri

`_load_chunks` yalnızca `##` başlıklarından bölüyor. Bir kitap bölümü tek
parçada binlerce kelime olur; embedding o parçanın ortalamasını alır ve arama
körelir.

- Üst sınır ~1.100 karakter, cümle sınırında bölme, ~120 karakter örtüşme
  (bir cümlenin iki parçaya bölünmesi anlamı öldürür).
- Parçaya üst veri: `book`, `chapter`, `section`, `lang`, `license`.
  Atıf ve süzme bunsuz mümkün değil, ve "hesaplanan ile yorumlanan ayrılır"
  ilkesi kaynağın gösterilebilmesini gerektiriyor.

### B2. Parça bazlı embedding önbelleği

Şu an önbellek **tüm korpusun** sağlamasıyla anahtarlanıyor. Tek bir dosyaya
tek satır eklemek 900 parçanın tamamını yeniden vektörletir. Anahtar parça
metninin sağlaması olmalı; değişmeyen parça yeniden vektörlenmez.

### B3. Embedding'i çalışma zamanından çıkar

Bu maddenin atlanması üretimde en pahalı hata olur:

`config.CACHE_DIR` Cloud Run'da **geçici disk**. Bugün korpus 12 parça olduğu
için görünmüyor; 900 parçada **her soğuk başlatma 900 embedding çağrısı**
demek — hem gecikme hem fatura, hem de ilk isteklerde arama sessizce anahtar
kelime moduna düşer.

Çözüm: embedding'ler derleme zamanında üretilip **imaja gömülür**
(`knowledge/embeddings/{lang}.npy` + parça sağlamaları). `scripts/build_embeddings.py`
+ Dockerfile adımı. Çalışma zamanında embedding üretimi yalnızca sorgu için
kalır.

### B4. numpy ile vektör arama

`_cosine` saf Python; her sorguda tüm parçalar üzerinde dönüyor. 900 parça ×
3.072 boyut ≈ 2,8 milyon çarpma → sohbet başına saniyeler. numpy zaten
bağımlılıkta (`requirements.txt:21`). Normalize edilmiş bir matris ile tek
`matmul`: milisaniyeler.

### B5. Teşhis ucu

`search_mode()` zaten var ve değerliydi (anlamsal aramanın anahtar kelimeye
düşmesi haftalarca fark edilmemişti). Yanına parça sayısı, vektör boyutu ve
embedding artefaktının yaşı eklenir. Korpus büyüdükçe "sessizce bozuldu" hâli
görünür olmalı.

**B'nin kabul ölçütü:** korpus 900 parçaya çıktığında soğuk başlatma süresi
değişmiyor, `search_mode()` `vector` diyor, arama gecikmesi < 50 ms.

### ✅ Faz B sonucu (2026-08-01)

| Ölçüt | Sonuç |
|---|---|
| Arama gecikmesi (900 parça × 3.072 boyut) | **0,2 ms** (saf Python: 266 ms — ~1300 kat) |
| Soğuk başlatmada embedding çağrısı | **0** (artefakt imajda) |
| Tek parça eklenince yeniden vektörlenen | **1** (önceden: tüm korpus) |
| Artefakt boyutu (900 parça tahmini) | ~11 MB `.npy` (JSON olsaydı ~55 MB) |
| `/health/rag` | mod, parça sayısı, kapsama, artefakt durumu |

Uygulama sırasında iki karar değişti:

- **Artefakt biçimi JSON değil `.npy` + küçük bir JSON künye.** JSON'da her
  float ~20 karakter tutuyor; 900 parça × 3.072 boyut 55 MB metin ederdi.
  float32 ikili biçimde aynı veri ~11 MB. Kitap gelmeden düzeltildi, sonradan
  yapılsaydı tüm korpusun yeniden vektörlenmesi gerekirdi.
- **Deploy betiği artık artefakt kapsamasını doğruluyor** (`--check`).
  Uyumsuzsa deploy durur; aksi halde üretimde sessizce yeniden vektörleme
  faturası çıkardı.

Ayrıca `_split_body` yazılırken çıkan bir kusur: örtüşme kuyruğu boyut
bütçesine sayılmıyordu, noktalamasız uzun pasajlarda üst sınır aşılıyordu.
Test yakaladı.

---

## Faz C — İlk kitap: *Tetrabiblos*

### Neden bu kitap

Batlamyus'un *Tetrabiblos*'u (MS 2. yy) Batı astrolojisinin gövdesi; sonraki
her şey ondan dallanıyor. Bizim için asıl önemlisi: içeriği **uygulamanın
hesapladığı şeyle birebir örtüşüyor** — gezegen doğaları, burç doğaları, açı
doktrini, ev anlamları, mizaç. Faz A'nın ürettiği olgular doğrudan bu metne
sorulabilir.

### Lisans — burada dikkatli olmak gerekiyor

Bir eserin kendisi kamu malı olsa bile **çevirisi ayrı bir telif taşır.**

- **J.M. Ashmand çevirisi (1822)** — kamu malı. Kullanılacak olan bu.
- **F.E. Robbins çevirisi (1940, Loeb)** — telifli. Kullanılamaz.
- Aynı tuzak I Ching'de de var: Wilhelm/Baynes çevirisi telifli.

Yapılacak ilk iş, ingest'ten önce **kaynak metnin baskısını ve lisans durumunu
doğrulamak** ve `knowledge/SOURCES.md` içine künyesini yazmak. Bu dosya ticari
bir üründe hukuki savunmanın kendisi.

### Türkçe tarafı

*Tetrabiblos*'un kamu malı bir Türkçe çevirisi yok. Üç seçenek değerlendirildi:

| Seçenek | Karar |
|---|---|
| Makine çevirisi | Hukuken sorunsuz (Ashmand kamu malı) ama kalite düşük ve ton tutmaz |
| Kamu malı Türkçe klasik (Marifetname, 1757) | Özgün metin kamu malı, ancak **modern transkripsiyonlar transkribe edenin telifini taşır**; ham Osmanlıca metin ayrı bir iş kolu |
| **Rytho'nun kendi Türkçe aktarımı** | **Seçilen.** Ashmand metninden bölüm bölüm bizim yazdığımız aktarım; telif bize ait, tonu kontrol ediyoruz |

Ayrıca doktrin birliği açısından da doğrusu bu: İngilizce kullanıcı Batlamyus,
Türkçe kullanıcı Marifetname okusaydı **aynı soruya iki farklı gelenekten**
cevap alırlardı. Marifetname kendi turunda, iki dile birden eklenmeli.

### Kapsam (ilk tur)

Tamamı değil, hesapladığımızla örtüşen kısım:

- **Kitap I** — gezegen doğaları, burç doğaları, üçgenler, açı doktrini
- **Kitap III**'ün ilgili bölümleri — mizaç, ruhun nitelikleri, ev anlamları

Yaklaşık 25–30 bin kelime → ~700–900 parça. Kitap II (ülke/iklim astrolojisi)
ve Kitap IV'ün büyük kısmı ürünle ilgisiz; alınmayacak.

### ✅ Faz C sonucu (2026-08-01)

Kaynak: Project Gutenberg #70850, Ashmand 1822. `ingest_tetrabiblos.py`
betiğiyle dönüştürüldü (elle düzenlenmedi — kapsam kararları kodda görünür ve
kaynak güncellenirse tekrar üretilebilir).

| Ölçüt | Öncesi | Sonrası |
|---|---|---|
| EN korpus | 13 parça / ~9 KB | **136 parça / ~105 KB** |
| TR korpus | 13 parça / ~9 KB | **33 parça / ~28 KB** |
| Alınan bölüm (EN) | — | 26 |
| Kapsam dışı | — | 30 (gerekçeleri betikte) |
| Vektör artefaktı | 0,2 MB | 1,6 MB (en) + 0,4 MB (tr) |
| Arama modu | vector | vector |

Türkçe tarafı **birebir çeviri değil, Rytho aktarımı**: kamu malı bir Türkçe
Tetrabiblos çevirisi yok, makine çevirisi de 1822 İngilizcesinden okunmaz bir
metin çıkarırdı. Aktarım hem telifi bize bırakıyor hem tonu kontrol
ettiriyor. Parça sayısı İngilizceden az çünkü aktarım daha yoğun — doktrin
kapsaması aynı, kelime sayısı değil.

Getirme kalitesi (gerçek sorgular, iki dilde):

| Sorgu | Dönen bölüm |
|---|---|
| "Saturn in the tenth house, career and vocation" | The Quality of Employment |
| "Mercury square Mars — how I think" | The Quality of the Mind |
| "Virgo ascendant, earth dominant, no air" | Signs and the Four Temperaments + The Triplicities |
| "Satürn onuncu evde, meslek ve kariyer" | Mesleğin Niteliği + Gezegenlerin Evleri |
| "Merkür Mars kare — nasıl düşündüğüm" | Aklın Niteliği + Fayda ve Zarar Verenler |
| "yükselenim Başak, toprak baskın, hiç hava yok" | Üçgenler — Dört Element + Burçların Mizaç Karşılıkları |

**Uygulama sırasında çıkan üç şey:**

1. **Korpus bir güvenlik yüzeyidir.** Ptolemaios'un ömür süresi, ölüm biçimi,
   hastalık ve servet bölümleri var. Bunları almak, yasak alan kapısını
   *arkadan delmek* olurdu: kapı kullanıcının SORUSUNU süzüyor, ama masum bir
   soruya getirilen "ölüm süresi" pasajı cevabı oraya sürükleyebilir. Yasak
   alan artık korpus seviyesinde de uygulanıyor — savunma iki katmanlı.
2. **Kaynağın tonu ürünün tonu değil.** Ptolemaios'un karakter tarifleri
   bugünün ölçüsüyle çok sert ("thoroughly depraved", "assassins"). Persona
   güçlendirildi: kaynağın ahlaki yargısı aktarılmaz, altındaki gözlem
   alınır. **Yağcılık yok ilkesi zor olanı söylemektir, birini aşağılamak
   değil.**
3. **Bölüm çeşitliliği gerekti.** Uzun bölümler çok parçaya bölündüğü için
   komşu parçalar benzer skor alıyor ve ilk iki sonucun ikisi de aynı
   bölümden çıkıyordu — 2 pasajlık bütçenin yarısı boşa gidiyordu. Arama artık
   farklı bölüm tercih ediyor.

**Ölçülen ama çözülmemiş:** sorgu embedding'i sohbet turuna **~0,8–1,4 sn**
ekliyor. Arama 0,2 ms; gecikme tamamen embedding API çağrısı. LRU önbelleği
yalnızca tekrar eden sorguları yakalıyor. Faz D/E'de ele alınacak.

### Alıntı ve atıf kuralı

Korpus parçaları prompt'a **bağlam** olarak giriyor, kullanıcıya doğrudan
gösterilmiyor. Yine de: model kaynağı kelimesi kelimesine aktarmamalı (persona
zaten "blok halinde aktarma" diyor), ve kaynak künyesi arayüzden erişilebilir
olmalı.

---

## Faz D — Haritadan sorgu üretme  ← asıl çarpan

Faz A ile Faz C'yi birleştiren madde. Tek başına en yüksek getirili olan bu.

Bugün RAG sorgusu **kullanıcının mesajının kendisi**. Kullanıcı "işimle ilgili
ne yapmalıyım?" yazdığında korpusta bu cümleye benzeyen bir şey aranıyor —
kadim metinde öyle bir cümle yok, dolayısıyla dönen pasaj ya alakasız ya boş.

Oysa artık kullanıcının haritasını biliyoruz. Aynı soru için gerçek sorgu şu
olmalı:

> Satürn onuncu evde, Oğlak · Mars Kare Güneş · transit Plüton Güneş'e kavuşum
> · toprak baskın, hava eksik — **meslek ve statü**

Yani: mesajın konusu (`_DOMAIN_TERMS` zaten bir konu sezgisi taşıyor) +
haritanın o konuyla ilgili faktörleri. Bu, korpustan gerçekten o kişiye ait
pasajı çeker.

### ✅ Faz D sonucu (2026-08-01)

`backend/services/chart_query.py`. Sorgu artık şöyle kuruluyor:

| Mesaj | Kurulan sorgu | Dönen bölüm |
|---|---|---|
| "İşimle ilgili ne yapmalıyım?" | *Mesleğin niteliği, iş, statü, rütbe. Merkür Başak 1. ev, Jüpiter Yengeç 10. ev… Güneş Kare Mars* | Mesleğin Niteliği (0,81) |
| "Why do I overthink everything?" | *The quality of the mind, manner of thinking… Moon Taurus house 9, Mercury Virgo house 1* | The Quality of the Mind (0,78) |

**Uygularken çıkan üç kusur — üçü de sessizdi:**

1. **Türkçe noktalı I.** `"İ".lower()` Python'da `"i"` değil, `"i" + U+0307`
   (birleşik nokta) veriyor. Sonuç: "İşimle ilgili…" diye başlayan bir
   mesajda `"iş"` kökü hiç eşleşmiyordu — yani RAG **hiç tetiklenmiyordu**.
   Türkçe cümleler büyük harfle başladığı için bu kenar durum değil; en sık
   sorulan kelimeler ("İşim", "İlişkim") tam buradan düşüyordu. Bu hata
   `prompt_composer.should_use_rag` içinde de vardı, yani Faz D'den önce de
   mevcuttu.
2. **Alt dizi eşleşmesi Türkçede yanlış.** "il**iş**kimde" içinde "iş"
   geçtiği için ilişki sorusu meslek konusunu tetikliyordu. Türkçe sondan
   eklemeli olduğundan kelime **başı** eşleşmesi doğru olan; İngilizcede ekler
   öne de geldiği için ("overthink" içinde "think") orada alt dizi kaldı.
3. **RAG kapısı fazla dardı.** "İşimle ilgili ne yapmalıyım?" 4 kelime olduğu
   için kısa sayılıp eleniyordu — oysa korpusta o soruya doğrudan cevap veren
   bir bölüm var. Konu tespiti artık kapıyı açıyor. ("timing" tek başına
   yeterli sayılmıyor: "bugün biraz keyifsizim" dönem sorusu değil.)

Yan fayda: sorgu artık aynı kullanıcı + aynı konu için **aynı metni** üretiyor,
yani sorgu embedding önbelleği gerçekten çalışıyor. Ham kullanıcı mesajları
neredeyse hiç tekrar etmediği için o önbellek pratikte hiç isabet etmiyordu.

### ✅ Faz E sonucu (2026-08-01)

**Bütçe ölçülerek değiştirildi.** 280 karakter, ortalama 907 karakterlik bir
parçanın **%68'ini** atıyordu — ve artık atılan şey alakasız değil, doğru
bulunmuş pasajdı. `MAX_PASSAGE_CHARS` 280 → **700**. Pasaj sayısı 2'de kaldı:
üçüncü kaynak odağı dağıtıyor ve persona zaten "en fazla tek bir ayrıntıyı
sindir" diyor.

**İlgililik tabanı eklendi (0,62).** Ölçüm: korpusta karşılığı olan sorgular
0,71–0,84 alıyor, hiç ilgisi olmayanlar ("wifi şifremi nasıl sıfırlarım")
0,49–0,56'da kalıyor. Eşik olmadan alakasız soruda da en yakın pasaj dönüyor
ve model kadim bir metni ilgisiz bir konuya bağlamaya çalışıyordu. Kaynak
yoksa kaynaksız cevap vermek daha dürüst. (Yalnızca vektör modunda; anahtar
kelime skorları tamamen farklı ölçekte.)

**Jeneriklik ölçüldü:** `backend/scripts/eval_genericness.py` (LLM çağırdığı
için CI testi değil, elle çalıştırılır).

| Ölçüt | Persona sıkılaştırmadan önce | Sonra |
|---|---|---|
| Cevap başına adıyla anılan **kendi haritasına ait** olgu | 2,3 | **2,7** |
| Hiç olgu anmayan cevap | 2 / 12 | **0 / 12** |
| Haritalar arası olgu örtüşmesi | %0 | **%0** |
| Yasak alan sızıntısı | 0 | **0** |

**Olgu örtüşmesinin %0 olması asıl sonuç:** hiçbir iki harita aynı yerleşimi
anmıyor, yani her cevap kendi haritasından konuşuyor. Jeneriklik tam olarak
bunun tersiydi.

İki dürüstlük notu:

- **Kosinüs benzerliği ölçüsü zayıf çıktı.** Taban 0,81 – tavan 0,87, yani
  dinamik aralık sadece 0,06. Aynı alanda, aynı uzunlukta, aynı tonda
  yazılmış iki Türkçe paragraf içerikleri farklı olsa da yüksek benzerlik
  alıyor. Bu ölçüden çıkan "%69 jenerik" rakamı yanıltıcı; olgu örtüşmesi
  çok daha ayırt edici ve o yüzden asıl gösterge olarak o alındı.
- **Ölçüm aracının kendisinde bir kusur çıktı:** yağcılık/yasak alan
  taraması düz alt dizi arıyordu ve `"hisse"` kalıbı
  `"hissedebileceğini"` içinde eşleşip **6 sahte sızıntı** raporlamıştı.
  Kelime sınırıyla arama yapılınca gerçek sayı **0** çıktı. Bu, Faz D'de
  düzeltilen "iliş**ki**/iş" hatasıyla aynı sınıf.

### Faz D — tasarım notları

Gerektirdikleri:

- Konu → ev/gezegen eşlemesi (meslek → 10. ev + Satürn; ilişki → 7. ev +
  Venüs; para → 2./8. ev). Küçük, denetlenebilir bir tablo — LLM'e sordurmak
  hem maliyet hem belirsizlik.
- Sorgu **korpusun dilinde** kurulmalı; kullanıcının dilinde değil. Faz A'nın
  anahtar tabanlı olgu sözlüğü tam da bunu mümkün kılıyor.
- Sorgu embedding'i önbelleklenebilir olsun diye normalize edilmeli.

---

## Faz E — Enjeksiyon bütçesi

`MAX_PASSAGES = 2`, `MAX_PASSAGE_CHARS = 280` → toplam 560 karakter. Bu sayılar
13 parçalık bir korpus için konmuştu ve gerçek bir kitapla anlamsız.

Ama kör bir büyütme de doğru değil: blok her sohbet turunda gidiyor, doğrudan
maliyet. Faz D uygulandıktan **sonra**, gelen pasajların ilgililik skoruna
bakarak ayarlanmalı — alakasız pasajı büyütmek cevabı iyileştirmez, sadece
pahalılaştırır.

Ölçüm önce, sayı sonra.

---

## Kalite nasıl ölçülecek

"Daha iyi oldu" yeterli değil. Somut bir jeneriklik ölçütü:

**Değiştirilebilirlik testi.** Aynı soruyu iki farklı harita için sor. Cevaplar
birbirinin yerine geçebiliyorsa hâlâ jeneriktir. Bir dizi (soru × harita)
çifti için cevapların ayrışması ölçülür.

Buna ek olarak korunacak regresyonlar:

- Prompt'ta olmayan bir konum/açı/transit cevapta geçmemeli (uydurma denetimi).
- İngilizce cevapta Türkçe kalıntı olmamalı (mevcut bekçi genişletildi).
- Harita bloğu karakter bütçesini aşmamalı (test var).

---

## Yapılmayacaklar ve neden

- **Fine-tuning.** Yanlış araç. Üslup öğretir, olgu öğretmez; binlerce eşleşme
  ister; bilgiyi güvenilir biçimde saklamaz ve kaynağı gösterilemez.
  Doğru iş RAG'i beslemek ve bütçeyi açmak.
- **Telif riskli kitaplar.** Modern çeviriler (Robbins, Wilhelm/Baynes) ve
  güncel telifli eserler ticari bir üründe gerçek risk. Kamu malı klasikler ve
  kendi yazdığımız sentez güvenli zemin. `knowledge/SOURCES.md` bunun kaydı.
- **Kitabın tamamını almak.** Ürünle ilgisiz bölümler arama uzayını kirletir
  ve alakasız pasaj döndürme olasılığını artırır.

---

## Sıra ve gerekçesi

```
A (bitti) → B (altyapı) → C (kitap) → D (haritadan sorgu) → E (bütçe)
```

B, C'den önce çünkü kitabı önce koymak her düzeltmede tüm korpusu yeniden
vektörletir. D, C'den sonra çünkü çekecek bir şey olmadan sorgu iyileştirmenin
anlamı yok. E en sonda çünkü ayarlanacak sayı ölçüme dayanmalı.
