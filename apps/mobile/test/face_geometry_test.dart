import 'dart:math' as math;
import 'dart:ui';

import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/features/face/face_geometry.dart';

/// Yüz geometrisi: türetilmiş oranlar ve çerçeveleme kalitesi.
///
/// Bu katmanın iki değişmezi var ve testlerin çoğu onları koruyor:
///
/// 1. **Sunucuya giden şey kişiyi tanımaya yaramaz.** Yalnızca oranlar
///    gider, koordinat gitmez; oranlar iki ondalığa yuvarlanır.
/// 2. **Ölçek bağımsızlık.** Kameraya yakınlık okumayı değiştirmemeli.
FaceLandmarks _yuz({
  double scale = 1.0,
  Offset offset = Offset.zero,
  double? cene,
}) {
  Offset p(double x, double y) =>
      Offset(x * scale + offset.dx, y * scale + offset.dy);

  final ceneYari = (cene ?? 60) * scale / 2;
  return FaceLandmarks(
    faceOval: [p(100, 0), p(200, 150), p(100, 300), p(0, 150)],
    foreheadTop: p(100, 0),
    browMid: p(100, 100),
    noseBase: p(100, 200),
    chin: p(100, 300),
    cheekLeft: p(10, 150),
    cheekRight: p(190, 150),
    jawLeft: Offset(p(100, 260).dx - ceneYari, p(100, 260).dy),
    jawRight: Offset(p(100, 260).dx + ceneYari, p(100, 260).dy),
    mouthLeft: p(70, 240),
    mouthRight: p(130, 240),
    upperLip: p(100, 235),
    lowerLip: p(100, 250),
    eyeLeft: p(60, 110),
    eyeRight: p(140, 110),
  );
}

void main() {
  group('San Ting — üç bölge', () {
    test('üç bölge toplamı bire yakın', () {
      final r = computeRatios(_yuz());
      final toplam = r.upperThird + r.middleThird + r.lowerThird;
      expect(toplam, closeTo(1.0, 0.01));
    });

    test('eşit bölünmüş yüzde üçü de üçte bir', () {
      final r = computeRatios(_yuz());
      expect(r.upperThird, closeTo(0.33, 0.01));
      expect(r.middleThird, closeTo(0.33, 0.01));
      expect(r.lowerThird, closeTo(0.33, 0.01));
    });
  });

  group('ölçek bağımsızlık', () {
    test('kameraya yakınlık oranları değiştirmez', () {
      final yakin = computeRatios(_yuz(scale: 2.4));
      final uzak = computeRatios(_yuz(scale: 0.6));

      expect(yakin.upperThird, closeTo(uzak.upperThird, 0.001));
      expect(yakin.widthToHeight, closeTo(uzak.widthToHeight, 0.001));
      expect(yakin.jawToCheek, closeTo(uzak.jawToCheek, 0.001));
    });

    test('kadrajdaki konum oranları değiştirmez', () {
      final sol = computeRatios(_yuz(offset: const Offset(-90, -40)));
      final sag = computeRatios(_yuz(offset: const Offset(310, 260)));
      expect(sol.toJson(), sag.toJson());
    });
  });

  group('ayırt edicilik', () {
    test('sivri çene ile geniş çene farklı oran verir', () {
      final sivri = computeRatios(_yuz(cene: 40));
      final genis = computeRatios(_yuz(cene: 150));
      expect(sivri.jawToCheek, lessThan(genis.jawToCheek));
    });

    test('simetrik yüz 1.0 civarında', () {
      expect(computeRatios(_yuz()).symmetry, closeTo(1.0, 0.02));
    });

    test('asimetri simetri skorunu düşürür', () {
      final temel = _yuz();
      final egri = FaceLandmarks(
        faceOval: temel.faceOval,
        foreheadTop: temel.foreheadTop,
        browMid: temel.browMid,
        noseBase: temel.noseBase,
        chin: temel.chin,
        // Sol yanak eksene çok daha yakın
        cheekLeft: const Offset(70, 150),
        cheekRight: temel.cheekRight,
        jawLeft: temel.jawLeft,
        jawRight: temel.jawRight,
        mouthLeft: temel.mouthLeft,
        mouthRight: temel.mouthRight,
        upperLip: temel.upperLip,
        lowerLip: temel.lowerLip,
        eyeLeft: temel.eyeLeft,
        eyeRight: temel.eyeRight,
      );
      expect(computeRatios(egri).symmetry, lessThan(0.95));
    });
  });

  group('gizlilik — sunucuya giden veri', () {
    test('yalnızca oranlar gider, koordinat gitmez', () {
      final json = computeRatios(_yuz()).toJson();
      // Piksel koordinatı taşıyan hiçbir alan olmamalı
      expect(json.keys, isNot(contains('faceOval')));
      expect(json.keys, isNot(contains('chin')));
      expect(json.values.every((v) => v.abs() < 10), isTrue,
          reason: 'oranlar 0-10 arasinda olmali; piksel degeri sizmis olabilir');
    });

    test('oranlar iki ondalığa yuvarlanır', () {
      final json = computeRatios(_yuz(scale: 1.37)).toJson();
      for (final v in json.values) {
        expect((v * 100) % 1, closeTo(0, 1e-9),
            reason: 'daha fazla hassasiyet sayi kumesini kisiye ozgu kilar');
      }
    });
  });

  group('bozuk tespit', () {
    test('sıfır boyutlu yüzde nötr oran döner, çökme yok', () {
      final bozuk = FaceLandmarks(
        faceOval: const [],
        foreheadTop: Offset.zero,
        browMid: Offset.zero,
        noseBase: Offset.zero,
        chin: Offset.zero,
        cheekLeft: Offset.zero,
        cheekRight: Offset.zero,
        jawLeft: Offset.zero,
        jawRight: Offset.zero,
        mouthLeft: Offset.zero,
        mouthRight: Offset.zero,
        upperLip: Offset.zero,
        lowerLip: Offset.zero,
        eyeLeft: Offset.zero,
        eyeRight: Offset.zero,
      );
      final r = computeRatios(bozuk);
      expect(r.upperThird, closeTo(0.33, 0.01));
      expect(r.symmetry, 1.0);
    });
  });

  group('çerçeveleme kalitesi', () {
    const kadraj = Size(1080, 1920);
    final hedef = guideOvalInImage(previewSize: kadraj);

    // Yuz kutusu KILAVUZ OVALINE gore olculur, kadraja gore degil. Onceki
    // surumde kadraja gore olculuyordu ve ovali gozle dolduran bir yuz
    // esigin altinda kaliyordu: kullanici kilavuzun dedigini yapiyor,
    // uygulama "biraz yaklas" deyip deklansoru hic acmiyordu.
    Rect kutu(double doluluk, {Offset kaydir = Offset.zero}) {
      final h = hedef.height * doluluk;
      return Rect.fromCenter(
        center: hedef.center + kaydir,
        width: h * 0.75,
        height: h,
      );
    }

    test('yüz yoksa noFace', () {
      expect(assessFrame(faceBox: null, previewSize: kadraj),
          FrameQuality.noFace);
    });

    test('çok küçük yüz tooFar', () {
      expect(assessFrame(faceBox: kutu(0.30), previewSize: kadraj),
          FrameQuality.tooFar);
    });

    test('çok büyük yüz tooClose', () {
      expect(assessFrame(faceBox: kutu(1.6), previewSize: kadraj),
          FrameQuality.tooClose);
    });

    test('merkezden kayık yüz offCentre', () {
      expect(
          assessFrame(
              faceBox: kutu(0.9, kaydir: Offset(hedef.height * 0.4, 0)),
              previewSize: kadraj),
          FrameQuality.offCentre);
    });

    test('eğik baş tilted', () {
      expect(
          assessFrame(
              faceBox: kutu(0.9), previewSize: kadraj, headAngleZ: 25),
          FrameQuality.tilted);
    });

    test('iyi çerçevelenmiş yüz ready', () {
      expect(
          assessFrame(faceBox: kutu(0.9), previewSize: kadraj, headAngleZ: 3),
          FrameQuality.ready);
    });

    test('kontrol sırası: önce mesafe, sonra konum', () {
      // Hem çok uzak hem kayık: kullanıcıya ONCE mesafe söylenmeli.
      // Ayni anda iki sey soylemek okunmuyor.
      expect(
          assessFrame(
              faceBox: kutu(0.20, kaydir: Offset(hedef.height * 0.5, 0)),
              previewSize: kadraj),
          FrameQuality.tooFar);
    });

    test('ML Kit kutusu ovalden DAR olsa da kabul edilir', () {
      // ASIL KALIBRASYON HATASI. ML Kit'in kutusu gorunen kafadan dar: sac
      // ve cene alti disarida kaliyor. Ovali gozle dolduran bir yuzun kutusu
      // ovalin ~%70-85'i cikiyor. Eski esik (kadrajin %30'u) bunu "cok uzak"
      // sayiyordu.
      for (final doluluk in [0.62, 0.70, 0.80, 0.95, 1.05]) {
        expect(assessFrame(faceBox: kutu(doluluk), previewSize: kadraj),
            FrameQuality.ready,
            reason: 'doluluk $doluluk reddedildi');
      }
    });

    test('histerezis: kilitliyken sınır genişler', () {
      // Titremenin sebebi tek esikti: olcum sinirin iki yaninda salinip
      // kilavuzu yesil-sari arasinda cirpitiyordu.
      final sinirda = kutu(kMinGuideFill - 0.04);

      expect(assessFrame(faceBox: sinirda, previewSize: kadraj),
          FrameQuality.tooFar,
          reason: 'kilitli DEGILKEN dar esik gecerli');
      expect(
          assessFrame(
              faceBox: sinirda, previewSize: kadraj, wasReady: true),
          FrameQuality.ready,
          reason: 'kilitliyken ayni kare kabul edilmeli');
    });

    test('kılavuz ovali görüntü uzayına doğru taşınır', () {
      // Oval EKRAN uzayinda ciziliyor, yuz kutusu GORUNTU uzayinda geliyor;
      // onizleme `BoxFit.cover` ile kirpiliyor. Donusum atlanirsa hedefin
      // boyutu yanlis cikar.
      const goruntu = Size(480, 640);
      const ekran = Size(1080, 2340);
      final imgOval =
          guideOvalInImage(previewSize: goruntu, screenSize: ekran);

      final olcek = math.max(ekran.width / goruntu.width,
          ekran.height / goruntu.height);
      expect(imgOval.width * olcek,
          closeTo(ekran.width * kGuideWidthFraction, 0.5));
      // Yatayda kirpildigi icin oval dikeyde kadrajin yarisindan az kaplar.
      expect(imgOval.height / goruntu.height, lessThan(0.5));
      expect(imgOval.height / goruntu.height, greaterThan(0.35));
    });

    test('ters çevrilmiş önizleme boyutu yüzü merkezden kaçık gösterir', () {
      // ASIL HATA BUYDU. ML Kit koordinatlari DONDURULMUS uzayda donuyor
      // (dik, 480x640); ham kare boyutu ise yatay geliyor (640x480). Ham
      // boyut verilince genislik ve yukseklik yer degistiriyor ve kadrajin
      // tam ortasindaki yuz "merkezden kacik" cikiyor — deklansor hic
      // acilmiyordu.
      const dik = Size(480, 640);
      const yatay = Size(640, 480); // ham kare: YANLIS olan bu
      final dikOval = guideOvalInImage(previewSize: dik);
      final yatayOval = guideOvalInImage(previewSize: yatay);

      // Once dogrudan: iki uzayda hedef AYNI OLAMAZ.
      expect(dikOval.center, isNot(yatayOval.center));
      expect(dikOval.height, isNot(closeTo(yatayOval.height, 1)));

      // Sonra sonucu uzerinden: dik uzayda kabul edilen bir yuz, ters boyutla
      // reddedilmeli.
      final yuz = Rect.fromCenter(
        center: dikOval.center,
        width: dikOval.height * 0.62 * 0.75,
        height: dikOval.height * 0.62,
      );

      expect(assessFrame(faceBox: yuz, previewSize: dik), FrameQuality.ready);
      expect(assessFrame(faceBox: yuz, previewSize: yatay),
          isNot(FrameQuality.ready),
          reason: 'ters boyutla ayni yuz kabul edilmemeli — hatanin kendisi');
    });

    test('bozuk önizleme boyutu çökmez', () {
      expect(assessFrame(faceBox: kutu(0.9), previewSize: Size.zero),
          FrameQuality.noFace);
    });
  });
}
