# İnceleme Notları ve Guideline 4.3 Savunması

Astroloji, App Store'da en çok reddedilen kategorilerden biri. Baskın red
gerekçesi **Guideline 4.3 (Design — Spam)**: "aynı şablondan üretilmiş,
birbirinden ayrışmayan uygulama". Bu belge iki işi yapıyor:

1. İnceleme ekibine yazılacak notun kendisi (§3, kopyalanabilir).
2. O notun her cümlesinin **kodda nerede karşılığı olduğu** (§2) — çünkü
   savunma ancak doğruysa işe yarar.

---

## 1. Neden 4.3 riski var

Kategoride çok sayıda uygulama şunu yapıyor: doğum tarihini alıp bir tabloya
bakıyor, önceden yazılmış 12 metinden birini gösteriyor. Bunlar birbirinden
ayrışmadığı için Apple tek bir şablon ailesi olarak görüyor.

Bizim ayrıştığımız yerler aşağıda. Hepsi **iddia değil, kodda doğrulanabilir**
— inceleme ekibi soru sorarsa dosya gösterilebilir.

---

## 2. Ayırt edici unsurlar ve kanıtları

### 2.1 Gerçek efemeris hesabı — tablo değil

Gezegen konumları, açılar, retro durumları ve ay evresi **Swiss Ephemeris** ile
milisaniye hassasiyetinde hesaplanıyor. Hiçbir gök verisi modele tahmin
ettirilmiyor.

- `backend/services/sky_service.py` — `swe.calc_ut` ile anlık konumlar
- `backend/services/astro_service.py` — natal harita, evler, açılar (kerykeion)
- `backend/services/bazi_service.py` — BaZi ay sütunları **gerçek güneş
  terimlerine** (Jie Qi) göre; Güneş'in ekliptik boylamı hesaplanıyor
- NASA JPL Horizons'tan gezegen uzaklıkları (günlük önbellekli)

> Karşılaştırma noktası: kategorideki tipik uygulama yalnızca güneş burcunu
> bilir. Rytho ay, yükselen, ev yerleşimleri ve o günün gerçek açılarıyla
> çalışır.

### 2.2 Zamanla öğrenen kullanıcı hafızası

Sohbetten **yapılandırılmış olgular** damıtılıyor ve sonraki okumalara bağlam
olarak giriyor. Ham transkript saklanmıyor.

- `backend/services/memory_extractor.py` — arka planda, kotalı çıkarım
- `backend/services/memory_service.py` — kapalı kategori kümesi, en fazla 40 olgu
- `backend/services/prompt_composer.py` — hafıza "arka plan fısıltısı" olarak
  iliştirilir, blok hâlinde dökülmez

Sonuç: iki kullanıcı aynı burçta olsa bile aynı metni almaz.

### 2.3 Yasak alan kapısı — modele hiç gitmeyen kesin engel

Sağlık, hamilelik, ölüm ve finans sorularında model **çağrılmıyor**; sabit ve
şeffaf bir yanıt dönüyor.

- `backend/services/safety_rules.py` — iki dilde konu + talep eşleşmesi
- `backend/tests/test_safety_rules.py` — yakalanması ve yakalanmaması
  gerekenler ayrı ayrı test ediliyor

> Kapı bilinçli olarak **dar**: engellenmek için hem yasak konu hem cevap
> talebi gerekiyor. "Annem hasta, üzgünüm" engellenmez — teselli arayan
> kullanıcıyı duvara çarptırmak, yasak soruyu cevaplamaktan daha büyük hata.

### 2.4 Serbest metin içermeyen sosyal katman

Kullanıcılar birbirine **yalnızca kapalı bir kümeden** tepki gönderebilir.
Gönderi, yorum, DM, profil biyografisi yok.

- `infra/firestore.rules` — `nudges` kuralı 12 anahtarlı kapalı kümeyi zorunlu kılar (R3-4 genişlemesi)
- `apps/mobile/lib/core/friends.dart` — `kReactions`

Bu, App Store 1.2 (UGC) yükümlülüklerini ve DSA moderasyon operasyonunu
kapsam dışında bırakıyor. **Beyanda "kullanıcı üretimi içerik: hayır"
işaretlenmelidir.**

### 2.5 Üç ayrı geleneğin tek hesap altyapısında birleşmesi

Batı astrolojisi, BaZi (Dört Sütun) ve I Ching. **Üçü de** gerçek hesaba
dayanıyor: ilk ikisi Swiss Ephemeris efemerisiyle, I Ching çekimi gerçek
olasılık dağılımıyla (yarrow oranları).

Mizaç/temperament bunlardan **ayrı bir sistem değil**: Batı haritasındaki
element dağılımının (geleneksel yedili + Yükselen) klasik adlandırması.
Bağımsız bir mizaç motoru yok; ad, ölçülen dağılımdan türetiliyor ve
yalnız kişisel raporda geçiyor — genel burç yorumunda asla. (Daha önce
bu bölüm "dört gelenek" diyor ve "üçü de" diye sayıyordu; ikisi de
yanlıştı.)

### 2.6 Yağcılık yapmayan persona

Ürün ilkesi: zor dönem zor denir. Persona talimatında açıkça yazılı ve testle
korunuyor.

- `backend/services/prompts/tr.py`, `en.py` — "POHPOHLAMA YOK" / "NO FLATTERY"
- `backend/tests/test_safety_rules.py::test_persona_pohpohlamayi_yasaklar`

### 2.7 İki dilde ayrı persona — çeviri değil

Türkçe ve İngilizce personalar birbirinin çevirisi değil; her dil kendi
metnini taşıyor. Dil sızıntısına karşı ayrı bir muhafız test dosyası var.

- `backend/services/prompts/` — dil başına modül
- `backend/tests/test_language_isolation.py`

---

## 3. İnceleme ekibine yazılacak not (kopyalanabilir)

> **App Review Notes**
>
> Rytho is an astrology and ancient-wisdom app. We are aware that this
> category is crowded, so here is what makes this app substantively
> different from template-based horoscope apps:
>
> 1. **Real ephemeris computation.** Planetary positions, aspects,
>    retrogrades and lunar phases are computed with the Swiss Ephemeris at
>    millisecond precision — nothing is looked up from a static table and
>    nothing is invented by the language model. The BaZi engine derives month
>    pillars from true solar terms (Jie Qi), not from calendar months.
> 2. **The app learns the user.** Structured facts distilled from
>    conversation feed later readings, so two users with the same sun sign do
>    not receive the same text. Raw transcripts are never stored.
> 3. **A hard safety gate.** Questions about health, pregnancy, death or
>    finance never reach the model; a fixed, transparent response is returned
>    instead. This is deterministic code, not a prompt instruction.
> 4. **No user-to-user free text.** Users can only send each other
>    reactions from a fixed set of 12. There are no posts, comments,
>    direct messages or bios, so there is no moderation surface between
>    users. (Users do write free text privately — AI chat and a personal
>    diary — but it is never shown to any other user.)
> 5. **No flattery by design.** The persona is instructed to name a difficult
>    period as difficult rather than reassure, and this is enforced by tests.
>
> **Test account:** `<E-POSTA>` / `<PAROLA>`
> The account already has completed onboarding and an active Rytho+
> entitlement, so every screen is reachable.
>
> **Suggested walkthrough**
> - *Sky tab* — the daily reading is generated from today's actual sky; the
>   moon phase and retrograde chips reflect live computation.
> - *Atlas tab* — the full natal chart: placements, houses and aspects.
> - *Oracle → BaZi* — Four Pillars from true solar terms.
> - *Chat* — ask "what does my Mercury retrograde mean". Then ask
>   "will my illness get better?" to see the safety gate return a fixed
>   response without calling the model.
> - *Profile → Notifications* — per-type toggles and quiet hours.
> - *Profile → Delete account* — in-app account deletion, as required by
>   5.1.1(v).
>
> **Purchases.** A single monthly auto-renewing subscription. Renewal terms,
> price, cancellation instructions and links to the Terms and Privacy Policy
> are all on the purchase screen.
>
> **Content framing.** Readings are presented as insight, not prediction. The
> app explicitly refuses medical, legal and financial questions. The purchase
> screen and the Terms of Use both state that astrological inference is a
> traditional practice and not a scientifically validated method of
> prediction.

---

## 4. Diğer risk noktaları

### 4.1 Guideline 5.3.1 — Gambling, gaming, lotteries

**Uygulanmıyor.** Uygulama kumar, çekiliş, yarışma veya para ödülü içermiyor.
I Ching çekimi bir para/ödül mekaniği değil, sembolik bir okuma.

### 4.2 Guideline 1.2 — User-Generated Content

**Uygulanmıyor.** Serbest metin yok (§2.4). Yine de şikayet ve engelleme
akışları mevcut — kapalı küme içinde bile taciz mümkün olabilir.

- `apps/mobile/lib/core/safety.dart`

### 4.3 Guideline 3.1.1 — In-App Purchase

Dijital içerik yalnızca uygulama içi satın almayla açılıyor; harici ödeme
bağlantısı yok.

### 4.4 Guideline 5.1.1(v) — Account Deletion

Uygulama içinden hesap silme mevcut: **Profil → Hesabı sil**. Menü arkasında
gizli değil, ana profil ekranında. Ne silineceği ve ne silinmeyeceği
(şikayet kayıtları) açıkça yazılı; abonelik iptalinin ayrı yapılması gerektiği
uyarısı var.

- `apps/mobile/lib/features/profile/delete_account.dart`
- `backend/services/account_service.py`

### 4.5 Sağlık iddiası riski

Uygulama hiçbir sağlık iddiasında bulunmuyor ve sağlık sorularını açıkça
reddediyor (§2.3). Mağaza açıklamasında **"iyileştirir", "tedavi", "şifa"
gibi kelimeler kullanılmamalıdır.**

---

## 5. Yayın öncesi kontrol

- [ ] Test hesabı oluşturuldu, onboarding tamamlandı, Rytho+ yetkisi verildi
- [ ] Yukarıdaki not App Store Connect → App Review Information'a yapıştırıldı
- [ ] Ekran görüntülerinde gerçek harita ve gerçek gökyüzü verisi görünüyor
      (şablon görsel değil — 4.3 savunmasının görsel karşılığı)
- [ ] Mağaza açıklamasında sağlık/kesin kehanet iddiası yok
- [ ] `docs/store-privacy-labels.md` beyanı iki konsola da girildi
