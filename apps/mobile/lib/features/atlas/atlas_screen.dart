import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_svg/flutter_svg.dart';

import '../../core/providers.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';

/// ATLAS — doğum haritası: Büyük Üçlü, gravür SVG çarkı, gezegen cetveli,
/// açılar ve derin AI raporu.
class AtlasScreen extends ConsumerWidget {
  const AtlasScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final natal = ref.watch(natalReportProvider);
    final svg = ref.watch(natalSvgProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Doğum Atlası')),
      body: natal.when(
        loading: () => const Center(child: AstrolabeSpinner()),
        error: (e, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Text('Atlas çizilemedi: $e',
                style: RythoText.body(14, color: RythoColors.parchmentDim)),
          ),
        ),
        data: (data) {
          if (data == null) return const SizedBox.shrink();
          final chart = Map<String, dynamic>.from(data['chart']);
          final points = List<Map<String, dynamic>>.from(chart['points'] ?? []);
          final aspects = List<Map<String, dynamic>>.from(chart['aspects'] ?? []);

          return ListView(children: [
            const SizedBox(height: 8),
            _BigThree(chart: chart),
            svg.when(
              loading: () => const SizedBox.shrink(),
              error: (_, _) => const SizedBox.shrink(),
              data: (svgString) => svgString == null
                  ? const SizedBox.shrink()
                  : Plaque(
                      label: 'Levha I — Gök Çarkı',
                      padding: const EdgeInsets.all(4),
                      child: SvgPicture.string(svgString, fit: BoxFit.contain),
                    ),
            ),
            Plaque(
              label: 'Levha II — Gezegen Cetveli',
              padding: EdgeInsets.zero,
              child: Column(children: [
                for (final p in points)
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
                    decoration: BoxDecoration(
                      border: p == points.last
                          ? null
                          : const Border(
                              bottom: BorderSide(color: RythoColors.line)),
                    ),
                    child: Row(children: [
                      SizedBox(
                        width: 130,
                        child: Text(p['name_tr'] ?? '',
                            style: RythoText.body(14)),
                      ),
                      Text('${p['sign_tr']} ${p['symbol'] ?? ''}',
                          style: RythoText.body(14,
                              color: RythoColors.parchmentDim)),
                      const Spacer(),
                      if (p['retrograde'] == true)
                        Padding(
                          padding: const EdgeInsets.only(right: 8),
                          child: Text('R',
                              style:
                                  RythoText.mono(12, color: RythoColors.copper)),
                        ),
                      Text('${(p['position'] as num).toStringAsFixed(1)}°',
                          style: RythoText.mono(13)),
                    ]),
                  ),
              ]),
            ),
            Plaque(
              label: 'Levha III — Açılar',
              padding: EdgeInsets.zero,
              child: Column(children: [
                for (final a in aspects.take(12))
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    decoration: BoxDecoration(
                      border: a == aspects.take(12).last
                          ? null
                          : const Border(
                              bottom: BorderSide(color: RythoColors.line)),
                    ),
                    child: Row(children: [
                      Expanded(
                        child: Text(
                          '${a['p1_tr']} — ${a['p2_tr']}',
                          style: RythoText.body(13.5),
                        ),
                      ),
                      Text(a['aspect_tr'] ?? '',
                          style: RythoText.body(13.5,
                              color: RythoColors.parchmentDim)),
                      const SizedBox(width: 12),
                      Text('${(a['orbit'] as num).toStringAsFixed(1)}°',
                          style: RythoText.mono(12,
                              color: RythoColors.parchmentDim)),
                    ]),
                  ),
              ]),
            ),
            const SectionDivider(),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: MarginNote(
                title: 'Rytho\'nun okuma notu',
                text: data['report'] ?? '',
              ),
            ),
            const SizedBox(height: 32),
          ]);
        },
      ),
    );
  }
}

class _BigThree extends StatelessWidget {
  const _BigThree({required this.chart});
  final Map<String, dynamic> chart;

  @override
  Widget build(BuildContext context) {
    final items = [
      ('GÜNEŞ', chart['sun_sign'] ?? '—', 'öz kimlik'),
      ('AY', chart['moon_sign'] ?? '—', 'duygu dünyası'),
      ('YÜKSELEN', chart['ascendant'] ?? '—', 'dışa açılan kapı'),
    ];
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(children: [
        for (final item in items)
          Expanded(
            child: Container(
              margin: EdgeInsets.only(right: item == items.last ? 0 : 8),
              padding: const EdgeInsets.symmetric(vertical: 14),
              decoration: BoxDecoration(
                border: Border.all(color: RythoColors.line),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Column(children: [
                Text(item.$1,
                    style: RythoText.mono(10, color: RythoColors.parchmentDim)),
                const SizedBox(height: 6),
                Text(item.$2, style: RythoText.display(17)),
                const SizedBox(height: 4),
                Text(item.$3,
                    style:
                        RythoText.body(10.5, color: RythoColors.parchmentDim)),
              ]),
            ),
          ),
      ]),
    );
  }
}
