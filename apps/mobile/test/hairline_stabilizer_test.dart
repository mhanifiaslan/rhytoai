import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/features/face/hairline_stabilizer.dart';

/// Cihazda yakalanan gercek kusur.
///
/// Arka arkaya iki olcum, ayni yuz, saniyeler arayla:
///
///     ust 0,31   orta 0,33   alt 0,37
///     ust 0,20   orta 0,39   alt 0,41
///
/// Sac one dustugu karede model alin pikselini "sac" sayiyor ve sinir asagi
/// kayiyor. Bu kozmetik degil: sunucu "dar alin" demek icin ortalamadan 0,045
/// fark istiyor ve iki okuma o esigin IKI YANINDA kaliyor. Yani urun ardisik
/// taramalarda celisik sey soylerdi.
///
/// Asagidaki testler kararliligi tutuyor. En onemlisi `KARARSIZ olcum
/// verilmez`: ortalamasini alip sunmak, bilmedigini biliyormus gibi
/// gostermek olurdu.

/// Kas 100, cene 300 -> taban 200. Oran 0,45 ise sac cizgisi y = 100-90 = 10.
double _sacY(double oran) => 100 - oran * 200;

void _ekle(HairlineStabilizer s, List<double> oranlar) {
  for (final o in oranlar) {
    s.add(hairlineY: _sacY(o), browY: 100, chinY: 300);
  }
}

void main() {
  group('yeterli ornek', () {
    test('uc ornekten az ise olcum YOK', () {
      final s = HairlineStabilizer();
      _ekle(s, [0.45, 0.45]);
      expect(s.median, isNull);
      expect(s.stable, isFalse);
      expect(s.hairlineFor(browY: 100, chinY: 300), isNull);
    });

    test('uc ornekte karar verilebilir', () {
      final s = HairlineStabilizer();
      _ekle(s, [0.45, 0.44, 0.46]);
      expect(s.median, closeTo(0.45, 0.001));
      expect(s.stable, isTrue);
    });
  });

  group('medyan uc degerleri sindirir', () {
    test('tek bir sicrama sonucu KAYDIRMAZ', () {
      // Dorduncu ornek gercek olayin ta kendisi: 0,45 yerine 0,25.
      // Ortalama alsaydik 0,41'e duserdi; medyan 0,45'te kaliyor.
      final s = HairlineStabilizer();
      _ekle(s, [0.45, 0.44, 0.46, 0.25, 0.45]);
      expect(s.median, closeTo(0.45, 0.001));
    });

    test('ortalama DEGIL medyan kullaniliyor', () {
      final s = HairlineStabilizer();
      _ekle(s, [0.40, 0.41, 0.42, 0.43, 0.90]);
      final ortalama = (0.40 + 0.41 + 0.42 + 0.43 + 0.90) / 5;
      expect(s.median, closeTo(0.42, 0.001));
      expect(s.median, isNot(closeTo(ortalama, 0.01)));
    });
  });

  group('KARARSIZ olcum verilmez', () {
    test('genis dagilim olcumu gecersiz kilar', () {
      // Gercek olaydaki iki deger: 0,449 ve 0,25 -> yayilim ~0,20.
      final s = HairlineStabilizer();
      _ekle(s, [0.449, 0.25, 0.44]);
      expect(s.spread, greaterThan(HairlineStabilizer.maxSpread));
      expect(s.stable, isFalse);
      expect(s.hairlineFor(browY: 100, chinY: 300), isNull,
          reason: 'kararsizken olcum sunuluyor');
    });

    test('dar dagilim olcumu gecerli kilar', () {
      final s = HairlineStabilizer();
      _ekle(s, [0.45, 0.47, 0.44]);
      expect(s.stable, isTrue);
      final y = s.hairlineFor(browY: 100, chinY: 300);
      expect(y, isNotNull);
      // Medyan 0,45 -> y = 100 - 0,45*200 = 10.
      expect(y!, closeTo(10, 0.5));
    });

    test('kadraj duzelince kararliliga DONULEBILIR', () {
      // Uyarinin kalici olmasi, duzeltildigini fark etmeyen bir ekran demek
      // olurdu. Pencere kaydikca eski uc degerler dusuyor.
      final s = HairlineStabilizer();
      _ekle(s, [0.25, 0.45, 0.44]);
      expect(s.stable, isFalse);

      _ekle(s, [0.45, 0.46, 0.45, 0.44]);
      expect(s.stable, isTrue,
          reason: 'pencere kaydi ama kararsiz sayilmaya devam ediyor');
    });
  });

  group('pencere', () {
    test('en fazla windowSize ornek tutulur', () {
      final s = HairlineStabilizer();
      _ekle(s, List.filled(20, 0.45));
      expect(s.sampleCount, HairlineStabilizer.windowSize);
    });
  });

  group('gecersiz geometri sessizce yutulmaz', () {
    test('cene kasin ustundeyse ornek EKLENMEZ', () {
      final s = HairlineStabilizer();
      expect(s.add(hairlineY: 10, browY: 300, chinY: 100), isFalse);
      expect(s.sampleCount, 0);
    });

    test('sac cizgisi kasin ALTINDAYSA eklenmez', () {
      // Boyle bir olcum fizik olarak anlamsiz; ortalamaya karistirmak
      // sessiz bir bozulma olurdu.
      final s = HairlineStabilizer();
      expect(s.add(hairlineY: 150, browY: 100, chinY: 300), isFalse);
      expect(s.sampleCount, 0);
    });

    test('sacma buyuklukte oran eklenmez', () {
      final s = HairlineStabilizer();
      expect(s.add(hairlineY: -500, browY: 100, chinY: 300), isFalse);
    });
  });

  group('olcek bagimsizligi', () {
    test('yuz kameraya yaklasinca oran DEGISMEZ', () {
      // Ham piksel tutulsaydi yaklasma kararsizlik gibi gorunurdu.
      final a = HairlineStabilizer();
      a.add(hairlineY: 10, browY: 100, chinY: 300); // taban 200
      final b = HairlineStabilizer();
      b.add(hairlineY: 20, browY: 200, chinY: 600); // taban 400, ayni oran

      a.add(hairlineY: 10, browY: 100, chinY: 300);
      a.add(hairlineY: 10, browY: 100, chinY: 300);
      b.add(hairlineY: 20, browY: 200, chinY: 600);
      b.add(hairlineY: 20, browY: 200, chinY: 600);

      expect(a.median, closeTo(b.median!, 0.0001));
    });
  });
}
