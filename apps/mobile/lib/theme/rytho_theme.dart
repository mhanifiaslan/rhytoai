import 'package:flutter/cupertino.dart' show CupertinoPageTransitionsBuilder;
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// "Mor Nebula" tasarım sistemi (v3) — bkz. docs/design/design-system.md
/// Koyu siyah-mor uzay zemini, mor→magenta degrade vurgular, yumuşak
/// yuvarlak koyu kartlar. Eski token adları ekran dosyaları kırılmasın
/// diye korunur; değerler tamamen v3'tür.
abstract final class RythoColors {
  // --- Zemin ---
  static const ink = Color(0xFF0B0710); // uzay siyahı (degrade üst ucu)
  static const inkDeep = Color(0xFF14091E); // mor derinlik (degrade alt ucu)
  static const inkLight = Color(0xFF1C1326); // kart yüzeyi
  static const inkLighter = Color(0xFF271A36); // yükseltilmiş yüzey / giriş alanı

  // --- Metin ---
  static const parchment = Color(0xFFF4EFFA); // ana metin (beyaz-lila)
  static const parchmentDim = Color(0xFFA99EC2); // ikincil metin

  // --- Vurgular ---
  static const violet = Color(0xFF7B2FF7); // birincil degrade başlangıcı
  static const purple = Color(0xFFB02EFF); // birincil degrade ortası
  static const magenta = Color(0xFFE64ACF); // birincil degrade ucu
  static const lilac = Color(0xFFB79CFF); // ikincil vurgu (çizgi/ikon)
  static const gold = Color(0xFFFFC24B); // ✨ yıldız/puan vurgusu
  static const goldBright = Color(0xFFFFD98A); // parlak yıldız vurgusu
  static const copper = Color(0xFFE64ACF); // eski "retro" vurgusu → magenta
  static const celadon = Color(0xFF7FD8A4); // olumlu
  static const madder = Color(0xFFFF6B81); // hata
  static const line = Color(0xFF2C1F40); // ayraç çizgileri

  // --- Kart/yüzey katmanı ---
  /// Kart dolgusu: koyu mor, hafif saydam.
  static const glassFill = Color(0xE61C1326);
  /// Kart üst kenar ışığı.
  static const glassEdge = Color(0x26B79CFF);
  /// Kart konturu: %6 beyaz.
  static const glassStroke = Color(0x0FFFFFFF);
  /// Mor glow (aktif öğeler, CTA).
  static const goldGlow = Color(0x557B2FF7);
  /// Magenta glow (merkez AI butonu).
  static const magentaGlow = Color(0x66E64ACF);

  /// Birincil degrade: CTA butonları, promo banner, aktif öğeler.
  static const primaryGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [violet, purple, magenta],
  );

  /// Zemin degradesi (üstten alta).
  static const backgroundGradient = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [ink, inkDeep],
  );

  /// 12 burcun çip renkleri (Koç→Balık) — rozetlerdeki degrade daireler için.
  static const signColors = [
    Color(0xFFFF6B4A), // Koç — turuncu-kızıl
    Color(0xFF63C77C), // Boğa — yeşil
    Color(0xFFFFC24B), // İkizler — sarı
    Color(0xFF5AC8FA), // Yengeç — açık mavi
    Color(0xFFFF9F43), // Aslan — altın-turuncu
    Color(0xFFB79CFF), // Başak — lila
    Color(0xFFFF7EB3), // Terazi — pembe
    Color(0xFF9B59F6), // Akrep — mor
    Color(0xFFFF8A5C), // Yay — mercan
    Color(0xFF8E8EA8), // Oğlak — gri-mor
    Color(0xFF4ACFE6), // Kova — turkuaz
    Color(0xFF6C8CFF), // Balık — mavi-mor
  ];
}

abstract final class RythoText {
  /// Ekran ve bölüm başlıkları — modern geometrik (Sora).
  static TextStyle display(double size,
          {Color color = RythoColors.parchment, FontWeight w = FontWeight.w700}) =>
      GoogleFonts.sora(
          fontSize: size, fontWeight: w, color: color, letterSpacing: -0.3);

  /// Gövde metni (Manrope).
  static TextStyle body(double size,
          {Color color = RythoColors.parchment, FontWeight w = FontWeight.w400, double? height}) =>
      GoogleFonts.manrope(
          fontSize: size, fontWeight: w, color: color, height: height ?? 1.55);

  /// Astronomik veri: dereceler, koordinatlar, saatler — daima mono.
  static TextStyle mono(double size,
          {Color color = RythoColors.lilac, FontWeight w = FontWeight.w400}) =>
      GoogleFonts.jetBrainsMono(
          fontSize: size,
          fontWeight: w,
          color: color,
          fontFeatures: const [FontFeature.tabularFigures()]);

  /// Buton / etiket: yarı kalın, hafif aralıklı.
  static TextStyle label(double size, {Color color = RythoColors.parchment}) =>
      GoogleFonts.manrope(
          fontSize: size, fontWeight: FontWeight.w700, color: color, letterSpacing: 0.8);
}

ThemeData buildRythoTheme() {
  final base = ThemeData.dark(useMaterial3: true);
  return base.copyWith(
    scaffoldBackgroundColor: RythoColors.ink,
    colorScheme: const ColorScheme.dark(
      primary: RythoColors.purple,
      secondary: RythoColors.magenta,
      surface: RythoColors.inkLight,
      error: RythoColors.madder,
      onPrimary: Colors.white,
      onSurface: RythoColors.parchment,
    ),
    appBarTheme: AppBarTheme(
      backgroundColor: Colors.transparent,
      elevation: 0,
      centerTitle: true,
      titleTextStyle: RythoText.display(19, w: FontWeight.w600),
      iconTheme: const IconThemeData(color: RythoColors.lilac, size: 22),
    ),
    dividerTheme: const DividerThemeData(color: RythoColors.line, thickness: 1),
    textSelectionTheme: const TextSelectionThemeData(
      cursorColor: RythoColors.purple,
      selectionColor: Color(0x338B4DF7),
      selectionHandleColor: RythoColors.purple,
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: RythoColors.inkLighter,
      hintStyle: RythoText.body(15, color: RythoColors.parchmentDim),
      labelStyle: RythoText.label(13, color: RythoColors.parchmentDim),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: RythoColors.glassStroke),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: RythoColors.glassStroke),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: RythoColors.purple),
      ),
    ),
    snackBarTheme: SnackBarThemeData(
      backgroundColor: RythoColors.inkLighter,
      contentTextStyle: RythoText.body(14),
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: RythoColors.glassStroke),
      ),
    ),
    pageTransitionsTheme: const PageTransitionsTheme(builders: {
      TargetPlatform.android: FadeForwardsPageTransitionsBuilder(),
      TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
    }),
  );
}
