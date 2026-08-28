// Bahsetme bandı bekçileri (OB1).
//
// Cihazda ölçülen kusur: GT6 çipleri '${relationIcon(...)} ' yazıyordu —
// relationIcon IconData döndürür ve string'e basılınca kullanıcı ekranda
// "IconData(U+0E25B) Annem" gördü. Bandı ÇİZEN hiçbir test yoktu; hata bu
// yüzden sızdı. Bu dosya bandı ilk kez gerçekten çizer.
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/features/chat/chat_screen.dart'
    show MentionCandidateList;
import 'package:rytho/features/chat/mention.dart';
import 'package:rytho/features/people/person_form_screen.dart'
    show relationEmoji;
import 'package:rytho/l10n/app_localizations.dart';

Widget _sar(Widget child) => MaterialApp(
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: AppLocalizations.supportedLocales,
      locale: const Locale('tr'),
      home: Scaffold(body: child),
    );

/// Ağaçtaki tüm Text içeriklerini toplar.
Iterable<String> _metinler(WidgetTester tester) => tester
    .widgetList<Text>(find.byType(Text))
    .map((t) => t.data ?? '')
    .where((s) => s.isNotEmpty);

void main() {
  const adaylar = [
    MentionCandidate(
        display: 'Annem', personId: 'p1', relation: 'parent',
        sunSign: 'Kova ♒'),
    MentionCandidate(
        display: 'Erkan', friendUid: 'f1', sunSign: 'Aslan ♌',
        username: 'erkan42'),
  ];

  testWidgets('bantta IconData ASLA görünmez (GT6 regresyonu)',
      (tester) async {
    await tester.pumpWidget(_sar(
        MentionCandidateList(candidates: adaylar, onSelect: (_) {})));
    for (final metin in _metinler(tester)) {
      expect(metin.contains('IconData'), isFalse,
          reason: 'ekrana IconData sızdı: "$metin"');
    }
    expect(find.text('Annem'), findsOneWidget);
    expect(find.text('Erkan'), findsOneWidget);
  });

  testWidgets('kişi satırı emoji + burç, arkadaş satırı @ad · burç',
      (tester) async {
    await tester.pumpWidget(_sar(
        MentionCandidateList(candidates: adaylar, onSelect: (_) {})));
    expect(find.text(relationEmoji('parent')), findsOneWidget);
    expect(find.text('Kova ♒'), findsOneWidget);
    expect(find.text('@erkan42 · Aslan ♌'), findsOneWidget);
    // Arkadaş dairesi baş harf taşır.
    expect(find.text('E'), findsOneWidget);
  });

  testWidgets('dokunma onSelect ile adayı verir', (tester) async {
    MentionCandidate? secilen;
    await tester.pumpWidget(_sar(MentionCandidateList(
        candidates: adaylar, onSelect: (a) => secilen = a)));
    await tester.tap(find.text('Erkan'));
    await tester.pump();
    expect(secilen?.friendUid, 'f1');
  });

  testWidgets('boş liste 42px kutuda dürüst boş durum', (tester) async {
    await tester.pumpWidget(_sar(
        const MentionCandidateList(candidates: [], onSelect: _yok)));
    expect(find.text('Eşleşen kişi yok — Çevrem\'den ekleyebilirsin'),
        findsOneWidget);
  });

  test('relationEmoji her ilişki için tek glif döner, IconData değil', () {
    for (final r in [
      'partner', 'child', 'parent', 'sibling', 'friend', 'work', 'other'
    ]) {
      final e = relationEmoji(r);
      expect(e, isNotEmpty);
      expect(e.contains('IconData'), isFalse);
      expect(e.length <= 4, isTrue, reason: 'tek glif kalmalı: $r → $e');
    }
  });
}

void _yok(MentionCandidate _) {}
