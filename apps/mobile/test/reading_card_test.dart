import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/l10n/app_localizations.dart';
import 'package:rytho/widgets/reading_card.dart';

/// `ReadingCard`'in varlik sebebi: uretilen metnin akisi UZATMAMASI.
///
/// Kullanici uygulamayi "insani yoran, dagitik" diye tarif etti ve olculdu:
/// Gokyuzu ~1500 px, Atlas ~2000 px. Bu uzunlugun buyuk kismi akisin icine
/// dokulmus sinirsiz AI metniydi — burc yorumu, kisisel okuma, tam natal
/// rapor.
///
/// Kural: akista uc satirdan uzun uretilmis metin duramaz. Asagidaki testler
/// o kurali koruyor. Ozellikle `metin uzadikca kart BUYUMEZ` testi: birinin
/// `maxLines`'i artirmasi ya da kaldirmasi cozdugumuz sorunu geri getirir ve
/// bu kimsenin gozune carpmaz — cunku ekran calismaya devam eder, sadece
/// yeniden uzar.

const _kisa = 'Bugun Ay Balik burcunda.';

/// Gercek bir gunluk okuma uzunlugu (~180-220 kelime hedefleniyor).
final _uzun = List.filled(
  60,
  'Bugun gokyuzunde belirgin bir gerilim var ve bu gerilim '
      'kararlarini hizlandirmaya calisacak. ',
).join();

Widget _sar(Widget child) => MaterialApp(
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: AppLocalizations.supportedLocales,
      locale: const Locale('tr'),
      home: Scaffold(body: child),
    );

void main() {
  group('akis kisa kalir', () {
    testWidgets('metin uzadikca kart BUYUMEZ', (tester) async {
      await tester.pumpWidget(
          _sar(const ReadingCard(title: 'Bugun', body: _kisa)));
      await tester.pumpAndSettle();
      final kisaYukseklik =
          tester.getSize(find.byType(ReadingCard)).height;

      await tester.pumpWidget(_sar(ReadingCard(title: 'Bugun', body: _uzun)));
      await tester.pumpAndSettle();
      final uzunYukseklik =
          tester.getSize(find.byType(ReadingCard)).height;

      // Uc satira kadar buyuyebilir, otesine gecemez. Sinirsiz metin
      // eskiden karti 300-400 px'e cikariyordu.
      expect(uzunYukseklik, lessThan(kisaYukseklik + 70),
          reason: 'kart metinle birlikte buyuyor — akis yine uzar');
      expect(uzunYukseklik, lessThan(230),
          reason: 'kart tek basina ekranin ucte birini yiyor');
    });

    test('onizleme satir siniri UC', () {
      // Sayinin kendisi sozlesme. Degistirmek isteyen once yukaridaki
      // aciklamayi okusun.
      const kart = ReadingCard(title: 'x', body: 'y');
      expect(kart.body, 'y');
    });

    testWidgets('uzun metin akista KIRPILIR', (tester) async {
      await tester.pumpWidget(_sar(ReadingCard(title: 'Bugun', body: _uzun)));
      await tester.pumpAndSettle();

      final metin = tester.widget<Text>(find.text(_uzun));
      expect(metin.maxLines, 3);
      expect(metin.overflow, TextOverflow.ellipsis);
    });
  });

  group('okuma sayfasi', () {
    testWidgets('karta dokununca TAM metin acilir', (tester) async {
      await tester.pumpWidget(_sar(ReadingCard(title: 'Bugun', body: _uzun)));
      await tester.pumpAndSettle();

      await tester.tap(find.byType(ReadingCard));
      // `pumpAndSettle` DEGIL: okuma sayfasi `CosmicScaffold` kullaniyor ve
      // onun yildiz alani surekli animasyonlu — hicbir zaman "durulmuyor".
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 400));

      expect(find.byType(ReadingScreen), findsOneWidget);

      // Okuma sayfasinda kirpma YOK.
      //
      // Metin artik markdown olarak COZULUYOR (R5-4): govde tek `Text`
      // degil, blok basina bir widget. Bu yuzden tam dizeyi arayan eski
      // iddia ise yaramaz — korunmasi gereken sey dizenin kimligi degil,
      // HICBIR govde satirinin kirpilmadigi.
      final govde = find.descendant(
          of: find.byType(ReadingScreen), matching: find.byType(Text));
      expect(govde, findsWidgets);
      for (final w in tester.widgetList<Text>(govde)) {
        expect(w.maxLines, isNull,
            reason: 'okuma sayfasinda metin kirpilmamali');
      }
      expect(
          find.descendant(
              of: find.byType(ReadingScreen),
              matching: find.textContaining('kararlarini hizlandirmaya')),
          findsOneWidget);
    });

    testWidgets('onOpen verilirse varsayilan sayfa acilmaz', (tester) async {
      var acildi = false;
      await tester.pumpWidget(_sar(ReadingCard(
        title: 'Bugun',
        body: _uzun,
        onOpen: () => acildi = true,
      )));
      await tester.pumpAndSettle();

      await tester.tap(find.byType(ReadingCard));
      await tester.pumpAndSettle();

      expect(acildi, isTrue);
      expect(find.byType(ReadingScreen), findsNothing);
    });
  });
}
