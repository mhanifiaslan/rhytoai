import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/glass.dart';

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

  /// FirebaseAuthException kodlarını kullanıcı dostu Türkçe mesajlara çevirir.
  String _authErrorMessage(FirebaseAuthException e) {
    switch (e.code) {
      case 'user-not-found':
      case 'wrong-password':
      case 'invalid-credential':
        return 'E-posta veya şifre hatalı.';
      case 'email-already-in-use':
        return 'Bu e-posta zaten kayıtlı. Giriş yapmayı deneyin.';
      case 'weak-password':
        return 'Şifre en az 6 karakter olmalı.';
      case 'invalid-email':
        return 'Geçerli bir e-posta yaz.';
      case 'too-many-requests':
        return 'Çok fazla deneme. Biraz sonra tekrar dene.';
      case 'operation-not-allowed':
        return 'E-posta ile giriş şu an kapalı.';
      case 'network-request-failed':
        return 'Bağlantı kurulamadı. İnternetini kontrol et.';
      default:
        return 'Bir şeyler ters gitti. Tekrar dene.';
    }
  }

  Future<void> _signInWithGoogle() async {
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
      _showSnack('Giriş başarısız: $e');
    } finally {
      if (mounted) setState(() => _googleBusy = false);
    }
  }

  /// Segmente göre e-posta ile giriş yapar ya da yeni hesap oluşturur.
  Future<void> _submitEmail() async {
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
      _showSnack('Bir şeyler ters gitti. Tekrar dene.');
    } finally {
      if (mounted) setState(() => _emailBusy = false);
    }
  }

  /// Şifre sıfırlama e-postası gönderir.
  Future<void> _resetPassword() async {
    final email = _emailCtrl.text.trim();
    if (email.isEmpty || !email.contains('@')) {
      _showSnack('Önce e-posta adresini yaz.');
      return;
    }
    try {
      await FirebaseAuth.instance.sendPasswordResetEmail(email: email);
      _showSnack('Şifre sıfırlama bağlantısı $email adresine gönderildi.');
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
              decoration: _fieldDecoration('Ad'),
              validator: (v) =>
                  (v == null || v.trim().isEmpty) ? 'Adını yaz.' : null,
            ),
            const SizedBox(height: 12),
          ],
          TextFormField(
            controller: _emailCtrl,
            style: RythoText.body(15),
            keyboardType: TextInputType.emailAddress,
            autocorrect: false,
            textInputAction: TextInputAction.next,
            decoration: _fieldDecoration('E-posta'),
            validator: (v) {
              final value = v?.trim() ?? '';
              if (value.isEmpty || !value.contains('@')) {
                return 'Geçerli bir e-posta yaz.';
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
              'Şifre',
              suffixIcon: _obscureToggle(
                  _obscurePass, () => setState(() => _obscurePass = !_obscurePass)),
            ),
            validator: (v) =>
                (v == null || v.length < 6) ? 'Şifre en az 6 karakter olmalı.' : null,
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
                'Şifre (tekrar)',
                suffixIcon: _obscureToggle(_obscurePass2,
                    () => setState(() => _obscurePass2 = !_obscurePass2)),
              ),
              validator: (v) =>
                  v != _passCtrl.text ? 'Şifreler eşleşmiyor.' : null,
            ),
          ],
          const SizedBox(height: 18),
          GoldButton(
            text: isRegister ? 'ÜYE OL' : 'GİRİŞ YAP',
            busy: _emailBusy,
            onPressed: _submitEmail,
          ),
          if (!isRegister) ...[
            const SizedBox(height: 10),
            Center(
              child: TextButton(
                onPressed: _resetPassword,
                child: Text('Şifremi unuttum',
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
    return CosmicScaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 24),
          children: [
            const SizedBox(height: 12),
            const Center(child: AstrolabeSpinner(size: 96)),
            const SizedBox(height: 28),
            Center(
              child: Text('RYTHO',
                  style: RythoText.label(22, color: RythoColors.gold)),
            ),
            const SizedBox(height: 10),
            Center(
              child: Text('Gök Atlası',
                  style: RythoText.display(38, w: FontWeight.w600)),
            ),
            const SizedBox(height: 12),
            Text(
              'Kadim bilgelik, hassas gökyüzü hesabıyla buluşur.\n'
              'Haritan çizilir, yüzün okunur, yolun aydınlanır.',
              textAlign: TextAlign.center,
              style: RythoText.body(15, color: RythoColors.parchmentDim),
            ),
            const SizedBox(height: 28),
            // Türkçe 'İ' için metinler önceden büyük harfle veriliyor
            // (toUpperCase 'i'yi 'I' yapar).
            GoldButton(
              text: 'GOOGLE İLE GİRİŞ',
              busy: _googleBusy,
              onPressed: _signInWithGoogle,
            ),
            // Ayraç: — ya da —
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 16),
              child: Row(children: [
                const Expanded(child: Divider()),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  child: Text('YA DA',
                      style:
                          RythoText.mono(10, color: RythoColors.parchmentDim)),
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
                    labels: const ['GİRİŞ YAP', 'ÜYE OL'],
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
            ),
            const SizedBox(height: 20),
            Text(
              'Devam ederek gizlilik ilkelerini kabul etmiş olursun.\n'
              'Yorumlar içgörü amaçlıdır; tıbbi/finansal tavsiye değildir.',
              textAlign: TextAlign.center,
              style: RythoText.body(11, color: RythoColors.parchmentDim),
            ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }
}
