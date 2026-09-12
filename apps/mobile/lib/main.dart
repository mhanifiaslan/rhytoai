import 'dart:async' show unawaited;

import 'package:dio/dio.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_crashlytics/firebase_crashlytics.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:intl/date_symbol_data_local.dart';

import 'core/api.dart';
import 'core/app_config.dart';
import 'core/deep_links.dart';
import 'core/device_session.dart' show deviceConflictProvider;
import 'core/gate_guard.dart';
import 'core/language_sync.dart';
import 'core/locale.dart';
import 'core/notifications.dart';
import 'core/providers.dart';
import 'core/subscription.dart';
import 'features/auth/device_conflict_screen.dart';
import 'features/auth/force_update_screen.dart';
import 'features/auth/login_screen.dart';
import 'features/onboarding/onboarding_wizard.dart';
import 'features/shell/app_shell.dart';
import 'l10n/app_localizations.dart';
import 'theme/rytho_theme.dart';
import 'theme/rytho_tokens.dart';
import 'widgets/atlas_widgets.dart';
import 'widgets/cosmic_scaffold.dart';
import 'widgets/motion.dart';

/// Sağlayıcı yeniden deneme politikası.
///
/// Riverpod 3'ün VARSAYILANI her hatayı 10 kez, üstel bekleyerek (200ms →
/// 6,4sn) yeniden dener. Bu, sunucu kotası (429) devreye girdiğinde kotayı
/// kendi kendini besleyen bir döngüye çeviriyordu: tek 429, sağlayıcı
/// başına ~11 isteğe; canlıdaki yedi sağlayıcı ~77 isteğe çıkıyor ve
/// pencere hiç boşalmadığı için tek çıkış yolu uygulamayı öldürmek
/// oluyordu. Kullanıcının "az kullanmama rağmen yoğun talep diyor"
/// bulgusunun istemci yarısı buydu.
///
/// Kural: 4xx **istemci** hatasıdır — yeniden denemek durumu değiştirmez
/// (402 paywall, 403 yetki, 429 kota, 404 yok). Yalnız geçici olabilecek
/// hatalar (ağ kopması, zaman aşımı, 5xx) sınırlı sayıda denenir.
Duration? rythoRetry(int retryCount, Object error) {
  if (error is DioException) {
    final kod = error.response?.statusCode;
    if (kod != null && kod >= 400 && kod < 500) return null;
  }
  if (retryCount >= 2) return null;
  return Duration(milliseconds: 400 * (retryCount + 1));
}

/// Sistem yazı ölçeğinin uygulanan tavanı (bkz. [RythoApp.build] `builder`).
///
/// Arayüz sabit puntolar üzerine kurulu (`RythoText`); %130'un üstünde kart
/// başlıkları ve iki sütunlu satırlar dar ekranda yerleşimi bozuyor. Tavan
/// yalnız üst uçtadır; küçültme serbesttir.
const double kMaxTextScale = 1.3;

/// Web client id (google-services.json / client_type 3) — Google Sign-In için.
const kServerClientId =
    '770582338651-0kimgrjfj4brfl6k5h3g6amn2rm7ue6a.apps.googleusercontent.com';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();

  // Crashlytics: yalnızca gerçek cihaz/release akışında etkin;
  // debug oturumları ve web rapor kirliliği yaratmasın.
  if (!kIsWeb && !kDebugMode) {
    FlutterError.onError =
        FirebaseCrashlytics.instance.recordFlutterFatalError;
    PlatformDispatcher.instance.onError = (error, stack) {
      FirebaseCrashlytics.instance.recordError(error, stack, fatal: true);
      return true;
    };
  }

  // TÜM diller yüklenir. Eskiden yalnız `'tr_TR'` yükleniyordu ve bu sessiz
  // bir hataydı: `DateFormat('MMM', 'en')` İngilizce sembol verisini
  // bulamayınca yüklü olan tek dile düşüyor, arayüz İngilizce olsa bile
  // tarihler Türkçe basılıyordu ("Ağu 27" / "Eyl 2"). Cihaz turunda
  // "kartlar İngilizceye çevirince de Türkçe kalıyor" diye görüldü.
  await initializeDateFormatting();
  try {
    await GoogleSignIn.instance.initialize(serverClientId: kServerClientId);
  } catch (_) {
    // Web'de serverClientId gerekmez; sessizce geç.
  }
  // Abonelik SDK'sı: anahtar tanımlı değilse sessizce atlanır, uygulama
  // ücretsiz katmanla normal çalışır.
  await initBilling();

  runApp(ProviderScope(retry: rythoRetry, child: const RythoApp()));
}

class RythoApp extends ConsumerWidget {
  const RythoApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Dil hem arayüzü hem backend'in ürettiği yorumları belirler; ikincisini
    // apiProvider aynı sağlayıcıyı izleyerek yapar (bkz. core/api.dart).
    final locale = ref.watch(localeProvider);

    // OT2: Firebase'in e-postaları (şifre sıfırlama, adres doğrulama)
    // şablon dilini BURADAN alır — hiç çağrılmadığı için Türk kullanıcıya
    // İngilizce "Reset your password" gidiyor ve spam sanılıyordu.
    // Çağrı ucuz ve idempotent; dil değişince kendiliğinden güncellenir.
    // GEÇERLİ dil (tercih yoksa sistem dili) — `SystemLocaleObserver`
    // sayesinde "Sistem" tercihinde telefon dili değişince de güncellenir.
    unawaited(FirebaseAuth.instance.setLanguageCode(
        ref.watch(effectiveLocaleProvider.select((l) => l.languageCode))));

    return SystemLocaleObserver(
      // Ön plana dönüşte zorunlu güncelleme eşiği yeniden okunur
      // (bkz. core/app_config.dart).
      child: UpdateGateObserver(
        // Kapı kapanınca (426/409) yığın köke iner: kapı ekranı `_Gate`'in
        // alt ağacında yaşar, basılı bir rotanın altında kalmasın (bkz.
        // core/gate_guard.dart).
        child: GateRootGuard(
          navigatorKey: rythoNavigatorKey,
          child: MaterialApp(
            title: 'Rytho',
            debugShowCheckedModeBanner: false,
            theme: buildRythoTheme(),
            // Sunucu 402 döndüğünde paywall'ı hangi ekranda olursak olalım
            // açabilmek için (bkz. core/api.dart).
            navigatorKey: rythoNavigatorKey,
            locale: locale,
            supportedLocales: kSupportedLocales,
            localizationsDelegates: AppLocalizations.localizationsDelegates,
            // Yazı ölçeği tavanı (cihaz bulgusu): sistem yazı boyutu çok
            // büyükken uzun başlık cümleleri dar ekranda satıra sığmıyor ve
            // sağ taraf kırpılıyordu. Yerleşimler esnetildi (Wrap/Flexible)
            // ama tipografi sabit punto üzerine kurulu: %130 üstü ölçekte
            // kart mimarisi dağılıyor. Tavan yalnız ÜST uçta — kullanıcı
            // yazıyı küçültmek isterse (0,85) ona dokunulmaz.
            builder: (context, child) {
              final mq = MediaQuery.of(context);
              final olcek = mq.textScaler.clamp(maxScaleFactor: kMaxTextScale);
              return MediaQuery(
                data: mq.copyWith(textScaler: olcek),
                child: child ?? const SizedBox.shrink(),
              );
            },
            home: const _Gate(),
          ),
        ),
      ),
    );
  }
}

/// Oturum + onboarding durumuna göre yönlendirme.
class _Gate extends ConsumerWidget {
  const _Gate();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // RevenueCat kimliğini Firebase oturumuna bağlar. İzlenmezse sağlayıcı
    // hiç kurulmaz ve satın almalar anonim kimliğe yazılır (bkz.
    // core/subscription.dart).
    ref.watch(billingIdentityProvider);
    // Bildirim altyapısı: FCM token, saat dilimi ve dil sunucuya yazılır,
    // bildirime dokunma yönlendirmesi kurulur (bkz. core/notifications.dart).
    ref.watch(notificationSyncProvider);
    // Bildirim dili: profildeki `language` alanının tek yazıcısı, geçerli
    // dili izler (bkz. core/language_sync.dart).
    ref.watch(languageSyncListenerProvider);
    // Davet bağlantılarını yakalar (bkz. core/deep_links.dart).
    ref.watch(deepLinkProvider);

    // Zorunlu güncelleme kapısı (F3 → PBZ): sunucu bu derlemeyi asgari
    // sürümün altında ilan ettiyse giriş/onboarding/kabuğa hiç girilmez.
    // İki kaynak: açılış okuması (sunucuya ulaşılamazsa son bilinen eşik)
    // ve açık oturumda herhangi bir isteğe dönen 426. Yanıt beklenmez —
    // splash gecikmesi yok; yalnız kesin "kilitle" kapıyı kapatır.
    if (ref.watch(mustForceUpdateProvider)) {
      return const ForceUpdateScreen();
    }

    final auth = ref.watch(authStateProvider);
    final ekran = auth.when(
      loading: () => const _Splash(),
      error: (e, _) => _Splash(message: '$e'),
      data: (user) {
        if (user == null) return const LoginScreen();
        // Tek cihaz kilidi kapısı (TC-turu K6): bu oturumun bir isteği 409
        // aldıysa onboarding/kabuk yerine çakışma ekranı — zorunlu
        // güncelleme kapısıyla aynı desen. Oturum AÇIK kalır ki "Bu cihazda
        // kullan" kimlikli gidebilsin; navigator yığınına basılmaz, diyalog
        // üstüne diyalog binmez (bkz. core/device_session.dart). Üstte
        // basılı rota varsa `GateRootGuard` yığını köke indirir.
        if (ref.watch(deviceConflictProvider) != null) {
          return const DeviceConflictScreen();
        }
        final profile = ref.watch(profileProvider);
        return profile.when(
          loading: () => const _Splash(),
          error: (e, _) => _Splash(message: '$e'),
          data: (data) {
            if (data == null || data['onboardingCompleted'] != true) {
              // Onboarding'e düşmek NADIR olmalı: yalnızca gerçekten yeni
              // kullanıcı. Cihaz testinde profili tam olan bir kullanıcıya
              // da açıldı ve sebebini ancak bu kararın girdisini görerek
              // bulabiliriz. Yalnızca hata ayıklama derlemesinde.
              assert(() {
                debugPrint('[RYTHO-GATE] onboarding acildi — '
                    'profilVar=${data != null} '
                    'alanlar=${data?.keys.toList() ?? "-"} '
                    'onboardingCompleted=${data?['onboardingCompleted']}');
                return true;
              }());
              return const OnboardingWizard();
            }
            return const AppShell();
          },
        );
      },
    );
    // Sert kesme yerine çapraz geçiş (R12-A1): splash → login/kabuk geçişi
    // eskiden tek karede oluyordu. Key EKRAN SINIFINA bağlı — _Gate her
    // yeniden build'inde yeni instance döner, key olmasa AnimatedSwitcher
    // aynı ekran için bile boşuna geçiş oynatırdı.
    return AnimatedSwitcher(
      duration: reduceMotion(context) ? Duration.zero : RythoMotion.slow,
      switchInCurve: RythoMotion.enter,
      child: KeyedSubtree(
        key: ValueKey(ekran.runtimeType),
        child: ekran,
      ),
    );
  }
}

/// Açılış sahnesi (R12-A1). Eski hâli çıplak spinner + statik "RYTHO"ydu —
/// uygulamanın ilk saniyesi markasızdı, logo yalnız giriş ekranındaydı.
/// Koreografi: logo belirir (600ms) → yazı, harf aralığı açılarak gelir
/// (mühür açılması) → usturlap süzülür. Splash zaten oturum çözülürken
/// görünüyor; sahne süre EKLEMEZ, var olan beklemeyi giydirir.
class _Splash extends StatelessWidget {
  const _Splash({this.message});
  final String? message;

  @override
  Widget build(BuildContext context) {
    final sabit = reduceMotion(context);

    Widget logo = Image.asset('assets/brand/rytho_logo_512.png',
        width: 72, height: 72, filterQuality: FilterQuality.medium);
    Widget spinner = const AstrolabeSpinner(size: 36);
    if (!sabit) {
      logo = logo.animate().fadeIn(duration: RythoMotion.slower).scale(
          begin: const Offset(0.92, 0.92),
          end: const Offset(1, 1),
          duration: RythoMotion.slower,
          curve: RythoMotion.enter);
      spinner =
          spinner.animate(delay: 500.ms).fadeIn(duration: RythoMotion.slow);
    }

    return CosmicScaffold(
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            logo,
            const SizedBox(height: 18),
            _Wordmark(sabit: sabit),
            const SizedBox(height: 28),
            spinner,
            if (message != null) ...[
              const SizedBox(height: 12),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 32),
                child: Text(message!,
                   style: RythoText.body(13, color: RythoColors.parchmentDim),
                    textAlign: TextAlign.center),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// "RYTHO" yazısı: harf aralığı 2→5 açılarak belirir.
class _Wordmark extends StatelessWidget {
  const _Wordmark({required this.sabit});
  final bool sabit;

  @override
  Widget build(BuildContext context) {
    TextStyle stil(double aralik) => RythoText.label(16,
        color: RythoColors.gold).copyWith(letterSpacing: aralik);
    if (sabit) return Text('RYTHO', style: stil(5));
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: 1),
      duration: const Duration(milliseconds: 800),
      // İlk çeyrek bekleme: logo önce gelir, yazı onu izler.
      curve: const Interval(0.25, 1, curve: RythoMotion.enter),
      builder: (_, t, _) => Opacity(
        opacity: t,
        child: Text('RYTHO', style: stil(2 + 3 * t)),
      ),
    );
  }
}
