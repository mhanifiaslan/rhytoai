/// "Yazıyor" noktaları glifi (OT5, kullanıcı seçimi).
///
/// Merkez sohbet düğmesinin içindeki işaret: konuşma balonu formunu
/// (kap zaten balon — bkz. glass.dart `_CenterAiButton`) üç noktalı
/// "biri yazıyor" göstergesiyle tamamlar — evrensel sohbet işareti.
/// Önceki glif ✦ idi ve iki turdur "chat'i anımsatmıyor" bulgusu
/// alıyordu; ✦ uygulamadaki 7+ satır içi "Rytho'ya sor" işaretinde
/// AYNEN yaşamaya devam eder (design-system doktrini).
///
/// Animasyon: [t] 0→1 fazı (dışarıdan gelen nefes denetleyicisi) üç
/// noktayı SIRAYLA parlatıp hafifçe yükseltir. reduceMotion'da çağıran
/// [t]'yi sabit verir — noktalar durağan çizilir, işaret yine okunur.
library;

import 'dart:math' as math;

import 'package:flutter/material.dart';

class TypingDotsGlyph extends StatelessWidget {
  const TypingDotsGlyph({
    super.key,
    required this.t,
    this.size = 26,
    this.color = Colors.white,
  });

  /// Animasyon fazı (0..1). Sabit değer = durağan çizim.
  final double t;

  final double size;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      size: Size(size, size * 0.42),
      painter: _TypingDotsPainter(t: t, color: color),
    );
  }
}

class _TypingDotsPainter extends CustomPainter {
  const _TypingDotsPainter({required this.t, required this.color});

  final double t;
  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final yaricap = size.height * 0.30;
    final merkezY = size.height / 2;
    final adim = size.width / 3;
    for (var i = 0; i < 3; i++) {
      // Her nokta fazın üçte birlik dilimini alır; sinüs tepesi noktayı
      // parlatır ve 1.5px yükseltir — daktilo ritmi.
      final yerel = ((t * 3) - i).clamp(0.0, 1.0);
      final vurgu = math.sin(yerel * math.pi);
      final boya = Paint()
        ..color = color.withValues(alpha: 0.45 + 0.55 * vurgu);
      canvas.drawCircle(
        Offset(adim * (i + 0.5), merkezY - 1.5 * vurgu),
        yaricap * (0.85 + 0.15 * vurgu),
        boya,
      );
    }
  }

  @override
  bool shouldRepaint(_TypingDotsPainter old) =>
      old.t != t || old.color != color;
}
