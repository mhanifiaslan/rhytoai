/// Yüz okuma akışı: rıza → çekim → okuma.
///
/// Rıza ekranı **atlanabilir değil** ve varsayılan kapalı. Biyometrik işleme
/// için açık rıza gerekiyor (GDPR Md.9 / KVKK md.6); "devam" düğmesine
/// basmayı rıza saymak açık rıza değildir, o yüzden ayrı bir onay kutusu var.
///
/// Rıza **kalıcı olarak saklanmıyor.** Her okumada yeniden soruluyor ve bu
/// bilinçli: rızanın geri alınabilir olması gerekiyor ve "bir kez onayladın,
/// artık hep açık" en kötü yorumu. Sürtünme burada bir kusur değil.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api.dart';
import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/glass.dart';
import '../profile/legal_page.dart' show LegalPage, privacyPolicySections;
import 'face_api.dart';
import 'face_capture_screen.dart';

/// Akışın giriş noktası: rıza ekranını açar, onaydan sonra kamerayı.
Future<void> startFaceReading(BuildContext context, WidgetRef ref) async {
  final onay = await Navigator.of(context).push<bool>(MaterialPageRoute(
    builder: (_) => const FaceConsentScreen(),
    fullscreenDialog: true,
  ));
  if (onay != true || !context.mounted) return;

  final sonuc = await Navigator.of(context).push<FaceCaptureResult>(
    MaterialPageRoute(builder: (_) => const FaceCaptureScreen()),
  );
  if (sonuc == null || !context.mounted) return;

  await Navigator.of(context).push(MaterialPageRoute(
    builder: (_) => FaceReadingScreen(result: sonuc),
  ));
}

// ---------------------------------------------------------------------------
// Rıza
// ---------------------------------------------------------------------------

class FaceConsentScreen extends StatefulWidget {
  const FaceConsentScreen({super.key});

  @override
  State<FaceConsentScreen> createState() => _FaceConsentScreenState();
}

class _FaceConsentScreenState extends State<FaceConsentScreen> {
  bool _onaylandi = false;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.faceReadingTitle)),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 28),
          children: [
            Text(l10n.faceConsentTitle, style: RythoText.display(20)),
            const SizedBox(height: 16),
            GlassPanel(
              child: Text(l10n.faceConsentBody,
                  style: RythoText.body(14, color: RythoColors.parchment)),
            ),
            const SizedBox(height: 8),
            TextButton(
              onPressed: () => Navigator.of(context).push(MaterialPageRoute(
                builder: (_) => LegalPage(
                  title: l10n.privacyPolicy,
                  sections: privacyPolicySections(
                      Localizations.localeOf(context).languageCode),
                ),
              )),
              child: Text(l10n.faceConsentLearnMore),
            ),
            const SizedBox(height: 8),
            // Ayrı onay kutusu: "devam"a basmayı rıza saymak açık rıza
            // değildir. Varsayılan KAPALI.
            CheckboxListTile(
              value: _onaylandi,
              onChanged: (v) => setState(() => _onaylandi = v ?? false),
              controlAffinity: ListTileControlAffinity.leading,
              contentPadding: EdgeInsets.zero,
              title: Text(l10n.faceConsentCheckbox,
                  style: RythoText.body(13.5)),
            ),
            const SizedBox(height: 12),
            FilledButton(
              onPressed:
                  _onaylandi ? () => Navigator.of(context).pop(true) : null,
              child: Text(l10n.faceConsentContinue),
            ),
          ],
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Okuma
// ---------------------------------------------------------------------------

class FaceReadingScreen extends ConsumerStatefulWidget {
  const FaceReadingScreen({super.key, required this.result});

  final FaceCaptureResult result;

  @override
  ConsumerState<FaceReadingScreen> createState() => _FaceReadingScreenState();
}

class _FaceReadingScreenState extends ConsumerState<FaceReadingScreen> {
  late final Future<String> _okuma =
      fetchFirasaReading(ref.read(apiProvider), widget.result);

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.faceReadingTitle)),
      body: SafeArea(
        child: FutureBuilder<String>(
          future: _okuma,
          builder: (context, snap) {
            if (snap.connectionState != ConnectionState.done) {
              return Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const CircularProgressIndicator(),
                    const SizedBox(height: 16),
                    Text(l10n.faceScanReading,
                        style:
                            RythoText.body(14, color: RythoColors.parchmentDim)),
                  ],
                ),
              );
            }
            if (snap.hasError) {
              return Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text(friendlyError(snap.error ?? Exception(), l10n),
                      textAlign: TextAlign.center,
                      style: RythoText.body(14)),
                ),
              );
            }
            return ListView(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 28),
              children: [
                // Geleneğin kendi sınırı okumanın ÜSTÜNDE duruyor, altında
                // değil: kullanıcı metni okumadan önce neye baktığını bilmeli.
                Text(l10n.faceReadingHint,
                    style: RythoText.body(12.5,
                        color: RythoColors.parchmentDim)),
                const SizedBox(height: 16),
                GlassPanel(
                  child: Text(snap.data ?? '',
                      style: RythoText.body(15, color: RythoColors.parchment)),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}
