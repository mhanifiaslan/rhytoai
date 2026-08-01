import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/core/auth_service.dart';

/// Kayıt şifresi kuralı ve Apple ile Giriş görünürlüğü.
///
/// Şifre kuralı bilinçli olarak **uzunluk + çeşitlilik**. Karmaşık bir kalıp
/// dayatmak (büyük harf + rakam + sembol zorunlu) kullanıcıyı şifresini bir
/// yere yazmaya iter; uzunluk daha çok koruma sağlar.
void main() {
  group('validatePassword — kabul edilenler', () {
    test('harf ve rakam karışımı geçer', () {
      expect(validatePassword('gokyuzu42'), isNull);
    });

    test('harf ve sembol karışımı geçer', () {
      expect(validatePassword('gokyuzu!!'), isNull);
    });

    test('uzun parola cümlesi geçer', () {
      expect(validatePassword('ay evresi 7 gun'), isNull);
    });

    test('Türkçe karakterli şifre geçer', () {
      expect(validatePassword('şifrem2026'), isNull);
    });
  });

  group('validatePassword — reddedilenler', () {
    test('Firebase alt sınırı (6 karakter) artık yetmez', () {
      // Eski kural buydu ve "123456"yı geçerli yapıyordu.
      expect(validatePassword('abc123'), PasswordIssue.tooShort);
      expect(validatePassword('123456'), PasswordIssue.tooShort);
    });

    test('8 karakterin altı reddedilir', () {
      expect(validatePassword('abc123!'), PasswordIssue.tooShort);
    });

    test('yalnızca harf reddedilir', () {
      expect(validatePassword('gokyuzudur'), PasswordIssue.tooSimple);
    });

    test('yalnızca rakam reddedilir', () {
      expect(validatePassword('12345678'), PasswordIssue.tooSimple);
    });

    test('boş şifre reddedilir', () {
      expect(validatePassword(''), PasswordIssue.tooShort);
    });
  });

  group('appleSignInAvailable', () {
    tearDown(() => debugDefaultTargetPlatformOverride = null);

    test('iOS için AÇIK — Guideline 4.8 zorunlu kılıyor', () {
      // Google girişi sunuluyorsa iOS'ta Apple ile Giriş de sunulmak
      // ZORUNDA; eksikliği tek başına red sebebi.
      debugDefaultTargetPlatformOverride = TargetPlatform.iOS;
      expect(appleSignInAvailable, isTrue);
    });

    test('Android için kapalı', () {
      // Android'de gerekli değil ve göstermek kafa karıştırır.
      debugDefaultTargetPlatformOverride = TargetPlatform.android;
      expect(appleSignInAvailable, isFalse);
    });
  });
}
