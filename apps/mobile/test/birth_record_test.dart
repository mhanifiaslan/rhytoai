import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/core/birth_record.dart';

/// Dogum kaydinin iki degismezi.
///
/// ## 1. Bayat Buyuk Uclu birakilmaz
///
/// `sunSign` / `moonSign` / `ascendant` profilde ONBELLEKLENMIS degerler.
/// Kullanici dogum tarihini duzeltir de harita cagrisi basarisiz olursa,
/// dokumanda *yeni tarih* ile *eski burclar* yan yana kalir. Hata cikmaz,
/// ekran calisir — sadece yalan soyler. Bu tam olarak bu projede tekrar
/// tekrar yakalanan sessiz kusur turu.
///
/// Silmek guvenli: okumalar bu alanlardan degil ham dogum verisinden
/// hesaplaniyor (`birthPayload`), ilk basarili cagrida geri geliyorlar.
///
/// ## 2. Degismeyen form kaydedilmez
///
/// `sameAs` kaydet butonunun etkinligini belirliyor. Yanlis olursa ya
/// gereksiz ag cagrisi olur ya da kullanici degisikligini kaydedemez.

BirthRecord _ornek({
  DateTime? tarih,
  String saat = '04:30',
  String sehir = 'Ankara',
  String cinsiyet = 'male',
}) =>
    BirthRecord(
      date: tarih ?? DateTime(1988, 3, 7),
      time: saat,
      city: sehir,
      gender: cinsiyet,
    );

void main() {
  group('bayat Buyuk Uclu', () {
    test('harita gelmezse burclar SILINIR, eski deger kalmaz', () {
      final veri = birthWriteData(_ornek(), uid: 'u1', chart: null);

      // Kritik: string DEGIL. Bir string kalsaydi eski burc yeni tarihle
      // yan yana durur ve kimse fark etmezdi.
      expect(veri['sunSign'], isA<FieldValue>());
      expect(veri['moonSign'], isA<FieldValue>());
      expect(veri['ascendant'], isA<FieldValue>());

      // Dogum verisi yine de yazilir — kullanici duzeltmesini kaybetmez.
      expect(veri['birthDate'], '1988-03-07');
      expect(veri['birthTime'], '04:30');
    });

    test('harita gelirse burclar tazelenir', () {
      final veri = birthWriteData(_ornek(), uid: 'u1', chart: const {
        'sun_sign': 'Balik ♓',
        'moon_sign': 'Aslan ♌',
        'ascendant': 'Kova ♒',
      });

      expect(veri['sunSign'], 'Balik ♓');
      expect(veri['moonSign'], 'Aslan ♌');
      expect(veri['ascendant'], 'Kova ♒');
    });

    test('harita eksik alanla gelirse o alan SILINIR', () {
      // Backend bir alani dondurmezse de bayat deger birakmamaliyiz.
      final veri = birthWriteData(_ornek(),
          uid: 'u1', chart: const {'sun_sign': 'Balik ♓'});

      expect(veri['sunSign'], 'Balik ♓');
      expect(veri['moonSign'], isA<FieldValue>());
      expect(veri['ascendant'], isA<FieldValue>());
    });
  });

  group('tarih bicimi', () {
    test('tek haneli ay ve gun sifirla doldurulur', () {
      expect(_ornek(tarih: DateTime(2001, 1, 5)).dateText, '2001-01-05');
    });

    test('profilden okuma: bozuk tarih varsayilan verir, cokmez', () {
      final k = BirthRecord.fromProfile({'birthDate': 'bilmemne'});
      expect(k.dateText, '2000-01-01');
    });

    test('profilden okuma: gercek deger korunur', () {
      final k = BirthRecord.fromProfile({
        'birthDate': '1988-03-07',
        'birthTime': '04:30',
        'birthCity': 'Ankara',
        'gender': 'male',
      });
      expect(k.dateText, '1988-03-07');
      expect(k.time, '04:30');
      expect(k.city, 'Ankara');
      expect(k.gender, 'male');
    });

    test('profil bossa makul varsayilan', () {
      final k = BirthRecord.fromProfile(null);
      expect(k.time, '12:00');
      expect(k.city, 'Istanbul');
    });
  });

  group('degisiklik tespiti', () {
    test('ayni kayit degismis sayilmaz', () {
      expect(_ornek().sameAs(_ornek()), isTrue);
    });

    test('sehirdeki bosluk fark yaratmaz', () {
      // Aksi hâlde imlecin biraktigi bir bosluk "degisti" sayilir ve
      // gereksiz bir harita hesabi tetiklerdi.
      expect(_ornek(sehir: '  Ankara ').sameAs(_ornek()), isTrue);
    });

    test('saat degisince degismis sayilir', () {
      expect(_ornek(saat: '05:30').sameAs(_ornek()), isFalse);
    });

    test('tarih degisince degismis sayilir', () {
      expect(_ornek(tarih: DateTime(1988, 3, 8)).sameAs(_ornek()), isFalse);
    });

    test('cinsiyet degisince degismis sayilir', () {
      expect(_ornek(cinsiyet: 'female').sameAs(_ornek()), isFalse);
    });
  });
}
