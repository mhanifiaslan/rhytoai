# Rytho Gizlilik Politikası

Son güncelleme: 5 Ağustos 2026

Rytho ("Uygulama"), kişisel kozmik içgörü deneyimi sunan bir mobil uygulamadır.
Bu politika, 6698 sayılı Kişisel Verilerin Korunması Kanunu (KVKK) ve Avrupa
Birliği Genel Veri Koruma Tüzüğü (GDPR) çerçevesinde hangi verileri neden
işlediğimizi, ne kadar sakladığımızı ve haklarınızı açıklar.

## 1. İşlenen veriler ve amaçları

### a) Hesap bilgileri
- **Ne:** Ad, e-posta adresi ve varsa profil fotoğrafı (e-posta, Google veya
  Apple ile giriş üzerinden).
- **Neden:** Hesabınızı oluşturmak, oturumunuzu doğrulamak ve profilinizi
  göstermek için.

### b) Doğum verisi
- **Ne:** Doğum tarihi, saati (biliniyorsa), şehri ve tercihe bağlı cinsiyet
  bilgisi.
- **Neden:** Astroloji (natal harita), BaZi, I Ching bağlamı ve günlük okuma
  hesaplamaları yalnızca bu verilerle yapılabilir. Doğum verisi, yorum üretimi
  amacıyla sunucularımızda işlenir ve profilinizde saklanır. Bu veriler reklam
  veya profilleme amacıyla üçüncü taraflarla paylaşılmaz.

### c) Yüz okuma (firaset) ölçümleri
- **Ne:** Yüz okuma özelliğini açıkça onaylayıp kullandığınızda, yüzünüzün
  CİHAZINIZDA ölçülen sayısal oranları.
- **ÖNEMLİ:** Yüz fotoğrafınız veya kamera görüntünüz **cihazınızdan hiç
  çıkmaz; sunucuya yüklenmez, hiçbir yerde saklanmaz.** Ölçüm tamamen
  telefonunuzda yapılır; sunucuya yalnızca isimsiz sayısal oran ölçümleri
  gönderilir ve yorum üretiminde kullanılır. Özellik, ayrı bir biyometrik
  rıza onayı olmadan çalışmaz; onayı istediğiniz zaman geri çekebilirsiniz.

### d) Sosyal veriler
- **Ne:** Kullanıcı adınız, arkadaşlık ilişkileriniz, kapalı bir kümeden
  seçilen hazır tepkiler ve (açarsanız) günlük seri görünürlüğünüz.
- **Neden:** Arkadaş listesi, günlük ikili okuma ve tepki özelliklerinin
  çalışması için. Uygulamada serbest metinli gönderi, yorum veya birebir
  mesajlaşma **yoktur**; diğer kullanıcılara yalnızca yukarıdaki sınırlı
  bilgiler görünür.

### e) Telefon numarası ve rehber eşleşmesi (isteğe bağlı)
- **Ne:** Telefonunuzu doğrularsanız numaranızın geri döndürülemez özeti
  (SHA-256); rehber eşleşmesini AÇARSANIZ rehberinizdeki numaraların aynı
  yöntemle özetleri.
- **Neden:** Arkadaşlarınızı bulabilmeniz için. **Ham telefon numaraları
  sunucuda saklanmaz**; rehber özetleri yalnızca eşleşme anında geçici olarak
  işlenir, kaydedilmez. Ad-soyad bilgisi rehberden okunmaz.

### f) Sohbet ve hafıza
- **Ne:** Rytho ile konuşmalarınız ve bu konuşmalardan damıtılmış kısa
  içgörüler.
- **Neden:** Kaldığınız yerden devam edebilmeniz ve yorumların sizi tanıması
  için. 30 gün boyunca açılmayan konuşmalar otomatik silinir.

### g) Teknik veriler
- **Ne:** Çökme kayıtları (Firebase Crashlytics), anonim kullanım olayları
  (Firebase Analytics), bildirim jetonu (FCM), satın alma durumu (RevenueCat).
- **Neden:** Uygulama kararlılığını iyileştirmek, bildirim gönderebilmek ve
  aboneliğinizi tanıyabilmek için.

## 2. Yapay zeka ile işleme

Okumalar ve sohbet yanıtları, Google Gemini modeli ile üretilir. Bu amaçla
doğum haritası özetiniz ve sorularınız Google Cloud altyapısında işlenir.
Konuşmalarınızın ham dökümleri kalıcı hafızaya alınmaz; yalnızca damıtılmış
kısa içgörüler saklanır. Üretilen yorumlar **eğlence ve kişisel içgörü
amaçlıdır; tıbbi, hukuki, finansal veya psikolojik tavsiye niteliği taşımaz.**

## 3. Alt işleyiciler

Verileriniz aşağıdaki hizmet sağlayıcıların altyapısında barındırılır ve
işlenir:

- **Google Firebase** (kimlik doğrulama, veritabanı, bildirim, analitik,
  çökme raporları) — Google LLC
- **Google Cloud Platform / Cloud Run** (hesaplama ve yapay zeka servisi,
  us-central1 bölgesi) — Google LLC
- **RevenueCat** (abonelik ve satın alma durumunun yönetimi; ödeme kartı
  bilgileriniz bize veya RevenueCat'e değil, Google Play / App Store'a
  verilir) — RevenueCat, Inc.

Google'ın veri işleme koşulları: https://cloud.google.com/terms/data-processing-addendum

## 4. Saklama süreleri

- Hesap ve doğum verisi: hesabınız silinene kadar.
- Yüz görüntüsü: **hiç toplanmaz** (ölçüm cihazda; sunucuda yalnız sayısal
  oranlar ve metin yorum).
- Konuşmalar: son açılıştan 30 gün sonra otomatik silinir; hesap silmede
  tamamı silinir.
- Sosyal veriler: siz kaldırana veya hesabınız silinene kadar.
- Çökme/analitik kayıtları: Firebase'in standart saklama süreleri (en fazla
  90 gün ham veri).

## 5. Haklarınız ve veri silme

KVKK m.11 ve GDPR kapsamında verilerinize erişme, düzeltme, silme, işlemeye
itiraz etme ve taşınabilirlik haklarına sahipsiniz.

**Veri silme:** Hesabınızı uygulama içinden (Profil → Hesap → Hesabı sil)
anında silebilirsiniz; tüm verileriniz bu işlemle kalıcı olarak kaldırılır.
Dilerseniz **aslan.mh@gmail.com** adresine kayıtlı e-posta adresinizden
yazabilirsiniz; talebiniz en geç 30 gün içinde sonuçlandırılır.

## 6. Çocukların gizliliği

Rytho 13 yaş altı kullanıcılara yönelik değildir. 13 yaşından küçük olduğunu
öğrendiğimiz kullanıcıların hesapları silinir.

## 7. Değişiklikler

Bu politika güncellendiğinde uygulama içinden duyurulur. Sorularınız için:
**aslan.mh@gmail.com**
