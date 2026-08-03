/// Cihaz kimliği — tek cihaz kilidinin istemci yarısı.
///
/// Rastgele üretilmiş 128 bitlik bir değer, SharedPreferences'ta saklanır ve
/// her API isteğine `X-Device-Id` başlığı olarak eklenir (bkz. core/api.dart).
///
/// ## Neden donanım kimliği değil
///
/// Donanım kimlikleri (IMEI, Android ID) izin ve mağaza beyanı gerektirir,
/// gizlilik etiketine "cihaz tanımlayıcısı topluyoruz" satırı ekletir ve
/// kazandırdığı tek şey "uygulama silinip kurulunca kimlik korunur" olurdu —
/// ki o durumda kilidin sıfırlanması zaten kabul edilebilir: kullanıcı kendi
/// cihazında yeniden kurulum yapıyor.
///
/// ## Neden secure storage değil
///
/// Kimlik bir sır değil, bir AYIRICI. Tek geçerli kimlik sunucudaki kayıt;
/// kimliği kopyalamak "devralma"nın ta kendisi ve bunun meşru yolu zaten var
/// (`POST /device/claim`). Şifreli saklamak eklenti bağımlılığı getirir,
/// güvenlik kazandırmaz.
library;

import 'dart:math';

import 'package:shared_preferences/shared_preferences.dart';

const String _kDeviceIdKey = 'rythoDeviceId';

String? _cached;

/// Bu cihazın kalıcı kimliği; ilk çağrıda üretilir.
Future<String> deviceId() async {
  final onbellek = _cached;
  if (onbellek != null) return onbellek;

  try {
    final prefs = await SharedPreferences.getInstance();
    var id = prefs.getString(_kDeviceIdKey);
    if (id == null || id.isEmpty) {
      id = _uret();
      await prefs.setString(_kDeviceIdKey, id);
    }
    _cached = id;
    return id;
  } catch (_) {
    // Depo okunamazsa oturum boyunca sabit bir kimlikle devam et: başlıksız
    // istek kilidi atlar (sunucu eski sürüm sanır) — üretmek her zaman
    // daha doğru.
    return _cached ??= _uret();
  }
}

String _uret() {
  final rasgele = Random.secure();
  final baytlar = List<int>.generate(16, (_) => rasgele.nextInt(256));
  return baytlar.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
}
