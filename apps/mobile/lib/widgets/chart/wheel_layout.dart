/// Çark geometrisi (HI-turu HA3) — SAF hesap, tek gerçek.
///
/// (boyut, veri, zoom) → halka yarıçapları + yelpazelenmiş glif
/// yerleşimleri + açı kirişi uçları + İSABET TABLOLARI tek değer
/// nesnesinde. HEM ressam HEM jest katmanı BUNU tüketir — eski çarkın
/// canlı kusuru (çizim size/2-46'da, isabet size/2-58'de; stellium'da
/// Venüs'e dokunup Merkür açılıyordu) bu mimariyle SINIF olarak ölür:
/// isabet konumu çizim konumunun kendisidir, iki ayrı hesap yoktur.
///
/// Ekran açısı sözleşmesi (profesyonel konvansiyon): Yükselen saat 9
/// yönünde, boylam saat yönünün TERSİNE artar. Evsiz düzende (saatsiz
/// natal / gökyüzü) 0° Koç solda.
library;

import 'dart:math' as math;
import 'dart:ui';

import 'chart_data.dart';

/// Küme içi asgari glif ayrımı (derece, zoom 1'de). Zoom büyüdükçe
/// gerçek konuma yaklaşılır (1/zoom).
const double kMinGlyphSeparationDeg = 7.0;

/// Gezegen dokunma yarıçapı (mantıksal px, sahne uzayında).
const double kPlanetHitRadius = 22.0;

/// Açı kirişi dokunma eşiği (nokta-segment uzaklığı, px).
const double kAspectHitDistance = 10.0;

/// Tek glifin çözülmüş yerleşimi.
class GlyphPlacement {
  const GlyphPlacement({
    required this.point,
    required this.ring,
    required this.trueLon,
    required this.displayLon,
    required this.center,
    required this.radius,
    required this.pointerFrom,
    required this.pointerTo,
  });

  final ChartPoint point;
  final int ring;

  /// Gerçek ekliptik boylam — işaretçi çizgisi buraya döner.
  final double trueLon;

  /// Yelpaze sonrası GÖSTERİM boylamı (küme yayılması).
  final double displayLon;

  final Offset center;
  final double radius;

  /// Glif → gerçek derece işaretçisi (yelpaze dürüstlüğü).
  final Offset pointerFrom;
  final Offset pointerTo;

  bool get fanned => (displayLon - trueLon).abs() > 0.01;
}

/// Tek açı kirişinin çözülmüş uçları. Kavuşum kiriş üretmez
/// ([isConjunction]) — jantta braket olarak çizilir.
class AspectSegment {
  const AspectSegment({
    required this.aspect,
    required this.a,
    required this.b,
    required this.isConjunction,
    this.rimMidLon,
  });

  final ChartAspect aspect;
  final Offset a;
  final Offset b;
  final bool isConjunction;

  /// Kavuşumda iki ucun jant orta boylamı (braket konumu).
  final double? rimMidLon;
}

/// Dokunma sonucu: gezegen YA DA açı (öncelik gezegende).
class WheelHit {
  const WheelHit.planet(GlyphPlacement this.placement) : segment = null;
  const WheelHit.aspect(AspectSegment this.segment) : placement = null;

  final GlyphPlacement? placement;
  final AspectSegment? segment;
}

class WheelLayout {
  WheelLayout._({
    required this.size,
    required this.data,
    required this.zoom,
    required this.ascLon,
    required this.center,
    required this.rimOuter,
    required this.signOuter,
    required this.signInner,
    required this.rulerInner,
    required this.houseInner,
    required this.aspectRadius,
    required this.outerBandOuter,
    required this.outerBandInner,
    required this.placements,
    required this.segments,
  });

  final Size size;
  final ChartData data;
  final double zoom;

  /// Dönüş referansı: evli düzende AC boylamı; evsizde 0 (Koç solda).
  final double ascLon;

  final Offset center;
  final double rimOuter;
  final double signOuter;
  final double signInner;

  /// Derece cetveli bandının iç yarıçapı (cetvel signInner→rulerInner).
  final double rulerInner;
  final double houseInner;
  final double aspectRadius;

  /// Bi-wheel dış bandı (tek çarkta 0).
  final double outerBandOuter;
  final double outerBandInner;

  /// [halka][glif] — yelpaze SONRASI yerleşimler; isabet tablosunun ta
  /// kendisi.
  final List<List<GlyphPlacement>> placements;

  final List<AspectSegment> segments;

  // -- açı/konum yardımcıları (ressamla paylaşılan TEK tanım) --

  double screenAngle(double lon) =>
      math.pi + (lon - ascLon) * math.pi / 180.0;

  Offset onCircle(double lon, double radius) {
    final a = screenAngle(lon);
    return Offset(center.dx + radius * math.cos(a),
        center.dy - radius * math.sin(a));
  }

  /// Dokunma çözümü: önce glifler (en yakın kazanır), sonra kirişler.
  WheelHit? hitTest(Offset pos) {
    GlyphPlacement? enYakin;
    var enYakinUzaklik = kPlanetHitRadius;
    for (final ring in placements) {
      for (final g in ring) {
        final d = (g.center - pos).distance;
        if (d < enYakinUzaklik) {
          enYakin = g;
          enYakinUzaklik = d;
        }
      }
    }
    if (enYakin != null) return WheelHit.planet(enYakin);

    AspectSegment? seg;
    var segUzaklik = kAspectHitDistance;
    for (final s in segments) {
      if (s.isConjunction) continue;
      final d = _pointToSegment(pos, s.a, s.b);
      if (d < segUzaklik) {
        seg = s;
        segUzaklik = d;
      }
    }
    return seg == null ? null : WheelHit.aspect(seg);
  }

  static double _pointToSegment(Offset p, Offset a, Offset b) {
    final ab = b - a;
    final len2 = ab.distanceSquared;
    if (len2 == 0) return (p - a).distance;
    var t = ((p - a).dx * ab.dx + (p - a).dy * ab.dy) / len2;
    t = t.clamp(0.0, 1.0);
    return (p - (a + ab * t)).distance;
  }

  // ---------------------------------------------------------------------

  factory WheelLayout.compute(Size size, ChartData data,
      {double zoom = 1.0}) {
    final merkez = Offset(size.width / 2, size.height / 2);
    final rim = size.shortestSide / 2 - 2;
    final biWheel = data.isBiWheel;

    // Yarıçap bütçesi: bi-wheel dış banda yer açar. Oranlar boyutla
    // ölçeklenir; zoom "boyut büyütme" olarak gelir (net metin stratejisi).
    final disBandDis = biWheel ? rim : 0.0;
    final disBandIc = biWheel ? rim - size.shortestSide * 0.085 : 0.0;
    final signOuter = biWheel ? disBandIc : rim;
    final signInner = signOuter - size.shortestSide * 0.075;
    final rulerInner = signInner - size.shortestSide * 0.028;
    final houseInner = rulerInner - size.shortestSide * 0.062;
    final aspectRadius = houseInner - size.shortestSide * 0.012;

    final ascLon =
        data.houses.isNotEmpty ? data.houses.first.absPosition : 0.0;

    final layout = WheelLayout._(
      size: size,
      data: data,
      zoom: zoom,
      ascLon: ascLon,
      center: merkez,
      rimOuter: rim,
      signOuter: signOuter,
      signInner: signInner,
      rulerInner: rulerInner,
      houseInner: houseInner,
      aspectRadius: aspectRadius,
      outerBandOuter: disBandDis,
      outerBandInner: disBandIc,
      placements: [],
      segments: [],
    );

    // Glif yarıçapları: iç halka cetvelin içinde, dış halka kendi bandında.
    final icGlifYaricap = (rulerInner + houseInner) / 2;
    final disGlifYaricap = biWheel ? (disBandDis + disBandIc) / 2 : 0.0;

    for (var r = 0; r < data.rings.length; r++) {
      final glifYaricap = r == 0 ? icGlifYaricap : disGlifYaricap;
      // İşaretçi hedefi: iç halka kendi cetveline, dış halka kendi
      // bandının iç kenarına döner (gerçek derecenin dürüst izi).
      final isaretciHedef = r == 0 ? rulerInner + 2 : signOuter + 2;
      layout.placements.add(_fanOut(
        layout,
        data.rings[r].points.where((p) => !p.isAngle).toList(),
        ring: r,
        glyphRadius: glifYaricap,
        pointerTargetRadius: isaretciHedef,
        zoom: zoom,
      ));
    }

    // Açı kirişleri: uçlar GERÇEK boylamda, aspectRadius üstünde.
    // Çözülemeyen uç = çizilmeyen açı (uydurma uç yok).
    for (final a in data.aspects) {
      final p1 = data.resolve(a.p1, a.p1Ring);
      final p2 = data.resolve(a.p2, a.p2Ring);
      if (p1 == null || p2 == null) continue;
      final kavusum = a.kind == 'conjunction';
      layout.segments.add(AspectSegment(
        aspect: a,
        a: layout.onCircle(p1.absPosition, aspectRadius),
        b: layout.onCircle(p2.absPosition, aspectRadius),
        isConjunction: kavusum,
        rimMidLon: kavusum
            ? _midLon(p1.absPosition, p2.absPosition)
            : null,
      ));
    }

    return layout;
  }

  /// İki boylamın kısa yay üzerindeki ortası.
  static double _midLon(double a, double b) {
    var fark = (b - a) % 360;
    if (fark > 180) fark -= 360;
    return (a + fark / 2) % 360;
  }

  /// Çarpışma yelpazesi v2: 0°/360° SARIMLI küme tespiti + küme içinde
  /// AÇISAL yayılma; kapasite aşımında radyal katman yedeği.
  ///
  /// Eski algoritmanın iki ölçülmüş kusuru: sarım yoktu (358° ile 2°
  /// komşuluğu görülmüyordu) ve %3 modulo döngüsü 4'lü stellium'da
  /// 1. katmana geri sarıp üst üste bindiriyordu.
  static List<GlyphPlacement> _fanOut(
    WheelLayout layout,
    List<ChartPoint> points, {
    required int ring,
    required double glyphRadius,
    required double pointerTargetRadius,
    required double zoom,
  }) {
    if (points.isEmpty) return const [];
    final minSep = math.max(3.0, kMinGlyphSeparationDeg / zoom);

    final sirali = [...points]
      ..sort((a, b) => a.absPosition.compareTo(b.absPosition));

    // SARIMLI kümeleme: en büyük boşluktan "kes", doğrusal kümele.
    var kesme = 0;
    var enBuyukBosluk = -1.0;
    for (var i = 0; i < sirali.length; i++) {
      final sonraki = sirali[(i + 1) % sirali.length];
      var bosluk = sonraki.absPosition - sirali[i].absPosition;
      if (bosluk <= 0) bosluk += 360;
      if (bosluk > enBuyukBosluk) {
        enBuyukBosluk = bosluk;
        kesme = (i + 1) % sirali.length;
      }
    }
    final dizi = [
      for (var i = 0; i < sirali.length; i++)
        sirali[(kesme + i) % sirali.length]
    ];

    final kumeler = <List<ChartPoint>>[];
    for (final p in dizi) {
      if (kumeler.isEmpty) {
        kumeler.add([p]);
        continue;
      }
      final son = kumeler.last.last;
      var bosluk = p.absPosition - son.absPosition;
      if (bosluk < 0) bosluk += 360;
      if (bosluk < minSep) {
        kumeler.last.add(p);
      } else {
        kumeler.add([p]);
      }
    }

    final yerlesimler = <GlyphPlacement>[];
    for (final kume in kumeler) {
      final n = kume.length;
      final merkezLon = _clusterMidLon(kume);
      // 4'e kadar tek katmanda açısal yayılma; 5+ stellium AYNI açısal
      // yayılmayla ≤4'lük alt gruplara bölünüp KATMANLANIR (katman k
      // glif çapı kadar içeride) — eski %3 modulo döngüsünün 4. glifi
      // 1. katmana geri sarıp üst üste bindirmesi böyle biter.
      const katmanBoyu = 4;
      const katmanAdimi = 16.0;
      for (var i = 0; i < n; i++) {
        final p = kume[i];
        final katman = i ~/ katmanBoyu;
        final katmandaki = i % katmanBoyu;
        final katmanEleman = math.min(katmanBoyu, n - katman * katmanBoyu);
        final yaricap = glyphRadius - katman * katmanAdimi;
        // Ayrım DERECE değil KORD hedefiyle: 7° küçük çarkta/iç katmanda
        // 21px'lik glif disklerini bindiriyordu — en az ~16px kord.
        final sep = math.max(minSep, 16.0 / yaricap * (180 / math.pi));
        final gosterim = n == 1
            ? p.absPosition
            : (merkezLon +
                    (katmandaki - (katmanEleman - 1) / 2) * sep +
                    360) %
                360;
        yerlesimler.add(GlyphPlacement(
          point: p,
          ring: ring,
          trueLon: p.absPosition,
          displayLon: gosterim,
          center: layout.onCircle(gosterim, yaricap),
          radius: yaricap,
          pointerFrom: layout.onCircle(gosterim, yaricap + 11),
          pointerTo: layout.onCircle(p.absPosition, pointerTargetRadius),
        ));
      }
    }
    return yerlesimler;
  }

  static double _clusterMidLon(List<ChartPoint> kume) {
    final ilk = kume.first.absPosition;
    var toplam = 0.0;
    for (final p in kume) {
      var fark = (p.absPosition - ilk) % 360;
      if (fark > 180) fark -= 360;
      toplam += fark;
    }
    return (ilk + toplam / kume.length + 360) % 360;
  }
}
