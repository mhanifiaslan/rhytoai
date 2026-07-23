import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../theme/rytho_theme.dart';

/// Yerli natal harita çarkı — Kerykeion SVG'sinin yerini alır.
/// Dış halka: burç dilimleri + glifler; orta halka: ev çizgileri ve numaraları;
/// gezegen glifleri mutlak boylamlarına yerleşir; merkezde açı (aspect) ağı.
/// Sweep animasyonuyla kurulur; gezegene dokununca bilgi geri çağrılır.
class NatalWheel extends StatefulWidget {
  const NatalWheel({
    super.key,
    required this.points,
    required this.houses,
    required this.aspects,
    this.size = 340,
    this.onPlanetTap,
  });

  /// [{name, name_tr, abs_position, retrograde, sign_tr, position}, ...]
  final List<Map<String, dynamic>> points;

  /// [{house, abs_position}, ...]
  final List<Map<String, dynamic>> houses;

  /// [{p1, p2, aspect}, ...]
  final List<Map<String, dynamic>> aspects;

  final double size;
  final ValueChanged<Map<String, dynamic>>? onPlanetTap;

  @override
  State<NatalWheel> createState() => _NatalWheelState();
}

class _NatalWheelState extends State<NatalWheel>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
      vsync: this, duration: const Duration(milliseconds: 1400))
    ..forward();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _handleTap(TapUpDetails details) {
    if (widget.onPlanetTap == null) return;
    final center = Offset(widget.size / 2, widget.size / 2);
    final ascAngle = _NatalWheelPainter.ascendantAngle(widget.houses);
    Map<String, dynamic>? nearest;
    double bestDistance = 26;
    for (final p in widget.points) {
      final pos = _NatalWheelPainter.planetOffset(
          p, center, widget.size / 2, ascAngle);
      final d = (details.localPosition - pos).distance;
      if (d < bestDistance) {
        bestDistance = d;
        nearest = p;
      }
    }
    if (nearest != null) widget.onPlanetTap!(nearest);
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapUp: _handleTap,
      child: AnimatedBuilder(
        animation: _controller,
        builder: (_, _) => CustomPaint(
          size: Size.square(widget.size),
          painter: _NatalWheelPainter(
            points: widget.points,
            houses: widget.houses,
            aspects: widget.aspects,
            progress: Curves.easeOutCubic.transform(_controller.value),
          ),
        ),
      ),
    );
  }
}

class _NatalWheelPainter extends CustomPainter {
  _NatalWheelPainter({
    required this.points,
    required this.houses,
    required this.aspects,
    required this.progress,
  });

  final List<Map<String, dynamic>> points;
  final List<Map<String, dynamic>> houses;
  final List<Map<String, dynamic>> aspects;
  final double progress;

  static const _signGlyphs = [
    '♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓'
  ];
  static const _planetGlyphs = {
    'Sun': '☉', 'Moon': '☽', 'Mercury': '☿', 'Venus': '♀', 'Mars': '♂',
    'Jupiter': '♃', 'Saturn': '♄', 'Uranus': '♅', 'Neptune': '♆',
    'Pluto': '♇', 'Chiron': '⚷', 'Mean_Lilith': '⚸',
    'True_North_Lunar_Node': '☊', 'True_South_Lunar_Node': '☋',
  };
  static const _aspectColors = {
    'conjunction': RythoColors.goldBright,
    'opposition': RythoColors.madder,
    'square': RythoColors.madder,
    'trine': RythoColors.celadon,
    'sextile': RythoColors.celadon,
    'quintile': RythoColors.parchmentDim,
    'quincunx': RythoColors.parchmentDim,
  };

  /// Klasik haritada Yükselen (1. ev başlangıcı) solda (9 yönünde) durur.
  static double ascendantAngle(List<Map<String, dynamic>> houses) {
    if (houses.isEmpty) return 0;
    return (houses.first['abs_position'] as num?)?.toDouble() ?? 0;
  }

  /// Mutlak ekliptik boylamı ekran açısına çevirir (Yükselen solda, saat
  /// yönünün tersine artar).
  static double _screenAngle(double absLongitude, double ascLongitude) {
    return math.pi + (absLongitude - ascLongitude) * math.pi / 180;
  }

  static Offset _polar(Offset center, double angle, double radius) {
    // Ekliptik boylam saat yönünün tersine artar → ekranda -sin
    return center + Offset(math.cos(angle), -math.sin(angle)) * radius;
  }

  static Offset planetOffset(Map<String, dynamic> point, Offset center,
      double outerRadius, double ascLongitude) {
    final lon = (point['abs_position'] as num?)?.toDouble() ?? 0;
    final angle = _screenAngle(lon, ascLongitude);
    return _polar(center, angle, outerRadius - 58);
  }

  @override
  void paint(Canvas canvas, Size size) {
    final center = size.center(Offset.zero);
    final outer = size.width / 2 - 2;
    final signInner = outer - 30; // burç halkası iç sınırı
    final houseInner = signInner - 26; // ev numarası halkası
    final aspectRadius = houseInner - 26; // açı ağı yarıçapı
    final asc = ascendantAngle(houses);

    final line = Paint()
      ..color = RythoColors.line
      ..style = PaintingStyle.stroke;
    final goldLine = Paint()
      ..color = RythoColors.gold.withValues(alpha: 0.75)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.2;

    // Sweep maskesi: çark saat yönünün tersine progress oranında çizilir
    final sweep = progress.clamp(0.0, 1.0);

    // Halkalar
    for (final r in [outer, signInner, houseInner, aspectRadius]) {
      canvas.drawArc(Rect.fromCircle(center: center, radius: r), math.pi,
          -2 * math.pi * sweep, false, line);
    }

    // Burç dilimleri + glifleri
    for (var i = 0; i < 12; i++) {
      final startLon = i * 30.0;
      final t = startLon / 360;
      if (t > sweep) continue;
      final a = _screenAngle(startLon, asc);
      canvas.drawLine(
          _polar(center, a, signInner), _polar(center, a, outer), line);
      final mid = _screenAngle(startLon + 15, asc);
      _drawText(canvas, _signGlyphs[i], _polar(center, mid, (outer + signInner) / 2),
          13, RythoColors.parchmentDim);
    }

    // Ev çizgileri + numaraları
    if (houses.isNotEmpty) {
      for (var i = 0; i < houses.length; i++) {
        final lon = (houses[i]['abs_position'] as num).toDouble();
        final rel = ((lon - asc) % 360 + 360) % 360;
        if (rel / 360 > sweep) continue;
        final a = _screenAngle(lon, asc);
        final isAxis = i % 3 == 0; // 1, 4, 7, 10. evler (AC/IC/DC/MC)
        canvas.drawLine(_polar(center, a, aspectRadius),
            _polar(center, a, signInner), isAxis ? goldLine : line);
        // Numara: bu ev ile sonraki ev arasının ortası
        final next = (houses[(i + 1) % 12]['abs_position'] as num).toDouble();
        var span = ((next - lon) % 360 + 360) % 360;
        if (span == 0) span = 30;
        final midHouse = _screenAngle(lon + span / 2, asc);
        _drawText(canvas, '${i + 1}',
            _polar(center, midHouse, (houseInner + aspectRadius) / 2), 9,
            RythoColors.parchmentDim.withValues(alpha: 0.75));
      }
    }

    // Açı ağı (merkez) — progress'in son çeyreğinde belirir
    final aspectAlpha = ((progress - 0.7) / 0.3).clamp(0.0, 1.0);
    if (aspectAlpha > 0) {
      final lonByName = {
        for (final p in points)
          p['name']: (p['abs_position'] as num?)?.toDouble() ?? 0
      };
      for (final aspect in aspects) {
        final lon1 = lonByName[aspect['p1']];
        final lon2 = lonByName[aspect['p2']];
        if (lon1 == null || lon2 == null) continue;
        final color = _aspectColors[aspect['aspect']] ?? RythoColors.line;
        final paint = Paint()
          ..color = color.withValues(alpha: 0.4 * aspectAlpha)
          ..strokeWidth = 0.9;
        canvas.drawLine(
          _polar(center, _screenAngle(lon1, asc), aspectRadius),
          _polar(center, _screenAngle(lon2, asc), aspectRadius),
          paint,
        );
      }
    }

    // Gezegenler — kalabalıkta radyal kaydırma ile çakışma önleme
    final sorted = [...points]..sort((a, b) =>
        ((a['abs_position'] as num?) ?? 0)
            .compareTo((b['abs_position'] as num?) ?? 0));
    double? prevLon;
    var offsetToggle = 0;
    for (final p in sorted) {
      final lon = (p['abs_position'] as num?)?.toDouble() ?? 0;
      final rel = ((lon - asc) % 360 + 360) % 360;
      if (rel / 360 > sweep) continue;
      if (prevLon != null && (lon - prevLon).abs() < 7) {
        offsetToggle = (offsetToggle + 1) % 3;
      } else {
        offsetToggle = 0;
      }
      prevLon = lon;
      final radius = signInner - 14 - offsetToggle * 15;
      final angle = _screenAngle(lon, asc);
      final pos = _polar(center, angle, radius);
      final retro = p['retrograde'] == true;
      final color = retro ? RythoColors.copper : RythoColors.goldBright;
      // İşaretçi çizgisi
      canvas.drawLine(_polar(center, angle, signInner),
          _polar(center, angle, signInner - 5),
          Paint()..color = color..strokeWidth = 1.2);
      _drawText(canvas, _planetGlyphs[p['name']] ?? '•', pos, 15, color);
      if (retro) {
        _drawText(canvas, 'R', pos + const Offset(9, -7), 7, RythoColors.copper);
      }
    }

    // Merkez
    _drawText(canvas, '✦', center, 11,
        RythoColors.gold.withValues(alpha: progress));
  }

  void _drawText(
      Canvas canvas, String text, Offset at, double fontSize, Color color) {
    final tp = TextPainter(
      text: TextSpan(
        text: text,
        style: TextStyle(fontSize: fontSize, color: color),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    tp.paint(canvas, at - Offset(tp.width / 2, tp.height / 2));
  }

  @override
  bool shouldRepaint(_NatalWheelPainter old) =>
      old.progress != progress || old.points != points;
}
