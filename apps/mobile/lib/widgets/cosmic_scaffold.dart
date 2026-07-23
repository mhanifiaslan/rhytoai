import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../theme/rytho_theme.dart';

/// Tüm ekranların zemini: siyah-mor uzay degradesi + yavaşça kayan,
/// göz kırpan yıldız alanı + üstte %3-4 opaklıkta dev zodyak çarkı
/// filigranı. Scaffold arka planı saydamdır.
class CosmicScaffold extends StatelessWidget {
  const CosmicScaffold({
    super.key,
    this.appBar,
    this.body,
    this.bottomNavigationBar,
    this.floatingActionButton,
    this.resizeToAvoidBottomInset,
    this.extendBody = false,
  });

  final PreferredSizeWidget? appBar;
  final Widget? body;
  final Widget? bottomNavigationBar;
  final Widget? floatingActionButton;
  final bool? resizeToAvoidBottomInset;
  final bool extendBody;

  @override
  Widget build(BuildContext context) {
    return Stack(children: [
      const Positioned.fill(child: StarfieldBackground()),
      Scaffold(
        backgroundColor: Colors.transparent,
        extendBody: extendBody,
        resizeToAvoidBottomInset: resizeToAvoidBottomInset,
        appBar: appBar,
        body: body,
        bottomNavigationBar: bottomNavigationBar,
        floatingActionButton: floatingActionButton,
      ),
    ]);
  }
}

/// Parallax hissi veren yıldız alanı: üç derinlik katmanı farklı hızlarda
/// kayar; yıldızlar sinüs fazıyla göz kırpar. Beyaz-lila tonlar.
class StarfieldBackground extends StatefulWidget {
  const StarfieldBackground({super.key});

  @override
  State<StarfieldBackground> createState() => _StarfieldBackgroundState();
}

class _StarfieldBackgroundState extends State<StarfieldBackground>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
      vsync: this, duration: const Duration(seconds: 120))
    ..repeat();

  static final List<_Star> _stars = _generateStars();

  static List<_Star> _generateStars() {
    final random = math.Random(7);
    return List.generate(140, (i) {
      final depth = i % 3; // 0 uzak, 2 yakın
      return _Star(
        x: random.nextDouble(),
        y: random.nextDouble(),
        size: 0.5 + depth * 0.45 + random.nextDouble() * 0.5,
        phase: random.nextDouble() * 2 * math.pi,
        depth: depth,
        warm: random.nextDouble() < 0.22,
      );
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: const BoxDecoration(gradient: RythoColors.backgroundGradient),
      child: Stack(fit: StackFit.expand, children: [
        // Üst kısımda hafif mor nebula parlaması
        const DecoratedBox(
          decoration: BoxDecoration(
            gradient: RadialGradient(
              center: Alignment(0.4, -1.1),
              radius: 1.3,
              colors: [Color(0x33471B6E), Colors.transparent],
            ),
          ),
        ),
        // Dev zodyak çarkı filigranı — ekranın üst kısmında, %3-4 opaklık
        const Positioned(
          top: -140,
          left: -60,
          right: -60,
          child: IgnorePointer(
            child: _ZodiacWatermark(height: 440),
          ),
        ),
        AnimatedBuilder(
          animation: _controller,
          builder: (_, _) => CustomPaint(
            painter: _StarfieldPainter(t: _controller.value, stars: _stars),
            size: Size.infinite,
          ),
        ),
      ]),
    );
  }
}

/// Çok hafif zodyak çarkı filigranı (statik CustomPaint).
class _ZodiacWatermark extends StatelessWidget {
  const _ZodiacWatermark({required this.height});
  final double height;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: height,
      child: const CustomPaint(painter: _ZodiacWatermarkPainter()),
    );
  }
}

class _ZodiacWatermarkPainter extends CustomPainter {
  const _ZodiacWatermarkPainter();

  static const _glyphs = [
    '♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓'
  ];

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = math.min(size.width, size.height) / 2 - 8;
    final stroke = Paint()
      ..color = RythoColors.lilac.withValues(alpha: 0.035)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;

    canvas.drawCircle(center, radius, stroke);
    canvas.drawCircle(center, radius * 0.82, stroke);
    canvas.drawCircle(center, radius * 0.5, stroke);

    for (var i = 0; i < 12; i++) {
      final a = i * math.pi / 6;
      final dir = Offset(math.cos(a), math.sin(a));
      canvas.drawLine(center + dir * radius * 0.82, center + dir * radius, stroke);
      // Glif dilimin ortasına
      final mid = a + math.pi / 12;
      final pos = center +
          Offset(math.cos(mid), math.sin(mid)) * radius * 0.91;
      final tp = TextPainter(
        text: TextSpan(
          text: _glyphs[i],
          style: TextStyle(
            fontSize: 18,
            color: RythoColors.lilac.withValues(alpha: 0.04),
          ),
        ),
        textDirection: TextDirection.ltr,
      )..layout();
      tp.paint(canvas, pos - Offset(tp.width / 2, tp.height / 2));
    }
  }

  @override
  bool shouldRepaint(_ZodiacWatermarkPainter old) => false;
}

class _Star {
  const _Star({
    required this.x,
    required this.y,
    required this.size,
    required this.phase,
    required this.depth,
    required this.warm,
  });
  final double x, y, size, phase;
  final int depth;
  final bool warm;
}

class _StarfieldPainter extends CustomPainter {
  _StarfieldPainter({required this.t, required this.stars});
  final double t;
  final List<_Star> stars;

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint();
    for (final star in stars) {
      // Derinliğe göre farklı hızda dikey süzülme
      final drift = t * (0.02 + star.depth * 0.03);
      final dy = (star.y + drift) % 1.0;
      final twinkle =
          0.35 + 0.65 * (0.5 + 0.5 * math.sin(star.phase + t * 2 * math.pi * 6));
      final baseColor = star.warm ? RythoColors.lilac : Colors.white;
      paint.color = baseColor.withValues(
          alpha: twinkle * (0.10 + star.depth * 0.10));
      canvas.drawCircle(
          Offset(star.x * size.width, dy * size.height), star.size, paint);
    }
  }

  @override
  bool shouldRepaint(_StarfieldPainter old) => old.t != t;
}
