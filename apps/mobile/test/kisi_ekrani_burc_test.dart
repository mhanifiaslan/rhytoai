// Eklenen kişinin ekranındaki Büyük Üçlü — KL-turu'nun hayatta kalmış
// kopyası.
//
// Sunucu `sun_sign`/`moon_sign`/`ascendant` alanlarını BİLEREK Türkçe
// bırakıyor (backend/services/prompts/__init__.py: "DOKUNULMAZ") ve
// yerelleşmiş karşılığı ayrı `*_local` alanında veriyor. Uygulamadaki diğer
// yedi gösterim yeri `localizedSignName` kullanıyordu; bu ekran tek
// istisnaydı ve İngilizce cihazda "Oğlak ♑" basıyordu. Kişi eklemek
// kontenjanlı bir özellik, yani testçinin baktığı ilk yerlerden.
//
// Panel `_HaritaBolumu`/`_MuhurSatiri` özel (private) olduğu ve veri ağdan
// geldiği için bekçi kaynağı okuyor: kusur tek satırlık bir
// kopyala-yapıştırla geri gelebilir. Sarmalayıcının kendi davranışı
// burc_yerellestirme_test.dart'ta sabitli.
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

const _yol = 'lib/features/people/person_detail_screen.dart';

void main() {
  test('Büyük Üçlü ham `chart[...]` değeri BASMAZ', () {
    final kaynak = File(_yol).readAsStringSync();
    expect(kaynak.contains('deger: chart['), isFalse,
        reason: '$_yol: ham değer _MuhurSatiri\'ye doğrudan veriliyor; '
            'localizedSignName(l10n, ...) ile sarılmalı');
  });

  test('üç alan da localizedSignName ile sarılı', () {
    final kaynak = File(_yol).readAsStringSync();
    for (final alan in ['sun_sign', 'moon_sign', 'ascendant']) {
      expect(kaynak,
          contains("localizedSignName(l10n, chart['$alan'] as String?)"),
          reason: '$alan çevrilmeden basılıyor');
    }
  });

  test('sunucu hâlâ ham Türkçe gönderiyor varsayımı yazılı', () {
    // Bu bekçinin dayanağı: alanlar sunucuda Türkçe kalıyor. Sunucu bir gün
    // `sun_sign`i yerelleştirirse localizedSignName zararsız (tanınmayan
    // değer aynen döner), ama o zaman bu dosyanın gerekçesi değişir.
    final sunucu = File('../../backend/services/prompts/__init__.py')
        .readAsStringSync();
    expect(sunucu, contains('DOKUNULMAZ'),
        reason: 'sunucu artık burç adlarını yerelleştiriyorsa bu testin '
            'gerekçesi güncellenmeli');
  });
}
