/// Bildirim dili — `users/{uid}.language` alanının TEK yazıcısı (PBZ).
///
/// Bildirim metni sunucuda üretiliyor ve sunucu istek başlığı görmediği
/// için `Accept-Language` oraya ulaşmıyor; dil profile yazılır. Cihazda
/// ölçülen kusur: eski yazıcı (`syncNotificationContext`) soğuk açılışta
/// İKİ kez yazıyordu — auth dinleyicisi tercih daha SharedPreferences'tan
/// yüklenmeden okuyup sistem dilini, tercih yüklenince ikinci dinleyici
/// doğru dili. İkisi de ateşle-unut olduğu için ilk (bayat) yazım çoğu kez
/// SON düşüyor, profil her açılışta `tr`/`en` arasında gidip geliyor ve o
/// günün bildirimleri son yazımın diliyle çıkıyordu.
///
/// Yarış sıralamayla değil yapıyla bitirilir (K5):
/// 1. **Tek yazıcı, promise zinciri:** yazımlar art arda koşar, hiçbir
///    zaman örtüşmez.
/// 2. **Sıra numarası — son niyet kazanır:** kuyruktaki bir yazım sırası
///    geldiğinde daha yeni bir niyet varsa ATLANIR.
/// 3. **`LocaleController.ready` beklenir:** tercih yüklenmeden yazım YOK.
/// 4. **Güdüm `effectiveLocaleProvider`:** arayüzün ve `Accept-Language`ın
///    kullandığı dil — "Sistem" tercihinde telefon dili değişince de yazılır.
library;

import 'dart:async' show unawaited;

import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart' show Locale;
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'locale.dart';
import 'providers.dart';

typedef LanguageWriter = Future<void> Function(String uid, String lang);

Future<void> _firestoreWrite(String uid, String lang) => FirebaseFirestore
    .instance
    .collection('users')
    .doc(uid)
    .set({'language': lang}, SetOptions(merge: true));

/// Tek yazıcı, son niyet kazanır.
///
/// [write] test dikişidir; üretimde `users/{uid}.set({'language'}, merge)`.
class LanguageSync {
  LanguageSync({LanguageWriter? write}) : _write = write ?? _firestoreWrite;

  final LanguageWriter _write;

  /// Promise zinciri: her yazım bir öncekinin bitmesini bekler.
  Future<void> _zincir = Future<void>.value();

  /// Sıra numarası: `push` her çağrıda artar; kuyruktaki yazım sırası
  /// geldiğinde kendi numarası güncel değilse (daha yeni niyet var) atlar.
  int _seq = 0;

  /// Son BAŞARIYLA yazılan `'$uid:$lang'` — aynı değer iki kez tetiklenirse
  /// (uid dinleyicisi + dil dinleyicisi aynı anda) tek yazım olur.
  String? _lastKey;

  /// Dili sıraya koyar; dönen future o niyetin (yazılsın ya da atlansın)
  /// işlenmesini bekler. Hata yutulur, zincir kopmaz: bir yazım düşerse
  /// sonraki niyet yine koşar ve `_lastKey` güncellenmediği için aynı değer
  /// yeniden denenir.
  Future<void> push(String uid, String lang) {
    final my = ++_seq;
    _zincir = _zincir.then((_) async {
      if (my != _seq) return; // daha yeni niyet kuyrukta — son niyet kazanır
      final key = '$uid:$lang';
      if (key == _lastKey) return; // çift tetik → tek yazım
      try {
        await _write(uid, lang);
        _lastKey = key;
      } catch (e) {
        debugPrint('Bildirim dili yazılamadı: $e');
      }
    });
    return _zincir;
  }
}

/// Profile yazılacak dil — arayüzün GÖSTERDİĞİ dille AYNI kural.
///
/// Desteklenen dil → kodu; değilse `kSupportedLocales.first` ('tr').
/// ⚠️ 'en' DEĞİL: main.dart'ta `localeResolutionCallback` yok, MaterialApp
/// desteklenmeyen sistem dilinde (ör. 'de') `supportedLocales.first` = TR
/// gösteriyor; backend varsayılanı da 'tr'. Bildirim arayüzden farklı dilde
/// gelmemeli.
String notificationLanguage(Locale effective) {
  final kod = effective.languageCode;
  if (kSupportedLocales.any((l) => l.languageCode == kod)) return kod;
  return kSupportedLocales.first.languageCode;
}

final languageSyncProvider = Provider<LanguageSync>((_) => LanguageSync());

/// Oturumdaki kullanıcının kimliği; oturum yoksa `null`.
final currentUidProvider =
    Provider<String?>((ref) => ref.watch(authStateProvider).value?.uid);

/// Geçerli dili [uid] için sıraya koyar.
///
/// `ready` ÖNCE beklenir, dil ondan SONRA okunur: tercih yüklenmeden okunan
/// dil sistem dili olur ve bayat yazım tam da buradan doğuyordu.
Future<void> syncLanguage(Ref ref, String uid) async {
  await ref.read(localeProvider.notifier).ready;
  final lang = notificationLanguage(ref.read(effectiveLocaleProvider));
  await ref.read(languageSyncProvider).push(uid, lang);
}

/// Dil senkronunu oturuma ve geçerli dile bağlar.
///
/// `notificationSyncProvider` ile aynı desen: izlenmezse hiç kurulmaz
/// (`_Gate` izler). İki tetik var — oturum açılışı ve dil değişimi — ikisi
/// de aynı yazıcıya düşer, bu yüzden aynı anda gelseler de tek yazım olur.
final languageSyncListenerProvider = Provider<void>((ref) {
  ref.listen<String?>(currentUidProvider, (_, uid) {
    if (uid != null) unawaited(syncLanguage(ref, uid));
  }, fireImmediately: true);

  // Locale NESNESİ değil DİL KODU izlenir (apiProvider'daki gerekçe):
  // "tr_TR" → "tr" geçişi sunucu için aynı dil.
  ref.listen<String>(effectiveLocaleProvider.select((l) => l.languageCode),
      (_, _) {
    final uid = ref.read(currentUidProvider);
    if (uid != null) unawaited(syncLanguage(ref, uid));
  });
});
