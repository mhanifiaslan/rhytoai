import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

/// PBZ 1.5 bütçe kapısı: kehanet sahnesi varlıkları kayıtlı, yerinde ve
/// bütçede. Klip başına ≤1 MB, toplam ≤5 MB; aşarsa 640×400 / q75'e inilir
/// (`ads/oracle-anim/README.md`). `flutter test` paket kökünden koşar
/// (apps/mobile) — yollar buna göre.
const _klipler = [
  'assets/anim/coins_air.webp',
  'assets/anim/coins_land_0.webp',
  'assets/anim/coins_land_1.webp',
  'assets/anim/coins_land_2.webp',
  'assets/anim/coins_land_3.webp',
  'assets/anim/bazi_wait.webp',
];
const _ses = 'assets/sounds/coin_land.wav';
const _klipUstSinir = 1024 * 1024; // 1 MB
const _toplamUstSinir = 5 * 1024 * 1024; // 5 MB

void main() {
  test('pubspec assets/anim/ ve assets/sounds/ kayıtlı', () {
    final pubspec = File('pubspec.yaml').readAsStringSync();
    expect(pubspec, contains('- assets/anim/'));
    expect(pubspec, contains('- assets/sounds/'));
  });

  test('6 webp + coin_land.wav var; her biri WebP/WAV imzalı', () {
    for (final yol in _klipler) {
      final dosya = File(yol);
      expect(dosya.existsSync(), isTrue, reason: '$yol yok');
      final bas = dosya.openSync().readSync(12);
      // RIFF....WEBP
      expect(String.fromCharCodes(bas.sublist(0, 4)), 'RIFF',
          reason: '$yol RIFF değil');
      expect(String.fromCharCodes(bas.sublist(8, 12)), 'WEBP',
          reason: '$yol WebP değil');
    }
    final ses = File(_ses);
    expect(ses.existsSync(), isTrue, reason: '$_ses yok');
    final bas = ses.openSync().readSync(12);
    expect(String.fromCharCodes(bas.sublist(0, 4)), 'RIFF');
    expect(String.fromCharCodes(bas.sublist(8, 12)), 'WAVE');
  });

  test('bütçe: klip ≤1 MB, toplam ≤5 MB; clink ≤400 ms', () {
    var toplam = 0;
    for (final yol in _klipler) {
      final boyut = File(yol).lengthSync();
      expect(boyut, lessThanOrEqualTo(_klipUstSinir),
          reason: '$yol ${boyut ~/ 1024} KB > 1 MB — 640×400 / q75');
      toplam += boyut;
    }
    final sesBoyut = File(_ses).lengthSync();
    toplam += sesBoyut;
    expect(toplam, lessThanOrEqualTo(_toplamUstSinir),
        reason: 'toplam ${toplam ~/ 1024} KB > 5 MB');
    // Mono 16 bit 44,1 kHz: 400 ms = 35 280 bayt veri (+44 bayt başlık).
    expect(sesBoyut, lessThanOrEqualTo(44 + 400 * 44100 * 2 ~/ 1000),
        reason: 'coin_land.wav 400 ms\'den uzun');
  });
}
