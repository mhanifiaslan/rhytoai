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
    this.hairlineY,
    this.hairlineFromCrown = false,
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

  /// ÖLÇÜLEN saç çizgisi (bkz. `face_hairline.dart`). `null` ise ölçülemedi.
  ///
  /// `foreheadTop` bunun yerine KULLANILAMAZ: o, ML Kit yüz konturunun en üst
  /// noktası ve kişinin saç çizgisiyle değil modelin davranışıyla belirleniyor.
  /// Gerçek bir yüzde üst bölgeyi 0,17 gösteriyordu (klasik ~0,33).
  final double? hairlineY;

  /// [hairlineY] saç sınırından değil kafatası tepesinden geldi mi.
  final bool hairlineFromCrown;
}

/// Sunucuya gidecek olan şey: yalnızca oranlar.
class FaceRatios {
  const FaceRatios({
    required this.upperThird,
    required this.middleThird,
    required this.lowerThird,
    this.foreheadMeasured = false,
    this.foreheadFromCrown = false,
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

  /// Saç çizgisi GERÇEKTEN ölçüldü mü?
  ///
  /// `false` ise üç bölge oranı sunucuya **gönderilmiyor**. Sebebi ölçülmüş
  /// bir kusur: ML Kit saç çizgisi vermiyor ve yüz konturunun tepesi alın
  /// üstü sayılınca üst bölge 0,17 çıkıyordu (klasik ~0,33). Payda da o
  /// noktadan hesaplandığı için orta ve alt bölge şişiyor, sunucu "kısa alın
  /// + baskın orta + baskın alt" gibi üç çelişkili iddia üretiyordu.
  ///
  /// Ölçemediğimizde susmak, yanlış ölçüp yorumlamaktan iyidir.
  final bool foreheadMeasured;

  /// Ölçüm saç çizgisinden değil KAFATASI TEPESİNDEN yapıldı (kel/tıraşlı).
  ///
  /// Okuma bunu söylemek zorunda. Gelenek üst bölgeyi saç çizgisinden
  /// tanımlıyor ve kel bir kafada o çizgi geri getirilemez; nereden
  /// ölçüldüğünü gizlemek, ölçmediğimiz bir şeyi ölçmüş gibi sunmak olurdu.
  final bool foreheadFromCrown;

  Map<String, double> toJson() => {
        // Üç bölge yalnızca saç çizgisi ölçüldüyse gider. Sunucu "alan yoksa
        // ölçemedim" diye okuyor; hareket ölçümünde de aynı desen var.
        // YÜKSEKLİĞE bölünen her oran saç çizgisine bağlı; ölçülemediyse
        // hiçbiri gitmiyor. Bunlar tek tek değil TOPLU düşer, çünkü hepsi
        // aynı yanlış paydadan besleniyordu.
        if (foreheadMeasured) ...{
          'upperThird': _yuvarla(upperThird),
          'middleThird': _yuvarla(middleThird),
          'lowerThird': _yuvarla(lowerThird),
          'widthToHeight': _yuvarla(widthToHeight),
          'lipFullness': _yuvarla(lipFullness),
          // 1 = kafatası tepesinden ölçüldü. Sunucu okumayı buna göre
          // ifade ediyor.
          'foreheadFromCrown': foreheadFromCrown ? 1.0 : 0.0,
        },
        // Genişliğe bölünenler saç çizgisinden bağımsız — her zaman gider.
        'jawToCheek': _yuvarla(jawToCheek),
        'mouthToFaceWidth': _yuvarla(mouthToFaceWidth),
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
  // Dikey referans SAÇ ÇİZGİSİ. Ölçülemediyse yükseklik türevli oranların
  // hiçbiri üretilmiyor (bkz. `FaceRatios.foreheadMeasured`); yanlış bir
  // tepe noktası üç bölgeyi de, en/boy oranını da, dudak dolgunluğunu da
  // birden kaydırıyordu.
  final sacCizgisi = lm.hairlineY;
  final olculdu = sacCizgisi != null;
  final tepeden = lm.hairlineFromCrown;
  final tepe = sacCizgisi ?? lm.foreheadTop.dy;

  final faceHeight = (lm.chin.dy - tepe).abs();
  final faceWidth = (lm.cheekRight.dx - lm.cheekLeft.dx).abs();

  // Sıfıra bölmeye karşı: tespit bozuksa oran üretmek yerine nötr dön.
  if (faceHeight < 1 || faceWidth < 1) return _neutral;

  final ust = (lm.browMid.dy - tepe).abs() / faceHeight;
  final orta = (lm.noseBase.dy - lm.browMid.dy).abs() / faceHeight;
  final alt = (lm.chin.dy - lm.noseBase.dy).abs() / faceHeight;

  final jawWidth = (lm.jawRight.dx - lm.jawLeft.dx).abs();
  final mouthWidth = (lm.mouthRight.dx - lm.mouthLeft.dx).abs();
  final lipHeight = (lm.lowerLip.dy - lm.upperLip.dy).abs();
  final eyeGap = (lm.eyeRight.dx - lm.eyeLeft.dx).abs();

  return FaceRatios(
    foreheadMeasured: olculdu,
    foreheadFromCrown: tepeden,
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

/// Kılavuz ovalinin geometrisi — **tek kaynak**.
///
/// Bunlar hem ekrana çizilen ovali (`FaceGuidePainter.guideOval`) hem de
/// kalite kontrolünün beklediği hedefi belirliyor. İkisi ayrı sabitler
/// kullanınca gerçek bir hata çıktı: oval ekranın %44'üne çiziliyor ama
/// kontrol yüzü %50'de arıyordu. Kullanıcı kılavuzun dediğini yapıyor,
/// uygulama "yüzünü ortala" deyip deklanşörü açmıyordu.
///
/// Oval bilinçli olarak merkezin biraz ÜSTÜNDE: yüzün doğal ağırlık merkezi
/// geometrik merkezin üstündedir, tam ortaya konursa kullanıcı içgüdüsel
/// olarak çenesini kaldırıyor.
const double kGuideCenterY = 0.44;
const double kGuideWidthFraction = 0.66;
const double kGuideAspect = 1.32;

/// Yüz kutusunun **kılavuz ovaline** göre doldurma oranı.
///
/// Eşik daha önce kadraja göreydi (`faceBox.height / previewSize.height`) ve
/// bu yanlış ölçüydü: kullanıcının hedefi kadraj değil oval. Oval, ekran
/// oranına göre kadrajın %40–49'u; üstüne ML Kit'in kutusu görünen kafadan
/// dar (saç ve çene altı dışarıda). Ovali gözle dolduran bir yüz eşiğin tam
/// sınırına düşüyor, "biraz yaklaş" diyor ve deklanşör açılmıyordu.
///
/// Bant BİLEREK geniş. Çıkan oranların hepsi ölçek bağımsız (bkz.
/// [computeRatios]) — yani yüzün büyüklüğü sonucu değiştirmiyor. Bu kapının
/// işi okumayı doğru kılmak değil, konturun güvenilir çıkacağı kadar piksel
/// ve cepheden bir duruş sağlamak.
const double kMinGuideFill = 0.55;
const double kMaxGuideFill = 1.15;

/// Kılavuz merkezinden izin verilen sapma (oval yüksekliğine oranla).
const double kMaxOffCentre = 0.22;

/// İzin verilen en büyük baş eğimi (derece).
const double kMaxTilt = 12.0;

/// Histerezis payı — **titremeyi bitiren şey**.
///
/// Tek eşik kullanılınca ölçüm sınırın iki yanında salınıyor ve kılavuz
/// yeşil–sarı arasında çırpınıyordu. "Hazır"a girmek için gereken ile
/// "hazır"dan çıkmak için gereken artık farklı: bir kez kilitlenince
/// tolerans genişliyor.
const double _kHisterezisOran = 0.08;
const double _kHisterezisSapma = 0.06;
const double _kHisterezisEgim = 4.0;

/// Kılavuz ovali — EKRAN uzayında.
Rect guideOvalOnScreen(Size screenSize) {
  final w = screenSize.width * kGuideWidthFraction;
  final h = w * kGuideAspect;
  return Rect.fromCenter(
    center: Offset(screenSize.width / 2, screenSize.height * kGuideCenterY),
    width: w,
    height: h,
  );
}

/// Kılavuz ovalinin GÖRÜNTÜ uzayındaki karşılığı.
///
/// Bu dönüşüm şart, çünkü iki uzay farklı: oval ekran ölçülerine göre
/// çiziliyor, ML Kit'in yüz kutusu ise görüntü ölçülerinde geliyor. Önizleme
/// ekrana `BoxFit.cover` ile oturuyor; burada o dönüşümün tersi alınıyor.
///
/// [screenSize] yoksa (test ya da ölçü bilinmiyorsa) önizlemenin ekranı
/// birebir kapladığı varsayılır.
Rect guideOvalInImage({required Size previewSize, Size? screenSize}) {
  if (screenSize == null ||
      screenSize.width < 1 ||
      screenSize.height < 1) {
    return guideOvalOnScreen(previewSize);
  }
  final ekranOval = guideOvalOnScreen(screenSize);
  final olcek = math.max(screenSize.width / previewSize.width,
      screenSize.height / previewSize.height);
  final dx = (screenSize.width - previewSize.width * olcek) / 2;
  final dy = (screenSize.height - previewSize.height * olcek) / 2;
  return Rect.fromCenter(
    center: Offset((ekranOval.center.dx - dx) / olcek,
        (ekranOval.center.dy - dy) / olcek),
    width: ekranOval.width / olcek,
    height: ekranOval.height / olcek,
  );
}

/// Tespit edilen yüz kutusundan çerçeveleme kalitesini çıkarır.
///
/// Kontrol sırası bilinçli: kullanıcıya aynı anda tek bir şey söylenir ve
/// önce en temel olan düzeltilir. "Yüzünü ortala ve biraz yaklaş ve başını
/// düzelt" üç ayrı iş demektir; kimse okumaz.
///
/// [wasReady] bir önceki karenin sonucu; histerezis bunun üzerinden çalışıyor.
FrameQuality assessFrame({
  required Rect? faceBox,
  required Size previewSize,
  Size? screenSize,
  double headAngleZ = 0,
  bool wasReady = false,
}) {
  if (faceBox == null) return FrameQuality.noFace;
  if (previewSize.width < 1 || previewSize.height < 1) {
    return FrameQuality.noFace;
  }

  final hedef = guideOvalInImage(
      previewSize: previewSize, screenSize: screenSize);
  if (hedef.height < 1) return FrameQuality.noFace;

  final pay = wasReady ? _kHisterezisOran : 0.0;
  final doluluk = faceBox.height / hedef.height;

  if (doluluk < kMinGuideFill - pay) return FrameQuality.tooFar;
  if (doluluk > kMaxGuideFill + pay) return FrameQuality.tooClose;

  // Hedef, ekrandaki kılavuz ovalinin merkezi — kadrajın geometrik merkezi
  // DEĞİL. İkisi ayrıldığında kullanıcı kılavuzun dediğini yapıyor ama
  // kontrol reddediyordu.
  final sapma = (faceBox.center - hedef.center).distance / hedef.height;
  final sapmaSiniri =
      kMaxOffCentre + (wasReady ? _kHisterezisSapma : 0.0);
  if (sapma > sapmaSiniri) return FrameQuality.offCentre;

  final egimSiniri = kMaxTilt + (wasReady ? _kHisterezisEgim : 0.0);
  if (headAngleZ.abs() > egimSiniri) return FrameQuality.tilted;

  return FrameQuality.ready;
}
