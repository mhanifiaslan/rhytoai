import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api.dart' show friendlyError;
import '../../core/providers.dart';
import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/motion.dart';
import '../paywall/plus_locked_card.dart';

/// İç Takvim (T5): ikincil progresyon (iç mevsim) + 30 günlük transit
/// takvimi tek ekranda. Renk dili tahmin doktrininden: kesinleşme günü
/// ALTIN, yaklaşan (applying) LİLA, ayrılan (separating) soluk. Bütün
/// adlar sunucudan isteğin dilinde gelir (`*_local`); ekran çeviri yapmaz.
class InnerCalendarScreen extends ConsumerWidget {
  const InnerCalendarScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final veri = ref.watch(innerCalendarProvider);

    return CosmicScaffold(
      appBar: AppBar(title: Text(l10n.innerCalendarTitle)),
      body: veri.when(
        loading: () => StagedWaiting(stages: [
          l10n.innerCalendarWaitStage1,
          l10n.innerCalendarWaitStage2,
        ]),
        error: (e, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Text(friendlyError(e, l10n),
                style: RythoText.body(14, color: RythoColors.parchmentDim)),
          ),
        ),
        data: (data) {
          if (data == null) {
            return PlusLockedCard(
              emoji: '🌗',
              title: l10n.innerCalendarTitle,
              description: l10n.innerCalendarLockedBody,
              centered: true,
            );
          }
          final prog = Map<String, dynamic>.from(data['progressions']);
          final progresyon =
              Map<String, dynamic>.from(prog['progressions']);
          final ay = Map<String, dynamic>.from(progresyon['prog_moon']);
          final vurgular = List<Map<String, dynamic>>.from(
              progresyon['solar_arc_hits'] ?? const []);
          final takvim = Map<String, dynamic>.from(data['calendar']);
          final olaylar = List<Map<String, dynamic>>.from(
              takvim['events'] ?? const []);
          final aktif = List<Map<String, dynamic>>.from(
              takvim['active_now'] ?? const []);
          final beyanlar = <String>{
            ...List<String>.from(
                progresyon['disclosure_texts'] ?? const []),
            ...List<String>.from(takvim['disclosure_texts'] ?? const []),
          };

          var sira = 0;
          Duration gecikme() => Duration(milliseconds: 110 * sira++);
          Widget blok(Widget w) => w
              .animate(delay: gecikme())
              .fadeIn(duration: 380.ms)
              .slideY(begin: 0.06, curve: Curves.easeOutCubic);

          return ListView(
            padding: const EdgeInsets.only(top: 8, bottom: 120),
            children: [
              // Progres Ay — iç mevsimin omurgası.
              blok(Plaque(
                label: l10n.innerCalendarProgMoon,
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                          '${ay['sign_local'] ?? ay['sign']} '
                          '${ay['position']}°',
                          style: RythoText.display(24)),
                      const SizedBox(height: 4),
                      Text('${ay['phase_local'] ?? ay['phase'] ?? ''}',
                          style: RythoText.body(13,
                              color: RythoColors.lilac)),
                      const SizedBox(height: 6),
                      Text(
                          l10n.innerCalendarNextSign(
                              '${ay['next_sign_at']}'),
                          style: RythoText.mono(11.5,
                              color: RythoColors.parchmentDim)),
                    ]),
              )),
              if (beyanlar.isNotEmpty)
                blok(Padding(
                  padding: const EdgeInsets.fromLTRB(16, 0, 16, 4),
                  child: Text(beyanlar.join('\n'),
                      style:
                          RythoText.body(11.5, color: RythoColors.copper)),
                )),
              // Şu an etkin açılar: yaklaşan lila, ayrılan soluk.
              if (aktif.isNotEmpty)
                blok(Plaque(
                  label: l10n.innerCalendarActive,
                  child: Column(
                      children: aktif
                          .map((a) => _AcikSatir(
                                metin: '${a['transit_local']} '
                                    '${a['aspect_local']} '
                                    '${a['natal_local']}',
                                ek: '${a['orb']}°',
                                renk: a['movement'] == 'applying'
                                    ? RythoColors.lilac
                                    : RythoColors.parchmentDim,
                              ))
                          .toList()),
                )),
              // 30 günlük çizelge: kesinleşme günleri altın rozetle.
              blok(Plaque(
                label: l10n.innerCalendarUpcoming,
                child: olaylar.isEmpty
                    ? Text(l10n.innerCalendarQuiet,
                        style: RythoText.body(13,
                            color: RythoColors.parchmentDim))
                    : Column(
                        children: olaylar.map((o) {
                          final kesin = o['type'] == 'aspect_exact';
                          final metin = kesin
                              ? '${o['transit_local']} '
                                  '${o['aspect_local']} '
                                  '${o['natal_local']}'
                              : '${o['transit_local']} — '
                                  '${o['type_local']}';
                          return _OlaySatiri(
                            tarih: '${o['date']}'.substring(5),
                            metin: metin,
                            altin: kesin,
                          );
                        }).toList()),
              )),
              // Yaşam yayı: solar arc kesinleşmeleri (yıl/ay hassasiyeti).
              if (vurgular.isNotEmpty)
                blok(Plaque(
                  label: l10n.innerCalendarArc,
                  child: Column(
                      children: vurgular
                          .map((h) => _AcikSatir(
                                metin: '${h['directed_local']} '
                                    '${h['aspect_local']} '
                                    '${h['natal_local']}',
                                // Gün değil AY hassasiyeti: doktrin gereği
                                // tarihi yıl-ay olarak kırpıyoruz.
                                ek: '${h['exact_on']}'.substring(0, 7),
                                renk: RythoColors.parchmentDim,
                              ))
                          .toList()),
                )),
              blok(const SectionDivider()),
              blok(Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: MarginNote(
                    title: l10n.innerCalendarNote,
                    text: prog['report'] ?? ''),
              )),
            ],
          );
        },
      ),
    );
  }
}

/// Tek satırlık açı/vurgu görünümü: metin + sağda mono ek bilgi.
class _AcikSatir extends StatelessWidget {
  const _AcikSatir(
      {required this.metin, required this.ek, required this.renk});

  final String metin;
  final String ek;
  final Color renk;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(children: [
        Expanded(child: Text(metin, style: RythoText.body(13, color: renk))),
        Text(ek, style: RythoText.mono(11, color: RythoColors.parchmentDim)),
      ]),
    );
  }
}

/// Takvim satırı: tarih rozeti + olay metni; kesinleşme günü altın.
class _OlaySatiri extends StatelessWidget {
  const _OlaySatiri(
      {required this.tarih, required this.metin, required this.altin});

  final String tarih;
  final String metin;
  final bool altin;

  @override
  Widget build(BuildContext context) {
    final renk = altin ? RythoColors.goldBright : RythoColors.parchmentDim;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(children: [
        Container(
          width: 52,
          padding: const EdgeInsets.symmetric(vertical: 3),
          decoration: BoxDecoration(
            color: RythoColors.inkLighter,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
                color: renk.withValues(alpha: altin ? 0.55 : 0.2)),
          ),
          child: Center(
              child: Text(tarih, style: RythoText.mono(10.5, color: renk))),
        ),
        const SizedBox(width: 10),
        Expanded(
            child: Text(metin,
                style: RythoText.body(13,
                    color: altin
                        ? RythoColors.parchment
                        : RythoColors.parchmentDim))),
      ]),
    );
  }
}
