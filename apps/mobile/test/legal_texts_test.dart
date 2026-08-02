import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/features/profile/legal_texts.dart';

/// Gizlilik politikasinin ICERIGI ve KODLA UYUMU.
///
/// Bu dosyanin varlik sebebi su: hukuki metin, urunun ne yaptigina dair bir
/// IDDIA. Kod degisip metin ayni kalirsa iddia yalana doner ve bu, teknik bir
/// kusurdan cok daha pahaliya patlar.
///
/// Yuz okuma bolumu su uc seyi soyluyor ve ucu de kodda dogrulanabilir:
/// goruntu sunucuya gitmiyor, diske YAZILMIYOR, sunucuya yalnizca turetilmis
/// oranlar gidiyor.

String _kaynak(String yol) => File(yol).readAsStringSync();

void main() {
  group('yuz okuma bolumu', () {
    test('her iki dilde de VAR', () {
      expect(
        kPrivacyPolicyTr.any((b) => b.$1 == 'Yüz okuma'),
        isTrue,
        reason: 'Turkce politikada yuz okuma bolumu yok',
      );
      expect(
        kPrivacyPolicyEn.any((b) => b.$1 == 'Face reading'),
        isTrue,
        reason: 'Ingilizce politikada yuz okuma bolumu yok',
      );
    });

    test('rizanin geri alinabilirligini soyluyor', () {
      final tr = kPrivacyPolicyTr
          .firstWhere((b) => b.$1 == 'Yüz okuma')
          .$2;
      // Riza geri alinabilir olmak zorunda (GDPR Md.7/2) ve metin bunu
      // SOYLEMELI; uygulamada var olup metinde olmamasi eksik beyandir.
      expect(tr, contains('geri'));
      expect(tr, contains('Gizlilik'));
    });

    test('karar amacli kullanilmayacagini soyluyor', () {
      final tr =
          kPrivacyPolicyTr.firstWhere((b) => b.$1 == 'Yüz okuma').$2;
      final en =
          kPrivacyPolicyEn.firstWhere((b) => b.$1 == 'Face reading').$2;
      // Ise alim / kredi / sigorta gibi kararlarda kullanim, duzenleyici
      // tarafta en riskli alan. Metin bunu acikca disliyor.
      expect(tr.toLowerCase(), contains('işe alım'));
      expect(en.toLowerCase(), contains('employment'));
    });
  });

  group('dil yalitimi', () {
    test('Ingilizce politikada Turkce karakter yok', () {
      // Projede baska katmanlarda da uygulanan kural: dil karismasin.
      final govde = kPrivacyPolicyEn.map((b) => '${b.$1} ${b.$2}').join(' ');
      for (final harf in ['ğ', 'ş', 'ı', 'İ', 'ç', 'ö', 'ü', 'Ğ', 'Ş']) {
        expect(govde.contains(harf), isFalse,
            reason: 'Ingilizce metinde Turkce harf: $harf');
      }
    });
  });

  group('metin KODLA uyusuyor mu', () {
    test('politika "diske yazilmaz" diyor — kod fotograf CEKMIYOR', () {
      // Onceki surum `takePicture()` ile gecici bir dosya yaziyordu. O cagri
      // geri gelirse politika yalan soylemeye baslar.
      //
      // Aranan sey CAGRI kalibi (`.takePicture(`), duz metin degil: dosyanin
      // aciklama satirlari eski davranisi ANLATIYOR ve `takePicture()` sozu
      // orada gecmeye devam etmeli. Ilk surum bunu ayirt etmiyor ve kendi
      // yorumuna takiliyordu.
      final ekran =
          _kaynak('lib/features/face/face_capture_screen.dart');
      expect(ekran.contains('.takePicture('), isFalse,
          reason: 'fotograf cekiliyor ama politika "diske yazilmaz" diyor');
    });

    test('sunucuya giden alanlar oran; koordinat gonderilmiyor', () {
      final geometri = _kaynak('lib/features/face/face_geometry.dart');
      // `toJson` yalnizca oran alanlari tasimali. Ham landmark adlari
      // gecerse sunucuya kisiye ozgu bir imza gidiyor demektir.
      final baslangic = geometri.indexOf('Map<String, double> toJson()');
      final bitis = geometri.indexOf('static double _yuvarla');
      expect(baslangic, greaterThan(-1));
      final govde = geometri.substring(baslangic, bitis);
      for (final yasak in ['faceOval', 'chin', 'noseBase', 'eyeLeft']) {
        expect(govde.contains("'$yasak'"), isFalse,
            reason: '$yasak sunucuya gonderiliyor');
      }
    });
  });
}
