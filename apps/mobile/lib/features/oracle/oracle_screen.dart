import 'package:flutter/material.dart';

import '../../widgets/cosmic_scaffold.dart';
import 'bazi_tab.dart';
import 'iching_tab.dart';
import '../../l10n/app_localizations.dart';

/// KEHANET ekranları — her disiplin KENDİ sayfasında (Revize R10).
///
/// Eski hâli tek `OracleScreen` + üstte İCHİNG|BAZİ sekmeleriydi. Atlas'ta
/// zaten iki ayrı karo varken karodan girilen sayfada aynı iki seçeneğin
/// sekme olarak tekrar çıkması kafa karıştırıyordu (kullanıcı bildirimi:
/// "baziye girince de ichinge girince de üstte iki seçenek var"). Karo
/// hangi disiplinse sayfa artık odur; diğerine geçiş Atlas üzerinden.
///
/// Gövdeler `iching_tab.dart` / `bazi_tab.dart` içinde kaldı — dosya adları
/// sekme döneminden miras, içerik sekmeye bağımlı değil.
class IChingScreen extends StatelessWidget {
  const IChingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return CosmicScaffold(
      appBar: AppBar(title: Text(l10n.iChing)),
      body: const IChingTab(),
    );
  }
}

class BaziScreen extends StatelessWidget {
  const BaziScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return CosmicScaffold(
      appBar: AppBar(title: Text(l10n.baZi)),
      body: const BaziTab(),
    );
  }
}
