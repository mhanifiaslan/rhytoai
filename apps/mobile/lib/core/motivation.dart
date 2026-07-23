import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:intl/intl.dart';

/// Günlük seri (streak) ve burca özel motivasyon cümleleri.
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
    return next;
  }
}

/// Burç adı (Türkçe) → kısa motive edici cümleler. Gün numarasıyla
/// döngüsel seçilir; böylece her gün aynı burca farklı cümle düşer.
const Map<String, List<String>> kSignNudges = {
  'Koç': [
    'Bugün ilk adımı atan sen ol — evren cesareti ödüllendirir. 🔥',
    'Enerjini tek hedefe topla; küçük bir zafer büyük kapı açar.',
    'İçindeki kıvılcım bugün birine ilham verecek.',
  ],
  'Boğa': [
    'Sabrın bugün meyvesini gösterir; yavaş ama sağlam ilerle. 🌱',
    'Kendine küçük bir güzellik armağan et — hak ediyorsun.',
    'Kararlılığın, etrafındakilere güven veriyor.',
  ],
  'İkizler': [
    'Bugün kuracağın bir cümle, birinin gününü değiştirebilir. ✨',
    'Merakını takip et; öğrendiğin şey yakında işine yarayacak.',
    'İki seçenek arasındaysan, kalbinin hızlandığını seç.',
  ],
  'Yengeç': [
    'Sezgilerin bugün pusulan olsun; onlar seni yanıltmaz. 🌙',
    'Sevdiğin birine küçük bir jest yap — döngü sana geri döner.',
    'Duyguların gücündür, zayıflığın değil.',
  ],
  'Aslan': [
    'Sahne bugün senin; ışığını kısma. ☀️',
    'Cömertliğin karizmandan daha parlak — ikisini de kullan.',
    'Birini yüreklendir; liderlik tam olarak budur.',
  ],
  'Başak': [
    'Bugün tek bir şeyi kusursuz yap, gerisi kendiliğinden düzelir.',
    'Detaylarda gizlenen fırsatı yalnızca sen görürsün. 🔍',
    'Kendine de başkalarına gösterdiğin özeni göster.',
  ],
  'Terazi': [
    'Dengede kalmak da bir hareket biçimidir; kendine güven. ⚖️',
    'Bugün bir güzelliği paylaş; estetik senin dilin.',
    'Karar vermek özgürleştirir — ertelediğini bugün seç.',
  ],
  'Akrep': [
    'Derinliğin bugün avantajın; yüzeyde oyalanma. 🌊',
    'Dönüşüm sancısız olmaz; bugünkü zorluk yarının gücü.',
    'Birine gerçekten güvenmeyi dene — kontrollü bir adım yeter.',
  ],
  'Yay': [
    'Ufkun çağırıyor; bugün küçük de olsa bir keşif yap. 🏹',
    'İyimserliğin bulaşıcı — bugün onu cömertçe dağıt.',
    'Büyük resmi görüyorsun; detaylara takılma.',
  ],
  'Oğlak': [
    'Zirve sabırla çıkılır; bugünkü adımın kaydedildi. 🏔️',
    'Disiplinin bugün sana beklenmedik bir kapı açacak.',
    'Dinlenmek de planın parçası — kendine izin ver.',
  ],
  'Kova': [
    'Farklı düşünmen bugün tam olarak ihtiyaç duyulan şey. ⚡',
    'Topluluğuna bir fikir armağan et; dalga etkisi yaratır.',
    'Özgünlüğün, en büyük sermayen.',
  ],
  'Balık': [
    'Hayal gücün bugün pratik bir soruna çözüm olacak. 🌌',
    'Sınır koymak, şefkatin düşmanı değil koruyucusudur.',
    'İçindeki sanatçıya bugün beş dakika ver.',
  ],
};

/// Günün burca özel motive edici cümlesi. Burç bilinmiyorsa evrensel mesaj.
String nudgeForSign(String? sunSign, {DateTime? now}) {
  final date = now ?? DateTime.now();
  final dayOfYear = int.parse(DateFormat('D').format(date));
  final list = kSignNudges[sunSign];
  if (list == null || list.isEmpty) {
    return 'Bugün gökyüzü senden yana; niyetini netleştir. ✨';
  }
  return list[dayOfYear % list.length];
}
