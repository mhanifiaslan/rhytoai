/// Yüz geometrisi — tespit edilen noktalardan **türetilmiş oranlar**.
///
/// Bu dosyanın varlık sebebi mimari bir karardır: **fotoğraf cihazdan
/// çıkmaz.** Tespit cihaz üstünde yapılır, buradaki oranlar hesaplanır ve
/// sunucuya yalnızca **sayılar** gider — görüntü değil, landmark koordinatı
/// değil, yalnızca birbirine bölünmüş uzunluklar.
///
/// Bunun üç sonucu var:
///
/// 1. **Biyometrik veri iletilmiyor ve saklanmıyor.** Buradan çıkan sayılar
///    kişiyi tanımaya yaramaz: "alın/orta yüz oranı 0.94" milyonlarca insanda
///    aynıdır. Ham landmark kümesi gönderilseydi durum başka olurdu — o,
///    kişiye özgü bir imzadır.
/// 2. **Ekranda gördüğün noktalar gerçek.** Tarama animasyonu sunucuyu
///    bekleseydi, ağ turu boyunca sahte nokta oynatmak gerekirdi. Uygulama
///    kendi hesabı hakkında yalan söylemiş olurdu.
/// 3. **Hesaplanan ile yorumlanan ayrı kalır.** Buradaki her sayı ölçümdür;
///    yorum sunucuda, kadim metne dayanarak yapılır.
library;

import 'dart:math' as math;
import 'dart:ui';

/// Yüz tespitinden gelen ve oran hesabı için gereken noktalar.
///
/// ML Kit'in kontur kümesinden yalnızca ihtiyacımız olanlar alınır. Tüm
/// koordinatlar görüntü uzayındadır (piksel).
class FaceLandmarks {
  const FaceLandmarks({
    required this.faceOval,
    required this.foreheadTop,
    required this.browMid,
    required this.noseBase,
    required this.chin,
    required this.cheekLeft,
    required this.cheekRight,
    required this.jawLeft,
    required this.jawRight,
    required this.mouthLeft,
    required this.mouthRight,
    required this.upperLip,
    required this.lowerLip,
    required this.eyeLeft,
    required this.eyeRight,
    this.headAngleZ = 0,
    this.headAngleY = 0,
  });

  /// Yüz ovalinin tüm kontur noktaları — animasyonda çizilen şey budur.
  final List<Offset> faceOval;

  final Offset foreheadTop;
  final Offset browMid;
  final Offset noseBase;
  final Offset chin;
  final Offset cheekLeft;
  final Offset cheekRight;
  final Offset jawLeft;
  final Offset jawRight;
  final Offset mouthLeft;
  final Offset mouthRight;
  final Offset upperLip;
  final Offset lowerLip;
  final Offset eyeLeft;
  final Offset eyeRight;

  /// Başın eğimi (derece). Çerçeveleme kalitesi için.
  final double headAngleZ;
  final double headAngleY;
}

/// Sunucuya gidecek olan şey: yalnızca oranlar.
class FaceRatios {
  const FaceRatios({
    required this.upperThird,
    required this.middleThird,
    required this.lowerThird,
    required this.widthToHeight,
    required this.jawToCheek,
    required this.mouthToFaceWidth,
    required this.lipFullness,
    required this.eyeSpacing,
    required this.symmetry,
  });

  /// San Ting — üç bölge yüksekliğinin yüze oranı. Toplamları ~1.0.
  final double upperThird;
  final double middleThird;
  final double lowerThird;

  /// Yüz en/boy oranı. Yüksek = geniş/yuvarlak, düşük = uzun/ince.
  final double widthToHeight;

  /// Çene genişliğinin elmacık genişliğine oranı. Düşük = sivri çene.
  final double jawToCheek;

  /// Ağız genişliğinin yüz genişliğine oranı.
  final double mouthToFaceWidth;

  /// Dudak kalınlığının yüz yüksekliğine oranı.
  final double lipFullness;

  /// Gözler arası mesafenin yüz genişliğine oranı.
  final double eyeSpacing;

  /// Sol-sağ simetri (1.0 = tam simetrik). Hiçbir yüz tam simetrik değildir;
  /// 0.9 altı belirgin asimetri sayılır.
  final double symmetry;

  Map<String, double> toJson() => {
        'upperThird': _yuvarla(upperThird),
        'middleThird': _yuvarla(middleThird),
        'lowerThird': _yuvarla(lowerThird),
        'widthToHeight': _yuvarla(widthToHeight),
        'jawToCheek': _yuvarla(jawToCheek),
        'mouthToFaceWidth': _yuvarla(mouthToFaceWidth),
        'lipFullness': _yuvarla(lipFullness),
        'eyeSpacing': _yuvarla(eyeSpacing),
        'symmetry': _yuvarla(symmetry),
      };

  /// İki ondalık YETER ve bilinçli: daha fazla hassasiyet okumayı
  /// iyileştirmez ama sayı kümesini kişiye özgü kılmaya yaklaştırır.
  /// Kabalaştırmak, gönderilen verinin tanımlayıcı olmamasını korur.
  static double _yuvarla(double d) => (d * 100).round() / 100;
}

/// Landmark'lardan oranları hesaplar.
///
/// Ölçek bağımsızdır: her uzunluk yüz yüksekliğine ya da genişliğine
/// bölünür, böylece kameraya yakınlık sonucu değiştirmez.
FaceRatios computeRatios(FaceLandmarks lm) {
  final faceHeight = (lm.chin.dy - lm.foreheadTop.dy).abs();
  final faceWidth = (lm.cheekRight.dx - lm.cheekLeft.dx).abs();

  // Sıfıra bölmeye karşı: tespit bozuksa oran üretmek yerine nötr dön.
  if (faceHeight < 1 || faceWidth < 1) return _neutral;

  final ust = (lm.browMid.dy - lm.foreheadTop.dy).abs() / faceHeight;
  final orta = (lm.noseBase.dy - lm.browMid.dy).abs() / faceHeight;
  final alt = (lm.chin.dy - lm.noseBase.dy).abs() / faceHeight;

  final jawWidth = (lm.jawRight.dx - lm.jawLeft.dx).abs();
  final mouthWidth = (lm.mouthRight.dx - lm.mouthLeft.dx).abs();
  final lipHeight = (lm.lowerLip.dy - lm.upperLip.dy).abs();
  final eyeGap = (lm.eyeRight.dx - lm.eyeLeft.dx).abs();

  return FaceRatios(
    upperThird: ust,
    middleThird: orta,
    lowerThird: alt,
    widthToHeight: faceWidth / faceHeight,
    jawToCheek: jawWidth / faceWidth,
    mouthToFaceWidth: mouthWidth / faceWidth,
    lipFullness: lipHeight / faceHeight,
    eyeSpacing: eyeGap / faceWidth,
    symmetry: _symmetry(lm, faceWidth),
  );
}

/// Yüz ekseni etrafındaki sol-sağ denge.
///
/// Eksen burun tabanından geçen dikey çizgi kabul edilir; sol ve sağ
/// karşılıkların bu eksene uzaklıkları karşılaştırılır.
double _symmetry(FaceLandmarks lm, double faceWidth) {
  final eksen = lm.noseBase.dx;
  double fark(Offset sol, Offset sag) =>
      ((eksen - sol.dx).abs() - (sag.dx - eksen).abs()).abs();

  final toplam = fark(lm.cheekLeft, lm.cheekRight) +
      fark(lm.jawLeft, lm.jawRight) +
      fark(lm.mouthLeft, lm.mouthRight) +
      fark(lm.eyeLeft, lm.eyeRight);

  // Ortalama sapmayı yüz genişliğine oranla ve 1'den çıkar.
  final oran = (toplam / 4) / faceWidth;
  return (1 - oran).clamp(0.0, 1.0);
}

const _neutral = FaceRatios(
  upperThird: 0.33,
  middleThird: 0.33,
  lowerThird: 0.34,
  widthToHeight: 0.7,
  jawToCheek: 0.8,
  mouthToFaceWidth: 0.4,
  lipFullness: 0.05,
  eyeSpacing: 0.45,
  symmetry: 1.0,
);

// ---------------------------------------------------------------------------
// Çerçeveleme kalitesi
// ---------------------------------------------------------------------------

/// Kameradaki yüzün çekime uygun olup olmadığı.
///
/// Kılavuz süs değil **kalite kapısıdır**: kötü çerçevelenmiş bir kareden
/// çıkan oranlar yanlış olur ve yanlış oranlardan üretilen okuma, kullanıcıya
/// kendi yüzü hakkında yanlış bir şey söyler. Deklanşör yalnızca [ready]
/// durumunda etkindir.
enum FrameQuality {
  noFace,
  tooFar,
  tooClose,
  offCentre,
  tilted,
  ready,
}

/// Yüzün kadraja göre kapladığı en küçük/en büyük oran.
const double kMinFaceRatio = 0.30;
const double kMaxFaceRatio = 0.78;

/// Kadraj merkezinden izin verilen en büyük sapma (kısa kenara oranla).
const double kMaxOffCentre = 0.14;

/// İzin verilen en büyük baş eğimi (derece).
const double kMaxTilt = 12.0;

/// Tespit edilen yüz kutusundan çerçeveleme kalitesini çıkarır.
///
/// Kontrol sırası bilinçli: kullanıcıya aynı anda tek bir şey söylenir ve
/// önce en temel olan düzeltilir. "Yüzünü ortala ve biraz yaklaş ve başını
/// düzelt" üç ayrı iş demektir; kimse okumaz.
FrameQuality assessFrame({
  required Rect? faceBox,
  required Size previewSize,
  double headAngleZ = 0,
}) {
  if (faceBox == null) return FrameQuality.noFace;
  if (previewSize.width < 1 || previewSize.height < 1) {
    return FrameQuality.noFace;
  }

  final kisaKenar = math.min(previewSize.width, previewSize.height);
  final oran = faceBox.height / previewSize.height;

  if (oran < kMinFaceRatio) return FrameQuality.tooFar;
  if (oran > kMaxFaceRatio) return FrameQuality.tooClose;

  final merkez = faceBox.center;
  final kadrajMerkezi =
      Offset(previewSize.width / 2, previewSize.height / 2);
  final sapma = (merkez - kadrajMerkezi).distance / kisaKenar;
  if (sapma > kMaxOffCentre) return FrameQuality.offCentre;

  if (headAngleZ.abs() > kMaxTilt) return FrameQuality.tilted;

  return FrameQuality.ready;
}
