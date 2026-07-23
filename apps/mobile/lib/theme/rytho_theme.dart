import 'package:flutter/cupertino.dart' show CupertinoPageTransitionsBuilder;
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// "Gök Atlası" tasarım sistemi — bkz. docs/design/design-system.md
/// Eski gökyüzü atlası / usturlap gravürü estetiği: mürekkep, parşömen, altın.
abstract final class RythoColors {
  static const ink = Color(0xFF0B1026); // gece mürekkebi zemin
  static const inkLight = Color(0xFF141B33); // kart yüzeyi
  static const inkLighter = Color(0xFF1E2742); // yükseltilmiş yüzey
  static const parchment = Color(0xFFEDE4CF); // ana metin
  static const parchmentDim = Color(0xFFB7AE99); // ikincil metin
  static const gold = Color(0xFFC9A227); // vurgu
  static const goldBright = Color(0xFFE8C55A); // basılı/parlak vurgu
  static const copper = Color(0xFFA66A3E); // ikincil vurgu / retro
  static const celadon = Color(0xFF7FA98F); // olumlu
  static const madder = Color(0xFFB4524B); // hata (kök boyası kızılı)
  static const line = Color(0xFF2C3552); // gravür çizgileri
}

abstract final class RythoText {
  /// Ekran ve bölüm başlıkları — eski kitap kapağı serifi.
  static TextStyle display(double size,
          {Color color = RythoColors.parchment, FontWeight w = FontWeight.w600}) =>
      GoogleFonts.cormorantGaramond(
          fontSize: size, fontWeight: w, color: color, letterSpacing: 0.5);

  /// Gövde metni.
  static TextStyle body(double size,
          {Color color = RythoColors.parchment, FontWeight w = FontWeight.w400, double? height}) =>
      GoogleFonts.spectral(fontSize: size, fontWeight: w, color: color, height: height ?? 1.5);

  /// Astronomik veri: dereceler, koordinatlar, saatler — daima mono.
  static TextStyle mono(double size,
          {Color color = RythoColors.gold, FontWeight w = FontWeight.w400}) =>
      GoogleFonts.jetBrainsMono(
          fontSize: size,
          fontWeight: w,
          color: color,
          fontFeatures: const [FontFeature.tabularFigures()]);

  /// Buton / kadran etiketi: büyük harf, geniş aralık.
  static TextStyle label(double size, {Color color = RythoColors.parchment}) =>
      GoogleFonts.spectral(
          fontSize: size, fontWeight: FontWeight.w500, color: color, letterSpacing: 1.4);
}

ThemeData buildRythoTheme() {
  final base = ThemeData.dark(useMaterial3: true);
  return base.copyWith(
    scaffoldBackgroundColor: RythoColors.ink,
    colorScheme: const ColorScheme.dark(
      primary: RythoColors.gold,
      secondary: RythoColors.copper,
      surface: RythoColors.inkLight,
      error: RythoColors.madder,
      onPrimary: RythoColors.ink,
      onSurface: RythoColors.parchment,
    ),
    appBarTheme: AppBarTheme(
      backgroundColor: RythoColors.ink,
      elevation: 0,
      centerTitle: true,
      titleTextStyle: RythoText.display(24),
      iconTheme: const IconThemeData(color: RythoColors.gold, size: 22),
    ),
    dividerTheme: const DividerThemeData(color: RythoColors.line, thickness: 1),
    textSelectionTheme: const TextSelectionThemeData(
      cursorColor: RythoColors.gold,
      selectionColor: Color(0x33C9A227),
      selectionHandleColor: RythoColors.gold,
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: RythoColors.inkLighter,
      hintStyle: RythoText.body(15, color: RythoColors.parchmentDim),
      labelStyle: RythoText.label(13, color: RythoColors.parchmentDim),
      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(4),
        borderSide: const BorderSide(color: RythoColors.line),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(4),
        borderSide: const BorderSide(color: RythoColors.line),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(4),
        borderSide: const BorderSide(color: RythoColors.gold),
      ),
    ),
    snackBarTheme: SnackBarThemeData(
      backgroundColor: RythoColors.inkLighter,
      contentTextStyle: RythoText.body(14),
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(4),
        side: const BorderSide(color: RythoColors.line),
      ),
    ),
    pageTransitionsTheme: const PageTransitionsTheme(builders: {
      TargetPlatform.android: FadeUpwardsPageTransitionsBuilder(),
      TargetPlatform.iOS: CupertinoPageTransitionsBuilder(),
    }),
  );
}
