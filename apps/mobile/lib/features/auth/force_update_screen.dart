/// Zorunlu güncelleme ekranı (F3).
///
/// Sunucu bu derlemeyi asgari sürümün altında ilan ettiğinde kapı burada
/// kapanır: giriş/onboarding/kabuk hiç açılmaz (bkz. main.dart _Gate).
/// Tek eylem mağazaya gitmek — "sonra" seçeneği bilinçli olarak yok;
/// sunucu bu eşiği ancak eski sürüm gerçekten çalışamaz olduğunda
/// yükseltir (varsayılan 0 = kapı kapalı).
library;

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import '../../theme/rytho_tokens.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/motion.dart';

class ForceUpdateScreen extends StatelessWidget {
  const ForceUpdateScreen({super.key});

  Future<void> _magazayaGit() async {
    // Önce Play uygulaması; kurulu değilse (ör. bazı tabletler) web sayfası.
    final market = Uri.parse('market://details?id=ai.rytho');
    final web = Uri.parse(
        'https://play.google.com/store/apps/details?id=ai.rytho');
    if (!await launchUrl(market)) {
      await launchUrl(web, mode: LaunchMode.externalApplication);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return CosmicScaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(RythoSpace.xl),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const RythoReveal(
                slide: 0,
                child: Text('✨',
                    style: TextStyle(fontSize: 44),
                    textAlign: TextAlign.center),
              ),
              const SizedBox(height: RythoSpace.lg),
              RythoReveal(
                index: 1,
                child: Text(l10n.forceUpdateTitle,
                    style: RythoText.display(22),
                    textAlign: TextAlign.center),
              ),
              const SizedBox(height: RythoSpace.md),
              RythoReveal(
                index: 2,
                child: Text(l10n.forceUpdateBody,
                    style: RythoType.bodyDim, textAlign: TextAlign.center),
              ),
              const SizedBox(height: RythoSpace.xxl),
              RythoReveal(
                index: 3,
                child: GoldButton(
                  text: l10n.forceUpdateAction,
                  onPressed: _magazayaGit,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
