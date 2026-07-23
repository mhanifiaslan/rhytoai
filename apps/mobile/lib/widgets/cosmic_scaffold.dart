import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../theme/rytho_theme.dart';

/// Tüm ekranların zemini: uzay degradesi + yavaşça kayan, göz kırpan
/// yıldız alanı. Scaffold arka planı saydamdır; içerik camların arkasında
/// bu alanı görür.
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

/// Parallax hissi veren yıldız alanı: üç derinlik katmanı, farklı hızlarda
/// kayar; yıldızlar sinüs fazıyla göz kırpar.
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
        warm: random.nextDouble() < 0.18,
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
      decoration: const BoxDecoration(
        gradient: RadialGradient(
          center: Alignment(0, -0.6),
          radius: 1.6,
          colors: [RythoColors.ink, RythoColors.inkDeep],
        ),
      ),
      child: AnimatedBuilder(
        animation: _controller,
        builder: (_, _) => CustomPaint(
          painter: _StarfieldPainter(t: _controller.value, stars: _stars),
          size: Size.infinite,
        ),
      ),
    );
  }
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
      final baseColor = star.warm ? RythoColors.goldBright : RythoColors.parchment;
      paint.color = baseColor.withValues(
          alpha: twinkle * (0.10 + star.depth * 0.10));
      canvas.drawCircle(
          Offset(star.x * size.width, dy * size.height), star.size, paint);
    }
  }

  @override
  bool shouldRepaint(_StarfieldPainter old) => old.t != t;
}
