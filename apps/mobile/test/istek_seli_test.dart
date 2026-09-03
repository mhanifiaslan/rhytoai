import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/core/providers.dart' show ayniProfil;
import 'package:rytho/features/face/face_geometry.dart';
import 'package:rytho/features/face/face_scan_overlay.dart';
import 'package:rytho/main.dart' show rythoRetry;

/// KL-turu: "az kullanmama rağmen yoğun talep" (429) bulgusunun istemci
/// yarısını sabitleyen bekçiler.
void main() {
  DioException _hata(int kod) => DioException(
        requestOptions: RequestOptions(path: '/x'),
        response: Response(
            requestOptions: RequestOptions(path: '/x'), statusCode: kod),
      );

  group('rythoRetry', () {
    test('429 ASLA yeniden denenmez', () {
      // Riverpod varsayılanı 10 kez denerdi: tek kota hatası ~11 isteğe,
      // yedi sağlayıcıda ~77 isteğe çıkıyor ve pencere hiç boşalmıyordu.
      expect(rythoRetry(0, _hata(429)), isNull);
      expect(rythoRetry(3, _hata(429)), isNull);
    });

    test('diğer 4xx de denenmez (402 paywall, 403 yetki, 404 yok)', () {
      for (final kod in [400, 402, 403, 404, 409]) {
        expect(rythoRetry(0, _hata(kod)), isNull, reason: '$kod');
      }
    });

    test('5xx ve ağ hatası sınırlı sayıda denenir', () {
      expect(rythoRetry(0, _hata(500)), isNotNull);
      expect(rythoRetry(1, _hata(503)), isNotNull);
      // Üçüncüde durur: sonsuz döngü yok.
      expect(rythoRetry(2, _hata(500)), isNull);
      expect(
          rythoRetry(
              0,
              DioException(
                  requestOptions: RequestOptions(path: '/x'),
                  type: DioExceptionType.connectionError)),
          isNotNull);
    });
  });

  group('ayniProfil', () {
    test('içerikçe aynı iki FARKLI Map eşit sayılır', () {
      // Firestore her anlık görüntüde yeni bir Map üretiyor; kimlik
      // karşılaştırması profili izleyen 12 sağlayıcıyı boşuna koşturuyordu.
      final a = {
        'displayName': 'Gezgin',
        'notifications': {'daily': true, 'streak': false},
        'tags': ['a', 'b'],
      };
      final b = {
        'displayName': 'Gezgin',
        'notifications': {'daily': true, 'streak': false},
        'tags': ['a', 'b'],
      };
      expect(identical(a, b), isFalse);
      expect(ayniProfil(a, b), isTrue);
    });

    test('iç içe alan değişince eşit DEĞİL', () {
      expect(
          ayniProfil({
            'notifications': {'daily': true}
          }, {
            'notifications': {'daily': false}
          }),
          isFalse);
      expect(ayniProfil({'a': 1}, {'a': 1, 'b': 2}), isFalse);
      expect(ayniProfil(null, {'a': 1}), isFalse);
      expect(ayniProfil(null, null), isTrue);
    });
  });

  group('FaceGuidePainter dörtgen çerçeve (KL-B)', () {
    test('çizilen çerçeve kalite kontrolüyle AYNI dikdörtgen', () {
      // Değişmez: çizim ile ölçüm ayrı hesap kullanamaz. Şekil oval'den
      // yuvarlatılmış dörtgene döndü, hedef Rect DEĞİŞMEDİ.
      const boyut = Size(400, 800);
      expect(FaceGuidePainter.guideFrame(boyut), guideOvalOnScreen(boyut));
    });

    testWidgets('çizim her aşamada fırlatmadan tamamlanır', (tester) async {
      for (final (kalite, nabiz, kilit) in [
        (FrameQuality.noFace, 0.0, 0.0),
        (FrameQuality.tooFar, 0.94, 0.0),
        (FrameQuality.ready, 0.5, 0.6),
        (FrameQuality.ready, 0.0, 1.0),
      ]) {
        await tester.pumpWidget(MaterialApp(
          home: CustomPaint(
            size: const Size(400, 800),
            painter: FaceGuidePainter(
                quality: kalite, pulse: nabiz, lockProgress: kilit),
          ),
        ));
        expect(tester.takeException(), isNull);
      }
    });
  });
}
