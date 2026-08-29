// Çark geometrisi bekçileri (HI-turu HA3).
//
// Canlı kusurun regresyon testi buradadır: eski çark isabeti ve çizimi
// İKİ AYRI hesapla yapıyordu (size/2-58 vs size/2-46) ve stellium'da
// Venüs'e dokunan kullanıcıya Merkür açılıyordu. Yeni mimaride isabet
// tablosu ÇİZİM yerleşiminin kendisidir — bu dosya o değişmezi sabitler.
import 'dart:ui';

import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/widgets/chart/chart_data.dart';
import 'package:rytho/widgets/chart/wheel_layout.dart';

ChartPoint _p(String name, double lon) => ChartPoint(
      name: name,
      localName: name,
      absPosition: lon,
      signIndex: signIndexFromAny(null, lon),
      degreeInSign: lon % 30,
    );

ChartData _tekHalka(List<ChartPoint> points,
        {List<ChartHouse> houses = const [],
        List<ChartAspect> aspects = const []}) =>
    ChartData(
      rings: [ChartRing(kind: ChartRingKind.natal, points: points)],
      houses: houses,
      aspects: aspects,
      hourKnown: houses.isNotEmpty,
    );

List<ChartHouse> _evler(double ascLon) => [
      for (var i = 0; i < 12; i++)
        ChartHouse(house: i + 1, absPosition: (ascLon + i * 30) % 360),
    ];

void main() {
  group('isabet == çizim (canlı kusurun ölümü)', () {
    test('her glifin merkezine dokunmak O glifi döndürür', () {
      final data = _tekHalka([
        _p('Sun', 10), _p('Moon', 100), _p('Mars', 200), _p('Venus', 300),
      ], houses: _evler(0));
      final l = WheelLayout.compute(const Size(360, 360), data);
      for (final ring in l.placements) {
        for (final g in ring) {
          final hit = l.hitTest(g.center);
          expect(hit?.placement?.point.name, g.point.name,
              reason: '${g.point.name} merkezine dokunuş kendisini '
                  'bulmalı — isabet ve çizim ayrıştı demektir');
        }
      }
    });

    test('stellium yelpazesinde bile doğru gezegen bulunur', () {
      // 4 gezegen 3° içinde: eski algoritma %3 modulo ile 4.yü 1.nin
      // üstüne bindiriyordu.
      final data = _tekHalka([
        _p('Sun', 120), _p('Mercury', 121), _p('Venus', 122),
        _p('Mars', 123),
      ], houses: _evler(0));
      final l = WheelLayout.compute(const Size(360, 360), data);
      final adlar = <String>{};
      for (final g in l.placements.first) {
        final hit = l.hitTest(g.center);
        expect(hit?.placement, isNotNull);
        adlar.add(hit!.placement!.point.name);
      }
      expect(adlar, {'Sun', 'Mercury', 'Venus', 'Mars'},
          reason: 'dört glif dört AYRI dokunma hedefi olmalı');
    });

    test('glifler üst üste binmez (asgari ayrım)', () {
      final data = _tekHalka([
        for (var i = 0; i < 6; i++) _p('P$i', 50 + i * 1.0),
      ], houses: _evler(0));
      final l = WheelLayout.compute(const Size(360, 360), data);
      final yerler = l.placements.first;
      for (var i = 0; i < yerler.length; i++) {
        for (var j = i + 1; j < yerler.length; j++) {
          expect((yerler[i].center - yerler[j].center).distance,
              greaterThan(14.0),
              reason:
                  '${yerler[i].point.name} ile ${yerler[j].point.name} '
                  'üst üste');
        }
      }
    });
  });

  group('0°/360° sarımı', () {
    test('Balık ucu ile Koç başı TEK küme sayılır', () {
      // Eski kusur: (lon - prevLon).abs() < 7 sarımı görmüyordu.
      final data = _tekHalka([
        _p('Neptune', 358), _p('Mercury', 2),
      ], houses: _evler(0));
      final l = WheelLayout.compute(const Size(360, 360), data);
      final a = l.placements.first[0];
      final b = l.placements.first[1];
      // Küme yayılmışsa gösterim boylamları gerçekten ayrışmıştır.
      expect((a.center - b.center).distance, greaterThan(14.0));
      expect(a.fanned || b.fanned, isTrue,
          reason: '358° ve 2° komşudur; yelpaze açılmalıydı');
    });
  });

  group('düzen sözleşmeleri', () {
    test('evli düzende AC saat 9 yönünde', () {
      final data = _tekHalka([_p('Sun', 95)], houses: _evler(95));
      final l = WheelLayout.compute(const Size(360, 360), data);
      final ac = l.onCircle(95, 100); // AC boylamı
      // Saat 9 = merkezin solu.
      expect(ac.dx, lessThan(l.center.dx));
      expect((ac.dy - l.center.dy).abs(), lessThan(0.001));
    });

    test('evsiz düzende 0° Koç solda', () {
      final data = _tekHalka([_p('Sun', 0)]);
      final l = WheelLayout.compute(const Size(360, 360), data);
      expect(l.ascLon, 0);
      final sifir = l.onCircle(0, 100);
      expect(sifir.dx, lessThan(l.center.dx));
    });

    test('bi-wheel dış bandı yer açar ve dış glifler kendi bandında',
        () {
      final data = ChartData(
        rings: [
          ChartRing(
              kind: ChartRingKind.natal, points: [_p('Sun', 10)]),
          ChartRing(
              kind: ChartRingKind.transit, points: [_p('Saturn', 200)]),
        ],
        houses: _evler(0),
        aspects: const [],
      );
      final l = WheelLayout.compute(const Size(360, 360), data);
      expect(l.outerBandOuter, greaterThan(l.outerBandInner));
      expect(l.signOuter, lessThanOrEqualTo(l.outerBandInner));
      final dis = l.placements[1].single;
      expect(dis.radius, greaterThan(l.signOuter),
          reason: 'dış halka glifi kendi bandında olmalı');
    });
  });

  group('açı kirişleri', () {
    test('AC/MC uçlu açı çizilir (sessiz düşüş bitti)', () {
      // Eski kusur: uçlar yalnız points'te aranıyordu, AC/MC houses'ta
      // yaşadığı için en kişisel açılar SESSİZCE düşüyordu.
      final json = {
        'points': [
          {'name': 'Sun', 'abs_position': 100.0, 'position': 10.0,
           'sign': 'Can', 'retrograde': false, 'house_no': 1},
        ],
        'houses': [
          for (var i = 0; i < 12; i++)
            {'house': i + 1, 'abs_position': (40.0 + i * 30) % 360,
             'sign': 'Tau', 'position': 10.0},
        ],
        'aspects': [
          {'p1': 'Sun', 'p2': 'Ascendant', 'aspect': 'sextile',
           'orbit': 0.5},
        ],
      };
      final data = ChartData.fromNatal(json);
      final l = WheelLayout.compute(const Size(360, 360), data);
      expect(l.segments, hasLength(1),
          reason: 'Ascendant ucu artık çözülmeli');
    });

    test('kavuşum kiriş üretmez, jant braketi üretir', () {
      final data = _tekHalka(
        [_p('Sun', 10), _p('Mercury', 12)],
        houses: _evler(0),
        aspects: const [
          ChartAspect(p1: 'Sun', p2: 'Mercury', kind: 'conjunction',
              orb: 2.0),
        ],
      );
      final l = WheelLayout.compute(const Size(360, 360), data);
      final seg = l.segments.single;
      expect(seg.isConjunction, isTrue);
      expect(seg.rimMidLon, closeTo(11.0, 0.01));
    });

    test('çözülemeyen uç açıyı sessizce DÜŞÜRÜR (uydurma uç yok)', () {
      final data = _tekHalka(
        [_p('Sun', 10)],
        houses: _evler(0),
        aspects: const [
          ChartAspect(p1: 'Sun', p2: 'Pluto', kind: 'trine', orb: 1.0),
        ],
      );
      final l = WheelLayout.compute(const Size(360, 360), data);
      expect(l.segments, isEmpty);
    });

    test('kirişe dokunmak açıyı, glife dokunmak gezegeni döndürür', () {
      final data = _tekHalka(
        [_p('Sun', 0), _p('Saturn', 180)],
        houses: _evler(90),
        aspects: const [
          ChartAspect(p1: 'Sun', p2: 'Saturn', kind: 'opposition',
              orb: 1.0),
        ],
      );
      final l = WheelLayout.compute(const Size(360, 360), data);
      // Kirişin ortası = merkez (karşıt açı).
      final hit = l.hitTest(l.center);
      expect(hit?.segment?.aspect.kind, 'opposition');
      // Glif önceliklidir.
      final glif = l.placements.first.first;
      expect(l.hitTest(glif.center)?.placement, isNotNull);
    });
  });
}
