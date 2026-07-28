import 'package:dio/dio.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:purchases_flutter/purchases_flutter.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'api.dart';
import 'providers.dart';

/// Rytho+ aboneliği.
///
/// İki kaynak vardır ve **sunucu esastır**: RevenueCat SDK'sı cihazda hızlı
/// yanıt verir ama asıl doğruluk `/api/v1/billing/status` ucundan gelir.
/// Sunucu bu bilgiyi yalnızca RevenueCat webhook'undan yazar; istemcinin
/// abonelik kaydına yazma izni yoktur (bkz. infra/firestore.rules).
///
/// Böylece istemci tarafında kurcalayarak ücretli içerik açılamaz: uçlar
/// kilitliyse sunucu 402 döner, arayüz ne gösterirse göstersin.

/// RevenueCat genel API anahtarları.
///
/// Kaynağa gömülmez; çalıştırırken geçilir:
/// `flutter run --dart-define-from-file=dart_defines.local.json`
/// (örnek için bkz. `dart_defines.example.json`).
///
/// Tanımlı değilse SDK hiç başlatılmaz ve satın alma devre dışı kalır —
/// uygulamanın geri kalanı ücretsiz katmanla normal çalışır.
///
/// UYARI: `test_` önekli anahtarlar RevenueCat Test Store'a aittir ve satın
/// almaları **simüle eder**. Yayın öncesi gerçek mağaza anahtarlarıyla
/// (`appl_...` / `goog_...`) değiştirilmelidir.
const String kRevenueCatAndroidKey =
    String.fromEnvironment('REVENUECAT_ANDROID_KEY');
const String kRevenueCatIosKey = String.fromEnvironment('REVENUECAT_IOS_KEY');

/// RevenueCat panelinde tanımlı yetki (entitlement) kimliği.
/// Paneldeki adla birebir aynı olmalı; farklıysa satın alma sonrası
/// `entitlements.active` boş görünür ve abonelik açılmaz.
const String kPlusEntitlement =
    String.fromEnvironment('RYTHO_PLUS_ENTITLEMENT', defaultValue: 'rytho_plus');

bool get billingConfigured =>
    kRevenueCatAndroidKey.isNotEmpty || kRevenueCatIosKey.isNotEmpty;

class SubscriptionStatus {
  const SubscriptionStatus({
    required this.active,
    this.productId,
    this.expiresAt,
    this.willRenew,
    this.isTrial,
  });

  final bool active;
  final String? productId;
  final DateTime? expiresAt;
  final bool? willRenew;
  final bool? isTrial;

  static const none = SubscriptionStatus(active: false);

  factory SubscriptionStatus.fromJson(Map<String, dynamic> json) {
    final raw = json['expires_at'] as String?;
    return SubscriptionStatus(
      active: json['active'] == true,
      productId: json['product_id'] as String?,
      expiresAt: raw == null ? null : DateTime.tryParse(raw),
      willRenew: json['will_renew'] as bool?,
      isTrial: json['is_trial'] as bool?,
    );
  }
}

/// RevenueCat SDK kurulumu. Anahtar yoksa sessizce atlanır.
Future<void> initBilling() async {
  if (!billingConfigured) return;
  try {
    final key = defaultTargetPlatform == TargetPlatform.iOS
        ? kRevenueCatIosKey
        : kRevenueCatAndroidKey;
    if (key.isEmpty) return;

    await Purchases.setLogLevel(LogLevel.warn);
    await Purchases.configure(PurchasesConfiguration(key));

    // Satın almanın doğru kullanıcıya bağlanması için RevenueCat'in
    // app_user_id'si Firebase uid olmalı; webhook da bu kimlikle geliyor.
    final uid = FirebaseAuth.instance.currentUser?.uid;
    if (uid != null) await Purchases.logIn(uid);
  } catch (e) {
    debugPrint('RevenueCat başlatılamadı: $e');
  }
}

/// Oturum açan kullanıcıyı RevenueCat'e bağlar (giriş sonrası çağrılır).
Future<void> syncBillingUser(String uid) async {
  if (!billingConfigured) return;
  try {
    await Purchases.logIn(uid);
  } catch (e) {
    debugPrint('RevenueCat kullanıcı eşleştirilemedi: $e');
  }
}

/// Sunucunun gördüğü abonelik durumu — arayüz kilitleri buna bakar.
final subscriptionProvider =
    FutureProvider<SubscriptionStatus>((ref) async {
  final user = ref.watch(authStateProvider).value;
  if (user == null) return SubscriptionStatus.none;

  final dio = ref.watch(apiProvider);
  try {
    final response = await dio.get('/api/v1/billing/status');
    return SubscriptionStatus.fromJson(
        Map<String, dynamic>.from(response.data));
  } on DioException {
    // Durum okunamadıysa ücretsiz varsay; sunucu zaten uçları koruyor.
    return SubscriptionStatus.none;
  }
});

/// Kullanıcıya sunulacak plan tipleri.
///
/// RevenueCat teklifinde başka paketler tanımlı olsa da uygulama yalnızca
/// buradakileri gösterir; böylece plan yapısı panele dokunmadan tek yerden
/// değişir. Karar: **sadece aylık**.
const List<PackageType> kOfferedPackageTypes = [PackageType.monthly];

/// Satın alınabilir paketler.
final offeringsProvider = FutureProvider<List<Package>>((ref) async {
  if (!billingConfigured) return const [];
  try {
    final offerings = await Purchases.getOfferings();
    final all = offerings.current?.availablePackages ?? const <Package>[];
    final filtered = all
        .where((p) => kOfferedPackageTypes.contains(p.packageType))
        .toList();
    // Teklifte hiç eşleşme yoksa kullanıcıyı boş ekranla baş başa bırakma.
    return filtered.isEmpty ? all : filtered;
  } catch (e) {
    debugPrint('Paketler alınamadı: $e');
    return const [];
  }
});

/// Satın alma. Başarılıysa sunucu durumunu tazeler.
///
/// Yetki webhook üzerinden sunucuya işlendiği için satın alma ile sunucunun
/// haberdar olması arasında kısa bir gecikme olabilir; bu yüzden durum
/// sağlayıcısı geçersiz kılınır ve bir kez daha okunur.
Future<bool> purchasePackage(WidgetRef ref, Package package) async {
  final result = await Purchases.purchase(PurchaseParams.package(package));
  final active =
      result.customerInfo.entitlements.active.containsKey(kPlusEntitlement);
  if (active) {
    ref.invalidate(subscriptionProvider);
  }
  return active;
}

/// Onboarding sonrası paywall'ın bir kez gösterilip gösterilmediği.
const String _kIntroPaywallKey = 'introPaywallShown';

/// Tanıtım paywall'ı daha önce gösterildi mi?
Future<bool> introPaywallShown() async {
  try {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_kIntroPaywallKey) ?? false;
  } catch (_) {
    // Okunamazsa göstermemiş gibi davranmak, kullanıcıyı her açılışta
    // paywall'la karşılaştırma riskini doğurur; güvenli taraf "gösterildi".
    return true;
  }
}

Future<void> markIntroPaywallShown() async {
  try {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kIntroPaywallKey, true);
  } catch (_) {}
}

/// Satın alımları geri yükle (mağaza kuralı: bu seçenek sunulmak zorunda).
Future<bool> restorePurchases(WidgetRef ref) async {
  final info = await Purchases.restorePurchases();
  final active = info.entitlements.active.containsKey(kPlusEntitlement);
  ref.invalidate(subscriptionProvider);
  return active;
}
