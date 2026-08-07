/// Takımyıldız ilerleme göstergesi (O3 — Yıldız Yolu).
///
/// Sıradan bir nokta-nokta ilerleme çubuğu değil: her tamamlanan adım bir
/// yıldız yakar ve önceki yıldıza altın bir çizgiyle bağlanır — sihirbaz
/// bittiğinde ortaya küçük bir takımyıldız çıkar. Psikoloji: ilk yıldız
/// YANMIŞ başlar (endowed progress — "başladın bile"), her adım görünür
/// bir kalıcı iz bırakır (kayıp isteksizliği: yarım takımyıldız bırakmak
/// zor gelir).
///
/// `reduceMotion` açıkken parlama/nabız yok — dolu ve boş yıldızlar
/// statik çizilir.
library;

import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../theme/rytho_theme.dart';
import '../../widgets/motion.dart';

class ConstellationProgress extends StatelessWidget {
  const ConstellationProgress({
    super.key,
    required this.total,
    required this.lit,
  });

  /// Toplam yıldız (adım) sayısı.
  final int total;

  /// Yanmış yıldız sayısı (karşılamada 1 — endowed progress).
  final int lit;

  @override
  Widget build(BuildContext context) {
    final azalt = reduceMotion(context);
    return SizedBox(
      height: 56,
      child: azalt
          ? CustomPaint(
              size: const Size(double.infinity, 56),
              painter: _ConstellationPainter(
                  total: total, lit: lit.toDouble(), pulse: 0),
            )
          : TweenAnimationBuilder<double>(
              // Yeni yıldız yumuşak yanar; çizgi ucuna doğru çizilir.
              tween: Tween(begin: 0, end: lit.toDouble()),
              duration: const Duration(milliseconds: 600),
              curve: Curves.easeOutCubic,
              builder: (context, deger, _) => _Nabiz(
                builder: (pulse) => CustomPaint(
                  size: const Size(double.infinity, 56),
                  painter: _ConstellationPainter(
                      total: total, lit: deger, pulse: pulse),
                ),
              ),
            ),
    );
  }
}

/// Sıradaki yıldızın nabzı — dikkat oraya çekilir ("sıradaki bu").
class _Nabiz extends StatefulWidget {
  const _Nabiz({required this.builder});

  final Widget Function(double pulse) builder;

  @override
  State<_Nabiz> createState() => _NabizState();
}

class _NabizState extends State<_Nabiz>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c = AnimationController(
      vsync: this, duration: const Duration(milliseconds: 1600))
    ..repeat(reverse: true);

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
        animation: _c,
        builder: (context, child) => widget.builder(_c.value),
      );
}

class _ConstellationPainter extends CustomPainter {
  _ConstellationPainter(
      {required this.total, required this.lit, required this.pulse});

  final int total;

  /// Kesirli olabilir (animasyon ortası): 2.4 = ikinci yıldız tam, üçüncüye
  /// giden çizginin %40'ı çizilmiş.
  final double lit;

  final double pulse;

  /// Yıldızlar hafif zikzaklı bir yol üzerinde — düz sıra "form alanı"
  /// hissi verirdi, zikzak gökyüzü. Ofsetler deterministik.
  Offset _konum(int i, Size size) {
    final adimGenisligi = size.width / (total + 1);
    final x = adimGenisligi * (i + 1);
    final y = size.height / 2 +
        math.sin(i * 2.1) * (size.height * 0.22);
    return Offset(x, y);
  }

  @override
  void paint(Canvas canvas, Size size) {
    final cizgi = Paint()
      ..color = RythoColors.goldBright.withValues(alpha: 0.5)
      ..strokeWidth = 1.4
      ..strokeCap = StrokeCap.round;
    final soluk = Paint()
      ..color = RythoColors.parchmentDim.withValues(alpha: 0.35)
      ..style = PaintingStyle.fill;

    // Çizgiler: tam yanmış yıldızlar arası dolu; kesir, ucu çizilmekte
    // olan çizgidir.
    for (var i = 0; i < total - 1; i++) {
      final bas = _konum(i, size);
      final son = _konum(i + 1, size);
      final tamamlanan = (lit - 1 - i).clamp(0.0, 1.0);
      if (tamamlanan <= 0) continue;
      canvas.drawLine(bas, Offset.lerp(bas, son, tamamlanan)!, cizgi);
    }

    for (var i = 0; i < total; i++) {
      final merkez = _konum(i, size);
      final yanmis = lit >= i + 1;
      final siradaki = !yanmis && lit >= i && lit < i + 1;
      if (yanmis) {
        // Parlama halkası + dolu yıldız.
        canvas.drawCircle(
            merkez,
            7,
            Paint()
              ..color = RythoColors.goldBright.withValues(alpha: 0.18)
              ..maskFilter =
                  const MaskFilter.blur(BlurStyle.normal, 6));
        _yildiz(canvas, merkez, 4.6,
            Paint()..color = RythoColors.goldBright);
      } else if (siradaki) {
        // Sıradaki yıldız soluk nabız atar — "yol burada devam ediyor".
        final r = 3.2 + pulse * 1.2;
        _yildiz(
            canvas,
            merkez,
            r,
            Paint()
              ..color = RythoColors.lilac
                  .withValues(alpha: 0.45 + pulse * 0.35));
      } else {
        canvas.drawCircle(merkez, 2.2, soluk);
      }
    }
  }

  /// Dört uçlu küçük yıldız (elmas + kısa çapraz kollar).
  void _yildiz(Canvas canvas, Offset c, double r, Paint boya) {
    final yol = Path()
      ..moveTo(c.dx, c.dy - r)
      ..quadraticBezierTo(c.dx + r * 0.25, c.dy - r * 0.25, c.dx + r, c.dy)
      ..quadraticBezierTo(c.dx + r * 0.25, c.dy + r * 0.25, c.dx, c.dy + r)
      ..quadraticBezierTo(c.dx - r * 0.25, c.dy + r * 0.25, c.dx - r, c.dy)
      ..quadraticBezierTo(c.dx - r * 0.25, c.dy - r * 0.25, c.dx, c.dy - r)
      ..close();
    canvas.drawPath(yol, boya);
  }

  @override
  bool shouldRepaint(_ConstellationPainter old) =>
      old.lit != lit || old.pulse != pulse || old.total != total;
}
