/// Zorunlu güncelleme ekranı (F3 → PBZ).
///
/// Sunucu bu derlemeyi asgari sürümün altında ilan ettiğinde kapı burada
/// kapanır: giriş/onboarding/kabuk hiç açılmaz (bkz. main.dart _Gate).
/// Tek eylem mağazaya gitmek — "sonra" seçeneği bilinçli olarak yok;
/// sunucu bu eşiği ancak eski sürüm gerçekten çalışamaz olduğunda
/// yükseltir (varsayılan 0 = kapı kapalı).
///
/// PBZ eklemeleri: geri tuşu kesilir ([PopScope] `canPop: false` — kök
/// rotada geri tuşu uygulamayı arka plana atıyor, kapı "geçilmiş" gibi
/// görünüyordu); ekranın açılışı ölçülür (eşik yükseltildiğinde kaç
/// kullanıcının kilitlendiği bilinmezse eşiğin bedeli bilinemez); mağaza
/// iki katmanda da açılamazsa kullanıcıya söylenir — sessiz kalan buton,
/// başka çıkışı olmayan ekranda "uygulama bozuldu" demektir.
library;

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/analytics.dart';
import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import '../../theme/rytho_tokens.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/motion.dart';

/// Mağaza bağlantısını açan fonksiyon — `url_launcher.launchUrl` imzası.
typedef StoreLauncher = Future<bool> Function(Uri url, {LaunchMode mode});

Future<bool> _varsayilanLauncher(Uri url,
        {LaunchMode mode = LaunchMode.platformDefault}) =>
    launchUrl(url, mode: mode);

/// Play uygulaması (kuruluysa) — cihazın çoğunda doğrudan mağaza sayfası.
final Uri kPlayMarketUri = Uri.parse('market://details?id=ai.rytho');

/// Web sayfası — Play uygulaması olmayan cihazlar (ör. bazı tabletler).
final Uri kPlayWebUri =
    Uri.parse('https://play.google.com/store/apps/details?id=ai.rytho');

class ForceUpdateScreen extends StatefulWidget {
  const ForceUpdateScreen({super.key, this.launcher});

  /// Test dikişi; üretimde `url_launcher.launchUrl`.
  final StoreLauncher? launcher;

  @override
  State<ForceUpdateScreen> createState() => _ForceUpdateScreenState();
}

class _ForceUpdateScreenState extends State<ForceUpdateScreen> {
  @override
  void initState() {
    super.initState();
    Analytics.forceUpdateShown();
  }

  Future<void> _magazayaGit() async {
    // Önce Play uygulaması; kurulu değilse (ör. bazı tabletler) web sayfası.
    // KT4: `market://` işleyen etkinlik YOKSA launchUrl false döndürmez,
    // PlatformException FIRLATIR — eski kod web'e hiç düşemiyor ve bu
    // ekranın başka çıkışı olmadığı için kullanıcı gerçekten kilitli
    // kalıyordu. İki katman da try içinde: son çare sessiz kalmaktansa
    // web denemesidir.
    final ac = widget.launcher ?? _varsayilanLauncher;
    // Messenger await'ten ÖNCE alınır: sonra context ölmüş olabilir.
    final mesajci = ScaffoldMessenger.of(context);
    final l10n = AppLocalizations.of(context);
    try {
      if (await ac(kPlayMarketUri)) return;
    } catch (_) {}
    try {
      if (await ac(kPlayWebUri, mode: LaunchMode.externalApplication)) return;
    } catch (_) {}
    // İki katman da düştü (Play yok, tarayıcı yok ya da kısıtlı profil):
    // kullanıcı mağazada elle aratabilsin diye söylenir.
    if (!mounted) return;
    mesajci.showSnackBar(SnackBar(content: Text(l10n.forceUpdateStoreFailed)));
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    // Geri tuşu geçmez: bu ekran kök rotada durur ve geri tuşu uygulamayı
    // arka plana atıp yeniden açılışta aynı ekrana düşürür — kilit hissi
    // yerine "takıldı" hissi veriyordu. Tek çıkış mağaza.
    return PopScope(
      canPop: false,
      child: CosmicScaffold(
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
      ),
    );
  }
}
