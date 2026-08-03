/// Atlas'ın detay sayfaları: gezegenler, kişilik, açılar.
///
/// ## Neden ayrıldılar
///
/// Hepsi Atlas akışının içinde, alt alta duruyordu. Ölçülen ekran uzunluğu
/// ~2000 px'di ve kullanıcının tarifi şuydu:
///
/// > "atlas sayfası da tuhaf, profilimde olan bilgiler de var yüz okuma da
/// > var, aşağı doğru uzanan uzun metinler de var, kişilik özellikleri,
/// > gezegen konumları vs... herşey heryerde hissi var. tam bir kaos."
///
/// Teşhis "çok özellik var" değil, **hepsinin aynı seviyede durması**. Bir
/// bakışta görülecek çark ile üç dakika incelenecek açı tablosu tek sütunda
/// yan yanaydı. Artık Atlas bir dizin; her giriş kendi sayfasını açıyor.
///
/// Açı listesi burada **kırpılmıyor**. Akışta 14 taneyle sınırlıydı, çünkü
/// hepsi ekranı boğuyordu; kendi sayfasında böyle bir sebep yok.
library;

import 'package:flutter/material.dart';

import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import '../../theme/rytho_tokens.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/glass.dart';
import '../../widgets/nebula_widgets.dart';
import 'atlas_screen.dart'
    show aspectKindLabel, aspectPairLabel, planetSignLabel;

/// Detay sayfalarının ortak iskeleti.
class _DetayIskelet extends StatelessWidget {
  const _DetayIskelet({required this.title, required this.children});

  final String title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return CosmicScaffold(
      appBar: AppBar(title: Text(title)),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(RythoSpace.lg, RythoSpace.md,
              RythoSpace.lg, RythoSpace.xxl),
          children: children,
        ),
      ),
    );
  }
}

/// Gezegen konumları — 2 sütunlu çip ızgarası.
class AtlasPlanetsScreen extends StatelessWidget {
  const AtlasPlanetsScreen({super.key, required this.points});

  final List<Map<String, dynamic>> points;

  @override
  Widget build(BuildContext context) {
    return _DetayIskelet(
      title: AppLocalizations.of(context).atlasPlanetPositions,
      children: [GlassPanel(child: PlanetGrid(points: points))],
    );
  }
}

/// Kişilik özellikleri — element/nitelik dağılımından türetilen çubuklar.
class AtlasTraitsScreen extends StatelessWidget {
  const AtlasTraitsScreen({super.key, required this.points});

  final List<Map<String, dynamic>> points;

  @override
  Widget build(BuildContext context) {
    return _DetayIskelet(
      title: AppLocalizations.of(context).atlasTraits,
      children: [GlassPanel(child: TraitBars(points: points))],
    );
  }
}

/// Açılar — **tam** liste.
class AtlasAspectsScreen extends StatelessWidget {
  const AtlasAspectsScreen({super.key, required this.aspects});

  final List<Map<String, dynamic>> aspects;

  @override
  Widget build(BuildContext context) {
    return _DetayIskelet(
      title: AppLocalizations.of(context).atlasAspects,
      children: [
        GlassPanel(
          child: Column(children: [
            // Kırpma YOK: akışta 14 taneyle sınırlıydı, burada sebebi yok.
            for (final a in aspects)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 5),
                child: Row(children: [
                  Expanded(
                    child: Text(aspectPairLabel(context, a),
                        style: RythoType.body),
                  ),
                  Text(aspectKindLabel(context, a), style: RythoType.bodyDim),
                  const SizedBox(width: RythoSpace.md),
                  Text('${(a['orbit'] as num).toStringAsFixed(1)}°',
                      style: RythoType.dataSmall),
                ]),
              ),
          ]),
        ),
      ],
    );
  }
}

/// Gezegen konumları ızgarası (Güneş ☀️ — Aslan ♌ gibi).
class PlanetGrid extends StatelessWidget {
  const PlanetGrid({super.key, required this.points});

  final List<Map<String, dynamic>> points;

  static const _planetEmojis = {
    'Sun': '☀️', 'Moon': '🌙', 'Mercury': '☿', 'Venus': '♀', 'Mars': '♂',
    'Jupiter': '♃', 'Saturn': '♄', 'Uranus': '♅', 'Neptune': '♆', 'Pluto': '♇',
  };

  @override
  Widget build(BuildContext context) {
    final majors =
        points.where((p) => _planetEmojis.containsKey(p['name'])).toList();
    return Column(children: [
      for (var i = 0; i < majors.length; i += 2)
        Padding(
          padding: const EdgeInsets.symmetric(vertical: RythoSpace.xs),
          child: Row(children: [
            Expanded(child: _hucre(context, majors[i])),
            const SizedBox(width: RythoSpace.sm),
            Expanded(
                child: i + 1 < majors.length
                    ? _hucre(context, majors[i + 1])
                    : const SizedBox()),
          ]),
        ),
    ]);
  }

  Widget _hucre(BuildContext context, Map<String, dynamic> p) {
    final signIndex = kSignNamesTr.indexOf(p['sign_tr'] ?? '');
    final glyph = signIndex >= 0 ? kSignGlyphs[signIndex] : '';
    final retro = p['retrograde'] == true;
    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: RythoSpace.md, vertical: 9),
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
            style: RythoText.body(12),
          ),
        ),
      ]),
    );
  }
}

/// Kişilik çubukları — element ve nitelik dağılımından türetilir.
class TraitBars extends StatelessWidget {
  const TraitBars({super.key, required this.points});

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

    int pct(int count) => (30 + (count / total) * 140).round().clamp(20, 97);

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
