import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';

/// BaZi — Dört Sütun tablosu, Day Master, element dağılımı, şans dönemleri.
class BaziTab extends ConsumerWidget {
  const BaziTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final bazi = ref.watch(baziReportProvider);

    return bazi.when(
      loading: () => const Center(child: AstrolabeSpinner()),
      error: (e, _) => Center(
        child: Text('BaZi hesaplanamadı: $e',
            style: RythoText.body(13, color: RythoColors.parchmentDim)),
      ),
      data: (data) {
        if (data == null) return const SizedBox.shrink();
        final chart = Map<String, dynamic>.from(data['chart']);
        final pillars = Map<String, dynamic>.from(chart['pillars']);
        final elements =
            Map<String, dynamic>.from(chart['element_distribution']);
        final luck = List<Map<String, dynamic>>.from(chart['luck_pillars']);

        return ListView(
            padding: const EdgeInsets.only(top: 8, bottom: 110),
            children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Text('Kaderin Dört Sütunu', style: RythoText.display(28)),
          ),
          const SizedBox(height: 4),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Text(
              'Çin burcun: ${chart['zodiac_animal']} · '
              '${chart['day_master']['description']}',
              style: RythoText.body(13, color: RythoColors.parchmentDim),
            ),
          ),
          Plaque(
            label: 'Dört Sütun',
            padding: const EdgeInsets.all(12),
            child: Row(children: [
              for (final key in const [
                ('hour', 'SAAT'),
                ('day', 'GÜN'),
                ('month', 'AY'),
                ('year', 'YIL'),
              ])
                Expanded(child: _PillarColumn(
                  label: key.$2,
                  pillar: Map<String, dynamic>.from(pillars[key.$1]),
                  highlight: key.$1 == 'day',
                )),
            ]),
          ),
          Plaque(
            label: 'Element Terazisi',
            child: Column(children: [
              for (final e in elements.entries)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Row(children: [
                    SizedBox(
                        width: 64,
                        child: Text(e.key, style: RythoText.body(13))),
                    Expanded(
                      child: Row(children: [
                        for (var i = 0; i < 8; i++)
                          Container(
                            width: 14,
                            height: 8,
                            margin: const EdgeInsets.only(right: 3),
                            decoration: BoxDecoration(
                              color: i < (e.value as num)
                                  ? RythoColors.gold
                                  : Colors.transparent,
                              border: Border.all(color: RythoColors.line),
                            ),
                          ),
                      ]),
                    ),
                    Text('${e.value}', style: RythoText.mono(12)),
                  ]),
                ),
              if ((chart['missing_elements'] as List).isNotEmpty) ...[
                const SizedBox(height: 8),
                Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    'Beslenecek element: ${(chart['missing_elements'] as List).join(', ')}',
                    style: RythoText.mono(11, color: RythoColors.copper),
                  ),
                ),
              ],
            ]),
          ),
          Plaque(
            label: 'Şans Sütunları (Da Yun)',
            padding: const EdgeInsets.all(8),
            child: SizedBox(
              height: 92,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: luck.length,
                separatorBuilder: (_, _) => const SizedBox(width: 8),
                itemBuilder: (_, i) {
                  final lp = luck[i];
                  return Container(
                    width: 96,
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      border: Border.all(color: RythoColors.line),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('${lp['from_age']}–${lp['to_age']} YAŞ',
                            style: RythoText.mono(10,
                                color: RythoColors.parchmentDim)),
                        const SizedBox(height: 4),
                        Text(
                            '${lp['stem']['cn']}${lp['branch']['cn']}',
                            style: RythoText.display(20)),
                        const Spacer(),
                        Text(lp['ten_god']['name'],
                            style: RythoText.body(10.5,
                                color: RythoColors.parchmentDim),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis),
                      ],
                    ),
                  );
                },
              ),
            ),
          ),
          const SectionDivider(),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: MarginNote(
                title: 'Rytho\'nun kader notu', text: data['report'] ?? ''),
          ),
          const SizedBox(height: 32),
        ]);
      },
    );
  }
}

class _PillarColumn extends StatelessWidget {
  const _PillarColumn(
      {required this.label, required this.pillar, this.highlight = false});
  final String label;
  final Map<String, dynamic> pillar;
  final bool highlight;

  @override
  Widget build(BuildContext context) {
    final stem = Map<String, dynamic>.from(pillar['stem']);
    final branch = Map<String, dynamic>.from(pillar['branch']);
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 3),
      padding: const EdgeInsets.symmetric(vertical: 10),
      decoration: BoxDecoration(
        border: Border.all(
            color: highlight ? RythoColors.gold : RythoColors.line),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Column(children: [
        Text(label, style: RythoText.mono(9, color: RythoColors.parchmentDim)),
        const SizedBox(height: 8),
        Text(stem['cn'], style: RythoText.display(24, color: RythoColors.goldBright)),
        Text(stem['element'],
            style: RythoText.body(10, color: RythoColors.parchmentDim)),
        const SizedBox(height: 6),
        Text(branch['cn'], style: RythoText.display(24)),
        Text(branch['animal'],
            style: RythoText.body(10, color: RythoColors.parchmentDim)),
      ]),
    );
  }
}
