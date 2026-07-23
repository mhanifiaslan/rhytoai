import 'package:firebase_analytics/firebase_analytics.dart';
import 'package:flutter/foundation.dart';

/// Basit analytics cephesi — tüm olay adları tek yerde dursun.
/// Olaylar arka planda gönderilir; hata olursa uygulama akışını etkilemez.
class Analytics {
  Analytics._();

  static Future<void> _log(String name, [Map<String, Object>? params]) async {
    try {
      await FirebaseAnalytics.instance.logEvent(name: name, parameters: params);
    } catch (e) {
      debugPrint('Analytics olayı gönderilemedi ($name): $e');
    }
  }

  /// Rapor üretimi — type: daily | natal | bazi | synastry
  static void reportGenerated(String type) =>
      _log('report_generated', {'report_type': type});

  /// Akışa veya kanala gönderi yayınlandı.
  static void postPublished({required bool toChannel}) =>
      _log('post_published', {'target': toChannel ? 'channel' : 'feed'});

  /// Bir kullanıcı takip edildi.
  static void userFollowed() => _log('user_followed');

  /// Bir kanala abone olundu.
  static void channelSubscribed() => _log('channel_subscribed');

  /// I Ching çekimi yapıldı — method: coins | yarrow
  static void ichingCast(String method) =>
      _log('iching_cast', {'method': method});

  /// Yüz analizi tamamlandı.
  static void faceAnalyzed() => _log('face_analyzed');
}
