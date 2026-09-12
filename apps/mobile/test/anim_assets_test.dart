import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

/// PBZ 1.5 → PZ2 bütçe kapısı: kehanet sahnesi varlıkları kayıtlı, yerinde
/// ve bütçede. Paralar artık kodla sürülür: beş kare-dizisi klibi (≈3 MB)
/// yerine iki alfa PNG doku (≤150 KB'er). BaZi bekleme döngüsü WebP kalır
/// (≤1 MB). `flutter test` paket kökünden koşar (apps/mobile).
const _dokular = [
  'assets/anim/coin_face.png',
  'assets/anim/coin_back.png',
];
const _klipler = ['assets/anim/bazi_wait.webp'];
const _eskiKlipler = [
  'assets/anim/coins_air.webp',
  'assets/anim/coins_land_0.webp',
  'assets/anim/coins_land_1.webp',
  'assets/anim/coins_land_2.webp',
  'assets/anim/coins_land_3.webp',
];
const _ses = 'assets/sounds/coin_land.wav';
const _dokuUstSinir = 150 * 1024;
const _klipUstSinir = 1024 * 1024; // 1 MB
const _toplamUstSinir = 2 * 1024 * 1024; // 2 MB

void main() {
  test('pubspec assets/anim/ ve assets/sounds/ kayıtlı', () {
    final pubspec = File('pubspec.yaml').readAsStringSync();
    expect(pubspec, contains('- assets/anim/'));
    expect(pubspec, contains('- assets/sounds/'));
  });

  test('dokular PNG, klip WebP, foley WAV imzalı; eski para klipleri YOK',
      () {
    for (final yol in _dokular) {
      final dosya = File(yol);
      expect(dosya.existsSync(), isTrue, reason: '$yol yok');
      final bas = dosya.openSync().readSync(8);
      expect(bas.sublist(1, 4), [0x50, 0x4E, 0x47], reason: '$yol PNG değil');
    }
    for (final yol in _klipler) {
      final dosya = File(yol);
      expect(dosya.existsSync(), isTrue, reason: '$yol yok');
      final bas = dosya.openSync().readSync(12);
      expect(String.fromCharCodes(bas.sublist(0, 4)), 'RIFF');
      expect(String.fromCharCodes(bas.sublist(8, 12)), 'WEBP');
    }
    final ses = File(_ses);
    expect(ses.existsSync(), isTrue, reason: '$_ses yok');
    final bas = ses.openSync().readSync(12);
    expect(String.fromCharCodes(bas.sublist(0, 4)), 'RIFF');
    expect(String.fromCharCodes(bas.sublist(8, 12)), 'WAVE');
    for (final yol in _eskiKlipler) {
      expect(File(yol).existsSync(), isFalse,
          reason: '$yol hâlâ paketleniyor — paralar artık kodla sürülür');
    }
  });

  test('bütçe: doku ≤150 KB, klip ≤1 MB, toplam ≤2 MB; clink ≤400 ms', () {
    var toplam = 0;
    for (final yol in _dokular) {
      final boyut = File(yol).lengthSync();
      expect(boyut, lessThanOrEqualTo(_dokuUstSinir),
          reason: '$yol ${boyut ~/ 1024} KB > 150 KB');
      toplam += boyut;
    }
    for (final yol in _klipler) {
      final boyut = File(yol).lengthSync();
      expect(boyut, lessThanOrEqualTo(_klipUstSinir),
          reason: '$yol ${boyut ~/ 1024} KB > 1 MB');
      toplam += boyut;
    }
    final sesBoyut = File(_ses).lengthSync();
    toplam += sesBoyut;
    expect(toplam, lessThanOrEqualTo(_toplamUstSinir),
        reason: 'toplam ${toplam ~/ 1024} KB > 2 MB');
    // Mono 16 bit 44,1 kHz: 400 ms = 35 280 bayt veri (+44 bayt başlık).
    expect(sesBoyut, lessThanOrEqualTo(44 + 400 * 44100 * 2 ~/ 1000),
        reason: 'coin_land.wav 400 ms\'den uzun');
  });
}
