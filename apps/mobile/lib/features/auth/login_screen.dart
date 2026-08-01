import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../../core/auth_service.dart';
import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/glass.dart';
import '../profile/legal_page.dart';

/// Giriş ve kayıt.
///
/// Düzen kararı: **form önce, sosyal giriş sonra.** Sosyal düğmeler üstteyken
/// e-posta akışı ikincil görünüyordu; ayrıca Apple'ın kuralı Apple ile
/// Giriş'in diğer sağlayıcılardan daha az görünür olmamasını istiyor.
///
/// Mağaza zorunlulukları burada karşılanıyor:
/// - **Guideline 4.8:** Google sunuluyorsa iOS'ta Apple ile Giriş de zorunlu.
/// - Hukuki metinlere **tıklanabilir** bağlantı: kullanıcı kabul ettiğini
///   okuyabilmeli. Eskiden yalnızca "kabul etmiş olursun" yazıyordu.
/// - Kayıtta yaş beyanı: kullanım şartlarındaki 13 yaş sınırının arayüzdeki
///   karşılığı. Sözleşmede olup ekranda olmayan şart yok hükmündedir.
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  /// 0: Giriş yap, 1: Üye ol
  int _segment = 0;

  bool _googleBusy = false;
  bool _appleBusy = false;
  bool _emailBusy = false;

  /// Herhangi bir giriş sürüyorsa tüm yollar kilitlenir; aksi halde iki
  /// giriş aynı anda başlatılabiliyordu.
  bool get _busy => _googleBusy || _appleBusy || _emailBusy;

  final _formKey = GlobalKey<FormState>();
  final _nameCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  final _pass2Ctrl = TextEditingController();

  // Klavyedeki "Sonraki" tuşunun çalışması için odak zinciri gerekiyor;
  // Flutter alanlar arası geçişi kendiliğinden yapmaz.
  final _emailFocus = FocusNode();
  final _passFocus = FocusNode();
  final _pass2Focus = FocusNode();

  bool _obscurePass = true;
  bool _obscurePass2 = true;
  bool _ageConfirmed = false;
  bool _ageError = false;

  @override
  void dispose() {
    for (final c in [_nameCtrl, _emailCtrl, _passCtrl, _pass2Ctrl]) {
      c.dispose();
    }
    for (final f in [_emailFocus, _passFocus, _pass2Focus]) {
      f.dispose();
    }
    super.dispose();
  }

  void _showSnack(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }

  /// Sekme değişince formu sıfırla.
  ///
  /// Eskiden şifre alanı ve hata mesajları geçişte duruyordu; kullanıcı
  /// "Üye ol"a geçtiğinde giriş denemesinden kalan şifreyi görüyordu.
  void _changeSegment(int index) {
    if (index == _segment) return;
    setState(() {
      _segment = index;
      _passCtrl.clear();
      _pass2Ctrl.clear();
      _ageError = false;
      _formKey.currentState?.reset();
    });
  }

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
        return l10n.passwordTooShort;
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

  Future<void> _runSocial(
      Future<void> Function() action, void Function(bool) setBusy) async {
    final l10n = AppLocalizations.of(context);
    setState(() => setBusy(true));
    try {
      await action();
    } on FirebaseAuthException catch (e) {
      _showSnack(_authErrorMessage(e));
    } catch (_) {
      // Kullanıcı akışı iptal ettiyse de buraya düşüyor; sessiz kalmak
      // yerine nötr bir mesaj göstermek "hiçbir şey olmadı" hissini önler.
      _showSnack(l10n.authFailed);
    } finally {
      if (mounted) setState(() => setBusy(false));
    }
  }

  Future<void> _submitEmail() async {
    final l10n = AppLocalizations.of(context);
    FocusScope.of(context).unfocus();

    final isRegister = _segment == 1;
    // Yaş beyanı form doğrulamasının dışında (onay kutusu), ayrıca kontrol.
    if (isRegister && !_ageConfirmed) {
      setState(() => _ageError = true);
      _showSnack(l10n.ageRequired);
      return;
    }
    if (!(_formKey.currentState?.validate() ?? false)) return;

    setState(() => _emailBusy = true);
    final email = _emailCtrl.text.trim();
    try {
      if (isRegister) {
        await registerWithEmail(
          email: email,
          password: _passCtrl.text,
          displayName: _nameCtrl.text.trim(),
        );
        _showSnack(l10n.verificationSent(email));
      } else {
        await signInWithEmail(email, _passCtrl.text);
      }
      // Yönlendirme _Gate üzerinden otomatik olur.
    } on FirebaseAuthException catch (e) {
      // Google/Apple ile açılmış bir hesaba şifreyle girilmeye çalışılıyorsa
      // Firebase yalnızca "geçersiz kimlik" diyor ve kullanıcı çıkmaza
      // giriyordu. Hangi sağlayıcının kullanıldığını sormak mümkün değil
      // (bkz. core/auth_service.dart) — bu yüzden her iki olasılığı birden
      // söylüyoruz. Bilgi sızdırmadan çıkmazı çözer.
      if (!isRegister && e.code == 'invalid-credential') {
        _showSnack(l10n.useGoogleInstead);
        return;
      }
      _showSnack(_authErrorMessage(e));
    } catch (_) {
      _showSnack(l10n.authFailed);
    } finally {
      if (mounted) setState(() => _emailBusy = false);
    }
  }

  /// Şifre sıfırlama.
  ///
  /// **Sonuç ne olursa olsun aynı mesaj.** Hatayı göstermek "bu e-posta
  /// kayıtlı mı" bilgisini sızdırırdı.
  Future<void> _resetPassword() async {
    final l10n = AppLocalizations.of(context);
    final email = _emailCtrl.text.trim();
    if (email.isEmpty || !email.contains('@')) {
      _showSnack(l10n.enterEmailFirst);
      return;
    }
    await sendPasswordReset(email);
    _showSnack(l10n.resetLinkSentNeutral);
  }

  void _openLegal(String title, LegalSections Function(String) sections) {
    Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => LegalPage(
        title: title,
        sections: sections(Localizations.localeOf(context).languageCode),
      ),
    ));
  }

  Widget _obscureToggle(bool obscure, VoidCallback onTap, String label) {
    return IconButton(
      onPressed: onTap,
      tooltip: label,
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
              // Şifre yöneticilerinin alanları tanıması için; olmadan
              // otomatik doldurma ve "güçlü şifre öner" hiç çalışmıyordu.
              autofillHints: const [AutofillHints.name],
              onFieldSubmitted: (_) => _emailFocus.requestFocus(),
              decoration: InputDecoration(labelText: l10n.nameLabel),
              validator: (v) => (v == null || v.trim().isEmpty)
                  ? l10n.authNameRequired
                  : null,
            ),
            const SizedBox(height: 12),
          ],
          TextFormField(
            controller: _emailCtrl,
            focusNode: _emailFocus,
            style: RythoText.body(15),
            keyboardType: TextInputType.emailAddress,
            autocorrect: false,
            textInputAction: TextInputAction.next,
            autofillHints: const [AutofillHints.email],
            onFieldSubmitted: (_) => _passFocus.requestFocus(),
            decoration: InputDecoration(labelText: l10n.email),
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
            focusNode: _passFocus,
            style: RythoText.body(15),
            obscureText: _obscurePass,
            textInputAction:
                isRegister ? TextInputAction.next : TextInputAction.done,
            autofillHints: [
              isRegister ? AutofillHints.newPassword : AutofillHints.password,
            ],
            onFieldSubmitted: (_) =>
                isRegister ? _pass2Focus.requestFocus() : _submitEmail(),
            decoration: InputDecoration(
              labelText: l10n.password,
              helperText: isRegister ? l10n.passwordRuleHint : null,
              helperStyle:
                  RythoText.body(11, color: RythoColors.parchmentDim),
              suffixIcon: _obscureToggle(_obscurePass,
                  () => setState(() => _obscurePass = !_obscurePass),
                  l10n.password),
            ),
            validator: (v) {
              final value = v ?? '';
              // Girişte kural uygulanmaz: eski hesapların şifresi daha zayıf
              // olabilir ve kendi kuralımız yüzünden kimseyi kendi hesabından
              // dışarıda bırakamayız.
              if (!isRegister) {
                return value.isEmpty ? l10n.passwordTooShort : null;
              }
              return switch (validatePassword(value)) {
                PasswordIssue.tooShort => l10n.passwordTooShort,
                PasswordIssue.tooSimple => l10n.passwordTooSimple,
                null => null,
              };
            },
          ),
          if (isRegister) ...[
            const SizedBox(height: 12),
            TextFormField(
              controller: _pass2Ctrl,
              focusNode: _pass2Focus,
              style: RythoText.body(15),
              obscureText: _obscurePass2,
              textInputAction: TextInputAction.done,
              autofillHints: const [AutofillHints.newPassword],
              onFieldSubmitted: (_) => _submitEmail(),
              decoration: InputDecoration(
                labelText: l10n.passwordRepeat,
                suffixIcon: _obscureToggle(_obscurePass2,
                    () => setState(() => _obscurePass2 = !_obscurePass2),
                    l10n.passwordRepeat),
              ),
              validator: (v) =>
                  v != _passCtrl.text ? l10n.passwordsDoNotMatch : null,
            ),
            const SizedBox(height: 6),
            // Yaş beyanı — kullanım şartlarındaki 13 yaş sınırının karşılığı.
            CheckboxListTile(
              value: _ageConfirmed,
              onChanged: (v) => setState(() {
                _ageConfirmed = v ?? false;
                if (_ageConfirmed) _ageError = false;
              }),
              contentPadding: EdgeInsets.zero,
              dense: true,
              controlAffinity: ListTileControlAffinity.leading,
              activeColor: RythoColors.magenta,
              title: Text(l10n.ageConfirm,
                  style: RythoText.body(13,
                      color: _ageError
                          ? RythoColors.copper
                          : RythoColors.parchment)),
            ),
          ],
          const SizedBox(height: 12),
          GoldButton(
            text: isRegister ? l10n.signUp : l10n.signIn,
            busy: _emailBusy,
            onPressed: _busy ? null : _submitEmail,
          ),
          if (!isRegister) ...[
            const SizedBox(height: 8),
            Center(
              child: TextButton(
                onPressed: _busy ? null : _resetPassword,
                child: Text(
                  l10n.forgotPassword,
                  style: RythoText.body(13, color: RythoColors.parchmentDim)
                      .copyWith(
                          decoration: TextDecoration.underline,
                          decorationColor: RythoColors.parchmentDim),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  /// Hukuki onay — metinler TIKLANABİLİR.
  ///
  /// Kullanıcının kabul ettiği şeyi okuyamaması hem hukuki bir boşluk hem
  /// mağaza incelemesinde sorulan bir madde.
  Widget _buildConsent() {
    final l10n = AppLocalizations.of(context);
    final normal = RythoText.body(11, color: RythoColors.parchmentDim);
    final link = normal.copyWith(
      color: RythoColors.lilac,
      decoration: TextDecoration.underline,
      decorationColor: RythoColors.lilac,
    );

    return Column(children: [
      Text.rich(
        TextSpan(children: [
          TextSpan(text: l10n.consentPrefix, style: normal),
          WidgetSpan(
            alignment: PlaceholderAlignment.baseline,
            baseline: TextBaseline.alphabetic,
            child: GestureDetector(
              onTap: () =>
                  _openLegal(l10n.termsOfUse, termsOfUseSections),
              child: Text(l10n.termsOfUse, style: link),
            ),
          ),
          TextSpan(text: l10n.consentAnd, style: normal),
          WidgetSpan(
            alignment: PlaceholderAlignment.baseline,
            baseline: TextBaseline.alphabetic,
            child: GestureDetector(
              onTap: () =>
                  _openLegal(l10n.privacyPolicy, privacyPolicySections),
              child: Text(l10n.privacyPolicy, style: link),
            ),
          ),
          TextSpan(text: l10n.consentSuffix, style: normal),
        ]),
        textAlign: TextAlign.center,
      ),
      const SizedBox(height: 8),
      // Sorumluluk reddi ayrı bir cümle: hukuki onayla aynı paragrafta
      // olduğunda ikisi de okunmuyordu.
      Text(l10n.insightNote, textAlign: TextAlign.center, style: normal),
    ]);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    var stagger = 0;
    Duration next() => Duration(milliseconds: 70 * stagger++);

    return CosmicScaffold(
      body: SafeArea(
        // AutofillGroup olmadan şifre yöneticileri alanları tek bir form
        // olarak görmüyor ve kaydetmeyi önermiyor.
        child: AutofillGroup(
          child: ListView(
            padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 24),
            children: [
              const SizedBox(height: 12),
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

              // Form önce.
              GlassPanel(
                margin: EdgeInsets.zero,
                padding: const EdgeInsets.fromLTRB(0, 16, 0, 18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    GlassSegments(
                      labels: [l10n.signIn, l10n.signUp],
                      index: _segment,
                      onChanged: _changeSegment,
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

              Padding(
                padding: const EdgeInsets.symmetric(vertical: 16),
                child: Row(children: [
                  const Expanded(child: Divider()),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    child: Text(l10n.orDivider,
                        style: RythoText.body(11,
                            color: RythoColors.parchmentDim)),
                  ),
                  const Expanded(child: Divider()),
                ]),
              ),

              // Sosyal giriş sonra. iOS'ta Apple ÜSTTE: Apple'ın kuralı
              // kendi düğmesinin diğerlerinden daha az görünür olmamasını
              // istiyor.
              if (appleSignInAvailable) ...[
                GoldButton(
                  text: l10n.signInWithApple,
                  busy: _appleBusy,
                  onPressed: _busy
                      ? null
                      : () => _runSocial(signInWithApple,
                          (v) => _appleBusy = v),
                ),
                const SizedBox(height: 10),
              ],
              GoldButton(
                text: l10n.signInWithGoogle,
                busy: _googleBusy,
                filled: !appleSignInAvailable,
                onPressed: _busy
                    ? null
                    : () => _runSocial(signInWithGoogle,
                        (v) => _googleBusy = v),
              ),

              const SizedBox(height: 22),
              _buildConsent().animate(delay: next()).fadeIn(duration: 400.ms),
              const SizedBox(height: 8),
            ],
          ),
        ),
      ),
    );
  }
}
