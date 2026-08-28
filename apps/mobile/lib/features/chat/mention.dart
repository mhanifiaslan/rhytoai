/// Sohbette @-bahsetme mantığı (GT-turu) — SAF fonksiyonlar, widget yok.
///
/// Kullanıcı '@' yazınca giriş bandı kişi/arkadaş adaylarına dönüşür;
/// seçim adı metne yazar ve o MESAJA bağlam (personId/friendUid) iliştirir.
/// Mesaj başına TEK bağlam: sunucuda tek ilişki yuvası var; ikinci seçim
/// ilkini değiştirir.
///
/// Gizlilik: kişi etiketi cihazda kalır; sunucuya yalnız kimlik gider.
/// Adın MESAJ METNİNE girmesi mevcut emsalle kabul edilmiş davranış
/// (relationshipAskPrefill aynı şeyi yapıyor).
library;

import '../../core/friends.dart';
import '../../core/people.dart';

/// Girece kadar süren aktif '@' belirteci.
class MentionToken {
  const MentionToken({required this.start, required this.query});

  /// '@' karakterinin metindeki konumu.
  final int start;

  /// '@' sonrası, girece kadarki sorgu (boş olabilir — tam liste açılır).
  final String query;
}

/// Metin + girece göre aktif bahsetme belirteci; yoksa null.
///
/// Kurallar: '@' metnin başında ya da boşluktan sonra olmalı (kelime
/// içindeki '@' — e-posta gibi — bahsetme DEĞİLDİR); '@' ile girece kadar
/// boşluk olmamalı (boşluk belirteci bitirir).
MentionToken? activeMentionToken(String text, int caret) {
  if (caret < 1 || caret > text.length) return null;
  final at = text.lastIndexOf('@', caret - 1);
  if (at < 0) return null;
  if (at > 0 && !_bosluk(text[at - 1])) return null;
  final sorgu = text.substring(at + 1, caret);
  if (sorgu.contains(RegExp(r'\s'))) return null;
  return MentionToken(start: at, query: sorgu);
}

bool _bosluk(String c) => c == ' ' || c == '\n' || c == '\t';

/// Seçilebilir aday: kişi YA DA arkadaş (tam biri dolu).
class MentionCandidate {
  const MentionCandidate({required this.display, this.personId, this.friendUid,
      this.relation});

  final String display;
  final String? personId;
  final String? friendUid;

  /// Kişi adayında ilişki türü (ikon seçimi için); arkadaşta null.
  final String? relation;
}

/// Sorguya göre aday listesi. KİŞİLER ÖNCE (daha kişisel), sonra yalnız
/// KABUL EDİLMİŞ arkadaşlar (sunucu arkadaş olmayanı reddeder). Önek
/// eşleşmesi içermeden önce sıralanır; boş sorgu tam listeyi döndürür
/// (keşfedilebilirlik). Türkçe İ tuzağı `normalizeTr` ile kapalı.
List<MentionCandidate> mentionCandidates(
  String query,
  List<Person> people,
  List<Friend> friends,
  String Function(Person) personDisplay, {
  int cap = 8,
}) {
  final q = normalizeTr(query.trim());

  final adaylar = <(int, MentionCandidate)>[];

  void ekle(String display, MentionCandidate aday) {
    final ad = normalizeTr(display);
    if (q.isEmpty) {
      adaylar.add((1, aday));
    } else if (ad.startsWith(q)) {
      adaylar.add((0, aday));
    } else if (ad.contains(q)) {
      adaylar.add((1, aday));
    }
  }

  for (final kisi in people) {
    final ad = personDisplay(kisi);
    ekle(ad, MentionCandidate(
        display: ad, personId: kisi.id, relation: kisi.relation));
  }
  for (final arkadas in friends) {
    if (arkadas.status != FriendStatus.accepted) continue;
    ekle(arkadas.name, MentionCandidate(
        display: arkadas.name, friendUid: arkadas.uid));
  }

  // Kararlı sıralama: önek eşleşenler öne; kişi/arkadaş sırası ekleme
  // sırasından (kişiler önce) korunur.
  adaylar.sort((a, b) => a.$1.compareTo(b.$1));
  return [for (final (_, aday) in adaylar.take(cap)) aday];
}

/// `_send` gövdesinin bağlam alanları — SAF, test edilebilir (GT6).
///
/// Öncelik: bahsedilen kişi > bahsedilen arkadaş > ekran bağlamı (kişi >
/// arkadaş) > cihaz ad eşlemesi (`labelMatch`). Bahsetme ya da ekran
/// bağlamı varken ad eşlemesi HİÇ kullanılmaz — açık niyet sezgiyi döver.
Map<String, dynamic> chatContextFields({
  String? mentionPersonId,
  String? mentionFriendUid,
  String? widgetPersonId,
  String? widgetFriendUid,
  String? labelMatch,
}) {
  if (mentionPersonId != null) return {'person_id': mentionPersonId};
  if (mentionFriendUid != null) return {'friend_uid': mentionFriendUid};
  return {
    'friend_uid': ?widgetFriendUid,
    'person_id': ?(widgetPersonId ??
        (widgetFriendUid == null ? labelMatch : null)),
  };
}
