import 'package:flutter/material.dart';

import '../l10n/app_localizations.dart';
import '../theme/rytho_theme.dart';
import '../theme/rytho_tokens.dart';

/// Tema anahtarı -> ikon. Anahtarlar sunucudaki signal_service.THEMES ile
/// aynı; sinyal kartları ve takvim günleri aynı işareti kullanır.
const kThemeIcons = {
  'career': '💼',
  'relationships': '❤️',
  'inner': '🌙',
  'finance': '🪙',
};

/// "Neden?" alt-sayfası (R2-S2): bir sinyalin DAYANAĞI.
///
/// "Ölçülmeyen söylenmez" ilkesinin görünür hâli: kart üstündeki cümlenin
/// hangi ölçümlerden çıktığını satır satır gösterir — gezen gezegen, natal
/// nokta (burcu ve eviyle), açı, ölçülen orb, kesinleşme tarihi. Yorum
/// (insight) varsa en sonda, "bu ölçümlerin üzerine kurulu" çerçevesiyle.
///
/// Sunucu sözleşmesi: /api/v1/reports/signals yanıtındaki tek sinyal
/// (localize edilmiş alanlarıyla). Bileşen alan yoksa satırı ATLAR —
/// üretilmemiş bilgi çizilmez.
Future<void> showSignalBasisSheet(
  BuildContext context,
  Map<String, dynamic> signal, {
  VoidCallback? onAsk,
  String? title,
}) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: RythoColors.inkLight,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(22)),
      side: BorderSide(color: RythoColors.glassStroke),
    ),
    builder: (_) => _BasisSheet(signal: signal, onAsk: onAsk, title: title),
  );
}

class _BasisSheet extends StatelessWidget {
  const _BasisSheet({required this.signal, this.onAsk, this.title});

  final Map<String, dynamic> signal;
  final VoidCallback? onAsk;

  /// Sayfa başlığı; verilmezse sinyal başlığı. Takvim günü aynı sayfayı
  /// "Bu tarih neden önemli?" başlığıyla kullanır (R2-Z1).
  final String? title;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);

    final gokyuzu = [
      signal['transit_local'] ?? signal['transit'],
      if (signal['movement_local'] != null) signal['movement_local'],
    ].whereType<String>().join(' · ');

    final natalParcalar = <String>[
      (signal['natal_local'] ?? signal['natal'] ?? '') as String,
      if (signal['natal_sign_local'] is String)
        signal['natal_sign_local'] as String,
      if (signal['natal_house'] is int)
        l10n.basisHouse((signal['natal_house'] as num).toInt()),
    ];

    final orb = signal['orb'];
    final insight = signal['insight'] as String?;

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(
            RythoSpace.lg, RythoSpace.md, RythoSpace.lg, RythoSpace.lg),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Center(
              child: Container(
                width: 36,
                height: 4,
                decoration: BoxDecoration(
                  color: RythoColors.glassStroke,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: RythoSpace.md),
            Text(title ?? l10n.basisSheetTitle,
                style: RythoText.display(17, w: FontWeight.w600)),
            const SizedBox(height: 6),
            // Teknik cümle KART YÜZEYİNDEN buraya taşındı (R2-S6): meraklı
            // kullanıcı tam ölçümü burada bulur, kart yüzeyi gündelik dilde
            // kalır. Eski sürümlerde alan yoksa kart cümlesine düşülür.
            Text(
                (signal['technical'] as String?) ??
                    (signal['headline'] as String? ?? ''),
                style: RythoText.body(13, color: RythoColors.lilac,
                    height: 1.4)),
            const SizedBox(height: RythoSpace.md),
            _Satir(etiket: l10n.basisSky, deger: gokyuzu),
            _Satir(
                etiket: l10n.basisNatal,
                deger:
                    natalParcalar.where((p) => p.isNotEmpty).join(' · ')),
            _Satir(
                etiket: l10n.basisAspect,
                deger: (signal['aspect_local'] ?? signal['aspect'] ?? '')
                    as String),
            if (orb is num)
              _Satir(etiket: l10n.basisOrb, deger: '${orb.toString()}°'),
            if (signal['exact_on_local'] is String)
              _Satir(
                  etiket: l10n.basisExact,
                  deger: signal['exact_on_local'] as String,
                  vurgu: true),
            if (insight != null && insight.isNotEmpty) ...[
              const SizedBox(height: RythoSpace.sm),
              Container(
                padding: const EdgeInsets.all(RythoSpace.md),
                decoration: BoxDecoration(
                  color: RythoColors.glassFill,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: RythoColors.glassStroke),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(l10n.basisSynthesis.toUpperCase(),
                        style: RythoType.dataSmall),
                    const SizedBox(height: 4),
                    Text(insight, style: RythoText.body(13.5, height: 1.45)),
                  ],
                ),
              ),
            ],
            const SizedBox(height: RythoSpace.md),
            Text(l10n.basisFootnote,
                style: RythoText.body(11.5,
                    color: RythoColors.parchmentDim, height: 1.4)),
            if (onAsk != null) ...[
              const SizedBox(height: RythoSpace.md),
              OutlinedButton.icon(
                onPressed: onAsk,
                icon: const Text('✦', style: TextStyle(fontSize: 14)),
                label: Text(l10n.signalAsk),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _Satir extends StatelessWidget {
  const _Satir(
      {required this.etiket, required this.deger, this.vurgu = false});

  final String etiket;
  final String deger;
  final bool vurgu;

  @override
  Widget build(BuildContext context) {
    if (deger.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 108,
            child: Text(etiket.toUpperCase(), style: RythoType.dataSmall),
          ),
          const SizedBox(width: RythoSpace.sm),
          Expanded(
            child: Text(
              deger,
              style: RythoText.body(13.5,
                  color: vurgu ? RythoColors.gold : RythoColors.parchment),
            ),
          ),
        ],
      ),
    );
  }
}
