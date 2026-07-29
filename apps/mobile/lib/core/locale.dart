import 'package:flutter/material.dart';
import 'package:flutter_riverpod/legacy.dart'
    show StateNotifier, StateNotifierProvider;
import 'package:shared_preferences/shared_preferences.dart';

/// Uygulama dili.
///
/// Dil iki yerde birden geçerli olmak zorunda:
/// 1. Arayüz metinleri (AppLocalizations / ARB)
/// 2. **Backend'in ürettiği yorumlar** — `Accept-Language` başlığıyla taşınır
///    (bkz. core/api.dart). Bu ikincisi asıl mesele: arayüz İngilizce olup
///    yorumların Türkçe gelmesi, çok dilliliğin hiç olmamasından kötüdür.
///
/// Varsayılan `null`: cihazın sistem dili kullanılır. Kullanıcı Profil >
/// Dil'den açıkça seçerse tercihi kalıcı olur.

const List<Locale> kSupportedLocales = [Locale('tr'), Locale('en')];

const String _kLocaleKey = 'appLocale';

class LocaleController extends StateNotifier<Locale?> {
  LocaleController() : super(null) {
    _load();
  }

  Future<void> _load() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final kod = prefs.getString(_kLocaleKey);
      if (kod != null && kSupportedLocales.any((l) => l.languageCode == kod)) {
        state = Locale(kod);
      }
    } catch (_) {
      // Okunamazsa sistem dilinde kalır.
    }
  }

  /// [locale] `null` ise sistem diline dönülür.
  Future<void> set(Locale? locale) async {
    state = locale;
    try {
      final prefs = await SharedPreferences.getInstance();
      if (locale == null) {
        await prefs.remove(_kLocaleKey);
      } else {
        await prefs.setString(_kLocaleKey, locale.languageCode);
      }
    } catch (_) {}
  }
}

final localeProvider =
    StateNotifierProvider<LocaleController, Locale?>((_) => LocaleController());

/// Backend'e gönderilecek dil kodu.
///
/// Tercih edilen dil yoksa cihazın sistem dili kullanılır; o da desteklenmiyorsa
/// backend kendi varsayılanına düşer (Türkçe). Bu değer bir Riverpod okuması
/// yapmadan da erişilebilir olmalı, çünkü Dio interceptor'ı ProviderScope
/// dışından çağrılıyor.
String? _tercihEdilenDil;

void setRequestLanguage(Locale? locale) {
  _tercihEdilenDil = locale?.languageCode;
}

/// `Accept-Language` başlık değeri.
String acceptLanguageHeader() {
  final secilen = _tercihEdilenDil;
  if (secilen != null) return secilen;

  final sistem = WidgetsBinding.instance.platformDispatcher.locale.languageCode;
  if (kSupportedLocales.any((l) => l.languageCode == sistem)) return sistem;
  // Desteklenmeyen sistem dili: q ağırlıklarıyla ikisini de bildir, backend
  // seçsin. Böylece ileride dil eklendiğinde istemci güncellemesi gerekmez.
  return 'en;q=0.9, tr;q=0.8';
}
