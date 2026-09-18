// gz-8 / ilkacilis-3 bekçileri: açılış kapısı HAM istisna basmaz ve
// kullanıcıyı ekranda KİLİTLEMEZ.
//
// Kapının iki hata dalı (`authStateProvider`, `profileProvider`) ilk açılışın
// tam ortasında. Eskiden `_Splash(message: '$e')` çağrılıyor ve ekranda
// çevrilmemiş `[cloud_firestore/permission-denied] ...` yazıyordu; altında
// hiçbir eylem yoktu ve kök rotada geri tuşu da çıkış vermiyor. Testçi
// dönen usturlabı görüp uygulamanın bozulduğunu düşünüyordu.
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/l10n/app_localizations.dart';
import 'package:rytho/main.dart' show SplashScene;
import 'package:rytho/widgets/atlas_widgets.dart' show GoldButton;

/// reduceMotion AÇIK sarılır (force_update_screen_test ile aynı gerekçe:
/// yıldız alanı ve usturlap sonsuz döngü — `pumpAndSettle` yasak).
Widget _sar(Widget child) => MaterialApp(
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: AppLocalizations.supportedLocales,
      locale: const Locale('tr'),
      home: Builder(
        builder: (context) => MediaQuery(
          data: MediaQuery.of(context).copyWith(disableAnimations: true),
          child: child,
        ),
      ),
    );

/// ARB'deki metin üretilen sınıftan okunur: metin değişince test kırılmasın,
/// anahtar silinirse DERLEME kırılsın.
AppLocalizations _tr() => lookupAppLocalizations(const Locale('tr'));

/// Kaynağı TAM SATIR yorumlarından arındırır.
///
/// Bir şeyin YOKLUĞUNU arayan bekçi, onu ANLATAN yorumu görmemeli — bu depoda
/// gerçekten patlamış bir tuzak. Yalnız tam satır yorumları atılıyor: satır
/// içi `//` dize literallerinde de geçebiliyor (ör. `https://`) ve onları
/// kesmek kaynağı bozardı.
String _yorumsuz(String kaynak) => kaynak
    .replaceAll('\r\n', '\n')
    .split('\n')
    .where((s) => !s.trimLeft().startsWith('//'))
    .join('\n');

void main() {
  testWidgets('mesajsız sahne normal bekleyiştir: hiçbir eylem çizilmez',
      (tester) async {
    await tester.pumpWidget(_sar(const SplashScene()));
    await tester.pump();

    expect(find.byType(GoldButton), findsNothing);
    expect(find.text(_tr().retry), findsNothing);
    expect(find.text(_tr().signOut), findsNothing);
  });

  testWidgets('hata mesajı varken ÇIKIŞ YOLU var: tekrar dene + oturumu kapat',
      (tester) async {
    var tekrar = 0;
    var cikis = 0;
    await tester.pumpWidget(_sar(SplashScene(
      message: _tr().errorGeneric,
      onRetry: () => tekrar++,
      onSignOut: () => cikis++,
    )));
    await tester.pump();

    expect(find.text(_tr().errorGeneric), findsOneWidget);
    // Kusurun kendisi buydu: mesajlı sahnede tek bir eylem bile yoktu.
    expect(find.byType(GoldButton), findsOneWidget,
        reason: 'mesajlı sahne bir KAPI; eylemsizse ekran kilittir');

    await tester.tap(find.text(_tr().retry));
    await tester.pump();
    await tester.tap(find.text(_tr().signOut));
    await tester.pump();

    expect(tekrar, 1);
    expect(cikis, 1);
  });

  testWidgets('kimlik dalında çıkış sunulmaz: oturum sahibi BİLİNMİYOR',
      (tester) async {
    await tester.pumpWidget(_sar(SplashScene(
      message: _tr().errorGeneric,
      onRetry: () {},
    )));
    await tester.pump();

    expect(find.text(_tr().retry), findsOneWidget);
    expect(find.text(_tr().signOut), findsNothing);
  });

  testWidgets('düğme etiketleri ARB\'den: İngilizce arayüzde Türkçe ÇIKMAZ',
      (tester) async {
    final en = lookupAppLocalizations(const Locale('en'));
    await tester.pumpWidget(MaterialApp(
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: AppLocalizations.supportedLocales,
      locale: const Locale('en'),
      home: Builder(
        builder: (context) => MediaQuery(
          data: MediaQuery.of(context).copyWith(disableAnimations: true),
          child: SplashScene(
            message: en.errorGeneric,
            onRetry: () {},
            onSignOut: () {},
          ),
        ),
      ),
    ));
    await tester.pump();

    expect(find.text(en.retry), findsOneWidget);
    expect(find.text(en.signOut), findsOneWidget);
    expect(find.text(_tr().retry), findsNothing,
        reason: 'gövdeye gömülü Türkçe etiket geri geldi');
  });

  group('Kaynak bekçisi', () {
    // `flutter test` paket kökünden koşar (apps/mobile).
    final kaynak = _yorumsuz(File('lib/main.dart').readAsStringSync());

    test('kapı HAM istisnayı EKRANA basmıyor', () {
      // Eşleşme dize literaline bağlı: ham `_Splash` ya da `message` aramak
      // yanlış pozitif üretirdi.
      expect(kaynak, isNot(contains("_Splash(message: '\$e')")),
          reason: 'ham Object.toString() çevrilmeden ekrana geliyordu');
      expect(kaynak, isNot(contains("SplashScene(message: '\$e')")));
      expect(kaynak, contains('friendlyError(hata, l10n)'),
          reason: 'iki dal da depodaki süzgeçten geçmeli');
    });

    test('sebep KAYBOLMUYOR: teşhis assert içinde loglanıyor', () {
      expect(kaynak, contains("debugPrint('[RYTHO-GATE] hata dali: \$hata')"));
    });

    test('gövdede gömülü kullanıcı metni YOK: tek doğru yer ARB', () {
      // hata_dili_test.dart'ın api.dart için kurduğu kuralın aynısı; kapı
      // ekranı da İngilizce arayüzde Türkçe düğme göstermemeli.
      expect(kaynak, isNot(contains("'Tekrar dene'")));
      expect(kaynak, isNot(contains("'Oturumu kapat'")));
      expect(kaynak, contains('l10n.retry'));
      expect(kaynak, contains('l10n.signOut'));
    });

    test('l10n ZORUNLU imzayla uyumlu: nullable arama KULLANILMIYOR', () {
      // `friendlyError` l10n'i non-nullable alıyor (api.dart) ve `_Gate`
      // MaterialApp'in `home`'u — temsilci kurulu, `of` fırlatmaz.
      expect(kaynak, contains('AppLocalizations.of(context)'));
      expect(kaynak, isNot(contains('Localizations.of<AppLocalizations>')),
          reason: 'nullable arama non-nullable imzayla DERLENMEZ');
    });
  });
}
