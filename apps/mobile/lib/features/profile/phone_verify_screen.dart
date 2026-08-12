/// Telefon doğrulama — hesaba numara BAĞLAMA (ayrı giriş yöntemi değil).
///
/// ## Akış
///
/// 1. Kullanıcı numarasını girer → Firebase SMS gönderir
///    (`verifyPhoneNumber`; Android'de bazen SMS'siz otomatik doğrular).
/// 2. Kod girilir → `linkWithCredential` mevcut hesaba numarayı bağlar.
/// 3. Token TAZELENİR (`getIdToken(true)`) — `phone_number` claim'i ancak
///    yeni token'da görünür — ve sunucuya "bağladım, kaydet" denir
///    (`POST /account/phone/sync`, gövdesiz: sunucu numarayı TOKEN'dan okur,
///    istemci beyanına güvenmez).
///
/// Sunucu tarafında hash dizini rehber eşleşmesinin (R3) temelini kurar;
/// ham numara Firestore'a hiç yazılmaz.
library;

import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_crashlytics/firebase_crashlytics.dart';
import 'package:flutter/foundation.dart' show kDebugMode;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api.dart';
import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import '../../theme/rytho_tokens.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/phone_number_field.dart';

class PhoneVerifyScreen extends ConsumerStatefulWidget {
  const PhoneVerifyScreen({super.key});

  @override
  ConsumerState<PhoneVerifyScreen> createState() => _PhoneVerifyScreenState();
}

class _PhoneVerifyScreenState extends ConsumerState<PhoneVerifyScreen> {
  /// E.164 derlenmiş numara — PhoneNumberField'dan gelir (O4): ülke
  /// aramalı listeden, boşluk/sıfır temizliği bileşende.
  String _numara = '';
  final _kod = TextEditingController();
  String? _verificationId;
  bool _mesgul = false;
  String? _hata;

  @override
  void dispose() {
    _kod.dispose();
    super.dispose();
  }

  Future<void> _kodGonder() async {
    final l10n = AppLocalizations.of(context);
    final numara = _numara;
    if (!numara.startsWith('+') || numara.length < 10) {
      setState(() => _hata = l10n.phoneInvalid);
      return;
    }
    setState(() {
      _mesgul = true;
      _hata = null;
    });
    await FirebaseAuth.instance.verifyPhoneNumber(
      phoneNumber: numara,
      // Android otomatik doğrulaması: SMS beklemeden kimlik gelebilir.
      verificationCompleted: (credential) => _bagla(credential),
      verificationFailed: (e) {
        if (!mounted) return;
        setState(() {
          _mesgul = false;
          _hata = _firebaseHatasi(e, l10n);
        });
      },
      codeSent: (verificationId, _) {
        if (!mounted) return;
        setState(() {
          _mesgul = false;
          _verificationId = verificationId;
        });
      },
      codeAutoRetrievalTimeout: (verificationId) {
        _verificationId ??= verificationId;
      },
    );
  }

  Future<void> _kodOnayla() async {
    final id = _verificationId;
    if (id == null) return;
    await _bagla(PhoneAuthProvider.credential(
      verificationId: id,
      smsCode: _kod.text.trim(),
    ));
  }

  Future<void> _bagla(PhoneAuthCredential credential) async {
    final l10n = AppLocalizations.of(context);
    final gezgin = Navigator.of(context);
    final mesajci = ScaffoldMessenger.of(context);
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) return;

    setState(() {
      _mesgul = true;
      _hata = null;
    });
    try {
      if (user.phoneNumber == null) {
        await user.linkWithCredential(credential);
      } else {
        // Numara değişikliği: bağlama değil güncelleme.
        await user.updatePhoneNumber(credential);
      }

      // Claim ancak TAZE token'da görünür; tazelenmeden sync 400 döner.
      await user.getIdToken(true);
      await ref.read(apiProvider).post('/api/v1/account/phone/sync');

      if (!mounted) return;
      mesajci.showSnackBar(SnackBar(content: Text(l10n.phoneLinkedDone)));
      gezgin.pop();
    } on FirebaseAuthException catch (e) {
      if (!mounted) return;
      setState(() {
        _mesgul = false;
        _hata = _firebaseHatasi(e, l10n);
      });
    } catch (e) {
      // Sunucu 409'u (numara başka hesapta) dahil: detail kullanıcının
      // dilinde geliyor.
      if (!mounted) return;
      setState(() {
        _mesgul = false;
        _hata = friendlyError(e, l10n);
      });
    }
  }

  String _firebaseHatasi(FirebaseAuthException e, AppLocalizations l10n) {
    switch (e.code) {
      case 'credential-already-in-use':
      case 'account-exists-with-different-credential':
        return l10n.phoneTakenError;
      case 'invalid-verification-code':
      case 'invalid-verification-id':
        return l10n.phoneCodeWrong;
      case 'invalid-phone-number':
        return l10n.phoneInvalid;
      case 'too-many-requests':
      case 'quota-exceeded':
        return l10n.phoneTooManyTries;
      // Aşağıdaki üçü KURULUM sorunlarıdır ve eskiden jenerik "bir şeyler
      // ters gitti"ye düşüyordu — kullanıcı "kod gelmiyor" diyor, neden
      // hiç görünmüyordu. Artık ayrışıyor: sağlayıcı kapalı / uygulama
      // doğrulaması (SHA-256, Play Integrity) eksik.
      case 'operation-not-allowed':
        return l10n.phoneSmsDisabled;
      case 'app-not-authorized':
      case 'missing-client-identifier':
        return l10n.phoneAppNotVerified;
      // 17499/39 (cihazda görüldü, 2026-08-07): Firebase'in kötüye
      // kullanım koruması — aynı numara/cihazla kısa sürede çok deneme.
      // Birkaç saatte kendiliğinden açılır; kullanıcıya bunu söylemek
      // "bir şeyler ters gitti"den çok daha az korkutucu.
      case 'internal-error':
        return l10n.phoneTemporarilyBlocked;
      default:
        // Aynı 17499/39 hatası her cihazda 'internal-error' koduyla
        // gelmiyor (2026-08-12'de 'unknown' kodla, mesajın içinde
        // "Error code:39" olarak görüldü) — koddan önce mesaja da bak.
        final mesaj = e.message ?? '';
        if (mesaj.contains('17499') || mesaj.contains('Error code:39')) {
          return l10n.phoneTemporarilyBlocked;
        }
        // Nedeni bilmiyorsak en azından BİZ öğrenelim: kod+mesaj
        // Crashlytics'e gider (eskiden hiçbir yere gitmiyordu).
        if (!kDebugMode) {
          FirebaseCrashlytics.instance.recordError(
              'phone-verify: ${e.code}: ${e.message}', StackTrace.current,
              fatal: false);
        }
        return l10n.genericError;
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final kodAsamasi = _verificationId != null;

    return CosmicScaffold(
      appBar: AppBar(title: Text(l10n.phoneVerifyTitle)),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(RythoSpace.xl, RythoSpace.md,
              RythoSpace.xl, RythoSpace.xxl),
          children: [
            Text(l10n.phoneVerifyBody, style: RythoType.bodyDim),
            const SizedBox(height: RythoSpace.xl),
            if (!kodAsamasi) ...[
              PhoneNumberField(
                onChanged: (e164) => setState(() {
                  _numara = e164;
                  _hata = null;
                }),
              ),
            ] else ...[
              Text(l10n.phoneCodeSentTo(_numara), style: RythoType.body),
              const SizedBox(height: RythoSpace.md),
              TextField(
                controller: _kod,
                style: RythoType.body,
                keyboardType: TextInputType.number,
                autofillHints: const [AutofillHints.oneTimeCode],
                decoration: InputDecoration(labelText: l10n.phoneCodeLabel),
                onChanged: (_) => setState(() => _hata = null),
              ),
              const SizedBox(height: RythoSpace.sm),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton(
                  onPressed: _mesgul
                      ? null
                      : () => setState(() {
                            _verificationId = null;
                            _kod.clear();
                          }),
                  child: Text(l10n.phoneChangeNumber,
                      style: RythoType.caption),
                ),
              ),
            ],
            if (_hata != null) ...[
              const SizedBox(height: RythoSpace.md),
              Text(_hata!,
                  style: RythoText.body(13, color: RythoColors.madder)),
            ],
            const SizedBox(height: RythoSpace.xxl),
            GoldButton(
              text: kodAsamasi ? l10n.phoneConfirmCode : l10n.phoneSendCode,
              busy: _mesgul,
              onPressed: _mesgul
                  ? null
                  : (kodAsamasi ? _kodOnayla : _kodGonder),
            ),
          ],
        ),
      ),
    );
  }
}
