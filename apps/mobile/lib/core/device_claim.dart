/// Cihaz devralma akışı — girişten sonra bir kez sorulur.
///
/// WhatsApp modeli: abonelik tek cihazda çalışır; kullanıcı yeni bir cihazda
/// oturum açtığında "bu cihazda kullan" onayı verir, sunucu kaydı devreder
/// ve ESKİ cihaz bir sonraki isteğinde 409 alıp oturumdan düşer.
///
/// Onay yalnızca gerektiğinde sorulur: sunucuda kayıtlı cihaz var + kayıtlı
/// cihaz bu değil. Ücretsiz kullanıcıda sunucu `claimed:false` döndüğü için
/// akış hiç görünmez. Vazgeçen kullanıcı oturumdan çıkarılır — kilidin
/// anlamı bu; "hem vazgeç hem kullan" diye bir durum yok, aboneli uçlar
/// zaten 409 dönerdi ve kullanıcı yarı çalışan bir uygulamada bırakılırdı.
library;

import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../l10n/app_localizations.dart';
import 'api.dart';

/// "Oturum başına bir kez"in bayrağı.
///
/// İç test bulgusu V1 (2026-08-12): bu bayrak eskiden fonksiyonun EN BAŞINDA
/// yakılıyordu ve hiçbir üretim yolu sıfırlamıyordu. Abonelik durumu daha
/// yüklenmeden erken çıkılınca soru hiç gösterilmediği hâlde "soruldu"
/// sayılıyor, 409 sonrası yeniden girişte de bir daha denenmiyordu —
/// kullanıcı çakışma ekranıyla sonsuz döngüye giriyordu. Kurallar artık:
/// bayrak yalnız dialog GERÇEKTEN gösterilince yanar; oturum değişiminde
/// ve 409-signOut yolunda sıfırlanır.
bool _soruldu = false;

/// Oturum başına bir kez: gerekiyorsa devralma onayını gösterir.
///
/// [context] gösterim anında hâlâ ekrandaysa kullanılır; kapatılmışsa akış
/// sessizce vazgeçer (bir sonraki açılışta yeniden denenir).
Future<void> maybeConfirmDeviceTakeover(
    BuildContext context, WidgetRef ref) async {
  if (_soruldu) return;

  try {
    // Abonelik ön-kontrolü BİLEREK yok: yeni girişte subscriptionProvider
    // henüz yüklenmemiş oluyor ve senkron okuma yanlış "abone değil"
    // veriyordu (V1). Tek gerçek sunucu: ücretsiz kullanıcıda /device/status
    // zaten claimed:false döner ve akış görünmez.
    final dio = ref.read(apiProvider);
    final durum = await dio.get('/api/v1/device/status');
    final veri = Map<String, dynamic>.from(durum.data as Map);
    if (veri['claimed'] != true || veri['this_device'] == true) return;

    if (!context.mounted) return; // sonraki açılışta yeniden denenir
    _soruldu = true; // dialog gerçekten gösteriliyor — ancak şimdi yak
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

/// Oturum değişiminde/çıkışta çağrılır: soru bir SONRAKİ oturumda yeniden
/// sorulabilsin (bkz. api.dart 409 yolu ve main.dart auth dinleyicisi).
void resetDeviceTakeoverPrompt() => _soruldu = false;
