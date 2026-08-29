/// Harita İnceleme (HI-turu HA7) — astrolog gözü için tam ekran çark.
///
/// Dört kip tek ekranda: natal | gökyüzü | bi-wheel | sinastri (Çevrem).
/// İçerik: veri başlığı (ad/tarih/ev sistemi — güven, ev sistemini
/// görmekle başlar), lejant, filtre çipleri + orb kaydırıcısı, etkileşimli
/// çark (dokun→seç/izole, tekrar dokun→alt-sayfa, pinch-zoom), açı
/// tablosu (aspectarian: tekilde üçgen, sinastride TAM dikdörtgen),
/// konum tablosu (erişilebilir temsil), "Rytho'ya sor" ve PNG paylaşım.
///
/// "Ölçülmeyen söylenmez": saatsiz haritada evler/eksenler çizilmez ve
/// beyan görünür; transit gezegene ev iddia edilmez; arkadaş sinastri
/// çarkı bilinçli yok (kullanıcı kararı — Çevrem v1).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/people.dart';
import '../../core/providers.dart';
import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import '../../theme/rytho_tokens.dart';
import '../../widgets/chart/chart_data.dart';
import '../../widgets/chart/chart_palette.dart';
import '../../widgets/chart/chart_wheel.dart';
import '../../widgets/chart/wheel_glyphs.dart';
import '../../widgets/chart/wheel_layout.dart';
import '../../widgets/chart/wheel_painter.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/glass.dart';
import '../../widgets/motion.dart' show StagedWaiting;
import '../../widgets/nebula_widgets.dart'
    show kSignNamesTr, signDisplayName;
import '../chat/chat_screen.dart';
import '../people/person_form_screen.dart' show relationLabel;
import '../share/share_card.dart' show shareRenderedCard;
import 'atlas_detail_screens.dart' show showAspectSheet, showPointSheet;

enum ChartInspectorMode { natal, sky, biwheel, synastry }

/// [ChartPoint] → mevcut `showPointSheet` yükü (atlas alt-sayfa ailesi
/// `sign_tr`/`name_tr` alanlarını okur — planetSignLabel sözleşmesi).
Map<String, dynamic> pointSheetMap(ChartPoint p) => {
      'name': p.name,
      'name_tr': p.localName,
      'name_local': p.localName,
      'sign': kSignCodes[p.signIndex],
      'sign_tr': kSignNamesTr[p.signIndex],
      'position': p.degreeInSign,
      'abs_position': p.absPosition,
      'house_no': p.houseNo,
      'retrograde': p.retrograde,
      'speed': p.speed,
    };

/// [ChartAspect] → mevcut `showAspectSheet` yükü.
Map<String, dynamic> aspectSheetMap(ChartAspect a) => {
      'p1': a.p1,
      'p2': a.p2,
      'p1_tr': a.p1Local,
      'p2_tr': a.p2Local,
      'aspect': a.kind,
      'aspect_tr': a.kindLocal,
      'orbit': a.orb,
      if (a.applying != null)
        'movement': a.applying! ? 'applying' : 'separating',
    };

class ChartInspectorScreen extends ConsumerStatefulWidget {
  const ChartInspectorScreen({
    super.key,
    required this.mode,
    this.person,
    this.natalOverride,
    this.titleOverride,
  });

  final ChartInspectorMode mode;

  /// Sinastri kipinde zorunlu; natal kipinde doluysa KİŞİNİN haritası
  /// incelenir (kendi haritası yerine).
  final Person? person;

  /// Kişi detayından gelen hazır natal yükü (yeniden istek atılmaz).
  final Map<String, dynamic>? natalOverride;

  final String? titleOverride;

  @override
  ConsumerState<ChartInspectorScreen> createState() =>
      _ChartInspectorScreenState();
}

class _ChartInspectorScreenState
    extends ConsumerState<ChartInspectorScreen> {
  late WheelAspectFilter _filter = switch (widget.mode) {
    // Karar 3: natal/gökyüzünde Tümü, çift halkalılarda Majör.
    ChartInspectorMode.biwheel ||
    ChartInspectorMode.synastry =>
      WheelAspectFilter.major,
    _ => WheelAspectFilter.all,
  };
  late double _maxOrb = switch (widget.mode) {
    ChartInspectorMode.biwheel => 3.0,
    ChartInspectorMode.synastry => 4.0,
    _ => 8.0,
  };
  bool _showMinors = false;
  bool _housesInner = true; // sinastri: evler A(sen)/B(kişi)
  WheelSelection _selection = WheelSelection.none;

  // ---------------------------------------------------------------------
  // Veri kurulumu
  // ---------------------------------------------------------------------

  /// (veri, yükleniyor-mu). Yükleniyorsa bi-wheel SESSİZCE tek halkaya
  /// düşmez (eski atlas kusuru) — bekleme durumu gösterilir.
  (ChartData?, bool) _buildData(AppLocalizations l10n) {
    final sen = l10n.chartLegendYou;
    switch (widget.mode) {
      case ChartInspectorMode.natal:
        if (widget.natalOverride != null) {
          return (
            ChartData.fromNatal(widget.natalOverride!, label: _personAd()),
            false
          );
        }
        final natal = ref.watch(natalChartProvider);
        if (natal.isLoading) return (null, true);
        final veri = natal.value;
        return (
          veri == null ? null : ChartData.fromNatal(veri, label: sen),
          false
        );
      case ChartInspectorMode.sky:
        final sky = ref.watch(skyNowProvider);
        if (sky.isLoading) return (null, true);
        final veri = sky.value;
        return (
          veri == null
              ? null
              : ChartData.fromSky(veri, label: l10n.chartLegendSkyNow),
          false
        );
      case ChartInspectorMode.biwheel:
        final natal = ref.watch(natalChartProvider);
        final transits = ref.watch(transitsProvider);
        if (natal.isLoading || transits.isLoading) return (null, true);
        if (natal.value == null || transits.value == null) {
          return (null, false);
        }
        return (
          ChartData.fromTransits(natal.value!, transits.value!,
              innerLabel: sen, outerLabel: l10n.chartLegendSkyNow),
          false
        );
      case ChartInspectorMode.synastry:
        final synastry =
            ref.watch(synastryChartProvider(widget.person!));
        if (synastry.isLoading) return (null, true);
        if (synastry.value == null) return (null, false);
        return (
          ChartData.fromSynastry(synastry.value!,
              innerLabel: sen,
              outerLabel: _personAd(),
              useInnerHouses: _housesInner),
          false
        );
    }
  }

  String _personAd() {
    final l10n = AppLocalizations.of(context);
    final p = widget.person;
    if (p == null) return '';
    return p.label ?? relationLabel(l10n, p.relation);
  }

  String _baslik(AppLocalizations l10n) {
    if (widget.titleOverride != null) return widget.titleOverride!;
    return switch (widget.mode) {
      ChartInspectorMode.natal => l10n.atlasWheelNatal,
      ChartInspectorMode.sky => l10n.atlasWheelSky,
      ChartInspectorMode.biwheel => l10n.atlasWheelBiwheel,
      ChartInspectorMode.synastry =>
        l10n.chartModeSynastry(_personAd()),
    };
  }

  // ---------------------------------------------------------------------
  // Etkileşim
  // ---------------------------------------------------------------------

  void _onPlanetTap(GlyphPlacement g) {
    final ayni = _selection.pointName == g.point.name &&
        _selection.pointRing == g.ring;
    if (ayni) {
      // İkinci dokunuş: ortak alt-sayfa ailesi (atlas listeleriyle aynı).
      showPointSheet(context, _pointAsMap(g.point));
      return;
    }
    setState(() => _selection =
        WheelSelection(pointName: g.point.name, pointRing: g.ring));
  }

  void _onAspectTap(ChartAspect a) {
    final ayni = _selection.aspect?.p1 == a.p1 &&
        _selection.aspect?.p2 == a.p2 &&
        _selection.aspect?.kind == a.kind;
    if (ayni) {
      showAspectSheet(context, _aspectAsMap(a));
      return;
    }
    setState(() => _selection = WheelSelection(aspect: a));
  }

  Map<String, dynamic> _pointAsMap(ChartPoint p) => pointSheetMap(p);

  Map<String, dynamic> _aspectAsMap(ChartAspect a) => aspectSheetMap(a);

  Future<void> _paylas(ChartData data) async {
    const boyut = 700.0;
    await shareRenderedCard(
      context,
      Container(
        color: RythoColors.ink,
        padding: const EdgeInsets.all(30),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          ChartWheel(
              data: data,
              size: boyut - 60,
              interactive: false,
              animate: false,
              filter: _filter,
              maxOrb: _maxOrb,
              showMinors: _showMinors),
          const SizedBox(height: 10),
          Text('RYTHO',
              style: RythoText.label(13, color: RythoColors.lilac)),
        ]),
      ),
      const Size(boyut, boyut + 40),
    );
  }

  void _sor(AppLocalizations l10n) {
    Navigator.of(context).push(MaterialPageRoute(
        builder: (_) => ChatScreen(
              personId: widget.mode == ChartInspectorMode.synastry
                  ? widget.person?.id
                  : null,
              initialText: l10n.chartAskPrefill(_baslik(l10n)),
            )));
  }

  // ---------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final (veri, yukleniyor) = _buildData(l10n);
    final genislik = MediaQuery.of(context).size.width;
    final carkBoyu = (genislik - RythoSpace.xl * 2).clamp(280.0, 460.0);

    return CosmicScaffold(
      appBar: AppBar(
        title: Text(_baslik(l10n)),
        actions: [
          if (veri != null)
            IconButton(
              tooltip: l10n.chartShareTooltip,
              icon: const Icon(Icons.ios_share_rounded, size: 20),
              onPressed: () => _paylas(veri),
            ),
        ],
      ),
      body: yukleniyor
          ? Center(
              child: StagedWaiting(stages: [l10n.chartOuterLoading]))
          : veri == null
              ? const SizedBox.shrink()
              : ListView(
                  padding: const EdgeInsets.fromLTRB(RythoSpace.xl, 0,
                      RythoSpace.xl, RythoSpace.xxl),
                  children: [
                    _Baslik(mode: widget.mode, data: veri,
                        personAd: _personAd()),
                    if (!veri.hourKnown &&
                        widget.mode != ChartInspectorMode.sky)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: Text(l10n.chartHourUnknownNote,
                            style: RythoText.body(11.5,
                                color: RythoColors.copper)),
                      ),
                    // Dokunulan yeri temizlemek için çark dışına dokunma.
                    GestureDetector(
                      onTap: _selection.isEmpty
                          ? null
                          : () => setState(
                              () => _selection = WheelSelection.none),
                      child: Center(
                        child: ChartWheel(
                          data: veri,
                          size: carkBoyu,
                          filter: _filter,
                          maxOrb: _maxOrb,
                          showMinors: _showMinors,
                          selection: _selection,
                          onPlanetTap: _onPlanetTap,
                          onAspectTap: _onAspectTap,
                        ),
                      ),
                    ),
                    _SecimCubugu(
                        selection: _selection,
                        data: veri,
                        onDetail: () {
                          if (_selection.aspect != null) {
                            showAspectSheet(
                                context, _aspectAsMap(_selection.aspect!));
                          } else if (_selection.pointName != null) {
                            final p = veri.resolve(_selection.pointName!,
                                _selection.pointRing ?? 0);
                            if (p != null) {
                              showPointSheet(context, _pointAsMap(p));
                            }
                          }
                        }),
                    _Lejant(data: veri),
                    const SizedBox(height: RythoSpace.md),
                    _FiltreCubugu(
                      filter: _filter,
                      maxOrb: _maxOrb,
                      showMinors: _showMinors,
                      onFilter: (f) => setState(() => _filter = f),
                      onOrb: (o) => setState(() => _maxOrb = o),
                      onMinors: (v) => setState(() => _showMinors = v),
                    ),
                    if (widget.mode == ChartInspectorMode.synastry &&
                        (widget.person?.hourKnown ?? false))
                      Padding(
                        padding: const EdgeInsets.only(top: 6),
                        child: Align(
                          alignment: Alignment.centerLeft,
                          child: FilterChip(
                            label: Text(_housesInner
                                ? l10n.chartHousesYou
                                : l10n.chartHousesOther(_personAd())),
                            selected: !_housesInner,
                            onSelected: (_) => setState(
                                () => _housesInner = !_housesInner),
                          ),
                        ),
                      ),
                    const SizedBox(height: RythoSpace.lg),
                    _Aspectarian(
                        data: veri,
                        filter: _filter,
                        maxOrb: _maxOrb,
                        showMinors: _showMinors),
                    const SizedBox(height: RythoSpace.lg),
                    _KonumTablosu(data: veri),
                    const SizedBox(height: RythoSpace.lg),
                    OutlinedButton.icon(
                      onPressed: () => _sor(l10n),
                      icon: const Text('✦',
                          style: TextStyle(fontSize: 14)),
                      label: Text(l10n.signalAsk),
                    ),
                  ],
                ),
    );
  }
}

// ---------------------------------------------------------------------------
// Parçalar
// ---------------------------------------------------------------------------

/// Veri başlığı: kim/ne zaman + ev sistemi (astrolog önce bunu okur).
class _Baslik extends ConsumerWidget {
  const _Baslik(
      {required this.mode, required this.data, required this.personAd});

  final ChartInspectorMode mode;
  final ChartData data;
  final String personAd;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final satirlar = <String>[];

    if (mode == ChartInspectorMode.sky) {
      final sky = ref.watch(skyNowProvider).value;
      final iso = sky?['timestamp_utc'] as String?;
      final t = iso == null ? null : DateTime.tryParse(iso)?.toLocal();
      if (t != null) {
        String iki(int n) => n.toString().padLeft(2, '0');
        satirlar.add(l10n.chartAsOf(
            '${iki(t.day)}.${iki(t.month)} ${iki(t.hour)}:${iki(t.minute)}'));
      }
    } else {
      final profil = ref.watch(profileProvider).value ?? {};
      final ad = mode == ChartInspectorMode.natal && personAd.isNotEmpty
          ? personAd
          : (profil['displayName'] as String? ?? '');
      final dogum = mode == ChartInspectorMode.natal && personAd.isNotEmpty
          ? null
          : profil['birthDate'] as String?;
      final sehir = mode == ChartInspectorMode.natal && personAd.isNotEmpty
          ? null
          : profil['birthCity'] as String?;
      satirlar.add([ad, dogum, sehir]
          .where((s) => s != null && s.isNotEmpty)
          .join(' · '));
    }
    if (data.hourKnown) satirlar.add(l10n.chartHouseSystem);

    return Padding(
      padding: const EdgeInsets.only(top: 6, bottom: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          for (final s in satirlar.where((s) => s.isNotEmpty))
            Text(s,
                style: RythoText.mono(10.5,
                    color: RythoColors.parchmentDim)),
        ],
      ),
    );
  }
}

/// Halkaları adlandıran lejant — adsız bi-wheel'e astrolog güvenmez.
class _Lejant extends StatelessWidget {
  const _Lejant({required this.data});

  final ChartData data;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    Widget rozet(Color renk, String metin) =>
        Row(mainAxisSize: MainAxisSize.min, children: [
          Container(
              width: 9,
              height: 9,
              decoration:
                  BoxDecoration(color: renk, shape: BoxShape.circle)),
          const SizedBox(width: 6),
          Text(metin,
              style:
                  RythoText.body(11.5, color: RythoColors.parchmentDim)),
        ]);

    return Padding(
      padding: const EdgeInsets.only(top: RythoSpace.md),
      child: Wrap(spacing: RythoSpace.lg, runSpacing: 4, children: [
        rozet(kInnerGlyphColor,
            l10n.chartLegendInner(data.rings.first.label)),
        if (data.isBiWheel)
          rozet(
              data.rings[1].kind == ChartRingKind.partner
                  ? kOuterPartnerColor
                  : kOuterTransitColor,
              l10n.chartLegendOuter(data.rings[1].label)),
      ]),
    );
  }
}

/// Seçili gezegen/açı bilgisi + "Detay →".
class _SecimCubugu extends StatelessWidget {
  const _SecimCubugu(
      {required this.selection,
      required this.data,
      required this.onDetail});

  final WheelSelection selection;
  final ChartData data;
  final VoidCallback onDetail;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    if (selection.isEmpty) return const SizedBox.shrink();

    String metin;
    if (selection.aspect != null) {
      final a = selection.aspect!;
      final hareket = a.applying == null
          ? ''
          : ' · ${a.applying! ? l10n.chartApplyingLetter : l10n.chartSeparatingLetter}';
      metin =
          '${a.localLabel ?? '${a.p1} ${a.kind} ${a.p2}'} · orb ${a.orb.toStringAsFixed(1)}°$hareket';
    } else {
      final p = data.resolve(
          selection.pointName!, selection.pointRing ?? 0);
      if (p == null) return const SizedBox.shrink();
      metin =
          '${p.localName} · ${p.degreeInSign.toStringAsFixed(1)}°'
          '${p.houseNo != null ? ' · ${l10n.houseN(p.houseNo!)}' : ''}';
    }

    return Padding(
      padding: const EdgeInsets.only(top: RythoSpace.sm),
      child: GlassPanel(
        child: Row(children: [
          Expanded(
              child: Text(metin,
                  style: RythoText.mono(11.5,
                      color: RythoColors.parchment))),
          TextButton(
              onPressed: onDetail,
              child: Text(l10n.chartSelectedDetail,
                  style: RythoText.label(11,
                      color: RythoColors.goldBright))),
        ]),
      ),
    );
  }
}

/// Filtre çipleri + orb kaydırıcısı.
class _FiltreCubugu extends StatelessWidget {
  const _FiltreCubugu({
    required this.filter,
    required this.maxOrb,
    required this.showMinors,
    required this.onFilter,
    required this.onOrb,
    required this.onMinors,
  });

  final WheelAspectFilter filter;
  final double maxOrb;
  final bool showMinors;
  final ValueChanged<WheelAspectFilter> onFilter;
  final ValueChanged<double> onOrb;
  final ValueChanged<bool> onMinors;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final adlar = {
      WheelAspectFilter.all: l10n.chartFilterAll,
      WheelAspectFilter.major: l10n.chartFilterMajor,
      WheelAspectFilter.applying: l10n.chartFilterApplying,
      WheelAspectFilter.hard: l10n.chartFilterHard,
      WheelAspectFilter.soft: l10n.chartFilterSoft,
    };
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Wrap(spacing: 8, runSpacing: 6, children: [
        for (final e in adlar.entries)
          ChoiceChip(
            label: Text(e.value),
            selected: filter == e.key,
            onSelected: (_) => onFilter(e.key),
            labelStyle: RythoText.label(11,
                color: filter == e.key
                    ? RythoColors.parchment
                    : RythoColors.parchmentDim),
          ),
        FilterChip(
          label: Text(l10n.chartFilterMinors),
          selected: showMinors,
          onSelected: onMinors,
          labelStyle: RythoText.label(11,
              color: showMinors
                  ? RythoColors.parchment
                  : RythoColors.parchmentDim),
        ),
      ]),
      Row(children: [
        Text(l10n.chartOrbLabel(maxOrb.round()),
            style: RythoText.mono(11, color: RythoColors.parchmentDim)),
        Expanded(
          child: Slider(
            value: maxOrb,
            min: 1,
            max: 8,
            divisions: 7,
            onChanged: onOrb,
          ),
        ),
      ]),
    ]);
  }
}

/// Aspectarian: tekil haritada alt-üçgen, sinastride TAM dikdörtgen
/// (satır = iç halka, sütun = dış halka). Hücre: açı glifi + orb + Y/A.
class _Aspectarian extends StatelessWidget {
  const _Aspectarian(
      {required this.data,
      required this.filter,
      required this.maxOrb,
      required this.showMinors});

  final ChartData data;
  final WheelAspectFilter filter;
  final double maxOrb;
  final bool showMinors;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final cross = data.isBiWheel;
    final satirlar = data.rings.first.points;
    final sutunlar = cross ? data.rings[1].points : satirlar;

    // (satır adı, sütun adı) → açı.
    final hucre = <(String, String), ChartAspect>{};
    for (final a in data.aspects) {
      if (!aspectVisible(a, filter, maxOrb, showMinors: showMinors)) {
        continue;
      }
      if (cross) {
        // p1 iç halkada olacak şekilde normalize et.
        if (a.p1Ring == 0) {
          hucre[(a.p1, a.p2)] = a;
        } else {
          hucre[(a.p2, a.p1)] = a;
        }
      } else {
        hucre[(a.p1, a.p2)] = a;
        hucre[(a.p2, a.p1)] = a;
      }
    }
    if (hucre.isEmpty) return const SizedBox.shrink();

    const kenar = 34.0;
    Widget baslikHucre(ChartPoint p, Color renk) => SizedBox(
          width: kenar,
          height: kenar,
          child: Center(
            child: kPlanetTextGlyphs.containsKey(p.name)
                ? Text(kPlanetTextGlyphs[p.name]!,
                    style: RythoText.body(13, color: renk))
                : CustomPaint(
                    size: const Size(13, 13),
                    painter: _MiniGlifPainter(p.name, renk)),
          ),
        );

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(l10n.chartAspectarianTitle,
          style: RythoText.mono(10, color: RythoColors.parchmentDim)),
      const SizedBox(height: 6),
      SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Column(children: [
          Row(children: [
            const SizedBox(width: kenar, height: kenar),
            for (final s in sutunlar)
              baslikHucre(
                  s, cross ? kOuterPartnerColor : kInnerGlyphColor),
          ]),
          for (var i = 0; i < satirlar.length; i++)
            Row(children: [
              baslikHucre(satirlar[i], kInnerGlyphColor),
              for (var j = 0; j < sutunlar.length; j++)
                SizedBox(
                  width: kenar,
                  height: kenar,
                  child: (!cross && j >= i)
                      ? const SizedBox.shrink()
                      : _AspectCell(
                          aspect: hucre[(
                            satirlar[i].name,
                            sutunlar[j].name
                          )],
                          l10n: l10n),
                ),
            ]),
        ]),
      ),
    ]);
  }
}

class _AspectCell extends StatelessWidget {
  const _AspectCell({required this.aspect, required this.l10n});

  final ChartAspect? aspect;
  final AppLocalizations l10n;

  @override
  Widget build(BuildContext context) {
    final a = aspect;
    if (a == null) {
      return const DecoratedBox(
          decoration: BoxDecoration(
              border: Border.fromBorderSide(
                  BorderSide(color: Color(0x142C1F40)))));
    }
    final renk = aspectColor(a.kind);
    final harf = a.applying == null
        ? ''
        : (a.applying!
            ? l10n.chartApplyingLetter
            : l10n.chartSeparatingLetter);
    return DecoratedBox(
      decoration: BoxDecoration(
        color: renk.withValues(alpha: 0.08),
        border: const Border.fromBorderSide(
            BorderSide(color: Color(0x142C1F40))),
      ),
      child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        a.kind == 'sextile'
            ? CustomPaint(
                size: const Size(10, 10),
                painter: _MiniGlifPainter('sextile', renk))
            : Text(kAspectTextGlyphs[a.kind] ?? '·',
                style: TextStyle(fontSize: 11, color: renk)),
        Text('${a.orb.toStringAsFixed(1)}$harf',
            style: RythoText.mono(6.8, color: RythoColors.parchmentDim)),
      ]),
    );
  }
}

/// Kiron/Lilith/sextile mini vektör glifi (tablo hücreleri).
class _MiniGlifPainter extends CustomPainter {
  const _MiniGlifPainter(this.name, this.color);

  final String name;
  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawPath(
        specialGlyphPath(
            name, Offset(size.width / 2, size.height / 2), size.width),
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.1
          ..strokeCap = StrokeCap.round
          ..color = color);
  }

  @override
  bool shouldRepaint(_MiniGlifPainter old) =>
      old.name != name || old.color != color;
}

/// Konum tablosu — çarkın erişilebilir (TalkBack) temsili.
class _KonumTablosu extends StatelessWidget {
  const _KonumTablosu({required this.data});

  final ChartData data;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(l10n.chartPositionsTitle,
          style: RythoText.mono(10, color: RythoColors.parchmentDim)),
      const SizedBox(height: 6),
      GlassPanel(
        child: Column(children: [
          for (var r = 0; r < data.rings.length; r++) ...[
            if (data.isBiWheel)
              Align(
                alignment: Alignment.centerLeft,
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Text(
                      r == 0
                          ? l10n.chartLegendInner(data.rings[r].label)
                          : l10n.chartLegendOuter(data.rings[r].label),
                      style: RythoText.label(10,
                          color: RythoColors.parchmentDim)),
                ),
              ),
            for (final p in data.rings[r].points.where((p) => !p.isAngle))
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 2.5),
                child: Row(children: [
                  SizedBox(
                    width: 22,
                    child: kPlanetTextGlyphs.containsKey(p.name)
                        ? Text(kPlanetTextGlyphs[p.name]!,
                            style: RythoText.body(13,
                                color: r == 0
                                    ? kInnerGlyphColor
                                    : kOuterTransitColor))
                        : CustomPaint(
                            size: const Size(13, 13),
                            painter: _MiniGlifPainter(
                                p.name,
                                r == 0
                                    ? kInnerGlyphColor
                                    : kOuterTransitColor)),
                  ),
                  Expanded(
                      child: Text(p.localName, style: RythoText.body(13))),
                  Text(
                    '${signDisplayName(l10n, p.signIndex)} '
                    "${p.degreeInSign.floor()}°"
                    "${(((p.degreeInSign - p.degreeInSign.floor()) * 60).round()).toString().padLeft(2, '0')}'"
                    '${p.houseNo != null ? ' · ${p.houseNo}' : ''}'
                    '${p.retrograde ? ' · R' : ''}',
                    style: RythoText.mono(11, color: RythoColors.lilac),
                  ),
                ]),
              ),
          ],
        ]),
      ),
    ]);
  }
}

