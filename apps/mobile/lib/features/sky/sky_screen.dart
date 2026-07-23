import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../core/motivation.dart';
import '../../core/providers.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/glass.dart';
import '../../widgets/nebula_widgets.dart';
import '../chat/chat_screen.dart';
import '../oracle/oracle_screen.dart';
import '../shell/app_shell.dart';

/// GÖKYÜZÜ — ana ekran v3: selamlama, burç çipleri, promo banner,
/// günün içgörüsü (+ seri ve kişisel nudge), kehanet araçları karuseli
/// ve canlı gökyüzü kartı. Kartlar 70ms stagger ile girer.
class SkyScreen extends ConsumerStatefulWidget {
  const SkyScreen({super.key});

  @override
  ConsumerState<SkyScreen> createState() => _SkyScreenState();
}

class _SkyScreenState extends ConsumerState<SkyScreen> {
  int? _selectedSign;
  bool _streakTouched = false;

  String get _greeting {
    final hour = DateTime.now().hour;
    if (hour >= 5 && hour < 12) return 'Günaydın';
    if (hour >= 12 && hour < 18) return 'İyi günler';
    if (hour >= 18 && hour < 23) return 'İyi akşamlar';
    return 'İyi geceler';
  }

  /// Günlük seri: profil geldiğinde bir kez işlenir.
  void _touchStreak(Map<String, dynamic> profile) {
    if (_streakTouched) return;
    _streakTouched = true;
    DailyStreak.touch(profile).catchError((_) => 0);
  }

  @override
  Widget build(BuildContext context) {
    final sky = ref.watch(skyNowProvider);
    final daily = ref.watch(dailyReadingProvider);
    final profile = ref.watch(profileProvider).value ?? {};
    if (profile.isNotEmpty) _touchStreak(profile);

    final sunSign = profile['sunSign'] as String?;
    final userSignIndex =
        sunSign != null ? kSignNamesTr.indexOf(sunSign) : -1;
    final selected = _selectedSign ?? (userSignIndex >= 0 ? userSignIndex : 0);
    final streak = (profile['streakCount'] as num?)?.toInt() ?? 0;

    // Burç şeridi: kullanıcının burcu önde, kalanı sırayla.
    final signOrder = [
      if (userSignIndex >= 0) userSignIndex,
      for (var i = 0; i < 12; i++)
        if (i != userSignIndex) i,
    ];

    var stagger = 0;
    Duration next() => Duration(milliseconds: 70 * stagger++);

    return Scaffold(
      backgroundColor: Colors.transparent,
      body: SafeArea(
        bottom: false,
        child: RefreshIndicator(
          color: RythoColors.magenta,
          backgroundColor: RythoColors.inkLight,
          onRefresh: () async {
            ref.invalidate(skyNowProvider);
            ref.invalidate(dailyReadingProvider);
          },
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.only(bottom: 130),
            children: [
              const SizedBox(height: 10),
              _Header(
                greeting: _greeting,
                name: profile['displayName'] ?? 'Gezgin',
                photoUrl: profile['photoUrl'],
                streak: streak,
              ).animate(delay: next()).fadeIn(duration: 360.ms).slideY(
                  begin: 0.08, curve: Curves.easeOutCubic),
              const SizedBox(height: 16),
              // Burç çipleri şeridi
              SizedBox(
                height: 78,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  itemCount: signOrder.length,
                  separatorBuilder: (_, _) => const SizedBox(width: 12),
                  itemBuilder: (_, i) => ZodiacChip(
                    signIndex: signOrder[i],
                    selected: signOrder[i] == selected,
                    onTap: () =>
                        setState(() => _selectedSign = signOrder[i]),
                  ),
                ),
              ).animate(delay: next()).fadeIn(duration: 360.ms).slideY(
                  begin: 0.08, curve: Curves.easeOutCubic),
              const SizedBox(height: 8),
              // Premium/upsell banner'ı → Atlas'ın derin raporu
              PromoBanner(
                title: 'Yıldızların ötesine geç ✨',
                subtitle:
                    'Doğum haritanın derin analizini ve kişilik raporunu keşfet.',
                buttonText: 'Keşfet',
                onTap: () =>
                    ref.read(shellTabProvider.notifier).state = 1,
              ).animate(delay: next()).fadeIn(duration: 360.ms).slideY(
                  begin: 0.08, curve: Curves.easeOutCubic),
              // Bugünün içgörüsü
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 14, 20, 6),
                child: Row(children: [
                  Text('Bugünün İçgörüsü', style: RythoText.display(19)),
                  const Spacer(),
                  Text(
                    DateFormat('d MMMM', 'tr_TR').format(DateTime.now()),
                    style: RythoText.mono(11, color: RythoColors.parchmentDim),
                  ),
                ]),
              ).animate(delay: next()).fadeIn(duration: 360.ms),
              daily.when(
                loading: () => const Padding(
                  padding: EdgeInsets.all(28),
                  child: Center(child: AstrolabeSpinner()),
                ),
                error: (e, _) => _ErrorCard(error: '$e'),
                data: (data) => data == null
                    ? const SizedBox.shrink()
                    : GlassPanel(
                        label:
                            '☀️ ${data['sun_sign']} · 🌙 ${data['moon_sign']} · ⬆️ ${data['ascendant']}',
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            TypewriterText(
                              text: data['reading'] ?? '',
                              style: RythoText.body(14.5, height: 1.6),
                            ),
                            const SizedBox(height: 14),
                            // Kişisel nudge: burca özel motive edici cümle
                            Container(
                              width: double.infinity,
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                borderRadius: BorderRadius.circular(14),
                                color: RythoColors.violet.withValues(alpha: 0.14),
                                border: Border.all(
                                    color: RythoColors.lilac
                                        .withValues(alpha: 0.25)),
                              ),
                              child: Text(
                                nudgeForSign(sunSign),
                                style: RythoText.body(13,
                                    color: RythoColors.lilac,
                                    w: FontWeight.w600),
                              ),
                            ),
                          ],
                        ),
                      ).animate(delay: next()).fadeIn(duration: 380.ms).slideY(
                          begin: 0.06, curve: Curves.easeOutCubic),
              ),
              // Kehanet araçları karuseli
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 14, 20, 8),
                child: Text('Kehanet Araçları', style: RythoText.display(19)),
              ).animate(delay: next()).fadeIn(duration: 360.ms),
              SizedBox(
                height: 118,
                child: ListView(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  children: [
                    for (final (i, tool) in const [
                      ('🪙', 'I Ching', 'Değişimler Kitabı'),
                      ('🀄', 'BaZi', 'Dört Sütun'),
                      ('🔮', 'Yüz Okuma', 'İlm-i Sima'),
                      ('💞', 'Sinastri', 'Kozmik uyum'),
                    ].indexed)
                      Padding(
                        padding: const EdgeInsets.only(right: 12),
                        child: _OracleCard(
                          emoji: tool.$1,
                          title: tool.$2,
                          subtitle: tool.$3,
                          onTap: () {
                            if (i < 3) {
                              Navigator.of(context).push(MaterialPageRoute(
                                  builder: (_) =>
                                      OracleScreen(initialTab: i)));
                            } else {
                              // Sinastri: Meclis'te bir profile girip
                              // "Kozmik uyum" ile hesaplanır.
                              ref.read(shellTabProvider.notifier).state = 2;
                            }
                          },
                        )
                            .animate(delay: Duration(milliseconds: 70 * stagger + i * 70))
                            .fadeIn(duration: 360.ms)
                            .slideX(begin: 0.1, curve: Curves.easeOutCubic),
                      ),
                  ],
                ),
              ),
              // Canlı gökyüzü
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 6),
                child: Text('Şu An Gökyüzünde', style: RythoText.display(19)),
              ).animate(delay: next()).fadeIn(duration: 360.ms),
              sky.when(
                loading: () => const SizedBox(
                    height: 180, child: Center(child: AstrolabeSpinner())),
                error: (e, _) => _ErrorCard(error: '$e'),
                data: (data) => GlassPanel(
                  child: Column(children: [
                    Center(
                      child: ZodiacRing(
                        planets:
                            List<Map<String, dynamic>>.from(data['planets']),
                        size: 230,
                      ),
                    ),
                    const SizedBox(height: 10),
                    _SkyStrip(sky: data),
                  ]),
                ).animate(delay: next()).fadeIn(duration: 380.ms).slideY(
                    begin: 0.06, curve: Curves.easeOutCubic),
              ),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }
}

/// Üst şerit: degrade halkalı avatar + selamlama + seri rozeti + sohbet ikonu.
class _Header extends StatelessWidget {
  const _Header({
    required this.greeting,
    required this.name,
    required this.photoUrl,
    required this.streak,
  });

  final String greeting;
  final String name;
  final String? photoUrl;
  final int streak;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(children: [
        Container(
          padding: const EdgeInsets.all(2.5),
          decoration: const BoxDecoration(
            shape: BoxShape.circle,
            gradient: RythoColors.primaryGradient,
          ),
          child: CircleAvatar(
            radius: 23,
            backgroundColor: RythoColors.inkLight,
            backgroundImage:
                photoUrl != null ? NetworkImage(photoUrl!) : null,
            child: photoUrl == null
                ? Text('☽', style: RythoText.display(18))
                : null,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(greeting,
                style: RythoText.body(12.5, color: RythoColors.parchmentDim)),
            Text(name,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: RythoText.display(18, w: FontWeight.w600)),
          ]),
        ),
        StreakBadge(count: streak),
        const SizedBox(width: 10),
        Pressable(
          onTap: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const ChatScreen())),
          child: Container(
            width: 42,
            height: 42,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: RythoColors.inkLight,
              border: Border.all(color: RythoColors.glassStroke),
            ),
            child: const Icon(Icons.forum_outlined,
                size: 20, color: RythoColors.lilac),
          ),
        ),
      ]),
    );
  }
}

/// Kehanet aracı kartı.
class _OracleCard extends StatelessWidget {
  const _OracleCard({
    required this.emoji,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  final String emoji;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Pressable(
      onTap: onTap,
      child: Container(
        width: 128,
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: RythoColors.glassFill,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: RythoColors.glassStroke),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(emoji, style: const TextStyle(fontSize: 26)),
          const Spacer(),
          Text(title, style: RythoText.body(14.5, w: FontWeight.w700)),
          const SizedBox(height: 2),
          Text(subtitle,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: RythoText.body(10.5, color: RythoColors.parchmentDim)),
        ]),
      ),
    );
  }
}

class _SkyStrip extends StatelessWidget {
  const _SkyStrip({required this.sky});
  final Map<String, dynamic> sky;

  @override
  Widget build(BuildContext context) {
    final moon = sky['moon_phase'] as Map<String, dynamic>? ?? {};
    final retros = List<String>.from(sky['retrogrades'] ?? []);
    final aspects = List<Map<String, dynamic>>.from(sky['aspects'] ?? []);

    return Column(children: [
      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text('${moon['emoji'] ?? ''} ${moon['name'] ?? ''}',
              style: RythoText.body(13.5, w: FontWeight.w600)),
          Text('  ·  ',
              style: RythoText.body(13.5, color: RythoColors.parchmentDim)),
          Text('aydınlanma %${moon['illumination'] ?? '—'}',
              style: RythoText.mono(11.5, color: RythoColors.parchmentDim)),
        ],
      ),
      if (retros.isNotEmpty) ...[
        const SizedBox(height: 10),
        Wrap(
          spacing: 8,
          runSpacing: 6,
          alignment: WrapAlignment.center,
          children: [
            for (final r in retros)
              InfoChip(text: '↩️ $r retro', color: RythoColors.magenta),
          ],
        ),
      ],
      if (aspects.isNotEmpty) ...[
        const SizedBox(height: 12),
        SizedBox(
          height: 32,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: aspects.length.clamp(0, 8),
            separatorBuilder: (_, _) => const SizedBox(width: 8),
            itemBuilder: (_, i) {
              final a = aspects[i];
              return InfoChip(text: '${a['p1']} ${a['aspect']} ${a['p2']}');
            },
          ),
        ),
      ],
    ]);
  }
}

class _ErrorCard extends StatelessWidget {
  const _ErrorCard({required this.error});
  final String error;

  @override
  Widget build(BuildContext context) {
    return GlassPanel(
      child: Text(
        'Gökyüzüne şu an ulaşılamıyor.\n$error',
        style: RythoText.body(13, color: RythoColors.parchmentDim),
      ),
    );
  }
}
