import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/l10n/app_localizations.dart';
import 'package:rytho/widgets/big_three_reveal.dart';

/// R12-B1: Büyük Üçlü perdesi — onboarding'in kayıp finali.
///
/// pumpAndSettle YOK (perde altında sonsuz animatör yok ama kural geneldir);
/// süreli pump adımlarıyla mühürlerin ve butonun gelişi beklenir.
void main() {
  testWidgets('perde üç mührü açar, buton kapatır', (tester) async {
    await tester.pumpWidget(MaterialApp(
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: const [Locale('tr')],
      locale: const Locale('tr'),
      home: Builder(
        builder: (context) => Scaffold(
          body: TextButton(
            onPressed: () => showBigThreeReveal(context,
                sun: 'Kova ♒', moon: 'Balık ♓', ascendant: 'Koç ♈'),
            child: const Text('ac'),
          ),
        ),
      ),
    ));

    await tester.tap(find.text('ac'));
    await tester.pump();
    await tester.pump(const Duration(seconds: 3));

    // Profildeki "Kova ♒" biçimi ayrıştırılıp yerel ada çevrilmeli.
    expect(find.text('GÜNEŞ'), findsOneWidget);
    expect(find.text('Kova'), findsOneWidget);
    expect(find.text('Balık'), findsOneWidget);
    expect(find.text('Koç'), findsOneWidget);
    expect(find.text('Yolculuğa başla'), findsOneWidget);

    await tester.tap(find.text('Yolculuğa başla'));
    // Kapanış: bir kare pop'u başlatır, sonraki kareler ters geçişi bitirir.
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));
    await tester.pump(const Duration(milliseconds: 300));
    expect(find.text('GÜNEŞ'), findsNothing);
  });
}
