/// "Şu an" — canlı gökyüzü çarkı ve ayrıntıları, kendi sayfasında.
///
/// ## Neden akıştan çıktı
///
/// 230 px'lik çark + ay evresi + retro çipleri + sekiz açı çipi, Gökyüzü
/// akışının sonunda tek blok hâlinde duruyordu. "Bugün ne var" diye bakan
/// kullanıcı her seferinde onun içinden geçmek zorundaydı; ölçülen ekran
/// uzunluğunun (~1500 px) büyük bir dilimi buydu.
///
/// Akışta artık tek satırlık bir özet var: ay evresi, retro sayısı, öne çıkan
/// açı. Ayrıntı bir dokunuş uzakta — yani kaybolmadı, sadece kendi seviyesine
/// indi.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api.dart' show friendlyError;
import '../../core/providers.dart';
import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import '../../theme/rytho_tokens.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/common.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/glass.dart';
import '../../widgets/nebula_widgets.dart';
import '../atlas/chart_inspector_screen.dart'
    show ChartInspectorMode, ChartInspectorScreen;

class SkyNowScreen extends ConsumerWidget {
  const SkyNowScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final sky = ref.watch(skyNowProvider);

    return CosmicScaffold(
      appBar: AppBar(title: Text(l10n.skyNow)),
      body: SafeArea(
        child: sky.when(
          loading: () => const Center(child: AstrolabeSpinner()),
          error: (e, _) => Padding(
            padding: const EdgeInsets.all(RythoSpace.xl),
            child: ErrorCard(
              message: friendlyError(e, l10n),
              onRetry: () => ref.invalidate(skyNowProvider),
            ),
          ),
          data: (data) => ListView(
            padding: const EdgeInsets.fromLTRB(0, RythoSpace.md, 0,
                RythoSpace.xxl),
            children: [
              Center(
                child: ZodiacRing(
                  planets: List<Map<String, dynamic>>.from(data['planets']),
                  size: 280,
                ),
              ),
              // Harita İnceleme girişi (HI-turu): gökyüzü çarkının
              // profesyonel görünümü — derece cetveli, açı ağı, tablo.
              Align(
                alignment: Alignment.centerRight,
                child: Padding(
                  padding:
                      const EdgeInsets.symmetric(horizontal: RythoSpace.lg),
                  child: TextButton.icon(
                    onPressed: () => Navigator.of(context).push(
                        MaterialPageRoute(
                            builder: (_) => const ChartInspectorScreen(
                                mode: ChartInspectorMode.sky))),
                    icon: const Icon(Icons.open_in_full_rounded, size: 15),
                    label: Text(l10n.chartExpandTooltip,
                        style: RythoText.label(11,
                            color: RythoColors.goldBright)),
                  ),
                ),
              ),
              const SizedBox(height: RythoSpace.sm),
              GlassPanel(child: SkyDetails(sky: data)),
            ],
          ),
        ),
      ),
    );
  }
}

/// Ay evresi, retrolar ve açılar — ayrıntı sayfasının gövdesi.
class SkyDetails extends StatelessWidget {
  const SkyDetails({super.key, required this.sky});

  final Map<String, dynamic> sky;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final moon = sky['moon_phase'] as Map<String, dynamic>? ?? {};
    final retros = List<String>.from(sky['retrogrades'] ?? []);
    final aspects = List<Map<String, dynamic>>.from(sky['aspects'] ?? []);

    return Column(children: [
      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text('${moon['emoji'] ?? ''} ${moon['name'] ?? ''}',
              style: RythoText.body(14, w: FontWeight.w600)),
          Text('  ·  ', style: RythoType.bodyDim),
          Text(l10n.moonIllumination(moon['illumination'] ?? '—'),
              style: RythoType.dataSmall),
        ],
      ),
      // Aydınlanma oranı ANA bağlıdır: bir gün içinde 10 puana kadar
      // değişir. Başka bir kaynakla kıyaslayan kullanıcının ilk sorusu
      // "hangi ana ait?" oluyor — cevabı ekranda duruyor.
      if (moon['as_of_utc'] != null) ...[
        const SizedBox(height: 4),
        Text(l10n.moonIlluminationAsOf(_yerelAn('${moon['as_of_utc']}')),
            style: RythoType.caption),
      ],
      if (retros.isNotEmpty) ...[
        const SizedBox(height: RythoSpace.md),
        Wrap(
          spacing: RythoSpace.sm,
          runSpacing: 6,
          alignment: WrapAlignment.center,
          children: [
            for (final r in retros)
              InfoChip(
                  text: '↩️ ${l10n.retrogradeChip(r)}',
                  color: RythoColors.magenta),
          ],
        ),
      ],
      if (aspects.isNotEmpty) ...[
        const SizedBox(height: RythoSpace.md),
        Wrap(
          spacing: RythoSpace.sm,
          runSpacing: 6,
          alignment: WrapAlignment.center,
          children: [
            // HA1: sunucu artık kararlı anahtarların üzerine yazmıyor;
            // görünen ad *_local'den gelir (eski sunucuya karşı yedekli).
            for (final a in aspects.take(8))
              InfoChip(
                  text: '${a['p1_local'] ?? a['p1']} '
                      '${a['aspect_local'] ?? a['aspect']} '
                      '${a['p2_local'] ?? a['p2']}'),
          ],
        ),
      ],
    ]);
  }

  /// UTC ISO damgasını cihazın yerel saatinde "07.08 06:12" biçimine çevirir.
  static String _yerelAn(String iso) {
    final t = DateTime.tryParse(iso)?.toLocal();
    if (t == null) return '';
    String iki(int n) => n.toString().padLeft(2, '0');
    return '${iki(t.day)}.${iki(t.month)} ${iki(t.hour)}:${iki(t.minute)}';
  }
}

/// Akıştaki tek satırlık özet — dokununca [SkyNowScreen] açar.
///
/// Gösterge uyumu: kart gibi görünüyor, kart gibi davranıyor, sağında chevron
/// var. "Görünüşü X, davranışı Y" sorunu tam olarak buradan doğuyordu.
class SkyNowSummary extends StatelessWidget {
  const SkyNowSummary({super.key, required this.sky});

  final Map<String, dynamic> sky;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final moon = sky['moon_phase'] as Map<String, dynamic>? ?? {};
    final retros = List<String>.from(sky['retrogrades'] ?? []);
    final aspects = List<Map<String, dynamic>>.from(sky['aspects'] ?? []);

    // Tek bir açı gösteriliyor: sekiz çipin hepsi bir bakışta okunmuyordu,
    // biri okunuyor.
    final oneCikan = aspects.isEmpty
        ? null
        : '${aspects.first['p1_local'] ?? aspects.first['p1']} '
            '${aspects.first['aspect_local'] ?? aspects.first['aspect']} '
            '${aspects.first['p2_local'] ?? aspects.first['p2']}';

    return GlassPanel(
      onTap: () => Navigator.of(context)
          .push(MaterialPageRoute(builder: (_) => const SkyNowScreen())),
      child: Row(
        children: [
          Text(moon['emoji'] as String? ?? '🌙',
              style: const TextStyle(fontSize: 26)),
          const SizedBox(width: RythoSpace.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${moon['name'] ?? ''} · '
                  '${l10n.moonIllumination(moon['illumination'] ?? '—')}',
                  style: RythoType.body,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 2),
                Text(
                  [
                    if (retros.isNotEmpty) l10n.retrogradeCount(retros.length),
                    ?oneCikan,
                  ].join(' · '),
                  style: RythoType.caption,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          const Icon(Icons.chevron_right_rounded,
              size: 20, color: RythoColors.parchmentDim),
        ],
      ),
    );
  }
}
