/// Üç para — 3D takla, kodla sürülür (PZ2: "şık, estetik, minimalist").
///
/// Doku GERÇEK, hareket KOD. Para yüzleri Higgsfield'da üretilmiş iki
/// still'dir (`assets/anim/coin_face.png` logo yüzü, `coin_back.png` düz
/// arka; alfa zemin) ve her para bir dikey eksen etrafında gerçek 3D
/// perspektifle döndürülür. Eski kare-dizisi klipleri (5 × ~0,6 MB WebP)
/// üç kusur taşıyordu ve üçü de yapısaldı: (1) tek görüntüde, 16:9 sahnede
/// DEV paralar; (2) döngü dikişi ve klip başı sıçraması — hareket modelin
/// insafındaydı; (3) iniş pozları rastgele (yan duran para) — sonuç
/// okunmuyordu. Kodla sürülünce üçü de kalkar:
///
/// * **Kusursuz döngü:** havadaki tüm frekanslar ortak periyodun ([kCoinLoop])
///   TAM KATI — `pose(t) == pose(t + T)` matematiksel olarak.
/// * **Kesintisiz iniş:** yanıt gelince o ANKİ açıdan hedef yüze
///   yavaşlanır; sınır beklemek, kesmek yok.
/// * **Determinist sonuç:** her atışta tam `logoUp` para logo yüzüyle iner
///   (0 ya da π radyan), hiçbiri yan durmaz.
/// * **Boyut:** para çapı [CoinToss.coinSize] (varsayılan 40 lp) — sahne
///   150×64 lp, glifin yanında sessiz durur.
///
/// Saf kinematik ([coinAirbornePose], [coinLandingPose]) widget'tan
/// bağımsız ve testlidir; ressam doku yüklenmeden de çizer (düz altın
/// disk) — doku asenkron gelir, ilk kare boş kalmaz.
library;

import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/foundation.dart';
import 'package:flutter/scheduler.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:flutter/widgets.dart';

import 'motion.dart' show reduceMotion;

/// Logo yüzü (Rytho işareti kabartma).
const String kCoinFaceAsset = 'assets/anim/coin_face.png';

/// Düz arka yüz (ince iç halka).
const String kCoinBackAsset = 'assets/anim/coin_back.png';

/// Havadaki döngünün periyodu; tüm frekanslar bunun tam katı.
const Duration kCoinLoop = Duration(milliseconds: 2600);

/// Bir atışın süresi (kalkış + düşüş + yerleşme).
const Duration kCoinTossDuration = Duration(milliseconds: 820);

/// Atış içinde yere TEMAS anı (0..1) — foley burada çalar.
const double kCoinContactAt = 0.78;

/// Havadaki turlar (periyot başına) — her para farklı ki üçü aynı anda aynı
/// yüzü göstermesin; hepsi tam sayı → döngü dikişsiz.
const List<int> _kTurlar = [2, 3, 2];

/// Faz farkları (radyan) — açı ve yükseklik için ayrı ayrı.
const List<double> _kAciFazi = [0.0, 1.2, 2.5];
const List<double> _kYukseklikFazi = [0.0, 2.1, 4.2];

/// Bir paranın anlık durumu: dikey eksen etrafındaki açı ve yükseklik.
@immutable
class CoinPose {
  const CoinPose({required this.angle, required this.height});

  /// Radyan; `cos(angle) > 0` → logo yüzü kameraya bakar.
  final double angle;

  /// 0 = yerde, 1 = en yüksek.
  final double height;

  /// Kameraya bakan yüz logo mu?
  bool get logoVisible => math.cos(angle) >= 0;

  @override
  bool operator ==(Object other) =>
      other is CoinPose && other.angle == angle && other.height == height;

  @override
  int get hashCode => Object.hash(angle, height);
}

/// Havadaki döngü: [t] saniye, [coin] 0..2.
///
/// Açı `2π·n·(t/T) + φ`, yükseklik `0,55 + 0,45·sin(2π·t/T + ψ)`; ikisi de
/// periyot T'de tam döner → `pose(t) == pose(t+T)`.
CoinPose coinAirbornePose(double t, int coin) {
  final u = t / (kCoinLoop.inMilliseconds / 1000);
  final aci = 2 * math.pi * _kTurlar[coin] * u + _kAciFazi[coin];
  final h = 0.55 + 0.45 * math.sin(2 * math.pi * u + _kYukseklikFazi[coin]);
  return CoinPose(angle: aci, height: h);
}

/// Hedef açı: [from]'dan en az 1,5 tur ileride, logo için `0`, arka için
/// `π` (mod 2π). Yavaşlama tam yüzde biter; yan duran para yoktur.
@visibleForTesting
double coinTargetAngle(double from, {required bool logoUp}) {
  final taban = logoUp ? 0.0 : math.pi;
  final k = ((from + 3 * math.pi - taban) / (2 * math.pi)).ceil();
  return taban + 2 * math.pi * k;
}

/// İniş: [p] 0..1 atış ilerlemesi. [from] atış başındaki durum; [lift]
/// true ise para yerden kalkar (2. atıştan itibaren), false ise zaten
/// havadadır (ilk atış — döngüden kesintisiz geçiş).
///
/// Kalkış 0–0,22 (yumuşak), düşüş 0,22–0,78 (yerçekimi: kare), temas
/// [kCoinContactAt], yerleşme 0,78–1 (tek küçük sekme, sönerek). Açı
/// 0–0,78 arasında `easeOutCubic` ile hedefe yavaşlar, temasla durur.
CoinPose coinLandingPose(double p, CoinPose from,
    {required bool logoUp, required bool lift}) {
  final hedef = coinTargetAngle(from.angle, logoUp: logoUp);
  final s = (p / kCoinContactAt).clamp(0.0, 1.0);
  final yavas = 1 - math.pow(1 - s, 3).toDouble(); // easeOutCubic
  final aci = from.angle + (hedef - from.angle) * yavas;

  double h;
  const kalkisBitis = 0.22;
  if (p < kalkisBitis) {
    final q = p / kalkisBitis;
    final tepe = lift ? 1.0 : math.max(from.height, 0.85);
    // Kalkış: easeOutQuad — hızlı çıkıp tepede yavaşlar.
    h = from.height + (tepe - from.height) * (1 - (1 - q) * (1 - q));
  } else if (p < kCoinContactAt) {
    final q = (p - kalkisBitis) / (kCoinContactAt - kalkisBitis);
    final tepe = lift ? 1.0 : math.max(from.height, 0.85);
    h = tepe * (1 - q * q); // yerçekimi
  } else {
    final q = (p - kCoinContactAt) / (1 - kCoinContactAt);
    h = 0.10 * math.sin(math.pi * q) * (1 - q); // tek sönen sekme
  }
  return CoinPose(angle: aci, height: h.clamp(0.0, 1.0));
}

/// [toss]. atışta logo yüzüyle inecek paralar: `k` tanesi, döner seçim —
/// altı atışta hep aynı paralar dönmesin.
@visibleForTesting
Set<int> coinsLogoUp(int toss, int logoUp) =>
    {for (var m = 0; m < logoUp.clamp(0, 3); m++) (toss + m) % 3};

/// Doku önbelleği — aynı `ui.Image` tüm sahnelere; süreç ömrü boyunca
/// yaşar (2 × ~256² RGBA ≈ 0,5 MB), dispose EDİLMEZ.
class CoinTextures {
  CoinTextures._();

  static final Map<String, Future<ui.Image>> _yukleniyor = {};
  static final Map<String, ui.Image> _hazir = {};

  /// Bayt → codec → ilk kare. `FrameSequence` ile aynı sahiplik kuralı:
  /// buffer codec'e geçer, biz `FrameInfo.image`'ı tutarız.
  static Future<ui.Image> load(String asset) {
    final hazir = _hazir[asset];
    if (hazir != null) return Future.value(hazir);
    return _yukleniyor.putIfAbsent(asset, () async {
      final data = await rootBundle.load(asset);
      final buffer = await ui.ImmutableBuffer.fromUint8List(
          data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes));
      final codec = await ui.instantiateImageCodecWithSize(buffer);
      final frame = await codec.getNextFrame();
      codec.dispose();
      _hazir[asset] = frame.image;
      return frame.image;
    });
  }

  /// Açılışta ısıt: ilk çekimde doku disk gecikmesi yok.
  static Future<void> precache() async {
    try {
      await Future.wait([load(kCoinFaceAsset), load(kCoinBackAsset)]);
    } catch (e) {
      debugPrint('Para dokuları yüklenemedi (düz disk çizilir): $e');
    }
  }

  static ui.Image? peek(String asset) => _hazir[asset];

  @visibleForTesting
  static void reset() {
    _yukleniyor.clear();
    _hazir.clear();
  }
}

/// Üç paranın sahnesi.
///
/// * `logoUp == null` → havada döngü.
/// * `logoUp` 0..3 → bu atışta o kadar para logo yüzüyle iner; [toss]
///   değişince yeni atış başlar (aynı `logoUp` art arda gelse de).
///   İlk atış (toss 0) havadan kesintisiz iner; sonrakiler yerden kalkar.
/// * [onContact] yere temas anında (foley), [onLanded] atış bitince — her
///   atışta birer kez.
/// * reduce-motion: hareket yok; havada üçü logo yüzüyle yerde durur, her
///   atış anında son pozuna geçer ve iki geri çağrı kare bitince gelir.
class CoinToss extends StatefulWidget {
  const CoinToss({
    super.key,
    this.logoUp,
    this.toss = 0,
    this.onContact,
    this.onLanded,
    this.coinSize = 40,
  });

  final int? logoUp;
  final int toss;
  final VoidCallback? onContact;
  final VoidCallback? onLanded;

  /// Para çapı (lp). Sahne genişliği `3·d + 2·gap`, yüksekliği `d + lift + 8`.
  final double coinSize;

  /// Paralar arası boşluk.
  double get gap => coinSize * 0.35;

  /// Havadaki en yüksek nokta (lp).
  double get lift => coinSize * 0.35;

  Size get sceneSize =>
      Size(3 * coinSize + 2 * gap, coinSize + lift + coinSize * 0.2);

  @override
  State<CoinToss> createState() => CoinTossState();
}

class CoinTossState extends State<CoinToss>
    with SingleTickerProviderStateMixin {
  late final Ticker _ticker;
  Duration _simdi = Duration.zero;

  /// İniş başlangıç durumları ve zamanı; null → havada.
  List<CoinPose>? _inisBaslangic;
  Duration _inisT0 = Duration.zero;
  bool _kalkarak = false;
  bool _temasEdildi = false;
  bool _indi = false;
  Set<int> _logoParalar = const {};

  /// Son çizilen pozlar (bitmiş atışta tutulur).
  List<CoinPose> _pozlar = const [
    CoinPose(angle: 0, height: 0),
    CoinPose(angle: 0, height: 0),
    CoinPose(angle: 0, height: 0),
  ];

  bool _azalt = false;
  bool _hazir = false;

  @visibleForTesting
  List<CoinPose> get poses => _pozlar;

  @visibleForTesting
  bool get isLanding => _inisBaslangic != null && !_indi;

  @override
  void initState() {
    super.initState();
    _ticker = createTicker(_tik);
    CoinTextures.precache().then((_) {
      if (mounted) setState(() {});
    });
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _azalt = reduceMotion(context);
    if (!_hazir) {
      _hazir = true;
      if (widget.logoUp != null) {
        _atisBasla(kalkarak: false);
      } else if (!_azalt) {
        _ticker.start();
      } else {
        _pozlar = _statikHava();
      }
    }
  }

  @override
  void didUpdateWidget(CoinToss oldWidget) {
    super.didUpdateWidget(oldWidget);
    final yeniAtis = widget.logoUp != null &&
        (oldWidget.logoUp == null || oldWidget.toss != widget.toss);
    if (yeniAtis) {
      // İlk atış havadan (kesintisiz), sonrakiler yerden kalkarak.
      _atisBasla(kalkarak: oldWidget.logoUp != null);
    } else if (widget.logoUp == null && oldWidget.logoUp != null) {
      // Havaya dönüş (yeniden çekim): döngü baştan.
      _inisBaslangic = null;
      _indi = false;
      _simdi = Duration.zero;
      if (_azalt) {
        setState(() => _pozlar = _statikHava());
      } else if (!_ticker.isActive) {
        _ticker.start();
      }
    }
  }

  @override
  void dispose() {
    _ticker.dispose();
    super.dispose();
  }

  List<CoinPose> _statikHava() =>
      List.filled(3, const CoinPose(angle: 0, height: 0));

  void _atisBasla({required bool kalkarak}) {
    _inisBaslangic = List.of(_pozlar);
    // Durmuş ticker yeniden başlayınca `elapsed` SIFIRDAN sayar; zaman
    // tabanı da sıfırlanmalı, yoksa ilerleme negatif kalır ve atış hiç
    // temas etmez (testte yakalandı: ikinci atışta clink yok).
    if (!_ticker.isActive) _simdi = Duration.zero;
    _inisT0 = _simdi;
    _kalkarak = kalkarak;
    _temasEdildi = false;
    _indi = false;
    _logoParalar = coinsLogoUp(widget.toss, widget.logoUp ?? 0);
    if (_azalt) {
      // Statik sahne: son poz hemen, geri çağrılar kare bitince (build
      // fazından üst setState çağrılmasın — CastScene'deki F5 dersi).
      _pozlar = [
        for (var i = 0; i < 3; i++)
          CoinPose(angle: _logoParalar.contains(i) ? 0 : math.pi, height: 0),
      ];
      _indi = true;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted) return;
        widget.onContact?.call();
        widget.onLanded?.call();
      });
      return;
    }
    if (!_ticker.isActive) _ticker.start();
  }

  void _tik(Duration elapsed) {
    _simdi = elapsed;
    final t = elapsed.inMicroseconds / 1e6;
    final baslangic = _inisBaslangic;
    if (baslangic == null) {
      setState(() {
        _pozlar = [for (var i = 0; i < 3; i++) coinAirbornePose(t, i)];
      });
      return;
    }
    final p = ((elapsed - _inisT0).inMicroseconds /
            kCoinTossDuration.inMicroseconds)
        .clamp(0.0, 1.0);
    setState(() {
      _pozlar = [
        for (var i = 0; i < 3; i++)
          coinLandingPose(p, baslangic[i],
              logoUp: _logoParalar.contains(i), lift: _kalkarak),
      ];
    });
    if (!_temasEdildi && p >= kCoinContactAt) {
      _temasEdildi = true;
      widget.onContact?.call();
    }
    if (p >= 1.0 && !_indi) {
      _indi = true;
      _ticker.stop();
      widget.onLanded?.call();
    }
  }

  @override
  Widget build(BuildContext context) {
    final boyut = widget.sceneSize;
    return RepaintBoundary(
      child: CustomPaint(
        size: boyut,
        painter: _CoinPainter(
          pozlar: _pozlar,
          coinSize: widget.coinSize,
          gap: widget.gap,
          lift: widget.lift,
          face: CoinTextures.peek(kCoinFaceAsset),
          back: CoinTextures.peek(kCoinBackAsset),
        ),
      ),
    );
  }
}

/// Üç parayı çizer: yer gölgesi → kenar kalınlığı → yüz dokusu → gölgeleme.
class _CoinPainter extends CustomPainter {
  _CoinPainter({
    required this.pozlar,
    required this.coinSize,
    required this.gap,
    required this.lift,
    required this.face,
    required this.back,
  });

  final List<CoinPose> pozlar;
  final double coinSize;
  final double gap;
  final double lift;
  final ui.Image? face;
  final ui.Image? back;

  // Altın tonları — uygulama paletinin altını (RythoColors.gold ailesi)
  // metal derinliğiyle: kenar koyu, doku yokken düz disk orta ton.
  static const _kenar = Color(0xFF7A5A22);
  static const _disk = Color(0xFFC9A24C);
  static const _diskKoyu = Color(0xFF8E6B2A);

  @override
  void paint(Canvas canvas, Size size) {
    final d = coinSize;
    final yer = lift + d; // paranın yerdeki merkezi (üstten)
    for (var i = 0; i < 3; i++) {
      final poz = pozlar[i];
      final cx = d / 2 + i * (d + gap);
      final cy = yer - d / 2 - poz.height * lift;
      final cosA = math.cos(poz.angle);
      final sinA = math.sin(poz.angle);
      final w = d * cosA.abs();

      // Yer gölgesi: yükseldikçe küçülür ve solar.
      final golgeW = d * (0.95 - 0.35 * poz.height);
      final golgeH = d * 0.18;
      final golgeAlfa = 0.42 * (1 - 0.55 * poz.height);
      final golgeMerkez = Offset(cx, yer + d * 0.06);
      final golgeRect = Rect.fromCenter(
          center: golgeMerkez, width: golgeW, height: golgeH);
      // Dairesel gradyanı elipse basmak: merkez etrafında dikey ölçek.
      final golgeMatris = Matrix4.identity()
        ..translateByDouble(golgeMerkez.dx, golgeMerkez.dy, 0, 1)
        ..scaleByDouble(1, golgeH / golgeW, 1, 1)
        ..translateByDouble(-golgeMerkez.dx, -golgeMerkez.dy, 0, 1);
      canvas.drawOval(
          golgeRect,
          Paint()
            ..shader = ui.Gradient.radial(
              golgeMerkez,
              golgeW / 2,
              [
                Color.fromRGBO(0, 0, 0, golgeAlfa),
                const Color.fromRGBO(0, 0, 0, 0),
              ],
              const [0.35, 1.0],
              TileMode.clamp,
              golgeMatris.storage,
            ));

      // Kenar kalınlığı: yüz döndükçe görünen sırt — yüzün arkasında,
      // dönüş yönüne kayık bir elips.
      final kalinlik = d * 0.10 * sinA.abs();
      if (kalinlik > 0.3) {
        final kayma = (cosA >= 0 ? -1 : 1) * (sinA >= 0 ? 1 : -1) * kalinlik;
        canvas.drawOval(
            Rect.fromCenter(
                center: Offset(cx + kayma / 2, cy),
                width: math.max(w, 1) + kalinlik.abs(),
                height: d),
            Paint()..color = _kenar);
      }

      if (w < 0.6) continue; // tam yan: yalnız kenar görünür

      final yuzRect =
          Rect.fromCenter(center: Offset(cx, cy), width: w, height: d);
      final doku = cosA >= 0 ? face : back;
      canvas.save();
      if (cosA < 0) {
        // Arka yüz ayna: gerçek bir para arkadan böyle görünür.
        canvas.translate(cx, 0);
        canvas.scale(-1, 1);
        canvas.translate(-cx, 0);
      }
      if (doku != null) {
        canvas.drawImageRect(
            doku,
            Rect.fromLTWH(
                0, 0, doku.width.toDouble(), doku.height.toDouble()),
            yuzRect,
            Paint()..filterQuality = FilterQuality.medium);
      } else {
        // Doku henüz yok: düz altın disk (ilk kare boş kalmasın).
        canvas.drawOval(
            yuzRect,
            Paint()
              ..shader = ui.Gradient.linear(
                  yuzRect.topLeft, yuzRect.bottomRight, [_disk, _diskKoyu]));
      }
      canvas.restore();

      // Gölgeleme: yüz kameradan döndükçe kararır (Fresnel hissi) ve
      // dönüşle kayan ince bir parıltı şeridi — metal.
      final karartma = 0.45 * (1 - cosA.abs());
      if (karartma > 0.01) {
        canvas.drawOval(yuzRect,
            Paint()..color = Color.fromRGBO(0, 0, 0, karartma));
      }
      final kayma = ((poz.angle / math.pi) % 1.0) * 2 - 1; // -1..1
      canvas.drawOval(
          yuzRect,
          Paint()
            ..shader = ui.Gradient.linear(
              Offset(yuzRect.left + w * (0.5 + kayma * 0.6), yuzRect.top),
              Offset(yuzRect.left + w * (0.5 + kayma * 0.6) + w * 0.5,
                  yuzRect.bottom),
              const [
                Color.fromRGBO(255, 255, 255, 0),
                Color.fromRGBO(255, 255, 255, 0.16),
                Color.fromRGBO(255, 255, 255, 0),
              ],
              const [0.0, 0.5, 1.0],
            ));
    }
  }

  @override
  bool shouldRepaint(_CoinPainter old) =>
      !listEquals(old.pozlar, pozlar) ||
      old.face != face ||
      old.back != back ||
      old.coinSize != coinSize;
}
