import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'analytics.dart';
import 'api.dart';
import 'subscription.dart';

/// Firebase oturum akışı.
final authStateProvider = StreamProvider<User?>(
  (ref) => FirebaseAuth.instance.authStateChanges(),
);

/// Engellenen kullanıcı kimlikleri (users/{uid}/blocked). Akış ve mesajlar
/// bu kümeye göre istemci tarafında filtrelenir.
final blockedUsersProvider = StreamProvider<Set<String>>((ref) {
  final user = ref.watch(authStateProvider).value;
  if (user == null) return Stream.value(<String>{});
  return FirebaseFirestore.instance
      .collection('users')
      .doc(user.uid)
      .collection('blocked')
      .snapshots()
      .map((snapshot) => snapshot.docs.map((d) => d.id).toSet());
});

/// Firestore'daki kullanıcı profili (users/{uid}).
final profileProvider = StreamProvider<Map<String, dynamic>?>((ref) {
  final user = ref.watch(authStateProvider).value;
  if (user == null) return Stream.value(null);
  return FirebaseFirestore.instance
      .collection('users')
      .doc(user.uid)
      .snapshots()
      .map((snapshot) => snapshot.data());
});

/// Anlık gökyüzü durumu (retrolar, Ay evresi, açılar, NASA mesafeleri).
final skyNowProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final dio = ref.watch(apiProvider);
  final response = await dio.get('/api/v1/sky/now');
  return Map<String, dynamic>.from(response.data['data']);
});

/// Burç bazlı günlük yorum — ÜCRETSİZ katmanın omurgası.
///
/// Kullanıcıdan bağımsızdır ve sunucuda paylaşımlı önbellekten servis edilir:
/// 12 burç için dönem başına tek LLM çağrısı yapılır, kullanıcı sayısı arttıkça
/// maliyet artmaz. Ana ekran bu yüzden hiçbir zaman boş kalmaz.
final signHoroscopeProvider =
    FutureProvider.family<Map<String, dynamic>, String>((ref, signKey) async {
  final dio = ref.watch(apiProvider);
  final response = await dio.get('/api/v1/reports/horoscope/$signKey');
  return Map<String, dynamic>.from(response.data['data']);
});

/// Kişiye özel günlük okuma — Rytho+ .
///
/// Abone olmayan için hiç İSTEK ATILMAZ. Atılsaydı sunucu 402 doner ve paywall
/// her acilista kendiliginden acilirdi; kilitli icerik kullanicinin
/// dokunmasiyla acilmali, yuzune firlatilmamali.
final dailyReadingProvider = FutureProvider<Map<String, dynamic>?>((ref) async {
  if (!_hasPlus(ref)) return null;

  final profile = ref.watch(profileProvider).value;
  if (profile == null || profile['onboardingCompleted'] != true) return null;

  final dio = ref.watch(apiProvider);
  final response =
      await dio.post('/api/v1/reports/daily', data: birthPayload(profile));
  Analytics.reportGenerated('daily');
  return Map<String, dynamic>.from(response.data['data']);
});

/// Abone değilken ücretli uca istek atılmamalı.
///
/// Atılırsa sunucu 402 döner ve paywall ekran açılır açılmaz kullanıcının
/// yüzüne fırlar. Kilitli içerik kullanıcının dokunmasıyla açılmalı; bu yüzden
/// ücretli sağlayıcılar abonelik yoksa `null` döner ve ekranlar kilitli
/// durumu gösterir.
bool _hasPlus(Ref ref) =>
    ref.watch(subscriptionProvider).value?.active ?? false;

/// Natal harita + derin rapor — Rytho+ .
final natalReportProvider = FutureProvider<Map<String, dynamic>?>((ref) async {
  if (!_hasPlus(ref)) return null;
  final profile = ref.watch(profileProvider).value;
  if (profile == null || profile['onboardingCompleted'] != true) return null;
  final dio = ref.watch(apiProvider);
  final response =
      await dio.post('/api/v1/reports/natal', data: birthPayload(profile));
  Analytics.reportGenerated('natal');
  return Map<String, dynamic>.from(response.data['data']);
});

/// BaZi haritası + rapor — Rytho+ .
final baziReportProvider = FutureProvider<Map<String, dynamic>?>((ref) async {
  if (!_hasPlus(ref)) return null;
  final profile = ref.watch(profileProvider).value;
  if (profile == null || profile['onboardingCompleted'] != true) return null;
  final dio = ref.watch(apiProvider);
  final response =
      await dio.post('/api/v1/reports/bazi', data: birthPayload(profile));
  Analytics.reportGenerated('bazi');
  return Map<String, dynamic>.from(response.data['data']);
});
