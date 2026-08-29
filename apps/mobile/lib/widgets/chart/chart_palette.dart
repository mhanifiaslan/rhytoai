/// Çark paleti (HI-turu HA5) — koyu zemin + konvansiyona demirli renkler.
///
/// Profesyonel yazılım konvansiyonu: SERT = kırmızı ailesi, YUMUŞAK =
/// mavi/yeşil, kavuşum nötr/altın, minörler gri KESİK. Saf #FF0000 koyu
/// morda titreşir; bu palet parlaklığı yükseltip doymayı düşürür ve
/// mevcut tema tonlarını kullanır. Eski çarkın kusuru buradan da
/// görülür: magenta AYNI ANDA kare + karşıt + retro demekti — üç anlam
/// tek renk. Renk artık tek anlam taşır; sert/yumuşak/minör ayrımı AYRICA
/// çizgi stiliyle (düz/kesik) verilir — renk körlüğünde de okunur.
library;

import 'dart:ui';

import '../../theme/rytho_theme.dart';

/// Açı türü → renk. Anahtarlar sunucuyla aynı (küçük-harf, HA1).
const Map<String, Color> kAspectColors = {
  'conjunction': Color(0xFFFFC24B), // altın — nötr/vurgulu
  'opposition': Color(0xFFFF5C7A),  // kırmızı okunur, koyuda yaşar
  'square': Color(0xFFFF8A5C),      // turuncu-kırmızı, karşıttan ayrışır
  'trine': Color(0xFF5AC8FA),       // serin mavi
  'sextile': Color(0xFF7FD8A4),     // celadon — "kolay" okunur
};

/// Minör açılar (yarım-altmışlık, yarım-kare, quincunx, sesqui, quintile).
const Color kMinorAspectColor = Color(0xFF8E8EA8);

/// Element tonları — burç bandının %12 alfa zemini (4 ton; 12'li
/// signColors bilerek DEĞİL: 12 renkli bant gökkuşağına dönüyor).
const List<Color> kElementTints = [
  Color(0xFFFF6B81), // ateş  (Koç/Aslan/Yay)
  Color(0xFFFFC24B), // toprak (Boğa/Başak/Oğlak)
  Color(0xFF5AC8FA), // hava  (İkizler/Terazi/Kova)
  Color(0xFF7FD8A4), // su    (Yengeç/Akrep/Balık)
];

Color elementTintFor(int signIndex) => kElementTints[signIndex % 4];

/// Halka kimliği: iç doğal (parşömen), dış transit (lila), partner
/// (altın-parlak) — bi-wheel lejantıyla aynı aile.
const Color kInnerGlyphColor = RythoColors.parchment;
const Color kOuterTransitColor = RythoColors.lilac;
const Color kOuterPartnerColor = Color(0xFFFFD98A);

/// Yapı çizgileri.
const Color kRingLine = Color(0x387B62B8);      // lila ~%22
const Color kTickColor = Color(0x66B79CFF);     // cetvel işaretleri
const Color kAxisColor = Color(0xD9B79CFF);     // AC/MC eksenleri
const Color kGlyphDisc = Color(0xE614091E);     // glif altı mürekkep diski

/// Açı çizgisi görünümü: orb daraldıkça kalınlaşır ve belirginleşir
/// (Astrodienst konvansiyonu). [selected] izole modunda vurgulanan uç.
({double width, double alpha}) aspectStroke(double orb, double maxOrb,
    {bool dimmed = false, bool selected = false}) {
  final sikilik = (1 - (orb / maxOrb)).clamp(0.0, 1.0);
  var width = 0.6 + 1.6 * sikilik;
  var alpha = 0.25 + 0.55 * sikilik;
  if (selected) {
    width += 0.6;
    alpha = alpha < 0.55 ? 0.75 : alpha + 0.2;
  }
  if (dimmed) alpha *= 0.25;
  return (width: width, alpha: alpha.clamp(0.12, 1.0));
}

Color aspectColor(String kind) =>
    kAspectColors[kind] ?? kMinorAspectColor;
