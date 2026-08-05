/// Tasarım token'ları — boşluk, yarıçap, süre ve tip rolleri.
///
/// ## Neden var
///
/// Bu dosyadan önce hiçbiri sabit değildi ve sonuç ölçülebilirdi:
///
/// * 40'tan fazla farklı font boyutu; 12.5, 13.5, 14.5, 9.5 gibi yarım punto
///   varyasyonlar her ekranda yeniden uydurulmuştu.
/// * Üç ayrı "kart" yarıçapı dolaşıyordu: `GlassPanel` 22, `_OracleCard` 20,
///   `PromoBanner` 24. Aynı ekranda yan yana duruyorlardı.
/// * `SizedBox` boşlukları 2'den 72'ye kadar 20 farklı değer alıyordu.
///
/// Tutarsızlık burada bir zevk meselesi değil: kullanıcı "dağınık, insanı
/// yoran bir yapı" diye tarif etti. Göz, hizalanmayan kenarları ve tutmayan
/// ritmi bilinçaltında gürültü olarak okuyor.
///
/// ## Nasıl kullanılır
///
/// Yeni kod **çıplak sayı yazmaz**. Var olan ekranlar dokunuldukça geçirilir;
/// hepsini tek seferde değiştirmek 40'tan fazla çağrı yerini aynı anda riske
/// atmak olurdu.
library;

import 'package:flutter/widgets.dart';

import 'rytho_theme.dart';

/// Boşluk ölçeği. Dörtün katları — ara değer yok.
abstract final class RythoSpace {
  /// Sıkı gruplama: bir etiketle değeri arası.
  static const xs = 4.0;

  /// İlişkili öğeler arası.
  static const sm = 8.0;

  /// Kart içi öğeler arası — en sık kullanılan.
  static const md = 12.0;

  /// Kart içi kenar boşluğu ve ekran yatay kenarı.
  static const lg = 16.0;

  /// Bölümler arası.
  static const xl = 24.0;

  /// Büyük ayrım — ekran üstü/altı nefes payı.
  static const xxl = 32.0;

  /// Alt gezinme çubuğunun kapladığı yer. Liste sonlarına bu eklenir,
  /// yoksa son kart dock'un altında kalıyor.
  static const dockClearance = 130.0;
}

/// Köşe yarıçapları.
abstract final class RythoRadius {
  /// Küçük öğeler: çip, rozet, küçük buton.
  static const sm = 12.0;

  /// Giriş alanları, ikincil yüzeyler.
  static const md = 16.0;

  /// **Kartlar.** Tek kart yarıçapı budur; `GlassPanel` varsayılanı.
  static const card = 22.0;

  /// Hap biçimi (tam yuvarlak uçlar).
  static const pill = 999.0;
}

/// Animasyon süreleri.
///
/// Kod tabanında 120/260/280/320/360/380/800/1600 ms serbestçe dolaşıyordu.
/// Aynı ekranda 320 ve 380 ms yan yana çalışınca göz senkronsuzluk görüyor.
abstract final class RythoMotion {
  /// Dokunma tepkisi, çip seçimi — kullanıcı beklemesin.
  static const fast = Duration(milliseconds: 160);

  /// Standart geçiş: kart açılması, durum değişimi.
  static const base = Duration(milliseconds: 260);

  /// Giriş animasyonu, sayfa açılışı.
  static const slow = Duration(milliseconds: 380);

  /// Tören anları: reveal, kutlama — "özel bir şey oluyor" süresi.
  static const slower = Duration(milliseconds: 600);

  /// Listede kademeli giriş için öğe başına gecikme.
  static const stagger = Duration(milliseconds: 70);

  // Eğriler (R12-A0): yeni eğri icat edilmedi — kod tabanında fiilen
  // kazanmış üç eğri adlandırıldı. Yeni kod eğriyi buradan alır.

  /// Giriş/kayma: fadeIn + slide zincirlerinin eğrisi.
  static const enter = Curves.easeOutCubic;

  /// Rozet/balon/kutlama: hafif taşmalı canlılık.
  static const pop = Curves.easeOutBack;

  /// Dokunma tepkisi: basma/bırakma.
  static const settle = Curves.easeOut;
}

/// Tip **rolleri** — boyut değil, iş.
///
/// `RythoText.body(13.5)` yazmak yerine `RythoType.body` yazılır. Boyut bir
/// gün değişirse tek yerden değişir; daha önemlisi, çağrı yerinde "bu metin
/// ne işe yarıyor" sorusunun cevabı görünür olur.
abstract final class RythoType {
  // --- Başlıklar (Sora) ---

  /// Ekranın tek büyük başlığı.
  static TextStyle get screenTitle => RythoText.display(22);

  /// Bölüm başlığı — "Bugün senin için", "Şu an".
  static TextStyle get sectionTitle => RythoText.display(19);

  /// Kart başlığı.
  static TextStyle get cardTitle => RythoText.display(16);

  // --- Gövde (Manrope) ---

  /// Okuma metni — uzun paragraflar. Satır yüksekliği okunurluk için açık.
  static TextStyle get reading => RythoText.body(15, height: 1.65);

  /// Standart gövde.
  static TextStyle get body =>
      RythoText.body(14, height: 1.55);

  /// İkincil gövde — açıklama, alt metin.
  static TextStyle get bodyDim =>
      RythoText.body(13, color: RythoColors.parchmentDim, height: 1.5);

  /// Küçük yardımcı metin.
  static TextStyle get caption =>
      RythoText.body(12, color: RythoColors.parchmentDim, height: 1.45);

  // --- Etiket (Manrope, aralıklı) ---

  /// Buton metni.
  static TextStyle get button => RythoText.label(13);

  /// Kart üstü küçük etiket, bölüm rozeti.
  static TextStyle get label =>
      RythoText.label(11, color: RythoColors.parchmentDim);

  // --- Veri (JetBrains Mono) ---

  /// Derece, saat, koordinat.
  static TextStyle get data => RythoText.mono(12);

  /// Küçük veri.
  static TextStyle get dataSmall =>
      RythoText.mono(11, color: RythoColors.parchmentDim);
}
