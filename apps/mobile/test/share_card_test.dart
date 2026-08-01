import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/features/share/share_card.dart';

/// Paylaşım kartına metnin sığdırılması.
///
/// Kart dışa açılan yüzdür. Kuralı şu: **okuma kesilmez.** Sığmıyorsa yazı
/// küçülür. Sabit bir boyutla kesmek, paylaşılan şeyin eksik olması demekti —
/// cümle sınırından kesmek yarım cümleyi önler ama okumayı yine yarıda bırakır.
void main() {
  // TextPainter ölçüm için bağlama ihtiyaç duyuyor.
  TestWidgetsFlutterBinding.ensureInitialized();

  // Yazı tipleri çalışma anında indiriliyor; testte ağ yok. Ölçüm bu yüzden
  // enjekte edilen düz bir stille yapılır — sınanan şey sığdırma MANTIĞI,
  // birebir piksel değerleri değil. Uygulamada kart paylaşıldığında yazı
  // tipleri arayüzden çoktan yüklüdür.
  TextStyle stil(double boyut) =>
      TextStyle(fontSize: boyut, height: 1.5);

  /// Tipik bir günlük burç yorumu (~110 kelime) — üretimde gelen uzunluk.
  const gercekciYorum =
      'Bugün Ay dolunay evresinde ilerlerken içindeki gürültü biraz artabilir; '
      'bu, bir şeylerin ters gittiği anlamına gelmiyor, yalnızca uzun süredir '
      'ertelediğin bir konunun yüzeye çıktığını gösteriyor. Satürn retrosu '
      'sorumluluk aldığın alanlarda seni yavaşlatıyor ve bu yavaşlama işine '
      'yarayabilir: aceleyle verilmiş bir karar bugün geri dönüp seni '
      'yoracaktı. Öğleden sonra iletişim kanalları açılıyor, konuşulması '
      'gereken bir şey varsa bugün söylenmesi yarına kalmasından iyi. '
      'Kendine bir şey vaat etme; bunun yerine bugün yapabileceğin en küçük '
      'somut adımı seç ve onu bitir. Akşama doğru enerjin düşebilir, bunu '
      'başarısızlık sayma.';

  group('bodyText — okuma kesilmez', () {
    test('gerçekçi uzunluktaki yorum olduğu gibi kalır', () {
      final sonuc = ShareCard.bodyText(styleBuilder: stil, gercekciYorum);
      expect(sonuc, gercekciYorum.trim(),
          reason: 'tipik bir okuma hiç kırpılmamalı');
      expect(sonuc.endsWith('…'), isFalse);
    });

    test('kısa metin olduğu gibi kalır', () {
      const metin = 'Bugün kısa bir aralık var.';
      expect(ShareCard.bodyText(styleBuilder: stil, metin), metin);
    });

    test('baştaki ve sondaki boşluklar kırpılır', () {
      expect(ShareCard.bodyText(styleBuilder: stil, '  Bugün sabır günü.  '), 'Bugün sabır günü.');
    });

    test('olağandışı uzun metin son çare olarak kırpılır', () {
      // Üretimde gelmez; kartın taşmasını engelleyen emniyet valfi.
      final cokUzun = gercekciYorum * 8;
      final sonuc = ShareCard.bodyText(styleBuilder: stil, cokUzun);
      expect(sonuc.length, lessThan(cokUzun.length));
      // Kırpma yine cümle sınırından olmalı.
      expect(sonuc.endsWith('.') || sonuc.endsWith('…'), isTrue);
    });
  });

  group('fittedFontSize — sığdırma', () {
    test('kısa metin en büyük boyutta gösterilir', () {
      final boyut = ShareCard.fittedFontSize(styleBuilder: stil, 'Bugün kısa bir aralık var.');
      expect(boyut, 52);
    });

    test('uzun metinde yazı küçülür ama tabanın altına inmez', () {
      final boyut = ShareCard.fittedFontSize(styleBuilder: stil, gercekciYorum);
      expect(boyut, lessThan(52), reason: 'uzun metin küçülmeli');
      expect(boyut, greaterThanOrEqualTo(26), reason: 'okunmaz olmamalı');
    });

    test('metin uzadıkça boyut küçülür', () {
      final kisa = ShareCard.fittedFontSize(styleBuilder: stil, 'Bugün sabır günü.');
      final orta = ShareCard.fittedFontSize(styleBuilder: stil, gercekciYorum);
      final uzun = ShareCard.fittedFontSize(styleBuilder: stil, gercekciYorum * 2);
      expect(orta, lessThanOrEqualTo(kisa));
      expect(uzun, lessThan(orta));
    });

    test('seçilen boyutta metin gerçekten sığar', () {
      // Sığdırma iddiasının kendisi ölçülüyor: bulunan boyutta metnin
      // yüksekliği alanı aşmamalı.
      for (final metin in [gercekciYorum, 'Kısa.', gercekciYorum * 2]) {
        final govde = ShareCard.bodyText(styleBuilder: stil, metin);
        final boyut = ShareCard.fittedFontSize(styleBuilder: stil, govde);
        expect(ShareCard.fitsAt(govde, boyut, styleBuilder: stil), isTrue,
            reason: 'boyut $boyut ile sığmalı');
      }
    });

    test('boş metin çökmez', () {
      expect(() => ShareCard.fittedFontSize(styleBuilder: stil, ''), returnsNormally);
      expect(() => ShareCard.bodyText(styleBuilder: stil, ''), returnsNormally);
    });
  });

  group('clampToSentence — son çare', () {
    test('cümle sınırından keser', () {
      final metin = '${'Birinci cümle burada. ' * 10}Son cümle.';
      final sonuc = ShareCard.clampToSentence(metin, 100);
      expect(sonuc.length, lessThanOrEqualTo(100));
      expect(sonuc.endsWith('.'), isTrue);
      expect(sonuc.endsWith('…'), isFalse);
    });

    test('ünlem ve soru işareti de cümle sonu sayılır', () {
      final metin = '${'Ne güzel bir gün! ' * 12}devam';
      expect(ShareCard.clampToSentence(metin, 90).endsWith('!'), isTrue);
    });

    test('cümle sınırı yoksa kelime sınırından keser', () {
      final metin = List.filled(60, 'kelime').join(' ');
      final sonuc = ShareCard.clampToSentence(metin, 100);
      expect(sonuc.endsWith('…'), isTrue);
      expect(sonuc.replaceAll('…', '').trim().endsWith('kelime'), isTrue);
    });

    test('çok erken gelen cümle sınırı kullanılmaz', () {
      final metin = 'Kısa. ${List.filled(60, 'kelime').join(' ')}';
      expect(ShareCard.clampToSentence(metin, 200).length, greaterThan(50));
    });
  });
}
