import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/core/deep_links.dart';

/// Davet bağlantısının ayrıştırılması.
///
/// Bağlantı DIŞARIDAN gelir: paylaşılan bir metinden, tarayıcıdan, başka bir
/// uygulamadan. İçerdiği değere güvenilemez — geçersiz ya da kötü niyetli bir
/// kullanıcı adı arkadaş ekleme kutusuna doldurulmamalı.
void main() {
  group('usernameFromInviteLink', () {
    test('geçerli davet bağlantısını çözer', () {
      final uri = Uri.parse('https://$kInviteHost/i/gezgin');
      expect(usernameFromInviteLink(uri), 'gezgin');
    });

    test('üretilen bağlantı kendi ayrıştırıcısıyla çözülebilir', () {
      // Üretim ve tüketim aynı sabiti kullanmak zorunda; ayrışırsa
      // paylaşılan bağlantı hiçbir yere gitmez.
      final link = inviteLinkFor('deniz_42');
      expect(usernameFromInviteLink(Uri.parse(link)), 'deniz_42');
    });

    test('büyük harf küçültülür', () {
      final uri = Uri.parse('https://$kInviteHost/i/GEZGIN');
      expect(usernameFromInviteLink(uri), 'gezgin');
    });

    test('sondaki eğik çizgi sorun olmaz', () {
      final uri = Uri.parse('https://$kInviteHost/i/gezgin/');
      expect(usernameFromInviteLink(uri), 'gezgin');
    });

    test('sorgu parametresi yok sayılır', () {
      final uri = Uri.parse('https://$kInviteHost/i/gezgin?utm_source=wa');
      expect(usernameFromInviteLink(uri), 'gezgin');
    });
  });

  group('reddedilmesi gerekenler', () {
    test('başka alan adı reddedilir', () {
      // Sahte bir alan adı, kullanıcıyı istemediği birini eklemeye
      // yönlendirebilirdi.
      final uri = Uri.parse('https://kotu-site.example/i/gezgin');
      expect(usernameFromInviteLink(uri), isNull);
    });

    test('davet olmayan yol reddedilir', () {
      for (final yol in ['/', '/hakkinda', '/i', '/x/gezgin']) {
        final uri = Uri.parse('https://$kInviteHost$yol');
        expect(usernameFromInviteLink(uri), isNull, reason: yol);
      }
    });

    test('kural dışı kullanıcı adları reddedilir', () {
      // Kullanıcı adı kuralı: 3-20 karakter, küçük harf/rakam/alt çizgi
      // (bkz. core/friends.dart, kUsernamePattern).
      final gecersizler = [
        'ab',                      // çok kısa
        'a' * 21,                  // çok uzun
        'ad soyad',                // boşluk
        'kullanıcı',               // Türkçe karakter
        'admin!',                  // noktalama
        '../../etc/passwd',        // yol kaçışı
        '<script>',                // enjeksiyon denemesi
      ];
      for (final ad in gecersizler) {
        final uri = Uri.parse(
            'https://$kInviteHost/i/${Uri.encodeComponent(ad)}');
        expect(usernameFromInviteLink(uri), isNull, reason: ad);
      }
    });

    test('boş kullanıcı adı reddedilir', () {
      expect(usernameFromInviteLink(Uri.parse('https://$kInviteHost/i//')),
          isNull);
    });
  });

  group('inviteLinkFor', () {
    test('doğru alan adını ve yolu kullanır', () {
      expect(inviteLinkFor('gezgin'), 'https://$kInviteHost/i/gezgin');
    });

    test('kullanıcı adı URL için kodlanır', () {
      // Kural dışı bir ad buraya gelmemeli ama gelse bile bağlantı bozulmamalı.
      expect(inviteLinkFor('a b'), contains('a%20b'));
    });
  });
}
