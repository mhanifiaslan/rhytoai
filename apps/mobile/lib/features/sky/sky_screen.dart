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
import '../../widgets/glass.dart';
import '../../widgets/motion.dart';
import '../../widgets/nebula_widgets.dart';
import '../../widgets/reading_card.dart';
import '../../widgets/star_burst.dart';
import '../../widgets/token_chip.dart';
import '../shell/app_shell.dart' show shellTabProvider;
import '../paywall/paywall_screen.dart';
import '../paywall/plus_locked_card.dart';
import 'calendar_strip.dart';
import 'sign_story_screen.dart';
import 'sky_now_screen.dart';
import '../../widgets/basis_sheet.dart';
import '../chat/chat_screen.dart';
import '../../core/api.dart' show friendlyError;
import '../profile/diary_screen.dart' show DiaryScreen;
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
            ref.invalidate(signalsProvider);
            ref.invalidate(dailyReadingProvider);
            // Abonelik durumu da tazelensin: satın alma sonrası webhook
            // sunucuya islenene kadar kisa bir gecikme olabiliyor.
            ref.invalidate(subscriptionProvider);
            // Takvim şeridi de tazelensin: sunucu penceresi gün dönümünde
            // kayıyor ve abonelik değişince kilit satırları açılıyor.
            ref.invalidate(transitCalendarProvider);
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
                onAvatarTap: () =>
                    ref.read(shellTabProvider.notifier).state = 3,
              ).animate(delay: next()).fadeIn(duration: 360.ms).slideY(
                  begin: 0.08, curve: Curves.easeOutCubic),
              const SizedBox(height: RythoSpace.lg),

              // Burç şeridi — HİKÂYE halkası. Dokunma tam ekran okuyucu açar.
              // Yeri SABİT: her zaman başlığın hemen altında, sosyal medya
              // durum çubuğu gibi. Hiçbir bölüm (sinyaller dahil) bunu aşağı
              // itmez — R2-S6'da bir kez itilmişti, geri alındı.
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

              // Takvim şeridi (R5-6) — burç şeridinin HEMEN ALTINDA, aynı
              // ölçü diliyle. "Önündeki 30 gün" artık Atlas'ın içinde
              // aranan bir liste değil, ana ekranda duran bir zaman
              // çizgisi. Ücretsiz hesapta da görünür: tarih ve tema
              // gerçek, kilitli olan yalnız okuma.
              const SizedBox(height: RythoSpace.sm),
              const CalendarStrip()
                  .animate(delay: next())
                  .fadeIn(duration: 360.ms)
                  .slideY(begin: 0.08, curve: Curves.easeOutCubic),

              // ---------- SİNYALLER (R2-S3) ----------
              // "Rytho bugün senin için fark etti": sorulmadan konuşan
              // astrolog. Bölüm kendi kendini gizler (veri yok / hata /
              // doğum kaydı eksik) — ana ekran sinyalsiz de ayakta durur.
              const _SignalsSection()
                  .animate(delay: next())
                  .fadeIn(duration: 360.ms)
                  .slideY(begin: 0.06, curve: Curves.easeOutCubic),

              // ---------- BUGÜN SENİN İÇİN ----------
              // Seri rozeti başlıktan buraya indi (R2-S3): motivasyon
              // sinyaller, seri yan ürün — "neden her gün açayım"ın cevabı
              // artık rozet değil, gökyüzünün bugün söyledikleri.
              SectionHeader(
                l10n.todaysInsight,
                trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                  Text(
                    // Tarih biçimi de dile bağlı: sabit 'tr_TR' İngilizce
                    // arayüzde Türkçe ay adı gösteriyordu.
                    DateFormat('d MMMM',
                            Localizations.localeOf(context).toLanguageTag())
                        .format(DateTime.now()),
                    style: RythoType.dataSmall,
                  ),
                  const SizedBox(width: RythoSpace.sm),
                  _StreakRozet(streak: streak, celebrate: _streakYeni),
                ]),
              ).animate(delay: next()).fadeIn(duration: 360.ms),

              // Genel burç kartı BURADAN KALKTI (R3-2, cihaz bulgusu):
              // hikâye halkasındaki metnin aynısıydı — aynı sayfada iki kez
              // durması "tekrarlı bilgi" şikayetinin kaynağıydı. Genel yorum
              // artık YALNIZ halkada; içgörü başlığı kişiye özel okumanın.
              //
              // Rytho+: kişiye özel okuma. Abone değilse istek atılmaz;
              // kilitli kart gösterilir ve paywall ancak dokununca açılır.
              daily.when(
                loading: () => const Padding(
                  padding: EdgeInsets.all(RythoSpace.xl),
                  child: Center(child: AstrolabeSpinner()),
                ),
                error: (e, _) => Padding(
                  padding:
                      const EdgeInsets.symmetric(horizontal: RythoSpace.lg),
                  child: ErrorCard(
                    message: friendlyError(e, l10n),
                    onRetry: () => ref.invalidate(dailyReadingProvider),
                  ),
                ),
                data: (data) {
                  // Kullanıcı ilk değerini gördü (kilitli kart da değer
                  // anlatır): tanıtım paywall'ı buradan tetiklenir —
                  // eskiden genel burç kartındaydı, kart kalktı (R3-2).
                  _maybeShowIntroPaywall();
                  return data == null
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
                        )
                          .animate(delay: next())
                          .fadeIn(duration: 380.ms)
                          .slideY(begin: 0.06, curve: Curves.easeOutCubic)
                          .then()
                          .shimmer(
                              duration: 900.ms,
                              color: RythoColors.gold
                                  .withValues(alpha: 0.12));
                },
              ),

              // "ŞU AN" bölümü Atlas'a taşındı (R3-2): gökyüzü durumu
              // haritanın yanında yaşar; bu ekran "bugün senin için"
              // anlatısına odaklandı.

              // GÜNLÜĞÜM kartı BURADAN KALKTI (1.5.1+18 cihaz turu): akışın
              // en dibinde, kaydırılmadan görünmeyen bir yerde duruyordu —
              // "yeri olmamış". Günlük artık başlığın sağ üst köşesinde
              // sabit bir düğme (bkz. _Header): ekranın en görünür, hiç
              // kaymayan noktası. Sohbet oraya ikinci bir kapıya ihtiyaç
              // duymuyordu, dock'un merkezinde zaten duruyor.
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

/// Seri rozeti + kutlama (R12-C1, R2-S3'te başlıktan bölüm başlığına indi).
///
/// Kutlama: rozet 1→1.25→1 şişer (pop), arkasında 12 kıvılcımlık mini
/// patlama. Profildeki sayı Firestore turundan henüz dönmediyse yeni sayı
/// [celebrate]'ten gösterilir; kullanıcı artışı ANINDA görür.
class _StreakRozet extends StatelessWidget {
  const _StreakRozet({required this.streak, this.celebrate});

  final int streak;

  /// Seri bu oturumda büyüdüyse yeni sayı. Null: vurgu yok.
  final int? celebrate;

  @override
  Widget build(BuildContext context) {
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
}

/// Üst şerit: degrade halkalı avatar + selamlama + jeton hapı + sohbet ikonu.
class _Header extends StatelessWidget {
  const _Header({
    required this.greeting,
    required this.name,
    required this.photoUrl,
    required this.onAvatarTap,
  });

  final String greeting;
  final String name;
  final String? photoUrl;

  /// Avatara dokunuş — Profil sekmesine geçiş (U1).
  final VoidCallback onAvatarTap;

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
        const SizedBox(width: 10),
        // GÜNLÜĞÜM. Buradaki düğme eskiden sohbete gidiyordu — ama sohbet
        // dock'un MERKEZİNDE zaten duruyor; aynı hedefe ikinci bir kapı
        // başlıkta yer harcıyordu. Günlüğün ise sabit bir kapısı yoktu:
        // akışın içinde bir karttı ve kaydırılmadan görünmüyordu.
        //
        // Günlük stratejik: kullanıcı yaşantısını not ettikçe okumalar
        // kişiselleşiyor. O yüzden ekranın en sabit, en görünür köşesini
        // o alıyor (cihaz turu kararı, 1.5.1+18).
        Pressable(
          onTap: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const DiaryScreen())),
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
            child: const Icon(Icons.auto_stories_rounded,
                size: 19, color: Colors.white),
          ),
        ),
      ]),
    );
  }
}

// `_DiaryQuickCard` KALDIRILDI (1.5.1+18): günlük girişi akıştaki bir
// karttan başlığın sağ üst köşesindeki sabit düğmeye taşındı. Kart
// ekranın dibinde kalıyor ve kaydırılmadan görünmüyordu; günlük gibi
// her gün tekrarlanacak bir ritüelin kapısı kaymayan bir yerde durmalı.

class _SignalsSection extends ConsumerWidget {
  const _SignalsSection();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final sinyaller = ref.watch(signalsProvider).value ?? const [];
    if (sinyaller.isEmpty) return const SizedBox.shrink();

    // En yakın kesinleşme: kartlarda tarih zaten geçiyor; bu satır güne
    // tek bakışta çapa atar ("bu hafta ne zaman önemli").
    final tarihler = [
      for (final s in sinyaller)
        if (s['exact_on_local'] is String &&
            (s['exact_on_local'] as String).isNotEmpty)
          (exactOn: s['exact_on'] as String? ?? '',
           local: s['exact_on_local'] as String),
    ]..sort((a, b) => a.exactOn.compareTo(b.exactOn));

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SectionHeader(
          l10n.signalsSection,
          trailing: tarihler.isEmpty
              ? null
              : Text('✦ ${l10n.signalUpcoming(tarihler.first.local)}',
                  style: RythoType.dataSmall
                      .copyWith(color: RythoColors.gold)),
        ),
        for (final sinyal in sinyaller) _SignalCard(sinyal: sinyal),
        const SizedBox(height: RythoSpace.sm),
      ],
    );
  }
}

/// Tek sinyal kartı: tema çipi + başlık cümlesi + (varsa) abone yorumu +
/// "Neden?" — dokunuş dayanak alt-sayfasını açar (R2-S2).
class _SignalCard extends StatelessWidget {
  const _SignalCard({required this.sinyal});

  final Map<String, dynamic> sinyal;

  void _openBasis(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    // Sayfaya karttaki CÜMLE de gider (R3-1): kullanıcı "neye dayanıyor"
    // sorusunu abone yorumuna sorduysa sayfa o cümleyle açılmalı.
    final insight = sinyal['insight'] as String?;
    final kartCumlesi = (insight != null && insight.isNotEmpty)
        ? insight
        : (sinyal['headline'] as String? ?? '');
    showSignalBasisSheet(
      context,
      {...sinyal, 'card_text': kartCumlesi},
      onAsk: () {
        Navigator.of(context).pop();
        // R4-1: soruya KARTTAKİ cümle + dayanağı birlikte gider — model
        // kullanıcının okuduğu cümleyi açar, "başka konu" hissi biter.
        Navigator.of(context).push(MaterialPageRoute(
          builder: (_) => ChatScreen(
              initialText: l10n.signalAskPrefill(
                  kartCumlesi,
                  (sinyal['technical'] as String?) ?? '')),
        ));
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final tema = sinyal['theme'] as String? ?? 'inner';

    // Kartın metni GÜNDELİK dildedir (R2-S6). Abonede LLM yorumu, ücretsiz
    // katmanda tema+ton şablonu — ikisi de "hayatında ne oluyor" anlatır.
    // "Kiron natal Venüs ile üçgen" cümlesi buradan kalktı; teknik dayanak
    // "Neye dayanıyor?" sayfasında, kendi başlığı altında duruyor.
    final insight = sinyal['insight'] as String?;
    final metin = (insight != null && insight.isNotEmpty)
        ? insight
        : (sinyal['headline'] as String? ?? '');
    final zaman = sinyal['timing_local'] as String?;

    return GlassPanel(
      margin: const EdgeInsets.symmetric(
          horizontal: RythoSpace.lg, vertical: 5),
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 11),
      onTap: () => _openBasis(context),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        // Tema başlığı: kullanıcı bir bakışta "bu kariyer mi ilişki mi"
        // sorusunu cevaplayabilmeli — ikon + büyük ad, silik değil.
        Row(children: [
          Text(kThemeIcons[tema] ?? '✦',
              style: const TextStyle(fontSize: 15)),
          const SizedBox(width: 7),
          Expanded(
            child: Text(sinyal['theme_local'] as String? ?? '',
                style: RythoText.display(13.5,
                    w: FontWeight.w700, color: RythoColors.lilac)),
          ),
          if (zaman != null && zaman.isNotEmpty)
            Text(zaman,
                style: RythoType.dataSmall
                    .copyWith(color: RythoColors.gold)),
        ]),
        const SizedBox(height: 7),
        Text(metin, style: RythoText.body(13.5, height: 1.45)),
        const SizedBox(height: 8),
        Text('${l10n.signalWhy} →',
            style: RythoText.body(11.5,
                color: RythoColors.parchmentDim, w: FontWeight.w600)),
      ]),
    );
  }
}

