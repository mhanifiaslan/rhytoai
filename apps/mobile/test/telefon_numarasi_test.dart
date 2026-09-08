/// E.164 derleyici bekçileri.
///
/// Bu testlerin sebebi CANLI bir olay (2026-09-08): bir kullanıcı SMS
/// alamadı, Google tarafında her şey sağlıklıydı — istek 200 döndü, SMS
/// TR'ye faturalandı, engellenmedi. Şüphelilerden biri derleyiciydi:
/// baştaki sıfır TEK SEFER kırpıldığı için "00532..." girişi
/// "+9005321234567" üretiyordu. Bu numara E.164 sınırları içinde kaldığı
/// için Firebase onu kabul edip faturalıyor, SMS var olmayan bir numaraya
/// gidiyor ve kullanıcının gördüğü tek şey "kod gelmiyor" oluyor.
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/widgets/phone_number_field.dart';

const _tr = Country('TR', '90', 'Turkey', 'Türkiye');
const _de = Country('DE', '49', 'Germany', 'Almanya');

void main() {
  group('composeE164 — her yazım tek doğru numaraya iner', () {
    test('sade ulusal numara', () {
      expect(composeE164(_tr, '5321234567'), '+905321234567');
    });

    test('baştaki sıfır', () {
      expect(composeE164(_tr, '05321234567'), '+905321234567');
    });

    test('uluslararası önek 00 + ülke kodu', () {
      expect(composeE164(_tr, '00905321234567'), '+905321234567');
    });

    test('ÇİFT sıfır (canlı hatanın kendisi)', () {
      // Eskiden "+9005321234567" üretiyordu: geçerli görünümlü, var
      // olmayan numara. Firebase kabul eder, SMS boşluğa gider.
      expect(composeE164(_tr, '005321234567'), '+905321234567');
    });

    test('ülke kodu elle yazılmış', () {
      expect(composeE164(_tr, '905321234567'), '+905321234567');
      expect(composeE164(_tr, '+90 532 123 45 67'), '+905321234567');
    });

    test('boşluk, tire, parantez', () {
      expect(composeE164(_tr, '(0532) 123-45 67'), '+905321234567');
    });

    test('başka ülke', () {
      expect(composeE164(_de, '01701234567'), '+491701234567');
    });
  });

  group('isPlausibleNational — yanlış numaraya gönderim kapısı', () {
    test('doğru TR numarası geçer', () {
      expect(isPlausibleNational(_tr, '5321234567'), isTrue);
    });

    test('eksik haneli TR numarası REDDEDİLİR', () {
      // Eski kapı ("+" ile başlasın ve >= 10 karakter olsun) bunu
      // geçiriyordu: "+905321234" 10 karakter.
      expect(isPlausibleNational(_tr, '5321234'), isFalse);
    });

    test('fazla haneli TR numarası REDDEDİLİR', () {
      expect(isPlausibleNational(_tr, '05321234567'.replaceAll('x', '')),
          isFalse);
      expect(isPlausibleNational(_tr, '53212345678'), isFalse);
    });

    test('sıfırla başlayan TR numarası REDDEDİLİR', () {
      // Buraya sıfırlı geliyorsa derleyici kırpmamış demektir.
      expect(isPlausibleNational(_tr, '0532123456'), isFalse);
    });

    test('boş giriş reddedilir', () {
      expect(isPlausibleNational(_tr, ''), isFalse);
    });

    test('listede olmayan ülke genel E.164 kuralına düşer', () {
      const bilinmeyen = Country('ZZ', '999', 'Nowhere', 'Hiçbiryer');
      expect(isPlausibleNational(bilinmeyen, '12345678'), isTrue);
      expect(isPlausibleNational(bilinmeyen, '123'), isFalse);
      // ülke kodu + ulusal <= 15 hane
      expect(isPlausibleNational(bilinmeyen, '1234567890123'), isFalse);
    });
  });

  group('PhoneEntry.masked — teşhis kaydına giden biçim', () {
    test('tam numara ASLA görünmez', () {
      const giris = PhoneEntry(
          e164: '+905321234567', country: _tr, national: '5321234567');
      expect(giris.masked, '+90532***4567');
      expect(giris.masked.contains('123'), isFalse);
    });

    test('eksik numarada maske üretilmez', () {
      const giris = PhoneEntry(e164: '', country: _tr, national: '532');
      expect(giris.masked, '');
    });

    test('boş girişte plausible false', () {
      expect(const PhoneEntry.bos().plausible, isFalse);
    });
  });
}
