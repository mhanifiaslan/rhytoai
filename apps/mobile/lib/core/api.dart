import 'package:dio/dio.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

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
      handler.next(options);
    },
  ));
  return dio;
});

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
