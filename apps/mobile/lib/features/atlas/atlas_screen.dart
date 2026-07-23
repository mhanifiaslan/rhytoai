import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../core/providers.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/glass.dart';
import '../../widgets/natal_wheel.dart';
import '../../widgets/nebula_widgets.dart';

/// ATLAS — Doğum Haritası Analizi v3: natal çark kartı, kişi kartı,
/// gezegen konumları grid'i, animasyonlu kişilik çubukları ve derin AI raporu.
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
    final profile = ref.watch(profileProvider).value ?? {};

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(title: const Text('Doğum Haritası Analizi')),
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

          var stagger = 0;
          Duration next() => Duration(milliseconds: 70 * stagger++);

          return ListView(
            padding: const EdgeInsets.only(bottom: 130),
            children: [
              const SizedBox(height: 8),
              // Natal çark
              GlassPanel(
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
                              color: RythoColors.inkLighter,
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(
                                  color: RythoColors.lilac
                                      .withValues(alpha: 0.3)),
                            ),
                            child: Row(children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      '${_selectedPlanet!['name_tr']} — ${_selectedPlanet!['sign_tr']}',
                                      style: RythoText.body(15,
                                          w: FontWeight.w700),
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
              ).animate(delay: next()).fadeIn(duration: 380.ms).slideY(
                  begin: 0.06, curve: Curves.easeOutCubic),
              // Kişi kartı
              _PersonCard(profile: profile, chart: chart)
                  .animate(delay: next())
                  .fadeIn(duration: 380.ms)
                  .slideY(begin: 0.06, curve: Curves.easeOutCubic),
              // Gezegen konumları
              GlassPanel(
                label: 'Gezegen Konumları',
                child: _PlanetGrid(points: points),
              ).animate(delay: next()).fadeIn(duration: 380.ms).slideY(
                  begin: 0.06, curve: Curves.easeOutCubic),
              // Kişilik özellikleri — animasyonlu çubuklar
              GlassPanel(
                label: 'Kişilik Özellikleri',
                child: _TraitBars(points: points),
              ).animate(delay: next()).fadeIn(duration: 380.ms).slideY(
                  begin: 0.06, curve: Curves.easeOutCubic),
              // Açılar (katlanır detay)
              _FoldSection(
                label: 'Açılar',
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
              ).animate(delay: next()).fadeIn(duration: 380.ms),
              const SectionDivider(),
              // Tam AI raporu
              GlassPanel(
                label: '✨ Rytho\'nun okuma notu',
                child: Text(data['report'] ?? '',
                    style: RythoText.body(14.5, height: 1.65)),
              ).animate(delay: next()).fadeIn(duration: 380.ms).slideY(
                  begin: 0.05, curve: Curves.easeOutCubic),
              const SizedBox(height: 16),
            ],
          );
        },
      ),
    );
  }
}

/// Kişi kartı: ad, doğum tarihi/saati/yeri.
class _PersonCard extends StatelessWidget {
  const _PersonCard({required this.profile, required this.chart});
  final Map<String, dynamic> profile;
  final Map<String, dynamic> chart;

  String get _birthDateText {
    final raw = profile['birthDate'] as String?;
    if (raw == null) return '—';
    try {
      return DateFormat('d MMMM yyyy', 'tr_TR').format(DateTime.parse(raw));
    } catch (_) {
      return raw;
    }
  }

  @override
  Widget build(BuildContext context) {
    return GlassPanel(
      child: Row(children: [
        Container(
          padding: const EdgeInsets.all(2),
          decoration: const BoxDecoration(
            shape: BoxShape.circle,
            gradient: RythoColors.primaryGradient,
          ),
          child: CircleAvatar(
            radius: 22,
            backgroundColor: RythoColors.inkLight,
            backgroundImage: profile['photoUrl'] != null
                ? NetworkImage(profile['photoUrl'])
                : null,
            child: profile['photoUrl'] == null
                ? Text('☽', style: RythoText.display(16))
                : null,
          ),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(profile['displayName'] ?? 'Gezgin',
                style: RythoText.body(16, w: FontWeight.w700)),
            const SizedBox(height: 4),
            Text(
              '$_birthDateText · 🕐 ${profile['birthTime'] ?? '—'} · 📍 ${profile['birthCity'] ?? '—'}',
              style: RythoText.body(12, color: RythoColors.parchmentDim),
            ),
          ]),
        ),
        Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
          Text('☀️ ${chart['sun_sign'] ?? '—'}',
              style: RythoText.body(12, w: FontWeight.w600)),
          const SizedBox(height: 2),
          Text('⬆️ ${chart['ascendant'] ?? '—'}',
              style: RythoText.body(12, color: RythoColors.parchmentDim)),
        ]),
      ]),
    );
  }
}

/// Gezegen konumları: 2 sütunlu çip grid'i (Güneş ☀️ – Aslan ♌ gibi).
class _PlanetGrid extends StatelessWidget {
  const _PlanetGrid({required this.points});
  final List<Map<String, dynamic>> points;

  static const _planetEmojis = {
    'Sun': '☀️', 'Moon': '🌙', 'Mercury': '☿', 'Venus': '♀', 'Mars': '♂',
    'Jupiter': '♃', 'Saturn': '♄', 'Uranus': '♅', 'Neptune': '♆', 'Pluto': '♇',
  };

  @override
  Widget build(BuildContext context) {
    final majors = points
        .where((p) => _planetEmojis.containsKey(p['name']))
        .toList();
    return Column(children: [
      for (var i = 0; i < majors.length; i += 2)
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: Row(children: [
            Expanded(child: _cell(majors[i])),
            const SizedBox(width: 8),
            Expanded(
                child: i + 1 < majors.length
                    ? _cell(majors[i + 1])
                    : const SizedBox()),
          ]),
        ),
    ]);
  }

  Widget _cell(Map<String, dynamic> p) {
    final signIndex = kSignNamesTr.indexOf(p['sign_tr'] ?? '');
    final glyph = signIndex >= 0 ? kSignGlyphs[signIndex] : '';
    final retro = p['retrograde'] == true;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
      decoration: BoxDecoration(
        color: RythoColors.inkLighter,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
            color: retro
                ? RythoColors.magenta.withValues(alpha: 0.4)
                : RythoColors.glassStroke),
      ),
      child: Row(children: [
        Text(_planetEmojis[p['name']] ?? '•',
            style: const TextStyle(fontSize: 14)),
        const SizedBox(width: 7),
        Expanded(
          child: Text(
            '${p['name_tr']} – ${p['sign_tr']} $glyph${retro ? ' ℞' : ''}',
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: RythoText.body(12, w: FontWeight.w600),
          ),
        ),
      ]),
    );
  }
}

/// Kişilik özellikleri: natal noktaların element/nitelik dağılımından
/// DETERMİNİSTİK türetilen 5 çubuk. Eşleme (uydurma ama tutarlı):
/// - Enerji      → ateş burçlarındaki gezegen oranı
/// - Pratiklik   → toprak oranı
/// - İletişim    → hava oranı
/// - Duyarlılık  → su oranı
/// - Kararlılık  → sabit (fixed) nitelik oranı
/// Yüzde = 30 + oran×140 (20–97 aralığına kırpılır) — böylece tipik
/// dağılımlar 35-75 bandında, baskın özellikler 80+ görünür.
class _TraitBars extends StatelessWidget {
  const _TraitBars({required this.points});
  final List<Map<String, dynamic>> points;

  @override
  Widget build(BuildContext context) {
    var fire = 0, earth = 0, air = 0, water = 0, fixed = 0, total = 0;
    for (final p in points) {
      final lon = (p['abs_position'] as num?)?.toDouble();
      if (lon == null) continue;
      final sign = (lon ~/ 30) % 12;
      total++;
      switch (sign % 4) {
        case 0: fire++;
        case 1: earth++;
        case 2: air++;
        case 3: water++;
      }
      if (sign % 3 == 1) fixed++; // Boğa, Aslan, Akrep, Kova
    }
    if (total == 0) total = 1;

    int pct(int count) =>
        (30 + (count / total) * 140).round().clamp(20, 97);

    final traits = [
      ('Enerji', pct(fire), RythoColors.magenta),
      ('Kararlılık', pct(fixed), RythoColors.gold),
      ('İletişim', pct(air), RythoColors.lilac),
      ('Duyarlılık', pct(water), const Color(0xFF5AC8FA)),
      ('Pratiklik', pct(earth), RythoColors.celadon),
    ];

    return Column(children: [
      for (final (i, t) in traits.indexed)
        GradientProgressBar(
          label: t.$1,
          percent: t.$2,
          color: t.$3,
          delay: Duration(milliseconds: 120 * i),
        ),
    ]);
  }
}

/// Katlanabilir bölüm.
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
              Text(widget.label,
                  style: RythoText.label(11, color: RythoColors.parchmentDim)),
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
