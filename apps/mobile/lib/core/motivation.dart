import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:intl/intl.dart';

import 'friends.dart' show syncPublicProfile;

/// Günlük seri (streak) takibi.
///
/// Burca özel konserve motivasyon cümleleri kaldırıldı: ana ekranda zaten
/// AI'ın gerçek gökyüzü verisiyle ürettiği burç yorumu var, altına hazır bir
/// cümle eklemek yorumu ucuzlatıyordu.
///
/// Seri kuralı: kullanıcı günlük okumayı art arda günlerde açtıkça
/// `streakCount` artar; bir gün atlanırsa 1'e döner. Durum Firestore
/// profilinde `lastSeenDaily` (yyyy-MM-dd) + `streakCount` alanlarında
/// tutulur — infra/firestore.rules bu alanlara izin verir.
class DailyStreak {
  DailyStreak._();

  static String _dayKey(DateTime d) => DateFormat('yyyy-MM-dd').format(d);

  /// Bugünü işler; profildeki yeni seri sayısını döndürür.
  /// Profil verisi çağrının yapıldığı andaki stream değeridir.
  static Future<int> touch(Map<String, dynamic> profile) async {
    final uid = FirebaseAuth.instance.currentUser?.uid;
    if (uid == null) return 0;

    final now = DateTime.now();
    final today = _dayKey(now);
    final yesterday = _dayKey(now.subtract(const Duration(days: 1)));
    final lastSeen = profile['lastSeenDaily'] as String?;
    final current = (profile['streakCount'] as num?)?.toInt() ?? 0;

    if (lastSeen == today) return current; // bugün zaten sayıldı

    final next = lastSeen == yesterday ? current + 1 : 1;
    await FirebaseFirestore.instance.collection('users').doc(uid).set({
      'lastSeenDaily': today,
      'streakCount': next,
    }, SetOptions(merge: true));
    // Arkadaşlar `users/{uid}` dokümanını okuyamaz (doğum verisi içerir);
    // seri bilgisi herkese açık karta buradan yansır.
    await syncPublicProfile();
    return next;
  }
}
