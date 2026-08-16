import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart' show StateProvider;

import 'analytics.dart';
import 'api.dart';
import 'subscription.dart';

/// Firebase oturum akışı.
final authStateProvider = StreamProvider<User?>(
  (ref) => FirebaseAuth.instance.authStateChanges(),
);

/// Onboarding finalinin sonucu (R12-B1 + O3).
enum OnboardOutcome {
  /// Harita hesaplandı — Büyük Üçlü perdesi açılır.
  chartOk,

  /// Doğum verisi yazıldı ama harita hesaplanamadı (ör. çevrimdışı).
  /// Perde açılmaz; kullanıcıya DÜRÜSTÇE söylenir — eskiden bu durum
  /// sessizce yutuluyordu ve rozetlerin yokluğu açıklanamıyordu.
  chartMissing,
}

/// Onboarding'i BU oturumda bitiren kullanıcının sonucu (R12-B1).
///
/// `saveBirthRecord` onboardingCompleted'ı tek yazımda yazar ve yazım iner
/// inmez `_Gate` kabuğa geçer — Büyük Üçlü perdesi bu yüzden onboarding
/// ekranında yaşayamaz. Değer yazım ÖNCESİ konur; AppShell ilk karede
/// görür, sahneyi oynatır ve sıfırlar. Kalıcı değil: uygulamanın sonraki
/// açılışlarında sahne tekrarlanmaz.
final justOnboardedProvider = StateProvider<OnboardOutcome?>((_) => null);

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

/// Bir profil anlık görüntüsüne **karar için** güvenilebilir mi?
///
/// Firestore, dinleyici kurulduğunda önce yerel önbellekten yayın yapıyor.
/// Önbellek boşsa (taze kurulum, yeni giriş) bu yayın "doküman yok" diyor —
/// oysa doküman sunucuda duruyor. Sunucu yanıtı bir an sonra geliyor ve
/// düzeliyor.
///
/// Cihaz testinde görülen şey buydu: giriş yapınca doğum bilgisi formu
/// açılıyor, sonra kendiliğinden geçiyordu. Kullanıcının profili tamdı
/// (`onboardingCompleted = true`); uygulama yalnızca bir anlığına yokmuş gibi
/// davranıyordu.
///
/// Kural: **var olan bir doküman her zaman güvenilir; "yok" bilgisi ancak
/// SUNUCUDAN geldiyse güvenilir.**
bool profileSnapshotIsAuthoritative({
  required bool exists,
  required bool isFromCache,
}) =>
    exists || !isFromCache;

/// Firestore'daki kullanıcı profili (users/{uid}).
final profileProvider = StreamProvider<Map<String, dynamic>?>((ref) {
  final user = ref.watch(authStateProvider).value;
  if (user == null) return Stream.value(null);
  return FirebaseFirestore.instance
      .collection('users')
      .doc(user.uid)
      .snapshots()
      // Güvenilmez anlık görüntü YAYILMIYOR; sağlayıcı o sırada `loading`
      // kalıyor ve arayüz açılış ekranını gösteriyor. Yanlış bir "profil yok"
      // yaymak, kullanıcıyı verisi dururken onboarding'e düşürüyordu.
      .where((s) => profileSnapshotIsAuthoritative(
            exists: s.exists,
            isFromCache: s.metadata.isFromCache,
          ))
      .map((snapshot) => snapshot.data());
});

/// Anlık gökyüzü durumu (retrolar, Ay evresi, açılar, NASA mesafeleri).
final skyNowProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final dio = ref.watch(apiProvider);
  final response = await dio.get('/api/v1/sky/now');
  return Map<String, dynamic>.from(response.data['data']);
});

/// Doğum haritası — ÜCRETSİZ katman (R2-F1).
///
/// Çark, yerleşimler, evler ve açılar herkese açıktır: bunlar hesaptır,
/// LLM maliyeti YOKTUR. Kullanıcı ilk dakikada "bu uygulama gerçekten
/// benim haritamı biliyor" diyebilmeli; ücretli olan, bu haritanın
/// Rytho tarafından OKUNMASI (natalReportProvider).
final natalChartProvider =
    FutureProvider<Map<String, dynamic>?>((ref) async {
  final profile = ref.watch(profileProvider).value;
  if (profile == null || profile['onboardingCompleted'] != true) return null;
  final dio = ref.watch(apiProvider);
  final response = await dio.post('/api/v1/astrology/natal-chart',
      data: birthPayload(profile));
  return Map<String, dynamic>.from(response.data['data']);
});

/// Günlük girişleri (R2-G1/R4-3): yeniden eskiye.
///
/// Ana ekrandaki hızlı giriş kartı son girişin tarihini göstermek için
/// izler; tam liste DiaryScreen'de. Kayıt POST sonrası invalidate edilir.
final diaryProvider =
    FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final profile = ref.watch(profileProvider).value;
  if (profile == null || profile['onboardingCompleted'] != true) {
    return const [];
  }
  final dio = ref.watch(apiProvider);
  final response = await dio.get('/api/v1/account/diary');
  final data = Map<String, dynamic>.from(response.data['data']);
  return [
    for (final e in (data['entries'] as List? ?? const []))
      Map<String, dynamic>.from(e as Map),
  ];
});

/// Kişisel sinyaller (R2-S1): "Rytho bugün senin için fark etti" kartları.
///
/// HER katmana açık: başlık cümleleri sunucuda ŞABLONLA (LLM'siz) kurulur,
/// abonede ayrıca tek cümlelik yorum ("insight") gelir. Doğum verisi yoksa
/// sunucu hata değil boş liste döner; ekran bölümü sessizce gizler — ana
/// ekran yeni kullanıcıya hata göstermez.
final signalsProvider =
    FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final profile = ref.watch(profileProvider).value;
  if (profile == null || profile['onboardingCompleted'] != true) {
    return const [];
  }
  final dio = ref.watch(apiProvider);
  final response = await dio.get('/api/v1/reports/signals');
  final data = Map<String, dynamic>.from(response.data['data']);
  return [
    for (final s in (data['signals'] as List? ?? const []))
      Map<String, dynamic>.from(s as Map),
  ];
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

/// Doğum Heksagramı — Rytho+ (Revize İ5). Kalıcı kimlik katmanı: doğum
/// anındaki Güneş boylamının 64 kapı çarkındaki yeri + Rytho okuması.
final birthHexagramProvider =
    FutureProvider<Map<String, dynamic>?>((ref) async {
  if (!_hasPlus(ref)) return null;
  final profile = ref.watch(profileProvider).value;
  if (profile == null || profile['onboardingCompleted'] != true) return null;
  final dio = ref.watch(apiProvider);
  final response = await dio.post('/api/v1/reports/birth-hexagram',
      data: birthPayload(profile));
  Analytics.reportGenerated('birth_hexagram');
  return Map<String, dynamic>.from(response.data['data']);
});

/// Yıl Haritası — Rytho+ (T5). Aktif güneş dönüşü + LLM yıl okuması.
/// Sunucu SR yılı boyunca aynı raporu önbellekten servis eder.
final solarReturnProvider =
    FutureProvider<Map<String, dynamic>?>((ref) async {
  if (!_hasPlus(ref)) return null;
  final profile = ref.watch(profileProvider).value;
  if (profile == null || profile['onboardingCompleted'] != true) return null;
  final dio = ref.watch(apiProvider);
  final response = await dio.post('/api/v1/reports/solar-return',
      data: birthPayload(profile));
  Analytics.reportGenerated('solar_return');
  return Map<String, dynamic>.from(response.data['data']);
});

/// İç Takvim — Rytho+ (T5). İki uç paralel: progresyon okuması (LLM,
/// jetonlu) + 30 günlük ham transit takvimi (jetonsuz; doğum verisi
/// PROFİLDEN okunur, gövde yok).
final innerCalendarProvider =
    FutureProvider<Map<String, dynamic>?>((ref) async {
  if (!_hasPlus(ref)) return null;
  final profile = ref.watch(profileProvider).value;
  if (profile == null || profile['onboardingCompleted'] != true) return null;
  final dio = ref.watch(apiProvider);
  final sonuclar = await Future.wait([
    dio.post('/api/v1/reports/progressions', data: birthPayload(profile)),
    dio.get('/api/v1/astrology/transit-calendar'),
  ]);
  Analytics.reportGenerated('progressions');
  return {
    'progressions':
        Map<String, dynamic>.from(sonuclar[0].data['data']),
    'calendar': Map<String, dynamic>.from(sonuclar[1].data['data']),
  };
});
