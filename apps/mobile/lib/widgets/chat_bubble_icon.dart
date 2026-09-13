/// Sohbet işareti — ÇİFT KONUŞMA BALONU (PZ3, kullanıcı kararı).
///
/// Alt dock'un merkez düğmesinin görseli: degrade balon kap + içinde
/// beyaz DOLU balon (üç noktası boyanmaz, KESİLİR) ve arkasında yalnız
/// konturu görünen ikinci balon. Kullanıcının verdiği referans birebir
/// buydu: üst üste binen iki balon, büyüğünde üç nokta.
///
/// ## Neden değişti
///
/// Önceki glif üç animasyonlu noktaydı (`TypingDotsGlyph`, OT5) ve cihaz
/// hükmü şuydu: *"sadece animasyonlu 3 nokta kafa karıştırabiliyor."*
/// Haklıydı — üç nokta tek başına "yükleniyor" da demektir. Şimdi
/// "konuşma"yı söyleyen şey noktalar değil, iki balonun ÜST ÜSTE
/// BİNMESİ: tek balon bir mesajdır, iki balon karşılıklı konuşmadır.
/// Sivri köşeler birbirinin aynası (büyük sol-alta, küçük sağ-alta bakar);
/// "karşılıklılık" duygusu tek bir ölçü eklemeden buradan gelir.
///
/// Dört bağımsız aday üretilip gerçek ressamlarından PNG basıldı ve göz
/// kararıyla seçildi (dock bağlamında, 62 px ve 24 px). Kazananın tek
/// üstünlüğü şuydu: dock'un en parlak öğesi olma rolünü KAYBETMEDEN
/// ilk bakışta "sohbet" diyor.
///
/// ## Teknik
///
/// Noktalar BOYANMAZ, KESİLİR (`Path.combine` difference): gövdeden
/// delinirler, altlarındaki degrade kaptan görünür. Boyanmış beyaz nokta
/// beyaz balonun içinde kaybolur; delik kaybolmaz, kontrastı balonun
/// kendi kontrastıdır — ikonu 24 px'te okunur yapan tek şey budur.
/// İkinci balonun konturu da araya boya sürülerek değil, büyük balonun
/// şişirilmiş silüeti clip'ten düşürülerek ayrılır.
///
/// [t] (0..1 döngüsel faz) iki iş yapar: delikler sırayla açılıp kapanır
/// (daktilo ritmi) ve ikinci balon soluk soluğa girer. **t = 0 ile t = 1
/// aynı kareyi verir** — çağıran `repeat()` ile besleyebilir, sarma
/// yerinde sıçrama olmaz. t sabit verilirse (reduceMotion) üç delik de
/// dinlenme yarıçapında, ikinci balon orta parlaklıkta durur — çizim
/// durağan ama tam okunur.
///
/// Kap da bu widget'ın işi: çağıran yalnız jest, haptic, erişilebilirlik
/// ve basma tepkisini taşır (bkz. `glass.dart` `_CenterAiButton`).
library;

import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../theme/rytho_theme.dart';

class ChatBubblesIcon extends StatelessWidget {
  const ChatBubblesIcon({super.key, required this.t, this.size = 62});

  /// Animasyon fazı (0..1). Sabit değer = durağan çizim.
  final double t;

  final double size;

  @override
  Widget build(BuildContext context) {
    // Döngünün iki ucunda da 0 olan nefes eğrisi — t=0 dinlenme hâli.
    final nefes = 0.5 - 0.5 * math.cos(2 * math.pi * t);
    final olcek = size / 62.0;

    // 0 = satır içi ikon ucu (≤28 px), 1 = dock düğmesi ucu (≥56 px).
    // Glif küçülürken ORANSAL olarak büyür: 24 px'te kabın nefes payı
    // gereksiz, okunurluk her şeyin önünde.
    final irilik = ((size - 28) / 28).clamp(0.0, 1.0);
    final glifKenar = size * (0.72 + (0.56 - 0.72) * irilik);

    // Kabın ölçüleri dock düğmesinden oranlandı: 24/62 ve 7/62. Sol-alt
    // köşenin sivriliği kabı balon yapan tek ipucu, ölçekle korunur.
    final buyukKose = Radius.circular(size * 0.387);
    final sivriKose = Radius.circular(size * 0.113);

    return Container(
      width: size,
      height: size,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        gradient: RythoColors.primaryGradient,
        borderRadius: BorderRadius.only(
          topLeft: buyukKose,
          topRight: buyukKose,
          bottomRight: buyukKose,
          bottomLeft: sivriKose,
        ),
        border: Border.all(
          color: RythoColors.parchment.withValues(alpha: 0.25),
          width: math.max(size * 0.0226, 0.8),
        ),
        // Glow yalnızca düğme boyunda: 24 px'te satır içi bir ikonun
        // etrafına taşan hale metni kirletir.
        boxShadow: size >= 34
            ? [
                BoxShadow(
                  color: RythoColors.magentaGlow,
                  blurRadius: (22 + 12 * nefes) * olcek,
                  spreadRadius: (1 + 2 * nefes) * olcek,
                ),
                BoxShadow(
                  color: RythoColors.goldGlow,
                  blurRadius: 40 * olcek,
                  spreadRadius: -2 * olcek,
                ),
              ]
            : null,
      ),
      child: CustomPaint(
        // Bileşimin kendi oranı 1.00 x 0.86 (iki balonun ortak sınırı).
        size: Size(glifKenar, glifKenar * 0.86),
        painter: _CiftBalonPainter(t: t, irilik: irilik),
      ),
    );
  }
}

class _CiftBalonPainter extends CustomPainter {
  const _CiftBalonPainter({required this.t, required this.irilik});

  final double t;

  /// 0 = 24 px ucu, 1 = 62 px ucu. Delik ve çizgi kalınlıkları buradan
  /// kalınlaşır: oran sabit kalsaydı küçük boyda delikler kapanırdı.
  final double irilik;

  @override
  void paint(Canvas canvas, Size size) {
    final g = size.width;

    // --- Büyük balon: üç köşe yuvarlak, sol-alt sivri (kabın dili) ---
    final govdeKose = Radius.circular(g * 0.18);
    final buyuk = RRect.fromRectAndCorners(
      Rect.fromLTWH(0, 0, g * 0.72, g * 0.60),
      topLeft: govdeKose,
      topRight: govdeKose,
      bottomRight: govdeKose,
      bottomLeft: Radius.circular(g * 0.055),
    );

    // --- İkinci balon: aynanın öbür yüzü, sağ-alt sivri ---
    final arkaKose = Radius.circular(g * 0.15);
    final kucuk = RRect.fromRectAndCorners(
      Rect.fromLTWH(g * 0.40, g * 0.36, g * 0.60, g * 0.50),
      topLeft: arkaKose,
      topRight: arkaKose,
      bottomLeft: arkaKose,
      bottomRight: Radius.circular(g * 0.045),
    );

    // İkinci balon büyük balonun ARKASINDA. Araya beyaz bir ayraç
    // çizilmez; büyük balonun şişirilmiş silüeti çizim alanından
    // düşürülür, boşluktan degrade kap görünür — negatif alan yine.
    final bosluk = math.max(g * 0.05, 1.2);
    final kesim = Path.combine(
      PathOperation.difference,
      Path()..addRect(Rect.fromLTWH(-g, -g, g * 3, g * 3)),
      Path()..addRRect(buyuk.inflate(bosluk)),
    );

    // Soluk soluğa: t=0'da orta parlaklık, tepe 0.95.
    final sis = 0.72 + 0.23 * (0.5 + 0.5 * math.sin(2 * math.pi * t));
    final cizgi = math.max(g * 0.038, 1.0);

    canvas.save();
    canvas.clipPath(kesim);
    canvas.drawRRect(
      kucuk.deflate(cizgi / 2),
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = cizgi
        ..strokeJoin = StrokeJoin.round
        ..color = RythoColors.parchment.withValues(alpha: sis),
    );
    canvas.restore();

    // --- Üç delik: boyanmaz, gövdeden kesilir ---
    final delikYaricap = g * (0.082 + (0.062 - 0.082) * irilik);
    final aralik = g * (0.195 + (0.165 - 0.195) * irilik);
    final merkez = Offset(g * 0.36, g * 0.30);

    final delikler = Path();
    for (var i = 0; i < 3; i++) {
      // Her delik fazın üçte birlik dilimini alır; tepede 0.78'den tam
      // yarıçapa açılır. Hiç kapanmaz — sabit t'de üçü de görünür kalsın.
      final yerel = ((t * 3) - i).clamp(0.0, 1.0);
      final vurgu = math.sin(yerel * math.pi);
      delikler.addOval(
        Rect.fromCircle(
          center: Offset(merkez.dx + aralik * (i - 1), merkez.dy),
          radius: delikYaricap * (0.78 + 0.22 * vurgu),
        ),
      );
    }

    canvas.drawPath(
      Path.combine(
        PathOperation.difference,
        Path()..addRRect(buyuk),
        delikler,
      ),
      Paint()..color = RythoColors.parchment,
    );
  }

  @override
  bool shouldRepaint(_CiftBalonPainter old) =>
      old.t != t || old.irilik != irilik;
}
