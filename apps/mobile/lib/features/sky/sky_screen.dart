import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../core/providers.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/glass.dart';
import '../chat/chat_screen.dart';

/// GÖKYÜZÜ — ana ekran: canlı zodyak çemberi (gerçek gezegen konumları),
/// Ay evresi, retrolar ve kişiye özel günlük okuma.
class SkyScreen extends ConsumerWidget {
  const SkyScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sky = ref.watch(skyNowProvider);
    final daily = ref.watch(dailyReadingProvider);
    final today = DateFormat('d MMMM yyyy', 'tr_TR').format(DateTime.now());

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: const Text('Şu Anki Sema'),
        actions: [
          IconButton(
            tooltip: 'Rytho ile konuş',
            icon: const Text('✧', style: TextStyle(fontSize: 22, color: RythoColors.gold)),
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const ChatScreen()),
            ),
          ),
        ],
      ),
      body: RefreshIndicator(
        color: RythoColors.gold,
        backgroundColor: RythoColors.inkLight,
        onRefresh: () async {
          ref.invalidate(skyNowProvider);
          ref.invalidate(dailyReadingProvider);
        },
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.only(bottom: 110),
          children: [
            const SizedBox(height: 8),
            Center(
              child: Text(today.toUpperCase(),
                  style: RythoText.mono(11, color: RythoColors.parchmentDim)),
            ),
            const SizedBox(height: 12),
            sky.when(
              loading: () => const SizedBox(
                  height: 300, child: Center(child: AstrolabeSpinner())),
              error: (e, _) => _ErrorPlaque(error: '$e'),
              data: (data) => Column(children: [
                Center(
                  child: ZodiacRing(
                    planets: List<Map<String, dynamic>>.from(data['planets']),
                    size: MediaQuery.of(context).size.width - 80,
                  ),
                ),
                const SizedBox(height: 16),
                _SkyStrip(sky: data),
              ]),
            ),
            const SectionDivider(),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Text('Günün Okuması', style: RythoText.display(24)),
            ),
            const SizedBox(height: 4),
            daily.when(
              loading: () => const Padding(
                padding: EdgeInsets.all(32),
                child: Center(child: AstrolabeSpinner()),
              ),
              error: (e, _) => _ErrorPlaque(error: '$e'),
              data: (data) => data == null
                  ? const SizedBox.shrink()
                  : GlassPanel(
                      label:
                          '${data['sun_sign']} · ${data['moon_sign']} · yükselen ${data['ascendant']}',
                      child: TypewriterText(
                        text: data['reading'] ?? '',
                        style: RythoText.body(15, height: 1.65),
                      ),
                    ),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}

class _SkyStrip extends StatelessWidget {
  const _SkyStrip({required this.sky});
  final Map<String, dynamic> sky;

  @override
  Widget build(BuildContext context) {
    final moon = sky['moon_phase'] as Map<String, dynamic>? ?? {};
    final retros = List<String>.from(sky['retrogrades'] ?? []);
    final aspects = List<Map<String, dynamic>>.from(sky['aspects'] ?? []);

    return Column(children: [
      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text('${moon['emoji'] ?? ''} ${moon['name'] ?? ''}',
              style: RythoText.body(14)),
          Text('  ·  ', style: RythoText.body(14, color: RythoColors.parchmentDim)),
          Text('aydınlanma %${moon['illumination'] ?? '—'}',
              style: RythoText.mono(12, color: RythoColors.parchmentDim)),
        ],
      ),
      if (retros.isNotEmpty) ...[
        const SizedBox(height: 8),
        Text('Retro: ${retros.join(' · ')}',
            style: RythoText.mono(12, color: RythoColors.copper)),
      ],
      if (aspects.isNotEmpty) ...[
        const SizedBox(height: 12),
        SizedBox(
          height: 30,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            itemCount: aspects.length.clamp(0, 8),
            separatorBuilder: (_, _) => const SizedBox(width: 8),
            itemBuilder: (_, i) {
              final a = aspects[i];
              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 10),
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  border: Border.all(color: RythoColors.line),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  '${a['p1']} ${a['aspect']} ${a['p2']}',
                  style: RythoText.mono(11, color: RythoColors.parchmentDim),
                ),
              );
            },
          ),
        ),
      ],
    ]);
  }
}

class _ErrorPlaque extends StatelessWidget {
  const _ErrorPlaque({required this.error});
  final String error;

  @override
  Widget build(BuildContext context) {
    return Plaque(
      child: Text(
        'Gökyüzüne şu an ulaşılamıyor.\n$error',
        style: RythoText.body(13, color: RythoColors.parchmentDim),
      ),
    );
  }
}
