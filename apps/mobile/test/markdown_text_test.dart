import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/widgets/markdown_text.dart';

/// R5-4'un degismezi: uretilen metin EKRANDA ham isaret gostermez.
///
/// Cihaz turunda tam rapor sayfasi "### 1. Oz Kimlik" ve "**Safravi**" diye
/// basiyordu. Metin duz `Text` ile ciziliyordu; modelin urettigi yapi hic
/// cozulmuyordu. Asagidaki testler cozucunun sozlesmesini korur.

const _ornek = '''
### 1. Öz Kimlik

Güneş'in **Aslan**'da olması, kendini gösterme ihtiyacını öne çıkarır.
Bu ihtiyaç sahne aramaz; tanınma arar.

- Ateş baskın
- Su eksik

## Yıl boyunca

Sıradan bir paragraf.
''';

void main() {
  group('bloklara ayirma', () {
    test('baslik seviyesiyle birlikte taninir', () {
      final bloklar = parseBlocks(_ornek);
      final basliklar = bloklar
          .where((b) => b.type == MarkdownBlockType.heading)
          .toList();

      expect(basliklar.length, 2);
      expect(basliklar.first.text, '1. Öz Kimlik');
      expect(basliklar.first.level, 3);
      expect(basliklar.last.level, 2);
    });

    test('madde satirlari paragraftan ayrilir', () {
      final maddeler = parseBlocks(_ornek)
          .where((b) => b.type == MarkdownBlockType.bullet)
          .map((b) => b.text)
          .toList();

      expect(maddeler, ['Ateş baskın', 'Su eksik']);
    });

    test('ardisik satirlar TEK paragrafta birlesir', () {
      // Model cumleleri satir sonuyla boluyor; her satiri ayri paragraf
      // saymak metni parcali gosterirdi.
      final paragraflar = parseBlocks(_ornek)
          .where((b) => b.type == MarkdownBlockType.paragraph)
          .toList();

      expect(paragraflar.first.text, contains('sahne aramaz'));
      expect(paragraflar.first.text, contains('Aslan'));
    });

    test('bos metin cokmez', () {
      expect(parseBlocks(''), isEmpty);
      expect(parseBlocks('\n\n   \n'), isEmpty);
    });
  });

  group('duz metne cevirme (paylasim karti)', () {
    test('isaretler soyulur, yapi korunur', () {
      final duz = markdownToPlain(_ornek);

      expect(duz, isNot(contains('#')));
      expect(duz, isNot(contains('**')));
      // `replaceAll` geri basvuru desteklemedigi icin bir ara `$1` yaziyordu.
      expect(duz, isNot(contains(r'$1')));
      expect(duz, contains('Aslan'));
      expect(duz, contains('• Ateş baskın'));
      expect(duz, contains('1. Öz Kimlik'));
    });
  });

  group('ekranda cizim', () {
    testWidgets('ham isaret GORUNMEZ', (tester) async {
      await tester.pumpWidget(MaterialApp(
        home: Scaffold(body: SingleChildScrollView(
            child: MarkdownText(_ornek))),
      ));
      await tester.pump();

      expect(find.textContaining('###'), findsNothing);
      expect(find.textContaining('**'), findsNothing);
      // Baslik metni kendisi duruyor — soyulan yalnizca isaret.
      expect(find.text('1. Öz Kimlik'), findsOneWidget);
    });

    testWidgets('kalin bolum w700 span olur', (tester) async {
      await tester.pumpWidget(const MaterialApp(
        home: Scaffold(body: MarkdownText('Güneş **Aslan**da.')),
      ));
      await tester.pump();

      final zengin = tester.widget<Text>(find.byType(Text).first);
      final parcalar = <InlineSpan>[];
      zengin.textSpan!.visitChildren((s) {
        parcalar.add(s);
        return true;
      });
      final kalin = parcalar.whereType<TextSpan>().where(
          (s) => s.style?.fontWeight == FontWeight.w700);
      expect(kalin.map((s) => s.text), contains('Aslan'));
    });
  });
}
