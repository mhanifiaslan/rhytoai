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
///
/// Varsayılan panele HİZALI (M1): eski varsayılan 'rytho_plus' idi ve
/// dart-define'sız her derleme (CI, düz `flutter build`) sessizce yanlış
/// yetkiye bakıyordu — panel 'RhytoAI Pro'. Tek gerçek panel kimliğidir.
const String kPlusEntitlement = String.fromEnvironment(
    'RYTHO_PLUS_ENTITLEMENT',
    defaultValue: 'RhytoAI Pro');

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
///
/// Burada **kullanıcı bağlanmaz**: uygulama açılırken Firebase oturumu henüz
/// geri yüklenmemiş olabilir ve `currentUser` null döner. Kimlik bağlama
/// [billingIdentityProvider] ile oturum akışına bağlıdır.
Future<void> initBilling() async {
  if (!billingConfigured) return;
  try {
    final key = defaultTargetPlatform == TargetPlatform.iOS
        ? kRevenueCatIosKey
        : kRevenueCatAndroidKey;
    if (key.isEmpty) return;

    await Purchases.setLogLevel(LogLevel.warn);
    await Purchases.configure(PurchasesConfiguration(key));
  } catch (e) {
    debugPrint('RevenueCat başlatılamadı: $e');
  }
}

/// RevenueCat kimliğini Firebase oturumuna bağlar.
///
/// **Bu bağlama olmadan satın alma kaybolur.** RevenueCat oturum açılmamışsa
/// anonim bir kimlik (`$RCAnonymousID:...`) üretir ve webhook sunucuya o
/// kimlikle gelir; sunucu aboneliği o dokümana yazar, kullanıcının Firebase
/// uid'i altında hiçbir şey olmaz. Sonuç: ödeme başarılı görünür ama kilitli
/// ekran açılmaz ve paywall tekrar tekrar gelir.
///
/// Eskiden bağlama yalnızca açılışta bir kez deneniyordu ve Firebase oturumu
/// asenkron geri yüklendiği için çoğu açılışta `currentUser` henüz null
/// oluyordu. Bu yüzden kimlik artık oturum AKIŞINA bağlı.
final billingIdentityProvider = Provider<void>((ref) {
  if (!billingConfigured) return;

  ref.listen<AsyncValue<User?>>(authStateProvider, (previous, next) {
    final uid = next.value?.uid;
    final oncekiUid = previous?.value?.uid;
    if (uid == oncekiUid) return;

    Future<void>(() async {
      try {
        if (uid == null) {
          await Purchases.logOut();
        } else {
          await Purchases.logIn(uid);
        }
      } catch (e) {
        debugPrint('RevenueCat kimliği bağlanamadı: $e');
      }
      ref.invalidate(subscriptionProvider);
    });
  }, fireImmediately: true);
});

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
  } catch (_) {
    // Durum okunamadıysa ücretsiz varsay; sunucu zaten uçları koruyor.
    //
    // Yakalama BİLEREK geniş (`on DioException` değil): bu sağlayıcı hata
    // durumuna DÜŞMEMELİ. Riverpod hatalı bir sağlayıcıyı yeniden deniyor ve
    // `.future` o süre boyunca tamamlanmıyor; satın alma sonrası yoklama da
    // orada asılı kalıyordu.
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

/// Satın alma. Başarılıysa sunucu yetkiyi görene kadar bekler.
///
/// Yetki sunucuya **webhook üzerinden** işleniyor: satın almanın bitmesiyle
/// `/billing/status` uçlarının "aktif" demesi arasında saniyeler olabilir.
/// Tek seferlik `invalidate` bu yarışı kaybediyordu — kullanıcı ödeme yapıyor,
/// ekran kapanıyor, kilitli içeriğe dokunuyor ve sunucu henüz haberdar
/// olmadığı için 402 dönüp paywall yeniden açılıyordu.
///
/// Bu yüzden durum kısa aralıklarla birkaç kez okunur. Süre dolarsa yine de
/// `true` döneriz: satın alma cihazda gerçekleşti, gecikme sunucu tarafındadır
/// ve kullanıcıyı ödeme ekranına geri göndermek yanlış olur.
Future<bool> purchasePackage(WidgetRef ref, Package package) async {
  final result = await Purchases.purchase(PurchaseParams.package(package));
  final active =
      result.customerInfo.entitlements.active.containsKey(kPlusEntitlement);
  if (!active) return false;

  await _waitForServerEntitlement(ref);
  return true;
}

/// Tek bir durum yoklamasının üst sınırı.
///
/// Dio'nun alım zaman aşımı 120 saniye; sınırsız bırakılırsa beş yoklama en
/// kötü hâlde on dakika sürebiliyordu. Kullanıcının gördüğü şey "ödeme
/// adımını geçemiyorum" oluyor.
const Duration _kYoklamaSiniri = Duration(seconds: 6);

/// Sunucuyu bekleme bütçesinin tamamı.
const Duration _kBeklemeButcesi = Duration(seconds: 15);

/// Sunucu aboneliği görene kadar bekler — sınırlı bir bütçeyle.
///
/// Süre dolarsa sessizce çıkılır: satın alma cihazda gerçekleşti, gecikme
/// sunucu tarafında ve kullanıcıyı ödeme ekranında tutmak yanlış olur.
Future<void> _waitForServerEntitlement(WidgetRef ref) async {
  const gecikmeler = [
    Duration(milliseconds: 400),
    Duration(seconds: 1),
    Duration(seconds: 2),
    Duration(seconds: 3),
    Duration(seconds: 4),
  ];
  final bitis = DateTime.now().add(_kBeklemeButcesi);
  for (final gecikme in gecikmeler) {
    if (DateTime.now().isAfter(bitis)) break;
    ref.invalidate(subscriptionProvider);
    try {
      final durum =
          await ref.read(subscriptionProvider.future).timeout(_kYoklamaSiniri);
      if (durum.active) return;
    } catch (_) {
      // Yoklama düşerse beklemeyi sürdür; bu bir satın alma hatası değil.
    }
    await Future<void>.delayed(gecikme);
  }
  ref.invalidate(subscriptionProvider);
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
  if (active) {
    await _waitForServerEntitlement(ref);
  } else {
    ref.invalidate(subscriptionProvider);
  }
  return active;
}
