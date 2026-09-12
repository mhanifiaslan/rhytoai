// PZ2: paralar kodla sürülür — kinematik saf ve testli, widget geri
// çağrıları her atışta birer kez, reduce-motion'da hareket yok.
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/widgets/coin_toss.dart';

const _t = 2.6; // kCoinLoop saniye

Widget _sar(Widget child, {bool azalt = false}) => MaterialApp(
      home: MediaQuery(
        data: MediaQueryData(disableAnimations: azalt),
        child: Scaffold(body: Center(child: child)),
      ),
    );

CoinTossState _durum(WidgetTester tester) =>
    tester.state<CoinTossState>(find.byType(CoinToss));

/// Açı `2π` katı farkla aynı yüz/aynı görünüm sayılır.
void _ayniPoz(CoinPose a, CoinPose b) {
  expect(math.cos(a.angle), closeTo(math.cos(b.angle), 1e-9));
  expect(math.sin(a.angle), closeTo(math.sin(b.angle), 1e-9));
  expect(a.height, closeTo(b.height, 1e-9));
}

void main() {
  setUp(CoinTextures.reset);

  group('kinematik', () {
    test('havadaki döngü dikişsiz: pose(t) == pose(t + T), üç para', () {
      for (final t in [0.0, 0.37, 1.1, 2.59]) {
        for (var i = 0; i < 3; i++) {
          _ayniPoz(coinAirbornePose(t, i), coinAirbornePose(t + _t, i));
        }
      }
      expect(kCoinLoop.inMilliseconds / 1000, _t);
    });

    test('havada üç para aynı anda aynı pozda değil (faz farkı)', () {
      final p = [for (var i = 0; i < 3; i++) coinAirbornePose(0.4, i)];
      expect(p[0], isNot(equals(p[1])));
      expect(p[1], isNot(equals(p[2])));
    });

    test('hedef açı: logo için 0, arka için π (mod 2π); 1,5–2,5 tur ileride',
        () {
      for (final from in [0.0, 1.3, 4.0, -2.2, 17.9]) {
        for (final logo in [true, false]) {
          final hedef = coinTargetAngle(from, logoUp: logo);
          final kalan = hedef % (2 * math.pi);
          expect(kalan, closeTo(logo ? 0 : math.pi, 1e-9),
              reason: 'from=$from logo=$logo');
          expect(hedef - from, greaterThanOrEqualTo(3 * math.pi - 1e-9));
          expect(hedef - from, lessThan(5 * math.pi));
        }
      }
    });

    test('iniş: temas anında açı hedefte ve yerde; sonda yerde; yan durmaz',
        () {
      const from = CoinPose(angle: 2.0, height: 0.7);
      final temas = coinLandingPose(kCoinContactAt, from,
          logoUp: true, lift: false);
      expect(math.cos(temas.angle), closeTo(1, 1e-9));
      expect(temas.height, closeTo(0, 1e-9));
      final son = coinLandingPose(1.0, from, logoUp: false, lift: true);
      expect(math.cos(son.angle), closeTo(-1, 1e-9));
      expect(son.height, closeTo(0, 1e-9));
      // Yerleşme: tek küçük sekme, 0,10'u geçmez.
      for (var p = kCoinContactAt; p <= 1.0; p += 0.02) {
        final h = coinLandingPose(p, from, logoUp: true, lift: true).height;
        expect(h, inInclusiveRange(0, 0.1001));
      }
    });

    test('iniş: yerden kalkan para 1,0\'a çıkar; havadaki para tepesinden '
        'düşer (sıçrama yok)', () {
      const yerde = CoinPose(angle: 0, height: 0);
      final tepe = coinLandingPose(0.22, yerde, logoUp: true, lift: true);
      expect(tepe.height, closeTo(1.0, 1e-9));
      const havada = CoinPose(angle: 1.0, height: 0.9);
      final ilk = coinLandingPose(0.0, havada, logoUp: true, lift: false);
      expect(ilk.height, closeTo(0.9, 1e-9), reason: 'başlangıç sürekli');
      expect(ilk.angle, closeTo(1.0, 1e-9));
    });

    test('logo yüzüyle inecek paralar: k tane, atışla döner', () {
      expect(coinsLogoUp(0, 0), isEmpty);
      expect(coinsLogoUp(0, 3), {0, 1, 2});
      expect(coinsLogoUp(0, 2), {0, 1});
      expect(coinsLogoUp(1, 2), {1, 2});
      expect(coinsLogoUp(2, 2), {2, 0});
      expect(coinsLogoUp(5, 1), {2});
    });
  });

  group('CoinToss widget', () {
    testWidgets('reduce-motion: hareket yok; atışta son poz anında, '
        'onContact + onLanded kare bitince birer kez', (tester) async {
      var temas = 0, indi = 0;
      Widget w(int? k, int toss) => _sar(
          CoinToss(
              logoUp: k,
              toss: toss,
              onContact: () => temas++,
              onLanded: () => indi++),
          azalt: true);

      await tester.pumpWidget(w(null, 0));
      final st = _durum(tester);
      final havada = st.poses;
      await tester.pump(const Duration(seconds: 1));
      expect(st.poses, havada, reason: 'statik sahnede poz değişmez');
      expect(temas + indi, 0);

      await tester.pumpWidget(w(2, 0));
      expect(temas, 1);
      expect(indi, 1);
      final p = st.poses;
      expect(math.cos(p[0].angle), closeTo(1, 1e-9));
      expect(math.cos(p[1].angle), closeTo(1, 1e-9));
      expect(math.cos(p[2].angle), closeTo(-1, 1e-9));
      expect(p.every((x) => x.height == 0), isTrue);

      // Aynı k, yeni atış → geri çağrılar yine birer kez.
      await tester.pumpWidget(w(2, 1));
      expect(temas, 2);
      expect(indi, 2);
      expect(math.cos(st.poses[0].angle), closeTo(-1, 1e-9),
          reason: 'toss 1 → {1,2} logo');
    });

    testWidgets('hareketli: havada döner; atış 820 ms — temas %78\'de bir, '
        'bitiş bir; ikinci atış yeniden', (tester) async {
      var temas = 0, indi = 0;
      Widget w(int? k, int toss) => _sar(CoinToss(
          logoUp: k,
          toss: toss,
          onContact: () => temas++,
          onLanded: () => indi++));

      await tester.pumpWidget(w(null, 0));
      final st = _durum(tester);
      await tester.pump(const Duration(milliseconds: 300));
      final a = st.poses;
      await tester.pump(const Duration(milliseconds: 300));
      expect(st.poses, isNot(equals(a)), reason: 'havada hareket var');
      expect(st.isLanding, isFalse);

      await tester.pumpWidget(w(1, 0));
      expect(st.isLanding, isTrue);
      await tester.pump(const Duration(milliseconds: 600));
      expect(temas, 0, reason: '%78 = 640 ms — henüz değil');
      await tester.pump(const Duration(milliseconds: 100));
      expect(temas, 1);
      expect(indi, 0);
      await tester.pump(const Duration(milliseconds: 200));
      expect(indi, 1);
      expect(st.isLanding, isFalse);
      final p = st.poses;
      expect(math.cos(p[0].angle), closeTo(1, 1e-6), reason: 'toss 0, k=1');
      expect(math.cos(p[1].angle), closeTo(-1, 1e-6));
      expect(math.cos(p[2].angle), closeTo(-1, 1e-6));
      expect(p.every((x) => x.height.abs() < 1e-6), isTrue);

      // Poz tutulur; ticker durdu.
      await tester.pump(const Duration(seconds: 1));
      expect(st.poses, p);

      await tester.pumpWidget(w(0, 1));
      expect(st.isLanding, isTrue);
      await tester.pump(const Duration(milliseconds: 900));
      expect(temas, 2);
      expect(indi, 2);
      expect(st.poses.every((x) => math.cos(x.angle) < -0.999), isTrue,
          reason: 'k=0: üçü de arka yüz');
      expect(tester.takeException(), isNull);
    });

    testWidgets('sahne boyutu: 40 lp para → 148×62 lp (küçük, sessiz)',
        (tester) async {
      await tester.pumpWidget(_sar(const CoinToss()));
      final boyut = tester.getSize(find.byType(CoinToss));
      expect(boyut.width, closeTo(148, 0.01));
      expect(boyut.height, closeTo(62, 0.01));
    });
  });
}
