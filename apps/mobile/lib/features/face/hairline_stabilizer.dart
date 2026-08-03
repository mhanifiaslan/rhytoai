/// Saç çizgisi ölçümünü tek kareye bırakmayan kararlılık katmanı.
///
/// ## Neden var
///
/// Cihazda arka arkaya alınan iki ölçüm, aynı yüzde şunu verdi:
///
///     üst 0,31   orta 0,33   alt 0,37
///     üst 0,20   orta 0,39   alt 0,41
///
/// Üst bölge üçte bir düştü. Sebep görünür: saç öne düştüğü karede model alın
/// pikselini "saç" sayıyor ve sınır aşağı kayıyor.
///
/// Bu kozmetik bir dalgalanma değil, ürünün **söylediği şeyi** değiştiriyor.
/// Sunucu "dar alın" demek için ortalamadan 0,045 fark istiyor: 0,31'de fark
/// 0,027 (iddia YOK), 0,20'de 0,133 (iddia VAR). Yani ardışık iki tarama
/// kullanıcıya birbiriyle çelişen iki şey söylerdi.
///
/// Ürünün ilkesi "gerçek veriler ne diyorsa onu söylemek". Kararsız bir ölçüm
/// gerçek veri değil.
///
/// ## Nasıl
///
/// Önizleme boyunca biriken örneklerin **medyanı** alınıyor — ortalama değil,
/// çünkü sorun tam olarak tek tük uç değerler ve ortalama onlardan etkilenir.
/// Medyan beş örnekte iki uç değeri sindirir.
///
/// Dağılım geniş kalırsa ölçüm **yapılmamış sayılıyor**. Kararsız bir sayıyı
/// ortalamasını alıp sunmak, bilmediğini biliyormuş gibi göstermek olurdu;
/// bu projede daha önce tam olarak bu tür sessiz kusurlar pahalıya patladı.
library;

import 'dart:math' as math;

/// Örneklerin ölçü birimi: alın yüksekliğinin **kaş-çene** mesafesine oranı.
///
/// Ham piksel değil, çünkü yüz kameraya yaklaşıp uzaklaştıkça piksel değişir
/// ama oran değişmez. Kararlılığı ölçmek istediğimiz şey yüzün geometrisi,
/// kullanıcının ne kadar yaklaştığı değil.
class HairlineStabilizer {
  /// Kaç örnek tutulacak. Önizlemede 700 ms'de bir ölçülüyor, yani beş örnek
  /// yaklaşık 3,5 saniyelik pencere — kullanıcının "sabit dur" süresi.
  static const int windowSize = 5;

  /// Karar için gereken en az örnek.
  ///
  /// Üç örnekten azında medyanın uç değer direnci yok; iki örnekte medyan
  /// zaten ortalamaya dönüşür.
  static const int minSamples = 3;

  /// Kabul edilen en geniş dağılım (kaş-çene birimi).
  ///
  /// Yukarıdaki gerçek olayda dağılım 0,20 idi ve `upperThird` cinsinden
  /// 0,11'lik bir sapmaya karşılık geliyordu — sunucunun 0,045'lik eşiğinin
  /// iki katından fazla. 0,10 sınırı, `upperThird`'de kabaca ±0,03 demek:
  /// eşiğin altında kalır, yani iddia kararsızlıktan dolayı yön değiştiremez.
  static const double maxSpread = 0.10;

  final List<double> _ornekler = <double>[];

  /// Ölçülen alın yüksekliğini ekler.
  ///
  /// [browY] ve [chinY] görüntü uzayında; [hairlineY] onların üstünde.
  /// Geçersiz geometri (çene kaşın üstünde, saç çizgisi kaşın altında)
  /// **sessizce yutulmuyor** — eklenmiyor ve `false` dönüyor.
  bool add({
    required double hairlineY,
    required double browY,
    required double chinY,
  }) {
    final taban = chinY - browY;
    if (taban <= 0) return false;
    final oran = (browY - hairlineY) / taban;
    if (oran <= 0 || oran > 2) return false;

    _ornekler.add(oran);
    if (_ornekler.length > windowSize) _ornekler.removeAt(0);
    return true;
  }

  void clear() => _ornekler.clear();

  int get sampleCount => _ornekler.length;

  /// Örneklerin medyanı; yeterli örnek yoksa `null`.
  double? get median {
    if (_ornekler.length < minSamples) return null;
    final sirali = [..._ornekler]..sort();
    final orta = sirali.length ~/ 2;
    return sirali.length.isOdd
        ? sirali[orta]
        : (sirali[orta - 1] + sirali[orta]) / 2;
  }

  /// En büyük ile en küçük örnek arası fark; yeterli örnek yoksa `null`.
  double? get spread {
    if (_ornekler.length < minSamples) return null;
    return _ornekler.reduce(math.max) - _ornekler.reduce(math.min);
  }

  /// Ölçüm güvenilir mi: yeterli örnek var ve dağılım dar.
  bool get stable {
    final s = spread;
    return s != null && s <= maxSpread;
  }

  /// Kararlı medyandan saç çizgisinin görüntü uzayındaki konumu.
  ///
  /// Kararsızsa `null`: ölçemediğimizde ölçmüş gibi yapmıyoruz.
  double? hairlineFor({required double browY, required double chinY}) {
    if (!stable) return null;
    final m = median;
    if (m == null) return null;
    return browY - m * (chinY - browY);
  }

  /// Teşhis satırı — cihazda görünür.
  String get debugLabel {
    final s = spread;
    if (s == null) return 'örnek ${_ornekler.length}/$minSamples';
    return 'örnek ${_ornekler.length} · yayılım ${s.toStringAsFixed(3)}'
        '${stable ? '' : ' KARARSIZ'}';
  }
}
