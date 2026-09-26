// Zorunlu güncelleme ekranı bekçileri (PBZ).
//
// Ekranın üç sözleşmesi: (1) geri tuşu geçmez — kök rotada geri tuşu
// uygulamayı arka plana atıp "kapı geçildi" hissi veriyordu; (2) mağaza iki
// katmanda da açılamazsa SÖYLENİR — başka çıkışı olmayan ekranda sessiz
// buton "uygulama bozuldu" demektir (KT4'te market:// fırlatınca kullanıcı
// gerçekten kilitli kaldı); (3) metinler l10n'dan gelir.
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/features/auth/force_update_screen.dart';
import 'package:rytho/l10n/app_localizations.dart';
import 'package:url_launcher/url_launcher.dart' show LaunchMode;

/// reduceMotion AÇIK sarılır: yıldız alanı sonsuz döngü (CosmicScaffold) —
/// depo doktrini `pumpAndSettle` yasak; kapı açıkken tek karede durur ve
/// giriş animasyonları hiç kurulmaz, zamanlı pump da gerekmez.
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

/// Çağrı sırasını kaydeden sahte mağaza açıcı.
class _SahteMagaza {
  _SahteMagaza({this.market = false, this.web = false, this.marketFirlatir = false});

  final bool market;
  final bool web;
  final bool marketFirlatir;
  final List<Uri> cagrilar = [];
  LaunchMode? webModu;

  Future<bool> ac(Uri url, {LaunchMode mode = LaunchMode.platformDefault}) async {
    cagrilar.add(url);
    if (url.scheme == 'market') {
      if (marketFirlatir) throw Exception('No Activity found to handle Intent');
      return market;
    }
    webModu = mode;
    return web;
  }
}

/// ARB'deki metin — testte sabit değil, üretilen sınıftan okunur ki metin
/// değişince test kırılmasın ama anahtar silinirse derleme kırılsın.
AppLocalizations _tr() => lookupAppLocalizations(const Locale('tr'));

void main() {
  testWidgets('geri tuşu geçmez: PopScope canPop false', (tester) async {
    await tester.pumpWidget(_sar(const ForceUpdateScreen()));
    // `find.byType(PopScope)` jenerik parametreyle eşleşmez; `is` ile.
    final kapsam = find.byWidgetPredicate((w) => w is PopScope);
    expect(kapsam, findsOneWidget);
    expect((tester.widget(kapsam) as PopScope).canPop, isFalse,
        reason: 'geri tuşu bu ekrandan çıkaramamalı — tek çıkış mağaza');
    // Ekran PopScope'un İÇİNDE: kapsam dışında kalan ekran korunmaz.
    expect(
        find.descendant(of: kapsam, matching: find.text(_tr().forceUpdateTitle)),
        findsOneWidget);
  });

  testWidgets('metinler l10n\'dan: başlık, gövde, eylem (tr)', (tester) async {
    await tester.pumpWidget(_sar(const ForceUpdateScreen()));
    final l10n = _tr();
    expect(find.text(l10n.forceUpdateTitle), findsOneWidget);
    expect(find.text(l10n.forceUpdateBody), findsOneWidget);
    expect(find.text(l10n.forceUpdateAction), findsOneWidget);
    // Mağaza adı metne GİRMEZ: aynı dize iOS'ta da gösteriliyor ve
    // Türkçe ek uyumu yüzünden yer tutucuyla çözülemiyor
    // ("Play'DE" ama "App Store'DA").
    expect(l10n.forceUpdateAction, isNot(contains('Google Play')));
    expect(l10n.forceUpdateAction, isNot(contains('App Store')));
    expect(find.byType(SnackBar), findsNothing);
  });

  testWidgets('iki deneme de düşerse SnackBar ile söylenir', (tester) async {
    final magaza = _SahteMagaza(market: false, web: false);
    await tester.pumpWidget(_sar(ForceUpdateScreen(launcher: magaza.ac)));
    await tester.tap(find.text(_tr().forceUpdateAction));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));

    // Sıra: önce Play uygulaması, sonra web (harici tarayıcı).
    expect(magaza.cagrilar, [kPlayMarketUri, kPlayWebUri]);
    expect(magaza.webModu, LaunchMode.externalApplication);
    expect(find.byType(SnackBar), findsOneWidget);
    expect(find.text(_tr().forceUpdateStoreFailed), findsOneWidget,
        reason: 'sessiz kalan buton, çıkışı olmayan ekranda kilit demektir');
  });

  testWidgets('market açılırsa web denenmez, SnackBar yok', (tester) async {
    final magaza = _SahteMagaza(market: true);
    await tester.pumpWidget(_sar(ForceUpdateScreen(launcher: magaza.ac)));
    await tester.tap(find.text(_tr().forceUpdateAction));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));

    expect(magaza.cagrilar, [kPlayMarketUri]);
    expect(find.byType(SnackBar), findsNothing);
  });

  testWidgets('market FIRLATIRSA (KT4) web denenir; web açılırsa SnackBar yok',
      (tester) async {
    final magaza = _SahteMagaza(marketFirlatir: true, web: true);
    await tester.pumpWidget(_sar(ForceUpdateScreen(launcher: magaza.ac)));
    await tester.tap(find.text(_tr().forceUpdateAction));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));

    expect(magaza.cagrilar, [kPlayMarketUri, kPlayWebUri]);
    expect(find.byType(SnackBar), findsNothing);
    expect(tester.takeException(), isNull);
  });

  group('mağaza adayları platforma göre', () {
    tearDown(() => debugDefaultTargetPlatformOverride = null);

    test('Android: önce market://, sonra web', () {
      debugDefaultTargetPlatformOverride = TargetPlatform.android;
      final adaylar = magazaAdaylari();
      expect(adaylar.map((a) => a.url).toList(), [kPlayMarketUri, kPlayWebUri]);
    });

    test('iOS: App Store kimliği YOKKEN aday üretilmez', () {
      // Bu turun asıl kararı. Kimlik `String.fromEnvironment` ile gelir ve
      // testte boştur — tıpkı App Store Connect kaydı açılmadan yapılan
      // her derlemede olduğu gibi. Uydurma bir kimlikle kurulan bağlantı
      // mağazada "uygulama bulunamadı" açar ve kullanıcı bu ekranda
      // GERÇEKTEN kilitli kalır; boş liste dürüst SnackBar'a düşürür.
      debugDefaultTargetPlatformOverride = TargetPlatform.iOS;
      expect(kAppStoreAppId, isEmpty,
          reason: 'test derlemesinde APPSTORE_APP_ID tanımlı olmamalı');
      expect(magazaAdaylari(), isEmpty);
    });

    testWidgets('iOS: çıkış yokken sessiz kalmaz, SnackBar söyler',
        (tester) async {
      // Sıfırlama GÖVDE İÇİNDE: `testWidgets` gövde biter bitmez foundation
      // debug değişkenlerinin sıfırlanmış olmasını doğruluyor
      // (binding._verifyInvariants), yani tearDown çok geç kalıyor.
      debugDefaultTargetPlatformOverride = TargetPlatform.iOS;
      try {
        final magaza = _SahteMagaza(market: false, web: false);
        await tester.pumpWidget(_sar(ForceUpdateScreen(launcher: magaza.ac)));
        await tester.tap(find.text(_tr().forceUpdateAction));
        await tester.pump();
        expect(magaza.cagrilar, isEmpty, reason: 'denenecek adres yok');
        expect(find.text(_tr().forceUpdateStoreFailed), findsOneWidget);
      } finally {
        debugDefaultTargetPlatformOverride = null;
      }
    });
  });
}
