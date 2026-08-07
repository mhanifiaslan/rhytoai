import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api.dart' show friendlyError;
import '../../core/providers.dart';
import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import '../../theme/rytho_tokens.dart';
import '../../widgets/atlas_widgets.dart';

/// "Şu an yaşadığın şehir" dialogu (D3).
///
/// Neden ayrı bir alan: Yıl Haritası (güneş dönüşü) geleneksel olarak
/// doğum gününde BULUNULAN yere kurulur ve konum haritayı gerçekten
/// değiştirir — aynı dönüş anında Yükselen İstanbul'da İkizler, Sydney'de
/// Terazi çıkıyor. Doğum şehri natal haritanın verisidir ve ona
/// dokunulmaz; bu alan ondan ayrı durur.
///
/// İsteğe bağlıdır: boş bırakılırsa yıl haritası doğum şehrine kurulur ve
/// ekranda bunu söyleyen bir beyan görünür — sessizce varsayılmaz.
Future<void> showResidenceDialog(BuildContext context, WidgetRef ref) {
  return showDialog(
    context: context,
    builder: (_) => const _ResidenceDialog(),
  );
}

class _ResidenceDialog extends ConsumerStatefulWidget {
  const _ResidenceDialog();

  @override
  ConsumerState<_ResidenceDialog> createState() => _ResidenceDialogState();
}

class _ResidenceDialogState extends ConsumerState<_ResidenceDialog> {
  late final TextEditingController _controller = TextEditingController(
      text: (ref.read(profileProvider).value?['residenceCity'] as String?) ??
          '');
  bool _busy = false;
  String? _hata;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _kaydet() async {
    final uid = FirebaseAuth.instance.currentUser?.uid;
    if (uid == null) return;
    setState(() {
      _busy = true;
      _hata = null;
    });
    try {
      // Profil alanı doğrudan yazılır — bildirim bağlamının (timezone,
      // language) izlediği yolun aynısı; ayrı bir uç açmayı hak edecek bir
      // hüküm yok, alan yalnızca haritanın kurulacağı yeri seçiyor.
      await FirebaseFirestore.instance.collection('users').doc(uid).set(
          {'residenceCity': _controller.text.trim()},
          SetOptions(merge: true));
      if (!mounted) return;
      ref.invalidate(profileProvider);
      // Yıl haritası artık başka bir şehre kuruluyor: eldeki okuma bayat.
      ref.invalidate(solarReturnProvider);
      Navigator.of(context).pop();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _hata = friendlyError(e, AppLocalizations.of(context));
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return AlertDialog(
      backgroundColor: RythoColors.inkLight,
      title: Text(l10n.residenceCityTitle, style: RythoText.display(20)),
      content: Column(mainAxisSize: MainAxisSize.min, children: [
        Text(l10n.residenceCityBody, style: RythoType.bodyDim),
        const SizedBox(height: 16),
        TextField(
          controller: _controller,
          autofocus: true,
          style: RythoType.body,
          decoration: InputDecoration(labelText: l10n.onboardingCity),
          onSubmitted: (_) => _kaydet(),
        ),
        if (_hata != null) ...[
          const SizedBox(height: 10),
          Text(_hata!,
              style: RythoText.body(12.5, color: RythoColors.magenta)),
        ],
      ]),
      actions: [
        TextButton(
          onPressed: _busy ? null : () => Navigator.of(context).pop(),
          child: Text(l10n.cancel, style: RythoType.bodyDim),
        ),
        GoldButton(text: l10n.save, busy: _busy, onPressed: _kaydet),
      ],
    );
  }
}
