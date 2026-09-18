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

  group('silme vaadi KODLA uyusuyor mu', () {
    // Kapali test denetimi (2026-09-14): politika "Hesabini sildiginde tum
    // veriler kalici olarak silinir" diyordu; oysa sunucu yalniz
    // `users/{uid}` agacini temizliyordu. Uc koleksiyon uid tasiyarak
    // disarida kaliyordu ve biri (`feedback`) kullanicinin KENDI yazdigi
    // serbest metindi. Yani vaat tutulmuyordu.
    //
    // Simdi ikisi birden dogrulaniyor: sunucu onlari siliyor VE metin
    // silinmeyenleri adiyla sayiyor. Biri degisip digeri ayni kalirsa
    // burasi duser.

    String backend(String yol) => _kaynak('../../backend/$yol');

    test('sunucu uid alanli koleksiyonlari siliyor', () {
      final kod = backend('services/account_service.py');
      for (final ad in ['usageEvents', 'phoneAttempts', 'feedback']) {
        expect(kod.contains('"$ad"'), isTrue,
            reason: '$ad silme kapsaminda degil ama metin "silinir" diyor');
      }
      expect(kod.contains('_delete_uid_documents(client, uid, sayac)'), isTrue,
          reason: 'silme fonksiyonu delete_account icinden cagrilmiyor');
    });

    test('saklanan kayitlar HER IKI dilde de adiyla yaziyor', () {
      // Yazili olmayan istisna, istisna degil ihlaldir.
      final tr = kPrivacyPolicyTr.map((b) => '${b.$1} ${b.$2}').join(' ');
      final en = kPrivacyPolicyEn.map((b) => '${b.$1} ${b.$2}').join(' ');

      expect(tr.contains('Satın alma ve iade'), isTrue,
          reason: 'TR metin saklanan mali kaydi anmiyor');
      expect(tr.contains('denetim izi'), isTrue,
          reason: 'TR metin saklanan denetim izini anmiyor');
      expect(en.toLowerCase().contains('purchase and refund'), isTrue,
          reason: 'EN metin saklanan mali kaydi anmiyor');
      expect(en.toLowerCase().contains('audit trail'), isTrue,
          reason: 'EN metin saklanan denetim izini anmiyor');
    });

    test('metin artik KOSULSUZ "her sey silinir" demiyor', () {
      // Kosulsuz cumle geri gelirse istisnalar yalan olur.
      final tr = kPrivacyPolicyTr.map((b) => b.$2).join(' ');
      final en = kPrivacyPolicyEn.map((b) => b.$2).join(' ');
      expect(tr.contains('tüm veriler kalıcı olarak silinir'), isFalse);
      expect(en.contains('all of it is permanently deleted'), isFalse);
    });
  });

  group('eklenen kişiler bölümü', () {
    // @-bahsetme (chat_screen.dart _selectMention) kişinin CİHAZDAKİ
    // etiketini mesaj gövdesine yazıyor; mesaj sunucuya gidip konu arşivine
    // yazılıyor. Metin ise "ADI sunucuya HİÇ gönderilmez" diyordu. Mutlak
    // cümle tek bir akışla bile yalana döner.
    test('mutlak "adı hiç gönderilmez" iddiası YOK', () {
      final tr = kPrivacyPolicyTr.map((b) => b.$2).join(' ');
      final en = kPrivacyPolicyEn.map((b) => b.$2).join(' ');
      expect(tr.contains('ADI sunucuya HİÇ gönderilmez'), isFalse);
      expect(en.contains('never sent to our servers'), isFalse);
    });

    test('sohbet istisnası HER İKİ dilde yazılı', () {
      final tr =
          kPrivacyPolicyTr.firstWhere((b) => b.$1 == 'Eklediğin kişiler').$2;
      final en =
          kPrivacyPolicyEn.firstWhere((b) => b.$1 == 'People you add').$2;
      expect(tr.contains('konu arşivine'), isTrue,
          reason: 'sohbette yazılan adın nereye gittiği yazılmıyor');
      expect(en.toLowerCase().contains('topic archive'), isTrue);
    });

    test('kod hâlâ adı gövdeye yazıyor — metin bu yüzden böyle', () {
      // Akış bir gün kapatılırsa metin FAZLA şey söylüyor olur: o gün burası
      // düşer ve üç beyan yeniden okunur.
      final kod = _kaynak('lib/features/chat/chat_screen.dart');
      expect(kod.contains(r"'${aday.display} '"), isTrue,
          reason: 'mention artık adı gövdeye yazmıyorsa metin daraltması '
              'gereksiz kalmış olabilir');
    });
  });
}
