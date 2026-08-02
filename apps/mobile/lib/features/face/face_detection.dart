/// ML Kit ile **cihaz üstü** yüz tespiti.
///
/// Bu dosyanın tamamı cihazda çalışır ve dışarıya hiçbir şey göndermez.
/// Görüntü buradan çıkmaz; çıkan tek şey [FaceLandmarks] ve ondan türetilen
/// oranlardır.
library;

import 'dart:typed_data';
import 'dart:ui';

import 'package:camera/camera.dart';
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';

import 'face_geometry.dart';

/// Kontur açık bir dedektör.
///
/// `enableContours` şart: oran hesabı için yüz ovali, kaş, burun ve dudak
/// hatları gerekiyor. Yalnız `enableLandmarks` göz/burun/ağız merkezlerini
/// verir, kontur vermez — San Ting oranları çıkarılamaz.
///
/// `performanceMode: fast` bilinçli: canlı önizlemede kare başına çalışıyor
/// ve `accurate` mod telefonu ısıtacak kadar pahalı. Çekim anındaki tek
/// karede fark yaratmıyor.
FaceDetector createFaceDetector() => FaceDetector(
      options: FaceDetectorOptions(
        enableContours: true,
        enableLandmarks: true,
        enableClassification: false,
        enableTracking: false,
        performanceMode: FaceDetectorMode.fast,
        minFaceSize: 0.15,
      ),
    );

/// Kamera karesini ML Kit'in beklediği biçime çevirir.
///
/// Platform farkı gerçek ve kaçınılmaz: Android kamerası YUV/NV21, iOS
/// BGRA8888 veriyor. Yanlış biçim verildiğinde ML Kit hata döndürmez,
/// **hiçbir yüz bulamaz** — yani kusur sessizdir ve "kamera bozuk" gibi
/// görünür.
InputImage? inputImageFromCamera({
  required CameraImage image,
  required CameraDescription camera,
  required int deviceOrientationDegrees,
}) {
  final rotation = _rotation(camera, deviceOrientationDegrees);
  if (rotation == null) return null;

  final format = InputImageFormatValue.fromRawValue(image.format.raw);
  if (format == null) return null;

  // Android'de NV21, iOS'ta BGRA8888 bekleniyor; başka bir şey gelirse
  // dönüştürmeye çalışmak yerine kareyi atlıyoruz — bozuk veriyle tespit
  // yapmaktansa o kareyi hiç işlememek doğru.
  if (format != InputImageFormat.nv21 &&
      format != InputImageFormat.bgra8888) {
    return null;
  }

  final bytes = _birlestir(image.planes);
  return InputImage.fromBytes(
    bytes: bytes,
    metadata: InputImageMetadata(
      size: Size(image.width.toDouble(), image.height.toDouble()),
      rotation: rotation,
      format: format,
      bytesPerRow: image.planes.first.bytesPerRow,
    ),
  );
}

Uint8List _birlestir(List<Plane> planes) {
  if (planes.length == 1) return planes.first.bytes;
  final builder = BytesBuilder(copy: false);
  for (final p in planes) {
    builder.add(p.bytes);
  }
  return builder.toBytes();
}

InputImageRotation? _rotation(CameraDescription camera, int deviceDegrees) {
  // Ön kamera aynalandığı için sensör açısı ters yönde toplanır; bu
  // atlanırsa yüz bulunur ama noktalar yatay olarak yanlış yere düşer.
  final aci = camera.lensDirection == CameraLensDirection.front
      ? (camera.sensorOrientation + deviceDegrees) % 360
      : (camera.sensorOrientation - deviceDegrees + 360) % 360;
  return InputImageRotationValue.fromRawValue(aci);
}

/// ML Kit yüzünden [FaceLandmarks] çıkarır.
///
/// Kontur eksikse `null` döner: eksik noktayla oran hesaplamak, uydurulmuş
/// bir ölçüm üretmek olur.
FaceLandmarks? landmarksFromFace(Face face) {
  final oval = face.contours[FaceContourType.face]?.points;
  if (oval == null || oval.length < 12) return null;

  Offset? nokta(FaceContourType tur, [int? indeks]) {
    final p = face.contours[tur]?.points;
    if (p == null || p.isEmpty) return null;
    final i = indeks ?? p.length ~/ 2;
    if (i >= p.length) return null;
    return Offset(p[i].x.toDouble(), p[i].y.toDouble());
  }

  Offset? isaret(FaceLandmarkType tur) {
    final l = face.landmarks[tur];
    return l == null ? null : Offset(l.position.x.toDouble(), l.position.y.toDouble());
  }

  final ovalNoktalar = [
    for (final p in oval) Offset(p.x.toDouble(), p.y.toDouble()),
  ];

  // Yüz ovali saat yönünde sıralı gelir; en üst ve en alt nokta alın ve çene.
  final enUst = ovalNoktalar.reduce((a, b) => a.dy < b.dy ? a : b);
  final enAlt = ovalNoktalar.reduce((a, b) => a.dy > b.dy ? a : b);
  final enSol = ovalNoktalar.reduce((a, b) => a.dx < b.dx ? a : b);
  final enSag = ovalNoktalar.reduce((a, b) => a.dx > b.dx ? a : b);

  final solKas = nokta(FaceContourType.leftEyebrowTop);
  final sagKas = nokta(FaceContourType.rightEyebrowTop);
  final burunAlt = nokta(FaceContourType.noseBottom);
  final ustDudak = nokta(FaceContourType.upperLipTop);
  final altDudak = nokta(FaceContourType.lowerLipBottom);
  final agizSol = isaret(FaceLandmarkType.leftMouth);
  final agizSag = isaret(FaceLandmarkType.rightMouth);
  final gozSol = isaret(FaceLandmarkType.leftEye);
  final gozSag = isaret(FaceLandmarkType.rightEye);

  if (solKas == null ||
      sagKas == null ||
      burunAlt == null ||
      ustDudak == null ||
      altDudak == null ||
      agizSol == null ||
      agizSag == null ||
      gozSol == null ||
      gozSag == null) {
    return null;
  }

  // Çene genişliği: ovalin alt üçte birindeki en geniş yer.
  final altBolge = ovalNoktalar
      .where((p) => p.dy > enUst.dy + (enAlt.dy - enUst.dy) * 0.66)
      .toList();
  final ceneSol = altBolge.isEmpty
      ? enSol
      : altBolge.reduce((a, b) => a.dx < b.dx ? a : b);
  final ceneSag = altBolge.isEmpty
      ? enSag
      : altBolge.reduce((a, b) => a.dx > b.dx ? a : b);

  return FaceLandmarks(
    faceOval: ovalNoktalar,
    foreheadTop: enUst,
    browMid: Offset((solKas.dx + sagKas.dx) / 2, (solKas.dy + sagKas.dy) / 2),
    noseBase: burunAlt,
    chin: enAlt,
    cheekLeft: enSol,
    cheekRight: enSag,
    jawLeft: ceneSol,
    jawRight: ceneSag,
    mouthLeft: agizSol,
    mouthRight: agizSag,
    upperLip: ustDudak,
    lowerLip: altDudak,
    eyeLeft: gozSol,
    eyeRight: gozSag,
    headAngleZ: face.headEulerAngleZ ?? 0,
    headAngleY: face.headEulerAngleY ?? 0,
  );
}

/// Hareket ölçümüne girecek noktalar — kare kare aynı sırada.
///
/// **Göz konturu bilerek yok.** Göz kırpması landmark'ları çok büyük bir
/// mesafe oynatıyor ve ölçüm tamamen kırpma sıklığına iniyor; oysa aranan
/// şey ifadenin genel canlılığı.
///
/// Herhangi bir kontur eksikse `null` döner: nokta sayısı kareden kareye
/// değişirse karşılaştırma anlamsız olur.
List<Offset>? motionPoints(Face face) {
  final parcalar = <Offset>[];
  for (final tur in const [
    FaceContourType.leftEyebrowTop,
    FaceContourType.rightEyebrowTop,
    FaceContourType.upperLipTop,
    FaceContourType.lowerLipBottom,
    FaceContourType.face,
  ]) {
    final p = face.contours[tur]?.points;
    if (p == null || p.isEmpty) return null;
    for (final nokta in p) {
      parcalar.add(Offset(nokta.x.toDouble(), nokta.y.toDouble()));
    }
  }
  return parcalar;
}

/// Animasyonda çizilecek nokta kümesi.
///
/// Tüm kontur noktalarını çizmek (yüzlerce) ağ değil leke veriyor; ovalden
/// seyreltilmiş bir alt küme + iç hatların anahtar noktaları hem okunur hem
/// "tarandı" hissini veriyor.
List<Offset> scanNodes(Face face) {
  final noktalar = <Offset>[];

  void ekle(FaceContourType tur, int adim) {
    final p = face.contours[tur]?.points;
    if (p == null) return;
    for (var i = 0; i < p.length; i += adim) {
      noktalar.add(Offset(p[i].x.toDouble(), p[i].y.toDouble()));
    }
  }

  ekle(FaceContourType.face, 2);
  ekle(FaceContourType.leftEyebrowTop, 2);
  ekle(FaceContourType.rightEyebrowTop, 2);
  ekle(FaceContourType.leftEye, 3);
  ekle(FaceContourType.rightEye, 3);
  ekle(FaceContourType.noseBridge, 1);
  ekle(FaceContourType.noseBottom, 2);
  ekle(FaceContourType.upperLipTop, 2);
  ekle(FaceContourType.lowerLipBottom, 2);

  return noktalar;
}
