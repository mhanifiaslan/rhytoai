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
import '../face/face_reading_flow.dart';
import '../paywall/plus_locked_card.dart';
import '../../core/subscription.dart' show subscriptionProvider;
import '../../core/api.dart' show friendlyError;
import '../../l10n/app_localizations.dart';

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
    final l10n = AppLocalizations.of(context);
    final natal = ref.watch(natalReportProvider);
    final profile = ref.watch(profileProvider).value ?? {};

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(title: Text(l10n.atlasTitle)),
      // Yüz okuma girişi natal raporun DIŞINDA duruyor.
      //
      // Önce `data != null` dalının içindeydi; sonuç şuydu: natal rapor
      // kilitliyken ya da yüklenemezken firaset girişi de hiç görünmüyordu.
      // Oysa firaset natal rapordan bağımsız bir özellik — harita varsa
      // okumaya katılıyor, yoksa yalnız başına da çalışıyor.
      body: Column(children: [
        const Padding(
          padding: EdgeInsets.fromLTRB(16, 8, 16, 0),
          child: FaceReadingEntry(),
        ),
        Expanded(
          child: natal.when(
            loading: () => const Center(child: AstrolabeSpinner()),
            error: (e, _) => Center(
              child: Padding(
                padding: const EdgeInsets.all(32),
                child: Text(friendlyError(e, l10n),
                    style:
                        RythoText.body(14, color: RythoColors.parchmentDim)),
              ),
            ),
            data: (data) {
              if (data == null) {
                return PlusLockedCard(
                  emoji: '🗺️',
                  title: l10n.natalLockedTitle,
                  description: l10n.natalLockedBody,
                  centered: true,
                );
              }
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
                                      planetSignLabel(
                                          context, _selectedPlanet!),
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
                label: l10n.atlasPlanetPositions,
                child: _PlanetGrid(points: points),
              ).animate(delay: next()).fadeIn(duration: 380.ms).slideY(
                  begin: 0.06, curve: Curves.easeOutCubic),
              // Kişilik özellikleri — animasyonlu çubuklar
              GlassPanel(
                label: l10n.atlasTraits,
                child: _TraitBars(points: points),
              ).animate(delay: next()).fadeIn(duration: 380.ms).slideY(
                  begin: 0.06, curve: Curves.easeOutCubic),
              // Açılar (katlanır detay)
              _FoldSection(
                label: l10n.atlasAspects,
                initiallyOpen: false,
                child: Column(children: [
                  for (final a in aspects.take(14))
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 5),
                      child: Row(children: [
                        Expanded(
                          child: Text(aspectPairLabel(context, a),
                              style: RythoText.body(13)),
                        ),
                        Text(aspectKindLabel(context, a),
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
                label: l10n.atlasReadingNote,
                child: Text(data['report'] ?? '',
                    style: RythoText.body(14.5, height: 1.65)),
              ).animate(delay: next()).fadeIn(duration: 380.ms).slideY(
                  begin: 0.05, curve: Curves.easeOutCubic),
              const SizedBox(height: 16),
            ],
          );
            },
          ),
        ),
      ]),
    );
  }
}

/// Gezegen + burç etiketi, arayüz diline göre.
///
/// Backend her iki adı da döndürüyor (`name` İngilizce, `name_tr` Türkçe);
/// burç adı yalnızca Türkçe geldiği için indekse çevrilip yerelleştiriliyor.
String planetSignLabel(BuildContext context, Map<String, dynamic> p) {
  final l10n = AppLocalizations.of(context);
  final ingilizce = Localizations.localeOf(context).languageCode == 'en';
  final signIndex = kSignNamesTr.indexOf(p['sign_tr'] ?? '');
  final gezegen = (ingilizce ? p['name'] : p['name_tr']) ?? p['name'] ?? '';
  final burc = signIndex >= 0
      ? signDisplayName(l10n, signIndex)
      : (p['sign_tr'] ?? '');
  return '$gezegen — $burc';
}

/// Açıdaki iki gezegen: "Güneş — Satürn" / "Sun — Saturn".
///
/// Natal harita ucu her iki adı da döndürüyor (`p1` İngilizce, `p1_tr`).
String aspectPairLabel(BuildContext context, Map<String, dynamic> a) {
  final ingilizce = Localizations.localeOf(context).languageCode == 'en';
  final p1 = (ingilizce ? a['p1'] : a['p1_tr']) ?? a['p1'] ?? '';
  final p2 = (ingilizce ? a['p2'] : a['p2_tr']) ?? a['p2'] ?? '';
  return '$p1 — $p2';
}

/// Açı türü: "Kare" / "Square".
///
/// İngilizce alan kerykeion'dan küçük harfle geliyor ("square"), gösterirken
/// baş harfi büyütülür.
String aspectKindLabel(BuildContext context, Map<String, dynamic> a) {
  final ingilizce = Localizations.localeOf(context).languageCode == 'en';
  if (!ingilizce) return (a['aspect_tr'] ?? a['aspect'] ?? '').toString();
  final ham = (a['aspect'] ?? '').toString();
  if (ham.isEmpty) return '';
  return ham[0].toUpperCase() + ham.substring(1);
}

/// Firestore/backend'den gelen Türkçe burç adını ("Kova ♒") arayüz diline
/// çevirir; tanınmazsa geldiği gibi gösterilir.
String localizedSign(BuildContext context, Object? raw) {
  if (raw == null) return '—';
  final index = signIndexOf(raw.toString());
  if (index < 0) return raw.toString();
  return '${signDisplayName(AppLocalizations.of(context), index)} '
      '${kSignGlyphs[index]}';
}

/// Kişi kartı: ad, doğum tarihi/saati/yeri.
class _PersonCard extends StatelessWidget {
  const _PersonCard({required this.profile, required this.chart});
  final Map<String, dynamic> profile;
  final Map<String, dynamic> chart;

  /// Doğum tarihi, arayüz diline göre biçimlenir.
  ///
  /// Dil kodu sabit 'tr_TR' idi: İngilizce arayüzde ay adları Türkçe
  /// çıkıyordu ("12 Mayıs 1990").
  String _birthDateText(BuildContext context) {
    final raw = profile['birthDate'] as String?;
    if (raw == null) return '—';
    try {
      final dil = Localizations.localeOf(context).languageCode;
      return DateFormat.yMMMMd(dil).format(DateTime.parse(raw));
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
            Text(
                profile['displayName'] ??
                    AppLocalizations.of(context).defaultUserName,
                style: RythoText.body(16, w: FontWeight.w700)),
            const SizedBox(height: 4),
            Text(
              '${_birthDateText(context)} · 🕐 ${profile['birthTime'] ?? '—'} · 📍 ${profile['birthCity'] ?? '—'}',
              style: RythoText.body(12, color: RythoColors.parchmentDim),
            ),
          ]),
        ),
        Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
          Text('☀️ ${localizedSign(context, chart['sun_sign'])}',
              style: RythoText.body(12, w: FontWeight.w600)),
          const SizedBox(height: 2),
          Text('⬆️ ${localizedSign(context, chart['ascendant'])}',
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
            Expanded(child: _cell(context, majors[i])),
            const SizedBox(width: 8),
            Expanded(
                child: i + 1 < majors.length
                    ? _cell(context, majors[i + 1])
                    : const SizedBox()),
          ]),
        ),
    ]);
  }

  Widget _cell(BuildContext context, Map<String, dynamic> p) {
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
            '${planetSignLabel(context, p)} $glyph${retro ? ' ℞' : ''}',
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

    final l10n = AppLocalizations.of(context);
    final traits = [
      (l10n.traitEnergy, pct(fire), RythoColors.magenta),
      (l10n.traitDetermination, pct(fixed), RythoColors.gold),
      (l10n.traitCommunication, pct(air), RythoColors.lilac),
      (l10n.traitSensitivity, pct(water), const Color(0xFF5AC8FA)),
      (l10n.traitPracticality, pct(earth), RythoColors.celadon),
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

/// Yüz okuma giriş kartı.
///
/// Ücretli uca **istek atmadan** kilit gösteriyor: abone olmayan biri karta
/// dokununca paywall açılıyor, kamera hiç başlamıyor. Kamerayı açıp sonunda
/// 402 almak, kullanıcıya yüzünü boşuna taratmak olurdu.
class FaceReadingEntry extends ConsumerWidget {
  const FaceReadingEntry({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final abonelik = ref.watch(subscriptionProvider);
    final acik = abonelik.value?.active ?? false;

    if (!acik) {
      return PlusLockedCard(
        emoji: '👁️',
        title: l10n.faceReadingTitle,
        description: l10n.faceReadingLockedBody,
      );
    }

    return GlassPanel(
      onTap: () => startFaceReading(context, ref),
      child: Row(children: [
        const Text('👁️', style: TextStyle(fontSize: 20)),
        const SizedBox(width: 12),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(l10n.faceReadingTitle, style: RythoText.display(16)),
            const SizedBox(height: 3),
            Text(l10n.faceReadingEntryBody,
                style: RythoText.body(12.5, color: RythoColors.parchmentDim)),
          ]),
        ),
        const Icon(Icons.chevron_right_rounded,
            size: 18, color: RythoColors.parchmentDim),
      ]),
    );
  }
}
