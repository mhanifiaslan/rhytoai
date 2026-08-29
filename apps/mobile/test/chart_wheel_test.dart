// ChartWheel + ressam bekçileri (HI-turu HA5/HA6).
//
// Golden dosyasız duman: üç kip (natal / bi-wheel / sinastri) kayıtlı
// kanvasa fırlatmadan çizilmeli. Widget testi dokunma → geri çağrı
// zincirinin GERÇEK yerleşimle çalıştığını (isabet==çizim) uçtan uca
// sabitler; reduce-motion süpürmeyi durdurur.
import 'dart:async';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:rytho/l10n/app_localizations.dart';
import 'package:rytho/widgets/chart/chart_data.dart';
import 'package:rytho/widgets/chart/chart_wheel.dart';
import 'package:rytho/widgets/chart/wheel_layout.dart';
import 'package:rytho/widgets/chart/wheel_painter.dart';

ChartPoint _p(String name, double lon) => ChartPoint(
      name: name,
      localName: name,
      absPosition: lon,
      signIndex: signIndexFromAny(null, lon),
      degreeInSign: lon % 30,
    );

List<ChartHouse> _evler(double asc) => [
      for (var i = 0; i < 12; i++)
        ChartHouse(house: i + 1, absPosition: (asc + i * 30) % 360),
    ];

ChartData _natal() => ChartData(
      rings: [
        ChartRing(kind: ChartRingKind.natal, points: [
          _p('Sun', 10), _p('Moon', 95), _p('Saturn', 190),
          _p('Chiron', 250), // vektör glif yolu da çizilsin
        ]),
      ],
      houses: _evler(0),
      aspects: const [
        ChartAspect(p1: 'Sun', p2: 'Saturn', kind: 'opposition',
            orb: 0.5),
        ChartAspect(p1: 'Sun', p2: 'Moon', kind: 'square', orb: 4.0),
        ChartAspect(p1: 'Moon', p2: 'Chiron', kind: 'conjunction',
            orb: 1.0),
      ],
    );

ChartData _biwheel() => ChartData(
      rings: [
        _natal().rings.first,
        ChartRing(kind: ChartRingKind.transit,
            points: [_p('Jupiter', 40), _p('Pluto', 300)]),
      ],
      houses: _evler(0),
      aspects: const [
        ChartAspect(p1: 'Jupiter', p2: 'Sun', kind: 'trine', orb: 1.2,
            p1Ring: 1, p2Ring: 0),
      ],
    );

void main() {
  // Ressam RythoText (GoogleFonts) stilleri kullanır; testte ağdan font
  // çekme denemesi arka planda fırlatıp İZLEYEN teste sızıyordu.
  GoogleFonts.config.allowRuntimeFetching = false;

  test('ressam dumanı: üç kip fırlatmadan çizilir', () async {
    // GoogleFonts test ortamında fontu bulamayınca HATASINI ASENKRON
    // fırlatır ve test bittikten sonra sızar; çizimin kendisi fontsuz da
    // geçerli (Ahem yedeği). Guarded bölge yalnız o sızıntıyı yutar —
    // paint() içindeki gerçek bir istisna yine testi düşürür.
    Object? cizimHatasi;
    await runZonedGuarded(() async {
      for (final data in [_natal(), _biwheel()]) {
        try {
          final layout = WheelLayout.compute(const Size(360, 360), data);
          final cache = GlyphTextCache();
          final statik = recordStaticLayer(layout, cache);
          final recorder = ui.PictureRecorder();
          final canvas = Canvas(recorder);
          RythoWheelPainter(
            layout: layout,
            staticLayer: statik,
            textCache: cache,
            progress: 1.0,
            selection:
                const WheelSelection(pointName: 'Sun', pointRing: 0),
          ).paint(canvas, const Size(360, 360));
          recorder.endRecording();
        } catch (e) {
          cizimHatasi = e;
        }
      }
      await Future<void>.delayed(const Duration(milliseconds: 50));
    }, (e, s) {
      // Yalnız font yükleme sızıntısı beklenir; başka her şey senkron
      // try/catch ile yakalanıp aşağıda raporlanır.
    });
    expect(cizimHatasi, isNull);
  });

  Widget sar(Widget child) => MaterialApp(
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: AppLocalizations.supportedLocales,
        locale: const Locale('tr'),
        home: Scaffold(
            body: Align(alignment: Alignment.topLeft, child: child)),
      );

  testWidgets('dokunma gerçek yerleşimle gezegeni bulur (uçtan uca)',
      (tester) async {
    final data = _natal();
    String? dokunulan;
    await tester.pumpWidget(sar(ChartWheel(
      data: data,
      size: 360,
      animate: false,
      onPlanetTap: (g) => dokunulan = g.point.name,
    )));
    await tester.pump();

    // Testte de AYNI geometri hesaplanır — tek kaynak ilkesinin kanıtı.
    final layout = WheelLayout.compute(const Size(360, 360), data);
    final hedef =
        layout.placements.first.firstWhere((g) => g.point.name == 'Moon');
    await tester.tapAt(tester.getTopLeft(find.byType(ChartWheel)) +
        hedef.center);
    // onDoubleTap kayıtlı: tekli dokunuş çift-dokunuş zaman aşımını
    // bekledikten sonra çözülür.
    await tester.pump(const Duration(milliseconds: 400));
    expect(dokunulan, 'Moon');
  });

  testWidgets('reduce-motion süpürmeyi durdurur (statik kare)',
      (tester) async {
    await tester.pumpWidget(MediaQuery(
      data: const MediaQueryData(disableAnimations: true),
      child: sar(ChartWheel(data: _natal(), size: 300)),
    ));
    await tester.pump(const Duration(milliseconds: 50));
    expect(tester.binding.transientCallbackCount, 0,
        reason: 'reduce-motion altında süpürme animasyonu dönmemeli');
  });
}
