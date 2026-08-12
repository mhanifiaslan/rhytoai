import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/core/contact_match.dart';

// I-turu: cihaz rehberini aktif/pasif ayıran saf fonksiyonun testi.
void main() {
  ContactMatch match(String uid, String hash, {String? username}) =>
      ContactMatch(uid: uid, hash: hash, username: username);

  DeviceContact dev(String name, List<String> hashes) =>
      DeviceContact(name: name, hashes: hashes.toSet());

  test('eşleşen kişiler aktif, kalanlar pasif olur', () {
    final dev1 = [
      dev('Zeynep', ['h-zeynep']),
      dev('Ali', ['h-ali']), // eşleşme yok → pasif
      dev('Mehmet', ['h-mehmet']),
    ];
    final matches = [
      match('u-zeynep', 'h-zeynep', username: 'zeynep'),
      match('u-mehmet', 'h-mehmet', username: 'mehmet'),
    ];

    final r = splitContacts(dev1, matches);

    // Aktif: Mehmet, Zeynep (alfabetik).
    expect(r.active.map((a) => a.name), ['Mehmet', 'Zeynep']);
    expect(r.active.first.match.username, 'mehmet');
    // Pasif: Ali.
    expect(r.passive.map((p) => p.name), ['Ali']);
  });

  test('Türkçe alfabetik sıralama (İ/ı/ş duyarlı)', () {
    final dev1 = [
      dev('Şükrü', ['h1']),
      dev('Irmak', ['h2']),
      dev('İlayda', ['h3']),
    ];
    final r = splitContacts(dev1, const []);
    // foldTurkish: I/İ/ı→i, ş→s. Katlanmış: "ilayda" < "irmak" < "sukru".
    expect(r.passive.map((p) => p.name), ['İlayda', 'Irmak', 'Şükrü']);
  });

  test('aynı app-kullanıcısı birden çok kayıtta bir kez aktif olur', () {
    final dev1 = [
      dev('İş Telefonu', ['h-ali']),
      dev('Ali Cep', ['h-ali']),
    ];
    final matches = [match('u-ali', 'h-ali', username: 'ali')];
    final r = splitContacts(dev1, matches);
    expect(r.active.length, 1);
    expect(r.passive, isEmpty);
  });

  test('bir kişinin bir numarası eşleşirse aktiftir', () {
    final dev1 = [
      dev('Deniz', ['h-ev', 'h-cep']),
    ];
    final matches = [match('u-deniz', 'h-cep')];
    final r = splitContacts(dev1, matches);
    expect(r.active.length, 1);
    expect(r.active.first.name, 'Deniz');
  });
}
