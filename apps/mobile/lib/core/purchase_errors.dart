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

String storeErrorText(PlatformException e, AppLocalizations l10n) {
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
      if (!kDebugMode) {
        FirebaseCrashlytics.instance.recordError(
            'store-purchase: ${e.code}: ${e.message}', StackTrace.current,
            fatal: false);
      }
      return l10n.purchaseFailed;
  }
}
