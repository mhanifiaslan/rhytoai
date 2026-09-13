// Kanıt çizimi: sohbet ikonunu (ChatBubblesIcon) gerçek ressamından PNG'ye
// basar — görsel denetim kodla değil gözle yapılır.
//
// Yalnız RYTHO_KANIT_DIR verilince koşar (normal `flutter test` atlar):
//   RYTHO_KANIT_DIR=<klasör> flutter test test/sohbet_ikonu_kanit_test.dart
//
// Basılan kareler:
//   sohbet-ikonu-62.png   — dock boyu, üç faz yan yana (animasyon ne yapıyor)
//   sohbet-ikonu-24.png   — satır içi boy + 3 kat büyütülmüş kopyası
//   sohbet-ikonu-dock.png — gerçek dock bağlamı (koyu şerit + yer tutucular)
//
// Testte gerçek yazı tipi yoktur (her harf punto kadar kare çizilir); bu
// yüzden karelerde metin kullanılmaz.
library;

import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/theme/rytho_theme.dart';
import 'package:rytho/widgets/chat_bubble_icon.dart';

const double _kenar = 24;
const double _aralik = 28;

/// Okunur faz — durağan karelerde bu kullanılır.
const double _fazOrta = 0.35;

void main() {
  final hedef = Platform.environment['RYTHO_KANIT_DIR'];

  testWidgets('sohbet ikonu kareleri', (tester) async {
    if (hedef == null) return;
    tester.view.devicePixelRatio = 3;
    tester.view.physicalSize = const Size(1600, 1600);
    addTearDown(tester.view.reset);

    final anahtar = GlobalKey();

    Future<void> bas(String ad, Widget icerik) async {
      await tester.pumpWidget(MaterialApp(
        home: MediaQuery(
          // Hareketi biz sürüyoruz (t parametresi); denetleyici kurulmasın.
          data: const MediaQueryData(disableAnimations: true),
          child: Scaffold(
            backgroundColor: RythoColors.ink,
            body: Center(
              child: RepaintBoundary(
                key: anahtar,
                child: Container(
                  color: RythoColors.ink,
                  padding: const EdgeInsets.all(_kenar),
                  child: icerik,
                ),
              ),
            ),
          ),
        ),
      ));
      await tester.pump();
      final sinir =
          anahtar.currentContext!.findRenderObject()! as RenderRepaintBoundary;
      final resim = await tester.runAsync(() => sinir.toImage(pixelRatio: 3));
      final bayt = await tester.runAsync(
          () => resim!.toByteData(format: ui.ImageByteFormat.png));
      File('$hedef/$ad.png').writeAsBytesSync(bayt!.buffer.asUint8List());
    }

    // 1 — dock boyu, üç faz: animasyonun tamamı tek bakışta.
    await bas(
        'sohbet-ikonu-62',
        const Row(mainAxisSize: MainAxisSize.min, children: [
          ChatBubblesIcon(t: 0.0),
          SizedBox(width: _aralik),
          ChatBubblesIcon(t: _fazOrta),
          SizedBox(width: _aralik),
          ChatBubblesIcon(t: 0.7),
        ]));

    // 2 — satır içi boy: 24 px ve 3 kat büyütülmüş hâli yan yana.
    await bas(
        'sohbet-ikonu-24',
        const Row(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              ChatBubblesIcon(t: _fazOrta, size: 24),
              SizedBox(width: _aralik * 2),
              ChatBubblesIcon(t: _fazOrta, size: 72),
            ]));

    // 3 — dock bağlamı: koyu şerit, dört yer tutucu, ortada düğme.
    await bas(
        'sohbet-ikonu-dock',
        SizedBox(
          width: 390 - _kenar * 2,
          height: 96,
          child: Stack(alignment: Alignment.center, children: [
            Positioned(
              left: 0,
              right: 0,
              bottom: 0,
              height: 64,
              child: Container(
                decoration: BoxDecoration(
                  color: RythoColors.inkLight,
                  borderRadius: BorderRadius.circular(22),
                  border: Border.all(color: RythoColors.glassStroke),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    for (var i = 0; i < 5; i++)
                      i == 2
                          ? const SizedBox(width: 62)
                          : Container(
                              width: 22,
                              height: 22,
                              decoration: BoxDecoration(
                                color: RythoColors.lilac
                                    .withValues(alpha: 0.45),
                                borderRadius: BorderRadius.circular(6),
                              ),
                            ),
                  ],
                ),
              ),
            ),
            const Positioned(
                bottom: 26, child: ChatBubblesIcon(t: _fazOrta)),
          ]),
        ));
  });
}
