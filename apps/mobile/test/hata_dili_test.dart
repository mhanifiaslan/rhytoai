// Hata metinlerinin DİLİ (kapalı test cilası).
//
// `friendlyError` l10n'i opsiyonel alıyordu ve 41 çağrı yerinin 8'i onu
// geçmiyordu: günlük defteri (3), arkadaş detayı + tepki (3), ilişki ekranı,
// doğum kaydı. Sunucuya hiç ulaşılamadığında — metro, asansör, zaman aşımı,
// Cloud Run'ın HTML 502'si, `_cerceveMetinleri` elemesi — gövdeye gömülü
// Türkçe sabit dönüyordu: İngilizce arayüzün ortasında kırmızı bir Türkçe
// SnackBar. Gramer/dil tarayıcısı ARB'ye bakıyor, gövdeye gömülü sabiti hiç
// görmüyor; bekçi bu yüzden var.
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/core/api.dart';
import 'package:rytho/l10n/app_localizations_en.dart';
import 'package:rytho/l10n/app_localizations_tr.dart';

DioException _kopuk() => DioException(
      requestOptions: RequestOptions(path: '/api/v1/account/diary'),
      type: DioExceptionType.connectionError,
    );

void main() {
  group('Bağlantı koptuğunda metin ARAYÜZ DİLİNDE', () {
    test('İngilizce arayüzde Türkçe metin ÇIKMAZ', () {
      final en = AppLocalizationsEn();
      expect(friendlyError(_kopuk(), en), en.errorConnection);
      expect(friendlyError(StateError('x'), en), en.errorGeneric);
      // Kusurun kendisi: gövdeye gömülü Türkçe sabitler.
      expect(friendlyError(_kopuk(), en), isNot(contains('Bağlantı')));
      expect(
          friendlyError(StateError('x'), en), isNot(contains('Beklenmeyen')));
    });

    test('Türkçe arayüzde metin Türkçe kalır', () {
      final tr = AppLocalizationsTr();
      expect(friendlyError(_kopuk(), tr), contains('Bağlantı'));
      expect(friendlyError(StateError('x'), tr), contains('Beklenmeyen'));
    });
  });

  group('Kaynak bekçisi', () {
    test('imza l10n\'i ZORUNLU alır', () {
      final kaynak = File('lib/core/api.dart').readAsStringSync();
      expect(
          kaynak,
          contains(
              'String friendlyError(Object error, AppLocalizations l10n)'));
      expect(kaynak, isNot(contains('[AppLocalizations? l10n]')),
          reason: 'opsiyonel olursa derleyici atlanan çağrıyı yakalamaz');
    });

    test('gövdede gömülü kullanıcı metni YOK', () {
      // Tek doğru yer ARB; gövdedeki sabit hem çevrilmez hem tarayıcıya
      // görünmez.
      final kaynak = File('lib/core/api.dart').readAsStringSync();
      expect(kaynak, isNot(contains('Bağlantı kurulamadı')));
      expect(kaynak, isNot(contains('Beklenmeyen bir sorun')));
    });

    test('hiçbir çağrı yeri l10n\'i atlamıyor', () {
      // Derleyici bugün zaten yakalıyor; bu bekçi imza yarın tekrar
      // gevşetilirse konuşur.
      final atlayanlar = <String>[];
      final tekArguman = RegExp(r'friendlyError\(\s*[A-Za-z_.]+\s*\)');
      for (final dosya in Directory('lib')
          .listSync(recursive: true)
          .whereType<File>()
          .where((f) => f.path.endsWith('.dart'))) {
        if (tekArguman.hasMatch(dosya.readAsStringSync())) {
          atlayanlar.add(dosya.path);
        }
      }
      expect(atlayanlar, isEmpty,
          reason: 'l10n geçilmeyen friendlyError çağrısı: $atlayanlar');
    });
  });
}
