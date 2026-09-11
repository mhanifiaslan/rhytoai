import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart' show SchedulerBinding, SchedulerPhase;
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/features/oracle/iching_tab.dart';
import 'package:rytho/l10n/app_localizations.dart';
import 'package:rytho/widgets/frame_sequence.dart';
import 'package:rytho/widgets/nebula_widgets.dart' show Pressable;

/// PBZ 1.2: atış sahnesi — varyant eşlemesi ve durum makinesi.
///
/// Sahne gerçek varlıkları (`assets/anim/coins_*.webp`, rootBundle) açar ama
/// durum makinesi çözmeye BAĞLI DEĞİL: reduce-motion'da her iniş post-frame
/// biter, normalde döngü sınırı ya da 2,5 s emniyet zamanlayıcısı indirir.
/// Bu yüzden `runAsync` YOK — gerçek olay döngüsü açılsaydı google_fonts'un
/// asenkron font hatası teste sızardı (chart_wheel_test.dart notu).
/// Ticker içeren ağaçta pumpAndSettle YOK — süreli pump adımları.

Widget _sar(Widget child, {bool azalt = false}) => MaterialApp(
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: const [Locale('tr')],
      locale: const Locale('tr'),
      home: MediaQuery(
        data: MediaQueryData(disableAnimations: azalt),
        child: Scaffold(
          body: Padding(padding: const EdgeInsets.all(16), child: child),
        ),
      ),
    );

/// Koşul sağlanana dek süreli pump (post-frame / zamanlayıcı ilerlesin);
/// en çok 60 adım.
Future<void> _ilerlet(WidgetTester tester, bool Function() hazir,
    {Duration adim = Duration.zero}) async {
  for (var i = 0; i < 60 && !hazir(); i++) {
    await tester.pump(adim);
  }
  expect(hazir(), isTrue, reason: 'zaman aşımı');
  await tester.pump();
}

CastSceneState _sahne(WidgetTester tester) =>
    tester.state<CastSceneState>(find.byType(CastScene));

void main() {
  group('landingVariants', () {
    test('6/7/8/9 → 0/1/2/3, sıra korunur (alttan üste)', () {
      expect(landingVariants([6, 7, 8, 9, 7, 8]), [0, 1, 2, 3, 1, 2]);
      expect(landingVariants([]), isEmpty);
    });

    test('aralık dışı ArgumentError', () {
      expect(() => landingVariants([6, 5]), throwsArgumentError);
      expect(() => landingVariants([10]), throwsArgumentError);
      expect(() => landingVariants([0]), throwsArgumentError);
    });
  });

  group('CastScene', () {
    testWidgets(
        'reduce-motion: 6 iniş anında biter, revealed=6, onFinished bir kez, '
        'clink BİR kez', (tester) async {
      var bitti = 0, inis = 0;
      Widget sahne(List<int>? degerler) => _sar(
          CastScene(
            lineValues: degerler,
            onFinished: () => bitti++,
            onLand: () async => inis++,
          ),
          azalt: true);

      // Havada: etiket "havada", glif boş, hiç iniş yok.
      await tester.pumpWidget(sahne(null));
      expect(find.text('Paralar havada...'), findsOneWidget);
      final st = _sahne(tester);
      expect(st.revealed, 0);
      expect(bitti, 0);
      expect(inis, 0);

      // Yanıt geldi (didUpdateWidget yolu): statik sahnede sınır beklenmez.
      await tester.pumpWidget(sahne(const [6, 7, 8, 9, 7, 8]));
      expect(st.isLanding || st.isDone, isTrue);
      expect(inis, 1, reason: 'ilk klip başında clink');

      // Her iniş bir post-frame: süreli bekleyiş YOK, çözme beklenmez.
      await _ilerlet(tester, () => st.isDone);
      expect(st.revealed, 6);
      expect(bitti, 1);
      // Statik sahnede altı iniş ~6 karede biter; altı clink üst üste
      // binerdi (F6) — yalnız İLK inişte çalar.
      expect(inis, 1, reason: 'reduce-motion: clink yalnız ilk inişte');
      expect(find.text('Paralar düşüyor… 6/6'), findsOneWidget);

      // Sonradan hiçbir şey tekrar tetiklenmez.
      await tester.pump(const Duration(seconds: 3));
      await tester.pump(const Duration(seconds: 3));
      expect(bitti, 1);
      expect(inis, 1);
    });

    testWidgets('iniş sırasında tepsiye dokunma done\'a atlar; onFinished bir kez',
        (tester) async {
      var bitti = 0;
      Widget sahne(List<int>? degerler) => _sar(CastScene(
            lineValues: degerler,
            onFinished: () => bitti++,
            onLand: () async {},
          ));

      await tester.pumpWidget(sahne(null));
      expect(find.byType(FrameSequence), findsOneWidget);

      // Yanıt geldi: iniş ancak döngü SINIRINDA başlar (kesme yok). Sahte
      // zamanda native çözme hiç bitmez → sınır gelmez; 2,5 s emniyet
      // zamanlayıcısı indirir — süreli pump ile geçilir.
      await tester.pumpWidget(sahne(const [7, 7, 7, 7, 7, 7]));
      final st = _sahne(tester);
      expect(st.isLanding, isFalse, reason: 'sınır beklenir');
      await tester.pump(const Duration(seconds: 2));
      expect(st.isLanding, isFalse, reason: 'emniyet 2,5 s — henüz değil');
      await _ilerlet(tester, () => st.isLanding,
          adim: const Duration(milliseconds: 100));
      expect(bitti, 0);
      expect(find.text('Paralar düşüyor… 1/6'), findsOneWidget);

      await tester.tap(find.byType(Pressable));
      await tester.pump();
      expect(st.isDone, isTrue);
      expect(st.revealed, 6);
      expect(bitti, 1);

      // Kalan klip dursa da onFinished tekrar gelmez; bekleyen zamanlayıcı yok.
      await tester.pump(const Duration(seconds: 3));
      await tester.pump(const Duration(seconds: 3));
      expect(bitti, 1);
    });

    // F5: gerçek kullanımda onFinished/onLand ÜSTTEKİ _IChingTabState'te
    // setState çağırır. _emdir didChangeDependencies / didUpdateWidget
    // içinde — yani build fazında — koşar; oradan doğrudan üst setState
    // "setState() called during build" assertion'ıyla düşerdi. Sarmalayıcı
    // StatefulBuilder o atayı canlandırır: geri çağrı kare BİTİNCE
    // (SchedulerPhase.postFrameCallbacks) ve bir kez gelmeli, hata yok.
    testWidgets(
        'bozuk sunucu değeri (monte yolu): kare bitince onFinished bir kez, '
        'üstteki setState assertion vermez', (tester) async {
      var bitti = 0;
      SchedulerPhase? faz;
      await tester.pumpWidget(_sar(
          StatefulBuilder(
            builder: (context, ustSetState) => CastScene(
              lineValues: const [6, 7, 8, 42, 7, 8],
              onFinished: () {
                faz = SchedulerBinding.instance.schedulerPhase;
                ustSetState(() => bitti++);
              },
              onLand: () async {},
            ),
          ),
          azalt: true));
      expect(tester.takeException(), isNull,
          reason: 'build fazında üst setState → assertion (F5)');
      expect(bitti, 1);
      expect(faz, SchedulerPhase.postFrameCallbacks,
          reason: 'onFinished karenin ardından gelmeli');
      await tester.pump();
      expect(_sahne(tester).isDone, isTrue);
      await tester.pump(const Duration(seconds: 3));
      await tester.pump(const Duration(seconds: 3));
      expect(bitti, 1);
      expect(tester.takeException(), isNull);
    });

    testWidgets(
        'boş satır değerleri (didUpdateWidget yolu): kare bitince onFinished '
        'bir kez, üstteki setState assertion vermez', (tester) async {
      var bitti = 0;
      SchedulerPhase? faz;
      Widget sahne(List<int>? degerler) => _sar(StatefulBuilder(
            builder: (context, ustSetState) => CastScene(
              lineValues: degerler,
              onFinished: () {
                faz = SchedulerBinding.instance.schedulerPhase;
                ustSetState(() => bitti++);
              },
              onLand: () async {},
            ),
          ));

      await tester.pumpWidget(sahne(null));
      final st = _sahne(tester);
      expect(bitti, 0);

      // Yanıtta `cast` yok → _lineValues boş liste verir: inecek para yok.
      await tester.pumpWidget(sahne(const []));
      expect(tester.takeException(), isNull,
          reason: 'build fazında üst setState → assertion (F5)');
      expect(bitti, 1);
      expect(faz, SchedulerPhase.postFrameCallbacks);
      await tester.pump();
      expect(st.isDone, isTrue);
      await tester.pump(const Duration(seconds: 3));
      await tester.pump(const Duration(seconds: 3));
      expect(bitti, 1);
      expect(tester.takeException(), isNull);
    });

    testWidgets(
        'reduce-motion + geçerli yanıt (didUpdateWidget yolu): ilk clink ve '
        'onFinished üstte setState çağırsa da assertion yok', (tester) async {
      var bitti = 0, inis = 0;
      Widget sahne(List<int>? degerler) => _sar(
          StatefulBuilder(
            builder: (context, ustSetState) => CastScene(
              lineValues: degerler,
              onFinished: () => ustSetState(() => bitti++),
              onLand: () async => ustSetState(() => inis++),
            ),
          ),
          azalt: true);

      await tester.pumpWidget(sahne(null));
      final st = _sahne(tester);
      // Statik sahnede _emdir hemen inişe geçer: onLand build fazında
      // çağrılsaydı üst setState düşerdi.
      await tester.pumpWidget(sahne(const [7, 7, 7, 7, 7, 7]));
      expect(tester.takeException(), isNull);
      expect(inis, 1);
      await _ilerlet(tester, () => st.isDone);
      expect(tester.takeException(), isNull);
      expect(bitti, 1);
      expect(inis, 1);
      expect(st.revealed, 6);
    });
  });
}
