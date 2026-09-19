/// Mağaza (RevenueCat/Play) hatalarının kullanıcı diline çevirisi (G-turu).
///
/// İç test bulgusu: paywall bilinmeyen mağaza hatasında `e.message`'ı ham
/// basıyordu — kullanıcı Türkçe arayüzde "This product is already active
/// for the user." gördü. Kural: ekrana YALNIZ l10n metni çıkar; bilinmeyen
/// kodlar Crashlytics'e gider (kaybolmaz ama kullanıcıyı İngilizceyle baş
/// başa bırakmaz).
library;

import 'package:firebase_crashlytics/firebase_crashlytics.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart' show PlatformException;
import 'package:purchases_flutter/purchases_flutter.dart';

import '../l10n/app_localizations.dart';
import 'api.dart' show friendlyError;

/// Bilinmeyen mağaza kodunu Crashlytics'e yazan varsayılan kanal.
void varsayilanMagazaHatasiKaydedici(String mesaj) {
  if (!kDebugMode) {
    FirebaseCrashlytics.instance
        .recordError(mesaj, StackTrace.current, fatal: false);
  }
}

/// Kayıt kanalı — test dikişi.
@visibleForTesting
void Function(String mesaj) magazaHatasiKaydedici =
    varsayilanMagazaHatasiKaydedici;

/// ÇİZİM yolunda bir kez bildirilmiş kodlar (bkz. [magazaVeyaAgHatasi]).
final Set<String> _cizimdeBildirilenKodlar = <String>{};

/// Testler arası sızmayı önler; kanalı da varsayılana döndürür.
@visibleForTesting
void magazaHataKaydiniSifirla() {
  _cizimdeBildirilenKodlar.clear();
  magazaHatasiKaydedici = varsayilanMagazaHatasiKaydedici;
}

/// Mağaza YA DA ağ hatasının kullanıcı diline çevirisi — paywall ile jeton
/// mağazasının hata dalının TEK kapısı.
///
/// Tek kapı şart: `friendlyError` PlatformException'ı tanımıyor, yani ayrı
/// ayrı çevirirsek aynı ağ hatası paywall'da doğru, jeton mağazasında
/// "beklenmeyen sorun" görünürdü.
///
/// Telemetri KOD BAŞINA BİR KEZ, ama YALNIZ BURADA. Bu fonksiyon `build()`
/// içinden çağrılıyor ve hata kartı ekranda durduğu SÜRECE her yeniden çizim
/// yeni bir Crashlytics kaydı üretirdi. Süzgeç [storeErrorText]in İÇİNE
/// KONAMAZ: satın alma akışı (paywall `_buy`/`_restore`, jeton mağazası
/// `_buy`) onu doğrudan çağırıyor ve oradaki tekrar sayısı sorunun
/// YAYGINLIĞIDIR — tekilleştirilirse ölçmek istediğimiz şey kaybolur.
String magazaVeyaAgHatasi(Object e, AppLocalizations l10n) {
  if (e is! PlatformException) return friendlyError(e, l10n);
  return storeErrorText(e, l10n, kaydet: _cizimdeBildirilenKodlar.add(e.code));
}

/// [kaydet] yalnız çizim yolunda `false` olabilir (bkz. [magazaVeyaAgHatasi]);
/// satın alma akışı HER denemeyi kaydeder.
String storeErrorText(PlatformException e, AppLocalizations l10n,
    {bool kaydet = true}) {
  switch (PurchasesErrorHelper.getErrorCode(e)) {
    case PurchasesErrorCode.productAlreadyPurchasedError:
      return l10n.purchaseAlreadyOwned;
    case PurchasesErrorCode.productNotAvailableForPurchaseError:
    case PurchasesErrorCode.purchaseInvalidError:
      // Tipik neden: cihazdaki Play hesabı iç test kanalına katılmış hesap
      // değil (Erkan vakası, 2026-08-12) — metin buna yönlendirir.
      return l10n.purchaseItemUnavailable;
    case PurchasesErrorCode.networkError:
    case PurchasesErrorCode.offlineConnectionError:
      return l10n.authNetwork;
    case PurchasesErrorCode.storeProblemError:
    case PurchasesErrorCode.purchaseNotAllowedError:
      return l10n.purchaseStoreProblem;
    default:
      if (kaydet) {
        magazaHatasiKaydedici('store-purchase: ${e.code}: ${e.message}');
      }
      return l10n.purchaseFailed;
  }
}
