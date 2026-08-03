/// Cihaz devralma akışı — girişten sonra bir kez sorulur.
///
/// WhatsApp modeli: abonelik tek cihazda çalışır; kullanıcı yeni bir cihazda
/// oturum açtığında "bu cihazda kullan" onayı verir, sunucu kaydı devreder
/// ve ESKİ cihaz bir sonraki isteğinde 409 alıp oturumdan düşer.
///
/// Onay yalnızca gerektiğinde sorulur: kullanıcı abone + sunucuda kayıtlı
/// cihaz var + kayıtlı cihaz bu değil. Ücretsiz kullanıcıya bu akış hiç
/// görünmez. Vazgeçen kullanıcı oturumdan çıkarılır — kilidin anlamı bu;
/// "hem vazgeç hem kullan" diye bir durum yok, aboneli uçlar zaten 409
/// dönerdi ve kullanıcı yarı çalışan bir uygulamada bırakılmış olurdu.
library;

import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../l10n/app_localizations.dart';
import 'api.dart';
import 'subscription.dart' show subscriptionProvider;

bool _soruldu = false;

/// Oturum başına bir kez: gerekiyorsa devralma onayını gösterir.
///
/// [context] gösterim anında hâlâ ekrandaysa kullanılır; kapatılmışsa akış
/// sessizce vazgeçer (bir sonraki açılışta yeniden denenir).
Future<void> maybeConfirmDeviceTakeover(
    BuildContext context, WidgetRef ref) async {
  if (_soruldu) return;
  _soruldu = true;

  try {
    final abone = ref.read(subscriptionProvider).value?.active ?? false;
    if (!abone) return;

    final dio = ref.read(apiProvider);
    final durum = await dio.get('/api/v1/device/status');
    final veri = Map<String, dynamic>.from(durum.data as Map);
    if (veri['claimed'] != true || veri['this_device'] == true) return;

    if (!context.mounted) {
      _soruldu = false; // ekran kapandıysa sonraki açılışta yeniden dene
      return;
    }
    final l10n = AppLocalizations.of(context);
    final onay = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (c) => AlertDialog(
        title: Text(l10n.deviceTakeoverTitle),
        content: Text(l10n.deviceTakeoverBody),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(c, false),
            child: Text(l10n.cancel),
          ),
          TextButton(
            onPressed: () => Navigator.pop(c, true),
            child: Text(l10n.deviceTakeoverConfirm),
          ),
        ],
      ),
    );

    if (onay == true) {
      await dio.post('/api/v1/device/claim', data: {
        'platform': defaultTargetPlatform.name,
      });
    } else {
      // Vazgeçti: bu cihazda abonelik kullanılamaz; yarı çalışan bir
      // uygulama bırakmak yerine oturum kapatılır.
      await FirebaseAuth.instance.signOut();
    }
  } catch (e) {
    // Durum sorgusu düşerse kullanıcıyı engelleme: kilit sunucuda zaten
    // uygulanıyor, bu akış yalnızca nazik bir ön kapı.
    debugPrint('Cihaz devralma akışı atlandı: $e');
  }
}

/// Test/oturum sıfırlama yardımcıcı.
@visibleForTesting
void resetDeviceTakeoverPrompt() => _soruldu = false;
