import 'dart:typed_data';
import 'dart:ui';

import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/features/face/face_hairline.dart';
import 'package:rytho/features/face/face_segmentation.dart';

/// Sac cizgisinin segmentasyon maskesinden cikarilmasi.
///
/// ## Neden bu dosya iki kez yazildi
///
/// Ust bolge, ML Kit yuz konturunun en ust noktasi "alin ustu" sayilarak
/// hesaplaniyordu. Gercek bir yuzde olculen:
///
///     ust 0,17   orta 0,40   alt 0,42     (klasik San Ting ~0,33 bekler)
///
/// Ilk duzeltme denemesi parlaklik profilinde ten -> sac gecisi ariyordu.
/// AYNI yuzde iki farkli karede 0,17 ve 0,41 verdi; yani kararsizdi. Karar
/// artik egitilmis bir modelin sinif maskesinden cikiyor.
///
/// ## En onemli grup: kel kafa
///
/// Kel bir kafa OLCULEMEZ bir durum degil, farkli bir geometri. Maske "sac
/// yok, yuz teni dogrudan arka plana cikiyor" diyorsa kafatasi tepesi
/// olculebiliyor demektir. Onceki surum bunu "gecis yok -> olcemedim" diye
/// okuyordu: aletin korlugunu verinin yoklugu sanmak.

const _kMask = 256;

/// Sentetik maske kurar. Satir araliklarina gore sinif atar.
///
/// Yuz seridi maskenin ortasinda; disari arka plan.
SegmentationMask _maske({
  required int sacUst,
  required int sacAlt,
  required int tenUst,
  required int tenAlt,
  int seritYari = 40,
}) {
  final b = Uint8List(_kMask * _kMask); // 0 = background
  const merkez = _kMask ~/ 2;
  for (var y = 0; y < _kMask; y++) {
    for (var x = merkez - seritYari; x <= merkez + seritYari; x++) {
      if (x < 0 || x >= _kMask) continue;
      if (y >= sacUst && y < sacAlt) {
        b[y * _kMask + x] = SegClass.hair;
      } else if (y >= tenUst && y < tenAlt) {
        b[y * _kMask + x] = SegClass.faceSkin;
      }
    }
  }
  return SegmentationMask(classes: b, width: _kMask, height: _kMask);
}

void main() {
  // Landmark uzayi maskeyle AYNI olcekte tutuldu ki testler okunur kalsin;
  // farkli olcek ayri bir testte sinaniyor.
  const goruntu = Size(256, 256);
  const browY = 150.0;
  const chinY = 230.0; // alt yukseklik 80
  const axisX = 128.0;
  const faceWidth = 90.0;

  group('sac cizgisi', () {
    test('sac sinirini bulur ve TURUNU hairline der', () {
      // Sac 60-110, ten 110-240. Sinir y=110.
      final m = _maske(sacUst: 60, sacAlt: 110, tenUst: 110, tenAlt: 240);
      final s = hairlineFromMask(
        mask: m,
        imageSize: goruntu,
        browY: browY,
        chinY: chinY,
        axisX: axisX,
        faceWidth: faceWidth,
      );

      expect(s, isNotNull);
      expect(s!.kind, HairlineKind.hairline);
      expect(s.y, closeTo(110, 6));
    });

    test('alindaki GURULTULU satir olcumu oldurmez', () {
      // Cihazda yakalanan kusur. Alindan yukari yurunurken tenin bittigi ILK
      // satirda guvene bakiliyor ve dusukse fonksiyon HEMEN pes ediyordu.
      // Alin kirisigi ya da golge tek bir gurultulu satir uretiyor, guven
      // 0,72'nin altinda kaliyor ve gercek sac cizgisi yirmi piksel yukarida
      // TEMIZ dururken "olculemedi" donuyordu.
      //
      // Cihazdaki gorunumu: ayni yuz bazen 0,31 veriyor, bazen hic
      // olculemiyordu. Ekranda hata yok, sadece ozelligin yarisi yok.
      final m = _maske(sacUst: 60, sacAlt: 110, tenUst: 110, tenAlt: 240);

      // y=125 satirini "ne ten ne sac" yap: alin kirisigi/golge taklidi.
      // Ustundeki bant hala tendir, yani guveni dusuktur.
      const merkez = 256 ~/ 2;
      for (var x = merkez - 40; x <= merkez + 40; x++) {
        m.classes[125 * 256 + x] = SegClass.other;
      }

      final s = hairlineFromMask(
        mask: m,
        imageSize: goruntu,
        browY: browY,
        chinY: chinY,
        axisX: axisX,
        faceWidth: faceWidth,
      );

      expect(s, isNotNull,
          reason: 'tek gurultulu satir gercek sac cizgisini gizliyor');
      expect(s!.y, closeTo(110, 8),
          reason: 'sinir gurultulu satira degil gercek sac cizgisine oturmali');
    });

    test('hicbir aday esigi gecemezse yine null', () {
      // Duzeltme esigi GEVSETMIYOR: bulanik maskeyle olcmus gibi yapmak,
      // bazi ten tonlarina sistematik olarak yanlis alin orani vermek olurdu
      // (model kartinda en kotu durum IoU 71,86 / ortalama 81,10).
      final b = Uint8List(256 * 256);
      const merkez = 256 ~/ 2;
      for (var y = 0; y < 256; y++) {
        for (var x = merkez - 40; x <= merkez + 40; x++) {
          // Ten bolgesi altta; ustunde saç ile arka plan YARI YARIYA —
          // hicbir bant cogunluk tutturamaz.
          if (y >= 110) {
            b[y * 256 + x] = SegClass.faceSkin;
          } else {
            b[y * 256 + x] = x.isEven ? SegClass.hair : SegClass.background;
          }
        }
      }
      final s = hairlineFromMask(
        mask: SegmentationMask(classes: b, width: 256, height: 256),
        imageSize: goruntu,
        browY: browY,
        chinY: chinY,
        axisX: axisX,
        faceWidth: faceWidth,
      );
      expect(s, isNull, reason: 'bulanik sinir kullanilmamali');
    });

    test('olculen sinir KLASIK orana yaklastirir', () {
      // Kusurun kendisi: kontur tepesi kullanilinca ust bolge 0,17 cikiyordu.
      final m = _maske(sacUst: 60, sacAlt: 110, tenUst: 110, tenAlt: 240);
      final s = hairlineFromMask(
        mask: m,
        imageSize: goruntu,
        browY: browY,
        chinY: chinY,
        axisX: axisX,
        faceWidth: faceWidth,
      )!;

      final yuzYuksekligi = chinY - s.y;
      final ust = (browY - s.y) / yuzYuksekligi;
      expect(ust, greaterThan(0.25),
          reason: 'hala kusurlu surumun bolgesinde');
      expect(ust, lessThan(0.45));
    });

    test('farkli olcekli maske dogru esleniyor', () {
      // Maske 256, landmark uzayi 512: her sey iki kat.
      final m = _maske(sacUst: 60, sacAlt: 110, tenUst: 110, tenAlt: 240);
      final s = hairlineFromMask(
        mask: m,
        imageSize: const Size(512, 512),
        browY: browY * 2,
        chinY: chinY * 2,
        axisX: axisX * 2,
        faceWidth: faceWidth * 2,
      );

      expect(s, isNotNull);
      expect(s!.y, closeTo(220, 12),
          reason: 'olcekleme atlanirsa sinir yari yerde cikar');
    });
  });

  group('kel kafa — olculemez DEGIL', () {
    test('sac yoksa kafatasi tepesinden olcer ve crown der', () {
      // Hic sac yok; ten 110-240, ustu dogrudan arka plan.
      final m = _maske(sacUst: 0, sacAlt: 0, tenUst: 110, tenAlt: 240);
      final s = hairlineFromMask(
        mask: m,
        imageSize: goruntu,
        browY: browY,
        chinY: chinY,
        axisX: axisX,
        faceWidth: faceWidth,
      );

      expect(s, isNotNull,
          reason: 'kel kafa olculebilir; susmak aletin korlugunu '
              'verinin yoklugu sanmakti');
      expect(s!.kind, HairlineKind.crown);
      expect(s.y, closeTo(110, 6));
    });
  });

  group('guven esigi', () {
    test('bulanik sinir KULLANILMIYOR', () {
      // Model kartindaki ten tonu farki (en kotu IoU 71,86 / ortalama 81,10)
      // maskenin bazi ten tonlarinda daha az isabetli oldugunu soyluyor.
      // Sinir bulanik ciktiginda olcumu kullanmak, bazi kullanicilara
      // SISTEMATIK olarak daha yanlis bir alin orani vermek olurdu.
      //
      // Seritte sac ile arka plani karistirarak hicbirinin esigi
      // gecemeyecegi bir sinir kuruyoruz.
      final b = Uint8List(_kMask * _kMask);
      const merkez = _kMask ~/ 2;
      for (var y = 0; y < _kMask; y++) {
        for (var x = merkez - 40; x <= merkez + 40; x++) {
          if (y >= 110 && y < 240) {
            b[y * _kMask + x] = SegClass.faceSkin;
          } else if (y < 110) {
            // Yari sac yari arka plan: ikisi de cogunluk esigini gecemiyor.
            b[y * _kMask + x] =
                (x % 2 == 0) ? SegClass.hair : SegClass.background;
          }
        }
      }
      final m = SegmentationMask(classes: b, width: _kMask, height: _kMask);

      expect(
        hairlineFromMask(
          mask: m,
          imageSize: goruntu,
          browY: browY,
          chinY: chinY,
          axisX: axisX,
          faceWidth: faceWidth,
        ),
        isNull,
        reason: 'bulanik sinirdan olcum uretiliyor',
      );
    });

    test('temiz sinirin guveni esigin USTUNDE', () {
      final m = _maske(sacUst: 60, sacAlt: 110, tenUst: 110, tenAlt: 240);
      final s = hairlineFromMask(
        mask: m,
        imageSize: goruntu,
        browY: browY,
        chinY: chinY,
        axisX: axisX,
        faceWidth: faceWidth,
      )!;
      expect(s.confidence, greaterThanOrEqualTo(kMinConfidence));
    });
  });

  group('olculemeyen durumlar', () {
    test('kakul alni ortuyorsa null doner', () {
      // Sac ta kasin dibine kadar iniyor: 60-160. Kas 150'de.
      final m = _maske(sacUst: 60, sacAlt: 160, tenUst: 160, tenAlt: 240);
      expect(
        hairlineFromMask(
          mask: m,
          imageSize: goruntu,
          browY: browY,
          chinY: chinY,
          axisX: axisX,
          faceWidth: faceWidth,
        ),
        isNull,
        reason: 'ortulu alin olculemez — ama kullaniciya SOYLENEBILIR',
      );
    });

    test('yuz teni hic yoksa null doner', () {
      final m = _maske(sacUst: 0, sacAlt: 0, tenUst: 0, tenAlt: 0);
      expect(
        hairlineFromMask(
          mask: m,
          imageSize: goruntu,
          browY: browY,
          chinY: chinY,
          axisX: axisX,
          faceWidth: faceWidth,
        ),
        isNull,
      );
    });

    test('bozuk landmark (kas cenenin altinda) null doner', () {
      final m = _maske(sacUst: 60, sacAlt: 110, tenUst: 110, tenAlt: 240);
      expect(
        hairlineFromMask(
          mask: m,
          imageSize: goruntu,
          browY: 230,
          chinY: 150,
          axisX: axisX,
          faceWidth: faceWidth,
        ),
        isNull,
      );
    });

    test('bozuk goruntu boyutu cokmez', () {
      final m = _maske(sacUst: 60, sacAlt: 110, tenUst: 110, tenAlt: 240);
      expect(
        hairlineFromMask(
          mask: m,
          imageSize: Size.zero,
          browY: browY,
          chinY: chinY,
          axisX: axisX,
          faceWidth: faceWidth,
        ),
        isNull,
      );
    });
  });
}
