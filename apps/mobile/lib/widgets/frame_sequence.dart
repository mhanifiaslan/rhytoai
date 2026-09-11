import 'dart:ui' as ui;

import 'package:flutter/foundation.dart';
import 'package:flutter/scheduler.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:flutter/widgets.dart';

import 'motion.dart' show reduceMotion;

/// Animasyonlu WebP kare dizisi — `dart:ui` codec + Ticker. Video eklentisi
/// YOK (PBZ-K4: depo doktrini, bağımlılık eklenmez; animasyonlu WebP engine
/// codec'inde birinci sınıf format, Skia/Impeller fark etmez).
///
/// - `loop=false`: son karenin süresi dolunca Ticker durur, [onDone] BİR kez
///   çağrılır, son kare tutulur ([holdLast]; kapalıysa çizim boşalır).
/// - `loop=true`: her sarmada (son kareden ilk kareye dönüş anı) [onLoop].
/// - reduce-motion: kareler ilerletilmez; [onDone] HEMEN post-frame çağrılır
///   (durum makinesi çözmeyi beklemez — çizgiler anında dolar), arka planda
///   `frameCount−1` kez ilerleyip SON kare statik çizilir, [onLoop] hiç
///   tetiklenmez (doktrin: sürekli animatör tek karede durur).
/// - `TickerMode` sayesinde görünmeyen rotada durur.
/// - Varlık açılamazsa (bozuk/eksik dosya) [onDone] yine post-frame çağrılır
///   ki üstündeki durum makinesi askıda kalmasın; çizim boş kalır.
///
/// Sahiplik (SDK 3.44.7 `painting.dart` doğrulandı): `ImmutableBuffer`'ı
/// biz dispose ETMEYİZ — `instantiateImageCodecWithSize` `finally` içinde
/// kendisi dispose ediyor; çift dispose native hata. Her `FrameInfo.image`
/// bizde dispose edilir (`RawImage` kendi klonunu tutar, bizimkine dokunmaz);
/// `getNextFrame()` son kareden sonra 0'a sarar; `repetitionCount`
/// (0 = bir kez, −1 = sonsuz) yok sayılır — döngüyü [loop] yönetir.
class FrameSequence extends StatefulWidget {
  const FrameSequence({
    super.key,
    required String this.asset,
    this.loop = false,
    this.holdLast = true,
    this.onDone,
    this.onLoop,
    this.fit = BoxFit.cover,
  }) : bytes = null;

  /// Bellekten (test fixture'ı yolu): pubspec kaydından ve `flutter test`
  /// paket derlemesinden bağımsız.
  const FrameSequence.memory({
    super.key,
    required Uint8List this.bytes,
    this.loop = false,
    this.holdLast = true,
    this.onDone,
    this.onLoop,
    this.fit = BoxFit.cover,
  }) : asset = null;

  /// rootBundle yolu (`assets/anim/x.webp`); [bytes] verilmişse null.
  final String? asset;

  /// Ham dosya baytları; [asset] verilmişse null.
  final Uint8List? bytes;

  /// Sonda başa sar (her sarmada [onLoop]); kapalıysa son karede dur.
  final bool loop;

  /// `loop=false` bitince son kare ekranda kalsın mı.
  final bool holdLast;

  /// `loop=false`'ta bir kez; varlık açılamazsa da bir kez (askı yok).
  final VoidCallback? onDone;

  /// `loop=true`'da her sarmada; reduce-motion'da hiç.
  final VoidCallback? onLoop;

  final BoxFit fit;

  /// rootBundle bayt önbelleği — aynı varlık ikinci kez diskten okunmaz.
  static final _baytlar = <String, Future<Uint8List>>{};

  static Future<Uint8List> _yukle(String asset) => _baytlar.putIfAbsent(
        asset,
        () => rootBundle.load(asset).then(
          (d) => d.buffer.asUint8List(d.offsetInBytes, d.lengthInBytes),
          onError: (Object e, StackTrace st) {
            // Başarısız yükleme önbellekte kalmasın: sonraki deneme yeniden okur.
            _baytlar.remove(asset);
            Error.throwWithStackTrace(e, st);
          },
        ),
      );

  /// Sekme açılınca çağrılır ki ilk çekimde diskten okuma gecikmesi
  /// olmasın. Hata yutulur — eksik varlık, kare dizisinin kendi hata
  /// yolunda `onDone` verir.
  static Future<void> precache(Iterable<String> assets) async {
    for (final asset in assets) {
      try {
        await _yukle(asset);
      } catch (e) {
        debugPrint('FrameSequence önbellek ($asset): $e');
      }
    }
  }

  @override
  State<FrameSequence> createState() => FrameSequenceState();
}

/// Public: testler kare indeksini, kare sayısını ve bitişi buradan okur.
class FrameSequenceState extends State<FrameSequence>
    with SingleTickerProviderStateMixin {
  ui.Codec? _codec;
  ui.Image? _image;

  /// Tembel: ancak ilk kare hazır olup oynatılacaksa kurulur. `late final`
  /// olsaydı hiç başlamamış bir dizide (reduce-motion, hata yolu) ilk
  /// erişim dispose içinde olur ve `createTicker` TickerMode atasını
  /// arardı — sökülmüş ağaçta ata araması güvensiz.
  Ticker? _ticker;

  Duration _kareSuresi = Duration.zero;
  Duration _kareBasi = Duration.zero;
  int _kare = -1; // henüz kare çözülmedi
  bool _cozuluyor = false; // yeniden giriş yok: tek getNextFrame uçuşta
  bool _bitti = false;
  bool _azalt = false;
  bool _acildi = false;

  /// Varlık değişince / dispose'da artar: eski çözmelerin devamı çöpe.
  int _nesil = 0;

  /// Gösterilen karenin indeksi; −1 = henüz yok.
  @visibleForTesting
  int get frameIndex => _kare;

  @visibleForTesting
  int get frameCount => _codec?.frameCount ?? 0;

  /// `loop=false` bitti ya da varlık açılamadı.
  @visibleForTesting
  bool get isDone => _bitti;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final azalt = reduceMotion(context);
    if (!_acildi) {
      _acildi = true;
      _azalt = azalt;
      _ac();
      return;
    }
    // Çalışırken kapı açıldı: Ticker durur, bitiş hemen, son kare statik.
    if (azalt && !_azalt) {
      _azalt = true;
      _ticker?.stop();
      _bitir(postFrame: true);
      if (_codec != null) _sonKare();
    }
  }

  @override
  void didUpdateWidget(FrameSequence oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.asset != widget.asset ||
        !identical(oldWidget.bytes, widget.bytes)) {
      _kapat();
      _ac();
    }
  }

  @override
  void dispose() {
    _kapat();
    _ticker?.dispose();
    _ticker = null;
    super.dispose();
  }

  void _kapat() {
    _nesil++;
    _ticker?.stop();
    _image?.dispose();
    _image = null;
    _codec?.dispose();
    _codec = null;
    _kare = -1;
    _kareBasi = Duration.zero;
    _kareSuresi = Duration.zero;
    _bitti = false;
    _cozuluyor = false;
  }

  Future<void> _ac() async {
    final nesil = _nesil;
    // Statik sahne: bitiş çözmeye bağlanmaz — post-frame hemen.
    if (_azalt) _bitir(postFrame: true);
    try {
      final baytlar =
          widget.bytes ?? await FrameSequence._yukle(widget.asset!);
      if (!mounted || nesil != _nesil) return;
      final tampon = await ui.ImmutableBuffer.fromUint8List(baytlar);
      // Tampon buradan sonra codec'in: instantiateImageCodecWithSize
      // `finally` içinde kendisi dispose ediyor — biz ETMEYİZ.
      final codec = await ui.instantiateImageCodecWithSize(tampon);
      if (!mounted || nesil != _nesil) {
        codec.dispose();
        return;
      }
      _codec = codec;
      if (_azalt) {
        await _sonKare();
        return;
      }
      await _ilerle();
      if (mounted && nesil == _nesil && !_bitti) {
        final ticker = _ticker ??= createTicker(_tik);
        if (!ticker.isActive) ticker.start();
      }
    } catch (e) {
      debugPrint(
          'FrameSequence açılamadı (${widget.asset ?? 'bellek'}): $e');
      if (mounted && nesil == _nesil) _bitir(postFrame: true);
    }
  }

  /// Bir kare ilerle: önceki `ui.Image` bizde dispose edilir.
  Future<void> _ilerle() async {
    final codec = _codec;
    if (codec == null || _cozuluyor) return;
    final nesil = _nesil;
    _cozuluyor = true;
    try {
      final kare = await codec.getNextFrame();
      if (!mounted || nesil != _nesil || codec != _codec) {
        kare.image.dispose();
        return;
      }
      _image?.dispose();
      _image = kare.image;
      // Sıfır süre "sonsuza dek göster" demek (FrameInfo.duration): tek
      // kareli yükte zaten bitiş; çok karelide 100 ms varsayılır.
      _kareSuresi = kare.duration > Duration.zero
          ? kare.duration
          : const Duration(milliseconds: 100);
      _kare = (_kare + 1) % codec.frameCount;
      setState(() {});
      // Tek kare: sarılacak bir şey yok, loop olsa da durur.
      if (codec.frameCount <= 1) _bitir();
    } catch (e) {
      debugPrint('FrameSequence kare çözülemedi: $e');
      if (mounted && nesil == _nesil) _bitir();
    } finally {
      if (nesil == _nesil) _cozuluyor = false;
    }
  }

  /// reduce-motion: kalan kareleri sessizce geçip SON kareyi statik çiz.
  Future<void> _sonKare() async {
    final codec = _codec;
    if (codec == null || _cozuluyor) return;
    final nesil = _nesil;
    _cozuluyor = true;
    try {
      final hedef = codec.frameCount - 1;
      ui.FrameInfo? kare;
      while (_kare < hedef) {
        kare?.image.dispose();
        kare = await codec.getNextFrame();
        if (!mounted || nesil != _nesil || codec != _codec) {
          kare.image.dispose();
          return;
        }
        _kare++;
      }
      if (kare != null) {
        _image?.dispose();
        _image = kare.image;
      }
      setState(() {});
    } catch (e) {
      debugPrint('FrameSequence son kare çözülemedi: $e');
    } finally {
      if (nesil == _nesil) _cozuluyor = false;
    }
  }

  void _tik(Duration gecen) {
    final codec = _codec;
    if (codec == null || _cozuluyor || _bitti) return;
    if (gecen - _kareBasi < _kareSuresi) return;
    _kareBasi = gecen;
    if (_kare < codec.frameCount - 1) {
      _ilerle();
      return;
    }
    if (widget.loop) {
      // Sarma: ilk kare çözülmeye başlar, sınır aynı anda bildirilir —
      // çağıran bu anda sahneyi değiştirebilir (iniş klipleri havadaki
      // ilk kareyle aynı görüntüden başlar, sıçrama yok).
      _ilerle();
      widget.onLoop?.call();
      return;
    }
    _bitir();
  }

  void _bitir({bool postFrame = false}) {
    if (_bitti) return;
    _bitti = true;
    _ticker?.stop();
    if (!widget.holdLast && _image != null) {
      _image?.dispose();
      _image = null;
      setState(() {});
    }
    final onDone = widget.onDone;
    if (onDone == null) return;
    if (!postFrame) {
      onDone();
      return;
    }
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) onDone();
    });
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox.expand(
      child: RawImage(
        image: _image,
        fit: widget.fit,
        filterQuality: FilterQuality.medium,
      ),
    );
  }
}

/// Animasyon sahnesi (PBZ-K1 revizyonu): klipler SAF SİYAH zeminde
/// üretilir ve `ads/oracle-anim/build.py` siyahı ALFA'ya çevirir
/// (a = max(r,g,b), renk unpremultiply). Kare dizisi böylece uygulamanın
/// kendi yıldızlı zemininin ÜSTÜNE sıradan `srcOver` ile çizilir — tepsi
/// yok, mekân yok, "video penceresi" yok; katman/BackdropFilter fark
/// etmez. Sahne yalnız en-boy oranını sabitler, zemin ya da kart ÇİZMEZ.
class AnimStage extends StatelessWidget {
  const AnimStage({super.key, required this.child, this.aspect = 16 / 9});

  final Widget child;

  /// Klipler 16:9 üretildi; farklı oran `BoxFit.cover` ile kırpardı.
  final double aspect;

  @override
  Widget build(BuildContext context) {
    return AspectRatio(aspectRatio: aspect, child: child);
  }
}
