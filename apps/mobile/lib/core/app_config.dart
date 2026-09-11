/// Zorunlu güncelleme kapısı (F3 → PBZ: sunucu zorlaması + sıcak anahtar).
///
/// Kapı iki kaynaktan kapanır:
/// 1. **Sunucu zorlaması:** her API isteği `X-App-Build` taşır
///    ([appBuildInterceptor]); sunucu eşiğin altındaki derlemeye 426 döner
///    ve kapı O ANDA kapanır — açık oturum da ([updateRequiredInterceptor]
///    → [forceUpdateProvider]). Eskiden kapı yalnız istemcideydi ve süreç
///    başına bir kez bakılıyordu; açık oturum günlerce eski sürümde kalırdı.
/// 2. **Açılış okuması:** giriş ekranından ÖNCE, kimliksiz
///    `/api/v1/config/app` ucundan eşik okunur ([updateRequiredProvider]);
///    ön plana dönüşte ≥30 sn geçtiyse yeniden ([UpdateGateObserver]).
///
/// FELSEFE "BİLİNEN EŞİK KİLİTLER": eski hâli her hatada açıktı (ağ yok /
/// zaman aşımı / 429 / 5xx → false) — çevrimdışı açılan eski sürüm kapıdan
/// geçiyordu. Şimdi sunucudan okunan her eşik (0 dahil) cihazda saklanır;
/// sunucuya ulaşılamazsa SON BİLİNEN eşik geçerli. Daha önce hiç eşik
/// görülmediyse (taze kurulum, ilk açılış çevrimdışı) kapı yine açık —
/// bilinmeyen eşikle kimse kilitlenmez; derleme numarası okunamıyorsa da
/// kilitlenmez ("ölçülmeyen söylenmez").
library;

import 'dart:async' show unawaited;

import 'package:dio/dio.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart' show StateProvider;
import 'package:package_info_plus/package_info_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'api.dart' show kApiBaseUrl;

/// Sunucunun "bu derleme desteklenmiyor" kodu (gövde: `min_build`).
const int kUpdateRequiredStatus = 426;

/// Her istekte taşınan derleme numarası başlığı (sunucu: `core/app_gate.py`).
const String kAppBuildHeader = 'X-App-Build';

/// Son bilinen eşiğin SharedPreferences anahtarı.
const String kMinBuildSeenKey = 'minBuildSeen';

/// Ön plana dönüşte eşiğin yeniden okunması için asgari aralık.
const Duration kUpdateRecheckInterval = Duration(seconds: 30);

/// Açılış okumasının zaman aşımı — açılışı bundan fazla bekletmeyiz.
const Duration _kFetchTimeout = Duration(seconds: 8);

/// Bu derlemenin numarası (pubspec `+N`). PackageInfo BİR kez okunur;
/// okunamazsa 0 = bilinmiyor.
final appBuildProvider = FutureProvider<int>((_) async {
  try {
    final paket = await PackageInfo.fromPlatform();
    return int.tryParse(paket.buildNumber) ?? 0;
  } catch (e) {
    debugPrint('Derleme numarası okunamadı: $e');
    return 0;
  }
});

typedef MinBuildFetcher = Future<int> Function(int buBuild);

/// Sunucudan eşiği okur; hata fırlatır, karar [updateRequiredProvider]'da.
Future<int> fetchMinBuild(int buBuild) async {
  // apiProvider bilerek KULLANILMIYOR: o kimlik/dil interceptor'larıyla
  // oturuma bağlı; bu istekse oturumdan önce ve tamamen anonim.
  final dio = Dio(BaseOptions(
    baseUrl: kApiBaseUrl,
    connectTimeout: _kFetchTimeout,
    receiveTimeout: _kFetchTimeout,
  ));
  final yanit = await dio.get(
    '/api/v1/config/app',
    options: Options(headers: {if (buBuild > 0) kAppBuildHeader: '$buBuild'}),
  );
  return ((yanit.data as Map)['data']['min_build'] as num?)?.toInt() ?? 0;
}

/// Test dikişi: sahte sunucu.
final minBuildFetcherProvider = Provider<MinBuildFetcher>((_) => fetchMinBuild);

/// Saf karar: derleme bilinmiyorsa (0) ya da eşik yoksa (≤0) kapı AÇIK;
/// yoksa eşiğin altı kilitler.
bool updateRequired({required int buBuild, required int minBuild}) =>
    buBuild != 0 && minBuild > 0 && buBuild < minBuild;

/// Sunucudan gelen eşiği saklar — 0 DAHİL: sunucu eşiği sıfırlarsa
/// çevrimdışı kilit de kalkmalı.
Future<void> rememberMinBuild(int minBuild) async {
  try {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(kMinBuildSeenKey, minBuild);
  } catch (e) {
    debugPrint('Sürüm eşiği saklanamadı: $e');
  }
}

/// Son bilinen eşik; hiç görülmediyse (ya da okunamazsa) 0 = kapı açık.
Future<int> lastSeenMinBuild() async {
  try {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getInt(kMinBuildSeenKey) ?? 0;
  } catch (_) {
    return 0;
  }
}

/// true = bu derleme sunucunun istediği asgari sürümün ALTINDA;
/// uygulama ForceUpdateScreen'e kilitlenir.
///
/// Sunucu okunursa eşik saklanır; okunamazsa son bilinen eşik kullanılır
/// (bilinen eşik kilitler — dosya başlığı). [UpdateGateObserver] ön plana
/// dönüşte `invalidate` eder; derleme numarası ayrı sağlayıcıda olduğu
/// için PackageInfo yeniden okunmaz.
final updateRequiredProvider = FutureProvider<bool>((ref) async {
  final buBuild = await ref.watch(appBuildProvider.future);
  final int esik;
  try {
    esik = await ref.watch(minBuildFetcherProvider)(buBuild);
  } catch (e) {
    debugPrint('Sürüm eşiği okunamadı, son bilinen geçerli: $e');
    return updateRequired(buBuild: buBuild, minBuild: await lastSeenMinBuild());
  }
  await rememberMinBuild(esik);
  return updateRequired(buBuild: buBuild, minBuild: esik);
});

/// Herhangi bir API isteği 426 aldı — açık oturumda sunucu zorlaması.
///
/// Yalnız [updateRequiredInterceptor] kaldırır (true), yalnız
/// [UpdateGateObserver] indirir (false): ön plana dönüşte sunucu "eşiğin
/// altında değil" derse (operatör eşiği 0'a çekti) kilit süreç içinde de
/// açılır; aksi hâlde tek çıkış uygulamayı öldürmekti.
final forceUpdateProvider = StateProvider<bool>((_) => false);

/// Kapının tek sorusu: sunucu zorladı MI ya da açılış okuması eşiğin
/// altında MI dedi? (`_Gate` bunu izler.)
final mustForceUpdateProvider = Provider<bool>((ref) {
  // İKİSİ DE KOŞULSUZ izlenir. `a || b` kısa devre yapınca bayrak bir kez
  // true olduğunda açılış okumasına bağımlılık düşüyordu: ön plan yeniden
  // okuması yapılıyor ama kapı onu hiç duymuyordu.
  final zorlandi = ref.watch(forceUpdateProvider);
  final esiginAltinda = ref.watch(updateRequiredProvider).value == true;
  return zorlandi || esiginAltinda;
});

/// Her isteğe `X-App-Build` ekler. Derleme bilinmiyorsa (0) başlık YOK —
/// sunucu başlıksız isteği zaten 0 sayar; uydurma değer göndermeyiz.
Interceptor appBuildInterceptor(Future<int> Function() build) =>
    InterceptorsWrapper(
      onRequest: (options, handler) async {
        var b = 0;
        try {
          b = await build();
        } catch (_) {
          // Derleme okunamadıysa istek yine gider; kapı sunucuda.
        }
        if (b > 0) options.headers[kAppBuildHeader] = '$b';
        handler.next(options);
      },
    );

/// 426 → [onRequired] + gövdedeki `min_build` saklanır (çevrimdışı açılış
/// için); hata olduğu gibi devam eder ki çağıran ekran da öğrensin.
Interceptor updateRequiredInterceptor(VoidCallback onRequired) =>
    InterceptorsWrapper(
      onError: (error, handler) async {
        if (error.response?.statusCode == kUpdateRequiredStatus) {
          try {
            onRequired();
          } catch (e) {
            debugPrint('Zorunlu güncelleme bayrağı kurulamadı: $e');
          }
          final data = error.response?.data;
          final esik =
              data is Map ? (data['min_build'] as num?)?.toInt() : null;
          if (esik != null) await rememberMinBuild(esik);
        }
        handler.next(error);
      },
    );

/// Ön plana dönüşte eşiği yeniden okutur; sunucu "gerekmiyor" derse 426
/// bayrağını da indirir.
///
/// Eski kapı non-autoDispose bir FutureProvider'dı ve hiç invalidate
/// edilmiyordu: süreç başına BİR kez bakılıyor, günlerce açık kalan oturum
/// eşiği hiç görmüyordu. [SystemLocaleObserver] ile aynı yerde, köke bir kez
/// takılır (bkz. `main.dart`). Aralık [kUpdateRecheckInterval]: her sekme
/// değişiminde sunucuya gitmeyelim.
///
/// Bayrağı indirme BURADA, sağlayıcı gövdesinde değil: sağlayıcı kurulurken
/// başka sağlayıcı değiştirilmez. Okuma düşerse bayrağa dokunulmaz — 426
/// gövdesindeki eşik zaten cihazda ([updateRequiredInterceptor]), son
/// bilinen eşik kilitler (dosya başlığı).
///
/// [now] test dikişidir.
class UpdateGateObserver extends ConsumerStatefulWidget {
  const UpdateGateObserver({super.key, required this.child, this.now});

  final Widget child;
  final DateTime Function()? now;

  @override
  ConsumerState<UpdateGateObserver> createState() =>
      _UpdateGateObserverState();
}

class _UpdateGateObserverState extends ConsumerState<UpdateGateObserver>
    with WidgetsBindingObserver {
  late DateTime _sonKontrol;

  DateTime _simdi() => (widget.now ?? DateTime.now)();

  @override
  void initState() {
    super.initState();
    // Açılış okuması ilk kontrol sayılır.
    _sonKontrol = _simdi();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state != AppLifecycleState.resumed) return;
    final simdi = _simdi();
    if (simdi.difference(_sonKontrol) < kUpdateRecheckInterval) return;
    _sonKontrol = simdi;
    unawaited(_yenidenOku());
  }

  /// Eşiği yeniden okur; sunucu "eşiğin altında değil" derse (0'a çekildi
  /// ya da bu derleme artık yeterli) 426 bayrağı iner ve kapı açılır.
  Future<void> _yenidenOku() async {
    ref.invalidate(updateRequiredProvider);
    final bool gerekli;
    try {
      gerekli = await ref.read(updateRequiredProvider.future);
    } catch (e) {
      // Sağlayıcı fırlatmaz (düşen okuma son bilinene düşer); yine de
      // bilinmeyen durumda kilide dokunmayız.
      debugPrint('Sürüm eşiği yeniden okunamadı: $e');
      return;
    }
    if (!mounted || gerekli) return;
    if (ref.read(forceUpdateProvider)) {
      ref.read(forceUpdateProvider.notifier).state = false;
    }
  }

  @override
  Widget build(BuildContext context) => widget.child;
}
