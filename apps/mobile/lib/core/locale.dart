import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart'
    show StateNotifier, StateNotifierProvider, StateProvider;
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

/// Cihazın **sistem** dili.
///
/// Kullanıcı uygulama içinden bir dil seçmediyse (varsayılan durum) gerçek
/// dil budur — hem arayüz hem `Accept-Language` buna düşer.
///
/// Ayrı bir sağlayıcı olmasının sebebi: sistem dili değiştiğinde Flutter
/// arayüzü yeniden çiziyor ama Riverpod'un ağ sağlayıcılarının haberi
/// olmuyordu. `apiProvider` yalnız [localeProvider]'ı izliyordu; kullanıcı
/// tercihi `null` kaldığı için hiçbir şey değişmemiş sayılıyor ve
/// ÖNBELLEKTEKİ Türkçe yorumlar ekranda kalıyordu. Sonraki istekler doğru
/// dille gidiyordu — yani hata "bazı kartlar çevrilmiyor" diye görünüyordu.
///
/// Değeri [SystemLocaleObserver] güncelliyor.
final systemLocaleProvider = StateProvider<Locale>((_) =>
    WidgetsBinding.instance.platformDispatcher.locale);

/// Uygulamanın o an geçerli dili: kullanıcı tercihi, yoksa sistem dili.
final effectiveLocaleProvider = Provider<Locale>((ref) =>
    ref.watch(localeProvider) ?? ref.watch(systemLocaleProvider));

/// Sistem dili değişimini [systemLocaleProvider]'a taşır.
///
/// Uygulamanın köküne bir kez takılır (bkz. `main.dart`).
class SystemLocaleObserver extends ConsumerStatefulWidget {
  const SystemLocaleObserver({super.key, required this.child});

  final Widget child;

  @override
  ConsumerState<SystemLocaleObserver> createState() =>
      _SystemLocaleObserverState();
}

class _SystemLocaleObserverState extends ConsumerState<SystemLocaleObserver>
    with WidgetsBindingObserver {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeLocales(List<Locale>? locales) {
    final yeni = locales?.firstOrNull ??
        WidgetsBinding.instance.platformDispatcher.locale;
    final onceki = ref.read(systemLocaleProvider);
    if (yeni.languageCode == onceki.languageCode) return;
    // Yalnız dil kodu karşılaştırılır: "en-US" -> "en-GB" geçişi sunucu
    // için aynı dil, gereksiz yere tüm yorumları yeniden çektirmemeli.
    ref.read(systemLocaleProvider.notifier).state = yeni;
  }

  @override
  Widget build(BuildContext context) => widget.child;
}

/// `Accept-Language` başlık değeri.
///
/// [tercih] `null` ise cihazın sistem dili kullanılır; o da desteklenmiyorsa
/// backend kendi varsayılanına düşer (Türkçe).
///
/// Saf fonksiyon olması bilinçli: dil daha önce modül düzeyinde bir değişkende
/// aynalanıyordu ve `apiProvider` onu izleyemediği için dil değiştiğinde
/// Riverpod önbellekteki yorumu yenilemiyordu — arayüz İngilizceye geçiyor,
/// içgörü metni Türkçe kalıyordu. Tek kaynak artık [localeProvider].
String acceptLanguageHeader(Locale? tercih) {
  final secilen = tercih?.languageCode;
  if (secilen != null) return secilen;

  final sistem = WidgetsBinding.instance.platformDispatcher.locale.languageCode;
  if (kSupportedLocales.any((l) => l.languageCode == sistem)) return sistem;
  // Desteklenmeyen sistem dili: q ağırlıklarıyla ikisini de bildir, backend
  // seçsin. Böylece ileride dil eklendiğinde istemci güncellemesi gerekmez.
  return 'en;q=0.9, tr;q=0.8';
}
