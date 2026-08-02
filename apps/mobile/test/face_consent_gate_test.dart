import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/core/api.dart';
import 'package:rytho/features/face/face_consent.dart';
import 'package:rytho/features/face/face_reading_flow.dart';
import 'package:rytho/l10n/app_localizations.dart';

/// Riza kapisinin SOZLESMESI: bir karar verir, `true` ya da `null` doner.
///
/// Cihaz testinde uygulama iki kez `'_dependents.isEmpty': is not true` diye
/// coktu ve her ikisinde de sebep ayniydi: **bir ekran kendi rotasini
/// degistirip onu bekliyordu.**
///
/// Birinci surumde kapi `faceConsentProvider`'i izliyordu; onay verilince
/// `invalidate` kapiyi yeniden kuruyor, kurdugu ara ekran da kendi
/// `pushReplacement`'ini planliyordu — ayni rota iki kez degistiriliyordu.
///
/// Ikinci surumde kapi kameraya `pushReplacement` ile geciyor ve bunu `await`
/// ediyordu. `pushReplacement` kapinin KENDI rotasini yok ediyor: State rotasi
/// silindikten sonra uyaniyordu. Ustelik kapinin future'i o anda `null` ile
/// kapandigi icin cekim sonucu akisin sahibine hic ulasmiyor, okuma ekrani
/// hic acilmiyordu.
///
/// Bu yuzden korunan degismez su: **kapi gezinmez, yalnizca deger dondurur ve
/// bunu TAM BIR KEZ yapar.**

class _SahteAdapter implements HttpClientAdapter {
  _SahteAdapter({this.durum = 200, this.govde = '{"granted":true,"version":1}'});

  final int durum;
  final String govde;
  int postSayisi = 0;

  @override
  Future<ResponseBody> fetch(RequestOptions options,
      Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    if (options.method == 'POST') postSayisi++;
    return ResponseBody.fromString(
      govde,
      durum,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}

/// Rotadan cikislari sayar.
class _Sayac extends NavigatorObserver {
  int cikis = 0;
  int degistirilen = 0;

  @override
  void didPop(Route<dynamic> route, Route<dynamic>? previousRoute) => cikis++;

  @override
  void didReplace({Route<dynamic>? newRoute, Route<dynamic>? oldRoute}) {
    degistirilen++;
  }
}

/// Kapiyi gercek akistaki gibi bir rotaya iterek calistirir.
class _Sonuc {
  bool? deger;
  bool dondu = false;
}

Widget _uygulama({
  required _Sayac sayac,
  required Dio dio,
  required _Sonuc sonuc,
  // null verilirse GERCEK saglayici kullanilir; hata davranisini sinamanin
  // tek durust yolu bu.
  FaceConsent? riza,
}) {
  return ProviderScope(
    overrides: [
      apiProvider.overrideWithValue(dio),
      if (riza != null)
        faceConsentProvider.overrideWith((ref) async => riza),
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
      navigatorObservers: [sayac],
      home: Builder(
        builder: (context) => Scaffold(
          body: Center(
            child: ElevatedButton(
              onPressed: () async {
                sonuc.deger = await Navigator.of(context).push<bool>(
                  MaterialPageRoute(builder: (_) => const FaceConsentGate()),
                );
                sonuc.dondu = true;
              },
              child: const Text('BASLA'),
            ),
          ),
        ),
      ),
    ),
  );
}

void main() {
  testWidgets('riza varsa kapi TAM BIR KEZ true donerek kapanir',
      (tester) async {
    final sayac = _Sayac();
    final sonuc = _Sonuc();
    final dio = Dio()..httpClientAdapter = _SahteAdapter();

    await tester.pumpWidget(_uygulama(
      sayac: sayac,
      dio: dio,
      sonuc: sonuc,
      riza: const FaceConsent(granted: true, version: 1),
    ));
    await tester.tap(find.text('BASLA'));
    await tester.pumpAndSettle();

    expect(sonuc.dondu, isTrue, reason: 'kapi hic kapanmadi');
    expect(sonuc.deger, isTrue);
    expect(sayac.cikis, 1, reason: 'cift pop altindaki rotayi da kapatir');
    expect(sayac.degistirilen, 0,
        reason: 'kapi kendi rotasini DEGISTIRMEMELI — cokmenin sebebi buydu');
  });

  testWidgets('riza yoksa form gosterilir, kapi kapanmaz', (tester) async {
    final sayac = _Sayac();
    final sonuc = _Sonuc();
    final dio = Dio()..httpClientAdapter = _SahteAdapter();

    await tester.pumpWidget(_uygulama(
      sayac: sayac,
      dio: dio,
      sonuc: sonuc,
      riza: FaceConsent.unknown,
    ));
    await tester.tap(find.text('BASLA'));
    await tester.pumpAndSettle();

    expect(find.byType(CheckboxListTile), findsOneWidget);
    expect(sonuc.dondu, isFalse);
    expect(sayac.cikis, 0);
  });

  testWidgets('onay verilince kapi TAM BIR KEZ true doner', (tester) async {
    final sayac = _Sayac();
    final sonuc = _Sonuc();
    final adapter = _SahteAdapter();
    final dio = Dio()..httpClientAdapter = adapter;

    await tester.pumpWidget(_uygulama(
      sayac: sayac,
      dio: dio,
      sonuc: sonuc,
      riza: FaceConsent.unknown,
    ));
    await tester.tap(find.text('BASLA'));
    await tester.pumpAndSettle();

    // Onay kutusu varsayilan KAPALI olmali: "devam"a basmayi riza saymak
    // acik riza degildir.
    final kutu = tester.widget<CheckboxListTile>(find.byType(CheckboxListTile));
    expect(kutu.value, isFalse);

    await tester.tap(find.byType(CheckboxListTile));
    await tester.pumpAndSettle();
    await tester.tap(find.byType(FilledButton));
    await tester.pumpAndSettle();

    expect(adapter.postSayisi, 1, reason: 'riza sunucuya bir kez yazilmali');
    expect(sonuc.deger, isTrue);
    expect(sayac.cikis, 1,
        reason: 'invalidate kapiyi yeniden kurup ikinci cikis uretmemeli');
  });

  testWidgets('durum okunamazsa riza YOK sayilir', (tester) async {
    // Saglayici BURADA gecilmiyor: sinanmak istenen sey gercek saglayicinin
    // hata karsisindaki davranisi. Sunucu 500 donuyor.
    final sayac = _Sayac();
    final sonuc = _Sonuc();
    final dio = Dio()
      ..httpClientAdapter = _SahteAdapter(durum: 500, govde: '{"detail":"x"}');

    await tester.pumpWidget(
        _uygulama(sayac: sayac, dio: dio, sonuc: sonuc));
    await tester.tap(find.text('BASLA'));
    await tester.pumpAndSettle();

    expect(find.byType(CheckboxListTile), findsOneWidget,
        reason: 'sessizce gecmek biyometrik islemeyi rizasiz acardi');
    expect(sonuc.dondu, isFalse);
  });
}
