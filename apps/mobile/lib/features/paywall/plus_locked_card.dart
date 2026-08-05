import 'package:flutter/material.dart';

import '../../theme/rytho_theme.dart';
import '../../widgets/fade_through_route.dart';
import '../../widgets/glass.dart';
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
    final card = GlassPanel(
      // Fade-through (R12-B2): kilitten satış ekranına sert Material
      // geçişi yerine içerik açılışı.
      onTap: () => Navigator.of(context)
          .push(FadeThroughRoute(builder: (_) => const PaywallScreen())),
      child: Row(children: [
        Text(emoji, style: const TextStyle(fontSize: 20)),
        const SizedBox(width: 12),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(title, style: RythoText.display(16)),
            const SizedBox(height: 3),
            Text(description,
                style: RythoText.body(12.5, color: RythoColors.parchmentDim)),
          ]),
        ),
        const Icon(Icons.chevron_right_rounded,
            size: 20, color: RythoColors.parchmentDim),
      ]),
    );

    if (!centered) return card;
    return Center(
      child: SingleChildScrollView(
        child: Column(mainAxisSize: MainAxisSize.min, children: [card]),
      ),
    );
  }
}
