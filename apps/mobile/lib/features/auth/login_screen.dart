import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/glass.dart';
import '../../l10n/app_localizations.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  bool _googleBusy = false;
  bool _emailBusy = false;

  /// 0: Giriş yap, 1: Üye ol
  int _segment = 0;

  final _formKey = GlobalKey<FormState>();
  final _nameCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  final _pass2Ctrl = TextEditingController();
  bool _obscurePass = true;
  bool _obscurePass2 = true;

  @override
  void dispose() {
    _nameCtrl.dispose();
    _emailCtrl.dispose();
    _passCtrl.dispose();
    _pass2Ctrl.dispose();
    super.dispose();
  }

  void _showSnack(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }

  /// FirebaseAuthException kodlarını kullanıcı dostu mesajlara çevirir.
  String _authErrorMessage(FirebaseAuthException e) {
    final l10n = AppLocalizations.of(context);
    switch (e.code) {
      case 'user-not-found':
      case 'wrong-password':
      case 'invalid-credential':
        return l10n.authWrongCredentials;
      case 'email-already-in-use':
        return l10n.authEmailInUse;
      case 'weak-password':
        return l10n.authWeakPassword;
      case 'invalid-email':
        return l10n.authInvalidEmail;
      case 'too-many-requests':
        return l10n.authTooManyRequests;
      case 'operation-not-allowed':
        return l10n.authDisabled;
      case 'network-request-failed':
        return l10n.authNetwork;
      default:
        return l10n.authFailed;
    }
  }

  Future<void> _signInWithGoogle() async {
    final l10n = AppLocalizations.of(context);
    setState(() => _googleBusy = true);
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
    } on FirebaseAuthException catch (e) {
      _showSnack(_authErrorMessage(e));
    } catch (e) {
      _showSnack(l10n.authFailed);
    } finally {
      if (mounted) setState(() => _googleBusy = false);
    }
  }

  /// Segmente göre e-posta ile giriş yapar ya da yeni hesap oluşturur.
  Future<void> _submitEmail() async {
    final l10n = AppLocalizations.of(context);
    FocusScope.of(context).unfocus();
    if (!(_formKey.currentState?.validate() ?? false)) return;
    setState(() => _emailBusy = true);
    try {
      final email = _emailCtrl.text.trim();
      final password = _passCtrl.text;
      if (_segment == 0) {
        await FirebaseAuth.instance
            .signInWithEmailAndPassword(email: email, password: password);
      } else {
        final credential = await FirebaseAuth.instance
            .createUserWithEmailAndPassword(email: email, password: password);
        // Adı Auth profiline de yaz; DM'ler gibi yerlerde
        // user.displayName kullanılıyor.
        await credential.user?.updateDisplayName(_nameCtrl.text.trim());
      }
      // Yönlendirme _Gate üzerinden otomatik olur.
    } on FirebaseAuthException catch (e) {
      _showSnack(_authErrorMessage(e));
    } catch (_) {
      _showSnack(l10n.authFailed);
    } finally {
      if (mounted) setState(() => _emailBusy = false);
    }
  }

  /// Şifre sıfırlama e-postası gönderir.
  Future<void> _resetPassword() async {
    final l10n = AppLocalizations.of(context);
    final email = _emailCtrl.text.trim();
    if (email.isEmpty || !email.contains('@')) {
      _showSnack(l10n.enterEmailFirst);
      return;
    }
    try {
      await FirebaseAuth.instance.sendPasswordResetEmail(email: email);
      _showSnack(l10n.resetLinkSent);
    } on FirebaseAuthException catch (e) {
      _showSnack(_authErrorMessage(e));
    }
  }

  InputDecoration _fieldDecoration(String label, {Widget? suffixIcon}) {
    return InputDecoration(labelText: label, suffixIcon: suffixIcon);
  }

  /// Şifre alanları için gizle/göster ikonu.
  Widget _obscureToggle(bool obscure, VoidCallback onTap) {
    return IconButton(
      onPressed: onTap,
      icon: Icon(
        obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined,
        size: 20,
        color: RythoColors.parchmentDim,
      ),
    );
  }

  Widget _buildEmailForm() {
    final l10n = AppLocalizations.of(context);
    final isRegister = _segment == 1;
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (isRegister) ...[
            TextFormField(
              controller: _nameCtrl,
              style: RythoText.body(15),
              textCapitalization: TextCapitalization.words,
              keyboardType: TextInputType.name,
              textInputAction: TextInputAction.next,
              decoration: _fieldDecoration(l10n.nameLabel),
              validator: (v) =>
                  (v == null || v.trim().isEmpty) ? l10n.authNameRequired : null,
            ),
            const SizedBox(height: 12),
          ],
          TextFormField(
            controller: _emailCtrl,
            style: RythoText.body(15),
            keyboardType: TextInputType.emailAddress,
            autocorrect: false,
            textInputAction: TextInputAction.next,
            decoration: _fieldDecoration(l10n.email),
            validator: (v) {
              final value = v?.trim() ?? '';
              if (value.isEmpty || !value.contains('@')) {
                return l10n.authInvalidEmail;
              }
              return null;
            },
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _passCtrl,
            style: RythoText.body(15),
            obscureText: _obscurePass,
            textInputAction:
                isRegister ? TextInputAction.next : TextInputAction.done,
            onFieldSubmitted: isRegister ? null : (_) => _submitEmail(),
            decoration: _fieldDecoration(
              l10n.password,
              suffixIcon: _obscureToggle(
                  _obscurePass, () => setState(() => _obscurePass = !_obscurePass)),
            ),
            validator: (v) =>
                (v == null || v.length < 6) ? l10n.authWeakPassword : null,
          ),
          if (isRegister) ...[
            const SizedBox(height: 12),
            TextFormField(
              controller: _pass2Ctrl,
              style: RythoText.body(15),
              obscureText: _obscurePass2,
              textInputAction: TextInputAction.done,
              onFieldSubmitted: (_) => _submitEmail(),
              decoration: _fieldDecoration(
                l10n.passwordRepeat,
                suffixIcon: _obscureToggle(_obscurePass2,
                    () => setState(() => _obscurePass2 = !_obscurePass2)),
              ),
              validator: (v) =>
                  v != _passCtrl.text ? l10n.passwordsDoNotMatch : null,
            ),
          ],
          const SizedBox(height: 18),
          GoldButton(
            text: isRegister ? l10n.signUp : l10n.signIn,
            busy: _emailBusy,
            onPressed: _submitEmail,
          ),
          if (!isRegister) ...[
            const SizedBox(height: 10),
            Center(
              child: TextButton(
                onPressed: _resetPassword,
                child: Text(l10n.forgotPassword,
                    style: RythoText.body(13, color: RythoColors.parchmentDim)
                        .copyWith(decoration: TextDecoration.underline,
                            decorationColor: RythoColors.parchmentDim)),
              ),
            ),
          ],
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    var stagger = 0;
    Duration next() => Duration(milliseconds: 70 * stagger++);

    return CosmicScaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 24),
          children: [
            const SizedBox(height: 12),
            // Nefes alan degrade ✦ küresi
            Center(
              child: Container(
                width: 92,
                height: 92,
                alignment: Alignment.center,
                decoration: const BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: RythoColors.primaryGradient,
                  boxShadow: [
                    BoxShadow(color: RythoColors.magentaGlow, blurRadius: 44),
                  ],
                ),
                child: const Text('✦',
                    style: TextStyle(fontSize: 40, color: Colors.white)),
              )
                  .animate(onPlay: (c) => c.repeat(reverse: true))
                  .scale(
                      begin: const Offset(1, 1),
                      end: const Offset(1.06, 1.06),
                      duration: 1500.ms,
                      curve: Curves.easeInOut),
            ).animate(delay: next()).fadeIn(duration: 500.ms),
            const SizedBox(height: 26),
            Center(
              child: Text('RYTHO',
                  style: RythoText.label(20, color: RythoColors.lilac)),
            ).animate(delay: next()).fadeIn(duration: 400.ms),
            const SizedBox(height: 8),
            Center(
              child: Text(l10n.appHeadline,
                  textAlign: TextAlign.center,
                  style: RythoText.display(30)),
            ).animate(delay: next()).fadeIn(duration: 400.ms).slideY(
                begin: 0.1, curve: Curves.easeOutCubic),
            const SizedBox(height: 12),
            Text(
              l10n.appTagline,
              textAlign: TextAlign.center,
              style: RythoText.body(14.5, color: RythoColors.parchmentDim),
            ).animate(delay: next()).fadeIn(duration: 400.ms),
            const SizedBox(height: 26),
            GoldButton(
              text: l10n.signInWithGoogle,
              busy: _googleBusy,
              onPressed: _signInWithGoogle,
            ).animate(delay: next()).fadeIn(duration: 400.ms).slideY(
                begin: 0.08, curve: Curves.easeOutCubic),
            // Ayraç: — ya da —
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 16),
              child: Row(children: [
                const Expanded(child: Divider()),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  child: Text(l10n.orDivider,
                      style:
                          RythoText.body(11, color: RythoColors.parchmentDim)),
                ),
                const Expanded(child: Divider()),
              ]),
            ),
            GlassPanel(
              margin: EdgeInsets.zero,
              // GlassSegments kendi içinde 16px yatay marj taşıdığı için
              // panel yatay dolgusu sıfır; form aynı marjla hizalanır.
              padding: const EdgeInsets.fromLTRB(0, 16, 0, 18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  GlassSegments(
                    labels: [l10n.signIn, l10n.signUp],
                    index: _segment,
                    onChanged: (i) {
                      if (i == _segment) return;
                      setState(() => _segment = i);
                    },
                  ),
                  const SizedBox(height: 18),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: _buildEmailForm(),
                  ),
                ],
              ),
            ).animate(delay: next()).fadeIn(duration: 400.ms).slideY(
                begin: 0.06, curve: Curves.easeOutCubic),
            const SizedBox(height: 20),
            Text(
              l10n.consentNote,
              textAlign: TextAlign.center,
              style: RythoText.body(11, color: RythoColors.parchmentDim),
            ).animate(delay: next()).fadeIn(duration: 400.ms),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }
}
