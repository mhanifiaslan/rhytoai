import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/core/providers.dart';
import 'package:rytho/features/sky/sign_story_screen.dart';
import 'package:rytho/features/sky/sky_now_screen.dart';
import 'package:rytho/l10n/app_localizations.dart';

/// Asama A2'nin iki degismezi.
///
/// ## 1. Serit HIKAYE acar
///
/// Burc yuvarlaklari Instagram/WhatsApp hikaye halkasi gibi GORUNUYORDU ama
/// oyle davranmiyordu: dokununca ekranin 200 px asagisindaki bir bolumun
/// metni degisiyordu. Kullanicinin tarifi buydu. Artik tam ekran okuyucu
/// aciliyor ve metin KIRPILMIYOR — okuyucunun varlik sebebi bu.
///
/// ## 2. Akistaki "Su an" TEK SATIR kalir
///
/// Eskiden akisin sonunda 230 px'lik cark + ay evresi + retro cipleri + sekiz
/// aci cipi tek blok halinde duruyordu; olculen ~1500 px'in buyuk dilimi
/// buydu. Ozet buyurse ayni sorun geri gelir ve bu kimsenin gozune carpmaz.

const _uzunYorum = 'Bugun gokyuzunde belirgin bir gerilim var ve bu gerilim '
    'kararlarini hizlandirmaya calisacak. Acele etme. Ay Balik burcunda '
    'ilerlerken sezgin yuksek ama olculerin kaygan. Aksama dogru netlesir.';

Map<String, dynamic> _yorum(String key) => {
      'reading': '$key: $_uzunYorum',
      'moon_phase': {'emoji': '🌒', 'name': 'Hilal', 'illumination': '%18'},
    };

final _gokyuzu = <String, dynamic>{
  'moon_phase': {'emoji': '🌒', 'name': 'Hilal', 'illumination': '%18'},
  'retrogrades': ['Merkur', 'Satürn'],
  'aspects': [
    {'p1': 'Ay', 'aspect': 'kare', 'p2': 'Mars'},
    {'p1': 'Güneş', 'aspect': 'üçgen', 'p2': 'Jüpiter'},
    {'p1': 'Venüs', 'aspect': 'karşıt', 'p2': 'Plüton'},
    {'p1': 'Merkür', 'aspect': 'altmışlık', 'p2': 'Neptün'},
  ],
};

/// Otomatik gecis testleri icin kisa metin: `okumaSuresi` taban degeri
/// olan 6 saniyeye duser, test 30 saniye beklemek zorunda kalmaz.
Map<String, dynamic> _kisaYorum(String key) => {'reading': '$key: Sakin bir gun.'};

Widget _sarKisa(Widget child) => _sarGenel(child, _kisaYorum);

Widget _sar(Widget child) => _sarGenel(child, _yorum);

Widget _sarGenel(
        Widget child, Map<String, dynamic> Function(String) uretici) =>
    ProviderScope(
      overrides: [
        signHoroscopeProvider.overrideWith((ref, key) async => uretici(key)),
      ],
      child: MaterialApp(
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: AppLocalizations.supportedLocales,
        locale: const Locale('tr'),
        home: Scaffold(body: child),
      ),
    );

/// `AstrolabeSpinner` surekli doner — `pumpAndSettle` hicbir zaman donmez.
Future<void> _bekle(WidgetTester tester) async {
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 400));
  await tester.pump(const Duration(milliseconds: 400));
}

void main() {
  group('hikaye okuyucu', () {
    testWidgets('istenen burcta acilir', (tester) async {
      // Serit sirasi kullanicinin burcunu one aliyor; okuyucu AYNI sirayi
      // almazsa kaydirinca beklenmedik burca gecilir.
      await tester.pumpWidget(_sar(const SignStoryScreen(
          order: [5, 0, 1, 2], initialIndex: 0)));
      await _bekle(tester);

      expect(find.textContaining('virgo:'), findsOneWidget);
      expect(find.textContaining('aries:'), findsNothing);
    });

    testWidgets('okuyucuda metin KIRPILMAZ', (tester) async {
      await tester.pumpWidget(_sar(const SignStoryScreen(
          order: [5, 0, 1, 2], initialIndex: 0)));
      await _bekle(tester);

      final metin =
          tester.widget<Text>(find.textContaining('virgo:'));
      // Kirpma olsaydi okuyucunun varlik sebebi kalmazdi: metin zaten
      // akistaki kartta 3 satir gorunuyor.
      expect(metin.maxLines, isNull,
          reason: 'hikaye sayfasinda tam metin gorunmeli');
    });

    testWidgets('yatay kaydirma sonraki burca gecer', (tester) async {
      await tester.pumpWidget(_sar(const SignStoryScreen(
          order: [5, 0, 1, 2], initialIndex: 0)));
      await _bekle(tester);

      await tester.drag(find.byType(PageView), const Offset(-500, 0));
      await _bekle(tester);

      expect(find.textContaining('aries:'), findsOneWidget);
    });

    testWidgets('ilerleme cubugu her burc icin bir bolme gosterir',
        (tester) async {
      await tester.pumpWidget(_sar(const SignStoryScreen(
          order: [5, 0, 1, 2, 3, 4], initialIndex: 2)));
      await _bekle(tester);

      // Bolmeler dokunulabilir olmali — atlamanin tek yolu kaydirma degil.
      final bolmeler = find.descendant(
        of: find.byType(SignStoryScreen),
        matching: find.byType(GestureDetector),
      );
      expect(tester.widgetList(bolmeler).length, greaterThanOrEqualTo(6));
    });
  });

  group('otomatik ilerleme', () {
    // Kullanici ilk surumu eksik buldu: "kaydirinca degisiyor ama kendisi
    // gecmiyor otomatik (instagram whatsapp davranisi bekliyorum)".
    //
    // Instagram'in sabit 5 saniyesi buraya tasinamaz: orada icerik gorsel,
    // burada ~150 kelimelik metin. Bu yuzden sure kelimeden hesaplaniyor.

    test('sure metnin uzunlugundan hesaplanir', () {
      // 200 kelime/dakika -> 100 kelime = 30 sn (ust sinir).
      final yuz = List.filled(100, 'kelime').join(' ');
      expect(okumaSuresi(yuz).inSeconds, 30);

      // 40 kelime = 12 sn.
      final kirk = List.filled(40, 'kelime').join(' ');
      expect(okumaSuresi(kirk).inSeconds, 12);
    });

    test('cok kisa metin bir anda gecip gitmez', () {
      // Taban olmasaydi uc kelimelik yorum ~1 sn'de kayardi.
      expect(okumaSuresi('Sakin bir gun.').inSeconds, 6);
      expect(okumaSuresi('').inSeconds, 6);
    });

    test('cok uzun metin hikayeyi durmus gostermez', () {
      final devasa = List.filled(500, 'kelime').join(' ');
      expect(okumaSuresi(devasa).inSeconds, 30);
    });

    testWidgets('sure dolunca KENDILIGINDEN sonraki burca gecer',
        (tester) async {
      await tester.pumpWidget(
          _sarKisa(const SignStoryScreen(order: [5, 0, 1], initialIndex: 0)));
      await _bekle(tester);
      expect(find.textContaining('virgo:'), findsOneWidget);

      await tester.pump(const Duration(seconds: 7));
      await _bekle(tester);

      expect(find.textContaining('aries:'), findsOneWidget,
          reason: 'hikaye kendiliginden ilerlemiyor');
    });

    testWidgets('parmak ekrandayken DURUR', (tester) async {
      await tester.pumpWidget(
          _sarKisa(const SignStoryScreen(order: [5, 0, 1], initialIndex: 0)));
      await _bekle(tester);

      // Basili tut: okuyor sayilir, sayfa altindan kaymamali.
      final dokunus = await tester.startGesture(const Offset(200, 400));
      await tester.pump(const Duration(seconds: 12));
      await tester.pump(const Duration(milliseconds: 400));
      expect(find.textContaining('virgo:'), findsOneWidget,
          reason: 'parmak ekrandayken ilerleme durmali');

      // Parmak kalkinca kaldigi yerden devam eder.
      await dokunus.up();
      // Once TEK kare: `Ticker` baslangic zamanini ilk tick'te kaydeder, o
      // karede ilerleme olmaz. Dogrudan 7 sn pompalamak sayaci hic
      // ilerletmezdi ve test urun hatasi varmis gibi duserdi.
      await tester.pump();
      await tester.pump(const Duration(seconds: 7));
      await _bekle(tester);
      expect(find.textContaining('aries:'), findsOneWidget);
    });

    testWidgets('son burcta ekran KAPANMAZ', (tester) async {
      // Instagram son hikayeden sonra cikar; burada okuma ortasinda
      // kullaniciyi ekrandan atmak olurdu.
      await tester.pumpWidget(
          _sarKisa(const SignStoryScreen(order: [5], initialIndex: 0)));
      await _bekle(tester);

      await tester.pump(const Duration(seconds: 10));
      await _bekle(tester);

      expect(find.byType(SignStoryScreen), findsOneWidget);
      expect(find.textContaining('virgo:'), findsOneWidget);
    });
  });

  group('akistaki "Su an" ozeti', () {
    testWidgets('TEK SATIR kalir, cark akista yok', (tester) async {
      await tester.pumpWidget(_sar(SkyNowSummary(sky: _gokyuzu)));
      await _bekle(tester);

      final yukseklik =
          tester.getSize(find.byType(SkyNowSummary)).height;
      // Eski hali 230 px cark + cipler = ~400 px idi. Ozet bir satir.
      expect(yukseklik, lessThan(110),
          reason: 'ozet buyudu — akis yine uzar');
    });

    testWidgets('retro sayisini ve tek one cikan aciyi gosterir',
        (tester) async {
      await tester.pumpWidget(_sar(SkyNowSummary(sky: _gokyuzu)));
      await _bekle(tester);

      expect(find.textContaining('2 gezegen retro'), findsOneWidget);
      // Dort aci var; ozette YALNIZCA ilki. Hepsi bir bakista okunmuyordu.
      expect(find.textContaining('Ay kare Mars'), findsOneWidget);
      expect(find.textContaining('Venüs karşıt Plüton'), findsNothing);
    });

    testWidgets('aci yoksa cokmez', (tester) async {
      await tester.pumpWidget(_sar(const SkyNowSummary(sky: {
        'moon_phase': {'emoji': '🌕', 'name': 'Dolunay', 'illumination': '%99'},
      })));
      await _bekle(tester);

      expect(find.textContaining('Dolunay'), findsOneWidget);
    });
  });
}
