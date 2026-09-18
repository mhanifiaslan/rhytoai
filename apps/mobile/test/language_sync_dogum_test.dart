// Doğum damgası bekçileri (olcum-4).
//
// Ölçülen kusur: `users/{uid}` dokümanı oturum açılışında doğuyor ama
// `createdAt` onboarding'in SON adımında yazılıyordu. Firestore `order_by`
// alanı bulunmayan dokümanı sonuç kümesinden düşürdüğü için (panel varsayılan
// sıralaması `createdAt DESC`) onboarding'i yarım bırakan testçi kullanıcı
// listesinde HİÇ görünmüyordu — kapalı testin ölçmek istediği tek şey buydu.
//
// İkinci kusur PARA kusuru: damga sunucu damgasıyla konsaydı, alanı hiç
// olmayan (aylar önce yarım bırakmış) hesap BUGÜN kaydolmuş görünür ve
// backend `core/entitlements._trial_remaining` ona sıfırdan 3 günlük Rytho+
// denemesi açardı. Damga bu yüzden Auth'un gerçek oluşma anından alınır.
//
// Kararlar saf işlevlerde tutuluyor: `_firestoreWrite` Firebase ister, bu
// yüzden damga dışarıdan geçilir ve bekçi eklentisiz koşar.
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/core/language_sync.dart';

/// Yorumsuz kaynak: aşağıdaki iddialar bir şeyin YOKLUĞUNU arıyor ve kusuru
/// ANLATAN yorum satırları ham aramada yanlış pozitif üretir.
String _kod(String yol) => File(yol)
    .readAsLinesSync()
    .where((s) => !s.trimLeft().startsWith('//'))
    .join('\n');

void main() {
  group('kayitDamgasi', () {
    test('Auth oluşma anı VARSA sunucu damgası kullanılmaz — yoksa aylar '
        'önce açılmış hesap bugün kaydolmuş görünür ve 3 günlük deneme '
        'sıfırdan başlar', () {
      final dogum = DateTime.utc(2026, 3, 4, 5, 6);
      expect(kayitDamgasi(dogum, 'SUNUCU-DAMGASI'), same(dogum));
    });

    test('Auth damgası yoksa sunucu damgasına düşülür: alanı hiç yazmamak '
        'panelde görünmezliği sürdürürdü', () {
      expect(kayitDamgasi(null, 'SUNUCU-DAMGASI'), 'SUNUCU-DAMGASI');
    });
  });

  group('dogumAlanlari', () {
    test('doküman yoksa (ilk oturum) yalnız damga konur', () {
      expect(dogumAlanlari(null, 'DAMGA'), {'createdAt': 'DAMGA'});
    });

    test('createdAt yoksa damga + elde olan kimlik alanları konur', () {
      final alanlar = dogumAlanlari(
          <String, Object?>{'language': 'tr'}, 'DAMGA',
          email: 'testci@ornek.com', displayName: 'Ayşe');
      expect(alanlar, {
        'createdAt': 'DAMGA',
        'email': 'testci@ornek.com',
        'displayName': 'Ayşe',
      });
    });

    test('createdAt VARSA hiçbir alan yazılmaz — kayıt tarihi değişmez bir '
        'olgu ve 3 günlük deneme penceresi ona bağlı', () {
      expect(
          dogumAlanlari(<String, Object?>{'createdAt': 'ESKI'}, 'DAMGA',
              email: 'a@b.c', displayName: 'Can'),
          isEmpty);
    });

    test('boş kimlik alanı yazılmaz: sonradan gelen gerçek ad null ile '
        'ezilmemeli', () {
      final alanlar = dogumAlanlari(<String, Object?>{}, 'DAMGA',
          email: null, displayName: null);
      expect(alanlar.containsKey('email'), isFalse);
      expect(alanlar.containsKey('displayName'), isFalse);
    });
  });

  group('kaynak bekçisi', () {
    test('damga Auth oluşma anından alınır (sunucu damgası yalnız yedek)', () {
      final kaynak = _kod('lib/core/language_sync.dart');
      expect(kaynak, contains('kayitDamgasi('));
      expect(kaynak, contains('metadata.creationTime'),
          reason: 'damga Auth oluşma anından alınmıyor: alanı hiç olmayan '
              'hesap BUGÜN kaydolmuş damgalanır ve bedava 3 günlük Plus '
              'denemesi açılır');
    });

    test('onboarding son adımı artık kayıt damgası yazmıyor', () {
      expect(_kod('lib/features/onboarding/onboarding_wizard.dart'),
          isNot(contains("'createdAt'")),
          reason: 'damga onboarding\'in SON adımında konarsa akışı yarım '
              'bırakan kullanıcı panelin createdAt sıralı listesinden düşer');
    });
  });
}
