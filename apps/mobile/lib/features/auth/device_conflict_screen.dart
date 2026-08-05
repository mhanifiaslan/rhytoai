/// Cihaz çakışması ekranı — abonelik başka cihazda devralındığında.
///
/// Kullanıcı buraya sunucudan 409 + `X-Device-Conflict` gelince düşer;
/// oturum o anda kapatılmıştır. Sessiz bir signOut "uygulama bozuldu" hissi
/// verirdi — bu ekran ne olduğunu söyler ve tek çıkış yolunu gösterir:
/// yeniden giriş yap, girişten sonra cihaz devralma onayı sorulur
/// (bkz. auth akışındaki `maybeConfirmDeviceTakeover`).
library;

import 'package:flutter/material.dart';

import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import '../../theme/rytho_tokens.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/motion.dart';

class DeviceConflictScreen extends StatelessWidget {
  const DeviceConflictScreen({super.key});

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
            // Yumuşak giriş (R12-C3): kullanıcının oturumdan atıldığını
            // öğrendiği şok anı — sert bir kesmeyle daha da sertleşmesin.
            children: [
              const RythoReveal(
                slide: 0,
                child: Text('📱',
                    style: TextStyle(fontSize: 44),
                    textAlign: TextAlign.center),
              ),
              const SizedBox(height: RythoSpace.lg),
              RythoReveal(
                index: 1,
                child: Text(l10n.deviceConflictTitle,
                    style: RythoText.display(22),
                    textAlign: TextAlign.center),
              ),
              const SizedBox(height: RythoSpace.md),
              RythoReveal(
                index: 2,
                child: Text(l10n.deviceConflictBody,
                    style: RythoType.bodyDim, textAlign: TextAlign.center),
              ),
              const SizedBox(height: RythoSpace.xxl),
              RythoReveal(
                index: 3,
                child: GoldButton(
                  text: l10n.deviceConflictAction,
                  // Oturum zaten kapalı: bu ekran kapanınca kök karar
                  // mekanizması (authStateProvider) giriş ekranını gösterir.
                  onPressed: () =>
                      Navigator.of(context).popUntil((r) => r.isFirst),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
