import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/widgets/atlas_widgets.dart' show ZodiacRing;
import 'package:rytho/widgets/motion.dart';

/// R12-A0 hareket altyapısının değişmezleri.
///
/// Kural: sonsuz repeat içeren ağaçta (AstrolabeSpinner) ASLA pumpAndSettle
/// çağrılmaz — süreli `pump` adımlarıyla ilerlenir; settle hiç bitmez.

Widget _sar(Widget child, {bool azalt = false}) => MaterialApp(
      home: MediaQuery(
        data: MediaQueryData(disableAnimations: azalt),
        child: Scaffold(body: child),
      ),
    );

void main() {
  group('RythoReveal', () {
    testWidgets('normalde animasyon zinciri kurulur', (tester) async {
      await tester.pumpWidget(
          _sar(const RythoReveal(index: 1, child: Text('selamlik'))));
      expect(find.byType(Animate), findsOneWidget);
      // Gecikme + giriş sonunda metin tam görünür.
      await tester.pump(const Duration(milliseconds: 700));
      expect(find.text('selamlik'), findsOneWidget);
    });

    testWidgets('reduce-motion açıkken çocuk ÇIPLAK döner', (tester) async {
      // Geciken görünmezlik, animasyonsuzluktan daha rahatsız edicidir:
      // kapı açıkken stagger gecikmesi dahil hiçbir şey kurulmamalı.
      await tester.pumpWidget(_sar(
          const RythoReveal(index: 5, child: Text('sabit')),
          azalt: true));
      expect(find.byType(Animate), findsNothing);
      expect(find.text('sabit'), findsOneWidget);
    });
  });

  group('StagedWaiting', () {
    testWidgets('aşamalar sırayla ilerler ve SONDA DURUR', (tester) async {
      await tester.pumpWidget(_sar(const StagedWaiting(
          stages: ['bir', 'iki', 'üç'],
          interval: Duration(milliseconds: 500))));
      expect(find.text('bir'), findsOneWidget);

      await tester.pump(const Duration(milliseconds: 600));
      await tester.pump(const Duration(milliseconds: 400));
      expect(find.text('iki'), findsOneWidget);

      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump(const Duration(milliseconds: 400));
      expect(find.text('üç'), findsOneWidget);

      // Döngü YOK: uzun süre sonra hâlâ son aşama — başa saran metin
      // "takıldı" hissi verirdi (yüz okuma sahnesinin kuralı).
      await tester.pump(const Duration(seconds: 3));
      await tester.pump(const Duration(milliseconds: 400));
      expect(find.text('üç'), findsOneWidget);
      expect(find.text('bir'), findsNothing);
    });

    testWidgets('tek aşamalı kullanım çökmeden durur', (tester) async {
      await tester.pumpWidget(
          _sar(const StagedWaiting(stages: ['bekle'])));
      expect(find.text('bekle'), findsOneWidget);
      await tester.pump(const Duration(seconds: 6));
      expect(find.text('bekle'), findsOneWidget);
    });
  });

  group('ZodiacRing reduce-motion (OT5 sürüklenme onarımı)', () {
    testWidgets('kapı açıkken nefes denetleyicisi DURUR', (tester) async {
      // Kusur: _breath, reduceMotion kapısı olmadan sonsuza dek dönüyordu
      // (_CenterAiButton deseninin eksik kopyası). Ölçü: kare zamanlayıcı
      // sayacı — dönen denetleyici sürekli geri çağrı tutar.
      await tester.pumpWidget(_sar(
          const ZodiacRing(planets: [], size: 120), azalt: true));
      await tester.pump(const Duration(milliseconds: 100));
      expect(tester.binding.transientCallbackCount, 0,
          reason: 'reduce-motion altında dönen animasyon kalmamalı');
    });

    testWidgets('normalde nefes alır', (tester) async {
      await tester.pumpWidget(
          _sar(const ZodiacRing(planets: [], size: 120)));
      await tester.pump(const Duration(milliseconds: 100));
      expect(tester.binding.transientCallbackCount, greaterThan(0));
    });
  });
}
