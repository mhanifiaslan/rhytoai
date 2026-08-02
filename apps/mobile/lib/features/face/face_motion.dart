/// Hareket hızı — sıcak–soğuk ekseni için tek dürüst ölçüm.
///
/// Gelenekte mizaç iki eksende okunur. Durağan geometriden yalnızca
/// kuru–nemli çıkıyordu; sıcak–soğuk ekseni "canlı renk, **hızlı hareket**,
/// gür ses"e bakıyor ve o eksen şimdiye kadar ölçülemedi diye modele
/// bildiriliyordu.
///
/// Üç adaydan bu seçildi:
///
/// * **Ten rengi: hayır.** Kamera mutlak yüz rengini ölçtüğünde ölçtüğü şey
///   mizaç değil etnisitedir; korpustan tam da bu sebeple çıkardığımız
///   eşlemeleri otomatik ölçüm olarak geri getirirdi.
/// * **Ses perdesi: hayır.** Perde büyük ölçüde cinsiyete bağlı; "kalın ses →
///   dayanıklılık" demek erkeklere ve kadınlara sistematik olarak farklı
///   okuma vermek olurdu.
/// * **Hareket: evet.** Irkla da cinsiyetle de korele değil, akış zaten
///   elimizde, yeni izin ya da yeni veri türü gerektirmiyor.
///
/// ## Ölçümün kendi sorunu — ve çözümü
///
/// Kullanıcı deklanşör için **bilerek sabit duruyor.** Hareket çabukluğunu
/// kıpırdamamaya çalışan birinde ölçmek yanlış şeyi ölçer. Bu yüzden iki
/// ayrı sayı üretiliyor:
///
/// * [MotionMetrics.motionRate] — **kilit dolmadan önceki** serbest evrede,
///   kullanıcı kadrajı ararken. Burada kimse poz vermiyor.
/// * [MotionMetrics.stillness] — kilit dolduktan sonraki **istemsiz**
///   mikro hareket. Sabit durmaya çalışırken bile beden durmuyor ve o artık
///   iradeye tabi değil.
///
/// Örnek kısaysa hiçbiri raporlanmaz: az veriyle ölçüm uydurmaktansa
/// "ölçemedim" demek doğru.
library;

import 'dart:math' as math;
import 'dart:ui';

/// Ölçüm sonucu. Tüm değerler **yüz genişliği / saniye** cinsinden, yani
/// kameraya uzaklıktan ve çözünürlükten bağımsız.
class MotionMetrics {
  const MotionMetrics({
    required this.motionRate,
    required this.stillness,
    required this.sampleSeconds,
  });

  /// Serbest evredeki ifade hareketi (rijit baş hareketi çıkarılmış).
  final double motionRate;

  /// Kilit evresindeki istemsiz mikro hareket.
  final double stillness;

  /// Toplam örnek süresi. Güven bunun üzerinden ölçülüyor.
  final double sampleSeconds;

  /// Ölçüm raporlanacak kadar sağlam mı?
  ///
  /// Eşik keyfi değil: kadrajı bulup kilidi doldurmak zaten ~2 sn sürüyor.
  /// Bunun altında kalan bir oturumda kullanıcı ya çerçeveye hiç girmedi ya
  /// da tespit kopuk kopuk çalıştı; iki durumda da ölçüm anlamsız.
  bool get confident => sampleSeconds >= kMinSampleSeconds;

  Map<String, double> toJson() => {
        'motionRate': _yuvarla(motionRate),
        'stillness': _yuvarla(stillness),
        'motionSeconds': _yuvarla(sampleSeconds),
      };

  static double _yuvarla(double d) => (d * 1000).round() / 1000;

  static const empty =
      MotionMetrics(motionRate: 0, stillness: 0, sampleSeconds: 0);
}

/// Güvenilir sayılması için gereken en az örnek süresi (saniye).
const double kMinSampleSeconds = 1.5;

/// Kare kare landmark'lardan hareket ölçen biriktirici.
///
/// Durum tutar ve tek bir çekim oturumu boyunca yaşar.
class MotionTracker {
  final List<double> _serbest = [];
  final List<double> _kilitli = [];

  List<Offset>? _oncekiNoktalar;
  int? _oncekiZamanMs;
  double _toplamSaniye = 0;

  /// Bir kareyi işler.
  ///
  /// [points] ölçüm noktaları (göz konturu HARİÇ — bkz. [expressionPoints]),
  /// [faceWidth] normalleştirme için, [locked] kilit evresinde miyiz.
  void addFrame({
    required List<Offset> points,
    required double faceWidth,
    required int timestampMs,
    required bool locked,
  }) {
    final onceki = _oncekiNoktalar;
    final oncekiZaman = _oncekiZamanMs;
    _oncekiNoktalar = points;
    _oncekiZamanMs = timestampMs;

    if (onceki == null || oncekiZaman == null) return;
    if (points.length != onceki.length || points.isEmpty) return;
    if (faceWidth < 1) return;

    final dt = (timestampMs - oncekiZaman) / 1000.0;
    // Çok kısa veya çok uzun aralık: kare atlanmış ya da saat sıçramış.
    // İkisinde de hız hesabı çöp üretir.
    if (dt <= 0.01 || dt > 0.5) return;

    // Rijit baş hareketi çıkarılır: kullanıcı başını çevirdiğinde TÜM
    // noktalar kayıyor ve bu ifade hareketi değil. Merkez kaymasını
    // düşürünce geriye yüzün kendi içindeki değişim kalıyor.
    final merkezKayma = _merkez(points) - _merkez(onceki);

    var toplam = 0.0;
    for (var i = 0; i < points.length; i++) {
      toplam += (points[i] - onceki[i] - merkezKayma).distance;
    }
    final hiz = (toplam / points.length) / faceWidth / dt;

    // Gerçekçi olmayan sıçramalar (tespit atlaması) atılır.
    if (hiz.isNaN || hiz.isInfinite || hiz > 5.0) return;

    _toplamSaniye += dt;
    (locked ? _kilitli : _serbest).add(hiz);
  }

  MotionMetrics get metrics => MotionMetrics(
        motionRate: _ortanca(_serbest),
        stillness: _ortanca(_kilitli),
        sampleSeconds: _toplamSaniye,
      );

  void reset() {
    _serbest.clear();
    _kilitli.clear();
    _oncekiNoktalar = null;
    _oncekiZamanMs = null;
    _toplamSaniye = 0;
  }

  static Offset _merkez(List<Offset> p) {
    var x = 0.0, y = 0.0;
    for (final o in p) {
      x += o.dx;
      y += o.dy;
    }
    return Offset(x / p.length, y / p.length);
  }

  /// Ortalama DEĞİL ortanca.
  ///
  /// Tek bir bozuk kare (tespit sıçraması) ortalamayı uçuruyor; ortanca
  /// bundan etkilenmiyor. Hareket ölçümünde aykırı değer kural, istisna değil.
  static double _ortanca(List<double> v) {
    if (v.isEmpty) return 0;
    final s = List<double>.from(v)..sort();
    final orta = s.length ~/ 2;
    return s.length.isOdd ? s[orta] : (s[orta - 1] + s[orta]) / 2;
  }
}

/// Hareket ölçümüne girecek nokta kümesi.
///
/// **Göz konturu bilerek dışarıda.** Göz kırpması landmark'ları çok büyük bir
/// mesafe oynatıyor ve ölçümü tamamen kırpma sıklığına indirgiyor; oysa
/// aranan şey ifadenin genel canlılığı. Kaş, ağız ve yüz ovali kalıyor:
/// ifade değişimini taşıyan asıl hatlar bunlar.
List<Offset> expressionPoints({
  required List<Offset> brows,
  required List<Offset> mouth,
  required List<Offset> oval,
}) =>
    [...brows, ...mouth, ...oval];

/// Ölçülen hıza karşılık gelen sıcak–soğuk eğilimi.
///
/// KALİBRASYON NOTU: eşikler ölçülmüş nüfus normları değil. Sabit durmaya
/// çalışan bir insanda mikro hareket ~0.02–0.05, serbest ifadede ~0.15–0.40
/// yüz genişliği/saniye civarında seyrediyor. Aradaki geniş boşluk bilerek
/// bırakıldı: arada kalan bir ölçüm için taraf seçmektense **hiçbir şey
/// söylememek** doğru.
const double kHeatFast = 0.18;
const double kHeatSlow = 0.06;

enum HeatLean { fast, slow, unclear }

HeatLean heatLean(MotionMetrics m) {
  if (!m.confident) return HeatLean.unclear;
  final hiz = math.max(m.motionRate, m.stillness);
  if (hiz >= kHeatFast) return HeatLean.fast;
  if (hiz > 0 && hiz <= kHeatSlow) return HeatLean.slow;
  return HeatLean.unclear;
}
