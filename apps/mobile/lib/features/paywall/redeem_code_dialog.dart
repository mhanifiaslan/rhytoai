import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api.dart';
import '../../core/wallet.dart';
import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';

/// Ortak kodu dialogu (W9): Profil satırından ve paywall'daki küçük
/// linkten açılır. Kod sunucuda doğrulanır; başarıda jeton bonusu yüklenir
/// ve SONRAKİ satın almalar koda atfedilir. Her hesapta TEK kod geçer —
/// 409 dahil tüm hüküm mesajları sunucudan gelir (friendlyError aynen
/// gösterir; metinler istek dilinde üretiliyor).
Future<void> showRedeemCodeDialog(BuildContext context, WidgetRef ref) {
  return showDialog(
    context: context,
    builder: (_) => const _RedeemCodeDialog(),
  ).then((sonuc) {
    if (sonuc is int && context.mounted) {
      ref.invalidate(walletProvider);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(
              AppLocalizations.of(context).redeemCodeSuccess(sonuc))));
    }
  });
}

class _RedeemCodeDialog extends ConsumerStatefulWidget {
  const _RedeemCodeDialog();

  @override
  ConsumerState<_RedeemCodeDialog> createState() =>
      _RedeemCodeDialogState();
}

class _RedeemCodeDialogState extends ConsumerState<_RedeemCodeDialog> {
  final _controller = TextEditingController();
  bool _busy = false;
  String? _hata;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _kullan() async {
    final kod = _controller.text.trim();
    if (kod.isEmpty) return;
    setState(() {
      _busy = true;
      _hata = null;
    });
    try {
      final dio = ref.read(apiProvider);
      final yanit = await dio.post('/api/v1/billing/redeem-code',
          data: {'code': kod});
      if (!mounted) return;
      Navigator.of(context)
          .pop((yanit.data['bonusTokens'] as num?)?.toInt() ?? 0);
    } on DioException catch (e) {
      if (mounted) {
        setState(() => _hata =
            friendlyError(e, AppLocalizations.of(context)));
      }
    } catch (e) {
      if (mounted) {
        setState(() =>
            _hata = friendlyError(e, AppLocalizations.of(context)));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return AlertDialog(
      backgroundColor: RythoColors.inkLight,
      shape:
          RoundedRectangleBorder(borderRadius: BorderRadius.circular(22)),
      title: Text(l10n.redeemCodeTitle, style: RythoText.display(18)),
      content: Column(mainAxisSize: MainAxisSize.min, children: [
        TextField(
          controller: _controller,
          autofocus: true,
          textCapitalization: TextCapitalization.characters,
          maxLength: 24,
          style: RythoText.mono(15),
          decoration: InputDecoration(
            hintText: l10n.redeemCodeHint,
            counterText: '',
          ),
          onSubmitted: (_) => _kullan(),
        ),
        if (_hata != null) ...[
          const SizedBox(height: 10),
          Text(_hata!,
              style: RythoText.body(12.5, color: RythoColors.madder)),
        ],
      ]),
      actions: [
        TextButton(
          onPressed: _busy ? null : () => Navigator.of(context).pop(),
          child: Text(l10n.cancel,
              style:
                  RythoText.label(12.5, color: RythoColors.parchmentDim)),
        ),
        _busy
            ? const Padding(
                padding: EdgeInsets.symmetric(horizontal: 16),
                child: AstrolabeSpinner(size: 20),
              )
            : TextButton(
                onPressed: _kullan,
                child: Text(l10n.redeemCodeAction,
                    style: RythoText.label(13,
                        color: RythoColors.goldBright)),
              ),
      ],
    );
  }
}
