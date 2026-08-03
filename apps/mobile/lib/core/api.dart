import 'package:dio/dio.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../features/auth/device_conflict_screen.dart';
import '../features/paywall/paywall_screen.dart';
import '../features/paywall/token_store_screen.dart';
import '../l10n/app_localizations.dart';
import 'device_id.dart';
import 'locale.dart';

/// Paywall'ı herhangi bir ekrandan açabilmek için kök navigatör.
final GlobalKey<NavigatorState> rythoNavigatorKey = GlobalKey<NavigatorState>();

/// Kilitli özellik için sunucunun döndürdüğü HTTP kodu.
const int kPaywallStatus = 402;

/// Tek cihaz kilidinin çakışma kodu (X-Device-Conflict başlığıyla birlikte).
const int kDeviceConflictStatus = 409;

bool _paywallOpen = false;
bool _deviceConflictHandling = false;

/// Cihaz çakışması: oturumu kapat ve çakışma ekranına düş.
///
/// Oturumun kapanması yeterli değil — kullanıcı NEDEN atıldığını görmeli.
/// Sessiz signOut, "uygulama bozuldu" hissi verir; ekran ise devralma
/// yolunu gösterir.
Future<void> _handleDeviceConflict() async {
  if (_deviceConflictHandling) return;
  _deviceConflictHandling = true;
  try {
    await FirebaseAuth.instance.signOut();
    final navigator = rythoNavigatorKey.currentState;
    if (navigator == null) return;
    await navigator.push(MaterialPageRoute(
      builder: (_) => const DeviceConflictScreen(),
      fullscreenDialog: true,
    ));
  } catch (_) {
    // signOut düşerse bile bayrak açık kalmasın; sonraki 409 yine dener.
  } finally {
    _deviceConflictHandling = false;
  }
}

/// Sunucu 402 döndüğünde doğru ekranı açar.
///
/// Kilit kararı tek yerde — sunucuda — verilir; istemci hangi ekranda olursa
/// olsun aynı davranışı gösterir. İki 402 türü var ve ayrım `detail`
/// metnine GÖMÜLEMEZ (o alan kullanıcıya gösterilen düz metin); sunucu
/// `X-Paywall-Reason: tokens` başlığıyla söyler:
///
/// * başlık yok  → abonelik sorunu → [PaywallScreen] ("abone ol")
/// * `tokens`    → bakiye bitti    → [TokenStoreScreen] ("doldur")
///
/// Token'ı biten aboneye abonelik satmaya çalışmak yanlış teşhis olurdu.
Future<void> _showPaywall(String? reason, {bool tokens = false}) async {
  if (_paywallOpen) return;
  final navigator = rythoNavigatorKey.currentState;
  if (navigator == null) return;

  _paywallOpen = true;
  try {
    await navigator.push(MaterialPageRoute(
      builder: (_) => tokens
          ? TokenStoreScreen(reason: reason)
          : PaywallScreen(reason: reason),
      fullscreenDialog: true,
    ));
  } finally {
    _paywallOpen = false;
  }
}

/// Backend adresi: --dart-define=RYTHO_API_URL=... ile geçilir;
/// verilmezse Cloud Run üretim adresi kullanılır.
const String kApiBaseUrl = String.fromEnvironment(
  'RYTHO_API_URL',
  defaultValue: 'https://rytho-backend-770582338651.us-central1.run.app',
);

final apiProvider = Provider<Dio>((ref) {
  // Dil izleniyor: değiştiğinde bu sağlayıcı yeniden kurulur ve ona bağlı tüm
  // ağ sağlayıcıları (burç yorumu, gökyüzü, günlük okuma...) tazelenir.
  // İzlenmezse başlık yalnızca SONRAKİ isteklerde değişir; ekrandaki yorum
  // eski dilde asılı kalır — dil değiştirmenin en görünür kusuru buydu.
  final locale = ref.watch(localeProvider);

  final dio = Dio(BaseOptions(
    baseUrl: kApiBaseUrl,
    connectTimeout: const Duration(seconds: 20),
    receiveTimeout: const Duration(seconds: 120),
  ));
  dio.interceptors.add(InterceptorsWrapper(
    onRequest: (options, handler) async {
      final user = FirebaseAuth.instance.currentUser;
      if (user != null) {
        final token = await user.getIdToken();
        options.headers['Authorization'] = 'Bearer $token';
      }
      // Backend yorumları bu başlığa göre üretir (persona, korpus ve önbellek
      // dahil). Gönderilmezse sunucu Türkçe varsayar ve arayüz İngilizce olsa
      // bile yorumlar Türkçe gelir.
      options.headers['Accept-Language'] = acceptLanguageHeader(locale);
      // Tek cihaz kilidi (yalnızca abonelerde etkili). Sunucu bu kimliği
      // kayıtlı cihazla karşılaştırır; uyuşmazlıkta 409 döner (aşağıda).
      options.headers['X-Device-Id'] = await deviceId();
      handler.next(options);
    },
    onError: (error, handler) {
      if (error.response?.statusCode == kPaywallStatus) {
        final detail = error.response?.data is Map
            ? (error.response!.data as Map)['detail'] as String?
            : null;
        final sebep =
            error.response?.headers.value('x-paywall-reason');
        _showPaywall(detail, tokens: sebep == 'tokens');
      }
      // Tek cihaz kilidi: abonelik başka cihazda devralınmış. Oturum
      // kapatılır ve çakışma ekranına düşülür — oradan yeniden girip
      // "bu cihazda kullan" denebilir.
      if (error.response?.statusCode == kDeviceConflictStatus &&
          error.response?.headers.value('x-device-conflict') == '1') {
        _handleDeviceConflict();
      }
      handler.next(error);
    },
  ));
  return dio;
});

/// FastAPI'nin KENDİ ürettiği, çevrilmemiş gövde metinleri.
///
/// Sunucumuz kendi hatalarında `detail` alanını kullanıcının dilinde üretiyor
/// (`core/messages.py` → `text()`) ve o metinler olduğu gibi gösterilebilir.
/// Ama **yönlendirme düzeyindeki** hataları — var olmayan uç, yanlış metot —
/// FastAPI üretiyor ve bunlar İngilizce sabitler.
///
/// Cihaz testinde tam olarak bu görüldü: yüz okuma ucu henüz deploy
/// edilmemişti, sunucu 404 döndü ve rıza ekranında kullanıcıya kırmızı
/// **"Not Found"** yazdı.
const _cerceveMetinleri = {'Not Found', 'Method Not Allowed'};

/// Hata mesajını kullanıcıya gösterilebilir hale getirir.
///
/// Backend kendi hatalarında kullanıcının dilinde ve anlaşılır bir `detail`
/// döndürüyor (kota, paywall, sunucu hatası). Ham `DioException` metnini
/// ekrana basmak kullanıcıya HTTP durum kodu ve MDN bağlantısı göstermek
/// demek.
String friendlyError(Object error, [AppLocalizations? l10n]) {
  if (error is DioException) {
    // Sunucunun `detail` alani zaten kullanicinin dilinde uretiliyor
    // (Accept-Language ile), o yuzden oldugu gibi gosterilir — cerceveden
    // gelenler HARIC.
    final data = error.response?.data;
    if (data is Map && data['detail'] is String) {
      final detay = data['detail'] as String;
      if (!_cerceveMetinleri.contains(detay)) return detay;
    }
    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.connectionError) {
      return l10n?.errorConnection ??
          'Bağlantı kurulamadı. İnternetini kontrol edip tekrar dene.';
    }
  }
  return l10n?.errorGeneric ??
      'Beklenmeyen bir sorun oluştu. Lütfen biraz sonra tekrar dene.';
}

/// Kullanıcının doğum verisini backend'in beklediği gövdeye çevirir.
Map<String, dynamic> birthPayload(Map<String, dynamic> profile) {
  final birthDate = (profile['birthDate'] as String?) ?? '2000-01-01';
  final birthTime = (profile['birthTime'] as String?) ?? '12:00';
  final dateParts = birthDate.split('-').map(int.parse).toList();
  final timeParts = birthTime.split(':').map(int.parse).toList();
  return {
    'name': profile['displayName'] ?? 'Gezgin',
    'year': dateParts[0],
    'month': dateParts[1],
    'day': dateParts[2],
    'hour': timeParts[0],
    'minute': timeParts[1],
    'city': profile['birthCity'] ?? 'Istanbul',
    'nation': profile['birthNation'],
    'gender': profile['gender'] ?? 'female',
  };
}
