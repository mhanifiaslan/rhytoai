// Bildirim dili bekçileri (PBZ — K5: tek yazıcı, son niyet kazanır).
//
// Cihazda ölçülen kusur: `users/{uid}.language` soğuk açılışta İKİ kez,
// sırasız yazılıyordu — auth dinleyicisi tercih daha SharedPreferences'tan
// yüklenmeden okuyup SİSTEM dilini, tercih yüklenince ikinci dinleyici
// doğru dili. İkisi de ateşle-unut olduğu için bayat yazım çoğu kez SON
// düşüyor, profil her açılışta tr/en arasında gidip geliyordu. Burada üç
// yapısal karar sabitlenir: promise zinciri (örtüşme yok), sıra numarası
// (son niyet kazanır) ve `ready` beklenmeden yazım YOK.
import 'dart:async';

import 'package:flutter/material.dart' show Locale;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart' show StateProvider;
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/core/language_sync.dart';
import 'package:rytho/core/locale.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Testin denetlediği oturum kimliği (gerçek `authStateProvider` Firebase
/// ister; kapı burada kesilir).
final _uid = StateProvider<String?>((_) => null);

/// Soğuk açılış kabı: sistem dili + oturum + kaydeden yazıcı.
ProviderContainer _kap(List<String> yazilan,
    {required Locale sistem, String? uid}) {
  final container = ProviderContainer(overrides: [
    currentUidProvider.overrideWith((ref) => ref.watch(_uid)),
    systemLocaleProvider.overrideWith((_) => sistem),
    languageSyncProvider.overrideWithValue(LanguageSync(
        write: (uid, lang) async => yazilan.add('$uid:$lang'))),
  ]);
  addTearDown(container.dispose);
  if (uid != null) container.read(_uid.notifier).state = uid;
  return container;
}

/// `_Gate`'nin `ref.watch`i gibi CANLI dinler. Riverpod 3'te hiç dinlenmeyen
/// sağlayıcının iç `ref.listen` abonelikleri DURAKLATILIR (element.dart
/// `subs[i].impl.pause()`); yalnız `read` ile ilk tetik gelir, sonrakiler gelmez.
void _dinle(ProviderContainer kap) =>
    kap.listen<void>(languageSyncListenerProvider, (_, _) {});

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('LanguageSync', () {
    test('örtüşen iki push: yavaş "en" sürerken gelen "tr" onu BEKLER — '
        'iniş sırası [en, tr], son yazılan tr', () async {
      // İniş sırası kaydedilir (yazım BİTİNCE), çağrı sırası değil: eski
      // kusur tam olarak "bayat yazım son iner"di.
      final inen = <String>[];
      final sunucu = Completer<void>();
      final sync = LanguageSync(write: (_, lang) async {
        if (lang == 'en') await sunucu.future; // ilk yazım sunucuda takılı
        inen.add(lang);
      });

      final ilk = sync.push('u1', 'en');
      await Future<void>.delayed(Duration.zero); // 'en' yola çıktı
      final ikinci = sync.push('u1', 'tr');
      await Future<void>.delayed(Duration.zero);
      expect(inen, isEmpty, reason: '"tr" zinciri atlayıp önce inmemeli');

      sunucu.complete();
      await ilk;
      await ikinci;
      expect(inen, ['en', 'tr']);
      expect(inen.last, 'tr', reason: 'son niyet profile son yazılan olmalı');
    });

    test('üç hızlı push en,tr,en → "tr" HİÇ yazılmaz (son niyet kazanır)',
        () async {
      final yazilan = <String>[];
      final sync = LanguageSync(write: (_, lang) async => yazilan.add(lang));
      sync.push('u1', 'en');
      sync.push('u1', 'tr');
      await sync.push('u1', 'en');
      // Sırası gelen her yazım "daha yeni niyet var mı" diye bakar: ilk iki
      // niyet eskimiştir, yalnız sonuncusu yazılır.
      expect(yazilan, ['en']);
      expect(yazilan, isNot(contains('tr')));
    });

    test('aynı değer iki kez → TEK yazım (uid + dil dinleyicisi aynı anda)',
        () async {
      final yazilan = <String>[];
      final sync = LanguageSync(write: (_, lang) async => yazilan.add(lang));
      await sync.push('u1', 'tr');
      await sync.push('u1', 'tr');
      expect(yazilan, ['tr']);
    });

    test('anahtar uid+dil: hesap değişince aynı dil yeniden yazılır',
        () async {
      final yazilan = <String>[];
      final sync =
          LanguageSync(write: (uid, lang) async => yazilan.add('$uid:$lang'));
      await sync.push('u1', 'tr');
      await sync.push('u2', 'tr');
      expect(yazilan, ['u1:tr', 'u2:tr']);
    });

    test('yazım düşerse zincir kopmaz ve aynı değer yeniden denenir',
        () async {
      final yazilan = <String>[];
      var dusur = true;
      final sync = LanguageSync(write: (_, lang) async {
        if (dusur) {
          dusur = false;
          throw StateError('Firestore yok');
        }
        yazilan.add(lang);
      });
      await sync.push('u1', 'en'); // düşer, yutulur
      await sync.push('u1', 'en'); // _lastKey güncellenmediği için yazılır
      expect(yazilan, ['en']);
    });
  });

  group('notificationLanguage', () {
    test('desteklenen dil → kodu (bölge atılır)', () {
      expect(notificationLanguage(const Locale('en', 'US')), 'en');
      expect(notificationLanguage(const Locale('tr', 'TR')), 'tr');
    });

    test('desteklenmeyen sistem dili → arayüz aynası "tr" (en DEĞİL)', () {
      // MaterialApp `localeResolutionCallback` olmadan desteklenmeyen dilde
      // `supportedLocales.first` (tr) gösterir; bildirim arayüzle aynı
      // dilde gelmeli. Backend varsayılanı da tr.
      expect(notificationLanguage(const Locale('de')), 'tr');
      expect(kSupportedLocales.first.languageCode, 'tr');
    });
  });

  group('languageSyncListenerProvider (soğuk açılış)', () {
    test('tercih en + sistem tr → TAM OLARAK [u1:en]; sistem dili hiç yazılmaz',
        () async {
      // Kusurun birebir sahnesi: tercih SharedPreferences'ta, henüz
      // yüklenmemiş; oturum açık. Eski kod burada önce "u1:tr" yazıyordu.
      SharedPreferences.setMockInitialValues({'appLocale': 'en'});
      final yazilan = <String>[];
      final kap = _kap(yazilan, sistem: const Locale('tr'), uid: 'u1');

      _dinle(kap);
      expect(yazilan, isEmpty, reason: 'tercih yüklenmeden yazım YOK');

      await kap.read(localeProvider.notifier).ready;
      await pumpEventQueue();
      expect(yazilan, ['u1:en']);
    });

    test('tercih yok: sistem dili yazılır; sistem dili değişince yeniden',
        () async {
      // "Sistem" tercihinde telefon dili değişince push dili de değişmeli —
      // eski dinleyici `localeProvider`ı (açık tercihi) izlediği için
      // bunu hiç görmüyordu.
      SharedPreferences.setMockInitialValues({});
      final yazilan = <String>[];
      final kap = _kap(yazilan, sistem: const Locale('en'), uid: 'u1');

      _dinle(kap);
      await kap.read(localeProvider.notifier).ready;
      await pumpEventQueue();
      expect(yazilan, ['u1:en']);

      kap.read(systemLocaleProvider.notifier).state = const Locale('tr');
      await pumpEventQueue();
      expect(yazilan, ['u1:en', 'u1:tr']);
    });

    test('oturum yokken yazım yok; giriş yapılınca yazılır', () async {
      SharedPreferences.setMockInitialValues({});
      final yazilan = <String>[];
      final kap = _kap(yazilan, sistem: const Locale('tr'));

      _dinle(kap);
      await kap.read(localeProvider.notifier).ready;
      await pumpEventQueue();
      expect(yazilan, isEmpty);

      kap.read(_uid.notifier).state = 'u1';
      await pumpEventQueue();
      expect(yazilan, ['u1:tr']);
    });

    test('Profil → EN tercihi: tek yazım, bölge kodu değişimi yazdırmaz',
        () async {
      SharedPreferences.setMockInitialValues({});
      final yazilan = <String>[];
      final kap = _kap(yazilan, sistem: const Locale('tr', 'TR'), uid: 'u1');

      _dinle(kap);
      await kap.read(localeProvider.notifier).ready;
      await pumpEventQueue();
      expect(yazilan, ['u1:tr']);

      // Locale NESNESİ değişir ("tr_TR" → "tr"), dil kodu değişmez → yazım yok.
      await kap.read(localeProvider.notifier).set(const Locale('tr'));
      await pumpEventQueue();
      expect(yazilan, ['u1:tr']);

      await kap.read(localeProvider.notifier).set(const Locale('en'));
      await pumpEventQueue();
      expect(yazilan, ['u1:tr', 'u1:en']);
    });
  });
}
