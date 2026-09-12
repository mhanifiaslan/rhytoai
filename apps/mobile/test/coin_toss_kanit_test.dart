// Kanıt çizimi (PZ2): CoinToss ressamını gerçek dokularla PNG'ye basar.
//
// Yalnız RYTHO_KANIT_DIR verilince koşar (normal `flutter test` atlar):
//   RYTHO_KANIT_DIR=<klasör> flutter test test/coin_toss_kanit_test.dart
// Üç kare: havada (t=0,3 s), iniş ortası (açılı paralar), yerde (k=2).
// Amaç görsel denetim — "şık, minimalist" hükmünü kod değil göz verir.
import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/theme/rytho_theme.dart';
import 'package:rytho/widgets/coin_toss.dart';

void main() {
  final hedef = Platform.environment['RYTHO_KANIT_DIR'];

  testWidgets('CoinToss kareleri PNG', (tester) async {
    if (hedef == null) return;
    tester.view.devicePixelRatio = 3.0;
    addTearDown(tester.view.reset);

    await tester.runAsync(CoinTextures.precache);
    expect(CoinTextures.peek(kCoinFaceAsset), isNotNull);

    final anahtar = GlobalKey();
    Widget sahne(int? k, int toss) => MaterialApp(
          home: Scaffold(
            backgroundColor: RythoColors.ink,
            body: Center(
              child: RepaintBoundary(
                key: anahtar,
                child: Container(
                  color: RythoColors.ink,
                  padding: const EdgeInsets.all(24),
                  child: CoinToss(logoUp: k, toss: toss),
                ),
              ),
            ),
          ),
        );

    Future<void> bas(String ad) async {
      final sinir =
          anahtar.currentContext!.findRenderObject()! as RenderRepaintBoundary;
      final resim = await tester.runAsync(() => sinir.toImage(pixelRatio: 3));
      final bayt = await tester.runAsync(
          () => resim!.toByteData(format: ui.ImageByteFormat.png));
      File('$hedef/$ad.png').writeAsBytesSync(bayt!.buffer.asUint8List());
    }

    await tester.pumpWidget(sahne(null, 0));
    await tester.pump(const Duration(milliseconds: 300));
    await bas('havada');

    await tester.pumpWidget(sahne(2, 0));
    await tester.pump(const Duration(milliseconds: 250));
    await bas('inis-ortasi');

    await tester.pump(const Duration(milliseconds: 900));
    await bas('yerde-k2');

    await tester.pumpWidget(sahne(0, 1));
    await tester.pump(const Duration(milliseconds: 900));
    await bas('yerde-k0');
  });
}
