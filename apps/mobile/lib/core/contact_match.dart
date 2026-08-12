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
import 'city_directory.dart' show foldTurkish;

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

/// Eşleşen kullanıcı kartı (sunucudan; publicProfiles alanları + eşleşme
/// hash'i). `hash` istemcinin gönderdiği değerdir; cihaz kişisiyle bu
/// app-kullanıcısını eşlemek için geri döner (I-turu).
class ContactMatch {
  const ContactMatch({
    required this.uid,
    this.hash,
    this.displayName,
    this.username,
    this.sunSign,
    this.photoUrl,
  });

  final String uid;
  final String? hash;
  final String? displayName;
  final String? username;
  final String? sunSign;
  final String? photoUrl;

  factory ContactMatch.fromJson(Map<String, dynamic> json) => ContactMatch(
        uid: json['uid'] as String,
        hash: json['hash'] as String?,
        displayName: json['displayName'] as String?,
        username: json['username'] as String?,
        sunSign: json['sunSign'] as String?,
        photoUrl: json['photoUrl'] as String?,
      );
}

/// Cihaz rehberindeki bir kişi — CİHAZDA kalır, sunucuya GİTMEZ.
/// [hashes] kişinin numaralarının SHA-256'ları (eşleşme korelasyonu için).
class DeviceContact {
  const DeviceContact({required this.name, required this.hashes, this.e164});

  final String name;
  final Set<String> hashes;

  /// Davet paylaşımı için birincil numara (pasif kişide gösterilmez,
  /// yalnız paylaş metnine değil; şimdilik kullanılmıyor ama elde tutulur).
  final String? e164;
}

/// Uygulamayı kullanan rehber kişisi (aktif): cihaz adı + app kartı.
class ActiveContact {
  const ActiveContact({required this.name, required this.match});
  final String name; // rehberdeki ad (app displayName'inden farklı olabilir)
  final ContactMatch match;
}

/// Uygulamayı kullanmayan rehber kişisi (pasif): yalnız ad — davet edilir.
class PassiveContact {
  const PassiveContact({required this.name});
  final String name;
}

/// Cihaz kişilerini, sunucu eşleşmeleriyle aktif/pasif olarak ayırır.
///
/// SAF fonksiyon (test edilebilir): app'te olan kişiler [active]'e (app
/// kartıyla), kalanlar [passive]'e düşer. İkisi de ada göre alfabetik
/// (Türkçe-duyarlı) sıralanır. Bir kişinin herhangi bir numarası eşleşirse
/// aktiftir. app'te olup contactMatch KAPALI kişi eşleşme dönmez → pasifte
/// görünür (mahremiyet doğru; onu ifşa edemeyiz).
({List<ActiveContact> active, List<PassiveContact> passive}) splitContacts(
    List<DeviceContact> devContacts, List<ContactMatch> matches) {
  final hashToMatch = <String, ContactMatch>{};
  for (final m in matches) {
    if (m.hash != null) hashToMatch[m.hash!] = m;
  }

  final active = <ActiveContact>[];
  final passive = <PassiveContact>[];
  final gorulenUid = <String>{};
  for (final k in devContacts) {
    ContactMatch? eslesme;
    for (final h in k.hashes) {
      final m = hashToMatch[h];
      if (m != null) {
        eslesme = m;
        break;
      }
    }
    if (eslesme != null) {
      // Aynı app-kullanıcısı birden çok rehber kaydında olabilir; bir kez.
      if (gorulenUid.add(eslesme.uid)) {
        active.add(ActiveContact(name: k.name, match: eslesme));
      }
    } else {
      passive.add(PassiveContact(name: k.name));
    }
  }

  int cmp(String a, String b) =>
      foldTurkish(a).compareTo(foldTurkish(b));
  active.sort((a, b) => cmp(a.name, b.name));
  passive.sort((a, b) => cmp(a.name, b.name));
  return (active: active, passive: passive);
}

/// Eşleşmenin neden BOŞ olduğunu ayırt eden durum (F1).
///
/// Eski tasarım her eksikte sessizce boş liste döndürüyordu; iç testte
/// kullanıcı "rehberimdekiler görünmüyor" dedi ve neyin eksik olduğunu
/// öğrenmenin hiçbir yolu yoktu. Ekran artık nedene göre yol gösteriyor.
enum ContactMatchBlocker {
  /// Kullanıcının kendi telefonu doğrulanmamış — karşı taraf onu hangi
  /// numarayla bulacak?
  telefonYok,

  /// Rehber okuma izni reddedilmiş.
  izinYok,
}

class ContactMatchResult {
  const ContactMatchResult({
    this.blocker,
    this.active = const [],
    this.passive = const [],
  });

  final ContactMatchBlocker? blocker;

  /// Uygulamayı kullanan rehber kişileri (alfabetik).
  final List<ActiveContact> active;

  /// Uygulamayı kullanmayan rehber kişileri (alfabetik) — davet edilir.
  final List<PassiveContact> passive;
}

/// Rehber eşleşmesini uçtan uca koşturur: cihaz kişilerini okur, hash'ler,
/// sunucuyla eşleştirir, aktif/pasif olarak ayırır. Rehber ADLARI CİHAZDA
/// kalır; ağa yalnız hash gider.
Future<ContactMatchResult> runContactMatch(Ref ref) async {
  final kendiNumaram = FirebaseAuth.instance.currentUser?.phoneNumber;
  if (kendiNumaram == null) {
    return const ContactMatchResult(
        blocker: ContactMatchBlocker.telefonYok);
  }

  if (!await FlutterContacts.requestPermission(readonly: true)) {
    return const ContactMatchResult(blocker: ContactMatchBlocker.izinYok);
  }

  // withProperties: telefon alanları gelsin; foto/organizasyon GELMESİN.
  final kisiler = await FlutterContacts.getContacts(withProperties: true);

  final kod = countryCodeOf(kendiNumaram);
  final devContacts = <DeviceContact>[];
  final tumHashler = <String>{};
  for (final kisi in kisiler) {
    final ad = kisi.displayName.trim();
    if (ad.isEmpty) continue; // adsız kayıt (yalnız numara) listelenmez
    final hashler = <String>{};
    String? birincilE164;
    for (final tel in kisi.phones) {
      final e164 = normalizeE164(tel.number, countryCode: kod);
      if (e164 == null || e164 == kendiNumaram) continue;
      hashler.add(_hash(e164));
      birincilE164 ??= e164;
    }
    if (hashler.isEmpty) continue; // geçerli numarası olmayan kişi atlanır
    devContacts.add(
        DeviceContact(name: ad, hashes: hashler, e164: birincilE164));
    tumHashler.addAll(hashler);
  }
  if (tumHashler.isEmpty) return const ContactMatchResult();

  final dio = ref.read(apiProvider);
  final yanit = await dio.post('/api/v1/contacts/match',
      data: {'hashes': tumHashler.take(2000).toList()});
  final ham = (yanit.data as Map)['matches'] as List? ?? const [];
  final matches = [
    for (final m in ham)
      ContactMatch.fromJson(Map<String, dynamic>.from(m as Map)),
  ];

  final bolunmus = splitContacts(devContacts, matches);
  return ContactMatchResult(
      active: bolunmus.active, passive: bolunmus.passive);
}

/// Eşleşme sonuçları — ayar açıkken çağrılır, bellekte yaşar (sunucu gibi
/// istemci de listeyi KALICI saklamaz).
final contactMatchesProvider =
    FutureProvider.autoDispose<ContactMatchResult>((ref) async {
  try {
    return await runContactMatch(ref);
  } catch (e) {
    // Ağ/sunucu hatası kullanıcıyı yanıltmasın: boş-ama-nedensiz sonuç,
    // ekranda "rehberinden kimse görünmüyor" bilgi metnine düşer.
    debugPrint('Rehber eşleşmesi başarısız: $e');
    return const ContactMatchResult();
  }
});
