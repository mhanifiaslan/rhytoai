import 'dart:io';
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';

/// Günlük yorumun dışa paylaşılabilir görsel kartı.
///
/// Kategorinin en güçlü büyüme kanalı: sosyal graf gerektirmez, moderasyon
/// yükü sıfırdır (paylaşılan metni kullanıcı yazmaz, uygulama üretir) ve
/// paylaşan kişi uygulamayı kendi çevresine tanıtır.
///
/// **Gizlilik kuralı: ham doğum verisi karta GİRMEZ.** Kartta yalnızca burç,
/// tarih, yorumdan bir alıntı ve o günün ay evresi var. Doğum tarihi/saati/
/// yeri hassas bir üçlüdür; kullanıcı bunu paylaştığını fark etmeden
/// paylaşmamalı.
class ShareCard extends StatelessWidget {
  const ShareCard({
    super.key,
    required this.signName,
    required this.signGlyph,
    required this.reading,
    required this.dateLabel,
    this.moonEmoji,
    this.moonName,
  });

  final String signName;
  final String signGlyph;
  final String reading;
  final String dateLabel;
  final String? moonEmoji;
  final String? moonName;

  /// Instagram story oranı (9:16). Diğer uygulamalar bunu sorunsuz kırpar.
  static const double width = 1080;
  static const double height = 1920;

  /// Metin alanının genişliği ve yüksekliği (dolgu düşülmüş hâliyle).
  static const double _textWidth = width - 96 * 2;
  static const double _textHeight = 900;

  /// Yorumun sığdırılacağı yazı boyutu aralığı.
  static const double _maxFontSize = 52;
  static const double _minFontSize = 26;

  /// Gövde metninin stili. Ölçüm ve çizim AYNI stili kullanmak zorunda;
  /// aksi halde sığdığı hesaplanan metin ekranda taşar.
  static TextStyle bodyStyle(double size) =>
      RythoText.body(size, height: 1.5);

  /// Metin verilen boyutta alana sığıyor mu?
  ///
  /// [styleBuilder] enjekte edilebilir: uygulamada gerçek yazı tipi kullanılır,
  /// testte ağ erişimi olmadığı için yedek stil verilir. Sığdırma MANTIĞI
  /// yazı tipi kaynağından bağımsız olmalı.
  static bool fitsAt(
    String text,
    double fontSize, {
    double maxWidth = _textWidth,
    double maxHeight = _textHeight,
    TextStyle Function(double)? styleBuilder,
  }) {
    final painter = TextPainter(
      text: TextSpan(
          text: text, style: (styleBuilder ?? bodyStyle)(fontSize)),
      textDirection: TextDirection.ltr,
    )..layout(maxWidth: maxWidth);
    return painter.height <= maxHeight;
  }

  /// Yorumu **kesmeden** karta sığdıran yazı boyutunu bulur.
  ///
  /// Önceki yaklaşım metni kırpıyordu. Cümle sınırından kesmek yarım cümleyi
  /// önlüyordu ama asıl sorunu çözmüyordu: 90-130 kelimelik bir okumadan
  /// birkaç cümle göstermek, paylaşılan şeyin eksik olması demek. Okumayı
  /// bölmek yerine yazıyı küçültüyoruz — kart dışa açılan yüz, orada eksik
  /// bir metin uygulamanın kendisini eksik gösterir.
  ///
  /// İkili arama: en büyük sığan boyut bulunur. Ölçüm gerçek yazı tipiyle
  /// yapıldığı için tahmin değil.
  static double fittedFontSize(
    String text, {
    double maxWidth = _textWidth,
    double maxHeight = _textHeight,
    double maxSize = _maxFontSize,
    double minSize = _minFontSize,
    TextStyle Function(double)? styleBuilder,
  }) {
    if (text.trim().isEmpty) return maxSize;

    bool sigar(double boyut) => fitsAt(text, boyut,
        maxWidth: maxWidth, maxHeight: maxHeight, styleBuilder: styleBuilder);

    if (sigar(maxSize)) return maxSize;

    var alt = minSize;
    var ust = maxSize;
    // 0.5 punto çözünürlük gözle fark edilmez; 8 tur yeter.
    for (var i = 0; i < 8; i++) {
      final orta = (alt + ust) / 2;
      if (sigar(orta)) {
        alt = orta;
      } else {
        ust = orta;
      }
    }
    return alt;
  }

  /// En küçük boyutta bile sığmayan metin için son çare kırpma.
  ///
  /// Normal bir günlük yorumda (90-130 kelime) buraya HİÇ girilmez; bu yol
  /// yalnızca beklenmedik uzunluktaki bir metnin kartı taşırmasını engeller.
  /// Kırpma yine cümle sınırından yapılır.
  static String clampToSentence(String text, int maxChars) {
    final temiz = text.trim();
    if (temiz.length <= maxChars) return temiz;

    final kesit = temiz.substring(0, maxChars);
    var son = -1;
    for (final isaret in ['. ', '! ', '? ', '.\n']) {
      final i = kesit.lastIndexOf(isaret);
      if (i > son) son = i;
    }
    if (son > maxChars ~/ 3) return kesit.substring(0, son + 1).trim();

    final bosluk = kesit.lastIndexOf(' ');
    return '${kesit.substring(0, bosluk > 0 ? bosluk : maxChars).trim()}…';
  }

  /// Karta girecek metin: kural olarak **TAM okuma**.
  ///
  /// Yalnızca en küçük yazı boyutunda bile sığmayan olağandışı uzunlukta bir
  /// metin kırpılır. Normal bir günlük yorumda buraya hiç girilmez.
  static String bodyText(String reading,
      {TextStyle Function(double)? styleBuilder}) {
    final temiz = reading.trim();
    if (temiz.isEmpty) return temiz;

    if (fitsAt(temiz, _minFontSize, styleBuilder: styleBuilder)) return temiz;

    // Sığan en uzun kırpmayı ikili aramayla bul. Orantı tahmini (yükseklik
    // oranı × karakter sayısı) uzun metinlerde şişiyor ve kart yine taşıyordu.
    var alt = 0;
    var ust = temiz.length;
    while (alt < ust) {
      final orta = (alt + ust + 1) ~/ 2;
      if (fitsAt(clampToSentence(temiz, orta), _minFontSize,
          styleBuilder: styleBuilder)) {
        alt = orta;
      } else {
        ust = orta - 1;
      }
    }
    return clampToSentence(temiz, alt);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);

    return SizedBox(
      width: width,
      height: height,
      child: DecoratedBox(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFF13091F), Color(0xFF241038), Color(0xFF0B0713)],
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(96, 150, 96, 110),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(dateLabel,
                  style: RythoText.mono(34, color: RythoColors.parchmentDim)),
              const SizedBox(height: 56),
              Row(children: [
                Text(signGlyph,
                    style: const TextStyle(
                        fontSize: 116, color: RythoColors.goldBright)),
                const SizedBox(width: 28),
                Expanded(
                  child: Text(signName.toUpperCase(),
                      style: RythoText.display(84)),
                ),
              ]),
              const SizedBox(height: 64),
              // Okuma KESİLMEZ: sığmıyorsa yazı küçülür. Sabit bir boyutla
              // kesmek, paylaşılan şeyin eksik olması demekti.
              Expanded(
                child: Builder(builder: (_) {
                  final metin = bodyText(reading);
                  // Çizim, ölçümle AYNI stil üreticisini kullanır; ayrışırsa
                  // sığdığı hesaplanan metin kartta taşar.
                  return Text(metin, style: bodyStyle(fittedFontSize(metin)));
                }),
              ),
              if (moonName != null) ...[
                Text('${moonEmoji ?? ''} $moonName'.trim(),
                    style: RythoText.body(36,
                        color: RythoColors.parchmentDim)),
                const SizedBox(height: 40),
              ],
              // Marka satırı: paylaşan kişi uygulamayı tanıtıyor. Ayırt edici
              // iddia da burada — "gerçek gökyüzü hesabıyla".
              Row(children: [
                Text('RYTHO',
                    style: RythoText.label(44, color: RythoColors.gold)),
                const SizedBox(width: 20),
                Expanded(
                  child: Text(l10n.shareCardTagline,
                      style: RythoText.body(32,
                          color: RythoColors.parchmentDim)),
                ),
              ]),
            ],
          ),
        ),
      ),
    );
  }
}

/// Kartı görüntüye çevirip paylaşım sayfasını açar.
///
/// Kart ekranda gösterilmiyor; ekran dışında çizilip PNG'ye alınıyor.
/// Kullanıcıyı önce bir önizleme ekranına götürmek fazladan adım olurdu —
/// paylaşım sayfası zaten önizleme gösteriyor.
Future<bool> shareReadingCard(
  BuildContext context, {
  required String signName,
  required String signGlyph,
  required String reading,
  required String dateLabel,
  String? moonEmoji,
  String? moonName,
}) async {
  final l10n = AppLocalizations.of(context);
  final mediaQuery = MediaQuery.of(context);
  final locale = Localizations.localeOf(context);

  try {
    final bayt = await _renderCard(
      ShareCard(
        signName: signName,
        signGlyph: signGlyph,
        reading: reading,
        dateLabel: dateLabel,
        moonEmoji: moonEmoji,
        moonName: moonName,
      ),
      mediaQuery: mediaQuery,
      locale: locale,
    );

    final dizin = await getTemporaryDirectory();
    final dosya = File('${dizin.path}/rytho-${DateTime.now()
        .millisecondsSinceEpoch}.png');
    await dosya.writeAsBytes(bayt);

    await SharePlus.instance.share(
      ShareParams(files: [XFile(dosya.path)], text: 'RYTHO'),
    );
    return true;
  } catch (e) {
    debugPrint('Paylaşım kartı oluşturulamadı: $e');
    if (context.mounted) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(l10n.shareFailed)));
    }
    return false;
  }
}

/// Widget'ı ekrana bağlamadan PNG'ye çevirir.
///
/// `RepaintBoundary`'yi ekranda gösterip yakalamak, kartı kullanıcıya bir an
/// için göstermek demek olurdu. Bunun yerine ayrı bir render ağacı kurulup
/// tek karede çiziliyor.
Future<Uint8List> _renderCard(
  Widget card, {
  required MediaQueryData mediaQuery,
  required Locale locale,
}) async {
  final repaintBoundary = RenderRepaintBoundary();
  final view = WidgetsBinding.instance.platformDispatcher.views.first;

  final renderView = RenderView(
    view: view,
    child: RenderPositionedBox(
      alignment: Alignment.center,
      child: repaintBoundary,
    ),
    configuration: ViewConfiguration(
      logicalConstraints: BoxConstraints.tight(
          const Size(ShareCard.width, ShareCard.height)),
      devicePixelRatio: 1.0,
    ),
  );

  final pipelineOwner = PipelineOwner()..rootNode = renderView;
  renderView.prepareInitialFrame();

  final buildOwner = BuildOwner(focusManager: FocusManager());
  final element = RenderObjectToWidgetAdapter<RenderBox>(
    container: repaintBoundary,
    child: Directionality(
      textDirection: TextDirection.ltr,
      child: MediaQuery(
        data: mediaQuery,
        child: Localizations(
          locale: locale,
          delegates: AppLocalizations.localizationsDelegates.toList(),
          child: card,
        ),
      ),
    ),
  ).attachToRenderTree(buildOwner);

  buildOwner
    ..buildScope(element)
    ..finalizeTree();
  pipelineOwner
    ..flushLayout()
    ..flushCompositingBits()
    ..flushPaint();

  final image = await repaintBoundary.toImage(pixelRatio: 1.0);
  final data = await image.toByteData(format: ui.ImageByteFormat.png);
  if (data == null) throw StateError('Kart PNG olarak alınamadı.');
  return data.buffer.asUint8List();
}
