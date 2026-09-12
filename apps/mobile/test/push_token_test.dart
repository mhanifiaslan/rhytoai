// JT-turu: çıkışta cihaz jetonu bu hesaptan sökülür — iki adım, ikisi de
// best-effort, hiçbiri çıkışı engellemez.
//
// Cihazda ölçülen kusur: aynı telefonda hesap değiştirilince eski hesabın
// profilindeki `fcmToken` duruyordu; telefona iki hesabın push'u geliyordu
// (sahip: Türkçe, test hesabı: İngilizce → "hem İngilizce hem Türkçe").
import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/core/notifications.dart' show forgetPushToken;

void main() {
  test('profil temizlenir (uid ile) ve FCM jetonu geçersizlenir — bu sırayla',
      () async {
    final sira = <String>[];
    await forgetPushToken(
      'u1',
      clearProfile: (uid) async => sira.add('profil:$uid'),
      deleteDeviceToken: () async => sira.add('deleteToken'),
    );
    expect(sira, ['profil:u1', 'deleteToken']);
  });

  test('profil yazımı düşse de jeton geçersizlenir; jeton düşse de fırlatmaz',
      () async {
    var silindi = 0;
    await forgetPushToken(
      'u1',
      clearProfile: (_) async => throw StateError('kural reddi'),
      deleteDeviceToken: () async => silindi++,
    );
    expect(silindi, 1);

    await expectLater(
      forgetPushToken(
        'u1',
        clearProfile: (_) async {},
        deleteDeviceToken: () async => throw StateError('FCM yok'),
      ),
      completes,
    );
  });

  test('askıda kalan adım zaman aşımıyla geçilir; çıkış beklemez', () async {
    var silindi = 0;
    await forgetPushToken(
      'u1',
      clearProfile: (_) => Completer<void>().future, // hiç dönmez
      deleteDeviceToken: () async => silindi++,
      timeout: const Duration(milliseconds: 30),
    );
    expect(silindi, 1, reason: 'ilk adım askıda kalsa da ikinci adım koşar');
  });
}
