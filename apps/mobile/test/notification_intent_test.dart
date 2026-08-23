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
