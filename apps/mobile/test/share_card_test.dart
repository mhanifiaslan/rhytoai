import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/features/share/share_card.dart';

/// Paylaşım kartındaki alıntı kesme mantığı.
///
/// Kart dışa açılan yüzdür: yarım cümleyle biten bir kart, uygulamanın
/// özensiz olduğunu düşündürür ve büyüme kanalının kendisini değersizleştirir.
void main() {
  group('ShareCard.excerpt', () {
    test('kısa metin olduğu gibi kalır', () {
      const metin = 'Bugün kısa bir aralık var.';
      expect(ShareCard.excerpt(metin), metin);
    });

    test('baştaki ve sondaki boşluklar kırpılır', () {
      expect(ShareCard.excerpt('  Bugün sabır günü.  '),
          'Bugün sabır günü.');
    });

    test('uzun metin cümle sınırından kesilir', () {
      final metin = '${'Birinci cümle burada. ' * 10}Son cümle.';
      final sonuc = ShareCard.excerpt(metin, maxChars: 100);

      expect(sonuc.length, lessThanOrEqualTo(100));
      expect(sonuc.endsWith('.'), isTrue,
          reason: 'cümle sınırından kesilmeli, yarım kalmamalı');
      expect(sonuc.endsWith('…'), isFalse);
    });

    test('ünlem ve soru işareti de cümle sonu sayılır', () {
      final metin = '${'Ne güzel bir gün! ' * 12}devam';
      final sonuc = ShareCard.excerpt(metin, maxChars: 90);
      expect(sonuc.endsWith('!'), isTrue);
    });

    test('cümle sınırı yoksa kelime sınırından kesilir', () {
      // Noktalama içermeyen tek uzun akış.
      final metin = List.filled(60, 'kelime').join(' ');
      final sonuc = ShareCard.excerpt(metin, maxChars: 100);

      expect(sonuc.endsWith('…'), isTrue);
      // Kelime ortasından kesilmemeli.
      expect(sonuc.replaceAll('…', '').trim().endsWith('kelime'), isTrue);
    });

    test('çok erken gelen cümle sınırı kullanılmaz', () {
      // İlk cümle çok kısa; ona kesmek metnin neredeyse tamamını atardı.
      final metin = 'Kısa. ${List.filled(60, 'kelime').join(' ')}';
      final sonuc = ShareCard.excerpt(metin, maxChars: 200);

      expect(sonuc.length, greaterThan(50),
          reason: 'ilk kısa cümleye kesip metni harcamamalı');
    });

    test('sınırdaki metin kesilmez', () {
      final metin = 'a' * 320;
      expect(ShareCard.excerpt(metin), metin);
    });
  });
}
