import 'dart:convert';
import 'dart:math';

import 'package:crypto/crypto.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';

import 'device_claim.dart' show resetDeviceTakeoverPrompt;

/// Kimlik doğrulama işlemleri.
///
/// Ekrandan ayrı tutuluyor: giriş akışının kuralları (Apple zorunluluğu,
/// e-posta doğrulaması, sağlayıcı çakışması) arayüz düzeninden bağımsız ve
/// test edilebilir olmalı.

/// Apple ile Giriş bu platformda sunulmalı mı?
///
/// **App Store Guideline 4.8:** üçüncü taraf bir giriş yöntemi (Google)
/// sunuyorsan, iOS'ta Apple ile Giriş'i de sunmak ZORUNLUDUR. Tek başına red
/// sebebidir. Android'de gerekli değil ve göstermek kafa karıştırır.
bool get appleSignInAvailable =>
    !kIsWeb && defaultTargetPlatform == TargetPlatform.iOS;

/// Kayıt için kabul edilebilir şifre mi?
///
/// Firebase'in mutlak alt sınırı 6 karakter; onu tek kural saymak "123456"yı
/// geçerli yapıyordu. Kural bilinçli olarak **uzunluk + çeşitlilik**:
/// 8 karakter ve en az iki farklı karakter sınıfı. Karmaşık bir kalıp
/// dayatmak (büyük harf + rakam + sembol) kullanıcıyı şifresini bir yere
/// yazmaya iter; uzunluk daha çok fayda sağlar.
PasswordIssue? validatePassword(String password) {
  if (password.length < 8) return PasswordIssue.tooShort;

  var siniflar = 0;
  if (RegExp(r'[a-zçğıöşü]').hasMatch(password.toLowerCase()) &&
      RegExp(r'[A-Za-zÇĞİÖŞÜçğıöşü]').hasMatch(password)) {
    siniflar++;
  }
  if (RegExp(r'[0-9]').hasMatch(password)) siniflar++;
  if (RegExp(r'[^A-Za-z0-9ÇĞİÖŞÜçğıöşü]').hasMatch(password)) siniflar++;

  if (siniflar < 2) return PasswordIssue.tooSimple;
  return null;
}

enum PasswordIssue { tooShort, tooSimple }

/// Google ile giriş.
Future<void> signInWithGoogle() async {
  if (kIsWeb) {
    await FirebaseAuth.instance.signInWithPopup(GoogleAuthProvider());
    return;
  }
  final account = await GoogleSignIn.instance.authenticate();
  final auth = account.authentication;
  await FirebaseAuth.instance.signInWithCredential(
    GoogleAuthProvider.credential(idToken: auth.idToken),
  );
}

/// Apple ile giriş.
///
/// Nonce zorunlu: Apple'ın döndürdüğü kimlik belirtecinin **bu isteğe ait
/// olduğunu** doğrular. Nonce'un ham hâli Firebase'e, SHA-256 özeti Apple'a
/// gider; Apple özeti belirtecin içine gömer ve Firebase ikisini karşılaştırır.
/// Olmadan yeniden oynatma (replay) saldırısı mümkün olur.
Future<void> signInWithApple() async {
  final rawNonce = _randomNonce();
  final credential = await SignInWithApple.getAppleIDCredential(
    scopes: [
      AppleIDAuthorizationScopes.email,
      AppleIDAuthorizationScopes.fullName,
    ],
    nonce: sha256.convert(utf8.encode(rawNonce)).toString(),
  );

  final userCredential = await FirebaseAuth.instance.signInWithCredential(
    OAuthProvider('apple.com').credential(
      idToken: credential.identityToken,
      rawNonce: rawNonce,
    ),
  );

  // Apple adı YALNIZCA ilk girişte döndürür; kaçırılırsa bir daha alınamaz.
  final ad = [credential.givenName, credential.familyName]
      .whereType<String>()
      .where((p) => p.trim().isNotEmpty)
      .join(' ')
      .trim();
  if (ad.isNotEmpty && (userCredential.user?.displayName ?? '').isEmpty) {
    await userCredential.user?.updateDisplayName(ad);
  }
}

String _randomNonce([int uzunluk = 32]) {
  const harfler =
      '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-._';
  final rastgele = Random.secure();
  return List.generate(
      uzunluk, (_) => harfler[rastgele.nextInt(harfler.length)]).join();
}

/// E-posta ile giriş.
Future<void> signInWithEmail(String email, String password) =>
    FirebaseAuth.instance
        .signInWithEmailAndPassword(email: email, password: password);

/// E-posta ile kayıt.
///
/// Kayıttan hemen sonra **doğrulama e-postası** gönderilir. Gönderilmezse
/// kimse sahibi olmadığı bir adresle hesap açabilir — ve o adresin gerçek
/// sahibi sonradan kaydolmak isteyince "e-posta kullanımda" duvarına çarpar.
Future<void> registerWithEmail({
  required String email,
  required String password,
  required String displayName,
}) async {
  final credential = await FirebaseAuth.instance
      .createUserWithEmailAndPassword(email: email, password: password);
  await credential.user?.updateDisplayName(displayName);
  try {
    await credential.user?.sendEmailVerification();
  } catch (e) {
    // Doğrulama e-postası gönderilemezse kayıt yine de geçerli; kullanıcıyı
    // burada durdurmak, hesabı olan birini dışarıda bırakmak olurdu.
    debugPrint('Doğrulama e-postası gönderilemedi: $e');
  }
}

/// Şifre sıfırlama.
///
/// **Sonuç ne olursa olsun sessizce döner.** Hatayı kullanıcıya göstermek
/// "bu e-posta kayıtlı mı" bilgisini sızdırırdı (kullanıcı sayımı); arayüz
/// her durumda aynı nötr mesajı gösterir.
Future<void> sendPasswordReset(String email) async {
  try {
    await FirebaseAuth.instance.sendPasswordResetEmail(email: email);
  } catch (e) {
    debugPrint('Şifre sıfırlama gönderilemedi: $e');
  }
}

// Sağlayıcı çakışması hakkında bir not:
//
// Google ile açılmış bir hesaba şifreyle girilmeye çalışıldığında Firebase
// yalnızca "geçersiz kimlik" diyor ve kullanıcı çıkmaza giriyor. Önce
// `fetchSignInMethodsForEmail` ile hangi sağlayıcının kullanıldığını sormayı
// denedim — o API **kaldırıldı**, çünkü tam da kaçınmaya çalıştığımız şeyi
// yapıyordu: bir e-postanın kayıtlı olup olmadığını dışarıya sızdırıyordu
// (kullanıcı sayımı). Firebase artık bunu "email enumeration protection" ile
// varsayılan olarak kapatıyor.
//
// Bu yüzden çözüm istemcide sorgu değil, DOĞRU YAZILMIŞ HATA MESAJI: giriş
// başarısız olduğunda kullanıcıya her iki olasılık birden söyleniyor
// (şifre yanlış olabilir ya da hesap sosyal giriş ile açılmış olabilir).
// Bilgi sızdırmadan çıkmazı çözer.

/// Hesaba e-posta/şifre girişi bağlar (F4).
///
/// Google/Apple ile açılmış hesapta `password` sağlayıcısı yoktur;
/// `updatePassword` çağrısı orada anlamsızdır — doğru araç
/// `linkWithCredential`: aynı hesaba ikinci bir giriş yolu ekler.
/// Şifre zaten bağlıysa `updatePassword` ile değiştirilir.
///
/// E-posta parametre olarak alınır ve `user.email` varsayılmaz: Apple
/// "Hide My Email" kullanıcısında adres privaterelay olabilir ya da hiç
/// gelmeyebilir; kullanıcı giriş için KULLANACAĞI adresi kendi yazar.
Future<void> linkPassword(String email, String password) async {
  final user = FirebaseAuth.instance.currentUser;
  if (user == null) throw StateError('Oturum yok');

  final sifreBagli =
      user.providerData.any((p) => p.providerId == 'password');
  if (sifreBagli) {
    await user.updatePassword(password);
    return;
  }
  await user.linkWithCredential(
      EmailAuthProvider.credential(email: email.trim(), password: password));
  // Sağlayıcı listesi token'da taşınır; tazelenmezse arayüz eski kalır.
  await user.getIdToken(true);
}

/// Hesaba Google girişini bağlar (F4) — e-posta/şifre kullanıcısı için.
Future<void> linkGoogle() async {
  final user = FirebaseAuth.instance.currentUser;
  if (user == null) throw StateError('Oturum yok');

  final account = await GoogleSignIn.instance.authenticate();
  final auth = account.authentication;
  await user.linkWithCredential(
      GoogleAuthProvider.credential(idToken: auth.idToken));
  await user.getIdToken(true);
}

Future<void> signOutEverywhere() async {
  // Cihaz devralma sorusu yeni oturumda yeniden sorulabilsin (V1).
  resetDeviceTakeoverPrompt();
  try {
    await GoogleSignIn.instance.signOut();
  } catch (_) {}
  await FirebaseAuth.instance.signOut();
}
