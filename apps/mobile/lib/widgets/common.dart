/// Her ekranda yeniden yazılan desenlerin ortak hâli.
///
/// Aşağıdakilerin hepsi kod tabanında birden fazla kez, birbirinden hafifçe
/// farklı biçimde tekrar yazılmıştı. Fark küçük olduğu için kimse bakıp
/// "burası tutarsız" demiyor; ama üst üste gelince kullanıcının "dağınık"
/// dediği his tam olarak bu oluyor.
///
/// * Bölüm başlığı: Gökyüzü `fromLTRB(20,14,20,6)` kullanıyordu, Arkadaşlar
///   `fromLTRB(20,4,20,2)` — aynı rol, iki ayrı ritim.
/// * Hata kartı: Gökyüzü'nde `_ErrorCard`, arkadaş detayında ayrı bir panel.
/// * Boş durum: yalnızca sohbette vardı, ötekiler düz metin gösteriyordu.
/// * Etiket-değer satırı: profilde ve yüz sekmesinde iki ayrı `_row`.
library;

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../theme/rytho_theme.dart';
import '../theme/rytho_tokens.dart';
import 'glass.dart';
import 'motion.dart';

/// Bölüm başlığı — "Bugün senin için", "Şu an", "Araçlar".
class SectionHeader extends StatelessWidget {
  const SectionHeader(this.title, {super.key, this.trailing});

  final String title;

  /// Sağ uçta küçük ikincil bilgi (tarih, sayaç).
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(
          RythoSpace.xl, RythoSpace.lg, RythoSpace.xl, RythoSpace.sm),
      child: Row(
        children: [
          Text(title, style: RythoType.sectionTitle),
          if (trailing != null) ...[const Spacer(), trailing!],
        ],
      ),
    );
  }
}

/// Hata kartı — isteğe bağlı yeniden deneme.
///
/// Hata metni `friendlyError()` ile üretilmiş olmalı; ham `DioException`
/// metnini basmak kullanıcıya HTTP durum kodu göstermek demek.
class ErrorCard extends StatelessWidget {
  const ErrorCard({super.key, required this.message, this.onRetry});

  final String message;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    final ingilizce = Localizations.localeOf(context).languageCode == 'en';
    final kart = GlassPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(Icons.error_outline_rounded,
                  size: 18, color: RythoColors.madder),
              const SizedBox(width: RythoSpace.sm),
              Expanded(child: Text(message, style: RythoType.bodyDim)),
            ],
          ),
          if (onRetry != null) ...[
            const SizedBox(height: RythoSpace.sm),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                onPressed: onRetry,
                child: Text(ingilizce ? 'Try again' : 'Tekrar dene',
                    style: RythoType.button),
              ),
            ),
          ],
        ],
      ),
    );
    if (reduceMotion(context)) return kart;
    // Girişte TEK küçük sarsıntı (R12-C3): hata fark edilir, panik
    // yaratmaz. Döngü yok.
    return kart
        .animate()
        .shake(hz: 3, offset: const Offset(3, 0), duration: 400.ms);
  }
}

/// Boş durum — içerik yokluğunu AÇIKLAYAN ekran parçası.
///
/// Boş bir alan bırakmak kullanıcıya "bir şey bozuldu" hissi veriyor; ne
/// olduğunu ve ne yapabileceğini söylemek gerekiyor.
class EmptyState extends StatelessWidget {
  const EmptyState({
    super.key,
    required this.emoji,
    required this.title,
    this.description,
    this.action,
  });

  final String emoji;
  final String title;
  final String? description;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    // Kademeli giriş (R12-C3): amblem pop'la, metinler reveal'le gelir —
    // TEK atış; 8+ ekrandaki boş durum tek dokunuşta ısındı.
    Widget amblem = Text(emoji, style: const TextStyle(fontSize: 34));
    if (!reduceMotion(context)) {
      amblem = amblem
          .animate()
          .fadeIn(duration: RythoMotion.base)
          .scale(
              begin: const Offset(0.7, 0.7),
              end: const Offset(1, 1),
              duration: const Duration(milliseconds: 400),
              curve: RythoMotion.pop);
    }
    return Padding(
      padding: const EdgeInsets.symmetric(
          horizontal: RythoSpace.xl, vertical: RythoSpace.xxl),
      child: Column(
        children: [
          amblem,
          const SizedBox(height: RythoSpace.md),
          RythoReveal(
            index: 1,
            child: Text(title,
                style: RythoType.cardTitle, textAlign: TextAlign.center),
          ),
          if (description != null) ...[
            const SizedBox(height: RythoSpace.sm),
            RythoReveal(
              index: 2,
              child: Text(description!,
                  style: RythoType.bodyDim, textAlign: TextAlign.center),
            ),
          ],
          if (action != null) ...[
            const SizedBox(height: RythoSpace.lg),
            RythoReveal(index: 3, child: action!),
          ],
        ],
      ),
    );
  }
}

/// Ayar/gezinme satırı: solda başlık (+açıklama), sağda değer ve chevron.
///
/// Profil ekranının iki seviyeli hâlinin yapı taşı. Önceki hâlde 14 kontrol
/// tek sayfada satır satır duruyordu; artık her grup kendi sayfasını açıyor.
class SettingsRow extends StatelessWidget {
  const SettingsRow({
    super.key,
    required this.title,
    this.subtitle,
    this.value,
    this.icon,
    this.onTap,
    this.trailing,
  });

  final String title;
  final String? subtitle;

  /// Sağda gösterilen mevcut değer — ör. doğum tarihi.
  final String? value;
  final IconData? icon;
  final VoidCallback? onTap;

  /// `trailing` verilirse chevron yerine bu gösterilir (ör. `Switch`).
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(RythoRadius.md),
      child: Padding(
        padding: const EdgeInsets.symmetric(
            horizontal: RythoSpace.lg, vertical: RythoSpace.md),
        child: Row(
          children: [
            if (icon != null) ...[
              Icon(icon, size: 19, color: RythoColors.lilac),
              const SizedBox(width: RythoSpace.md),
            ],
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: RythoType.body),
                  if (subtitle != null) ...[
                    const SizedBox(height: 2),
                    Text(subtitle!, style: RythoType.caption),
                  ],
                ],
              ),
            ),
            if (value != null) ...[
              const SizedBox(width: RythoSpace.sm),
              Text(value!, style: RythoType.dataSmall),
            ],
            if (trailing != null)
              trailing!
            else if (onTap != null) ...[
              const SizedBox(width: RythoSpace.xs),
              const Icon(Icons.chevron_right_rounded,
                  size: 20, color: RythoColors.parchmentDim),
            ],
          ],
        ),
      ),
    );
  }
}

/// Etiket-değer satırı — salt okunur veri gösterimi.
class LabelValueRow extends StatelessWidget {
  const LabelValueRow({super.key, required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: RythoType.bodyDim),
          Text(value, style: RythoType.data),
        ],
      ),
    );
  }
}
