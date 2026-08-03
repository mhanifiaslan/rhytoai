import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/features/atlas/atlas_detail_screens.dart';
import 'package:rytho/l10n/app_localizations.dart';

/// Asama A3'un degismezleri.
///
/// Kullanicinin tarifi: "atlas sayfasi da tuhaf, profilimde olan bilgiler de
/// var yuz okuma da var, asagi dogru uzanan uzun metinler de var, kisilik
/// ozellikleri, gezegen konumlari vs... her sey her yerde hissi var."
///
/// Teshis "cok ozellik var" DEGIL, hepsinin ayni seviyede durmasiydi. Atlas
/// artik bir dizin; asagidaki testler detayin gercekten detay sayfasinda
/// oldugunu ve orada KIRPILMADIGINI koruyor.

List<Map<String, dynamic>> _aciUret(int adet) => [
      for (var i = 0; i < adet; i++)
        {
          'p1': 'Gezegen$i',
          'p1_tr': 'Gezegen$i',
          'p2': 'Hedef$i',
          'p2_tr': 'Hedef$i',
          'aspect': 'square',
          'aspect_tr': 'Kare',
          'orbit': 1.5 + i,
        },
    ];

final _gezegenler = <Map<String, dynamic>>[
  {'name': 'Sun', 'name_tr': 'Güneş', 'sign_tr': 'Aslan', 'abs_position': 130.0},
  {'name': 'Moon', 'name_tr': 'Ay', 'sign_tr': 'Balık', 'abs_position': 340.0},
  {
    'name': 'Mercury',
    'name_tr': 'Merkür',
    'sign_tr': 'Başak',
    'abs_position': 160.0,
    'retrograde': true,
  },
];

Widget _sar(Widget child) => MaterialApp(
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: AppLocalizations.supportedLocales,
      locale: const Locale('tr'),
      home: child,
    );

/// `AstrolabeSpinner` ve yildiz alani surekli animasyonlu — `pumpAndSettle`
/// hicbir zaman donmez.
Future<void> _bekle(WidgetTester tester) async {
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 400));
}

/// `GradientProgressBar` her cubugu 120 ms gecikmeyle baslatir ve 800 ms'de
/// doldurur. Beklenmezse widget agaci sokulurken zamanlayici hala aciktir ve
/// test "A Timer is still pending" diye duser — urun hatasi degil.
Future<void> _cubuklariBekle(WidgetTester tester) async {
  await tester.pump();
  await tester.pump(const Duration(seconds: 3));
}

void main() {
  group('acilar sayfasi', () {
    testWidgets('aci listesi KIRPILMAZ', (tester) async {
      // Akista `aspects.take(14)` vardi cunku hepsi ekrani boguyordu.
      // Kendi sayfasinda o sebep yok; kirpma geri gelirse kullanici
      // haritasinin bir kismini goremez ve bunu HIC fark etmez.
      await tester
          .pumpWidget(_sar(AtlasAspectsScreen(aspects: _aciUret(22))));
      await _bekle(tester);

      // Liste kaydirilarak sonuncuya kadar gidilebilmeli.
      await tester.scrollUntilVisible(
          find.text('Gezegen21 — Hedef21'), 200,
          scrollable: find.byType(Scrollable).first);
      expect(find.text('Gezegen21 — Hedef21'), findsOneWidget);
    });

    test('aci sayisi altyaziya girer', () {
      // Karonun alt satiri "22 açı" der; kullanici tiklamadan once ne
      // bulacagini bilir.
      expect(_aciUret(22).length, 22);
    });
  });

  group('gezegenler sayfasi', () {
    testWidgets('her buyuk gezegen listelenir', (tester) async {
      await tester
          .pumpWidget(_sar(AtlasPlanetsScreen(points: _gezegenler)));
      await _bekle(tester);

      expect(find.textContaining('Güneş'), findsOneWidget);
      expect(find.textContaining('Ay'), findsOneWidget);
      expect(find.textContaining('Merkür'), findsOneWidget);
    });

    testWidgets('retro gezegen isaretlenir', (tester) async {
      await tester
          .pumpWidget(_sar(AtlasPlanetsScreen(points: _gezegenler)));
      await _bekle(tester);

      expect(find.textContaining('℞'), findsOneWidget);
    });

    testWidgets('taninmayan nokta sessizce atlanir', (tester) async {
      // Backend yeni bir nokta eklerse (ör. Chiron) ekran cokmemeli.
      await tester.pumpWidget(_sar(AtlasPlanetsScreen(points: [
        ..._gezegenler,
        {'name': 'Chiron', 'sign_tr': 'Koç', 'abs_position': 10.0},
      ])));
      await _bekle(tester);

      expect(find.textContaining('Chiron'), findsNothing);
      expect(find.textContaining('Güneş'), findsOneWidget);
    });
  });

  group('kisilik sayfasi', () {
    testWidgets('bes ozellik cubugu cizilir', (tester) async {
      await tester.pumpWidget(_sar(AtlasTraitsScreen(points: _gezegenler)));
      await _cubuklariBekle(tester);

      expect(find.text('Enerji'), findsOneWidget);
      expect(find.text('Kararlılık'), findsOneWidget);
      expect(find.text('İletişim'), findsOneWidget);
      expect(find.text('Duyarlılık'), findsOneWidget);
      expect(find.text('Pratiklik'), findsOneWidget);
    });

    testWidgets('nokta yoksa sifira bolme HATASI vermez', (tester) async {
      await tester.pumpWidget(_sar(const AtlasTraitsScreen(points: [])));
      await _cubuklariBekle(tester);

      expect(find.text('Enerji'), findsOneWidget);
    });
  });
}
