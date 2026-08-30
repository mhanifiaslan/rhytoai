/// Şartlar/gizlilik kabulünün SUNUCU kaydı — tekrar denenebilir (KT2).
///
/// ## Neden var
///
/// Kabul kaydı (`POST /account/consent`) iki iş görür: KVKK/GDPR
/// clickwrap İSPATI ve 30'luk deneme karşılama jetonunun yüklenmesi.
/// Eskiden yalnız onboarding bitişinde, sessizce yutulan tek bir
/// çağrıydı — bir ağ hıçkırığı hem ispatı hem jetonu KALICI olarak
/// kaybettiriyordu. Artık başarı cihazda bayrakla işaretlenir; bayrak
/// yoksa her uygulama açılışında bir kez daha denenir. Uç sunucuda
/// idempotent (jeton defterle tek sefer), bu yüzden tekrar zararsız.
library;

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart' show debugPrint;
import 'package:shared_preferences/shared_preferences.dart';

/// Kabul edilen şartlar sürümü — backend `TERMS_CONSENT_VERSION` ile
/// elle senkron (legal_texts güncellenince ikisi birlikte artar).
const int kTermsConsentVersion = 1;

String get _bayrak => 'consent-recorded-v$kTermsConsentVersion';

/// Kabul kaydını garantiye alır; başarı bir kez işaretlenir.
/// Hata İSTEĞİ DÜŞÜRMEZ — bir sonraki açılış yeniden dener.
Future<void> ensureConsentRecorded(Dio dio) async {
  final prefs = await SharedPreferences.getInstance();
  if (prefs.getBool(_bayrak) ?? false) return;
  try {
    await dio.post('/api/v1/account/consent',
        data: {'version': kTermsConsentVersion});
    await prefs.setBool(_bayrak, true);
  } catch (e) {
    debugPrint('Kabul kaydı ertelendi (sonraki açılışta denenecek): $e');
  }
}
