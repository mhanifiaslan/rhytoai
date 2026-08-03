/// Galeriden seçilen fotoğraftan yüz ölçümü.
///
/// Kamera akışıyla AYNI boru hattı: ML Kit tespiti → segmentasyon → saç
/// çizgisi → oranlar. Farklar bilinçli ve az:
///
/// * **Tek kare.** Kararlılık penceresi (medyan + yayılım) akış ister;
///   fotoğrafta yalnızca bir örnek var. Saç çizgisi ölçümü kendi güven
///   eşiklerinden geçiyorsa kabul ediliyor ve sonuç "tek kareden ölçüldü"
///   diye İŞARETLENİYOR — okuma ekranı bunu kullanıcıya söylüyor.
///   Söylenmeden kabul etmek, kararlılık katmanının varlık sebebini
///   (çelişen ardışık okumalar) galeri yolundan sessizce geri getirmek olurdu.
/// * **Hareket ölçümü yok.** Fotoğraf kıpırdamaz; `MotionMetrics` alanları
///   sunucuya hiç gönderilmez ve sunucu o ekseni "ölçülemedi" diye okur
///   (sıcak–soğuk ekseni okumadan düşer — sunucu bunu zaten söylüyor).
/// * **Görüntü bellekte işlenir, uygulama diske YAZMAZ.** Seçici eklentisi
///   fotoğrafın bir kopyasını uygulama önbelleğine koyuyor (eklentinin
///   çalışma biçimi); işimiz bitince o kopya siliniyor. Sunucuya yine
///   yalnızca oranlar gidiyor — biyometrik görüntü cihazdan çıkmıyor.
///
/// ## Koordinat uzayları
///
/// ML Kit `InputImage.fromFilePath` EXIF dönüşünü kendisi uygular ve
/// koordinatları DİK görüntü uzayında verir. `dart:ui` çözücüsü de EXIF'i
/// uygular. Yani landmark'lar ve çözülen bitmap aynı uzayda — kameradaki
/// `rotatedImageSize` dansına gerek yok, derece hep 0.
library;

import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/foundation.dart';
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';

import 'face_capture_screen.dart' show FaceCaptureResult;
import 'face_detection.dart';
import 'face_geometry.dart';
import 'face_hairline.dart';
import 'face_motion.dart';
import 'face_segmentation.dart';

/// Durağan analiz sonucu — başarısızlıkta SEBEP kayboluyor olmasın.
///
/// `null` dönen bir fonksiyon "yüz yok mu, model mi yüklenmedi, dosya mı
/// bozuk" sorusuna cevap vermez; bu projede sessiz başarısızlık defalarca
/// saat yaktı. Sebep, kullanıcıya gösterilecek metni seçmek için de gerekli.
class StillAnalysis {
  const StillAnalysis.ok(FaceCaptureResult this.result) : failure = null;
  const StillAnalysis.fail(StillFailure this.failure) : result = null;

  final FaceCaptureResult? result;
  final StillFailure? failure;
}

enum StillFailure {
  /// Fotoğrafta yüz bulunamadı (ya da dosya çözülemedi).
  noFace,

  /// Yüz var ama landmark geometrisi çıkarılamadı (aşırı profil, örtük).
  noLandmarks,
}

/// Fotoğrafı analiz eder; görüntüyü **bellekte** işler.
///
/// [detector] ve [segmenter] çağıranın malı — kamera ekranı zaten ikisini
/// de kurmuş durumda, yeniden yüklemek birkaç yüz milisaniye israf olurdu.
Future<StillAnalysis> analyzeStillImage({
  required String path,
  required FaceDetector detector,
  required FaceSegmenter segmenter,
}) async {
  // 1) Tespit — dosyadan, EXIF'i ML Kit çözer.
  final List<Face> yuzler;
  try {
    yuzler = await detector.processImage(InputImage.fromFilePath(path));
  } catch (_) {
    return const StillAnalysis.fail(StillFailure.noFace);
  }
  if (yuzler.isEmpty) return const StillAnalysis.fail(StillFailure.noFace);

  final temel = landmarksFromFace(yuzler.first);
  if (temel == null) {
    return const StillAnalysis.fail(StillFailure.noLandmarks);
  }

  // 2) Saç çizgisi için segmentasyon. Model yüklenememişse ya da maske
  // üretilemezse akış DURMUYOR: alın ölçülmemiş sayılır ve üç bölge oranı
  // gönderilmez — kameradaki duruşun aynısı.
  Hairline? sac;
  var boyut = ui.Size.zero;
  final maske = await _maskeUret(path, segmenter);
  if (maske != null) {
    boyut = maske.$2;
    sac = hairlineFromMask(
      mask: maske.$1,
      imageSize: boyut,
      browY: temel.browMid.dy,
      chinY: temel.chin.dy,
      axisX: temel.noseBase.dx,
      faceWidth: (temel.cheekRight.dx - temel.cheekLeft.dx).abs(),
    );
  }

  final lm = sac == null
      ? temel
      : FaceLandmarks(
          faceOval: temel.faceOval,
          foreheadTop: temel.foreheadTop,
          browMid: temel.browMid,
          noseBase: temel.noseBase,
          chin: temel.chin,
          cheekLeft: temel.cheekLeft,
          cheekRight: temel.cheekRight,
          jawLeft: temel.jawLeft,
          jawRight: temel.jawRight,
          mouthLeft: temel.mouthLeft,
          mouthRight: temel.mouthRight,
          upperLip: temel.upperLip,
          lowerLip: temel.lowerLip,
          eyeLeft: temel.eyeLeft,
          eyeRight: temel.eyeRight,
          headAngleZ: temel.headAngleZ,
          headAngleY: temel.headAngleY,
          hairlineY: sac.y,
          hairlineFromCrown: sac.kind == HairlineKind.crown,
        );

  // 3) Hareket ölçümü YOK: boş izleyicinin metrikleri `confident=false`
  // döner ve alanlar sunucuya hiç gitmez.
  return StillAnalysis.ok(FaceCaptureResult(
    computeRatios(lm),
    MotionTracker().metrics,
    singleFrame: true,
  ));
}

/// Fotoğrafı çözer ve segmentasyon maskesini üretir; başarısızlıkta `null`.
///
/// **Tam çözünürlükte, tek çözüm.** Küçülterek çözmek (`targetWidth`)
/// denendi ve bilerek geri alındı: `ImageDescriptor` boyutları EXIF
/// dönüşsüz HAM boyutlar, ML Kit ise dönüş UYGULANMIŞ uzayda koordinat
/// veriyor. Telefon fotoğraflarının çoğu EXIF döner — iki uzay karışınca
/// maske eşlemesinde en/boy yer değiştirir ve saç çizgisi sessizce yanlış
/// yere düşer (bu projede koordinat uzayı karıştırmanın faturası daha önce
/// iki kez ödendi). Çözülmüş karenin kendisi tek güvenilir uzay: hem
/// dönüşü uygulanmış hem landmark'larla aynı. Bedeli 12 MP fotoğrafta
/// ~48 MB'lik geçici RGBA tamponu — bir kez, saniyeler içinde bırakılıyor.
Future<(SegmentationMask, ui.Size)?> _maskeUret(
    String path, FaceSegmenter segmenter) async {
  if (!segmenter.ready) return null;
  try {
    final baytlar = await File(path).readAsBytes();
    final codec = await ui.instantiateImageCodec(baytlar);
    final kare = (await codec.getNextFrame()).image;
    codec.dispose();

    final ham = await kare.toByteData(format: ui.ImageByteFormat.rawRgba);
    final boyut = ui.Size(kare.width.toDouble(), kare.height.toDouble());
    final w = kare.width;
    final h = kare.height;
    kare.dispose();
    if (ham == null) return null;

    final maske = await segmenter.runStill(
      rgba: ham.buffer.asUint8List(ham.offsetInBytes, ham.lengthInBytes),
      width: w,
      height: h,
    );
    if (maske == null) return null;

    return (maske, boyut);
  } catch (e) {
    debugPrint('RYTHO-STILL çözme düştü: $e');
    return null;
  }
}
