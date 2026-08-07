import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../core/motivation.dart';
import '../../core/providers.dart';
import '../../core/sound.dart';
import '../../core/subscription.dart'
    show introPaywallShown, markIntroPaywallShown, subscriptionProvider;
import '../../theme/rytho_theme.dart';
import '../../theme/rytho_tokens.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/common.dart';
import '../../widgets/motion.dart';
import '../../widgets/nebula_widgets.dart';
import '../../widgets/reading_card.dart';
import '../../widgets/star_burst.dart';
import '../../widgets/token_chip.dart';
import '../chat/conversation_list_screen.dart';
import '../shell/app_shell.dart' show shellTabProvider;
import '../paywall/paywall_screen.dart';
import '../paywall/plus_locked_card.dart';
import 'sign_story_screen.dart';
import 'sky_now_screen.dart';
import '../../core/api.dart' show friendlyError;
import '../../core/notifications.dart'
    show
        markNotificationPromptShown,
        notificationPromptShown,
        requestNotificationPermission;
import '../../l10n/app_localizations.dart';

/// GÖKYÜZÜ — **bugün** ekranı.
///
/// ## Yeniden kurgulandı
///
/// Önceki hâli ~1500 px uzunluğundaydı ve kullanıcı tarifi şuydu: "tamamen
/// karışık bir yer". Sebebi, bir bakışta görülecek şeyle üç dakika okunacak
/// şeyin aynı seviyede, tek kaydırma sütununda durmasıydı.
///
/// Üç şey akıştan çıktı:
///
/// * **Burç yorumu** → hikâye okuyucusu ([SignStoryScreen]). Şerit zaten
///   hikâye halkası gibi görünüyordu; artık öyle davranıyor.
/// * **Gökyüzü çarkı** → [SkyNowScreen]. Akışta tek satırlık özet kaldı.
/// * **Tanıtım bandı** → silindi. Satış mesajı [PlusLockedCard]'da, yani
///   kullanıcının kilitli içeriğe baktığı yerde duruyor.
///
/// Kalan yapı iki bölüm: bugün senin için · şu an. (Araçlar Atlas'a
/// taşındı — Revize R6, madde 11.)
class SkyScreen extends ConsumerStatefulWidget {
  const SkyScreen({super.key});

  @override
  ConsumerState<SkyScreen> createState() => _SkyScreenState();
}

class _SkyScreenState extends ConsumerState<SkyScreen> {
  int? _selectedSign;
  bool _streakTouched = false;
  bool _introPaywallHandled = false;

  /// Seri BU oturumda büyüdüyse yeni sayı (R12-C1) — rozet vurgusu bir kez
  /// oynar. Null: kutlanacak bir şey yok.
  int? _streakYeni;

  String _greeting(AppLocalizations l10n) {
    final hour = DateTime.now().hour;
    if (hour >= 5 && hour < 12) return l10n.greetingMorning;
    if (hour >= 12 && hour < 18) return l10n.greetingDay;
    if (hour >= 18 && hour < 23) return l10n.greetingEvening;
    return l10n.greetingNight;
  }

  /// Günlük seri: profil geldiğinde bir kez işlenir.
  ///
  /// R12-C1: dönen sayı artık atılmıyor — seri BÜYÜDÜYSE rozet vurgusu +
  /// mini yıldız patlaması + ses. Sıfırlanma (5→1) kutlanmaz; bugünkü
  /// ikinci açılış aynı sayıyı döndürür ve sessiz kalır.
  void _touchStreak(Map<String, dynamic> profile) {
    if (_streakTouched) return;
    _streakTouched = true;
    final onceki = (profile['streakCount'] as num?)?.toInt() ?? 0;
    DailyStreak.touch(profile).then<void>((yeni) {
      if (!mounted || yeni <= onceki) return;
      SoundFx.streak();
      setState(() => _streakYeni = yeni);
    }).catchError((_) {});
  }

  /// Tanıtım paywall'ı: hesap ömründe **bir kez**, kullanıcı ilk değerini
  /// gördükten sonra.
  ///
  /// Onboarding biter bitmez göstermek erken terk oranını artırıyor; hiç
  /// göstermemek ise kilitli karta dokunmayan kullanıcıya Rytho+'ın varlığını
  /// hiç duyurmuyor. Bu yüzden tetikleyici, ücretsiz günlük yorumun ekrana
  /// gelmesidir.
  ///
  /// Yorum paylaşımı akıştan hikâye okuyucusuna taşındı — paylaşılacak metnin
  /// tamamı orada görünüyor (bkz. sign_story_screen.dart).

  /// İlk değer ekrana geldikten sonraki tek seferlik akış.
  ///
  /// Sıra önemli: paywall gösterilecekse bildirim izni BU AÇILIŞTA
  /// istenmez. Kullanıcıyı arka arkaya iki modalla karşılamak ikisinin de
  /// reddedilme olasılığını artırır; bildirim izni bir sonraki açılışta
  /// sorulur ve o zaman tek başına görünür.
  void _maybeShowIntroPaywall() {
    if (_introPaywallHandled) return;
    _introPaywallHandled = true;

    WidgetsBinding.instance.addPostFrameCallback((_) async {
      if (!mounted) return;

      final abone = ref.read(subscriptionProvider).value?.active ?? false;
      final paywallGosterilecek =
          !abone && !(await introPaywallShown());

      if (paywallGosterilecek) {
        await markIntroPaywallShown();
        if (!mounted) return;
        await Navigator.of(context).push(MaterialPageRoute(
          builder: (_) => const PaywallScreen(),
          fullscreenDialog: true,
        ));
        return;
      }

      // Bildirim izni: kullanıcı ilk değeri gördü, artık neyin bildirimini
      // alacağını biliyor. Değer görmeden sorulan izin reddediliyor ve
      // sistem bir daha sormaya izin vermiyor.
      if (await notificationPromptShown()) return;
      await markNotificationPromptShown();
      await requestNotificationPermission();
    });
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final sky = ref.watch(skyNowProvider);
    final daily = ref.watch(dailyReadingProvider);
    final profile = ref.watch(profileProvider).value ?? {};
    if (profile.isNotEmpty) _touchStreak(profile);

    final sunSign = profile['sunSign'] as String?;
    final userSignIndex = signIndexOf(sunSign);
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
            ref.invalidate(signHoroscopeProvider(kSignKeys[selected]));
            ref.invalidate(dailyReadingProvider);
            // Abonelik durumu da tazelensin: satın alma sonrası webhook
            // sunucuya islenene kadar kisa bir gecikme olabiliyor.
            ref.invalidate(subscriptionProvider);
          },
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.only(bottom: RythoSpace.dockClearance),
            children: [
              const SizedBox(height: RythoSpace.sm),
              _Header(
                greeting: _greeting(l10n),
                name: profile['displayName'] ?? 'Gezgin',
                photoUrl: profile['photoUrl'],
                streak: streak,
                celebrate: _streakYeni,
                onAvatarTap: () =>
                    ref.read(shellTabProvider.notifier).state = 3,
              ).animate(delay: next()).fadeIn(duration: 360.ms).slideY(
                  begin: 0.08, curve: Curves.easeOutCubic),
              const SizedBox(height: RythoSpace.lg),
              // Burç şeridi — HİKÂYE halkası. Dokunma tam ekran okuyucu açar.
              //
              // Eskiden bu şerit bir "seçici"ydi: dokunulunca 200 px aşağıdaki
              // bölümün metni değişiyordu, arada da alakasız bir tanıtım bandı
              // duruyordu. Görünüşü hikâye, davranışı sekme filtresiydi.
              SizedBox(
                height: 78,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(
                      horizontal: RythoSpace.lg),
                  itemCount: signOrder.length,
                  separatorBuilder: (_, _) =>
                      const SizedBox(width: RythoSpace.md),
                  itemBuilder: (_, i) => ZodiacChip(
                    signIndex: signOrder[i],
                    selected: signOrder[i] == selected,
                    onTap: () => _openStory(signOrder, i),
                  ),
                ),
              ).animate(delay: next()).fadeIn(duration: 360.ms).slideY(
                  begin: 0.08, curve: Curves.easeOutCubic),

              // ---------- BUGÜN SENİN İÇİN ----------
              SectionHeader(
                l10n.todaysInsight,
                trailing: Text(
                  // Tarih biçimi de dile bağlı: sabit 'tr_TR' İngilizce
                  // arayüzde Türkçe ay adı gösteriyordu.
                  DateFormat('d MMMM',
                          Localizations.localeOf(context).toLanguageTag())
                      .format(DateTime.now()),
                  style: RythoType.dataSmall,
                ),
              ).animate(delay: next()).fadeIn(duration: 360.ms),

              // Ücretsiz katman: kullanıcının kendi burcunun günlük yorumu.
              // Paylaşımlı önbellekten geldiği için her zaman doludur ve
              // kullanıcı sayısından bağımsız maliyettedir.
              //
              // Spinner → kart geçişi AnimatedSwitcher'da (R12-B2): okumanın
              // GELİŞİ artık bir an — kart üstünden tek atışlık altın parıltı
              // geçer ("bugünün okuması yeni geldi" işareti, döngü yok).
              AnimatedSwitcher(
                duration:
                    reduceMotion(context) ? Duration.zero : RythoMotion.slow,
                switchInCurve: RythoMotion.enter,
                child:
                    ref.watch(signHoroscopeProvider(kSignKeys[selected])).when(
                          loading: () => const Padding(
                            padding: EdgeInsets.all(RythoSpace.xl),
                            child: Center(child: AstrolabeSpinner()),
                          ),
                          error: (e, _) => Padding(
                            padding: const EdgeInsets.symmetric(
                                horizontal: RythoSpace.lg),
                            child: ErrorCard(
                              message: friendlyError(e, l10n),
                              onRetry: () => ref.invalidate(
                                  signHoroscopeProvider(kSignKeys[selected])),
                            ),
                          ),
                          data: (data) {
                            // Kullanıcı ilk değerini gördü: tanıtım paywall'ı
                            // buradan tetiklenir (hesap ömründe bir kez).
                            _maybeShowIntroPaywall();
                            return ReadingCard(
                              label: l10n.signToday(
                                  signDisplayName(l10n, selected)),
                              title: signDisplayName(l10n, selected),
                              body: data['reading'] ?? '',
                              // Kart yalnızca ÖNİZLEME. Tam metin hikâye
                              // okuyucusunda; iki ayrı "tam metin" yeri
                              // olmamalı.
                              onOpen: () => _openStory(
                                  signOrder, signOrder.indexOf(selected)),
                            )
                                .animate(delay: next())
                                .fadeIn(duration: 380.ms)
                                .slideY(
                                    begin: 0.06, curve: Curves.easeOutCubic)
                                .then()
                                .shimmer(
                                    duration: 900.ms,
                                    color: RythoColors.gold
                                        .withValues(alpha: 0.12));
                          },
                        ),
              ),

              // Rytho+: kişiye özel okuma. Abone değilse istek atılmaz;
              // kilitli kart gösterilir ve paywall ancak dokununca açılır.
              daily.when(
                loading: () => const SizedBox.shrink(),
                error: (e, _) => Padding(
                  padding:
                      const EdgeInsets.symmetric(horizontal: RythoSpace.lg),
                  child: ErrorCard(
                    message: friendlyError(e, l10n),
                    onRetry: () => ref.invalidate(dailyReadingProvider),
                  ),
                ),
                data: (data) => data == null
                    ? PlusLockedCard(
                        title: l10n.personalReadingLocked,
                        description: userSignIndex < 0
                            ? l10n.personalReadingLockedBody
                            : l10n.personalReadingLockedBodyWithSign(
                                signDisplayName(l10n, userSignIndex)),
                      )
                    : ReadingCard(
                        label:
                            '☀️ ${data['sun_sign']} · 🌙 ${data['moon_sign']} · ⬆️ ${data['ascendant']}',
                        title: l10n.personalReadingTitle,
                        body: data['reading'] ?? '',
                        glow: true,
                      ).animate(delay: next()).fadeIn(duration: 380.ms),
              ),

              // ---------- ŞU AN ----------
              // Çark ve açı çipleri kendi sayfasına taşındı; akışta tek
              // satırlık özet duruyor (bkz. sky_now_screen.dart).
              SectionHeader(l10n.skyNow)
                  .animate(delay: next())
                  .fadeIn(duration: 360.ms),
              sky.when(
                loading: () => const Padding(
                  padding: EdgeInsets.all(RythoSpace.xl),
                  child: Center(child: AstrolabeSpinner()),
                ),
                error: (e, _) => Padding(
                  padding:
                      const EdgeInsets.symmetric(horizontal: RythoSpace.lg),
                  child: ErrorCard(
                    message: friendlyError(e, l10n),
                    onRetry: () => ref.invalidate(skyNowProvider),
                  ),
                ),
                data: (data) => SkyNowSummary(sky: data)
                    .animate(delay: next())
                    .fadeIn(duration: 380.ms)
                    .slideY(begin: 0.06, curve: Curves.easeOutCubic),
              ),

              // ARAÇLAR bölümü buradan KALKTI (Revize R6, madde 11):
              // İching + BaZi artık Atlas'ta, Yüz Okuma ile tek satırda
              // (atlas_screen.dart → _DivinationRow). Gökyüzü ~140 px
              // kısaldı ve "bugün" anlatısına odaklandı.
            ],
          ),
        ),
      ),
    );
  }

  /// Burç hikâyesini tam ekran açar.
  void _openStory(List<int> order, int index) {
    if (index < 0) return;
    Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => SignStoryScreen(order: order, initialIndex: index),
      fullscreenDialog: true,
    ));
  }
}

/// Üst şerit: degrade halkalı avatar + selamlama + seri rozeti + sohbet ikonu.
///
/// [_rozet]: seri kutlaması — rozet 1→1.25→1 şişer (pop), arkasında 12
/// kıvılcımlık mini patlama. Profildeki sayı Firestore turundan henüz
/// dönmediyse yeni sayı [_Header.celebrate]'ten gösterilir; kullanıcı
/// artışı ANINDA görür.
class _Header extends StatelessWidget {
  const _Header({
    required this.greeting,
    required this.name,
    required this.photoUrl,
    required this.streak,
    required this.onAvatarTap,
    this.celebrate,
  });

  final String greeting;
  final String name;
  final String? photoUrl;
  final int streak;

  /// Avatara dokunuş — Profil sekmesine geçiş (U1).
  final VoidCallback onAvatarTap;

  /// Seri bu oturumda büyüdüyse yeni sayı (R12-C1): rozet bir kez şişip
  /// yerine oturur, arkasında mini yıldız patlaması. Null: vurgu yok.
  final int? celebrate;

  Widget _rozet(BuildContext context) {
    final rozet = StreakBadge(count: celebrate ?? streak);
    if (celebrate == null || reduceMotion(context)) return rozet;
    return Stack(
      alignment: Alignment.center,
      clipBehavior: Clip.none,
      children: [
        Positioned.fill(
          child: OverflowBox(
            maxWidth: 100,
            maxHeight: 100,
            child: const StarBurst(size: 100, particles: 12),
          ),
        ),
        rozet
            .animate(key: ValueKey('seri-$celebrate'))
            .scale(
                begin: const Offset(1, 1),
                end: const Offset(1.25, 1.25),
                duration: const Duration(milliseconds: 250),
                curve: RythoMotion.pop)
            .then()
            .scale(
                begin: const Offset(1, 1),
                end: const Offset(0.8, 0.8),
                duration: const Duration(milliseconds: 250),
                curve: RythoMotion.settle),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(children: [
        // Avatar dokunulabilir (U1): Profil sekmesine götürür — en
        // tanıdık desen (üstteki avatar = profil kapısı).
        Pressable(
          onTap: onAvatarTap,
          child: Container(
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
        // Jeton hapı (U1): ekonomi ana ekranda her an görünür; dokununca
        // Abonelik ve Jetonlar açılır (Duolingo mücevher sayacı modeli).
        const TokenChip(),
        const SizedBox(width: 8),
        _rozet(context),
        const SizedBox(width: 10),
        // Dock'taki merkez balonun MİNİSİ — aynı hedef (sohbet), aynı işaret.
        // Eski hâli `forum_outlined` lilac @ inkLight zemindi: düşük kontrast
        // ("görünmüyor" şikayeti) ve dock'la alakasız ikinci bir işaretti.
        Pressable(
          onTap: () => Navigator.of(context).push(MaterialPageRoute(
              builder: (_) => const ConversationListScreen())),
          child: Container(
            width: 40,
            height: 40,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              gradient: RythoColors.primaryGradient,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(15),
                topRight: Radius.circular(15),
                bottomRight: Radius.circular(15),
                bottomLeft: Radius.circular(5),
              ),
              border: Border.all(
                  color: Colors.white.withValues(alpha: 0.22)),
              boxShadow: const [
                BoxShadow(color: RythoColors.magentaGlow, blurRadius: 14),
              ],
            ),
            child: const Text('✦',
                style: TextStyle(fontSize: 17, color: Colors.white)),
          ),
        ),
      ]),
    );
  }
}

