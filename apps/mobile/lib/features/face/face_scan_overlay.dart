/// Kamera üstündeki kılavuz ve tarama katmanı.
///
/// İki ayrı iş yapar ve ikisi ayrı sınıf:
///
/// * [FaceGuidePainter] — çekimden ÖNCE. Yüz ovali kılavuzu; kadraja göre
///   renk değiştirir, hazır olduğunda kilitlenir.
/// * [FaceScanPainter] — çekimden SONRA. Tarama çizgisi, ardından tespit
///   edilen noktaların yüze oturması.
///
/// Animasyondaki noktalar **gerçek tespit sonucundan** gelir. Sahte nokta
/// oynatmak, uygulamanın kendi hesabı hakkında yalan söylemesi olurdu; oysa
/// ürünün ilkesi hesaplananı yorumlanandan ayırmak.
library;

import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../theme/rytho_theme.dart';
import 'face_geometry.dart';

/// Tarama paleti — **uygulamanın kendi paletinden** türetilir.
///
/// İlk denemede camgöbeği/turkuaz bir bilim kurgu paleti kullanılmıştı;
/// teknik olarak hoş ama ekran uygulamaya ait görünmüyordu. Rytho'nun kimliği
/// mor-lila-magenta; sinematik his renkten değil **hareketten ve karanlıktan**
/// geliyor, o yüzden palet markaya çekildi.
class ScanPalette {
  const ScanPalette._();

  /// Arayan/beklerken — sönük, nötr.
  static const searching = RythoColors.parchmentDim;

  /// Hazır — kilitlenme rengi (olumlu).
  static const locked = RythoColors.celadon;

  /// Uyarı — kullanıcının düzeltmesi gereken bir şey var.
  static const warn = RythoColors.gold;

  /// Tarama çizgisi ve noktalar.
  static const beam = RythoColors.lilac;
  static const node = RythoColors.goldBright;

  /// Kılavuz dışının karartması. Zemin renginin koyu ucundan geliyor ki
  /// kamera görüntüsü uygulamanın içine gömülü hissettirsin.
  static const vignette = Color(0xCC0B0710);
}

// ---------------------------------------------------------------------------
// Çekim öncesi: kılavuz
// ---------------------------------------------------------------------------

class FaceGuidePainter extends CustomPainter {
  FaceGuidePainter({
    required this.quality,
    required this.pulse,
    required this.lockProgress,
  });

  final FrameQuality quality;

  /// 0..1 arası sürekli nabız; "arıyor" hâlinde kılavuzu canlı tutar.
  final double pulse;

  /// 0..1; yüz hazır konuma geldiğinde kilit halkasının dolma oranı.
  final double lockProgress;

  @override
  void paint(Canvas canvas, Size size) {
    final oval = guideOval(size);
    final renk = _renk(quality);

    // Dışarısı karartılır: kullanıcının gözü otomatik olarak ovalin içine
    // gider. Kılavuzu çizip ortamı aydınlık bırakmak, kadrajı hissettirmiyor.
    final disari = Path()
      ..addRect(Offset.zero & size)
      ..addOval(oval)
      ..fillType = PathFillType.evenOdd;
    canvas.drawPath(disari, Paint()..color = ScanPalette.vignette);

    // Oval hattı — kesikli ve dönen. Sabit bir çizgi "donmuş" görünüyor.
    _kesikliOval(canvas, oval, renk, pulse);

    // Köşe pençeleri: kadrajın teknik/optik hissi buradan geliyor.
    _pencesler(canvas, oval, renk);

    // Kilit halkası: hazır olduğunda oval boyunca dolar.
    if (lockProgress > 0) {
      canvas.drawArc(
        oval.deflate(6),
        -math.pi / 2,
        2 * math.pi * lockProgress.clamp(0.0, 1.0),
        false,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = 3
          ..strokeCap = StrokeCap.round
          ..color = ScanPalette.locked,
      );
    }
  }

  /// Kılavuz ovali — kadrajın ortasında, dikey olarak biraz yukarıda.
  ///
  /// Yüzün doğal ağırlık merkezi geometrik merkezin biraz üstündedir;
  /// oval tam ortaya konursa kullanıcı içgüdüsel olarak çenesini kaldırıyor.
  static Rect guideOval(Size size) {
    final w = size.width * 0.66;
    final h = w * 1.32;
    return Rect.fromCenter(
      center: Offset(size.width / 2, size.height * 0.44),
      width: w,
      height: h,
    );
  }

  static Color _renk(FrameQuality q) => switch (q) {
        FrameQuality.ready => ScanPalette.locked,
        FrameQuality.noFace => ScanPalette.searching,
        _ => ScanPalette.warn,
      };

  void _kesikliOval(Canvas canvas, Rect oval, Color renk, double faz) {
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.6
      ..strokeCap = StrokeCap.round
      ..color = renk.withValues(alpha: 0.85);

    const parca = 42;
    const dolu = 0.55; // her parçanın çizilen kısmı
    for (var i = 0; i < parca; i++) {
      final bas = (i / parca + faz) * 2 * math.pi;
      final son = bas + (dolu / parca) * 2 * math.pi;
      canvas.drawArc(oval, bas, son - bas, false, paint);
    }
  }

  void _pencesler(Canvas canvas, Rect oval, Color renk) {
    final kutu = oval.inflate(14);
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.2
      ..strokeCap = StrokeCap.round
      ..color = renk;
    final uzunluk = kutu.width * 0.13;

    void pence(Offset kose, double dx, double dy) {
      canvas.drawLine(kose, kose.translate(uzunluk * dx, 0), paint);
      canvas.drawLine(kose, kose.translate(0, uzunluk * dy), paint);
    }

    pence(kutu.topLeft, 1, 1);
    pence(kutu.topRight, -1, 1);
    pence(kutu.bottomLeft, 1, -1);
    pence(kutu.bottomRight, -1, -1);
  }

  @override
  bool shouldRepaint(FaceGuidePainter old) =>
      old.quality != quality ||
      old.pulse != pulse ||
      old.lockProgress != lockProgress;
}

// ---------------------------------------------------------------------------
// Çekim sonrası: tarama ve nokta yerleşmesi
// ---------------------------------------------------------------------------

/// Tarama animasyonunun aşamaları ve zamanlaması.
///
/// Toplam süre tespit süresinden **bağımsız** tutuldu. Tespit ~100 ms sürüyor;
/// animasyonu ona bağlamak göz kırpması kadar kısa, anlaşılmaz bir geçiş
/// verirdi. Buradaki süreler okunabilirlik için seçildi, oyalama için değil —
/// tespit zaten bitmiş durumda ve noktalar gerçek.
class ScanTiming {
  const ScanTiming._();

  /// Tarama çizgisinin yüzü baştan aşağı geçmesi.
  static const beam = Duration(milliseconds: 1100);

  /// Noktaların tek tek oturması.
  static const nodes = Duration(milliseconds: 1300);

  /// Bağ çizgilerinin çekilmesi.
  static const mesh = Duration(milliseconds: 600);

  static Duration get total => beam + nodes + mesh;
}

class FaceScanPainter extends CustomPainter {
  FaceScanPainter({
    required this.points,
    required this.progress,
    required this.imageSize,
  });

  /// Tespit edilen noktalar — GÖRÜNTÜ uzayında.
  final List<Offset> points;

  /// 0..1 arası toplam ilerleme.
  final double progress;

  /// Noktaların ait olduğu görüntünün boyutu; ekrana ölçeklemek için.
  final Size imageSize;

  @override
  void paint(Canvas canvas, Size size) {
    if (points.isEmpty || imageSize.width < 1 || imageSize.height < 1) return;

    final ekranNoktalari = _olcekle(size);
    final t = progress.clamp(0.0, 1.0);

    final beamPay = ScanTiming.beam.inMilliseconds / ScanTiming.total.inMilliseconds;
    final nodePay = ScanTiming.nodes.inMilliseconds / ScanTiming.total.inMilliseconds;

    final beamT = (t / beamPay).clamp(0.0, 1.0);
    final nodeT = ((t - beamPay) / nodePay).clamp(0.0, 1.0);
    final meshT = ((t - beamPay - nodePay) / (1 - beamPay - nodePay))
        .clamp(0.0, 1.0);

    if (meshT > 0) _mesh(canvas, ekranNoktalari, meshT);
    if (nodeT > 0) _noktalar(canvas, ekranNoktalari, nodeT);
    if (beamT > 0 && beamT < 1) _beam(canvas, size, beamT);
  }

  List<Offset> _olcekle(Size size) {
    // Kamera görüntüsü ekrana `BoxFit.cover` ile oturuyor; noktalar da aynı
    // dönüşümden geçmeli, yoksa yüzün üstünde değil yanında belirirler.
    final olcek = math.max(
        size.width / imageSize.width, size.height / imageSize.height);
    final dx = (size.width - imageSize.width * olcek) / 2;
    final dy = (size.height - imageSize.height * olcek) / 2;
    return [
      for (final p in points) Offset(p.dx * olcek + dx, p.dy * olcek + dy),
    ];
  }

  /// Tarama çizgisi: yüzü yukarıdan aşağı geçen ışık bandı.
  void _beam(Canvas canvas, Size size, double t) {
    final y = size.height * t;
    const yukseklik = 130.0;

    canvas.drawRect(
      Rect.fromLTWH(0, y - yukseklik / 2, size.width, yukseklik),
      Paint()
        ..shader = const LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            Color(0x00B79CFF),
            Color(0x66B79CFF),
            Color(0x00B79CFF),
          ],
        ).createShader(
            Rect.fromLTWH(0, y - yukseklik / 2, size.width, yukseklik)),
    );

    canvas.drawLine(
      Offset(0, y),
      Offset(size.width, y),
      Paint()
        ..strokeWidth = 1.4
        ..color = ScanPalette.beam.withValues(alpha: 0.9),
    );
  }

  /// Noktalar sırayla oturur; her biri küçük bir halkayla "kenetlenir".
  void _noktalar(Canvas canvas, List<Offset> noktalar, double t) {
    final gorunen = (noktalar.length * t).ceil();
    final dolgu = Paint()..color = ScanPalette.node;
    final halka = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.2
      ..color = ScanPalette.beam.withValues(alpha: 0.7);

    for (var i = 0; i < gorunen && i < noktalar.length; i++) {
      final p = noktalar[i];
      // Son oturan noktanın kenetlenme halkası açık, öncekiler sönmüş.
      final yas = (gorunen - i) / math.max(noktalar.length * 0.18, 1);
      final canli = (1 - yas).clamp(0.0, 1.0);

      canvas.drawCircle(p, 1.9, dolgu);
      if (canli > 0) {
        canvas.drawCircle(p, 2 + 9 * (1 - canli),
            halka..color = ScanPalette.beam.withValues(alpha: 0.7 * canli));
      }
    }
  }

  /// Komşu noktalar arasında bağ çizgileri — "ağ" hissi.
  ///
  /// Her noktayı herkesle bağlamak çorba görüntüsü veriyor; yalnızca kontur
  /// üzerindeki ardışık komşular bağlanıyor.
  void _mesh(Canvas canvas, List<Offset> noktalar, double t) {
    if (noktalar.length < 2) return;
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 0.9
      ..color = ScanPalette.beam.withValues(alpha: 0.35 * t);

    final yol = Path()..moveTo(noktalar.first.dx, noktalar.first.dy);
    final adet = (noktalar.length * t).ceil();
    for (var i = 1; i < adet && i < noktalar.length; i++) {
      yol.lineTo(noktalar[i].dx, noktalar[i].dy);
    }
    canvas.drawPath(yol, paint);
  }

  @override
  bool shouldRepaint(FaceScanPainter old) =>
      old.progress != progress || old.points != points;
}
