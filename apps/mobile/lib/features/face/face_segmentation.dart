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
library;

import 'dart:async';
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

/// Segmentasyon modeli — tek örnek, tembel yüklenir.
///
/// Yorumlayıcı pahalı: yükleme birkaç yüz milisaniye sürebiliyor. Kamera
/// ekranı açılırken bir kez kurulup ekran kapanınca bırakılıyor.
class FaceSegmenter {
  Interpreter? _yorumlayici;

  /// Çıkarımı AYRI bir isolate'ta koşturur.
  ///
  /// Ana isolate'ta koşarken ölçülen süre **594 ms**'ydi ve o süre boyunca
  /// arayüz tamamen donuyordu — üstelik bu kod kamera akışı geri çağrısının
  /// içinde. Yarım saniyelik donma hem başlı başına kusur, hem de o sırada
  /// kuyruğa giren dokunuşlar bir anda boşalıyor.
  IsolateInterpreter? _isolate;
  bool _denendi = false;
  bool _mesgul = false;

  bool get ready => _isolate != null;

  /// Girdi ve çıktı tamponları — bir kez ayrılır, her çağrıda üzerine yazılır.
  ///
  /// **İÇ İÇE OLMAK ZORUNDA.** Düz `Float32List` denendi ve çıkarım kırıldı:
  /// `Interpreter.runInference`, girdinin biçimini nesneden çıkarıyor
  /// (`getInputShapeIfDifferent`). Düz bir listenin biçimi `[196608]` olarak
  /// okunuyor, tensör o boyuta yeniden boyutlandırılmaya çalışılıyor ve
  /// `allocateTensors` düşüyor:
  ///
  ///     #1 Interpreter.allocateTensors (interpreter.dart:156)
  ///     #2 Interpreter.runInference (interpreter.dart:204)
  ///
  /// Yeniden tahsis pahalı olduğu için tamponlar saklanıyor; bu, ana
  /// isolate'ta ölçülen 594 ms'nin kayda değer bir kısmıydı.
  late final List<List<List<List<double>>>> _girdiTamponu = List.generate(
    1,
    (_) => List.generate(
      _kInput,
      (_) => List.generate(_kInput, (_) => List.filled(3, 0.0)),
    ),
  );
  late final List<List<List<List<double>>>> _ciktiTamponu = List.generate(
    1,
    (_) => List.generate(
      _kInput,
      (_) => List.generate(_kInput, (_) => List.filled(_kClasses, 0.0)),
    ),
  );

  /// Son hatanın metni — **yutulmuyor**.
  ///
  /// İlk sürümde `catch (_) { return null; }` vardı ve cihazda yalnızca
  /// "çalışmadı" görünüyordu. Sessiz yutma bu projede defalarca saat
  /// kaybettirdi; sebep görünür olmak zorunda.
  String? lastError;

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

  /// Modeli yükler. Başarısızlık **sessiz değil**: `false` döner ve çağıran
  /// ölçümü yapmadığını bilir.
  Future<bool> load() async {
    if (_denendi) return _yorumlayici != null;
    _denendi = true;
    try {
      final yorumlayici = await Interpreter.fromAsset(
        _kModelAsset,
        options: InterpreterOptions()..threads = 2,
      );
      _yorumlayici = yorumlayici;
      _isolate = await IsolateInterpreter.create(address: yorumlayici.address);
      lastError = null;
      return true;
    } catch (e) {
      lastError = 'yükleme: $e';
      _isolate = null;
      _yorumlayici = null;
      return false;
    }
  }

  void dispose() {
    _isolate?.close();
    _isolate = null;
    _yorumlayici?.close();
    _yorumlayici = null;
  }

  /// Kamera karesini segmentleyip sınıf maskesi döndürür.
  ///
  /// Maske, landmark'larla **aynı** (döndürülmüş) uzayda ölçeklenmiş olarak
  /// dönüyor: koordinat uzaylarını karıştırmak bu projede daha önce noktaların
  /// yüzün yanına düşmesine ve deklanşörün hiç açılmamasına yol açtı.
  /// **Asenkron ve tek seferlik.** Bir çıkarım sürerken gelen istek
  /// reddediliyor: kamera saniyede onlarca kare üretiyor ve kuyruk biriktirmek
  /// gecikmeyi büyütmekten başka işe yaramaz.
  Future<SegmentationMask?> run({
    required CameraImage image,
    required CameraDescription camera,
    required int deviceOrientationDegrees,
  }) async {
    final isolate = _isolate;
    if (isolate == null) {
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

    final girdi = _girdiTensoru(image, derece);
    if (girdi == null) {
      lastError = 'kare biçimi tanınmadı: '
          'düzlem=${image.planes.length} '
          'bpr=${image.planes.first.bytesPerRow} en=${image.width}';
      return null;
    }

    final cikti = _ciktiTamponu;

    _mesgul = true;
    try {
      // Zaman sınırı ŞART. Isolate içindeki bir hata `await`e ulaşmayabiliyor
      // ve o zaman `_mesgul` kalıcı olarak takılı kalıyor: cihazda görülen
      // "basarisiz 0ms — null" satırlarının sebebi buydu. İlk çağrı
      // `allocateTensors` içinde düştü, sonraki her çağrı sessizce reddedildi.
      await isolate
          .run(girdi, cikti)
          .timeout(const Duration(seconds: 6));
      lastError = null;
    } on TimeoutException {
      lastError = 'çıkarım zaman aşımı';
      return null;
    } catch (e) {
      lastError = 'çıkarım: $e';
      return null;
    } finally {
      _mesgul = false;
    }

    // En yüksek olasılıklı sınıf. Model kartı "post-processed (maxed) via
    // image segmenter API" diyor; API'yi kullanmadığımız için argmax burada.
    final maske = Uint8List(_kInput * _kInput);
    for (var y = 0; y < _kInput; y++) {
      final satir = cikti[0][y];
      for (var x = 0; x < _kInput; x++) {
        final p = satir[x];
        var enIyi = 0;
        var enIyiDeger = p[0];
        for (var c = 1; c < _kClasses; c++) {
          if (p[c] > enIyiDeger) {
            enIyiDeger = p[c];
            enIyi = c;
          }
        }
        maske[y * _kInput + x] = enIyi;
      }
    }

    return SegmentationMask(
      classes: maske,
      width: _kInput,
      height: _kInput,
    );
  }

  /// Kamera karesini 256×256 normalize RGB tensöre çevirir — döndürerek.
  ///
  /// Döndürme burada yapılıyor ki maske landmark'larla aynı uzayda çıksın.
  List<List<List<List<double>>>>? _girdiTensoru(
    CameraImage image,
    int derece,
  ) {
    final ceyrek = derece == 90 || derece == 270;
    final donmusW = ceyrek ? image.height : image.width;
    final donmusH = ceyrek ? image.width : image.height;

    final oku = _pikselOkuyucu(image);
    if (oku == null) return null;

    final tensor = _girdiTamponu;

    for (var y = 0; y < _kInput; y++) {
      final dy = (y * donmusH / _kInput).floor();
      for (var x = 0; x < _kInput; x++) {
        final dx = (x * donmusW / _kInput).floor();

        // Döndürülmüş (dx,dy) -> ham (u,v)
        final int u;
        final int v;
        switch (derece) {
          case 90:
            u = dy;
            v = image.height - 1 - dx;
          case 180:
            u = image.width - 1 - dx;
            v = image.height - 1 - dy;
          case 270:
            u = image.width - 1 - dy;
            v = dx;
          default:
            u = dx;
            v = dy;
        }

        final rgb = oku(u, v);
        final hucre = tensor[0][y][x];
        hucre[0] = rgb[0] / 255.0;
        hucre[1] = rgb[1] / 255.0;
        hucre[2] = rgb[2] / 255.0;
      }
    }
    return tensor;
  }

  /// Ham kare biçimine göre bir piksel okuyucu üretir.
  ///
  /// Biçim tanınmazsa `null`: gri tonlamayla idare etmek modeli sessizce
  /// kötüleştirirdi ve bugünün dersi tam olarak sessiz bozulma.
  /// NV21 renk dönüşümü — YVU sırası (NV21'de kroma V, sonra U).
  static List<int> _yuvToRgb(double y, double v, double u) => [
        (y + 1.370705 * v).round().clamp(0, 255),
        (y - 0.337633 * u - 0.698001 * v).round().clamp(0, 255),
        (y + 1.732446 * u).round().clamp(0, 255),
      ];

  List<int> Function(int u, int v)? _pikselOkuyucu(CameraImage image) {
    final p0 = image.planes.first;
    final stride = p0.bytesPerRow;
    final bayt = p0.bytes;

    // iOS: tek düzlem, BGRA (piksel başına dört bayt).
    if (image.planes.length == 1 && stride >= image.width * 4) {
      return (u, v) {
        final i = v * stride + u * 4;
        if (i + 2 >= bayt.length) return const [0, 0, 0];
        return [bayt[i + 2], bayt[i + 1], bayt[i]];
      };
    }

    // Android NV21 — TEK düzlem.
    //
    // Cihazda ölçülen: `düzlem=1 bpr=720 en=720`. Kamera eklentisi NV21'i
    // iki ayrı düzlem olarak DEĞİL, tek tamponda veriyor: önce Y bloğu
    // (yükseklik × satırAdımı), hemen ardından araya geçmiş VU bloğu.
    // İki düzlem beklediğim için biçim hiç tanınmıyordu.
    if (image.planes.length == 1) {
      final kromaBas = stride * image.height;
      return (u, v) {
        final yi = v * stride + u;
        if (yi >= bayt.length) return const [0, 0, 0];
        final Y = bayt[yi].toDouble();

        // Kroma yarı çözünürlüklü: iki satır ve iki sütun bir çifti paylaşır.
        final ci = kromaBas + (v >> 1) * stride + (u & ~1);
        if (ci + 1 >= bayt.length) {
          final g = Y.round().clamp(0, 255);
          return [g, g, g];
        }
        return _yuvToRgb(Y, bayt[ci] - 128.0, bayt[ci + 1] - 128.0);
      };
    }

    // YUV420 — ayrı düzlemler.
    if (image.planes.length >= 2) {
      final vu = image.planes[1];
      final ikiKatli = (vu.bytesPerPixel ?? 2) == 2;
      return (u, v) {
        final yi = v * stride + u;
        if (yi >= bayt.length) return const [0, 0, 0];
        final Y = bayt[yi].toDouble();

        final ci = (v >> 1) * vu.bytesPerRow +
            (u >> 1) * (ikiKatli ? 2 : 1);
        if (ci + 1 >= vu.bytes.length) {
          final g = Y.round().clamp(0, 255);
          return [g, g, g];
        }
        return _yuvToRgb(
            Y, vu.bytes[ci] - 128.0, vu.bytes[ci + 1] - 128.0);
      };
    }

    return null;
  }
}
