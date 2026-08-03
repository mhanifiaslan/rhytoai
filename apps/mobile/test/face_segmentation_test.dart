import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/features/face/face_segmentation.dart';

/// Segmentasyon boru hattinin **sessizce** yanlis olabilecek yerleri.
///
/// Bu dosyadaki hicbir hata bir istisna uretmez. Kroma indeksi bir bayt
/// kayarsa renkler bozulur, model saci ten sanar, alin olcusu tutmaz ve
/// ekranda yalnizca "seg 300ms sac=%2" yazar — sorunun nerede oldugunu
/// soyleyen hicbir sey yoktur. Bu projede tam olarak bu tur kusurlar
/// defalarca saat kaybettirdi.
///
/// Ayrica Asama #62'de tum bu kod ana isolate'tan isci isolate'a tasindi.
/// Tasima sirasinda bir indeks kaymasi olsaydi yine hicbir hata cikmazdi.

/// NV21: once Y blogu (yukseklik x adim), ardindan araya gecmis VU blogu.
Uint8List _nv21({
  required int width,
  required int height,
  required int stride,
  required int y,
  required int v,
  required int u,
}) {
  final bayt = Uint8List(stride * height + stride * (height ~/ 2));
  for (var i = 0; i < stride * height; i++) {
    bayt[i] = y;
  }
  for (var i = stride * height; i < bayt.length; i += 2) {
    bayt[i] = v;
    bayt[i + 1] = u;
  }
  return bayt;
}

void main() {
  group('NV21 renk cevrimi', () {
    test('notr kroma GRI verir', () {
      // V=U=128 -> kroma katkisi sifir; R=G=B=Y olmali. Sira karisirsa
      // burasi hala gri cikar, asagidaki testler onu yakaliyor.
      final bayt = _nv21(
          width: 4, height: 4, stride: 4, y: 200, v: 128, u: 128);
      final rgb = Float64List(3);
      readPixelRgb(
        format: FrameFormat.nv21SinglePlane,
        plane0: bayt,
        u: 1,
        v: 1,
        width: 4,
        height: 4,
        stride0: 4,
        hedef: rgb,
      );
      expect(rgb[0], closeTo(200, 0.5));
      expect(rgb[1], closeTo(200, 0.5));
      expect(rgb[2], closeTo(200, 0.5));
    });

    test('NV21 sirasi V-sonra-U — ters olursa kirmizi ile mavi yer degistirir',
        () {
      // Yuksek V kirmiziyi buyutur. Sira ters okunsaydi maviyi buyuturdu ve
      // ten rengi maviye kayardi; model tenden emin olamaz, saç sınırı
      // gurultulenir.
      final bayt =
          _nv21(width: 4, height: 4, stride: 4, y: 128, v: 220, u: 128);
      final rgb = Float64List(3);
      readPixelRgb(
        format: FrameFormat.nv21SinglePlane,
        plane0: bayt,
        u: 0,
        v: 0,
        width: 4,
        height: 4,
        stride0: 4,
        hedef: rgb,
      );
      expect(rgb[0], greaterThan(rgb[2]),
          reason: 'V kanali kirmiziyi degil maviyi buyutuyor — sira ters');
      expect(rgb[0], closeTo(128 + 1.370705 * 92, 1));
    });

    test('kroma YARIM cozunurluklu: komsu iki piksel ayni cifti paylasir', () {
      final bayt = Uint8List(4 * 4 + 4 * 2);
      for (var i = 0; i < 16; i++) {
        bayt[i] = 100;
      }
      // Ilk kroma cifti (V=200,U=128), ikinci cift (V=60,U=128).
      bayt[16] = 200;
      bayt[17] = 128;
      bayt[18] = 60;
      bayt[19] = 128;

      final a = Float64List(3);
      final b = Float64List(3);
      readPixelRgb(
          format: FrameFormat.nv21SinglePlane,
          plane0: bayt,
          u: 0,
          v: 0,
          width: 4,
          height: 4,
          stride0: 4,
          hedef: a);
      readPixelRgb(
          format: FrameFormat.nv21SinglePlane,
          plane0: bayt,
          u: 1,
          v: 0,
          width: 4,
          height: 4,
          stride0: 4,
          hedef: b);
      // u=0 ve u=1 AYNI cifti kullanmali (u & ~1).
      expect(a[0], closeTo(b[0], 0.001));

      final c = Float64List(3);
      readPixelRgb(
          format: FrameFormat.nv21SinglePlane,
          plane0: bayt,
          u: 2,
          v: 0,
          width: 4,
          height: 4,
          stride0: 4,
          hedef: c);
      // u=2 SONRAKI cifte gecmeli.
      expect(c[0], lessThan(a[0]));
    });

    test('tampon disi okuma cokmez', () {
      final bayt = Uint8List(8);
      final rgb = Float64List(3);
      readPixelRgb(
        format: FrameFormat.nv21SinglePlane,
        plane0: bayt,
        u: 99,
        v: 99,
        width: 4,
        height: 4,
        stride0: 4,
        hedef: rgb,
      );
      expect(rgb[0], 0);
    });
  });

  group('BGRA', () {
    test('kanal sirasi B-G-R-A okunur', () {
      // iOS BGRA veriyor; siralamayi duz okumak kirmizi ile maviyi
      // degistirirdi.
      final bayt = Uint8List.fromList([10, 20, 30, 255]);
      final rgb = Float64List(3);
      readPixelRgb(
        format: FrameFormat.bgra,
        plane0: bayt,
        u: 0,
        v: 0,
        width: 1,
        height: 1,
        stride0: 4,
        hedef: rgb,
      );
      expect(rgb[0], 30, reason: 'R');
      expect(rgb[1], 20, reason: 'G');
      expect(rgb[2], 10, reason: 'B');
    });
  });

  group('RGBA (galeri, Revize R5)', () {
    test('kanal sirasi R-G-B-A okunur — BGRA ile AYNI baytlar farkli renk',
        () {
      // dart:ui cozucusu rawRgba verir. Ayni dort bayt BGRA diye okunsaydi
      // kirmizi ile mavi yer degistirirdi; model saci ten sanar ve galeri
      // fotograflarinda alin olcusu sessizce yanlis cikardi.
      final bayt = Uint8List.fromList([10, 20, 30, 255]);
      final rgb = Float64List(3);
      readPixelRgb(
        format: FrameFormat.rgba,
        plane0: bayt,
        u: 0,
        v: 0,
        width: 1,
        height: 1,
        stride0: 4,
        hedef: rgb,
      );
      expect(rgb[0], 10, reason: 'R');
      expect(rgb[1], 20, reason: 'G');
      expect(rgb[2], 30, reason: 'B');
    });

    test('tampon disi okuma cokmez, sifir verir', () {
      final rgb = Float64List(3)..[0] = 99;
      readPixelRgb(
        format: FrameFormat.rgba,
        plane0: Uint8List(4),
        u: 5,
        v: 5,
        width: 8,
        height: 8,
        stride0: 32,
        hedef: rgb,
      );
      expect(rgb[0], 0);
    });
  });

  group('dondurme eslemesi', () {
    // Koordinat uzaylarini karistirmak bu projede daha once noktalarin yuzun
    // YANINA dusmesine yol acti.

    test('0 derece birebir', () {
      final s = sourcePixel(dx: 3, dy: 7, width: 10, height: 20, degrees: 0);
      expect(s.u, 3);
      expect(s.v, 7);
    });

    test('90 derece', () {
      final s = sourcePixel(dx: 0, dy: 0, width: 10, height: 20, degrees: 90);
      expect(s.u, 0);
      expect(s.v, 19);
    });

    test('180 derece kosegen kosede biter', () {
      final s = sourcePixel(dx: 0, dy: 0, width: 10, height: 20, degrees: 180);
      expect(s.u, 9);
      expect(s.v, 19);
    });

    test('270 derece', () {
      final s = sourcePixel(dx: 0, dy: 0, width: 10, height: 20, degrees: 270);
      expect(s.u, 9);
      expect(s.v, 0);
    });

    test('90 ve 270 birbirinin tersi', () {
      const w = 10, h = 20;
      final a = sourcePixel(dx: 4, dy: 6, width: w, height: h, degrees: 90);
      final b = sourcePixel(dx: 4, dy: 6, width: w, height: h, degrees: 270);
      expect(a.u, w - 1 - b.u);
      expect(a.v, h - 1 - b.v);
    });
  });

  group('argmax', () {
    /// Duz, satir oncelikli tampon: ((y * 256) + x) * 6 + sinif.
    ///
    /// Ic ice liste BIRAKILDI: `Interpreter.run` onlari eleman eleman bayta
    /// ceviriyordu ve cihazda olculen 1656 ms'nin baskin kalemi buydu.
    Float32List tensor(List<double> Function(int x, int y) uret) {
      final t = Float32List(256 * 256 * 6);
      for (var y = 0; y < 256; y++) {
        for (var x = 0; x < 256; x++) {
          final p = uret(x, y);
          final taban = ((y * 256) + x) * 6;
          for (var c = 0; c < 6; c++) {
            t[taban + c] = p[c];
          }
        }
      }
      return t;
    }

    test('en yuksek olasilikli sinif secilir', () {
      final maske = argmaxMask(tensor((x, y) {
        final p = List.filled(6, 0.1);
        p[SegClass.hair] = 0.9;
        return p;
      }));
      expect(maske.length, 256 * 256);
      expect(maske.every((c) => c == SegClass.hair), isTrue);
    });

    test('esitlikte ILK sinif kazanir', () {
      // `>` kullaniliyor, `>=` degil. Fark onemli: `>=` olsaydi butun
      // olasiliklar esitken maske "aksesuar" ile dolardi ve sac hic
      // bulunamazdi.
      final maske = argmaxMask(tensor((x, y) => List.filled(6, 0.16)));
      expect(maske.every((c) => c == SegClass.background), isTrue);
    });

    test('piksel piksel farkli sinif verebilir', () {
      final maske = argmaxMask(tensor((x, y) {
        final p = List.filled(6, 0.0);
        p[y < 128 ? SegClass.hair : SegClass.faceSkin] = 1.0;
        return p;
      }));
      expect(maske[0], SegClass.hair);
      expect(maske[200 * 256], SegClass.faceSkin);
    });

    test('maske 256x256 ve satir-oncelikli', () {
      final maske = argmaxMask(tensor((x, y) {
        final p = List.filled(6, 0.0);
        p[x == 5 && y == 3 ? SegClass.clothes : SegClass.background] = 1.0;
        return p;
      }));
      expect(maske[3 * 256 + 5], SegClass.clothes);
      expect(maske[5 * 256 + 3], SegClass.background);
    });
  });
}
