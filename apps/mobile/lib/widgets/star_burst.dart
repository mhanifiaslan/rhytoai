import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../theme/rytho_theme.dart';
import '../theme/rytho_tokens.dart';
import 'motion.dart';

/// Tek atışlık yıldız patlaması (R12-C1) — StarfieldBackground boyacısının
/// torunu. Hazır Lottie konfetisi yerine markanın kendi parçacık dili:
/// altın+magenta kıvılcımlar merkezden dışa saçılır, sönerek kaybolur.
/// Döngü YOK; animasyon bitince hiçbir şey çizilmez. Reduce-motion'da hiç
/// başlamaz — kutlamanın bilgisini taşıyan şey patlama değil, eşlik ettiği
/// içerik (rozet/mühür).
class StarBurst extends StatefulWidget {
  const StarBurst({
    super.key,
    this.size = 240,
    this.particles = 48,
    this.duration = const Duration(milliseconds: 1100),
  });

  final double size;
  final int particles;
  final Duration duration;

  @override
  State<StarBurst> createState() => _StarBurstState();
}

class _StarBurstState extends State<StarBurst>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller =
      AnimationController(vsync: this, duration: widget.duration)..forward();

  late final List<_Kivilcim> _kivilcimlar = _uret(widget.particles);

  static List<_Kivilcim> _uret(int adet) {
    final rastgele = math.Random();
    return List.generate(adet, (_) {
      return _Kivilcim(
        aci: rastgele.nextDouble() * 2 * math.pi,
        hiz: 0.45 + rastgele.nextDouble() * 0.55,
        boy: 1.2 + rastgele.nextDouble() * 1.8,
        altin: rastgele.nextDouble() < 0.65,
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
    if (reduceMotion(context)) return SizedBox.square(dimension: widget.size);
    return IgnorePointer(
      child: AnimatedBuilder(
        animation: _controller,
        builder: (_, _) => _controller.isCompleted
            ? SizedBox.square(dimension: widget.size)
            : CustomPaint(
                size: Size.square(widget.size),
                painter: _StarBurstPainter(
                    t: _controller.value, kivilcimlar: _kivilcimlar),
              ),
      ),
    );
  }
}

class _Kivilcim {
  const _Kivilcim({
    required this.aci,
    required this.hiz,
    required this.boy,
    required this.altin,
  });
  final double aci, hiz, boy;
  final bool altin;
}

class _StarBurstPainter extends CustomPainter {
  _StarBurstPainter({required this.t, required this.kivilcimlar});
  final double t;
  final List<_Kivilcim> kivilcimlar;

  @override
  void paint(Canvas canvas, Size size) {
    final merkez = size.center(Offset.zero);
    final yaricap = size.width / 2;
    final ilerleme = RythoMotion.enter.transform(t);
    final paint = Paint();
    for (final k in kivilcimlar) {
      final uzaklik = ilerleme * k.hiz * yaricap;
      final konum =
          merkez + Offset(math.cos(k.aci), math.sin(k.aci)) * uzaklik;
      final renk = k.altin ? RythoColors.gold : RythoColors.magenta;
      paint.color = renk.withValues(alpha: (1 - t) * 0.9);
      canvas.drawCircle(konum, k.boy * (1 - t * 0.4), paint);
    }
  }

  @override
  bool shouldRepaint(_StarBurstPainter old) => old.t != t;
}
