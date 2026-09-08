// KA5/KA6 bekçileri: bildirim niyeti, yük kodlaması ve kişi adı eşlemesi.
//
// Kusurların kaynağı cihaz turu: bildirime dokunmak yalnız sekme açıyordu
// (R2-S4'ün derin bağlantı vaadi hiç yazılmamıştı) ve sohbet, ana sekmeden
// sorulan "eşimle aram nasıl?" sorusuna bağlamsız gidiyordu.
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/core/notifications.dart';
import 'package:rytho/core/people.dart';

void main() {
  group('yük kodlama', () {
    test('soru & ve = içerse de gidiş-dönüş bozulmaz', () {
      // Naif `key=value&` birleştirmesi bu soruda sessizce bozuluyordu.
      final veri = {
        'type': 'checkin',
        'q': 'İş & ev dengesi nasıldı? x=1 oldu mu?',
        'q_date': '2026-08-23',
      };
      final cozulen = decodeNotificationPayload(
          encodeNotificationPayload(veri));
      expect(cozulen['q'], veri['q']);
      expect(cozulen['type'], 'checkin');
      expect(cozulen['q_date'], '2026-08-23');
    });

    test('kodlanmamış eski biçim yine çözülür', () {
      final cozulen = decodeNotificationPayload('type=daily&sign=leo');
      expect(cozulen['type'], 'daily');
      expect(cozulen['sign'], 'leo');
    });
  });

  group('tabForNotification', () {
    test('checkin Gökyüzü zemininde kalır (sohbet üstüne açılır)', () {
      expect(tabForNotification({'type': 'checkin'}), 0);
    });
    test('bilinen türler değişmedi', () {
      expect(tabForNotification({'type': 'friend'}), 2);
      expect(tabForNotification({'type': 'daily'}), 0);
      expect(tabForNotification({'type': 'streak'}), 0);
      expect(tabForNotification({'type': 'bilinmeyen'}), 0);
    });
  });

  group('resolveNotificationRoute (BY-turu)', () {
    // Cihaz bulgusu: "öğle bildirimine tıkladım, sadece uygulama açıldı."
    // Bu matris HER türün anlamlı bir hedefe düştüğünü sabitler — hiçbir
    // yük "yalnız uygulamayı aç"ta kalamaz.
    NotificationRoute r(Map<String, String> data) =>
        resolveNotificationRoute(data);

    test('daily route=signal → sinyal dayanak sayfası (SkyScreen işi)', () {
      expect(r({'type': 'daily', 'route': 'signal', 'fp': 'x'}).kind,
          NotificationRouteKind.signalSheet);
    });

    test('daily route=story ve ROUTE\'SUZ ESKİ yük → günlük okuma', () {
      expect(r({'type': 'daily', 'route': 'story', 'sign': 'leo'}).kind,
          NotificationRouteKind.dailyStory);
      final eski = r({'type': 'daily', 'sign': 'leo'});
      expect(eski.kind, NotificationRouteKind.dailyStory);
      expect(eski.sign, 'leo');
    });

    test('streak → günlük okuma (istenen eylemi yapar)', () {
      expect(r({'type': 'streak'}).kind, NotificationRouteKind.dailyStory);
      expect(r({'type': 'streak', 'route': 'story'}).kind,
          NotificationRouteKind.dailyStory);
    });

    test('checkin → soru yazılı sohbet', () {
      final rota = r({'type': 'checkin', 'q': 'Nasıl geçti?',
          'q_date': '2026-08-29'});
      expect(rota.kind, NotificationRouteKind.checkinChat);
      expect(rota.question, 'Nasıl geçti?');
      expect(rota.questionDate, '2026-08-29');
    });

    test('SS-turu: route=chat_answer + cid → Rytho SORDU', () {
      // Ayrım TÜRE değil YAPIYA bağlı: gövde bir soruysa sunucu konuyu
      // tohumlar ve yüke cid koyar. Tür adına bakan bir kural, ileride
      // eklenecek soru biçimli başka bir bildirimde yanlış çalışırdı.
      final rota = r({
        'type': 'checkin',
        'route': 'chat_answer',
        'cid': 'ask-2026-09-08',
        'q': 'Bugün iş tarafı nasıl geçti?',
        'q_date': '2026-09-08',
      });
      expect(rota.kind, NotificationRouteKind.rythoAsks);
      expect(rota.conversationId, 'ask-2026-09-08');
      // Soru yalnız YEDEK olarak taşınır (arşiv boş dönerse çizilir);
      // giriş kutusuna YAZILMAZ — o davranış tam da onarılan hataydı.
      expect(rota.question, 'Bugün iş tarafı nasıl geçti?');
    });

    test('SS-turu: cid yoksa ESKİ davranışa düşer (tohum yazılamadı)', () {
      // Sunucu tohumu yazamazsa yüke cid KOYMAZ; bildirim yine gider ve
      // dokunuş eski yolu izler — kullanıcı bir şey kaybetmez.
      final rota = r({
        'type': 'checkin',
        'route': 'chat_answer',
        'q': 'Nasıl geçti?',
        'q_date': '2026-09-08',
      });
      expect(rota.kind, NotificationRouteKind.checkinChat);
      expect(rota.conversationId, isNull);
    });

    test('öğle çift ânı ve kabul → o İLİŞKİNİN ekranı', () {
      final ogle = r({'type': 'friend', 'src': 'midday', 'fromUid': 'f1'});
      expect(ogle.kind, NotificationRouteKind.friendRelation);
      expect(ogle.friendUid, 'f1');
      expect(
          r({'type': 'friend', 'src': 'invite_accepted',
              'fromUid': 'f2'}).kind,
          NotificationRouteKind.friendRelation);
      // Çevrem kişisiyle öğle ânı → kişi ilişki ekranı.
      final kisi = r({'type': 'friend', 'src': 'midday', 'pid': 'p9'});
      expect(kisi.kind, NotificationRouteKind.personRelation);
      expect(kisi.personId, 'p9');
    });

    test('davet ve tepki → Çevrem sekmesi (istek/kutu en üstte)', () {
      expect(r({'type': 'friend', 'src': 'invite', 'fromUid': 'f1'}).kind,
          NotificationRouteKind.circleTab);
      expect(
          r({'type': 'friend', 'src': 'reaction', 'fromUid': 'f1'}).kind,
          NotificationRouteKind.circleTab);
      // ESKİ src'siz yük de çıkmaz sokakta kalmaz.
      expect(r({'type': 'friend', 'fromUid': 'f1'}).kind,
          NotificationRouteKind.circleTab);
    });

    test('bilinmeyen tür ana sekmede güvenle kalır', () {
      expect(r({'type': 'yeni-tur'}).kind, NotificationRouteKind.homeTab);
      expect(r({}).kind, NotificationRouteKind.homeTab);
    });
  });

  group('bekleyen niyet', () {
    test('kur / oku / temizle', () {
      final container = ProviderContainer();
      addTearDown(container.dispose);
      final notifier =
          container.read(pendingNotificationProvider.notifier);

      notifier.set({'type': 'daily', 'fp': 'abc', 'idx': 0});
      final niyet = container.read(pendingNotificationProvider);
      expect(niyet, isNotNull);
      expect(niyet!.type, 'daily');
      // Değerler String'e çevrilir: FCM data haritası dinamik gelebilir.
      expect(niyet.data['idx'], '0');

      notifier.clear();
      expect(container.read(pendingNotificationProvider), isNull);
    });
  });

  group('kişi adı eşlemesi (etiket cihazda)', () {
    Person kisi(String id, String? label) => Person(
          id: id,
          relation: 'partner',
          label: label,
          birthDate: '1992-03-04',
          birthCity: 'İzmir',
        );

    test('mesajdaki ad kişiye eşlenir', () {
      final kisiler = [kisi('p1', 'Ayşe'), kisi('p2', 'Mehmet')];
      expect(matchPersonIdByLabel('Mehmet ile aram nasıl?', kisiler), 'p2');
    });

    test('noktalı İ tuzağı: büyük harfli ad da eşleşir', () {
      // "İrem".toLowerCase() birleşik nokta üretir; normalize edilmezse
      // "irem" araması sessizce kaçırırdı (Türkçe metin tuzağı).
      final kisiler = [kisi('p1', 'İrem')];
      expect(matchPersonIdByLabel('irem bugün nasıl olur?', kisiler), 'p1');
    });

    test('kısa etiket yanlış pozitife karşı eşleşmez', () {
      final kisiler = [kisi('p1', 'Al')];
      expect(matchPersonIdByLabel('normal bir soru', kisiler), isNull);
    });

    test('etiketsiz kişi ve eşleşmeyen mesaj null', () {
      final kisiler = [kisi('p1', null)];
      expect(matchPersonIdByLabel('Ayşe nasıl?', kisiler), isNull);
      expect(matchPersonIdByLabel('bugün nasılım?', const []), isNull);
    });
  });
}
