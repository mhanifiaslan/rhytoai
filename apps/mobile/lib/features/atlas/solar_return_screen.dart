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

/// Yıl Haritası (T5): aktif güneş dönüşü — Güneş'in natal boylamına tam
/// döndüğü ana kurulan harita, bir sonraki doğum gününe kadar geçerli
/// yılın tonu. Saatsiz doğumda SR Yükseleni/evleri HİÇ gösterilmez;
/// sunucunun bakır beyanı aynen basılır (üretilmeyen şey söylenmez).
class SolarReturnScreen extends ConsumerWidget {
  const SolarReturnScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final veri = ref.watch(solarReturnProvider);

    return CosmicScaffold(
      appBar: AppBar(title: Text(l10n.solarReturnTitle)),
      body: veri.when(
        // Rapor LLM üretimi — sahneli bekleyiş (R12-B3 kuralı).
        loading: () => StagedWaiting(stages: [
          l10n.solarReturnWaitStage1,
          l10n.solarReturnWaitStage2,
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
              emoji: '🌞',
              title: l10n.solarReturnTitle,
              description: l10n.solarReturnLockedBody,
              centered: true,
            );
          }
          final sr = Map<String, dynamic>.from(data['solar_return']);
          final beyanlar =
              List<String>.from(sr['disclosure_texts'] ?? const []);
          final asc = sr['sr_ascendant'] != null
              ? Map<String, dynamic>.from(sr['sr_ascendant'])
              : null;
          // Sert cast değil hoşgörülü ayrıştırma: alan beklenmedik tipte
          // gelirse satır GİZLENİR, ekran çökmez (üretimde yaşandı —
          // sunucu bir ara kerykeion'un "Tenth_House" metnini geçiriyordu).
          final evHam = sr['sr_sun_house'];
          final gunesEvi =
              evHam is int ? evHam : int.tryParse('${evHam ?? ''}');

          var sira = 0;
          Duration gecikme() => Duration(milliseconds: 130 * sira++);
          Widget blok(Widget w) => w
              .animate(delay: gecikme())
              .fadeIn(duration: 380.ms)
              .slideY(begin: 0.06, curve: Curves.easeOutCubic);

          return ListView(
            padding: const EdgeInsets.only(top: 8, bottom: 120),
            children: [
              // Dönüş anı — dakika hassasiyetinde hesap, mono yazımla.
              blok(Plaque(
                label: l10n.solarReturnMoment,
                child:
                    Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(_an(sr['return_at_local']),
                      style: RythoText.mono(22,
                          color: RythoColors.goldBright)),
                  const SizedBox(height: 6),
                  Text(
                      l10n.solarReturnNext(
                          _an(sr['next_return_at_local'])),
                      style: RythoText.body(12,
                          color: RythoColors.parchmentDim)),
                ]),
              )),
              // Saatsizlik/şehir beyanı — natal ekrandaki bakır dil.
              if (beyanlar.isNotEmpty)
                blok(Padding(
                  padding: const EdgeInsets.fromLTRB(16, 0, 16, 4),
                  child: Text(beyanlar.join('\n'),
                      style:
                          RythoText.body(11.5, color: RythoColors.copper)),
                )),
              // Yılın kimliği: SR Yükseleni (saat biliniyorsa), Güneş'in
              // yıl evi, yıl Ay'ı. Alan YOKSA satır HİÇ kurulmaz.
              blok(Plaque(
                label: l10n.solarReturnIdentity,
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      if (asc != null)
                        _satir(l10n.solarReturnAsc,
                            '${asc['sign_local'] ?? asc['sign']} ${asc['position']}°'),
                      if (gunesEvi != null)
                        _satir(l10n.solarReturnSunHouse,
                            l10n.solarReturnHouseN(gunesEvi)),
                      _satir(l10n.solarReturnMoon,
                          '${sr['sr_moon_local'] ?? sr['sr_moon_sign'] ?? '-'}'),
                    ]),
              )),
              blok(const SectionDivider()),
              blok(Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: MarginNote(
                    title: l10n.solarReturnNote,
                    text: data['report'] ?? ''),
              )),
            ],
          );
        },
      ),
    );
  }

  /// "2026-05-12T20:16:00+03:00" → "2026-05-12 20:16" — saniye ve dilim
  /// eki ekranda gürültü; hesap hassasiyeti raporun konusu değil.
  static String _an(Object? iso) {
    final s = (iso ?? '').toString();
    return s.length >= 16 ? '${s.substring(0, 10)} ${s.substring(11, 16)}' : s;
  }

  static Widget _satir(String etiket, String deger) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 3),
        child: Row(children: [
          Expanded(
              child: Text(etiket,
                  style: RythoText.body(13,
                      color: RythoColors.parchmentDim))),
          Text(deger, style: RythoText.body(13.5, w: FontWeight.w700)),
        ]),
      );
}
