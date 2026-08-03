import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/core/contact_match.dart';

/// Rehber esleme normalizasyonunun degismezleri (Revize R3).
///
/// Buradaki her hata SESSIZ: "0555 111 22 33" ile "+905551112233" ayni
/// numara ama bayt olarak farkli — hash'leri tutmaz ve eslesme bos doner.
/// Ekranda hata yok, yalnizca "rehberinde kimse yok" yalani var. Sunucu
/// hash'i Firebase'in E.164'unden hesapliyor; buradaki cikti o bicime
/// birebir oturmak zorunda.

void main() {
  group('normalizeE164', () {
    test('yerel TR bicimi ulke koduna oturur', () {
      expect(normalizeE164('0555 111 22 33', countryCode: '+90'),
          '+905551112233');
      expect(normalizeE164('0555-111-22-33', countryCode: '+90'),
          '+905551112233');
      expect(normalizeE164('(0555) 111 22 33', countryCode: '+90'),
          '+905551112233');
    });

    test('zaten E.164 olan aynen kalir', () {
      expect(normalizeE164('+905551112233', countryCode: '+90'),
          '+905551112233');
      expect(normalizeE164('+1 555 123 4567', countryCode: '+90'),
          '+15551234567');
    });

    test('00 oneki + isaretine cevrilir', () {
      expect(normalizeE164('00905551112233', countryCode: '+90'),
          '+905551112233');
    });

    test('bas sifirsiz duz numara ulke kodu alir', () {
      expect(normalizeE164('5551112233', countryCode: '+90'),
          '+905551112233');
    });

    test('dahili numaralar ve kisa kodlar ATILIR', () {
      // 7 haneden kisa girdiler (dahili no, banka kisa kodu) hash'lenirse
      // bosuna sunucuya tasinir ve tavani doldurur.
      expect(normalizeE164('1234', countryCode: '+90'), isNull);
      expect(normalizeE164('112', countryCode: '+90'), isNull);
    });

    test('harf iceren girdiler atilir', () {
      expect(normalizeE164('CALL-NOW', countryCode: '+90'), isNull);
      expect(normalizeE164('0555ABC', countryCode: '+90'), isNull);
    });

    test('asiri uzun girdiler atilir', () {
      expect(normalizeE164('+123456789012345678', countryCode: '+90'),
          isNull);
    });

    test('bos ve bosluk girdiler atilir', () {
      expect(normalizeE164('', countryCode: '+90'), isNull);
      expect(normalizeE164('   ', countryCode: '+90'), isNull);
    });
  });

  group('countryCodeOf', () {
    test('TR numarasi +90 verir', () {
      expect(countryCodeOf('+905551112233'), '+90');
    });

    test('NANP numarasi +1 verir', () {
      expect(countryCodeOf('+15551234567'), '+1');
    });

    test('Rusya +7 verir', () {
      expect(countryCodeOf('+79261234567'), '+7');
    });

    test('Almanya +49 verir', () {
      expect(countryCodeOf('+491701234567'), '+49');
    });
  });

  group('uctan uca tutarlilik', () {
    test('yerel bicim ile E.164 ayni hash uretir', () {
      // Testin asil amaci: iki bicim ayni E.164'e indirgenmeli — hash
      // fonksiyonu ayni girdiye ayni ciktiyi zaten verir.
      final a = normalizeE164('0555 111 22 33', countryCode: '+90');
      final b = normalizeE164('+90 555 111 2233', countryCode: '+90');
      expect(a, b);
    });
  });
}
