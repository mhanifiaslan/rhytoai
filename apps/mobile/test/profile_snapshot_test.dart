import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/core/providers.dart';

/// Profil anlik goruntusune ne zaman guvenilecegi.
///
/// Cihaz testinde su gorundu: giris yapinca dogum bilgisi formu aciliyor,
/// sonra KENDILIGINDEN geciyordu. Kullanicinin profili tamdi — Firestore'da
/// `onboardingCompleted = true` ve dogum verisi doluydu.
///
/// Sebep: Firestore dinleyici kurulunca once YEREL ONBELLEKTEN yayin yapiyor.
/// Onbellek bossa (taze kurulum, yeni giris) o yayin "dokuman yok" diyor.
/// Uygulama bunu "onboarding tamamlanmamis" diye okuyup formu aciyordu;
/// sunucu yaniti gelince duzeliyordu.
///
/// Kusur zararsiz gorunuyor ama degil: kullanici formu doldurmaya baslarsa
/// dogum verisinin uzerine yaziyor.

void main() {
  group('profil anlik goruntusu guvenilir mi', () {
    test('sunucudan gelen "dokuman var" guvenilir', () {
      expect(
        profileSnapshotIsAuthoritative(exists: true, isFromCache: false),
        isTrue,
      );
    });

    test('sunucudan gelen "dokuman yok" GUVENILIR — gercekten yeni kullanici',
        () {
      // Bu dallanma sart: yoksa yeni kullanici onboarding'i hic goremez.
      expect(
        profileSnapshotIsAuthoritative(exists: false, isFromCache: false),
        isTrue,
      );
    });

    test('onbellekten gelen "dokuman var" guvenilir — cevrimdisi calismali',
        () {
      // Daha once profili yuklemis bir kullanici ucaksa da uygulamayi acabilmeli.
      expect(
        profileSnapshotIsAuthoritative(exists: true, isFromCache: true),
        isTrue,
      );
    });

    test('onbellekten gelen "dokuman yok" GUVENILMEZ — kusurun kendisi', () {
      expect(
        profileSnapshotIsAuthoritative(exists: false, isFromCache: true),
        isFalse,
        reason: 'bos onbellek "profil yok" demek degildir; kullaniciyi '
            'verisi dururken onboarding formuna dusuruyordu',
      );
    });
  });
}
