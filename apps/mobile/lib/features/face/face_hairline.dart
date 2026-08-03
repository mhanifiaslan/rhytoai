/// Saç çizgisi — **segmentasyon maskesinden**.
///
/// ## Neden bu dosya iki kez yazıldı
///
/// Üst bölge, ML Kit yüz konturunun en üst noktası "alın üstü" sayılarak
/// hesaplanıyordu. Gerçek bir yüzde ölçülen:
///
///     üst 0,17   orta 0,40   alt 0,42      (klasik San Ting ~0,33 bekler)
///
/// Alın olması gerekenin yarısı çıkıyordu. Payda da o noktadan hesaplandığı
/// için hata orta ve alt bölgeyi de şişiriyor, sunucu "kısa alın + baskın
/// orta + baskın alt" gibi birbiriyle çelişen üç iddia üretiyordu.
///
/// İlk düzeltme denemesi alın bölgesinin **parlaklık profilinde** ten→saç
/// geçişi arıyordu. Sinyal işleme sezgisiydi ve aynı yüzde iki farklı karede
/// 0,17 ve 0,41 verdi — yani kararsızdı. Kel kafada, kâkülde ve açık renk
/// saçta sessizce çuvallıyordu.
///
/// Artık karar eğitilmiş bir modelin sınıf maskesinden çıkıyor
/// (bkz. `face_segmentation.dart`).
///
/// ## Kel kafa bir başarısızlık değil, farklı bir geometri
///
/// Maske "saç yok, yüz teni doğrudan arka plana çıkıyor" diyorsa kafatası
/// tepesi ölçülebiliyor demektir. Önceki sürüm bunu "geçiş yok → ölçemedim"
/// diye okuyordu; aletin körlüğünü verinin yokluğu sanmak.
///
/// Üç sonuç var ve üçü de bilgi:
///
/// * [HairlineKind.hairline] — saç sınırı bulundu, klasik San Ting geçerli.
/// * [HairlineKind.crown] — saç yok; kafatası tepesinden ölçüldü. Gelenek
///   saç çizgisini varsayar ve kel bir kafada o çizgi geri getirilemez, bu
///   yüzden okuma **nereden ölçüldüğünü söylemek zorunda**.
/// * `null` — alın örtülü (kâkül, şapka) ya da maske güvenilmez. Bu durumda
///   susmak yetmez: kullanıcıya "alnını aç" denir ve ölçüm tekrarlanır.
library;

import 'dart:math' as math;
import 'dart:ui';

import 'face_segmentation.dart';

/// Ölçümün neye dayandığı.
enum HairlineKind {
  /// Saç sınırı bulundu.
  hairline,

  /// Saç yok; kafatası tepesi kullanıldı (kel ya da tıraşlı).
  crown,
}

class Hairline {
  const Hairline({
    required this.y,
    required this.kind,
    required this.confidence,
  });

  /// Görüntü uzayında dikey konum.
  final double y;
  final HairlineKind kind;

  /// 0..1 — sınırın ne kadar temiz olduğu.
  final double confidence;
}

/// Şeridin genişliği (yüz genişliğine oranla).
///
/// Alnın ortası kullanılıyor: şakaklar saçla erken kesişiyor ve sınırı
/// olduğundan aşağıda gösteriyor.
const double kStripWidth = 0.34;

/// Bir satırın "yüz teni" sayılması için gereken oran.
const double kSkinMajority = 0.6;

/// Bir satırın "saç" ya da "arka plan" sayılması için gereken oran.
const double kAboveMajority = 0.5;

/// Alın örtülü sayılması için kaşın hemen üstünde aranan saç oranı.
const double kOccludedThreshold = 0.5;

/// Sınırın kullanılabilmesi için gereken EN AZ güven.
///
/// Bu eşik model kartındaki bir ölçüme dayanıyor ve keyfi değil. MediaPipe
/// Selfie Multiclass'ın ten tonu değerlendirmesinde en kötü durum ortalama
/// IoU **71,86**, veri kümesi ortalaması **81,10** — yani ~9 puanlık bir
/// fark var. Google kendi ölçütüne göre (bir standart sapma içinde) bunu
/// "adil" sayıyor, ama pratikte şu demek: **maske bazı ten tonlarında daha
/// az isabetli.**
///
/// Kişisel bir okuma üreten üründe bu bilinerek tasarlanmalı. Sınır bulanık
/// çıktığında ölçümü kullanmak, bazı kullanıcılara sistematik olarak daha
/// yanlış bir alın oranı vermek olurdu. Bulanıksa ölçüm yapılmıyor ve üst
/// bölge hiç gönderilmiyor — okuma ölçebildiği eksenlerin üstünde duruyor.
const double kMinConfidence = 0.72;

/// Maskeden saç çizgisini çıkarır.
///
/// [browY], [chinY], [axisX], [faceWidth] landmark uzayında; [imageSize] o
/// uzayın boyutu. Maske farklı çözünürlükte olabildiği için ölçekleme burada
/// yapılıyor — koordinat uzaylarını karıştırmak bu projede defalarca sessiz
/// kusura yol açtı.
Hairline? hairlineFromMask({
  required SegmentationMask mask,
  required Size imageSize,
  required double browY,
  required double chinY,
  required double axisX,
  required double faceWidth,
}) {
  if (imageSize.width < 1 || imageSize.height < 1) return null;
  final altYukseklik = chinY - browY;
  if (altYukseklik < 8 || faceWidth < 8) return null;

  final olcekX = mask.width / imageSize.width;
  final olcekY = mask.height / imageSize.height;

  final mBrow = browY * olcekY;
  final yariGenislik = math.max(1, (faceWidth * kStripWidth / 2 * olcekX).round());
  final mAxis = (axisX * olcekX).round();

  /// Bir satırdaki sınıf oranları.
  (double ten, double sac, double arka) satir(int my) {
    var ten = 0;
    var sac = 0;
    var arka = 0;
    var toplam = 0;
    for (var x = mAxis - yariGenislik; x <= mAxis + yariGenislik; x++) {
      if (x < 0 || x >= mask.width) continue;
      final c = mask.at(x, my);
      if (c == SegClass.faceSkin) ten++;
      if (c == SegClass.hair) sac++;
      if (c == SegClass.background) arka++;
      toplam++;
    }
    if (toplam == 0) return (0, 0, 0);
    return (ten / toplam, sac / toplam, arka / toplam);
  }

  // Kaşın hemen üstü ten olmalı. Değilse alın örtülü demektir ve ölçüm
  // yapılamaz — ama bu kullanıcıya söylenebilir bir durum, sessiz bir
  // başarısızlık değil.
  final kasUstu = (mBrow - altYukseklik * 0.12 * olcekY).round();
  final (tenKas, sacKas, _) = satir(kasUstu.clamp(0, mask.height - 1));
  if (sacKas > kOccludedThreshold) return null;
  if (tenKas < 0.25) return null;

  // Sınırın üstünde bakılacak bant yüksekliği.
  //
  // Karar TEK SATIRA bakarak veriliyordu ve cihazda kırılgan çıktı: aynı
  // yüzde üç çekimin ikisi "ölçülemedi" döndü, tutan da eşiğin hemen
  // üstündeydi (0,78). Sebep saç sınırının kademeli olması — o satırda saç
  // telleri ile alın derisi karışık ve ne saç ne arka plan çoğunluğu
  // tutturabiliyor.
  //
  // Bandın ORTALAMASI hem daha kararlı hem daha anlamlı: güven değeri artık
  // tek gürültülü satırın değil, sınırın üstündeki bölgenin ne olduğunun
  // ölçüsü.
  final bant = math.max(3, (altYukseklik * 0.12 * olcekY).round());

  // Alından yukarı yürü, tenin bittiği ilk satırı bul.
  final ustSinir = math.max(0, (mBrow - altYukseklik * 1.6 * olcekY).round());
  for (var my = kasUstu; my >= ustSinir; my--) {
    final (ten, _, _) = satir(my);
    if (ten >= kSkinMajority) continue;

    // Ten bitti. ÜSTÜNDE ne var? Bu, iki durumu ayıran soru.
    var sacTop = 0.0;
    var arkaTop = 0.0;
    var adet = 0;
    for (var b = my; b > my - bant && b >= 0; b--) {
      final (_, s, a) = satir(b);
      sacTop += s;
      arkaTop += a;
      adet++;
    }
    if (adet == 0) return null;

    final sacOrt = sacTop / adet;
    final arkaOrt = arkaTop / adet;
    final baskin = sacOrt >= arkaOrt;
    final guven = (baskin ? sacOrt : arkaOrt).clamp(0.0, 1.0);

    if (guven < kMinConfidence) return null;
    return Hairline(
      y: my / olcekY,
      kind: baskin ? HairlineKind.hairline : HairlineKind.crown,
      confidence: guven,
    );
  }

  return null;
}
