import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/l10n/app_localizations.dart';
import 'package:rytho/widgets/nebula_widgets.dart';

/// KL-turu: Firestore ve backend burç adını TÜRKÇE tutuyor
/// (`sunSign: "Oğlak ♑"`, `sun_sign`). Ham basıldığında İngilizce arayüzde
/// "Oğlak" görünüyordu — cihazda ölçüldü, mağaza ekran görüntüsünde yakalandı.
///
/// Bu bekçi tek şeyi sabitliyor: ham Türkçe değer, arayüz dilinde gösterilir.
Future<AppLocalizations> _l10n(WidgetTester tester, Locale dil) async {
  late AppLocalizations yakalanan;
  await tester.pumpWidget(MaterialApp(
    locale: dil,
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
    home: Builder(builder: (context) {
      yakalanan = AppLocalizations.of(context);
      return const SizedBox();
    }),
  ));
  return yakalanan;
}

void main() {
  testWidgets('İngilizce arayüzde Türkçe burç adı ÇEVRİLİR', (tester) async {
    final en = await _l10n(tester, const Locale('en'));
    expect(localizedSignName(en, 'Oğlak'), 'Capricorn');
    expect(localizedSignName(en, 'Akrep'), 'Scorpio');
    expect(localizedSignName(en, 'İkizler'), 'Gemini');
  });

  testWidgets('glif ham değerde varsa KORUNUR, yoksa eklenmez', (tester) async {
    final en = await _l10n(tester, const Locale('en'));
    // Sunucu "Oğlak ♑" biçiminde döndürüyor; glif dilden bağımsız,
    // tasarımın parçası ve kaybolmamalı.
    expect(localizedSignName(en, 'Oğlak ♑'), 'Capricorn ♑');
    expect(localizedSignName(en, 'Oğlak'), isNot(contains('♑')));
  });

  testWidgets('Türkçe arayüzde ad Türkçe kalır', (tester) async {
    final tr = await _l10n(tester, const Locale('tr'));
    expect(localizedSignName(tr, 'Oğlak ♑'), 'Oğlak ♑');
    expect(localizedSignName(tr, 'Akrep'), 'Akrep');
  });

  testWidgets('tanınmayan değer AYNEN döner, kaybolmaz', (tester) async {
    final en = await _l10n(tester, const Locale('en'));
    // Biçim değişirse ad çevrilmeden görünür — boş çip göstermekten iyi.
    expect(localizedSignName(en, 'Ophiuchus'), 'Ophiuchus');
    expect(localizedSignName(en, '  Koç  '), 'Aries');
    expect(localizedSignName(en, null), '');
    expect(localizedSignName(en, ''), '');
  });
}
