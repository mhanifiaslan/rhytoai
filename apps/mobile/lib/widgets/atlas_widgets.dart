import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../theme/rytho_theme.dart';
import 'glass.dart';

/// "Levha" — v2'de cam panele delege eder; eski çağrı yüzeyi korunur.
class Plaque extends StatelessWidget {
  const Plaque({
    super.key,
    required this.child,
    this.label,
    this.padding = const EdgeInsets.all(16),
    this.margin = const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
  });

  final Widget child;
  final String? label;
  final EdgeInsets padding;
  final EdgeInsets margin;

  @override
  Widget build(BuildContext context) {
    return GlassPanel(
      label: label,
      padding: padding,
      margin: margin,
      child: child,
    );
  }
}

/// Birincil CTA butonu — v3: mor→magenta degrade dolgu, glow,
/// basınca scale 0.96 + haptic. Adı tarihsel (v1 "altın buton").
class GoldButton extends StatefulWidget {
  const GoldButton({
    super.key,
    required this.text,
    this.onPressed,
    this.busy = false,
    this.filled = true,
  });

  final String text;
  final VoidCallback? onPressed;
  final bool busy;
  final bool filled;

  @override
  State<GoldButton> createState() => _GoldButtonState();
}

class _GoldButtonState extends State<GoldButton> {
  bool _pressed = false;

  @override
  Widget build(BuildContext context) {
    final enabled = widget.onPressed != null && !widget.busy;
    return GestureDetector(
      onTapDown: enabled ? (_) => setState(() => _pressed = true) : null,
      onTapCancel: () => setState(() => _pressed = false),
      onTapUp: enabled
          ? (_) {
              setState(() => _pressed = false);
              HapticFeedback.lightImpact();
              widget.onPressed!();
            }
          : null,
      child: AnimatedScale(
        scale: _pressed ? 0.96 : 1.0,
        duration: const Duration(milliseconds: 120),
        curve: Curves.easeOut,
        child: Container(
          height: 52,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(18),
            gradient: enabled
                ? RythoColors.primaryGradient
                : const LinearGradient(colors: [
                    RythoColors.inkLighter,
                    RythoColors.inkLighter,
                  ]),
            border: Border.all(color: Colors.white.withValues(alpha: 0.12)),
            boxShadow: enabled
                ? const [BoxShadow(color: RythoColors.goldGlow, blurRadius: 22, spreadRadius: -4)]
                : null,
          ),
          child: widget.busy
              ? const SizedBox(
                  width: 22, height: 22, child: AstrolabeSpinner(size: 22))
              : Text(widget.text,
                  style: RythoText.label(14,
                      color: enabled
                          ? Colors.white
                          : RythoColors.parchmentDim)),
        ),
      ),
    );
  }
}

/// Bölüm ayracı: ince çizgi, merkezde ✦.
class SectionDivider extends StatelessWidget {
  const SectionDivider({super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 12),
      child: Row(children: [
        const Expanded(child: Divider()),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12),
          child: Text('✦', style: RythoText.mono(10, color: RythoColors.lilac)),
        ),
        const Expanded(child: Divider()),
      ]),
    );
  }
}

/// AI metni: sol kenarı mor degrade çizgili not bloğu.
class MarginNote extends StatelessWidget {
  const MarginNote({super.key, required this.text, this.title});

  final String text;
  final String? title;

  @override
  Widget build(BuildContext context) {
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            width: 3,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [RythoColors.violet, RythoColors.magenta],
              ),
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (title != null) ...[
                  Text(title!,
                      style: RythoText.label(11, color: RythoColors.lilac)),
                  const SizedBox(height: 6),
                ],
                Text(text, style: RythoText.body(15, height: 1.65)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Metni daktilo/akış hissiyle beliren blok — AI okumaları için.
class TypewriterText extends StatefulWidget {
  const TypewriterText({super.key, required this.text, required this.style});
  final String text;
  final TextStyle style;

  @override
  State<TypewriterText> createState() => _TypewriterTextState();
}

class _TypewriterTextState extends State<TypewriterText>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: Duration(milliseconds: (widget.text.length * 9).clamp(600, 6000)),
  )..forward();

  @override
  void didUpdateWidget(TypewriterText old) {
    super.didUpdateWidget(old);
    if (old.text != widget.text) _controller.forward(from: 0);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (_, _) {
        final count =
            (widget.text.length * Curves.easeOut.transform(_controller.value))
                .round();
        return Text(widget.text.substring(0, count), style: widget.style);
      },
    );
  }
}

/// Yükleme göstergesi: dönen usturlap kadranı.
class AstrolabeSpinner extends StatefulWidget {
  const AstrolabeSpinner({super.key, this.size = 44});
  final double size;

  @override
  State<AstrolabeSpinner> createState() => _AstrolabeSpinnerState();
}

class _AstrolabeSpinnerState extends State<AstrolabeSpinner>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller =
      AnimationController(vsync: this, duration: const Duration(seconds: 4))..repeat();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: const BoxDecoration(
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(color: RythoColors.goldGlow, blurRadius: 24, spreadRadius: -4),
        ],
      ),
      child: AnimatedBuilder(
        animation: _controller,
        builder: (_, _) => CustomPaint(
          size: Size.square(widget.size),
          painter: _AstrolabePainter(angle: _controller.value * 2 * math.pi),
        ),
      ),
    );
  }
}

class _AstrolabePainter extends CustomPainter {
  _AstrolabePainter({required this.angle});
  final double angle;

  @override
  void paint(Canvas canvas, Size size) {
    final center = size.center(Offset.zero);
    final radius = size.width / 2 - 1;
    final line = Paint()
      ..color = RythoColors.line
      ..style = PaintingStyle.stroke;
    final gold = Paint()
      ..color = RythoColors.lilac
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.2;

    canvas.drawCircle(center, radius, line);
    canvas.drawCircle(center, radius * 0.62, line);

    // Tik işaretleri
    for (var i = 0; i < 24; i++) {
      final a = i * math.pi / 12;
      final isMajor = i % 6 == 0;
      final start = center + Offset(math.cos(a), math.sin(a)) * radius;
      final end = center +
          Offset(math.cos(a), math.sin(a)) * (radius - (isMajor ? 5 : 2.5));
      canvas.drawLine(start, end, isMajor ? gold : line);
    }

    // Dönen ibre (alidade)
    final tip = center + Offset(math.cos(angle), math.sin(angle)) * radius * 0.85;
    final tail = center - Offset(math.cos(angle), math.sin(angle)) * radius * 0.35;
    canvas.drawLine(tail, tip, gold);
    canvas.drawCircle(center, 1.6, gold..style = PaintingStyle.fill);
  }

  @override
  bool shouldRepaint(_AstrolabePainter old) => old.angle != angle;
}

/// Canlı zodyak çemberi: /sky/now verisinden gerçek gezegen konumları.
class ZodiacRing extends StatefulWidget {
  const ZodiacRing({super.key, required this.planets, this.size = 300});

  /// [{name_tr, longitude, symbol, retrograde}, ...]
  final List<Map<String, dynamic>> planets;
  final double size;

  @override
  State<ZodiacRing> createState() => _ZodiacRingState();
}

class _ZodiacRingState extends State<ZodiacRing>
    with SingleTickerProviderStateMixin {
  late final AnimationController _breath = AnimationController(
      vsync: this, duration: const Duration(seconds: 4))
    ..repeat(reverse: true);

  @override
  void dispose() {
    _breath.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _breath,
      builder: (_, _) => CustomPaint(
        size: Size.square(widget.size),
        painter: _ZodiacRingPainter(
          planets: widget.planets,
          breath: Curves.easeInOut.transform(_breath.value),
        ),
      ),
    );
  }
}

class _ZodiacRingPainter extends CustomPainter {
  _ZodiacRingPainter({required this.planets, this.breath = 0});
  final List<Map<String, dynamic>> planets;

  /// 0..1 — gezegen glow'unun nefes fazı.
  final double breath;

  static const _planetGlyphs = {
    'Sun': '☉', 'Moon': '☽', 'Mercury': '☿', 'Venus': '♀', 'Mars': '♂',
    'Jupiter': '♃', 'Saturn': '♄', 'Uranus': '♅', 'Neptune': '♆', 'Pluto': '♇',
  };
  static const _signGlyphs = [
    '♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓'
  ];

  @override
  void paint(Canvas canvas, Size size) {
    final center = size.center(Offset.zero);
    final outer = size.width / 2 - 4;
    final inner = outer - 26;

    final linePaint = Paint()
      ..color = RythoColors.line
      ..style = PaintingStyle.stroke;

    canvas.drawCircle(center, outer, linePaint);
    canvas.drawCircle(center, inner, linePaint);
    canvas.drawCircle(center, inner * 0.55, linePaint);

    // 12 burç dilimi + glifler (0° Koç solda, saat yönünün tersi — klasik harita)
    for (var i = 0; i < 12; i++) {
      final boundary = math.pi - (i * 30) * math.pi / 180;
      canvas.drawLine(
        center + Offset(math.cos(boundary), math.sin(boundary)) * inner,
        center + Offset(math.cos(boundary), math.sin(boundary)) * outer,
        linePaint,
      );
      // glif dilimin ortasına
      final mid = math.pi - ((i * 30 + 15) * math.pi / 180);
      final glyphPos =
          center + Offset(math.cos(mid), math.sin(mid)) * (outer - 13);
      _drawText(canvas, _signGlyphs[i], glyphPos, 11, RythoColors.parchmentDim);
    }

    // Derece tikleri (her 10°)
    for (var d = 0; d < 360; d += 10) {
      final a = math.pi - d * math.pi / 180;
      canvas.drawLine(
        center + Offset(math.cos(a), math.sin(a)) * inner,
        center + Offset(math.cos(a), math.sin(a)) * (inner - 4),
        linePaint,
      );
    }

    // Gezegenler — nefes alan glow ile
    for (final p in planets) {
      final lon = (p['longitude'] as num).toDouble();
      final a = math.pi - lon * math.pi / 180;
      final retro = p['retrograde'] == true;
      final pos = center + Offset(math.cos(a), math.sin(a)) * (inner - 22);
      final glyph = _planetGlyphs[p['name']] ?? '•';
      final glowColor = retro ? RythoColors.copper : RythoColors.gold;
      final glowPaint = Paint()
        ..color = glowColor.withValues(alpha: 0.12 + 0.16 * breath)
        ..maskFilter =
            MaskFilter.blur(BlurStyle.normal, 6 + 5 * breath);
      canvas.drawCircle(pos, 9 + 3 * breath, glowPaint);
      _drawText(canvas, glyph, pos, 14,
          retro ? RythoColors.copper : RythoColors.gold);
      // konum işaretçisi
      final markPaint = Paint()
        ..color = retro ? RythoColors.copper : RythoColors.gold
        ..strokeWidth = 1;
      canvas.drawLine(
        center + Offset(math.cos(a), math.sin(a)) * (inner - 8),
        center + Offset(math.cos(a), math.sin(a)) * inner,
        markPaint,
      );
    }

    // Merkez yıldız
    _drawText(canvas, '✦', center, 12, RythoColors.gold);
  }

  void _drawText(Canvas canvas, String text, Offset at, double size, Color color) {
    final tp = TextPainter(
      text: TextSpan(text: text, style: TextStyle(fontSize: size, color: color)),
      textDirection: TextDirection.ltr,
    )..layout();
    tp.paint(canvas, at - Offset(tp.width / 2, tp.height / 2));
  }

  @override
  bool shouldRepaint(_ZodiacRingPainter old) =>
      old.planets != planets || old.breath != breath;
}
