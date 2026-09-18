// ilkacilis-2 bekçileri: "abone değil" ile "bilmiyorum" aynı şey değil.
//
// Sunucu yeni hesabı gerçekten AÇIK sayıyor (3 günlük deneme, sunucu tarafı).
// İstemcide `/billing/status` tek kez düşerse eski kod `SubscriptionStatus`u
// `none` döndürüyor, tanıtım paywall'ı denemedeki testçinin yüzüne açılıyor ve
// hesap ömründeki TEK gösterim boşa yanıyordu (dönüşüm ölçümü de bozuluyor).
//
// Okuma sağlayıcıdan AYRI bir fonksiyona çıkarıldı: sağlayıcıyı koşturmak
// sahte bir Firebase `User`ı gerektirirdi.
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/core/subscription.dart';

/// Sabit yanıt veren sahte sunucu (app_gate_test ile aynı desen).
class _SahteAdapter implements HttpClientAdapter {
  _SahteAdapter({this.durum = 200, this.govde = '{}', this.kopar = false});

  final int durum;
  final String govde;
  final bool kopar;

  @override
  Future<ResponseBody> fetch(RequestOptions options,
      Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    if (kopar) {
      throw DioException(
          requestOptions: options, type: DioExceptionType.connectionTimeout);
    }
    return ResponseBody.fromString(govde, durum, headers: {
      Headers.contentTypeHeader: [Headers.jsonContentType],
    });
  }

  @override
  void close({bool force = false}) {}
}

Dio _dio(_SahteAdapter adapter) =>
    Dio(BaseOptions(baseUrl: 'https://test.invalid'))
      ..httpClientAdapter = adapter;

void main() {
  group('abonelikDurumunuOku', () {
    test('sunucu cevap verdiyse durum OKUNABİLDİ', () async {
      final durum = await abonelikDurumunuOku(_dio(_SahteAdapter(
          govde: '{"active":true,"is_trial":true,"trial_days_left":2}')));

      expect(durum.active, isTrue);
      expect(durum.okunabildi, isTrue);
      expect(durum.trialDaysLeft, 2);
    });

    test('200 + abone DEĞİL de BİLİNEN bir cevaptır', () async {
      // Ayrımın asıl yeri burası: gerçek "abone değil" ile ağ hatası.
      final durum = await abonelikDurumunuOku(
          _dio(_SahteAdapter(govde: '{"active":false}')));

      expect(durum.active, isFalse);
      expect(durum.okunabildi, isTrue);
    });

    test('5xx: "abone değil" DEĞİL, "bilinmiyor"', () async {
      final durum = await abonelikDurumunuOku(
          _dio(_SahteAdapter(durum: 500, govde: '{}')));

      expect(durum.active, isFalse, reason: 'kilitler kapalı tarafta kalır');
      expect(durum.okunabildi, isFalse);
    });

    test('zaman aşımı da bilinmiyor sayılır', () async {
      final durum = await abonelikDurumunuOku(_dio(_SahteAdapter(kopar: true)));

      expect(durum.okunabildi, isFalse);
    });

    test('bozuk gövde de sağlayıcıyı HATAYA DÜŞÜRMEZ', () async {
      // Geniş `catch` bilerek var: hatalı sağlayıcıda `.future` tamamlanmıyor
      // ve satın alma sonrası yoklama orada asılı kalıyordu.
      final durum = await abonelikDurumunuOku(
          _dio(_SahteAdapter(govde: 'bu json degil')));

      expect(durum.okunabildi, isFalse);
    });
  });

  test('oturumsuzluk BİLİNEN durumdur, ağ hatası değil', () {
    expect(SubscriptionStatus.none.okunabildi, isTrue);
    expect(SubscriptionStatus.bilinmiyor.okunabildi, isFalse);
    // Kilitler iki durumda da kapalı tarafta kalır.
    expect(SubscriptionStatus.none.active, isFalse);
    expect(SubscriptionStatus.bilinmiyor.active, isFalse);
  });

  test('mevcut çağrıların hiçbiri değişmiyor: varsayılan okunabildi', () {
    expect(
        SubscriptionStatus.fromJson({'active': true}).okunabildi, isTrue);
  });

  group('paywallKarariVerilebilir', () {
    test('yükleniyorken karar verilmez (KT3)', () {
      expect(paywallKarariVerilebilir(const AsyncLoading<SubscriptionStatus>()),
          isFalse);
    });

    test('durum bilinmiyorken karar verilmez (ilkacilis-2)', () {
      expect(
          paywallKarariVerilebilir(const AsyncData<SubscriptionStatus>(
              SubscriptionStatus.bilinmiyor)),
          isFalse,
          reason: 'tek 5xx, denemedeki testçinin yüzüne paywall açıp hesap '
              'ömründeki TEK gösterimi harcıyordu');
    });

    test('gerçek cevap geldiyse karar VERİLİR', () {
      // Düzeltmenin paywall'ı tamamen öldürmediğini kanıtlayan tek iddia.
      expect(
          paywallKarariVerilebilir(
              const AsyncData<SubscriptionStatus>(SubscriptionStatus.none)),
          isTrue);
    });
  });

  group('Kaynak bekçisi', () {
    // Tanıtım paywall'ının kapısı ekranın içinde; kararı sahte Firebase
    // oturumu olmadan pump ederek gözlemek mümkün değil, o yüzden kapının
    // KULLANILDIĞI kaynaktan sabitlenir (device_session_test ile aynı desen).
    final sky = File('lib/features/sky/sky_screen.dart').readAsStringSync();

    test('tanıtım paywall\'ı kararı KAPIDAN geçiyor', () {
      expect(sky, contains('if (!paywallKarariVerilebilir(durum))'));
      expect(sky, isNot(contains('if (durum.isLoading) {')),
          reason: 'eski kapı yalnız yüklemeyi biliyordu; okunamadı vakası '
              'paywall\'ı açıp tek gösterimi harcıyordu');
    });
  });
}
