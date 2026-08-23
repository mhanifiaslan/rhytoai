import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart' show StateProvider;

import '../../core/device_claim.dart';
import '../../core/notifications.dart'
    show PendingNotification, pendingNotificationProvider;
import '../../core/providers.dart'
    show OnboardOutcome, justOnboardedProvider, profileProvider;
import '../../widgets/big_three_reveal.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../l10n/app_localizations.dart';
import '../../widgets/glass.dart';
import '../atlas/atlas_screen.dart';
import '../chat/chat_screen.dart';
import '../chat/conversation_list_screen.dart';
import '../friends/friends_screen.dart';
import '../profile/profile_screen.dart';
import '../sky/sky_screen.dart';

/// Aktif sekme — ekranlar (örn. promo banner) sekme değiştirebilsin diye
/// Riverpod üzerinden paylaşılır. 0: Gökyüzü, 1: Atlas, 2: Arkadaşlar, 3: Profil.
///
/// Eski "Meclis" sekmesinin yerini Arkadaşlar aldı: gönderi akışı, kanallar ve
/// DM (serbest metinli kullanıcı içeriği) kaldırıldı; yerine serbest metin
/// içermeyen arkadaş katmanı geldi — seri görünürlüğü, kapalı kümeden hazır
/// tepkiler ve günlük ikili dinamik.
final shellTabProvider = StateProvider<int>((_) => 0);

/// Ana kabuk: yıldız alanı zemin + 4 sekme + merkez degrade AI butonu
/// (Rytho sohbetini açar). Kehanet araçlarına ana ekran kartlarından gidilir.
class AppShell extends ConsumerStatefulWidget {
  const AppShell({super.key});

  @override
  ConsumerState<AppShell> createState() => _AppShellState();
}

class _AppShellState extends ConsumerState<AppShell> {
  @override
  void initState() {
    super.initState();
    // Tek cihaz kilidi: abonelik başka cihazda kayıtlıysa devralma onayı
    // BURADA sorulur — kullanıcı 409 duvarına çarpmadan önce, girişin hemen
    // ardından. Oturum başına bir kez; ücretsiz kullanıcı hiç görmez.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      maybeConfirmDeviceTakeover(context, ref);
      _buyukUcluPerdesi();
      // Soğuk açılış: check-in niyeti dinleyiciden ÖNCE yazılmış olabilir.
      final bekleyen = ref.read(pendingNotificationProvider);
      if (bekleyen != null && bekleyen.type == 'checkin') {
        _checkinNiyeti(bekleyen);
      }
    });
  }

  /// Onboarding'in finali (R12-B1): kullanıcı doğum verisini az önce verdiyse
  /// Büyük Üçlü perdesi burada açılır — onboarding ekranında açılamaz, çünkü
  /// `onboardingCompleted` yazımı iner inmez `_Gate` o ekranı söker.
  void _buyukUcluPerdesi() {
    final sonuc = ref.read(justOnboardedProvider);
    if (sonuc == null) return;
    ref.read(justOnboardedProvider.notifier).state = null;
    final profil = ref.read(profileProvider).value ?? const {};
    final gunes = profil['sunSign'] as String?;
    final ay = profil['moonSign'] as String?;
    final yukselen = profil['ascendant'] as String?;
    // Harita hesaplanamadıysa perde açılmaz — yalan rozet göstermeme
    // kuralı (core/birth_record.dart). Ama artık SESSİZ değil (O3):
    // kullanıcı verisinin kaydedildiğini ve haritanın sonra çizileceğini
    // duyar; rozetlerin yokluğu açıklanamayan bir davranış olmaktan çıkar.
    if (sonuc == OnboardOutcome.chartMissing ||
        gunes == null ||
        ay == null) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content:
              Text(AppLocalizations.of(context).birthRecordSavedNoChart)));
      return;
    }
    showBigThreeReveal(context, sun: gunes, moon: ay, ascendant: yukselen);
  }

  /// Akşam check-in bildirimi (KA5): dokunma sohbeti SORUYLA açar.
  /// Soru bayatsa (dünün bildirimi bugün açıldı) yalnız konu listesi
  /// açılır — dünkü soruyu bugün sormak yanıltıcı olur.
  void _checkinNiyeti(PendingNotification niyet) {
    ref.read(pendingNotificationProvider.notifier).clear();
    final soru = niyet.data['q'] ?? '';
    final gun = niyet.data['q_date'] ?? '';
    final bugun = DateTime.now().toIso8601String().substring(0, 10);
    if (soru.isNotEmpty && gun == bugun) {
      Navigator.of(context).push(MaterialPageRoute(
          builder: (_) => ChatScreen(initialText: soru, source: 'checkin')));
    } else {
      Navigator.of(context).push(MaterialPageRoute(
          builder: (_) => const ConversationListScreen()));
    }
  }

  @override
  Widget build(BuildContext context) {
    // Bekleyen check-in niyeti: bildirime dokunulduğunda uygulama hangi
    // hâlde olursa olsun (soğuk/sıcak) buradan işlenir. Daily niyetini
    // SkyScreen tüketir (ilgili sinyal kartının dayanak sayfası).
    ref.listen<PendingNotification?>(pendingNotificationProvider,
        (previous, next) {
      if (next != null && next.type == 'checkin' && mounted) {
        _checkinNiyeti(next);
      }
    });
    final index = ref.watch(shellTabProvider);
    final l10n = AppLocalizations.of(context);
    // Etiketler dile göre üretildiği için const olamaz.
    final tabs = [
      (icon: Icons.home_outlined, activeIcon: Icons.home_rounded,
       label: l10n.tabSky),
      (icon: Icons.donut_large_outlined, activeIcon: Icons.donut_large_rounded,
       label: l10n.tabAtlas),
      (icon: Icons.people_outline_rounded, activeIcon: Icons.people_rounded,
       label: l10n.tabFriends),
      (icon: Icons.person_outline_rounded, activeIcon: Icons.person_rounded,
       label: l10n.tabProfile),
    ];
    return CosmicScaffold(
      extendBody: true,
      body: Stack(children: [
        for (var i = 0; i < 4; i++)
          IgnorePointer(
            ignoring: index != i,
            child: AnimatedOpacity(
              opacity: index == i ? 1 : 0,
              duration: const Duration(milliseconds: 280),
              curve: Curves.easeOutCubic,
              child: AnimatedSlide(
                offset: index == i ? Offset.zero : const Offset(0, 0.012),
                duration: const Duration(milliseconds: 280),
                curve: Curves.easeOutCubic,
                child: const [
                  SkyScreen(),
                  AtlasScreen(),
                  FriendsScreen(),
                  ProfileScreen(),
                ][i],
              ),
            ),
          ),
      ]),
      bottomNavigationBar: CosmicDock(
        items: tabs,
        index: index,
        onChanged: (i) => ref.read(shellTabProvider.notifier).state = i,
        // Sohbet artık KONU listesine açılır (Revize R4): kaldığı yerden
        // devam ya da yeni konu — AI uygulamalarındaki desen.
        onCenterTap: () => Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => const ConversationListScreen()),
        ),
      ),
    );
  }
}
