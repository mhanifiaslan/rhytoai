// ChartData normalizasyon bekçileri (HI-turu HA2).
//
// Üç sunucu yükünün farklılıkları (orbit/orb, position/degree_in_sign,
// 'Ari'/'aries') bu modelde ölür; testler dört fabrikanın sözleşmesini
// ve iki doktrini sabitler: AC/MC enjeksiyonu (saatliyken) ve transit
// noktalarının ev iddiasının ATILMASI.
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/widgets/chart/chart_data.dart';
import 'package:rytho/widgets/chart/wheel_painter.dart'
    show WheelAspectFilter, aspectVisible;

Map<String, dynamic> _natalJson({bool saatli = true}) => {
      'points': [
        {'name': 'Sun', 'name_local': 'Güneş', 'abs_position': 100.0,
         'position': 10.0, 'sign': 'Can', 'retrograde': false,
         'house_no': saatli ? 3 : null, 'speed': 0.98},
        {'name': 'Saturn', 'name_local': 'Satürn', 'abs_position': 305.5,
         'position': 5.5, 'sign': 'Aqu', 'retrograde': true,
         'house_no': saatli ? 10 : null, 'speed': -0.05},
      ],
      'houses': saatli
          ? [
              for (var i = 0; i < 12; i++)
                {'house': i + 1, 'abs_position': (40.0 + i * 30) % 360,
                 'sign': 'Tau', 'position': 10.0},
            ]
          : <Map<String, dynamic>>[],
      'aspects': [
        {'p1': 'Sun', 'p2': 'Saturn', 'aspect': 'trine', 'orbit': 2.1,
         'movement': 'applying', 'p1_local': 'Güneş',
         'p2_local': 'Satürn', 'aspect_local': 'Üçgen'},
      ],
    };

void main() {
  group('fromNatal', () {
    test('alanlar normalize olur; orbit anahtarı okunur', () {
      final d = ChartData.fromNatal(_natalJson());
      final sun = d.rings.first.pointByName('Sun')!;
      expect(sun.localName, 'Güneş');
      expect(sun.signIndex, 3); // Can → Yengeç
      expect(sun.houseNo, 3);
      final a = d.aspects.single;
      expect(a.orb, 2.1);
      expect(a.applying, isTrue);
      expect(a.localLabel, 'Güneş Üçgen Satürn');
    });

    test('AC/MC saatliyken birinci sınıf nokta olur', () {
      final d = ChartData.fromNatal(_natalJson());
      final ac = d.rings.first.pointByName('Ascendant')!;
      expect(ac.isAngle, isTrue);
      expect(ac.absPosition, 40.0); // houses[0]
      expect(d.rings.first.pointByName('Medium_Coeli')!.absPosition,
          (40.0 + 9 * 30) % 360);
    });

    test('saatsizken AC/MC ÜRETİLMEZ ve evsiz düzen', () {
      final d = ChartData.fromNatal(_natalJson(saatli: false));
      expect(d.houseless, isTrue);
      expect(d.hourKnown, isFalse);
      expect(d.rings.first.pointByName('Ascendant'), isNull);
    });
  });

  group('fromSky', () {
    test('longitude/orb/degree_in_sign anahtarları normalize olur', () {
      final d = ChartData.fromSky({
        'planets': [
          {'name': 'Venus', 'name_local': 'Venüs', 'longitude': 215.3,
           'sign': 'scorpio', 'degree_in_sign': 5.3,
           'retrograde': false},
        ],
        'aspects': [
          {'p1': 'Venus', 'p2': 'Mars', 'aspect': 'square', 'orb': 1.4,
           'p1_local': 'Venüs', 'p2_local': 'Mars',
           'aspect_local': 'Kare'},
        ],
      });
      final v = d.rings.first.points.single;
      expect(v.absPosition, 215.3);
      expect(v.signIndex, 7); // scorpio
      expect(v.degreeInSign, 5.3);
      expect(d.aspects.single.orb, 1.4);
      expect(d.houseless, isTrue);
    });
  });

  group('fromTransits (bi-wheel)', () {
    final transitsJson = {
      'transiting_points': [
        {'name': 'Saturn', 'name_local': 'Satürn', 'abs_position': 200.0,
         'position': 20.0, 'sign': 'Lib', 'retrograde': false,
         // Greenwich artefaktı: İSTEMCİDE ATILMALI.
         'house_no': 7, 'house': 'Seventh_House'},
      ],
      'aspects_to_natal': [
        {'p1': 'Saturn', 'p2': 'Sun', 'aspect': 'square', 'orbit': 0.8,
         'movement': 'applying'},
      ],
    };

    test('transit ev iddiası ATILIR; çapraz açı halkaları doğru', () {
      final d = ChartData.fromTransits(_natalJson(), transitsJson);
      expect(d.isBiWheel, isTrue);
      final transitSaturn = d.rings[1].pointByName('Saturn')!;
      expect(transitSaturn.houseNo, isNull,
          reason: 'transit gezegene ev iddia etmek uydurmadır');
      final a = d.aspects.single;
      expect(a.isCross, isTrue);
      expect(a.p1Ring, 1); // transit ucu dış halka
      expect(a.p2Ring, 0); // natal ucu iç halka
      // Evler İÇ haritanındır (bi-wheel konvansiyonu).
      expect(d.houses.first.absPosition, 40.0);
    });
  });

  group('fromSynastry', () {
    final synastryJson = {
      'points1': [
        {'name': 'Sun', 'name_local': 'Güneş', 'abs_position': 100.0,
         'position': 10.0, 'sign': 'Can', 'retrograde': false,
         'house_no': 1},
      ],
      'points2': [
        {'name': 'Moon', 'name_local': 'Ay', 'abs_position': 280.0,
         'position': 10.0, 'sign': 'Cap', 'retrograde': false,
         'house_no': null},
      ],
      'houses1': [
        for (var i = 0; i < 12; i++)
          {'house': i + 1, 'abs_position': (10.0 + i * 30) % 360,
           'sign': 'Ari', 'position': 10.0},
      ],
      'houses2': <Map<String, dynamic>>[], // saatsiz taraf
      'aspects': [
        {'p1': 'Sun', 'p2': 'Moon', 'aspect': 'opposition', 'orbit': 0.0},
      ],
    };

    test('iç=kullanıcı, dış=kişi; yalnız çapraz açılar', () {
      final d = ChartData.fromSynastry(synastryJson,
          innerLabel: 'sen', outerLabel: 'eşin');
      expect(d.rings[1].kind, ChartRingKind.partner);
      expect(d.rings[1].label, 'eşin');
      final a = d.aspects.single;
      expect((a.p1Ring, a.p2Ring), (0, 1));
      // Evler A'nın (saatli taraf); AC yalnız ev sahibine eklenir.
      expect(d.houses, hasLength(12));
      expect(d.rings[0].pointByName('Ascendant'), isNotNull);
      expect(d.rings[1].pointByName('Ascendant'), isNull);
    });

    test('B tarafının evleri seçilir ve boşsa evsiz düzen', () {
      final d = ChartData.fromSynastry(synastryJson,
          useInnerHouses: false);
      expect(d.houseless, isTrue,
          reason: 'saatsiz tarafın evi yok — öğle dolgusu çizilmez');
    });
  });

  group('aspectVisible (ressam+tablo+test ortak kuralı)', () {
    const sert = ChartAspect(p1: 'a', p2: 'b', kind: 'square', orb: 2.0);
    const minor =
        ChartAspect(p1: 'a', p2: 'b', kind: 'quincunx', orb: 1.0);

    test('filtreler ve orb tavanı', () {
      expect(aspectVisible(sert, WheelAspectFilter.hard, 8), isTrue);
      expect(aspectVisible(sert, WheelAspectFilter.soft, 8), isFalse);
      expect(aspectVisible(sert, WheelAspectFilter.all, 1.0), isFalse,
          reason: 'orb tavanı aşan açı çizilmez');
      expect(aspectVisible(minor, WheelAspectFilter.all, 8), isFalse,
          reason: 'minörler varsayılan kapalı');
      expect(
          aspectVisible(minor, WheelAspectFilter.all, 8,
              showMinors: true),
          isTrue);
    });
  });
}
