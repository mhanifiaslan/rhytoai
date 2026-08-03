/// Rehber eşleşmesi — istemci yarısı (Revize R3).
///
/// ## Gizlilik sözleşmesi (sunucudaki `api/contacts.py` ile aynı)
///
/// * Rehber numaraları CİHAZDA E.164'e çevrilir ve SHA-256'lanır; ağdan
///   yalnızca hash listesi geçer. Ad, soyad, e-posta — rehberin başka
///   HİÇBİR alanı okunup gönderilmez.
/// * Ayar varsayılan KAPALI; sunucu karşılıklılık arar (iki taraf da açık
///   olmadan kimse kimseyi görmez).
///
/// ## Normalizasyon neden burada ve neden bu kadar önemli
///
/// Rehberdeki "0555 111 22 33" ile Firebase'in doğruladığı "+905551112233"
/// AYNI numara ama bayt olarak farklı — hash'leri de farklı olur ve eşleşme
/// SESSİZCE boş döner. Sunucu tarafı hash'i Firebase'in E.164'ünden
/// hesaplıyor; buradaki normalizasyon da aynı biçime çıkmak zorunda.
/// Ülke kodu varsayımı kullanıcının KENDİ doğrulanmış numarasından alınır.
library;

import 'dart:convert';

import 'package:crypto/crypto.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_contacts/flutter_contacts.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'api.dart';

/// Yerel biçimli numarayı E.164'e çevirir; çeviremezse `null`.
///
/// [countryCode] "+90" gibi — kullanıcının kendi doğrulanmış numarasından
/// türetilir. Kurallar:
/// * `+...`  → olduğu gibi (boşluk/ayraç temizlenir)
/// * `00...` → `+...`
/// * `0...`  → ülke kodu + baştaki sıfır atılır ("05xx" → "+905xx")
/// * düz 7-12 hane → ülke kodu öne eklenir
/// * 7 haneden kısa ya da harf içeren girdiler atılır (dahili no, *kodlar*)
@visibleForTesting
String? normalizeE164(String raw, {required String countryCode}) {
  var s = raw.replaceAll(RegExp(r'[\s\-().]'), '');
  if (s.isEmpty) return null;
  if (s.contains(RegExp(r'[^0-9+]'))) return null;

  if (s.startsWith('00')) s = '+${s.substring(2)}';
  if (s.startsWith('+')) {
    final hane = s.substring(1);
    if (hane.length < 8 || hane.length > 15) return null;
    return s;
  }
  if (s.startsWith('0')) s = s.substring(1);
  if (s.length < 7 || s.length > 12) return null;
  return '$countryCode$s';
}

/// Kullanıcının kendi E.164 numarasından ülke kodunu çıkarır ("+90").
///
/// Kaba ama yeterli: 1-3 haneli kodların tam ayrımı NANP/ITU tablosu
/// ister; rehberdeki numaraların ezici çoğunluğu kullanıcının kendi
/// ülkesinden olduğu için kendi numarasının ilk 3 hanesini denemek pratikte
/// doğru sonucu verir (TR için "+90" kesin çıkar).
@visibleForTesting
String countryCodeOf(String e164) {
  // Tek haneli bilinen kodlar: +1 (NANP), +7.
  if (e164.startsWith('+1') || e164.startsWith('+7')) {
    return e164.substring(0, 2);
  }
  // Kalanların büyük kısmı 2 haneli (+90, +44, +49...). 3 haneli kodlarda
  // (örn. +995) 2 hane varsayımı yanlış olur ama kendi ülkesi içi numaralar
  // yine tutar: yanlış kod yalnızca kod YAZILMAMIŞ girdilere eklenir.
  return e164.length >= 3 ? e164.substring(0, 3) : e164;
}

String _hash(String e164) =>
    sha256.convert(utf8.encode(e164.trim())).toString();

/// Eşleşen kullanıcı kartı (sunucudan; publicProfiles alanları).
class ContactMatch {
  const ContactMatch({
    required this.uid,
    this.displayName,
    this.username,
    this.sunSign,
    this.photoUrl,
  });

  final String uid;
  final String? displayName;
  final String? username;
  final String? sunSign;
  final String? photoUrl;

  factory ContactMatch.fromJson(Map<String, dynamic> json) => ContactMatch(
        uid: json['uid'] as String,
        displayName: json['displayName'] as String?,
        username: json['username'] as String?,
        sunSign: json['sunSign'] as String?,
        photoUrl: json['photoUrl'] as String?,
      );
}

/// Rehber eşleşmesini uçtan uca koşturur.
///
/// İzin reddedilirse boş liste döner (çağıran ayarı açık bırakabilir;
/// kullanıcı sistem ayarından izni sonra verebilir).
Future<List<ContactMatch>> runContactMatch(Ref ref) async {
  final kendiNumaram = FirebaseAuth.instance.currentUser?.phoneNumber;
  if (kendiNumaram == null) {
    // Telefon doğrulanmadan eşleşme anlamsız: karşı taraf bizi hangi
    // numarayla bulacak? Çağıran ekran bunu ayrı bir durumla gösterir.
    return const [];
  }

  if (!await FlutterContacts.requestPermission(readonly: true)) {
    return const [];
  }

  // withProperties: telefon alanları gelsin; foto/organizasyon GELMESİN.
  final kisiler = await FlutterContacts.getContacts(withProperties: true);

  final kod = countryCodeOf(kendiNumaram);
  final hashler = <String>{};
  for (final kisi in kisiler) {
    for (final tel in kisi.phones) {
      final e164 = normalizeE164(tel.number, countryCode: kod);
      if (e164 != null && e164 != kendiNumaram) hashler.add(_hash(e164));
    }
  }
  if (hashler.isEmpty) return const [];

  final dio = ref.read(apiProvider);
  final yanit = await dio.post('/api/v1/contacts/match',
      data: {'hashes': hashler.take(2000).toList()});
  final ham = (yanit.data as Map)['matches'] as List? ?? const [];
  return [
    for (final m in ham)
      ContactMatch.fromJson(Map<String, dynamic>.from(m as Map)),
  ];
}

/// Eşleşme sonuçları — ayar açıkken çağrılır, bellekte yaşar (sunucu gibi
/// istemci de listeyi KALICI saklamaz).
final contactMatchesProvider =
    FutureProvider.autoDispose<List<ContactMatch>>((ref) async {
  try {
    return await runContactMatch(ref);
  } catch (e) {
    debugPrint('Rehber eşleşmesi başarısız: $e');
    return const [];
  }
});
