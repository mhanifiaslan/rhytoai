import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_crashlytics/firebase_crashlytics.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:intl/date_symbol_data_local.dart';

import 'core/providers.dart';
import 'features/auth/login_screen.dart';
import 'features/onboarding/onboarding_screen.dart';
import 'features/shell/app_shell.dart';
import 'theme/rytho_theme.dart';
import 'widgets/atlas_widgets.dart';
import 'widgets/cosmic_scaffold.dart';

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

  await initializeDateFormatting('tr_TR');
  try {
    await GoogleSignIn.instance.initialize(serverClientId: kServerClientId);
  } catch (_) {
    // Web'de serverClientId gerekmez; sessizce geç.
  }
  runApp(const ProviderScope(child: RythoApp()));
}

class RythoApp extends StatelessWidget {
  const RythoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Rytho',
      debugShowCheckedModeBanner: false,
      theme: buildRythoTheme(),
      home: const _Gate(),
    );
  }
}

/// Oturum + onboarding durumuna göre yönlendirme.
class _Gate extends ConsumerWidget {
  const _Gate();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authStateProvider);
    return auth.when(
      loading: () => const _Splash(),
      error: (e, _) => _Splash(message: '$e'),
      data: (user) {
        if (user == null) return const LoginScreen();
        final profile = ref.watch(profileProvider);
        return profile.when(
          loading: () => const _Splash(),
          error: (e, _) => _Splash(message: '$e'),
          data: (data) {
            if (data == null || data['onboardingCompleted'] != true) {
              return const OnboardingScreen();
            }
            return const AppShell();
          },
        );
      },
    );
  }
}

class _Splash extends StatelessWidget {
  const _Splash({this.message});
  final String? message;

  @override
  Widget build(BuildContext context) {
    return CosmicScaffold(
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const AstrolabeSpinner(size: 56),
            const SizedBox(height: 24),
            Text('RYTHO', style: RythoText.label(16, color: RythoColors.gold)),
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
