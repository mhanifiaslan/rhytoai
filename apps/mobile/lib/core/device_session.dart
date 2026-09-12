/// Tek cihaz kilidi — istemci yarısı (TC-turu, 1.15.1+36).
///
/// Hakem SUNUCU: her korumalı istek, Firebase ID token'ındaki `auth_time`'a
/// bakıp kendi başına karar verir ("son giriş kazanır"). İstemcinin üç işi
/// kalır:
///
/// * 409 + `X-Device-Conflict` gelince kimseyi oturumdan ATMADAN kapıyı
///   kapatmak ([deviceConflictProvider] → `_Gate` `DeviceConflictScreen`);
/// * "Bu cihazda kullan" deyince KİMLİKLİ `POST /device/claim`
///   ([claimThisDevice]);
/// * çıkışta kilidi bırakmak ([releaseThisDevice]) ki "eski cihazdan çıkış
///   yeni cihazı açar" sözü gerçek olsun.
///
/// Eski akış (`device_claim.dart`, silindi) açılışta devralma sorusu soruyor
/// ve 409'da ANINDA `signOut` yapıyordu. Soru `SkyScreen`'in ilk
/// `POST /reports/daily`'siyle yarışıp kaybediyordu: 409 oturumu kapatıyor,
/// ardından "Bu cihazda kullan" kimliksiz gidip 401 yiyordu (B4: "soru hiç
/// çıkmıyor"). Sunucu hakemken o makinenin hiçbir parçası gerekmiyor;
/// yarışın kaynağıydı.
library;

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/legacy.dart'
    show StateController, StateProvider;

import 'api.dart' show kDeviceConflictStatus;

/// 409'un "bu bizim kilidimiz" işareti (`core/device.py`); değeri `1`.
const String kDeviceConflictHeader = 'x-device-conflict';

/// Kilidi elinde tutan diğer cihazın platformu (`android`, `iOS`...).
const String kDeviceOtherPlatformHeader = 'x-device-other-platform';

/// Diğer cihazın kilidi aldığı an — ISO-8601, UTC.
const String kDeviceClaimedAtHeader = 'x-device-claimed-at';

/// BU cihazın platformu — her istekle gider (`apiProvider`). Sunucu
/// otomatik devralmada kayda yazar; kaybeden cihazın kapı ekranı böylece
/// DOĞRU cihazı söyler ("iOS cihazında"), kendi platformunu değil. Başlık
/// yoksa sunucu platformu bilinmiyor sayar (ekranda "—") — eski değeri
/// koruyup yanlış cihaz adı söylemez.
const String kDevicePlatformHeader = 'X-Device-Platform';

/// Sunucuya bildirilen platform adı (`android`, `iOS`...): istek başlığı ve
/// `POST /claim` gövdesi aynı kaynaktan.
String devicePlatform() => defaultTargetPlatform.name;

/// Çıkıştaki bırakma isteğinin tavanı: çıkış bundan uzun BEKLETİLMEZ.
const Duration kDeviceReleaseTimeout = Duration(seconds: 3);

/// Sunucunun çakışma yanıtındaki "diğer cihaz" bilgisi.
///
/// Değerler yanıtın BAŞLIKLARINDAN gelir, gövdeden değil: `detail` alanı
/// kullanıcıya olduğu gibi gösterilen düz metin, oraya yapı gömülmez —
/// 402'deki `X-Paywall-Reason` kararıyla aynı (bkz. api.dart).
@immutable
class DeviceConflict {
  const DeviceConflict({this.platform, this.claimedAt});

  /// Boş/eksik başlık → null; bozuk tarih → null. Ekran "—" basar; bilgi
  /// yok diye kapı açık kalmaz.
  factory DeviceConflict.fromHeaders(Headers headers) {
    final platform = headers.value(kDeviceOtherPlatformHeader)?.trim();
    final zaman = headers.value(kDeviceClaimedAtHeader)?.trim();
    return DeviceConflict(
      platform: (platform == null || platform.isEmpty) ? null : platform,
      claimedAt: (zaman == null || zaman.isEmpty) ? null : _utc(zaman),
    );
  }

  /// Diğer cihazın platformu; bilinmiyorsa null.
  final String? platform;

  /// Diğer cihazın kilidi aldığı an (UTC); bilinmiyorsa null.
  final DateTime? claimedAt;

  /// Sunucu UTC yazar; saat dilimi eki yoksa da UTC sayılır — yerel sanmak
  /// ekranda saati kaydırırdı.
  static DateTime? _utc(String iso) {
    final t = DateTime.tryParse(iso);
    if (t == null) return null;
    if (t.isUtc) return t;
    return DateTime.utc(t.year, t.month, t.day, t.hour, t.minute, t.second,
        t.millisecond, t.microsecond);
  }

  @override
  bool operator ==(Object other) =>
      other is DeviceConflict &&
      other.platform == platform &&
      other.claimedAt == claimedAt;

  @override
  int get hashCode => Object.hash(platform, claimedAt);
}

/// Kapının tek sorusu: bu oturumun bir isteği 409 aldı mı? (`_Gate` izler;
/// dolu → `DeviceConflictScreen`, kabuk/onboarding yerine.)
///
/// Düşürenler: devralma başarısı (`DeviceConflictScreen`) ve çıkış
/// (`signOutEverywhere`) — çıkışta düşmese bir sonraki giriş aynı ekrana
/// düşerdi.
final deviceConflictProvider = StateProvider<DeviceConflict?>((_) => null);

/// Kapıyı kapatan yazıcı — `apiProvider` 409 kancasını buna bağlar.
///
/// İLK çakışma kazanır: kapı kapanınca uçuştaki diğer istekler de 409 alır
/// (soğuk açılışta 4-6 sağlayıcı paralel ateşlenir); her biri bayrağı
/// yeniden yazsa ekran boşuna yeniden kurulur ve ilk `claimedAt` ezilirdi.
void noteDeviceConflict(
    StateController<DeviceConflict?> kapi, DeviceConflict cakisma) {
  if (kapi.state != null) return;
  kapi.state = cakisma;
}

/// 409 + `X-Device-Conflict: 1` → [onConflict] (başlıklardan ayrıştırılmış
/// çakışma); hata olduğu gibi devam eder ki çağıran sağlayıcı da düşsün —
/// kapı açılınca ekranda yarım veri kalmasın.
///
/// Oturuma DOKUNMAZ — bu dosya Firebase'i hiç bilmez (bekçi test bunu
/// sabitler). Eski hâli burada oturumu kapatıyordu ve devralma yolu tam bu
/// yüzden kilitleniyordu: "Bu cihazda kullan" kimliksiz gidiyor, 401
/// yiyordu. Karar `_Gate`'te, oturum açıkken verilir.
/// Kanca fırlatsa da hata çağırana ulaşır (426 deseni, app_config.dart).
Interceptor deviceConflictInterceptor(
        void Function(DeviceConflict cakisma) onConflict) =>
    InterceptorsWrapper(
      onError: (error, handler) {
        final yanit = error.response;
        if (yanit != null &&
            yanit.statusCode == kDeviceConflictStatus &&
            yanit.headers.value(kDeviceConflictHeader) == '1') {
          try {
            onConflict(DeviceConflict.fromHeaders(yanit.headers));
          } catch (e) {
            debugPrint('Cihaz çakışması kapıya yazılamadı: $e');
          }
        }
        handler.next(error);
      },
    );

/// Kimlikli devralma: `POST /device/claim {platform}`.
///
/// Sunucu DÜRÜST `claimed` döner — yazılamadıysa (Firestore düştü, istemci
/// yok) false; çağıran buna göre kullanıcıya söyler. Ağ/HTTP hatası
/// fırlatır; ekran yakalar. Platform, diğer cihazın çakışma ekranında
/// "{platform} cihazında" diye görünür.
Future<bool> claimThisDevice(Dio dio) async {
  final yanit = await dio.post('/api/v1/device/claim', data: {
    'platform': devicePlatform(),
  });
  final veri = yanit.data;
  return veri is Map && veri['claimed'] == true;
}

/// Kilidi bırakır: `DELETE /device/claim` (sunucu yalnız sahipse siler).
///
/// Çıkış yolunda, Firebase çıkışından ÖNCE çağrılır — Authorization
/// `currentUser`'dan geliyor; sonra çağrılsa 401 yer ve eski cihaz kilidi
/// elinde tutardı (B4'ün "eski cihazdan çıkış yeni cihazı açmıyor" yarısı).
/// Çıkışı geciktirmez: [timeout] tavanı (üretimde [kDeviceReleaseTimeout]),
/// her hata yutulur — kilit sunucuda `auth_time` ile zaten çözülür, burası
/// nezaket. [timeout] test dikişidir.
Future<void> releaseThisDevice(Dio dio,
    {Duration timeout = kDeviceReleaseTimeout}) async {
  try {
    await dio.delete('/api/v1/device/claim').timeout(timeout);
  } catch (e) {
    debugPrint('Cihaz kilidi bırakılamadı (çıkış sürer): $e');
  }
}
