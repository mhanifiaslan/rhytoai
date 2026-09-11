import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/widgets/frame_sequence.dart';

/// PBZ: kare dizisi değişmezleri — hepsi bellek içi fixture ile
/// (`FrameSequence.memory`); pubspec kaydından ve varlık dosyalarından
/// bağımsız.
///
/// Fixture: ffmpeg ile BİR kez üretilmiş 8×8, 2 kareli (kırmızı → mavi),
/// kare başına 100 ms animasyonlu WebP (148 bayt). Dosya olarak tutulmaz;
/// baytlar burada. (`color=red/blue:s=8x8:r=10` → `concat` → `libwebp_anim
/// -lossless 1 -loop 0`.)
///
/// Kurallar: Ticker içeren ağaçta pumpAndSettle YOK — süreli pump adımları.
/// Kod çözme native ve GERÇEK olay döngüsünde biter; FakeAsync onu
/// ilerletmez, bu yüzden her çözme `tester.runAsync` ile beklenir.
const _fixtureBaytlari = <int>[
  0x52, 0x49, 0x46, 0x46, 0x8c, 0x00, 0x00, 0x00, 0x57, 0x45, 0x42, 0x50,
  0x56, 0x50, 0x38, 0x58, 0x0a, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00,
  0x07, 0x00, 0x00, 0x07, 0x00, 0x00, 0x41, 0x4e, 0x49, 0x4d, 0x06, 0x00,
  0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0x00, 0x00, 0x41, 0x4e, 0x4d, 0x46,
  0x2c, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x07, 0x00,
  0x00, 0x07, 0x00, 0x00, 0x64, 0x00, 0x00, 0x02, 0x56, 0x50, 0x38, 0x4c,
  0x14, 0x00, 0x00, 0x00, 0x2f, 0x07, 0xc0, 0x01, 0x00, 0x07, 0x10, 0xf5,
  0x8f, 0xfe, 0x07, 0x00, 0x82, 0xf0, 0xff, 0xed, 0x21, 0xa2, 0xff, 0x21,
  0x41, 0x4e, 0x4d, 0x46, 0x2c, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x07, 0x00, 0x00, 0x07, 0x00, 0x00, 0x64, 0x00, 0x00, 0x00,
  0x56, 0x50, 0x38, 0x4c, 0x14, 0x00, 0x00, 0x00, 0x2f, 0x07, 0xc0, 0x01,
  0x00, 0x07, 0x10, 0xd1, 0xff, 0xfe, 0x07, 0x00, 0x82, 0xf0, 0xff, 0xed,
  0x21, 0xa2, 0xff, 0x21,
];

final kFixture = Uint8List.fromList(_fixtureBaytlari);
const kKare = Duration(milliseconds: 100);

Widget _sar(Widget child, {bool azalt = false}) => MaterialApp(
      home: MediaQuery(
        data: MediaQueryData(disableAnimations: azalt),
        child: Scaffold(
          body: SizedBox(width: 80, height: 50, child: child),
        ),
      ),
    );

/// Native çözme bitene dek gerçek zamanda bekler (en çok ~2 s), sonra bir
/// kare pump'lar (setState / post-frame callback'ler işlesin).
Future<void> _cozulsun(WidgetTester tester, bool Function() hazir) async {
  for (var i = 0; i < 100 && !hazir(); i++) {
    await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 20)));
    await tester.pump();
  }
  expect(hazir(), isTrue, reason: 'çözme zaman aşımı');
  await tester.pump();
}

FrameSequenceState _durum(WidgetTester tester) =>
    tester.state<FrameSequenceState>(find.byType(FrameSequence));

void main() {
  testWidgets('reduce-motion: SON kare statik, onDone bir kez, onLoop hiç',
      (tester) async {
    var done = 0, loop = 0;
    await tester.pumpWidget(_sar(
        FrameSequence.memory(
            bytes: kFixture,
            loop: true,
            onDone: () => done++,
            onLoop: () => loop++),
        azalt: true));
    final st = _durum(tester);
    // Bitiş çözmeye bağlı değil: ilk karenin post-frame'inde onDone.
    expect(st.isDone, isTrue);
    expect(done, 1, reason: 'onDone post-frame, hemen ve bir kez');
    // Arka planda frameCount−1 kez ilerler: 2 karelik yükte indeks 1.
    await _cozulsun(tester, () => st.frameIndex == 1);
    expect(st.frameCount, 2);

    // Uzun süre geçse de kare ilerlemez, sarma yok.
    await tester.pump(const Duration(seconds: 2));
    await tester.pump(const Duration(seconds: 2));
    expect(st.frameIndex, 1);
    expect(loop, 0);
    expect(done, 1);
  });

  testWidgets('zamanlı pump ile kare ilerler; onDone BİR kez; son kare tutulur',
      (tester) async {
    var done = 0;
    await tester.pumpWidget(
        _sar(FrameSequence.memory(bytes: kFixture, onDone: () => done++)));
    final st = _durum(tester);
    await _cozulsun(tester, () => st.frameIndex == 0);
    expect(st.frameCount, 2);
    expect(done, 0);

    await tester.pump(); // Ticker'ın ilk tiki (elapsed 0)
    await tester.pump(const Duration(milliseconds: 60));
    expect(st.frameIndex, 0, reason: '100 ms dolmadan ilerlemez');

    await tester.pump(const Duration(milliseconds: 50)); // 110 ms → ilerle
    await _cozulsun(tester, () => st.frameIndex == 1);
    expect(done, 0, reason: 'son kare gösterilirken bitmiş sayılmaz');

    await tester.pump(kKare); // son karenin süresi doldu → bitti
    expect(done, 1);
    expect(st.isDone, isTrue);

    // Bittikten sonra ne ilerler ne tekrar onDone verir; son kare tutulur.
    await tester.pump(const Duration(seconds: 1));
    await tester.pump(const Duration(seconds: 1));
    expect(done, 1);
    expect(st.frameIndex, 1);
  });

  testWidgets('loop: her sarmada onLoop, onDone hiç', (tester) async {
    var loop = 0, done = 0;
    await tester.pumpWidget(_sar(FrameSequence.memory(
        bytes: kFixture,
        loop: true,
        onLoop: () => loop++,
        onDone: () => done++)));
    final st = _durum(tester);
    await _cozulsun(tester, () => st.frameIndex == 0);
    await tester.pump(); // ilk tik

    await tester.pump(kKare);
    await _cozulsun(tester, () => st.frameIndex == 1);
    expect(loop, 0);

    await tester.pump(kKare); // sarma anı: onLoop, kare 0 çözülmeye başlar
    expect(loop, 1);
    await _cozulsun(tester, () => st.frameIndex == 0);

    await tester.pump(kKare);
    await _cozulsun(tester, () => st.frameIndex == 1);
    await tester.pump(kKare);
    expect(loop, 2);
    expect(done, 0);
  });

  testWidgets('dispose sızdırmaz: çözme uçuştayken sökülse de hata yok',
      (tester) async {
    await tester.pumpWidget(_sar(FrameSequence.memory(bytes: kFixture)));
    final st = _durum(tester);
    await _cozulsun(tester, () => st.frameIndex == 0);
    await tester.pump();
    // İlerleme tetiklenir (getNextFrame uçuşta) ve ağaç hemen sökülür.
    await tester.pump(kKare);
    await tester.pumpWidget(_sar(const SizedBox()));
    // Uçuştaki çözmenin devamı gerçek döngüde biter: kare atılır, hata yok.
    await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 100)));
    await tester.pump();
    expect(tester.takeException(), isNull);
    expect(find.byType(FrameSequence), findsNothing);
  });

  testWidgets('bozuk yük: onDone yine bir kez (durum makinesi askıda kalmaz)',
      (tester) async {
    var done = 0;
    await tester.pumpWidget(_sar(FrameSequence.memory(
        bytes: Uint8List.fromList(const [1, 2, 3, 4]),
        onDone: () => done++)));
    final st = _durum(tester);
    await _cozulsun(tester, () => st.isDone);
    expect(done, 1);
    expect(st.frameCount, 0);
    await tester.pump(const Duration(seconds: 1));
    expect(done, 1);
  });

  testWidgets('AnimStage varsayılan oran 16:9 ve ZEMİNSİZ', (tester) async {
    // Klipler 16:9 ve alfa kanallı: sahne yalnız oranı sabitler; kart,
    // zemin ya da vinyet ÇİZMEZ — paralar uygulamanın kendi zemininin
    // üstünde durur (tepsi/mekân yok). Bir DecoratedBox/ColoredBox geri
    // gelirse "video penceresi" hissi geri gelmiş demektir.
    await tester.pumpWidget(const MaterialApp(
        home: Scaffold(
            body: SizedBox(
                width: 320,
                child: AnimStage(child: SizedBox.expand())))));
    final oran = tester.widget<AspectRatio>(find.descendant(
        of: find.byType(AnimStage), matching: find.byType(AspectRatio)));
    expect(oran.aspectRatio, closeTo(16 / 9, 1e-9));
    final boyut = tester.getSize(find.byType(AspectRatio));
    expect(boyut.width / boyut.height, closeTo(16 / 9, 1e-6));
    expect(
        find.descendant(
            of: find.byType(AnimStage), matching: find.byType(DecoratedBox)),
        findsNothing,
        reason: 'sahne zemin çizmez');
    expect(
        find.descendant(
            of: find.byType(AnimStage), matching: find.byType(ColoredBox)),
        findsNothing,
        reason: 'sahne kart çizmez');
  });
}
