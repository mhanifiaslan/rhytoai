import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../../theme/rytho_theme.dart';
import '../../theme/rytho_tokens.dart';
import '../../widgets/fade_through_route.dart';
import '../../widgets/glass.dart';
import '../../widgets/motion.dart';
import '../../widgets/nebula_widgets.dart' show Pressable;
import 'paywall_screen.dart';

/// Rytho+ kilitli içerik kartı.
///
/// Kilitli bir ekrana girildiğinde ücretli uca istek ATILMAZ; onun yerine bu
/// kart gösterilir ve paywall ancak kullanıcı dokununca açılır. Sunucudan 402
/// dönüp paywall'ın kendiliğinden açılması, kullanıcının o ekrana her
/// girişinde yüzüne satış ekranı fırlatmak demek olurdu.
class PlusLockedCard extends StatelessWidget {
  const PlusLockedCard({
    super.key,
    required this.title,
    required this.description,
    this.emoji = '🔒',
    this.centered = false,
  });

  final String title;
  final String description;
  final String emoji;

  /// Tüm ekranı kaplayan boş durumlarda ortalanır (Atlas, BaZi gibi).
  final bool centered;

  @override
  Widget build(BuildContext context) {
    // Altın kilit rozeti (R12-C3): girişte bir kez parlar (tek atış
    // shimmer) — 5 kullanım yerinin hepsinde aynı anda nefes alan sürekli
    // bir döngü ekranı ucuzlatırdı, o yüzden BİLEREK yok.
    Widget kilit = Container(
      padding: const EdgeInsets.all(5),
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: RythoColors.gold.withValues(alpha: 0.12),
      ),
      child: const Icon(Icons.lock_rounded,
          size: 14, color: RythoColors.goldBright),
    );
    if (!reduceMotion(context)) {
      kilit = kilit
          .animate()
          .scale(
              begin: const Offset(0.7, 0.7),
              end: const Offset(1, 1),
              duration: const Duration(milliseconds: 400),
              curve: RythoMotion.pop)
          .then()
          .shimmer(
              duration: 800.ms,
              color: RythoColors.goldBright.withValues(alpha: 0.35));
    }

    // Pressable (R12-C3): dokununca ölçek + haptik — kilitli kart artık
    // "basılabilir" hissettiriyor. Fade-through R12-B2'den.
    final card = Pressable(
      onTap: () => Navigator.of(context)
          .push(FadeThroughRoute(builder: (_) => const PaywallScreen())),
      child: GlassPanel(
        child: Row(children: [
          Text(emoji, style: const TextStyle(fontSize: 20)),
          const SizedBox(width: 12),
          Expanded(
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(title, style: RythoText.display(16)),
              const SizedBox(height: 3),
              Text(description,
                  style:
                      RythoText.body(12.5, color: RythoColors.parchmentDim)),
            ]),
          ),
          kilit,
          const SizedBox(width: 6),
          const Icon(Icons.chevron_right_rounded,
              size: 20, color: RythoColors.parchmentDim),
        ]),
      ),
    );

    if (!centered) return card;
    return Center(
      child: SingleChildScrollView(
        child: Column(mainAxisSize: MainAxisSize.min, children: [card]),
      ),
    );
  }
}
