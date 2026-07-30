import 'package:flutter/material.dart';

import '../../theme/rytho_theme.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/glass.dart';

export 'legal_texts.dart' show privacyPolicySections, termsOfUseSections;

/// Sade cam panelli hukuki metin görüntüleyici.
/// Metinler dile göre `legal_texts.dart` içinden gelir.
class LegalPage extends StatelessWidget {
  const LegalPage({super.key, required this.title, required this.sections});

  final String title;

  /// (başlık | null, gövde) çiftleri — başlıksız girdiler düz paragraftır.
  final List<(String?, String)> sections;

  @override
  Widget build(BuildContext context) {
    return CosmicScaffold(
      appBar: AppBar(title: Text(title)),
      body: ListView(
        padding: const EdgeInsets.only(top: 8, bottom: 40),
        children: [
          GlassPanel(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                for (final (heading, body) in sections) ...[
                  if (heading != null) ...[
                    const SizedBox(height: 14),
                    Text(heading.toUpperCase(),
                        style: RythoText.mono(11,
                            color: RythoColors.goldBright)),
                    const SizedBox(height: 6),
                  ],
                  Text(body,
                      style: RythoText.body(13.5,
                          height: 1.6, color: RythoColors.parchmentDim)),
                  const SizedBox(height: 6),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}
