import 'package:firebase_analytics/firebase_analytics.dart';
import 'package:flutter/foundation.dart';

/// Basit analytics cephesi — tüm olay adları tek yerde dursun.
///
/// Olaylar arka planda gönderilir; hata olursa uygulama akışını etkilemez.
///
/// **Kural: burada yalnızca var olan akışların olayları durur.** Şema bir
/// dönem kaldırılmış özelliklerin olaylarını taşıdı (gönderi yayınlama,
/// takip, kanal aboneliği, yüz analizi) — hiçbiri tetiklenmiyordu ama
/// konsolda var görünüyor, ölçümü kirletiyordu.
///
/// **Olaylara kişisel veri girmez.** Parametreler yalnızca dar kümeli
/// kategorilerdir (burç, rapor türü, tepki anahtarı); doğum verisi, kullanıcı
/// adı, arkadaş kimliği veya sohbet içeriği hiçbir olayda taşınmaz.
class Analytics {
  Analytics._();

  static Future<void> _log(String name, [Map<String, Object>? params]) async {
    try {
      await FirebaseAnalytics.instance.logEvent(name: name, parameters: params);
    } catch (e) {
      debugPrint('Analytics olayı gönderilemedi ($name): $e');
    }
  }

  // --- Okumalar ---

  /// Rapor üretimi — type: daily | natal | bazi | synastry | dyad
  static void reportGenerated(String type) =>
      _log('report_generated', {'report_type': type});

  /// I Ching çekimi yapıldı — method: coins | yarrow
  static void ichingCast(String method) =>
      _log('iching_cast', {'method': method});

  // --- Abonelik ---
  //
  // Dönüşüm hunisi bu üç olayla ölçülür: paywall kaç kez göründü, kaç kişi
  // satın almaya başladı, kaçı tamamladı. Ortadaki adım olmadan "paywall
  // çalışmıyor" ile "mağaza akışı düşüyor" ayırt edilemez.

  /// Paywall açıldı — reason: intro (ilk değerden sonra) | locked (402)
  static void paywallShown(String reason) =>
      _log('paywall_shown', {'reason': reason});

  /// Kullanıcı satın alma akışını başlattı.
  static void purchaseStarted() => _log('purchase_started');

  /// Satın alma tamamlandı ve yetki açıldı.
  static void purchaseCompleted() => _log('purchase_completed');

  /// Satın alımlar geri yüklendi — found: aktif abonelik bulundu mu.
  static void purchasesRestored({required bool found}) =>
      _log('purchases_restored', {'found': found.toString()});

  // --- Bildirimler ---
  //
  // Bu kategoride retention doğrudan bildirime bağlı; izin oranı ve
  // bildirimden dönüş ölçülmezse bildirim sisteminin işe yarayıp yaramadığı
  // bilinemez.

  /// Sistem bildirim izni sorusunun sonucu.
  static void notificationPermission({required bool granted}) =>
      _log('notification_permission', {'granted': granted.toString()});

  /// Bildirime dokunularak uygulama açıldı — type: daily | streak | friend
  static void notificationOpened(String type) =>
      _log('notification_opened', {'notification_type': type});

  // --- Arkadaş katmanı ---

  /// Arkadaşlık daveti gönderildi.
  static void friendInviteSent() => _log('friend_invite_sent');

  /// Hazır tepki gönderildi — reaction: kapalı kümeden anahtar.
  static void reactionSent(String reaction) =>
      _log('reaction_sent', {'reaction': reaction});

  // --- Hesap ---

  /// Kullanıcı hesabını sildi. Kayıp analizinde en anlamlı sinyal.
  static void accountDeleted() => _log('account_deleted');
}
