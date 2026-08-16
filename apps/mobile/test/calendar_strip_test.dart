import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// `Override` riverpod 3'te ana kütüphaneden değil buradan geliyor.
import 'package:flutter_riverpod/misc.dart' show Override;
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/core/providers.dart';
import 'package:rytho/features/sky/calendar_strip.dart';
import 'package:rytho/l10n/app_localizations.dart';

/// R5-6'nin degismezleri: ana ekrandaki 30 gunluk takvim seridi ve
/// ucretsiz katmanin DURUST teaser'i.
///
/// Kullanicinin istegi: "ana sayfada burc kartlarinin hemen altina yatay
/// takvim, tek satirlik... tiklaninca detayli bir kart acilacak. bir
/// sonraki ayin olaylari yaklastiginda konular kartlarda gorunecek ama
/// icerikler kilitli olacak."
///
/// Kritik olan cizgi: ucretsiz kullanici GERCEK tarihi ve GERCEK temayi
/// gorur, yalnizca okuma kilitlidir. Teaser uydurma olursa urunun
/// "olculmeyen soylenmez" ilkesi kirilir.

String _bugun([int gunSonra = 0]) {
  final d = DateTime.now().add(Duration(days: gunSonra));
  return '${d.year}-${d.month.toString().padLeft(2, '0')}-'
      '${d.day.toString().padLeft(2, '0')}';
}

/// Abonenin gordugu olay: okuma satiri ve dayanak var.
Map<String, dynamic> _acikOlay({int gunSonra = 2}) => {
      'type': 'aspect_exact',
      'date': _bugun(gunSonra),
      'date_local': '20 Ağustos',
      'theme': 'relationships',
      'theme_local': 'İlişkiler',
      'tone': 'support',
      'line': 'Yakınlarınla aranda biriken şeyi konuşmak kolaylaşıyor.',
      'technical': 'Mars, natal Venüs ile üçgen — orb 0.4°',
      'transit_local': 'Mars',
      'natal_local': 'Venüs',
      'aspect_local': 'Üçgen',
      'orb': 0.4,
    };

/// Ucretsiz kullanicinin gordugu ayni olay: sunucu okumayi cikardi.
Map<String, dynamic> _kilitliOlay({int gunSonra = 2}) {
  final o = Map<String, dynamic>.from(_acikOlay(gunSonra: gunSonra))
    ..remove('line')
    ..remove('technical');
  return o..['locked'] = true;
}

Widget _sar(Widget child, {List<Override> overrides = const []}) =>
    ProviderScope(
      overrides: overrides,
      child: MaterialApp(
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: AppLocalizations.supportedLocales,
        locale: const Locale('tr'),
        home: child,
      ),
    );

/// Gun kartini acan yardimci: sayfa `showDaySheet` ile aciliyor, bunun
/// icin gercek bir `BuildContext` gerekiyor.
Future<void> _gunKartiniAc(
    WidgetTester tester, List<Map<String, dynamic>> olaylar) async {
  await tester.pumpWidget(_sar(Builder(builder: (context) {
    return Scaffold(
      body: Center(
        child: ElevatedButton(
          onPressed: () =>
              showDaySheet(context, DateTime.now(), olaylar),
          child: const Text('aç'),
        ),
      ),
    );
  })));
  await tester.tap(find.text('aç'));
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 400));
}

void main() {
  group('takvim şeridi', () {
    testWidgets('otuz gün çizilir ve bugün en başta durur', (tester) async {
      await tester.pumpWidget(_sar(
        const Scaffold(body: CalendarStrip()),
        overrides: [
          transitCalendarProvider.overrideWith((ref) async => {
                'events': [_acikOlay()],
              }),
        ],
      ));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      // Bugünün günü ilk hücrede.
      expect(find.text('${DateTime.now().day}'), findsWidgets);
      expect(CalendarStrip.gunSayisi, 30);
    });

    testWidgets('veri yoksa şerit HİÇ çizilmez', (tester) async {
      // Bölüm kendi kendini gizler; ana ekran şeritsiz de ayakta kalmalı.
      await tester.pumpWidget(_sar(
        const Scaffold(body: CalendarStrip()),
        overrides: [
          transitCalendarProvider.overrideWith((ref) async => null),
        ],
      ));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      expect(tester.takeException(), isNull);
      expect(find.byType(ListView), findsNothing);
    });

    testWidgets('olaysız takvim ekranı bozmaz', (tester) async {
      await tester.pumpWidget(_sar(
        const Scaffold(body: CalendarStrip()),
        overrides: [
          transitCalendarProvider
              .overrideWith((ref) async => {'events': <dynamic>[]}),
        ],
      ));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 300));

      expect(tester.takeException(), isNull);
    });
  });

  group('gün kartı', () {
    testWidgets('abonede okuma cümlesi ve dayanak girişi var',
        (tester) async {
      await _gunKartiniAc(tester, [_acikOlay()]);

      expect(find.text('İlişkiler'), findsOneWidget);
      expect(find.textContaining('konuşmak kolaylaşıyor'), findsOneWidget);
      expect(find.text('Neye dayanıyor?'), findsOneWidget);
    });

    testWidgets('ücretsizde tema GÖRÜNÜR ama okuma kilitli',
        (tester) async {
      await _gunKartiniAc(tester, [_kilitliOlay()]);

      // Teaser dürüst: tema başlığı gerçek ve görünür.
      expect(find.text('İlişkiler'), findsOneWidget);
      // Okuma yok, yerinde kilit satırı var.
      expect(find.textContaining('konuşmak kolaylaşıyor'), findsNothing);
      expect(find.textContaining('Rytho+'), findsOneWidget);
    });

    testWidgets('olaylar temaya göre BAŞLIKLANIR', (tester) async {
      final kariyer = Map<String, dynamic>.from(_acikOlay())
        ..['theme'] = 'career'
        ..['theme_local'] = 'Kariyer'
        ..['line'] = 'İşinde görünürlüğün artıyor.';
      await _gunKartiniAc(tester, [_acikOlay(), kariyer]);

      expect(find.text('İlişkiler'), findsOneWidget);
      expect(find.text('Kariyer'), findsOneWidget);
    });

    testWidgets('temasız olay da başlıksız kalmaz', (tester) async {
      // İstasyonların teması yok; başlıksız bir satır ekranda öksüz durur.
      final istasyon = {
        'type': 'station',
        'date': _bugun(3),
        'transit_local': 'Merkür',
        'locked': true,
      };
      await _gunKartiniAc(tester, [istasyon]);

      expect(find.text('Diğer hareketler'), findsOneWidget);
    });
  });
}
