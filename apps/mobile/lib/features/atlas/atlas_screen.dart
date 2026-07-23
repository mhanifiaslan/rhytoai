import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/glass.dart';
import '../../widgets/natal_wheel.dart';

/// ATLAS — doğum haritası: Büyük Üçlü, yerli çizim natal çark,
/// gezegen cetveli, açılar ve derin AI raporu.
class AtlasScreen extends ConsumerStatefulWidget {
  const AtlasScreen({super.key});

  @override
  ConsumerState<AtlasScreen> createState() => _AtlasScreenState();
}

class _AtlasScreenState extends ConsumerState<AtlasScreen> {
  Map<String, dynamic>? _selectedPlanet;

  @override
  Widget build(BuildContext context) {
    final natal = ref.watch(natalReportProvider);

    return Scaffold(
      backgroundColor: Colors.transparent,
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
          final houses = List<Map<String, dynamic>>.from(chart['houses'] ?? []);
          final aspects = List<Map<String, dynamic>>.from(chart['aspects'] ?? []);

          return ListView(
            padding: const EdgeInsets.only(bottom: 110),
            children: [
              const SizedBox(height: 8),
              _BigThree(chart: chart)
                  .animate()
                  .fadeIn(duration: 400.ms)
                  .slideY(begin: 0.06, curve: Curves.easeOutCubic),
              GlassPanel(
                label: 'Gök Çarkı — dokunarak keşfet',
                padding: const EdgeInsets.all(8),
                child: Column(children: [
                  Center(
                    child: NatalWheel(
                      points: points,
                      houses: houses,
                      aspects: aspects,
                      size: MediaQuery.of(context).size.width - 72,
                      onPlanetTap: (p) => setState(() => _selectedPlanet = p),
                    ),
                  ),
                  AnimatedSize(
                    duration: const Duration(milliseconds: 260),
                    curve: Curves.easeOutCubic,
                    child: _selectedPlanet == null
                        ? const SizedBox(width: double.infinity)
                        : Container(
                            width: double.infinity,
                            margin: const EdgeInsets.fromLTRB(8, 4, 8, 8),
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: RythoColors.inkLighter.withValues(alpha: 0.7),
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: RythoColors.glassEdge),
                            ),
                            child: Row(children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      '${_selectedPlanet!['name_tr']} — ${_selectedPlanet!['sign_tr']}',
                                      style: RythoText.body(15,
                                          w: FontWeight.w600),
                                    ),
                                    Text(
                                      '${(_selectedPlanet!['position'] as num).toStringAsFixed(1)}°'
                                      '${_selectedPlanet!['house'] != null ? ' · ${_selectedPlanet!['house']}' : ''}'
                                      '${_selectedPlanet!['retrograde'] == true ? ' · retro' : ''}',
                                      style: RythoText.mono(12,
                                          color: RythoColors.parchmentDim),
                                    ),
                                  ],
                                ),
                              ),
                              IconButton(
                                icon: const Icon(Icons.close,
                                    size: 16, color: RythoColors.parchmentDim),
                                onPressed: () =>
                                    setState(() => _selectedPlanet = null),
                              ),
                            ]),
                          ),
                  ),
                ]),
              ),
              _FoldSection(
                label: 'Levha II — Gezegen Cetveli',
                child: Column(children: [
                  for (final p in points)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 6),
                      child: Row(children: [
                        SizedBox(
                          width: 132,
                          child:
                              Text(p['name_tr'] ?? '', style: RythoText.body(13.5)),
                        ),
                        Text('${p['sign_tr']} ${p['symbol'] ?? ''}',
                            style: RythoText.body(13.5,
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
              _FoldSection(
                label: 'Levha III — Açılar',
                initiallyOpen: false,
                child: Column(children: [
                  for (final a in aspects.take(14))
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 5),
                      child: Row(children: [
                        Expanded(
                          child: Text('${a['p1_tr']} — ${a['p2_tr']}',
                              style: RythoText.body(13)),
                        ),
                        Text(a['aspect_tr'] ?? '',
                            style: RythoText.body(13,
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
              GlassPanel(
                label: 'Rytho\'nun okuma notu',
                child: Text(data['report'] ?? '',
                    style: RythoText.body(15, height: 1.65)),
              ),
              const SizedBox(height: 16),
            ],
          );
        },
      ),
    );
  }
}

/// Katlanabilir cam bölüm.
class _FoldSection extends StatefulWidget {
  const _FoldSection({
    required this.label,
    required this.child,
    this.initiallyOpen = true,
  });

  final String label;
  final Widget child;
  final bool initiallyOpen;

  @override
  State<_FoldSection> createState() => _FoldSectionState();
}

class _FoldSectionState extends State<_FoldSection> {
  late bool _open = widget.initiallyOpen;

  @override
  Widget build(BuildContext context) {
    return GlassPanel(
      padding: EdgeInsets.zero,
      child: Column(children: [
        InkWell(
          onTap: () => setState(() => _open = !_open),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
            child: Row(children: [
              Text(widget.label.toUpperCase(),
                  style: RythoText.mono(11, color: RythoColors.parchmentDim)),
              const Spacer(),
              AnimatedRotation(
                turns: _open ? 0.5 : 0,
                duration: const Duration(milliseconds: 260),
                child: const Icon(Icons.keyboard_arrow_down,
                    size: 18, color: RythoColors.parchmentDim),
              ),
            ]),
          ),
        ),
        AnimatedSize(
          duration: const Duration(milliseconds: 280),
          curve: Curves.easeOutCubic,
          alignment: Alignment.topCenter,
          child: _open
              ? Padding(
                  padding: const EdgeInsets.fromLTRB(16, 0, 16, 14),
                  child: widget.child,
                )
              : const SizedBox(width: double.infinity),
        ),
      ]),
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
                color: RythoColors.glassFill,
                border: Border.all(color: RythoColors.glassStroke),
                borderRadius: BorderRadius.circular(14),
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
