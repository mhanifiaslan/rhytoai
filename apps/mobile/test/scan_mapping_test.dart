import 'dart:ui';

import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/features/face/face_scan_overlay.dart';

/// Tarama noktalarinin GORUNTU uzayindan EKRAN uzayina tasinmasi.
///
/// Bu esleme iki kez bozuldu ve ikisinde de kusur SESSIZDI — hicbir hata
/// cikmadi, noktalar sadece yanlis yere dustu:
///
/// 1. Olcekleme icin verilen goruntu boyutu UYDURULMUSTU (`yuz kutusu x 3`).
///    Gercek kareyle ilgisi olmadigi icin noktalar rastgele bir yerde
///    beliriyordu.
/// 2. On kamera onizlemesi ayna gibi gosteriliyor (CameraX varsayilani) ama
///    ML Kit koordinatlari aynalanMAMIS sensor uzayinda geliyor. Cihazda
///    "noktalar yuzumun solunda" diye gorundu.
///
/// Ikincisinin neden gec fark edildigi onemli: **aynalamak kadrajlama
/// kontrolunu etkilemiyor.** Merkeze uzaklik aynalamada degismiyor, yalnizca
/// isareti donuyor. Yani kilavuz dogru calisirken noktalar yanlis yerdeydi.

void main() {
  // Dik goruntu, uzun ekran: yatayda kirpilir (BoxFit.cover).
  const goruntu = Size(480, 640);
  const ekran = Size(1080, 2340);

  group('BoxFit.cover eslemesi', () {
    test('goruntu merkezi ekran merkezine dusrer', () {
      final sonuc = mapScanPoints(
        points: [Offset(goruntu.width / 2, goruntu.height / 2)],
        imageSize: goruntu,
        screenSize: ekran,
        mirrored: false,
      );
      expect(sonuc.single.dx, closeTo(ekran.width / 2, 0.5));
      expect(sonuc.single.dy, closeTo(ekran.height / 2, 0.5));
    });

    test('dikeyde tam kaplar — ust ve alt kenar ekrana oturur', () {
      final sonuc = mapScanPoints(
        points: [const Offset(240, 0), const Offset(240, 640)],
        imageSize: goruntu,
        screenSize: ekran,
        mirrored: false,
      );
      expect(sonuc.first.dy, closeTo(0, 0.5));
      expect(sonuc.last.dy, closeTo(ekran.height, 0.5));
    });

    test('yatayda kirpilir — kenarlar ekran disina tasar', () {
      final sonuc = mapScanPoints(
        points: [const Offset(0, 320)],
        imageSize: goruntu,
        screenSize: ekran,
        mirrored: false,
      );
      expect(sonuc.single.dx, lessThan(0),
          reason: 'cover yatayda kirpiyor; sol kenar ekranin disinda kalmali');
    });

    test('bozuk goruntu boyutu cokmez', () {
      expect(
        mapScanPoints(
          points: [const Offset(1, 1)],
          imageSize: Size.zero,
          screenSize: ekran,
          mirrored: false,
        ),
        isEmpty,
      );
    });
  });

  group('aynalama', () {
    test('merkez aynalamada YERINDE kalir', () {
      // Bu, kusurun neden gec fark edildigini gosteriyor: yuz tam ortadayken
      // aynalama hicbir sey degistirmiyor.
      final duz = mapScanPoints(
        points: [Offset(goruntu.width / 2, 200)],
        imageSize: goruntu,
        screenSize: ekran,
        mirrored: false,
      );
      final ayna = mapScanPoints(
        points: [Offset(goruntu.width / 2, 200)],
        imageSize: goruntu,
        screenSize: ekran,
        mirrored: true,
      );
      expect(ayna.single.dx, closeTo(duz.single.dx, 0.5));
    });

    test('merkezden kacik nokta KARSI tarafa gecer', () {
      const nokta = Offset(120, 200); // goruntunun sol yarisi
      final duz = mapScanPoints(
        points: const [nokta],
        imageSize: goruntu,
        screenSize: ekran,
        mirrored: false,
      );
      final ayna = mapScanPoints(
        points: const [nokta],
        imageSize: goruntu,
        screenSize: ekran,
        mirrored: true,
      );

      final orta = ekran.width / 2;
      expect(duz.single.dx, lessThan(orta));
      expect(ayna.single.dx, greaterThan(orta),
          reason: 'aynalanan nokta ekran merkezinin obur tarafinda olmali');
      // Merkeze uzakliklar esit: aynalama bir kaydirma degil, yansitma.
      expect((ayna.single.dx - orta).abs(),
          closeTo((duz.single.dx - orta).abs(), 0.5));
    });

    test('dikey eksen aynalamadan ETKILENMEZ', () {
      final duz = mapScanPoints(
        points: const [Offset(120, 200)],
        imageSize: goruntu,
        screenSize: ekran,
        mirrored: false,
      );
      final ayna = mapScanPoints(
        points: const [Offset(120, 200)],
        imageSize: goruntu,
        screenSize: ekran,
        mirrored: true,
      );
      expect(ayna.single.dy, closeTo(duz.single.dy, 0.001));
    });
  });
}
