// Zorunlu güncelleme kapısı bekçileri (PBZ — sunucu zorlaması + sıcak anahtar).
//
// Eski kapının üç kusuru vardı ve üçü de burada sabitlenir:
// 1. **Yalnız istemcide**: hiçbir istek sürüm taşımıyordu, sunucu eski
//    sürümün her isteğini kabul ediyordu → her istek `X-App-Build` taşır,
//    426 gelince kapı O ANDA kapanır.
// 2. **Her hatada açık**: ağ yok / zaman aşımı / 5xx → `false`; çevrimdışı
//    açılan eski sürüm kapıdan geçiyordu → bilinen eşik kilitler
//    (fail-closed), hiç eşik görülmediyse açık.
// 3. **Süreç başına bir kez**: açık oturum günlerce eski sürümde kalıyordu →
//    ön plana dönüşte ≥30 sn geçtiyse eşik yeniden okunur.
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/core/app_config.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Sabit yanıt veren sahte sunucu; son isteğin seçeneklerini saklar.
class _SahteAdapter implements HttpClientAdapter {
  _SahteAdapter({this.durum = 200, this.govde = '{"status":"ok"}'});

  final int durum;
  final String govde;
  RequestOptions? son;

  @override
  Future<ResponseBody> fetch(RequestOptions options,
      Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    son = options;
    return ResponseBody.fromString(
      govde,
      durum,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}

Dio _dio(_SahteAdapter adapter, List<Interceptor> interceptors) {
  final dio = Dio(BaseOptions(baseUrl: 'https://test.invalid'));
  dio.httpClientAdapter = adapter;
  dio.interceptors.addAll(interceptors);
  return dio;
}

/// Sunucunun 426 gövdesi (backend/core/app_gate.py ile aynı şekil).
const _kGovde426 =
    '{"status":"error","code":"update_required","detail":"Güncelle.","min_build":40}';

Future<int?> _saklananEsik() async =>
    (await SharedPreferences.getInstance()).getInt(kMinBuildSeenKey);

/// Sağlayıcı kabı: derleme numarası + sahte eşik okuyucu.
ProviderContainer _kap({
  required int build,
  required Future<int> Function(int buBuild) fetcher,
}) {
  final container = ProviderContainer(overrides: [
    appBuildProvider.overrideWith((_) async => build),
    minBuildFetcherProvider.overrideWithValue(fetcher),
  ]);
  addTearDown(container.dispose);
  return container;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('appBuildInterceptor', () {
    test('her istek X-App-Build başlığını taşır', () async {
      final adapter = _SahteAdapter();
      final dio = _dio(adapter, [appBuildInterceptor(() async => 35)]);
      await dio.get('/api/v1/x');
      expect(adapter.son!.headers[kAppBuildHeader], '35');
    });

    test('derleme bilinmiyorsa (0) başlık YOK — uydurma değer gitmez',
        () async {
      final adapter = _SahteAdapter();
      final dio = _dio(adapter, [appBuildInterceptor(() async => 0)]);
      await dio.get('/api/v1/x');
      expect(adapter.son!.headers.containsKey(kAppBuildHeader), isFalse);
    });

    test('derleme okunamazsa istek yine gider', () async {
      final adapter = _SahteAdapter();
      final dio = _dio(
          adapter, [appBuildInterceptor(() async => throw StateError('yok'))]);
      final yanit = await dio.get('/api/v1/x');
      expect(yanit.statusCode, 200);
      expect(adapter.son!.headers.containsKey(kAppBuildHeader), isFalse);
    });
  });

  group('updateRequiredInterceptor', () {
    test('426 → callback + gövdedeki min_build saklanır; hata devam eder',
        () async {
      SharedPreferences.setMockInitialValues({});
      var cagri = 0;
      final dio = _dio(_SahteAdapter(durum: 426, govde: _kGovde426),
          [updateRequiredInterceptor(() => cagri++)]);

      await expectLater(
          dio.get('/api/v1/x'),
          throwsA(isA<DioException>()
              .having((e) => e.response?.statusCode, 'statusCode', 426)),
          reason: 'çağıran ekran da öğrenmeli — hata yutulmaz');
      expect(cagri, 1);
      // Çevrimdışı açılış için eşik cihazda: bir sonraki soğuk açılışta
      // sunucuya ulaşılamasa da kilit kalkmaz.
      expect(await _saklananEsik(), 40);
    });

    test('426 dışı (500) dokunmaz: callback yok, saklanan eşik aynı',
        () async {
      SharedPreferences.setMockInitialValues({kMinBuildSeenKey: 7});
      var cagri = 0;
      final dio = _dio(
          _SahteAdapter(durum: 500, govde: '{"detail":"patladı"}'),
          [updateRequiredInterceptor(() => cagri++)]);

      await expectLater(dio.get('/api/v1/x'), throwsA(isA<DioException>()));
      expect(cagri, 0);
      expect(await _saklananEsik(), 7);
    });

    test('426 gövdesinde min_build yoksa callback yine çalışır, eşik yazılmaz',
        () async {
      SharedPreferences.setMockInitialValues({});
      var cagri = 0;
      final dio = _dio(_SahteAdapter(durum: 426, govde: '{"detail":"x"}'),
          [updateRequiredInterceptor(() => cagri++)]);
      await expectLater(dio.get('/api/v1/x'), throwsA(isA<DioException>()));
      expect(cagri, 1);
      expect(await _saklananEsik(), isNull);
    });
  });

  group('updateRequired (saf karar)', () {
    test('eşiğin altı kilitler; eşit/üstü geçer; 0 derleme ve 0 eşik açık',
        () {
      expect(updateRequired(buBuild: 35, minBuild: 36), isTrue);
      expect(updateRequired(buBuild: 36, minBuild: 36), isFalse);
      expect(updateRequired(buBuild: 37, minBuild: 36), isFalse);
      expect(updateRequired(buBuild: 0, minBuild: 36), isFalse);
      expect(updateRequired(buBuild: 35, minBuild: 0), isFalse);
      expect(updateRequired(buBuild: 35, minBuild: -1), isFalse);
    });
  });

  group('updateRequiredProvider', () {
    test('fetch 36 / derleme 35 → kilit; eşik cihaza yazılır', () async {
      SharedPreferences.setMockInitialValues({});
      var gorulenBuild = -1;
      final kap = _kap(
          build: 35,
          fetcher: (b) async {
            gorulenBuild = b;
            return 36;
          });
      expect(await kap.read(updateRequiredProvider.future), isTrue);
      expect(gorulenBuild, 35, reason: 'açılış okuması da derlemeyi taşır');
      expect(await _saklananEsik(), 36);
    });

    test('fetch 0 → açık; 0 DA saklanır (eski 40 silinir)', () async {
      // Sunucu eşiği sıfırlarsa çevrimdışı kilit de kalkmalı.
      SharedPreferences.setMockInitialValues({kMinBuildSeenKey: 40});
      final kap = _kap(build: 35, fetcher: (_) async => 0);
      expect(await kap.read(updateRequiredProvider.future), isFalse);
      expect(await _saklananEsik(), 0);
    });

    test('fetch DÜŞER + saklanan 40 → KİLİT (fail-closed)', () async {
      // Eski kapı burada `false` dönüyordu: uçak modundaki eski sürüm
      // kapıdan geçiyordu.
      SharedPreferences.setMockInitialValues({kMinBuildSeenKey: 40});
      final kap = _kap(
          build: 35,
          fetcher: (_) async => throw DioException(
              requestOptions: RequestOptions(path: '/api/v1/config/app'),
              type: DioExceptionType.connectionError));
      expect(await kap.read(updateRequiredProvider.future), isTrue);
      // Düşen okuma saklananı ezmez.
      expect(await _saklananEsik(), 40);
    });

    test('fetch düşer + hiç eşik görülmemiş → açık (bilinmeyen eşik kilitlemez)',
        () async {
      SharedPreferences.setMockInitialValues({});
      final kap = _kap(build: 35, fetcher: (_) async => throw StateError('ağ'));
      expect(await kap.read(updateRequiredProvider.future), isFalse);
      expect(await _saklananEsik(), isNull);
    });

    test('derleme 0 (okunamadı) → açık, eşik 36 olsa da', () async {
      SharedPreferences.setMockInitialValues({});
      final kap = _kap(build: 0, fetcher: (_) async => 36);
      expect(await kap.read(updateRequiredProvider.future), isFalse);
    });
  });

  group('mustForceUpdateProvider', () {
    test('açılış okuması VEYA 426 bayrağı kapıyı kapatır', () async {
      SharedPreferences.setMockInitialValues({});
      final kap = _kap(build: 35, fetcher: (_) async => 0);
      // Sağlayıcı canlı tutulur ki bağımlılık değişince yeniden hesaplansın.
      final degerler = <bool>[];
      kap.listen<bool>(mustForceUpdateProvider, (_, v) => degerler.add(v),
          fireImmediately: true);
      expect(degerler.last, isFalse);

      await kap.read(updateRequiredProvider.future);
      expect(kap.read(mustForceUpdateProvider), isFalse);

      // Açık oturumda herhangi bir istek 426 aldı.
      kap.read(forceUpdateProvider.notifier).state = true;
      expect(kap.read(mustForceUpdateProvider), isTrue);
    });

    test('açılış okuması eşiğin altında derse bayrak olmadan da kapanır',
        () async {
      SharedPreferences.setMockInitialValues({});
      final kap = _kap(build: 35, fetcher: (_) async => 36);
      kap.listen<bool>(mustForceUpdateProvider, (_, _) {});
      expect(kap.read(mustForceUpdateProvider), isFalse,
          reason: 'yanıt beklenmez — splash gecikmesi yok');
      await kap.read(updateRequiredProvider.future);
      expect(kap.read(mustForceUpdateProvider), isTrue);
      expect(kap.read(forceUpdateProvider), isFalse);
    });

    test('426 bayrağı önce gelse bile açılış okumasına bağlı kalır', () {
      // `a || b` kısa devre yapınca bayrak true iken açılış okuması hiç
      // izlenmiyordu: ön plan yeniden okuması yapılıyor, kapı duymuyordu.
      SharedPreferences.setMockInitialValues({});
      final kap = _kap(build: 35, fetcher: (_) async => 0);
      kap.read(forceUpdateProvider.notifier).state = true;
      kap.listen<bool>(mustForceUpdateProvider, (_, _) {});
      expect(kap.read(mustForceUpdateProvider), isTrue);
      expect(kap.exists(updateRequiredProvider), isTrue,
          reason: 'bayrak true iken de açılış okuması izlenmeli');
    });
  });

  group('UpdateGateObserver', () {
    Future<void> yasamDongusu(WidgetTester tester, String durum) async {
      await tester.binding.defaultBinaryMessenger.handlePlatformMessage(
        'flutter/lifecycle',
        const StringCodec().encodeMessage(durum),
        (_) {},
      );
      await tester.pump();
    }

    testWidgets('ön plana dönüşte ≥30 sn geçtiyse eşik yeniden okunur',
        (tester) async {
      SharedPreferences.setMockInitialValues({});
      var okuma = 0;
      var saat = DateTime(2026, 9, 11, 9, 0);
      await tester.pumpWidget(ProviderScope(
        overrides: [
          appBuildProvider.overrideWith((_) async => 35),
          minBuildFetcherProvider.overrideWithValue((_) async {
            okuma++;
            return 0;
          }),
        ],
        child: UpdateGateObserver(
          now: () => saat,
          // Kapı gerçek ağaçtaki gibi sağlayıcıyı izler.
          child: Consumer(
              builder: (_, ref, _) => Text(
                  '${ref.watch(mustForceUpdateProvider)}',
                  textDirection: TextDirection.ltr)),
        ),
      ));
      await tester.pump();
      expect(okuma, 1, reason: 'açılış okuması');

      // 10 sn sonra ön plan: sekme değiştirmiş olabilir — sunucuya gidilmez.
      saat = saat.add(const Duration(seconds: 10));
      await yasamDongusu(tester, 'AppLifecycleState.inactive');
      await yasamDongusu(tester, 'AppLifecycleState.resumed');
      expect(okuma, 1);

      // 31 sn sonra ön plan: eski kapı burada HİÇ bakmıyordu (süreç başına
      // bir kez) — açık oturum günlerce eski sürümde kalıyordu.
      saat = saat.add(const Duration(seconds: 31));
      await yasamDongusu(tester, 'AppLifecycleState.paused');
      await yasamDongusu(tester, 'AppLifecycleState.resumed');
      await tester.pump();
      expect(okuma, 2);

      // Arka plana gidiş tek başına okutmaz.
      saat = saat.add(const Duration(minutes: 5));
      await yasamDongusu(tester, 'AppLifecycleState.paused');
      expect(okuma, 2);
    });

    /// Gerçek ağaç gibi: kap + gözlemci + kapıyı izleyen Consumer. Kap
    /// dışarıda tutulur ki 426 api.dart'taki dikişle aynı yoldan
    /// (interceptor → bayrak) bağlansın.
    Future<ProviderContainer> agac(
      WidgetTester tester, {
      required DateTime Function() now,
      required MinBuildFetcher fetcher,
    }) async {
      final kap = ProviderContainer(overrides: [
        appBuildProvider.overrideWith((_) async => 35),
        minBuildFetcherProvider.overrideWithValue(fetcher),
      ]);
      addTearDown(kap.dispose);
      await tester.pumpWidget(UncontrolledProviderScope(
        container: kap,
        child: UpdateGateObserver(
          now: now,
          child: Consumer(
              builder: (_, ref, _) => Text(
                  '${ref.watch(mustForceUpdateProvider)}',
                  textDirection: TextDirection.ltr)),
        ),
      ));
      await tester.pump();
      return kap;
    }

    /// Açık oturumdaki bir istek 426 aldı (gövde: min_build 40). Dio'nun
    /// hattı testin sahte zamanında ilerlemez → gerçek olay döngüsünde.
    Future<void> istek426(WidgetTester tester, ProviderContainer kap) =>
        tester.runAsync(() async {
          final dio = _dio(_SahteAdapter(durum: 426, govde: _kGovde426), [
            updateRequiredInterceptor(
                () => kap.read(forceUpdateProvider.notifier).state = true),
          ]);
          await expectLater(
              dio.get('/api/v1/x'), throwsA(isA<DioException>()));
        });

    Future<void> onPlanaDonus(WidgetTester tester) async {
      await yasamDongusu(tester, 'AppLifecycleState.paused');
      await yasamDongusu(tester, 'AppLifecycleState.resumed');
      await tester.pumpAndSettle();
    }

    testWidgets('426 sonrası eşik sıfıra çekilirse ön plana dönüş kilidi AÇAR',
        (tester) async {
      // Eski kod: bayrak hiç inmiyordu ve `||` kısa devresi yüzünden kapı
      // yeniden okumayı duymuyordu — operatör eşiği geri alsa da tek çıkış
      // uygulamayı öldürmekti.
      SharedPreferences.setMockInitialValues({});
      var saat = DateTime(2026, 9, 11, 9, 0);
      var sunucuEsik = 0;
      final kap = await agac(tester,
          now: () => saat, fetcher: (_) async => sunucuEsik);
      expect(find.text('false'), findsOneWidget);

      sunucuEsik = 40;
      await istek426(tester, kap);
      await tester.pump();
      expect(find.text('true'), findsOneWidget);
      expect(await _saklananEsik(), 40);

      // Eşik hâlâ 40: ön plana dönüş kilidi açmaz, bayrak yerinde.
      saat = saat.add(const Duration(seconds: 31));
      await onPlanaDonus(tester);
      expect(find.text('true'), findsOneWidget);
      expect(kap.read(forceUpdateProvider), isTrue);

      // Operatör eşiği 0'a çekti (belgelenmiş geri alma).
      sunucuEsik = 0;
      saat = saat.add(const Duration(seconds: 31));
      await onPlanaDonus(tester);
      expect(find.text('false'), findsOneWidget);
      expect(kap.read(forceUpdateProvider), isFalse);
      expect(await _saklananEsik(), 0, reason: 'çevrimdışı kilit de kalkar');
    });

    testWidgets('426 sonrası yeniden okuma düşerse kilit KALIR', (tester) async {
      // Düşen okuma "gerekmiyor" demek değildir; 426 gövdesindeki eşik
      // cihazda, son bilinen eşik kilitler.
      SharedPreferences.setMockInitialValues({});
      var saat = DateTime(2026, 9, 11, 9, 0);
      var okuma = 0;
      var sunucuDusuk = false;
      final kap = await agac(tester, now: () => saat, fetcher: (_) async {
        okuma++;
        if (sunucuDusuk) throw StateError('ağ');
        return 0;
      });
      expect(find.text('false'), findsOneWidget);

      await istek426(tester, kap);
      await tester.pump();
      expect(find.text('true'), findsOneWidget);

      sunucuDusuk = true;
      saat = saat.add(const Duration(seconds: 31));
      await onPlanaDonus(tester);
      expect(okuma, 2, reason: 'yeniden okuma denendi');
      expect(find.text('true'), findsOneWidget);
      expect(kap.read(forceUpdateProvider), isTrue,
          reason: 'bilinmeyen durumda bayrak inmez');
      expect(await _saklananEsik(), 40);
    });
  });
}
