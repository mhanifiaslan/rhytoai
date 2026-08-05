/// Uzun üretilmiş metni akıştan çıkaran kart ve onun okuma sayfası.
///
/// ## Neden var
///
/// Kullanıcı uygulamayı "insanı yoran, dağınık" diye tarif etti ve sebebi
/// ölçüldü: Gökyüzü ekranı ~1500 px, Atlas ~2000 px uzunluğundaydı. Bu
/// uzunluğun büyük kısmı **akışın içine dökülmüş sınırsız AI metniydi** —
/// burç yorumu, kişisel okuma, tam natal rapor.
///
/// Bunlar akışa ait değil. Bir bakışta görülmesi gereken şeyle üç dakika
/// okunacak şey aynı seviyede duramaz; kullanıcı "bugün ne var" diye bakarken
/// üç paragrafın içinden geçmek zorunda kalıyordu.
///
/// Kural: **üretilen hiçbir metin akışta 3 satırdan uzun duramaz.** Uzun olan
/// [ReadingCard] içinde önizlenir, [ReadingScreen] içinde okunur.
library;

import 'package:flutter/material.dart';

import '../theme/rytho_theme.dart';
import '../theme/rytho_tokens.dart';
import 'cosmic_scaffold.dart';
import 'fade_through_route.dart';
import 'glass.dart';
import 'motion.dart';

/// Uzun metnin akıştaki temsilcisi: başlık + üç satır + "devamı".
class ReadingCard extends StatelessWidget {
  const ReadingCard({
    super.key,
    required this.title,
    required this.body,
    this.label,
    this.glow = false,
    this.trailing,
    this.onOpen,
  });

  /// Okuma sayfasının başlığı.
  final String title;

  /// Tam metin. Kartta ilk üç satırı görünür.
  final String body;

  /// Kartın üstündeki küçük etiket — ör. "☀️ Aslan · 🌙 Balık".
  final String? label;

  final bool glow;

  /// Okuma sayfasının altına eklenecek ek içerik (ör. paylaş butonu).
  final Widget? trailing;

  /// Varsayılan davranışın yerine geçer. Verilmezse [ReadingScreen] açılır.
  final VoidCallback? onOpen;

  @override
  Widget build(BuildContext context) {
    return GlassPanel(
      label: label,
      glow: glow,
      onTap: onOpen ?? () => open(context),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: RythoType.cardTitle),
          const SizedBox(height: RythoSpace.sm),
          Text(
            body,
            style: RythoType.body,
            // ÜÇ SATIR — bu sayı kartın varlık sebebi. Artırmak, çözdüğümüz
            // sorunu geri getirir.
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: RythoSpace.md),
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              Text(_devami(context), style: RythoType.button),
              const SizedBox(width: RythoSpace.xs),
              const Icon(Icons.arrow_forward_rounded,
                  size: 15, color: RythoColors.parchment),
            ],
          ),
        ],
      ),
    );
  }

  void open(BuildContext context) {
    // Fade-through (R12-B2): kart → sayfa geçişini içerik açılışı taşır.
    Navigator.of(context).push(FadeThroughRoute(
      builder: (_) => ReadingScreen(
        title: title,
        body: body,
        label: label,
        trailing: trailing,
      ),
    ));
  }

  static String _devami(BuildContext context) =>
      Localizations.localeOf(context).languageCode == 'en'
          ? 'Read'
          : 'Okumaya devam et';
}

/// Uzun metnin kendi sayfası.
///
/// Tek işi metni okutmak: kenar boşluğu geniş, satır yüksekliği açık, başka
/// hiçbir şey yok. Akışta kaybolan okunurluk burada geri geliyor.
class ReadingScreen extends StatelessWidget {
  const ReadingScreen({
    super.key,
    required this.title,
    required this.body,
    this.label,
    this.trailing,
  });

  final String title;
  final String body;
  final String? label;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    // Paragraf canlanması (R12-B2): uygulamanın en uzun ve en değerli metni
    // eskiden tek karede basılıyordu. İlk altı paragraf kademeli belirir;
    // gerisi ANINDA görünür — ekran dışına stagger borcu bindirilmez,
    // hızlı kaydıran okur bekletilmez.
    final paragraflar = body.split('\n\n');
    return CosmicScaffold(
      appBar: AppBar(title: Text(title)),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(
              RythoSpace.xl, RythoSpace.md, RythoSpace.xl, RythoSpace.xxl),
          children: [
            if (label != null) ...[
              RythoReveal(
                  slide: 0, child: Text(label!, style: RythoType.label)),
              const SizedBox(height: RythoSpace.md),
            ],
            for (var i = 0; i < paragraflar.length; i++) ...[
              if (i < 6)
                RythoReveal(
                  index: i + 1,
                  child: Text(paragraflar[i], style: RythoType.reading),
                )
              else
                Text(paragraflar[i], style: RythoType.reading),
              if (i != paragraflar.length - 1)
                const SizedBox(height: RythoSpace.lg),
            ],
            if (trailing != null) ...[
              const SizedBox(height: RythoSpace.xl),
              trailing!,
            ],
          ],
        ),
      ),
    );
  }
}
