/// Cihaz üstü **segmentasyon** — saç, yüz teni ve arka planı piksel piksel ayırır.
///
/// ## Neden gerekiyor
///
/// ML Kit saç çizgisi vermiyor. Yüz konturunun en üst noktası "alın üstü"
/// sayılıyordu ve gerçek bir yüzde ölçülen şuydu:
///
///     üst 0,17   orta 0,40   alt 0,42      (klasik San Ting ~0,33 bekler)
///
/// Alın olması gerekenin yarısı çıkıyordu. Payda da o noktadan hesaplandığı
/// için hata orta ve alt bölgeyi de şişiriyor, sunucu "kısa alın + baskın
/// orta + baskın alt" gibi birbiriyle çelişen üç iddia üretiyordu.
///
/// Parlaklık eşiğiyle geçiş aramak denendi; o bir sinyal işleme sezgisiydi ve
/// kel kafada, kâkülde, açık renk saçta sessizce çuvallıyordu. Doğru alet bu:
/// eğitilmiş bir segmentasyon modeli.
///
/// ## Model
///
/// MediaPipe **Selfie Multiclass** (256×256, Apache 2.0, Google, 10 Mayıs
/// 2023). Altı sınıf üretiyor: arka plan, saç, gövde teni, yüz teni, giysi,
/// aksesuar. Bize saç ile yüz teni arasındaki sınır lazım.
///
/// Model kartındaki iki nokta ürünü doğrudan ilgilendiriyor:
///
/// * **Kapsam dışı:** gözetim ve kimlik tanıma. Bizim kullanımımız ikisi de
///   değil — kimseyi tanımıyoruz, yalnızca oran ölçüyoruz.
/// * **Sınır:** kötü ışık, arkadan aydınlatma ve büyük örtücüler maskeyi
///   bozuyor. Bu yüzden ölçüm güveni düşükse okuma yapılmıyor.
///
/// ## Görüntü telefondan çıkmıyor
///
/// Çıkarım cihazda. Bu bir performans tercihi değil, ürünün rıza metninde
/// verdiği sözün ta kendisi: biyometrik veri özel nitelikli (GDPR Md.9 /
/// KVKK md.6) ve yüz görüntüsünü sunucuya taşımak yükümlülüğü kat kat
/// artırırdı.
///
/// ## İşçi isolate: neden `IsolateInterpreter` değil
///
/// İlk sürüm ana isolate'ta koşuyordu ve **594 ms** sürüyordu; o süre boyunca
/// arayüz tamamen donuyordu. Çıkarım `IsolateInterpreter`'a taşındı ve süre
/// **1253 ms**'ye ÇIKTI — yani sorunu çözmek yerine iki katına katladı.
///
/// Sebep: `IsolateInterpreter.run(girdi, çıktı)` hazır tensörleri isolate
/// sınırından geçiriyor. Girdi 1×256×256×3, çıktı 1×256×256×6 ve tflite'ın
/// biçim çıkarımı yüzünden ikisi de **iç içe liste** olmak zorunda. Dart bu
/// nesne grafiğini her gönderimde derin kopyalıyor: ~590 bin `double`, 131
/// bin ayrı `List` nesnesinin içinde. Kopyalama, kaçırılmak istenen işten
/// pahalıya geldi.
///
/// Bu sürümde sınırdan **ham kamera baytları** geçiyor (düz bir `Uint8List`,
/// tek memcpy) ve geri yalnızca 256×256'lık sınıf maskesi dönüyor (64 KB).
/// YUV→RGB çevrimi, tensör kurulumu, çıkarım ve argmax'ın tamamı işçinin
/// içinde; iç içe tamponlar orada bir kez ayrılıp her karede yeniden
/// kullanılıyor ve hiçbir zaman sınırı geçmiyor.
library;

import 'dart:async';
import 'dart:isolate';
import 'dart:typed_data';

import 'package:camera/camera.dart';
import 'package:tflite_flutter/tflite_flutter.dart';

import 'face_detection.dart';

/// Modelin ürettiği sınıflar — sıra model kartındaki sırayla aynı.
class SegClass {
  const SegClass._();

  static const background = 0;
  static const hair = 1;
  static const bodySkin = 2;
  static const faceSkin = 3;
  static const clothes = 4;
  static const other = 5;
}

/// Sınıf maskesi — her piksel için bir [SegClass] değeri.
class SegmentationMask {
  const SegmentationMask({
    required this.classes,
    required this.width,
    required this.height,
  });

  final Uint8List classes;
  final int width;
  final int height;

  int at(int x, int y) {
    if (x < 0 || y < 0 || x >= width || y >= height) return SegClass.background;
    return classes[y * width + x];
  }
}

const int _kInput = 256;
const int _kClasses = 6;
const String _kModelAsset =
    'assets/models/selfie_multiclass_256x256.tflite';

/// Ham kare biçimi. Ayrım ana isolate'ta yapılıyor ([CameraImage] orada) ve
/// işçiye yalnızca sonuç bildiriliyor.
enum FrameFormat {
  /// iOS: tek düzlem, piksel başına dört bayt, BGRA sırası.
  bgra,

  /// Android: TEK düzlemde NV21 — önce Y bloğu, ardından araya geçmiş VU.
  nv21SinglePlane,

  /// YUV420: Y ayrı düzlemde, kroma ayrı düzlemde.
  yuv420Planar,
}

/// Tek pikselin rengini okur; sonuç [hedef] dizisine yazılır (0-255).
///
/// Ayrı bir fonksiyon çünkü sessizce yanlış olabilecek tek yer burası:
/// kroma indeksi bir bayt kayarsa renkler bozulur, model saçı ten sanır ve
/// **hiçbir hata görünmez** — yalnızca alın ölçüsü tutmaz. Testle korunuyor.
///
/// Piksel başına liste ayrılmıyor. Önceki sürüm her piksel için üç elemanlı
/// bir `List<int>` üretiyordu: kare başına 65 bin çöp nesne.
void readPixelRgb({
  required FrameFormat format,
  required Uint8List plane0,
  Uint8List? plane1,
  required int u,
  required int v,
  required int width,
  required int height,
  required int stride0,
  int stride1 = 0,
  int pixelStride1 = 2,
  required Float64List hedef,
}) {
  switch (format) {
    case FrameFormat.bgra:
      final i = v * stride0 + u * 4;
      if (i + 2 >= plane0.length) {
        hedef[0] = hedef[1] = hedef[2] = 0;
        return;
      }
      hedef[0] = plane0[i + 2].toDouble();
      hedef[1] = plane0[i + 1].toDouble();
      hedef[2] = plane0[i].toDouble();

    case FrameFormat.nv21SinglePlane:
      final yi = v * stride0 + u;
      if (yi >= plane0.length) {
        hedef[0] = hedef[1] = hedef[2] = 0;
        return;
      }
      final Y = plane0[yi].toDouble();
      // Kroma yarı çözünürlüklü: iki satır ve iki sütun bir çifti paylaşır.
      // NV21'de sıra V, sonra U.
      final ci = stride0 * height + (v >> 1) * stride0 + (u & ~1);
      if (ci + 1 >= plane0.length) {
        hedef[0] = hedef[1] = hedef[2] = Y.clamp(0, 255);
        return;
      }
      _yuv(Y, plane0[ci] - 128.0, plane0[ci + 1] - 128.0, hedef);

    case FrameFormat.yuv420Planar:
      final yi = v * stride0 + u;
      if (yi >= plane0.length || plane1 == null) {
        hedef[0] = hedef[1] = hedef[2] = 0;
        return;
      }
      final Y = plane0[yi].toDouble();
      final ci = (v >> 1) * stride1 + (u >> 1) * pixelStride1;
      if (ci + 1 >= plane1.length) {
        hedef[0] = hedef[1] = hedef[2] = Y.clamp(0, 255);
        return;
      }
      _yuv(Y, plane1[ci] - 128.0, plane1[ci + 1] - 128.0, hedef);
  }
}

void _yuv(double y, double cv, double cu, Float64List hedef) {
  hedef[0] = (y + 1.370705 * cv).clamp(0, 255);
  hedef[1] = (y - 0.337633 * cu - 0.698001 * cv).clamp(0, 255);
  hedef[2] = (y + 1.732446 * cu).clamp(0, 255);
}

/// En yüksek olasılıklı sınıf — her piksel için argmax.
///
/// Model kartı "post-processed (maxed) via image segmenter API" diyor;
/// API'yi kullanmadığımız için argmax bizde. **İşçinin içinde** yapılıyor:
/// aksi hâlde 393 bin `float` isolate sınırını geçerdi, oysa sonuç 64 KB.
///
/// Girdi **düz** ve satır öncelikli: `((y * 256) + x) * 6 + sınıf`.
Uint8List argmaxMask(Float32List cikti) {
  final maske = Uint8List(_kInput * _kInput);
  for (var i = 0; i < _kInput * _kInput; i++) {
    final taban = i * _kClasses;
    var enIyi = 0;
    var enIyiDeger = cikti[taban];
    for (var c = 1; c < _kClasses; c++) {
      final d = cikti[taban + c];
      if (d > enIyiDeger) {
        enIyiDeger = d;
        enIyi = c;
      }
    }
    maske[i] = enIyi;
  }
  return maske;
}

// ---------------------------------------------------------------------------
// İşçi isolate ile konuşulan mesajlar
// ---------------------------------------------------------------------------

class _Kurulum {
  const _Kurulum(this.address, this.yanit);

  /// Yerel yorumlayıcının işaretçi adresi. Yerel bellek süreç genelinde
  /// geçerli; işçi aynı örneği `Interpreter.fromAddress` ile sarmalıyor.
  final int address;
  final SendPort yanit;
}

class _Kare {
  const _Kare({
    required this.yanit,
    required this.bicim,
    required this.duzlem0,
    required this.duzlem1,
    required this.genislik,
    required this.yukseklik,
    required this.adim0,
    required this.adim1,
    required this.pikselAdim1,
    required this.derece,
  });

  final SendPort yanit;
  final FrameFormat bicim;
  final Uint8List duzlem0;
  final Uint8List? duzlem1;
  final int genislik;
  final int yukseklik;
  final int adim0;
  final int adim1;
  final int pikselAdim1;
  final int derece;
}

/// İşçinin başarılı yanıtı: maske + zaman dökümü.
///
/// Döküm teşhis için şart. "1656 ms" tek başına hangi kalemin pahalı olduğunu
/// söylemiyor ve bu proje bir kez tahminle optimize edip yanılmışlığını gördü:
/// isolate sınırı kaldırıldı, süre düşmedi, çünkü asıl maliyet başka yerdeydi.
class _Sonuc {
  const _Sonuc({
    required this.maske,
    required this.cevrimMs,
    required this.cikarimMs,
    required this.argmaxMs,
  });

  final Uint8List maske;
  final int cevrimMs;
  final int cikarimMs;
  final int argmaxMs;
}

/// İşçinin hata yanıtı. Maske yerine bu dönerse sebep **kaybolmuyor**.
class _Hata {
  const _Hata(this.mesaj);
  final String mesaj;
}

// ---------------------------------------------------------------------------
// İşçi isolate
// ---------------------------------------------------------------------------

/// İşçinin giriş noktası. Üst düzey olmak **zorunda** ([Isolate.spawn] kuralı).
Future<void> _isciGiris(_Kurulum kurulum) async {
  // `close()` ÇAĞRILMIYOR: bu sarmalayıcı yerel örneğin sahibi değil, ana
  // isolate'taki yorumlayıcıyla aynı işaretçiyi gösteriyor. Buradan silmek
  // ana isolate'ın elinde sarkan bir işaretçi bırakırdı.
  // `allocated: true` — tensörler ana isolate'ta zaten ayrıldı. Varsayılan
  // `false` bırakılırsa `invoke()` "Interpreter not allocated" diye düşer.
  final yorumlayici =
      Interpreter.fromAddress(kurulum.address, allocated: true);

  // Düz, tipli tampon. **İç içe liste YOK.**
  //
  // `Interpreter.run(girdi, çıktı)` kullanılmıyor, çünkü onun içindeki
  // `Tensor.setTo` ve `Tensor.copyTo` iç içe listeyi ELEMAN ELEMAN yürüyüp
  // bayta çeviriyor: kare başına 196 bin + 393 bin değer, iki ayrı yönde.
  // Cihazda ölçülen 1656 ms'nin baskın kalemi buydu — isolate sınırını
  // kaldırmak yetmedi, çünkü asıl maliyet sınırda değil marshalling'deydi.
  //
  // `Tensor.data` ise yerel tamponun kendisine memcpy yapıyor.
  final girdi = Float32List(_kInput * _kInput * 3);
  final girdiTensor = yorumlayici.getInputTensors().first;
  final ciktiTensor = yorumlayici.getOutputTensors().first;
  final girdiBaytlari =
      girdi.buffer.asUint8List(girdi.offsetInBytes, girdi.lengthInBytes);

  final kapi = ReceivePort();
  kurulum.yanit.send(kapi.sendPort);

  await for (final mesaj in kapi) {
    if (mesaj is! _Kare) break; // null = kapan
    try {
      final t0 = DateTime.now().microsecondsSinceEpoch;
      _kareyiTensore(mesaj, girdi);
      final t1 = DateTime.now().microsecondsSinceEpoch;

      girdiTensor.data = girdiBaytlari;
      yorumlayici.invoke();
      final t2 = DateTime.now().microsecondsSinceEpoch;

      // Yerel çıktı tamponunun ÜSTÜNDE görünüm — kopya yok.
      final ham = ciktiTensor.data;
      final cikti =
          ham.buffer.asFloat32List(ham.offsetInBytes, ham.length ~/ 4);
      final maske = argmaxMask(cikti);
      final t3 = DateTime.now().microsecondsSinceEpoch;

      mesaj.yanit.send(_Sonuc(
        maske: maske,
        cevrimMs: (t1 - t0) ~/ 1000,
        cikarimMs: (t2 - t1) ~/ 1000,
        argmaxMs: (t3 - t2) ~/ 1000,
      ));
    } catch (e) {
      mesaj.yanit.send(_Hata('çıkarım: $e'));
    }
  }
  kapi.close();
}

/// Döndürülmüş (dx,dy) hedef pikselini ham (u,v) kaynağına eşler.
///
/// Döndürme burada yapılıyor ki maske landmark'larla **aynı** uzayda çıksın;
/// koordinat uzaylarını karıştırmak bu projede daha önce noktaların yüzün
/// yanına düşmesine ve deklanşörün hiç açılmamasına yol açtı.
({int u, int v}) sourcePixel({
  required int dx,
  required int dy,
  required int width,
  required int height,
  required int degrees,
}) =>
    switch (degrees) {
      90 => (u: dy, v: height - 1 - dx),
      180 => (u: width - 1 - dx, v: height - 1 - dy),
      270 => (u: width - 1 - dy, v: dx),
      _ => (u: dx, v: dy),
    };

/// Ham kareyi 256×256 normalize RGB tensöre çevirir — döndürerek.
///
/// Hedef **düz** ve satır öncelikli: `((y * 256) + x) * 3 + kanal`.
void _kareyiTensore(_Kare k, Float32List tensor) {
  final ceyrek = k.derece == 90 || k.derece == 270;
  final donmusW = ceyrek ? k.yukseklik : k.genislik;
  final donmusH = ceyrek ? k.genislik : k.yukseklik;

  // Tek tampon, kare boyunca yeniden kullanılıyor.
  final rgb = Float64List(3);

  var i = 0;
  for (var y = 0; y < _kInput; y++) {
    final dy = (y * donmusH / _kInput).floor();
    for (var x = 0; x < _kInput; x++) {
      final dx = (x * donmusW / _kInput).floor();
      final kaynak = sourcePixel(
        dx: dx,
        dy: dy,
        width: k.genislik,
        height: k.yukseklik,
        degrees: k.derece,
      );

      readPixelRgb(
        format: k.bicim,
        plane0: k.duzlem0,
        plane1: k.duzlem1,
        u: kaynak.u,
        v: kaynak.v,
        width: k.genislik,
        height: k.yukseklik,
        stride0: k.adim0,
        stride1: k.adim1,
        pixelStride1: k.pikselAdim1,
        hedef: rgb,
      );

      tensor[i++] = rgb[0] / 255.0;
      tensor[i++] = rgb[1] / 255.0;
      tensor[i++] = rgb[2] / 255.0;
    }
  }
}

// ---------------------------------------------------------------------------
// Ana isolate tarafı
// ---------------------------------------------------------------------------

/// Segmentasyon modeli — tek örnek, tembel yüklenir.
///
/// Yorumlayıcı pahalı: yükleme birkaç yüz milisaniye sürebiliyor. Kamera
/// ekranı açılırken bir kez kurulup ekran kapanınca bırakılıyor.
class FaceSegmenter {
  Interpreter? _yorumlayici;
  Isolate? _isci;
  SendPort? _isciKapisi;
  bool _denendi = false;
  bool _mesgul = false;

  bool get ready => _isciKapisi != null;

  /// Son hatanın metni — **yutulmuyor**.
  ///
  /// İlk sürümde `catch (_) { return null; }` vardı ve cihazda yalnızca
  /// "çalışmadı" görünüyordu. Sessiz yutma bu projede defalarca saat
  /// kaybettirdi; sebep görünür olmak zorunda.
  String? lastError;

  /// Son ölçümün zaman dökümü — hangi kalemin pahalı olduğu.
  String? lastTimings;

  /// Modelin beklediği ve ürettiği tensör biçimleri (teşhis için).
  String get shapes {
    final y = _yorumlayici;
    if (y == null) return 'model yüklü değil';
    try {
      final g = y.getInputTensors().map((t) => '${t.shape}').join(',');
      final c = y.getOutputTensors().map((t) => '${t.shape}').join(',');
      return 'in=$g out=$c';
    } catch (e) {
      return 'biçim okunamadı: $e';
    }
  }

  /// Modeli yükler ve işçiyi başlatır. Başarısızlık **sessiz değil**:
  /// `false` döner ve çağıran ölçümü yapmadığını bilir.
  Future<bool> load() async {
    if (_denendi) return ready;
    _denendi = true;
    ReceivePort? kurulumKapisi;
    try {
      final yorumlayici = await Interpreter.fromAsset(
        _kModelAsset,
        options: InterpreterOptions()..threads = 2,
      );
      // Tensörler ANA isolate'ta ayrılıyor. İşçi aynı yerel örneği
      // sarmalayacak ve ilk karede yeniden ayırmak zorunda kalmayacak.
      yorumlayici.allocateTensors();
      _yorumlayici = yorumlayici;

      kurulumKapisi = ReceivePort();
      _isci = await Isolate.spawn(
        _isciGiris,
        _Kurulum(yorumlayici.address, kurulumKapisi.sendPort),
        errorsAreFatal: false,
      );
      // İşçi hazır olunca kendi kapısını bildiriyor.
      _isciKapisi = await kurulumKapisi.first
          .timeout(const Duration(seconds: 10)) as SendPort;
      lastError = null;
      return true;
    } catch (e) {
      lastError = 'yükleme: $e';
      _isci?.kill(priority: Isolate.immediate);
      _isci = null;
      _isciKapisi = null;
      _yorumlayici?.close();
      _yorumlayici = null;
      return false;
    } finally {
      kurulumKapisi?.close();
    }
  }

  void dispose() {
    _isciKapisi?.send(null);
    _isci?.kill(priority: Isolate.beforeNextEvent);
    _isci = null;
    _isciKapisi = null;
    _yorumlayici?.close();
    _yorumlayici = null;
  }

  /// Kamera karesini segmentleyip sınıf maskesi döndürür.
  ///
  /// **Asenkron ve tek seferlik.** Bir çıkarım sürerken gelen istek
  /// reddediliyor: kamera saniyede onlarca kare üretiyor ve kuyruk biriktirmek
  /// gecikmeyi büyütmekten başka işe yaramaz.
  Future<SegmentationMask?> run({
    required CameraImage image,
    required CameraDescription camera,
    required int deviceOrientationDegrees,
  }) async {
    final kapi = _isciKapisi;
    if (kapi == null) {
      lastError = 'yorumlayıcı yok';
      return null;
    }
    if (_mesgul) {
      lastError = 'önceki çıkarım sürüyor';
      return null;
    }

    final derece = cameraRotationDegrees(
      camera: camera,
      deviceOrientationDegrees: deviceOrientationDegrees,
    );
    if (derece == null) {
      lastError = 'döndürme çözülemedi';
      return null;
    }

    final kare = _kareMesaji(image, derece);
    if (kare == null) {
      lastError = 'kare biçimi tanınmadı: '
          'düzlem=${image.planes.length} '
          'bpr=${image.planes.first.bytesPerRow} en=${image.width}';
      return null;
    }

    final yanitKapisi = ReceivePort();
    _mesgul = true;
    try {
      kapi.send(kare(yanitKapisi.sendPort));
      // Zaman sınırı ŞART. İşçideki bir hata `await`e ulaşmayabiliyor ve o
      // zaman `_mesgul` kalıcı olarak takılı kalıyor: cihazda görülen
      // "basarisiz 0ms — null" satırlarının sebebi buydu.
      final sonuc =
          await yanitKapisi.first.timeout(const Duration(seconds: 6));

      if (sonuc is _Hata) {
        lastError = sonuc.mesaj;
        return null;
      }
      if (sonuc is! _Sonuc) {
        lastError = 'beklenmeyen yanıt: ${sonuc.runtimeType}';
        return null;
      }
      lastError = null;
      lastTimings = 'çevrim ${sonuc.cevrimMs} · çıkarım ${sonuc.cikarimMs}'
          ' · argmax ${sonuc.argmaxMs}';
      return SegmentationMask(
        classes: sonuc.maske,
        width: _kInput,
        height: _kInput,
      );
    } on TimeoutException {
      lastError = 'çıkarım zaman aşımı';
      return null;
    } catch (e) {
      lastError = 'çıkarım: $e';
      return null;
    } finally {
      yanitKapisi.close();
      _mesgul = false;
    }
  }

  /// Ham kareyi biçimine göre bir mesaj kurucusuna çevirir.
  ///
  /// Biçim tanınmazsa `null`: gri tonlamayla idare etmek modeli sessizce
  /// kötüleştirirdi ve bu projenin en pahalı dersi tam olarak sessiz bozulma.
  _Kare Function(SendPort)? _kareMesaji(CameraImage image, int derece) {
    final p0 = image.planes.first;
    final adim0 = p0.bytesPerRow;

    FrameFormat? bicim;
    Uint8List? duzlem1;
    var adim1 = 0;
    var pikselAdim1 = 2;

    if (image.planes.length == 1 && adim0 >= image.width * 4) {
      bicim = FrameFormat.bgra;
    } else if (image.planes.length == 1) {
      // Cihazda ölçülen: `düzlem=1 bpr=720 en=720`. Kamera eklentisi NV21'i
      // iki ayrı düzlem olarak DEĞİL, tek tamponda veriyor: önce Y bloğu
      // (yükseklik × satırAdımı), hemen ardından araya geçmiş VU bloğu.
      // İki düzlem beklendiği için biçim bir dönem hiç tanınmıyordu.
      bicim = FrameFormat.nv21SinglePlane;
    } else if (image.planes.length >= 2) {
      bicim = FrameFormat.yuv420Planar;
      final vu = image.planes[1];
      duzlem1 = vu.bytes;
      adim1 = vu.bytesPerRow;
      pikselAdim1 = vu.bytesPerPixel ?? 2;
    }
    if (bicim == null) return null;

    final secilen = bicim;
    return (yanit) => _Kare(
          yanit: yanit,
          bicim: secilen,
          // Gönderim sırasında kopyalanıyor (tek memcpy, ~1,4 MB). Taşıma
          // (`TransferableTypedData`) daha ucuz olurdu ama tamponu göndericiden
          // KOPARIRDI; aynı kareyi ML Kit de okuyor.
          duzlem0: p0.bytes,
          duzlem1: duzlem1,
          genislik: image.width,
          yukseklik: image.height,
          adim0: adim0,
          adim1: adim1,
          pikselAdim1: pikselAdim1,
          derece: derece,
        );
  }
}
