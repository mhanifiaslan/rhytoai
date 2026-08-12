/// Giriş yöntemleri (F4): hesaba ikinci bir giriş yolu bağlama.
///
/// İki akış:
/// * Google/Apple kullanıcısı ŞİFRE oluşturur → e-posta+şifreyle de
///   girebilir (`linkWithCredential`, yeni hesap AÇILMAZ).
/// * E-posta/şifre kullanıcısı GOOGLE bağlar → tek dokunuş girişi kazanır.
///
/// Tamamen istemci tarafı: sağlayıcı listesi Firebase token'ında yaşar,
/// sunucuda ayrıca tutulmaz. Hata eşlemesi phone_verify_screen desenini
/// izler; bilinmeyen kodlar Crashlytics'e gider.
library;

import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_crashlytics/firebase_crashlytics.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../../core/auth_service.dart';
import '../../theme/rytho_theme.dart';
import '../../theme/rytho_tokens.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/common.dart';
import '../../widgets/glass.dart';
import '../../l10n/app_localizations.dart';
import 'profile_sections.dart' show SettingsPage;

/// Profil satırındaki özet: "Google · Şifre" gibi.
String signInMethodsSummary(User? user, AppLocalizations l10n) {
  if (user == null) return '';
  final adlar = <String>[];
  for (final p in user.providerData) {
    switch (p.providerId) {
      case 'google.com':
        adlar.add('Google');
      case 'apple.com':
        adlar.add('Apple');
      case 'password':
        adlar.add(l10n.password);
      case 'phone':
        adlar.add(l10n.providerPhone);
    }
  }
  return adlar.join(' · ');
}

class SignInMethodsScreen extends StatefulWidget {
  const SignInMethodsScreen({super.key});

  @override
  State<SignInMethodsScreen> createState() => _SignInMethodsScreenState();
}

class _SignInMethodsScreenState extends State<SignInMethodsScreen> {
  final _emailCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  bool _busy = false;
  String? _hata;
  bool _sifreGizli = true;

  @override
  void initState() {
    super.initState();
    _emailCtrl.text = FirebaseAuth.instance.currentUser?.email ?? '';
  }

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passCtrl.dispose();
    super.dispose();
  }

  bool _bagli(String providerId) =>
      FirebaseAuth.instance.currentUser?.providerData
          .any((p) => p.providerId == providerId) ??
      false;

  String _baglamaHatasi(FirebaseAuthException e, AppLocalizations l10n) {
    switch (e.code) {
      case 'provider-already-linked':
        return l10n.linkAlreadyLinked;
      case 'credential-already-in-use':
      case 'email-already-in-use':
        return l10n.linkCredentialInUse;
      case 'requires-recent-login':
        return l10n.linkRequiresRecentLogin;
      case 'weak-password':
        return l10n.passwordTooShort;
      case 'invalid-email':
        return l10n.authInvalidEmail;
      default:
        if (!kDebugMode) {
          FirebaseCrashlytics.instance.recordError(
              'link-provider: ${e.code}: ${e.message}', StackTrace.current,
              fatal: false);
        }
        return l10n.authFailed;
    }
  }

  Future<void> _calistir(Future<void> Function() is_,
      {required String basarili}) async {
    final l10n = AppLocalizations.of(context);
    final mesajci = ScaffoldMessenger.of(context);
    setState(() {
      _busy = true;
      _hata = null;
    });
    try {
      await is_();
      if (!mounted) return;
      mesajci.showSnackBar(SnackBar(content: Text(basarili)));
      setState(() {}); // sağlayıcı listesi değişti; ✓ rozetleri tazelensin
    } on FirebaseAuthException catch (e) {
      if (mounted) setState(() => _hata = _baglamaHatasi(e, l10n));
    } catch (e) {
      if (mounted) setState(() => _hata = l10n.authFailed);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _sifreKaydet() async {
    final l10n = AppLocalizations.of(context);
    final sorun = validatePassword(_passCtrl.text);
    if (sorun != null) {
      setState(() => _hata = sorun == PasswordIssue.tooShort
          ? l10n.passwordTooShort
          : l10n.passwordTooSimple);
      return;
    }
    if (_emailCtrl.text.trim().isEmpty) {
      setState(() => _hata = l10n.authInvalidEmail);
      return;
    }
    await _calistir(
        () => linkPassword(_emailCtrl.text, _passCtrl.text),
        basarili: l10n.linkPasswordDone);
    if (mounted && _hata == null) _passCtrl.clear();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final sifreBagli = _bagli('password');
    final googleBagli = _bagli('google.com');
    final appleBagli = _bagli('apple.com');
    final telefonBagli = _bagli('phone');

    Widget rozet(bool bagli) => bagli
        ? const Icon(Icons.check_circle_rounded,
            size: 18, color: RythoColors.goldBright)
        : const Icon(Icons.radio_button_unchecked,
            size: 18, color: RythoColors.parchmentDim);

    return SettingsPage(title: l10n.signInMethodsTitle, children: [
      Padding(
        padding: const EdgeInsets.fromLTRB(
            RythoSpace.lg, 0, RythoSpace.lg, RythoSpace.md),
        child: Text(l10n.signInMethodsBody,
            style: RythoText.body(12.5, color: RythoColors.parchmentDim)),
      ),
      GlassPanel(
        child: Column(children: [
          SettingsRow(
            icon: Icons.g_mobiledata_rounded,
            title: 'Google',
            trailing: googleBagli
                ? rozet(true)
                : TextButton(
                    onPressed: _busy
                        ? null
                        : () => _calistir(linkGoogle,
                            basarili: l10n.linkGoogleDone),
                    child: Text(l10n.linkAction),
                  ),
          ),
          if (appleSignInAvailable || appleBagli) ...[
            const Divider(height: 1, indent: RythoSpace.lg),
            SettingsRow(
              icon: Icons.apple_rounded,
              title: 'Apple',
              trailing: rozet(appleBagli),
            ),
          ],
          const Divider(height: 1, indent: RythoSpace.lg),
          SettingsRow(
            icon: Icons.sms_outlined,
            title: l10n.providerPhone,
            trailing: rozet(telefonBagli),
          ),
          const Divider(height: 1, indent: RythoSpace.lg),
          SettingsRow(
            icon: Icons.key_outlined,
            title: l10n.password,
            trailing: rozet(sifreBagli),
          ),
        ]),
      ),
      const SizedBox(height: RythoSpace.md),
      GlassPanel(
        label: sifreBagli
            ? l10n.changePasswordSection
            : l10n.setPasswordSection,
        child:
            Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(
            sifreBagli ? l10n.changePasswordBody : l10n.setPasswordBody,
            style: RythoText.body(12.5, color: RythoColors.parchmentDim),
          ),
          const SizedBox(height: 12),
          if (!sifreBagli) ...[
            // Apple "Hide My Email" gerçeği: adres varsayılmaz, düzenlenir.
            TextField(
              controller: _emailCtrl,
              keyboardType: TextInputType.emailAddress,
              autocorrect: false,
              style: RythoText.body(15),
              decoration: InputDecoration(hintText: l10n.email),
            ),
            const SizedBox(height: 10),
          ],
          TextField(
            controller: _passCtrl,
            obscureText: _sifreGizli,
            style: RythoText.body(15),
            decoration: InputDecoration(
              hintText: l10n.password,
              errorText: _hata,
              suffixIcon: IconButton(
                icon: Icon(
                    _sifreGizli
                        ? Icons.visibility_outlined
                        : Icons.visibility_off_outlined,
                    size: 18),
                onPressed: () =>
                    setState(() => _sifreGizli = !_sifreGizli),
              ),
            ),
          ),
          const SizedBox(height: 12),
          GoldButton(
            text: sifreBagli
                ? l10n.changePasswordAction
                : l10n.setPasswordAction,
            busy: _busy,
            onPressed: _busy ? null : _sifreKaydet,
          ),
        ]),
      ),
    ]);
  }
}
