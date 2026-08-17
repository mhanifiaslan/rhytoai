import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/core/people.dart';
import 'package:rytho/features/people/person_form_screen.dart';
import 'package:rytho/l10n/app_localizations.dart';

/// P-turu'nun degismezleri: kullanicinin kendi ekledigi kisiler.
///
/// Iki sey sessizce bozulabilir ve ikisi de urunun duruslarini kirar:
///
/// 1. **Kisiye tepki gonderilemez.** Karsi tarafta bir kullanici yok;
///    olmayan bir etkilesimi cizmek "olculmeyen soylenmez" ilkesinin
///    arayuz tarafindaki karsiligini cignemek olurdu.
/// 2. **Saatsiz kayit "12:00" degildir.** Alanin YOKLUGU bilinmiyor
///    demek; `toBirthPayload` bunu `hour_known: false` diye tasimali,
///    yoksa sunucu uydurma bir Yukselen uretir.

Widget _sar(Widget child) => MaterialApp(
      locale: const Locale('tr'),
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: AppLocalizations.supportedLocales,
      home: Scaffold(body: child),
    );

const _cocuk = Person(
  id: 'p1',
  relation: 'child',
  label: 'Deniz',
  birthDate: '2015-06-01',
  birthCity: 'Izmir',
);

const _es = Person(
  id: 'p2',
  relation: 'partner',
  label: 'Ada',
  birthDate: '1990-03-12',
  birthTime: '07:05',
  birthCity: 'Ankara',
  birthNation: 'TR',
);

void main() {
  group('Saat-bilinmiyor disiplini', () {
    test('saati olmayan kisi hour_known: false tasir', () {
      expect(_cocuk.hourKnown, isFalse);
      final yuk = _cocuk.toBirthPayload();
      expect(yuk['hour_known'], isFalse);
      // 12:00 teknik dolgu; gercegi tasiyan bayrak.
      expect(yuk['hour'], 12);
    });

    test('saati olan kisi gercek saati tasir', () {
      final yuk = _es.toBirthPayload();
      expect(yuk['hour_known'], isTrue);
      expect(yuk['hour'], 7);
      expect(yuk['minute'], 5);
    });

    test('dogum yukunde AD YOK', () {
      // Sunucu kisinin adini bilmiyor; prompt'ta iliski etiketi kullanilir.
      expect(_es.toBirthPayload().containsKey('name'), isFalse);
    });
  });

  group('Kayit cozumleme', () {
    test('birthTime alani yoksa null kalir (varsayilan konmaz)', () {
      final kisi = Person.fromDoc('x', {
        'relation': 'parent',
        'birthDate': '1960-01-01',
        'birthCity': 'Urfa',
      });
      expect(kisi.birthTime, isNull);
      expect(kisi.hourKnown, isFalse);
    });

    test('etiket dokumandan DEGIL disaridan gelir', () {
      // Ad cihazda yasiyor; Firestore dokumaninda displayName yok.
      final kisi = Person.fromDoc(
          'x', {'relation': 'child', 'birthDate': '2015-06-01'},
          label: 'Deniz');
      expect(kisi.label, 'Deniz');
      final etiketsiz = Person.fromDoc(
          'x', {'relation': 'child', 'birthDate': '2015-06-01'});
      expect(etiketsiz.label, isNull);
    });
  });

  group('Tur kumesi', () {
    test('backend RELATIONS ile birebir ayni', () {
      // Tur yalniz simge degil: eksen adlarini ve AI cercevesini belirliyor.
      // Iki taraf ayrisirsa cocukta "Cekim" ekseni geri gelebilir.
      expect(kRelations, [
        'partner',
        'child',
        'parent',
        'sibling',
        'friend',
        'work',
        'other',
      ]);
    });

    testWidgets('her tur icin etiket ve simge var', (tester) async {
      late AppLocalizations l10n;
      await tester.pumpWidget(_sar(Builder(builder: (c) {
        l10n = AppLocalizations.of(c);
        return const SizedBox();
      })));
      for (final tur in kRelations) {
        expect(relationLabel(l10n, tur), isNotEmpty, reason: tur);
        expect(relationIcon(tur), isA<IconData>(), reason: tur);
      }
    });
  });
}
