import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/l10n/app_localizations.dart';
import 'package:rytho/theme/rytho_theme.dart';
import 'package:rytho/widgets/atlas_widgets.dart';
import 'package:rytho/widgets/glass.dart';

/// Asama A5'in degismezleri.
///
/// ## 1. Segment buton gibi GORUNMEZ
///
/// Secili segment `primaryGradient` + `goldGlow` aliyordu; yani birincil
/// butonla birebir ayni gorsel muamele. Kullanicinin ifadesi:
///
/// > "giris yap, uye ol tab isimleri giris yap butonlarina benziyor ve
/// > tiklanilarak girilecegini cagristiriyor, bu yanlis bir his."
///
/// Segment bir DURUM gostergesi, buton bir EYLEM. Degrade ve glow yalnizca
/// eyleme ait.
///
/// ## 2. Ekranda tek birincil buton
///
/// E-posta, Apple ve Google butonlari birebir ayni degradede alt alta
/// duruyordu. Bir ekranda birden fazla "birincil" varsa hicbiri birincil
/// degildir.

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

/// Verilen dalda degrade dolgusu kullanan kutu sayisi.
int _degradeSayisi(WidgetTester tester, Finder kok) {
  var n = 0;
  for (final e in tester.widgetList(find.descendant(
      of: kok, matching: find.byType(AnimatedContainer)))) {
    final d = (e as AnimatedContainer).decoration;
    if (d is BoxDecoration && d.gradient != null) n++;
  }
  for (final e in tester.widgetList(
      find.descendant(of: kok, matching: find.byType(Container)))) {
    final d = (e as Container).decoration;
    if (d is BoxDecoration && d.gradient != null) n++;
  }
  return n;
}

void main() {
  group('segment secici', () {
    testWidgets('secili segment DEGRADE kullanmaz', (tester) async {
      await tester.pumpWidget(_sar(GlassSegments(
        labels: const ['Giriş yap', 'Üye ol'],
        index: 0,
        onChanged: (_) {},
      )));
      await tester.pumpAndSettle();

      expect(_degradeSayisi(tester, find.byType(GlassSegments)), 0,
          reason: 'segment yine butona benziyor');
    });

    testWidgets('secili segment GLOW kullanmaz', (tester) async {
      await tester.pumpWidget(_sar(GlassSegments(
        labels: const ['Giriş yap', 'Üye ol'],
        index: 1,
        onChanged: (_) {},
      )));
      await tester.pumpAndSettle();

      final golgeli = tester
          .widgetList<AnimatedContainer>(find.descendant(
              of: find.byType(GlassSegments),
              matching: find.byType(AnimatedContainer)))
          .where((c) {
        final d = c.decoration;
        return d is BoxDecoration && (d.boxShadow?.isNotEmpty ?? false);
      });
      expect(golgeli, isEmpty, reason: 'glow yalnizca eyleme ait');
    });

    testWidgets('secim yine de GORULEBILIR', (tester) async {
      // Ayrimi silmek de hata olurdu: kullanici hangi sekmede oldugunu
      // gormeli. Degrade yerine ince zemin farki var.
      await tester.pumpWidget(_sar(GlassSegments(
        labels: const ['Giriş yap', 'Üye ol'],
        index: 0,
        onChanged: (_) {},
      )));
      await tester.pumpAndSettle();

      final dolgular = tester
          .widgetList<AnimatedContainer>(find.descendant(
              of: find.byType(GlassSegments),
              matching: find.byType(AnimatedContainer)))
          .map((c) => (c.decoration as BoxDecoration?)?.color)
          .toList();
      expect(dolgular.where((c) => c != null).length, 1,
          reason: 'secili segment ayirt edilemiyor');
    });

    testWidgets('dokununca secim degisir', (tester) async {
      var secilen = -1;
      await tester.pumpWidget(_sar(GlassSegments(
        labels: const ['Giriş yap', 'Üye ol'],
        index: 0,
        onChanged: (i) => secilen = i,
      )));
      await tester.pumpAndSettle();

      await tester.tap(find.text('Üye ol'));
      expect(secilen, 1);
    });
  });

  group('buton hiyerarsisi', () {
    testWidgets('ikincil buton degrade ve glow ALMAZ', (tester) async {
      await tester.pumpWidget(_sar(Column(children: [
        GoldButton(text: 'Birincil', onPressed: () {}),
        GoldButton(text: 'Ikincil', filled: false, onPressed: () {}),
      ])));
      await tester.pumpAndSettle();

      final kutular = tester
          .widgetList<Container>(find.descendant(
              of: find.byType(GoldButton), matching: find.byType(Container)))
          .toList();
      final degradeli = kutular.where((c) {
        final d = c.decoration;
        return d is BoxDecoration && d.gradient != null;
      });
      // Iki butondan YALNIZCA biri degrade aliyor.
      expect(degradeli.length, 1,
          reason: 'ikincil varyant yine birincil gibi cizilyor');
    });

    testWidgets('ikincil buton metni okunur kaliyor', (tester) async {
      await tester.pumpWidget(_sar(
          GoldButton(text: 'Google ile devam et', filled: false,
              onPressed: () {})));
      await tester.pumpAndSettle();

      final metin = tester.widget<Text>(find.text('Google ile devam et'));
      expect(metin.style?.color, RythoColors.parchment);
    });

    testWidgets('mesgulken tekrar basilamaz', (tester) async {
      // Sosyal giris butonlari `busy` iken de ekranda duruyor. Ikinci
      // dokunus ikinci bir OAuth akisi baslatirdi.
      var sayac = 0;
      await tester.pumpWidget(_sar(GoldButton(
        text: 'Gonder',
        busy: true,
        onPressed: () => sayac++,
      )));
      await tester.pump();

      await tester.tap(find.byType(GoldButton), warnIfMissed: false);
      await tester.pump();
      expect(sayac, 0, reason: 'mesgul buton yine tetikleniyor');
    });

    testWidgets('acikken bir kez tetiklenir', (tester) async {
      // Yukaridaki testin gercekten bir sey olctugunu gosteren karsit
      // durum: ayni kurulum `busy: false` iken sayaci artirmali.
      var sayac = 0;
      await tester.pumpWidget(_sar(GoldButton(
        text: 'Gonder',
        onPressed: () => sayac++,
      )));
      await tester.pump();

      await tester.tap(find.byType(GoldButton));
      await tester.pump();
      expect(sayac, 1);
    });
  });
}
