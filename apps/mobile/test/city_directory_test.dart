import 'package:flutter_test/flutter_test.dart';

import 'package:rytho/core/city_directory.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('foldTurkish', () {
    test('noktali/noktasiz I ve aksanlar katlanir', () {
      expect(foldTurkish('İstanbul'), 'istanbul');
      expect(foldTurkish('ISPARTA'), 'isparta');
      expect(foldTurkish('Şanlıurfa'), 'sanliurfa');
      expect(foldTurkish('Kahramanmaraş'), 'kahramanmaras');
      expect(foldTurkish('Zürich'), 'zurich');
      expect(foldTurkish('  Muğla '), 'mugla');
    });
  });

  group('CityDirectory', () {
    late CityDirectory dizin;

    setUpAll(() async {
      dizin = await CityDirectory.load();
    });

    test('turkce yazimla arama nufus sirali', () {
      final sonuc = dizin.search('istanbul');
      expect(sonuc, isNotEmpty);
      expect(sonuc.first.name, 'Istanbul');
      expect(sonuc.first.nation, 'TR');
    });

    test('onek eslesmesi one gecer', () {
      final sonuc = dizin.search('ankar');
      expect(sonuc.first.name.toLowerCase(), startsWith('ankar'));
    });

    test('iki eregli admin1 ile ayrisir', () {
      final sonuc = dizin.search('eregli');
      final iller = sonuc
          .where((s) => s.nation == 'TR')
          .map((s) => s.admin1)
          .toSet();
      // Konya ve Zonguldak Ereğli'leri ayrı satır — kullanıcı ilinden seçer.
      expect(iller.length, greaterThanOrEqualTo(2));
    });

    test('bulunamayan sorgu bos liste', () {
      expect(dizin.search('xqzwv123'), isEmpty);
      // Serbest metin kaçışı UI katmanında — dizin liste dayatmaz.
    });

    test('iki harften kisa sorgu aranmaz', () {
      expect(dizin.search('a'), isEmpty);
    });
  });
}
