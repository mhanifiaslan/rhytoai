// @-bahsetme bekçileri (GT6): belirteç tespiti, aday süzme, bağlam
// önceliği. Kusurun kaynağı: sohbette arkadaş/kişi bağlamına ana
// sekmeden ulaşmanın hiçbir yolu yoktu — @ bunu doldurur.
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/core/friends.dart';
import 'package:rytho/core/people.dart';
import 'package:rytho/features/chat/mention.dart';

Person _kisi(String id, String? label, {String relation = 'partner'}) =>
    Person(
      id: id,
      relation: relation,
      label: label,
      birthDate: '1992-03-04',
      birthCity: 'İzmir',
    );

Friend _arkadas(String uid, String ad,
        {FriendStatus status = FriendStatus.accepted}) =>
    Friend(uid: uid, status: status, displayName: ad);

String _goster(Person k) => k.label ?? k.relation;

void main() {
  group('activeMentionToken', () {
    test('metin başında ve boşluk sonrası tanınır', () {
      expect(activeMentionToken('@ay', 3)?.query, 'ay');
      expect(activeMentionToken('selam @er', 9)?.query, 'er');
      expect(activeMentionToken('selam @', 7)?.query, '');
    });

    test('kelime içindeki @ bahsetme DEĞİLDİR (e-posta)', () {
      expect(activeMentionToken('mail a@b.com', 8), isNull);
    });

    test('boşluk belirteci bitirir', () {
      expect(activeMentionToken('@ayşe nasıl', 11), isNull);
    });

    test('girece kadar bakılır — sonrası önemsiz', () {
      final t = activeMentionToken('@ay sonra', 3);
      expect(t?.start, 0);
      expect(t?.query, 'ay');
    });
  });

  group('mentionCandidates', () {
    final kisiler = [_kisi('p1', 'Ayşe'), _kisi('p2', 'İrem')];
    final arkadaslar = [
      _arkadas('f1', 'Erkan'),
      _arkadas('f2', 'Feyza', status: FriendStatus.incoming),
    ];

    test('kişiler önce, yalnız kabul edilmiş arkadaşlar', () {
      final sonuc = mentionCandidates('', kisiler, arkadaslar, _goster);
      expect(sonuc.map((c) => c.display).toList(), ['Ayşe', 'İrem', 'Erkan']);
      // incoming Feyza YOK — sunucu arkadaş olmayanı reddeder.
    });

    test('Türkçe İ tuzağı: küçük harf sorgu büyük İ adı bulur', () {
      final sonuc = mentionCandidates('ir', kisiler, arkadaslar, _goster);
      expect(sonuc.single.personId, 'p2');
    });

    test('önek eşleşmesi içermeden önce gelir', () {
      final liste = [_kisi('a', 'Nur'), _kisi('b', 'Onur')];
      final sonuc = mentionCandidates('nur', liste, const [], _goster);
      expect(sonuc.first.personId, 'a'); // "Nur" öneki, "Onur" içermesi
    });

    test('etiketsiz kişi ilişki adıyla görünür', () {
      final sonuc = mentionCandidates(
          '', [_kisi('p3', null)], const [], _goster);
      expect(sonuc.single.display, 'partner'); // _goster yedeği
      expect(sonuc.single.relation, 'partner');
    });

    test('tavan uygulanır', () {
      final kalabalik = [for (var i = 0; i < 20; i++) _kisi('p$i', 'Ad$i')];
      expect(mentionCandidates('', kalabalik, const [], _goster).length, 8);
    });
  });

  group('chatContextFields — öncelik tablosu', () {
    test('bahsedilen kişi her şeyi döver', () {
      final f = chatContextFields(
          mentionPersonId: 'mp', mentionFriendUid: null,
          widgetPersonId: 'wp', widgetFriendUid: 'wf', labelMatch: 'lm');
      expect(f, {'person_id': 'mp'});
    });

    test('bahsedilen arkadaş ekran bağlamını döver', () {
      final f = chatContextFields(
          mentionFriendUid: 'mf', widgetPersonId: 'wp');
      expect(f, {'friend_uid': 'mf'});
    });

    test('bahsetme yokken ekran bağlamı aynen', () {
      expect(chatContextFields(widgetFriendUid: 'wf'),
          {'friend_uid': 'wf'});
      expect(chatContextFields(widgetPersonId: 'wp'),
          {'person_id': 'wp'});
    });

    test('hiçbir bağlam yoksa ad eşlemesi kullanılır', () {
      expect(chatContextFields(labelMatch: 'lm'), {'person_id': 'lm'});
      expect(chatContextFields(), isEmpty);
    });
  });
}
