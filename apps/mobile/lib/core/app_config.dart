/// Açılış yapılandırması — zorunlu güncelleme kapısı (F3).
///
/// Giriş ekranından ÖNCE, kimliksiz `/api/v1/config/app` ucundan okunur.
/// FELSEFE FAIL-OPEN: sunucuya ulaşılamazsa, yanıt bozuksa ya da sürüm
/// okunamazsa kapı AÇIK kalır — ağı kesik kullanıcıyı güncelleme ekranına
/// kilitlemek, kapının önleyeceği her sorundan daha kötü olurdu
/// (device_claim.dart'taki "nazik ön kapı" ilkesiyle aynı).
library;

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:package_info_plus/package_info_plus.dart';

import 'api.dart' show kApiBaseUrl;

/// true = bu derleme sunucunun istediği asgari sürümün ALTINDA;
/// uygulama ForceUpdateScreen'e kilitlenir.
final updateRequiredProvider = FutureProvider<bool>((ref) async {
  try {
    // apiProvider bilerek KULLANILMIYOR: o kimlik/dil interceptor'larıyla
    // oturuma bağlı; bu istekse oturumdan önce ve tamamen anonim.
    final dio = Dio(BaseOptions(
      baseUrl: kApiBaseUrl,
      connectTimeout: const Duration(seconds: 8),
      receiveTimeout: const Duration(seconds: 8),
    ));
    final yanit = await dio.get('/api/v1/config/app');
    final minBuild =
        (yanit.data['data']['min_build'] as num?)?.toInt() ?? 0;
    if (minBuild <= 0) return false;

    final paket = await PackageInfo.fromPlatform();
    final buBuild = int.tryParse(paket.buildNumber) ?? 0;
    // buildNumber okunamazsa (0) kilitleme — fail-open.
    if (buBuild == 0) return false;
    return buBuild < minBuild;
  } catch (e) {
    debugPrint('Sürüm kapısı atlandı: $e');
    return false;
  }
});
