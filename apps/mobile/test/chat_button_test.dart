// Merkez sohbet düğmesi bekçileri (OT5).
//
// Kullanıcı seçimi: balon biçimli kap + "yazıyor" noktaları — ✦ glifi
// merkezi terk etti (satır içi "Rytho'ya sor" işaretlerinde yaşıyor).
// Ayrıca düğme ilk kez erişilebilirlik etiketi kazandı.
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/l10n/app_localizations.dart';
import 'package:rytho/widgets/chat_bubble_icon.dart';
import 'package:rytho/widgets/glass.dart';

Widget _dock({bool azalt = false, VoidCallback? onCenterTap}) => MaterialApp(
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: AppLocalizations.supportedLocales,
      locale: const Locale('tr'),
      home: MediaQuery(
        data: MediaQueryData(disableAnimations: azalt),
        child: Scaffold(
          bottomNavigationBar: CosmicDock(
            items: const [
              (icon: Icons.sunny, activeIcon: Icons.sunny, label: 'a'),
              (icon: Icons.map, activeIcon: Icons.map, label: 'b'),
              (icon: Icons.people, activeIcon: Icons.people, label: 'c'),
              (icon: Icons.person, activeIcon: Icons.person, label: 'd'),
            ],
            index: 0,
            onChanged: (_) {},
            onCenterTap: onCenterTap ?? () {},
          ),
        ),
      ),
    );

void main() {
  testWidgets('merkez düğme yazıyor-noktaları taşır, ✦ değil',
      (tester) async {
    await tester.pumpWidget(_dock());
    await tester.pump(const Duration(milliseconds: 100));
    expect(find.byType(TypingDotsGlyph), findsOneWidget);
    expect(find.text('✦'), findsNothing);
  });

  testWidgets('erişilebilirlik etiketi var ve dokunma çalışır',
      (tester) async {
    var acildi = 0;
    await tester.pumpWidget(_dock(onCenterTap: () => acildi++));
    await tester.pump(const Duration(milliseconds: 50));
    final dugme = find.bySemanticsLabel('Rytho ile sohbet et');
    expect(dugme, findsOneWidget);
    await tester.tap(dugme);
    expect(acildi, 1);
  });

  testWidgets('reduce-motion: noktalar durağan (t sabit), nefes durur',
      (tester) async {
    await tester.pumpWidget(_dock(azalt: true));
    await tester.pump(const Duration(milliseconds: 100));
    expect(find.byType(TypingDotsGlyph), findsOneWidget);
    final glif =
        tester.widget<TypingDotsGlyph>(find.byType(TypingDotsGlyph));
    expect(glif.t, 0.0);
    expect(tester.binding.transientCallbackCount, 0);
  });
}
