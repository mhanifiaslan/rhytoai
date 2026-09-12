// Tek cihaz kilidi — istemci yarısı bekçileri (TC-turu).
//
// Cihaz bulgusu: "ikinci cihazda giriş yapınca uygulama kullanılamıyor,
// eski cihazdan çıkış da açmıyor" (B4). İstemci tarafındaki sebepler ve
// burada sabitlenen sözleşmeler:
// 1. 409 oturumu KAPATMAZ: bayrak kapıya yazılır, oturum açık kalır ki "Bu
//    cihazda kullan" kimlikli gidebilsin (eski kod anında signOut yapıyor,
//    devralma 401'e çarpıyordu).
// 2. İlk 409 kazanır: uçuştaki diğer istekler kapıyı yeniden yazmaz.
// 3. Devralma `POST /device/claim {platform}` ve sunucunun DÜRÜST `claimed`
//    değeri; bırakma `DELETE /device/claim`, ≤3 sn, hata yutulur.
// 4. Çıkış sırası: bırak (kimlik hâlâ varken) → oturum kapat → bayrağı düşür.
// 5. Açılıştaki devralma sorusu (`maybeConfirmDeviceTakeover`, `_soruldu`)
//    koddan silindi — yarışın kaynağıydı.
import 'dart:async';
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/core/api.dart'
    show apiProvider, kDeviceConflictStatus, rythoNavigatorKey;
import 'package:rytho/core/auth_service.dart' show signOutEverywhere;
import 'package:rytho/core/device_session.dart';

/// Her isteği kaydeden, sabit yanıt veren sahte sunucu.
class _SahteAdapter implements HttpClientAdapter {
  _SahteAdapter({
    this.durum = 200,
    this.govde = '{"status":"ok"}',
    this.basliklar = const {},
    this.askidaBirak = false,
    this.onIstek,
  });

  final int durum;
  final String govde;
  final Map<String, String> basliklar;

  /// true → yanıt HİÇ gelmez (zaman aşımı senaryosu).
  final bool askidaBirak;
  final void Function(RequestOptions)? onIstek;
  final List<RequestOptions> istekler = [];

  @override
  Future<ResponseBody> fetch(RequestOptions options,
      Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    istekler.add(options);
    onIstek?.call(options);
    if (askidaBirak) return Completer<ResponseBody>().future;
    return ResponseBody.fromString(
      govde,
      durum,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
        for (final e in basliklar.entries) e.key: [e.value],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}

Dio _dio(_SahteAdapter adapter, [List<Interceptor> interceptors = const []]) {
  final dio = Dio(BaseOptions(baseUrl: 'https://test.invalid'));
  dio.httpClientAdapter = adapter;
  dio.interceptors.addAll(interceptors);
  return dio;
}

/// Sunucunun 409 gövdesi (backend/core/device.py ile aynı şekil). Diğer
/// cihaz bilgisi gövdede DEĞİL, başlıklarda.
const _kGovde409 =
    '{"status":"error","code":"device_conflict","detail":"Hesabın başka bir cihazda açıldı."}';
const _kIso = '2026-09-12T10:00:00+00:00';
final _kAn = DateTime.utc(2026, 9, 12, 10);

_SahteAdapter _cakisma({String platform = 'android', String zaman = _kIso}) =>
    _SahteAdapter(durum: 409, govde: _kGovde409, basliklar: {
      kDeviceConflictHeader: '1',
      kDeviceOtherPlatformHeader: platform,
      kDeviceClaimedAtHeader: zaman,
    });

final _throws409 = throwsA(isA<DioException>()
    .having((e) => e.response?.statusCode, 'statusCode', kDeviceConflictStatus));

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('deviceConflictInterceptor', () {
    test('409 + X-Device-Conflict → kanca; platform ve claimedAt BAŞLIKLARDAN; '
        'hata çağırana devam eder', () async {
      final gelen = <DeviceConflict>[];
      final dio = _dio(_cakisma(), [deviceConflictInterceptor(gelen.add)]);

      await expectLater(dio.post('/api/v1/reports/daily'), _throws409,
          reason: 'çağıran sağlayıcı da düşmeli — kapı açılınca yarım veri '
              'kalmasın');
      expect(gelen, hasLength(1));
      expect(gelen.single.platform, 'android');
      expect(gelen.single.claimedAt, _kAn);
    });

    test('başlıklar boş/bozuksa null — ekran "—" basar, kapı yine kapanır',
        () async {
      final gelen = <DeviceConflict>[];
      final dio = _dio(_cakisma(platform: '', zaman: 'dün'),
          [deviceConflictInterceptor(gelen.add)]);
      await expectLater(dio.get('/x'), _throws409);
      expect(gelen.single.platform, isNull);
      expect(gelen.single.claimedAt, isNull);
    });

    test('saat dilimi eki olmayan tarih UTC sayılır (yerel sanmak saati kaydırır)',
        () async {
      final gelen = <DeviceConflict>[];
      final dio = _dio(_cakisma(zaman: '2026-09-12T10:00:00'),
          [deviceConflictInterceptor(gelen.add)]);
      await expectLater(dio.get('/x'), _throws409);
      expect(gelen.single.claimedAt, _kAn);
      expect(gelen.single.claimedAt!.isUtc, isTrue);
    });

    test('409 ama X-Device-Conflict yok → kanca YOK (o 409 bizim değil)',
        () async {
      var cagri = 0;
      final dio = _dio(_SahteAdapter(durum: 409, govde: '{"detail":"çakıştı"}'),
          [deviceConflictInterceptor((_) => cagri++)]);
      await expectLater(dio.get('/x'), _throws409);
      expect(cagri, 0);
    });

    test('409 dışı (500) dokunmaz', () async {
      var cagri = 0;
      final dio = _dio(_SahteAdapter(durum: 500, govde: '{"detail":"patladı"}'),
          [deviceConflictInterceptor((_) => cagri++)]);
      await expectLater(dio.get('/x'), throwsA(isA<DioException>()));
      expect(cagri, 0);
    });

    test('kanca fırlatsa da hata çağırana ulaşır (426 deseni)', () async {
      final dio = _dio(_cakisma(),
          [deviceConflictInterceptor((_) => throw StateError('kap yok'))]);
      await expectLater(dio.get('/x'), _throws409);
    });
  });

  group('noteDeviceConflict — kapı', () {
    /// apiProvider'daki kancayla BİREBİR aynı bağlama (bkz. core/api.dart).
    Interceptor kanca(ProviderContainer kap) => deviceConflictInterceptor(
        (c) => noteDeviceConflict(kap.read(deviceConflictProvider.notifier), c));

    test('ilk 409 kazanır: uçuştaki ikinci 409 yok sayılır', () async {
      final kap = ProviderContainer();
      addTearDown(kap.dispose);
      expect(kap.read(deviceConflictProvider), isNull);

      await expectLater(_dio(_cakisma(), [kanca(kap)]).get('/x'), _throws409);
      expect(kap.read(deviceConflictProvider),
          DeviceConflict(platform: 'android', claimedAt: _kAn));

      // Soğuk açılışta paralel ateşlenen ikinci sağlayıcı da 409 aldı —
      // başka bilgiyle. İlk `claimedAt` ezilmez, ekran yeniden kurulmaz.
      await expectLater(
          _dio(_cakisma(platform: 'iOS', zaman: '2026-09-12T11:00:00Z'),
              [kanca(kap)]).get('/y'),
          _throws409);
      expect(kap.read(deviceConflictProvider)!.platform, 'android');
      expect(kap.read(deviceConflictProvider)!.claimedAt, _kAn);
    });

    test('kapı açıldıktan sonra yeni 409 yeniden kapatır', () async {
      // Devralma başarılı → kapı açık; sonra üçüncü cihaz devralırsa
      // ekran yine gelmeli.
      final kap = ProviderContainer();
      addTearDown(kap.dispose);
      await expectLater(_dio(_cakisma(), [kanca(kap)]).get('/x'), _throws409);
      kap.read(deviceConflictProvider.notifier).state = null;

      await expectLater(
          _dio(_cakisma(platform: 'iOS'), [kanca(kap)]).get('/y'), _throws409);
      expect(kap.read(deviceConflictProvider)?.platform, 'iOS');
    });
  });

  group('claimThisDevice', () {
    test('POST /api/v1/device/claim {platform}; claimed:true → true', () async {
      final adapter = _SahteAdapter(govde: '{"claimed":true}');
      expect(await claimThisDevice(_dio(adapter)), isTrue);

      final istek = adapter.istekler.single;
      expect(istek.method, 'POST');
      expect(istek.path, '/api/v1/device/claim');
      expect((istek.data as Map)['platform'], defaultTargetPlatform.name,
          reason: 'diğer cihazın ekranında "{platform} cihazında" görünür');
    });

    test('claimed:false → false (sunucu dürüst; ekran SnackBar gösterir)',
        () async {
      expect(await claimThisDevice(_dio(_SahteAdapter(govde: '{"claimed":false}'))),
          isFalse);
    });

    test('gövde beklenmedikse false — "devralındı" yalanı yok', () async {
      expect(await claimThisDevice(_dio(_SahteAdapter(govde: '{"ok":true}'))),
          isFalse);
    });

    test('HTTP hatası fırlatır — yutulmaz, ekran başarısızlığı söyler',
        () async {
      await expectLater(
          claimThisDevice(_dio(_SahteAdapter(durum: 500, govde: '{}'))),
          throwsA(isA<DioException>()));
    });
  });

  group('releaseThisDevice', () {
    test('DELETE /api/v1/device/claim', () async {
      final adapter = _SahteAdapter(govde: '{"released":true}');
      await releaseThisDevice(_dio(adapter));
      final istek = adapter.istekler.single;
      expect(istek.method, 'DELETE');
      expect(istek.path, '/api/v1/device/claim');
    });

    test('sunucu hatası yutulur — çıkış sürer', () async {
      final adapter = _SahteAdapter(durum: 500, govde: '{"detail":"patladı"}');
      await releaseThisDevice(_dio(adapter));
      expect(adapter.istekler, hasLength(1));
    });

    test('yanıt gelmezse tavandan sonra bırakılır; üretim tavanı 3 sn',
        () async {
      // Çıkış düğmesine basan kullanıcı ağ yüzünden asılı kalmamalı.
      final saat = Stopwatch()..start();
      await releaseThisDevice(_dio(_SahteAdapter(askidaBirak: true)),
          timeout: const Duration(milliseconds: 50));
      expect(saat.elapsed, lessThan(const Duration(seconds: 2)));
      expect(kDeviceReleaseTimeout, const Duration(seconds: 3));
    });
  });

  group('signOutEverywhere sırası', () {
    // Navigatörsüz senaryo ÖNCE: sonraki testler kök navigatör anahtarını
    // ağaca takıyor.
    test('navigatör yokken (Firebase\'siz yol) çıkış yine sürer', () async {
      var cikis = 0;
      await signOutEverywhere(signOut: () async => cikis++);
      expect(cikis, 1);
    });

    /// Gerçek ağaç gibi: kap + kök navigatör anahtarı; Dio kapta.
    Future<ProviderContainer> agac(
        WidgetTester tester, _SahteAdapter adapter) async {
      final kap = ProviderContainer(
          overrides: [apiProvider.overrideWithValue(_dio(adapter))]);
      addTearDown(kap.dispose);
      kap.read(deviceConflictProvider.notifier).state =
          DeviceConflict(platform: 'android', claimedAt: _kAn);
      await tester.pumpWidget(UncontrolledProviderScope(
        container: kap,
        child: MaterialApp(
            navigatorKey: rythoNavigatorKey, home: const SizedBox()),
      ));
      return kap;
    }

    testWidgets(
        'bırak → jetonu unut → oturum kapat → bayrağı düşür; ilk ikisi kimlik '
        'hâlâ varken', (tester) async {
      final sira = <String>[];
      final adapter = _SahteAdapter(
          govde: '{"released":true}', onIstek: (_) => sira.add('release'));
      final kap = await agac(tester, adapter);

      // Dio hattı testin sahte zamanında ilerlemez → gerçek olay döngüsü.
      await tester.runAsync(() => signOutEverywhere(
          forgetToken: () async => sira.add('forget'),
          signOut: () async => sira.add('signOut')));

      expect(sira, ['release', 'forget', 'signOut'],
          reason: 'DELETE /device/claim ve jeton sökme Firebase kimliğiyle '
              'gider; çıkıştan sonra çağrılsa 401/kural reddi yer — eski '
              'cihaz kilidi elinde, eski hesabın push\'u telefonda kalırdı');
      final istek = adapter.istekler.single;
      expect(istek.method, 'DELETE');
      expect(istek.path, '/api/v1/device/claim');
      expect(kap.read(deviceConflictProvider), isNull,
          reason: 'bayrak inmese bir sonraki giriş aynı ekrana düşerdi');
    });

    testWidgets('bırakma düşse de (500) çıkış sürer ve bayrak iner',
        (tester) async {
      var cikis = 0;
      final adapter = _SahteAdapter(durum: 500, govde: '{"detail":"patladı"}');
      final kap = await agac(tester, adapter);
      await tester.runAsync(
          () => signOutEverywhere(signOut: () async => cikis++));
      expect(adapter.istekler, hasLength(1));
      expect(cikis, 1);
      expect(kap.read(deviceConflictProvider), isNull);
    });
  });

  group('bekçi — eski devralma makinesi silindi', () {
    Iterable<File> kaynaklar() => Directory('lib')
        .listSync(recursive: true)
        .whereType<File>()
        .where((f) => f.path.endsWith('.dart'));

    test('maybeConfirmDeviceTakeover / resetDeviceTakeoverPrompt kodda YOK; '
        'device_claim.dart yok', () {
      for (final dosya in kaynaklar()) {
        final kaynak = dosya.readAsStringSync();
        expect(kaynak, isNot(contains('maybeConfirmDeviceTakeover')),
            reason: dosya.path);
        expect(kaynak, isNot(contains('resetDeviceTakeoverPrompt')),
            reason: dosya.path);
      }
      expect(File('lib/core/device_claim.dart').existsSync(), isFalse);
    });

    test('409 yolu oturuma dokunmaz: device_session.dart Firebase bilmez, '
        'api.dart oturum kapatmaz, kanca apiProvider\'a bağlı', () {
      final oturum = File('lib/core/device_session.dart').readAsStringSync();
      expect(oturum, isNot(contains('firebase_auth')));
      expect(oturum, isNot(contains('.signOut(')));

      final api = File('lib/core/api.dart').readAsStringSync();
      expect(api, isNot(contains('.signOut(')),
          reason: '409\'da signOut devralmayı 401\'e çarptırıyordu');
      expect(api, contains('deviceConflictInterceptor('));
      expect(api, contains('noteDeviceConflict('));
    });

    test('her istek platformu taşır: api.dart X-Device-Platform başlığını '
        'devicePlatform() ile yazar; claim gövdesi aynı kaynaktan', () {
      // Sunucu otomatik devralmada bunu kayda yazar; yoksa kaybeden cihazın
      // ekranı "öbür cihaz" diye KENDİ platformunu okurdu.
      final api = File('lib/core/api.dart').readAsStringSync();
      expect(api, contains('options.headers[kDevicePlatformHeader] = '
          'devicePlatform()'));
      expect(kDevicePlatformHeader.toLowerCase(), 'x-device-platform');
      expect(devicePlatform(), defaultTargetPlatform.name);
      expect(devicePlatform(), isNotEmpty);
    });
  });
}
