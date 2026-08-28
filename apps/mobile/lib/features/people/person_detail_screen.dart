/// Eklenen kişinin ekranı — mini Atlas (P-turu).
///
/// ## Neden ana Atlas'ın kişi seçicisi değil
///
/// Ana Atlas'ın altındaki her şey — günlük okuma, sinyaller, takvim,
/// yıl haritası — "sen"e ait. Oraya bir kişi seçici koymak her ekranda
/// "bu kimin günü?" belirsizliği yaratırdı. Kişi kendi ekranında yaşar.
///
/// ## Ücretsiz olan ne
///
/// Çark, Büyük Üçlü ve yerleşimler: hepsi LLM'siz hesap, hepsi ücretsiz
/// ("hesap bedava, yorum paralı"). Kilitlenen yalnız YORUM.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api.dart';
import '../../core/discovery.dart';
import '../../core/people.dart';
import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import '../../theme/rytho_tokens.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/common.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/glass.dart';
import '../../widgets/nebula_widgets.dart' show Pressable;
import '../../widgets/natal_wheel.dart';
import '../chat/chat_screen.dart';
import '../friends/relationship_screen.dart' show RelationshipScreen;
import 'person_form_screen.dart' show PersonFormScreen, relationLabel;

/// Kişinin haritası. Anahtar kişinin kimliği + doğum verisi: kullanıcı
/// kaydı düzeltince harita da tazelenir.
final personChartProvider =
    FutureProvider.family<Map<String, dynamic>, Person>((ref, kisi) async {
  final dio = ref.watch(apiProvider);
  final response = await dio.post('/api/v1/astrology/natal-chart',
      data: kisi.toBirthPayload());
  return Map<String, dynamic>.from(response.data['data'] as Map);
});

class PersonDetailScreen extends ConsumerWidget {
  const PersonDetailScreen({super.key, required this.person});

  final Person person;

  Future<void> _sil(BuildContext context, WidgetRef ref) async {
    final l10n = AppLocalizations.of(context);
    final onay = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        backgroundColor: RythoColors.inkLight,
        content: Text(l10n.peopleRemoveConfirm, style: RythoText.body(14)),
        actions: [
          TextButton(
              onPressed: () => Navigator.of(c).pop(false),
              child: Text(l10n.cancel)),
          TextButton(
              onPressed: () => Navigator.of(c).pop(true),
              child: Text(l10n.peopleRemove,
                  style: const TextStyle(color: RythoColors.copper))),
        ],
      ),
    );
    if (onay != true || !context.mounted) return;

    final gezgin = Navigator.of(context);
    final mesajci = ScaffoldMessenger.of(context);
    try {
      await deletePerson(ref.read(apiProvider), person.id);
      ref.invalidate(personSlotsProvider);
      mesajci.showSnackBar(SnackBar(content: Text(l10n.peopleRemoved)));
      gezgin.pop();
    } catch (e) {
      mesajci.showSnackBar(SnackBar(content: Text(friendlyError(e, l10n))));
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final ad = person.label ?? relationLabel(l10n, person.relation);
    final harita = ref.watch(personChartProvider(person));

    // OB4: çevreden birine bakmak keşif halkasının üçüncü dilimi.
    // build İÇİNDE provider değiştirilemez; kare sonrasına ertelenir
    // (mark idempotent — yeniden çizimde tekrar çağrılması zararsız).
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (context.mounted) {
        ref.read(discoveryProvider.notifier).mark(DiscoveryTask.circle);
      }
    });

    return CosmicScaffold(
      appBar: AppBar(
        title: Text(ad),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit_outlined, size: 20),
            onPressed: () async {
              final degisti = await Navigator.of(context).push<bool>(
                  MaterialPageRoute(
                      builder: (_) => PersonFormScreen(existing: person)));
              if (degisti == true) ref.invalidate(personChartProvider(person));
            },
          ),
          IconButton(
            icon: const Icon(Icons.delete_outline_rounded, size: 20),
            onPressed: () => _sil(context, ref),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.only(bottom: 60),
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(
                RythoSpace.lg, RythoSpace.md, RythoSpace.lg, 0),
            child: Text(relationLabel(l10n, person.relation),
                style: RythoText.mono(11.5, color: RythoColors.parchmentDim)),
          ),
          const SizedBox(height: RythoSpace.md),

          harita.when(
            loading: () => const Padding(
              padding: EdgeInsets.only(top: 60),
              child: Center(child: AstrolabeSpinner()),
            ),
            error: (e, _) => Padding(
              padding: const EdgeInsets.all(RythoSpace.lg),
              child: ErrorCard(
                  message: friendlyError(e, l10n),
                  onRetry: () =>
                      ref.invalidate(personChartProvider(person))),
            ),
            data: (h) => _HaritaBolumu(person: person, chart: h),
          ),

          const SizedBox(height: RythoSpace.xl),
          Padding(
            padding:
                const EdgeInsets.symmetric(horizontal: RythoSpace.lg),
            child: Column(children: [
              _EylemSatiri(
                icon: Icons.public_rounded,
                label: l10n.relationshipTitle(ad),
                onTap: () => Navigator.of(context).push(MaterialPageRoute(
                    builder: (_) =>
                        RelationshipScreen.forPerson(person: person))),
              ),
              const SizedBox(height: RythoSpace.sm),
              _EylemSatiri(
                icon: Icons.auto_awesome_rounded,
                label: l10n.signalAsk,
                onTap: () => Navigator.of(context).push(MaterialPageRoute(
                    builder: (_) => ChatScreen(personId: person.id))),
              ),
            ]),
          ),
        ],
      ),
    );
  }
}

class _HaritaBolumu extends StatelessWidget {
  const _HaritaBolumu({required this.person, required this.chart});

  final Person person;
  final Map<String, dynamic> chart;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final points = [
      for (final p in (chart['points'] as List? ?? const []))
        Map<String, dynamic>.from(p as Map),
    ];
    final houses = [
      for (final h in (chart['houses'] as List? ?? const []))
        Map<String, dynamic>.from(h as Map),
    ];
    final aspects = [
      for (final a in (chart['aspects'] as List? ?? const []))
        Map<String, dynamic>.from(a as Map),
    ];

    return Column(children: [
      // Büyük Üçlü: Yükselen saatsizken sunucu ZATEN üretmiyor, bu yüzden
      // burada "—" değil, satır hiç çizilmiyor ve altta beyan duruyor.
      Padding(
        padding: const EdgeInsets.symmetric(horizontal: RythoSpace.lg),
        child: GlassPanel(
          label: l10n.bigThreeTitle,
          child: Column(children: [
            _MuhurSatiri(
                etiket: l10n.bigThreeSun, deger: chart['sun_sign'] as String?),
            _MuhurSatiri(
                etiket: l10n.bigThreeMoon,
                deger: chart['moon_sign'] as String?),
            if ((chart['ascendant'] as String?) != null)
              _MuhurSatiri(
                  etiket: l10n.bigThreeAscendant,
                  deger: chart['ascendant'] as String?),
          ]),
        ),
      ),
      if (!person.hourKnown) ...[
        const SizedBox(height: RythoSpace.sm),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: RythoSpace.lg),
          child: Text(l10n.peopleHourUnknownBadge,
              style: RythoText.body(11.5, color: RythoColors.copper)),
        ),
      ],
      const SizedBox(height: RythoSpace.lg),
      if (points.isNotEmpty)
        Center(
          child: NatalWheel(
              points: points, houses: houses, aspects: aspects, size: 320),
        ),
    ]);
  }
}

class _MuhurSatiri extends StatelessWidget {
  const _MuhurSatiri({required this.etiket, required this.deger});

  final String etiket;
  final String? deger;

  @override
  Widget build(BuildContext context) {
    if (deger == null || deger!.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(children: [
        Text(etiket, style: RythoType.label),
        const Spacer(),
        Text(deger!, style: RythoText.body(14, w: FontWeight.w600)),
      ]),
    );
  }
}

class _EylemSatiri extends StatelessWidget {
  const _EylemSatiri(
      {required this.icon, required this.label, required this.onTap});

  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Pressable(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(
            horizontal: RythoSpace.lg, vertical: 14),
        decoration: BoxDecoration(
          color: RythoColors.inkLighter,
          border: Border.all(color: RythoColors.glassStroke),
          borderRadius: BorderRadius.circular(RythoRadius.md),
        ),
        child: Row(children: [
          Icon(icon, size: 18, color: RythoColors.lilac),
          const SizedBox(width: RythoSpace.md),
          Expanded(
              child: Text(label, style: RythoText.body(14.5))),
          const Icon(Icons.chevron_right_rounded,
              size: 18, color: RythoColors.parchmentDim),
        ]),
      ),
    );
  }
}
