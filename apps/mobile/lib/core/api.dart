import 'package:dio/dio.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../features/paywall/paywall_screen.dart';
import 'locale.dart';

/// Paywall'ı herhangi bir ekrandan açabilmek için kök navigatör.
final GlobalKey<NavigatorState> rythoNavigatorKey = GlobalKey<NavigatorState>();

/// Kilitli özellik için sunucunun döndürdüğü HTTP kodu.
const int kPaywallStatus = 402;

bool _paywallOpen = false;

/// Sunucu 402 döndüğünde paywall'ı açar.
///
/// Kilit kararı tek yerde — sunucuda — verilir; istemci hangi ekranda olursa
/// olsun aynı davranışı gösterir. Böylece her ekrana ayrı kilit mantığı
/// yazmak gerekmez ve arayüz ile sunucu birbirinden ayrışamaz.
Future<void> _showPaywall(String? reason) async {
  if (_paywallOpen) return;
  final navigator = rythoNavigatorKey.currentState;
  if (navigator == null) return;

  _paywallOpen = true;
  try {
    await navigator.push(MaterialPageRoute(
      builder: (_) => PaywallScreen(reason: reason),
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
      options.headers['Accept-Language'] = acceptLanguageHeader();
      handler.next(options);
    },
    onError: (error, handler) {
      if (error.response?.statusCode == kPaywallStatus) {
        final detail = error.response?.data is Map
            ? (error.response!.data as Map)['detail'] as String?
            : null;
        _showPaywall(detail);
      }
      handler.next(error);
    },
  ));
  return dio;
});

/// Hata mesajını kullanıcıya gösterilebilir hale getirir.
///
/// Backend her hatada Türkçe ve anlaşılır bir `detail` döndürüyor (kota,
/// paywall, sunucu hatası). Ham `DioException` metnini ekrana basmak
/// kullanıcıya HTTP durum kodu ve MDN bağlantısı göstermek demek.
String friendlyError(Object error) {
  if (error is DioException) {
    final data = error.response?.data;
    if (data is Map && data['detail'] is String) return data['detail'] as String;
    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.connectionError) {
      return 'Bağlantı kurulamadı. İnternetini kontrol edip tekrar dene.';
    }
  }
  return 'Beklenmeyen bir sorun oluştu. Lütfen biraz sonra tekrar dene.';
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
