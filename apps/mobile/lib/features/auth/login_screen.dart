import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  bool _busy = false;

  Future<void> _signIn() async {
    setState(() => _busy = true);
    try {
      if (kIsWeb) {
        await FirebaseAuth.instance.signInWithPopup(GoogleAuthProvider());
      } else {
        final account = await GoogleSignIn.instance.authenticate();
        final auth = account.authentication;
        final credential =
            GoogleAuthProvider.credential(idToken: auth.idToken);
        await FirebaseAuth.instance.signInWithCredential(credential);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Giriş başarısız: $e')));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 32),
          child: Column(
            children: [
              const Spacer(flex: 2),
              const AstrolabeSpinner(size: 120),
              const SizedBox(height: 40),
              Text('RYTHO', style: RythoText.label(22, color: RythoColors.gold)),
              const SizedBox(height: 12),
              Text('Gök Atlası',
                  style: RythoText.display(40, w: FontWeight.w600)),
              const SizedBox(height: 16),
              Text(
                'Kadim bilgelik, hassas gökyüzü hesabıyla buluşur.\n'
                'Haritan çizilir, yüzün okunur, yolun aydınlanır.',
                textAlign: TextAlign.center,
                style: RythoText.body(15, color: RythoColors.parchmentDim),
              ),
              const Spacer(flex: 3),
              SizedBox(
                width: double.infinity,
                child: GoldButton(
                  text: 'Google ile giriş',
                  busy: _busy,
                  onPressed: _signIn,
                ),
              ),
              const SizedBox(height: 16),
              Text(
                'Devam ederek gizlilik ilkelerini kabul etmiş olursun.\n'
                'Yorumlar içgörü amaçlıdır; tıbbi/finansal tavsiye değildir.',
                textAlign: TextAlign.center,
                style: RythoText.body(11, color: RythoColors.parchmentDim),
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}
