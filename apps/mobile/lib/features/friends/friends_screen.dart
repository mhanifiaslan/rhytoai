import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/analytics.dart';
import '../../core/contact_match.dart';
import '../../core/deep_links.dart';
import '../../core/friends.dart';
import '../../core/providers.dart';
import '../../core/safety.dart';
import '../../theme/rytho_theme.dart';
import '../../theme/rytho_tokens.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/glass.dart';
import '../../widgets/nebula_widgets.dart';
import '../profile/account_screen.dart' show AccountScreen;
import '../profile/diary_screen.dart' show DiaryScreen;
import 'contacts_screen.dart' show ContactsScreen;
import 'friend_detail_screen.dart' show FriendDetailScreen, reactionLabel;
import 'reaction_sheet.dart' show showReactionSheet;
import 'relationship_screen.dart' show RelationshipScreen;
import '../../core/api.dart' show friendlyError;
import '../../l10n/app_localizations.dart';

/// ARKADAŞLAR — serbest metin içermeyen sosyal katman.
///
/// Görünen her şey türetilmiş veridir: seri, burç ve "bugün okumasını yaptı
/// mı". Arkadaşın doğum verisi hiçbir zaman istemciye gelmez. Etkileşim
/// yalnızca [kReactions] içindeki kapalı kümeden seçilen hazır tepkilerdir;
/// yazı kutusu bilinçli olarak yoktur.
class FriendsScreen extends ConsumerWidget {
  const FriendsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final profile = ref.watch(profileProvider).value;
    final friendsAsync = ref.watch(friendsProvider);
    final username = profile?['username'] as String?;

    // Davet bağlantısıyla açıldıysa ekleme sayfasını kullanıcı adı dolu
    // olarak aç. Bağlantı uygulama açılırken de gelebildiği için burada
    // ele alınıyor: bu noktada oturum ve onboarding tamamlanmış oluyor.
    _handlePendingInvite(context, ref, username);

    return CosmicScaffold(
      appBar: AppBar(
        title: Text(l10n.friendsTitle),
        actions: [
          // Görünür, dolgulu düğme (Revize R6). Eski hâli AppBar varsayılan
          // renkli IconButton'dı ve kullanıcı adı yokken disabled-griydi —
          // "görünmez" şikayetinin iki sebebi. Devre dışı bırakmak yerine
          // dokununca SEBEBİ söylüyor: görünmez düğme değil, açıklayan düğme.
          Padding(
            padding: const EdgeInsets.only(right: RythoSpace.md),
            child: Pressable(
              onTap: () {
                if (username == null) {
                  ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text(l10n.addFriendNeedsUsername)));
                  return;
                }
                _showAddFriendSheet(context, username);
              },
              child: Container(
                width: 40,
                height: 40,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: RythoColors.inkLighter,
                  border: Border.all(
                      color: RythoColors.lilac.withValues(alpha: 0.55)),
                ),
                child: const Icon(Icons.person_add_alt_1_rounded,
                    size: 20, color: RythoColors.parchment),
              ),
            ),
          ),
        ],
      ),
      body: ListView(padding: const EdgeInsets.only(bottom: 120), children: [
        if (username == null)
          const _UsernameSetupPanel()
        else
          _MyCardPanel(
            username: username,
            streakCount: (profile?['streakCount'] as num?)?.toInt() ?? 0,
          ),
        _InboxPanel(friends: friendsAsync.value ?? const []),
        // Rehber önerileri (Revize R3 → F1): panel artık HER ZAMAN mount —
        // ayar kapalıysa/telefon doğrusuzsa/izin yoksa sessiz boşluk yerine
        // yol gösteren kart çizer. Sonuçlar bellekte yaşar; ne istemci ne
        // sunucu listeyi saklar.
        _ContactsEntry(ayarAcik: profile?['contactMatch'] == true),
        friendsAsync.when(
          loading: () => const Padding(
            padding: EdgeInsets.only(top: 48),
            child: Center(child: AstrolabeSpinner()),
          ),
          error: (e, _) => Padding(
            padding: const EdgeInsets.all(24),
            child: Text(friendlyError(e, l10n),
                style: RythoText.body(13, color: RythoColors.parchmentDim)),
          ),
          data: (friends) => _FriendsList(friends: friends),
        ),
      ]),
    );
  }
}

/// Kullanıcı adı henüz alınmamışsa: arkadaşların seni bulabilmesi için gerekli.
class _UsernameSetupPanel extends StatefulWidget {
  const _UsernameSetupPanel();

  @override
  State<_UsernameSetupPanel> createState() => _UsernameSetupPanelState();
}

class _UsernameSetupPanelState extends State<_UsernameSetupPanel> {
  final _controller = TextEditingController();
  String? _error;
  bool _busy = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final l10n = AppLocalizations.of(context);
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await claimUsername(_controller.text);
    } on UsernameException catch (e) {
      if (mounted) setState(() => _error = usernameErrorText(l10n, e.error));
    } catch (e) {
      if (mounted) setState(() => _error = friendlyError(e, l10n));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  /// Veri katmanı kod döndürür, metni burada çözüyoruz.
  static String usernameErrorText(AppLocalizations l10n, UsernameError e) =>
      switch (e) {
        UsernameError.empty => l10n.usernameEmpty,
        UsernameError.invalid => l10n.usernameInvalid,
        UsernameError.taken => l10n.usernameTaken,
      };

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return GlassPanel(
      label: l10n.usernameLabel,
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(l10n.usernameHeadline, style: RythoText.display(19)),
        const SizedBox(height: 6),
        Text(
          l10n.usernameBody,
          style: RythoText.body(12.5, color: RythoColors.parchmentDim),
        ),
        const SizedBox(height: 14),
        TextField(
          controller: _controller,
          autocorrect: false,
          enableSuggestions: false,
          maxLength: 20,
          style: RythoText.body(15),
          decoration: InputDecoration(
            prefixText: '@',
            hintText: l10n.usernameHint,
            counterText: '',
            errorText: _error,
            hintStyle: RythoText.body(15, color: RythoColors.parchmentDim),
          ),
        ),
        const SizedBox(height: 12),
        GoldButton(text: l10n.claimUsername, busy: _busy, onPressed: _submit),
      ]),
    );
  }
}

/// Rehber ekranına KOMPAKT giriş (I-turu). Eski hâli büyük açıklama
/// kartları/uzun liste çiziyordu ("çok büyük" şikâyeti). Artık tek satır:
/// başlık + duruma göre alt yazı (N kişi uygulamada / aç / doğrula) +
/// ok. Dokununca tam ekran [ContactsScreen] açılır (aktif/pasif + davet).
class _ContactsEntry extends ConsumerWidget {
  const _ContactsEntry({required this.ayarAcik});

  final bool ayarAcik;

  void _ac(BuildContext context) => Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const ContactsScreen()));

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);

    String altYazi;
    VoidCallback onTap;

    if (!ayarAcik) {
      altYazi = l10n.contactsFindEnable;
      onTap = () async {
        await setContactMatch(true);
        ref.invalidate(profileProvider);
        ref.invalidate(contactMatchesProvider);
        if (context.mounted) _ac(context);
      };
    } else {
      final sonuc = ref.watch(contactMatchesProvider);
      altYazi = switch (sonuc) {
        AsyncData(:final value) => switch (value.blocker) {
            ContactMatchBlocker.telefonYok => l10n.contactsFindVerifyPhone,
            ContactMatchBlocker.izinYok => l10n.contactMatchPermTitle,
            null => l10n.contactsFindActive(value.active.length),
          },
        _ => '…',
      };
      onTap = () => _ac(context);
    }

    return GlassPanel(
      child: Pressable(
        onTap: onTap,
        child: Row(children: [
          Container(
            width: 38,
            height: 38,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: RythoColors.inkLight,
              border: Border.all(color: RythoColors.glassStroke),
            ),
            child: const Icon(Icons.contacts_outlined,
                size: 19, color: RythoColors.parchment),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(l10n.contactsFindEntry,
                      style: RythoText.body(14, w: FontWeight.w600)),
                  const SizedBox(height: 2),
                  Text(altYazi,
                      style: RythoText.body(
                          12, color: RythoColors.parchmentDim)),
                ]),
          ),
          const Icon(Icons.chevron_right_rounded,
              size: 20, color: RythoColors.parchmentDim),
        ]),
      ),
    );
  }
}

/// SEN kartı — TEK SATIR (R3-4, cihaz bulgusu: "koca koca kartlar var").
///
/// @ad + seri rozeti solda; sağda üç küçük ikon: kullanıcı adını düzenle,
/// davet bağlantısını kopyala, Günlüğüm. Seri görünürlük anahtarı buradan
/// KALKTI — zaten Profil → Gizlilik'te duruyor (aynı Firestore alanı);
/// bir gizlilik ayarının sosyal ekranda yer kaplaması gerekmiyor.
class _MyCardPanel extends StatelessWidget {
  const _MyCardPanel({
    required this.username,
    required this.streakCount,
  });

  final String username;
  final int streakCount;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);

    Widget ikon(String tooltip, IconData icon, VoidCallback onTap) =>
        IconButton(
          tooltip: tooltip,
          visualDensity: VisualDensity.compact,
          icon: Icon(icon, size: 18, color: RythoColors.lilac),
          onPressed: onTap,
        );

    return GlassPanel(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      child: Row(children: [
        Expanded(
          child: Text('@$username',
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: RythoText.display(16, w: FontWeight.w600)),
        ),
        StreakBadge(count: streakCount),
        const SizedBox(width: 4),
        // Kullanıcı adı bir dönem yalnızca BİR KEZ yazılabiliyordu; düzeltme
        // yolu bu ikon (AccountScreen).
        ikon(l10n.edit, Icons.edit_outlined, () {
          Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const AccountScreen()));
        }),
        ikon(l10n.copyInviteLink, Icons.link_rounded, () async {
          await Clipboard.setData(
              ClipboardData(text: inviteLinkFor(username)));
          if (context.mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text(l10n.inviteLinkCopied)));
          }
        }),
        // Günlüğüm (R3-4): "kişi kendisiyle ilgili günlükleri kendi
        // kartından takip edebilsin" — Profil listesinden buraya taşındı.
        ikon(l10n.profileDiaryRow, Icons.edit_note_rounded, () {
          Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const DiaryScreen()));
        }),
      ]),
    );
  }
}

/// Bana gelen hazır tepkiler. Dokununca okundu sayılır ve silinir.
class _InboxPanel extends ConsumerWidget {
  const _InboxPanel({required this.friends});

  final List<Friend> friends;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final nudges = ref.watch(myNudgesProvider).value ?? const [];
    if (nudges.isEmpty) return const SizedBox.shrink();

    String nameOf(String? uid) {
      for (final friend in friends) {
        if (friend.uid == uid) return friend.name;
      }
      return l10n.aFriend;
    }

    return GlassPanel(
      label: l10n.inboxLabel,
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        for (final nudge in nudges.take(6))
          if (kReactions[nudge['reaction']] case final emoji?)
            InkWell(
              borderRadius: BorderRadius.circular(12),
              onTap: () => dismissNudge(nudge['id'] as String),
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: Row(children: [
                  Text(emoji, style: const TextStyle(fontSize: 18)),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      '${nameOf(nudge['fromUid'] as String?)} · '
                      '${reactionLabel(l10n, nudge['reaction'] as String)}',
                      style: RythoText.body(13.5),
                    ),
                  ),
                  const Icon(Icons.close_rounded,
                      size: 16, color: RythoColors.parchmentDim),
                ]),
              ),
            ),
      ]),
    );
  }
}

class _FriendsList extends StatelessWidget {
  const _FriendsList({required this.friends});

  final List<Friend> friends;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    if (friends.isEmpty) {
      return Padding(
        padding: const EdgeInsets.fromLTRB(28, 40, 28, 0),
        child: Column(children: [
          const Text('🛰️', style: TextStyle(fontSize: 34)),
          const SizedBox(height: 12),
          Text(l10n.noFriendsYet,
              style: RythoText.display(18), textAlign: TextAlign.center),
          const SizedBox(height: 6),
          Text(
            l10n.noFriendsBody,
            style: RythoText.body(12.5, color: RythoColors.parchmentDim),
            textAlign: TextAlign.center,
          ),
        ]),
      );
    }

    final incoming =
        friends.where((f) => f.status == FriendStatus.incoming).toList();
    final accepted =
        friends.where((f) => f.status == FriendStatus.accepted).toList();
    final outgoing =
        friends.where((f) => f.status == FriendStatus.outgoing).toList();

    return Column(children: [
      if (incoming.isNotEmpty) ...[
        const SectionDivider(),
        _sectionTitle(l10n.incomingRequests),
        for (final friend in incoming) _RequestTile(friend: friend),
      ],
      if (accepted.isNotEmpty) ...[
        const SectionDivider(),
        _sectionTitle(l10n.yourFriends),
        for (final (i, friend) in accepted.indexed)
          _FriendTile(friend: friend)
              .animate(delay: Duration(milliseconds: 40 * i))
              .fadeIn(duration: 300.ms),
      ],
      if (outgoing.isNotEmpty) ...[
        const SectionDivider(),
        _sectionTitle(l10n.pendingInvites),
        for (final friend in outgoing) _PendingTile(friend: friend),
      ],
    ]);
  }

  Widget _sectionTitle(String text) => Padding(
        padding: const EdgeInsets.fromLTRB(20, 4, 20, 2),
        child: Text(text, style: RythoText.mono(11, color: RythoColors.parchmentDim)),
      );
}

/// Arkadaş satırı — SLİM (R3-4, cihaz bulgusu: "az bilgi çok yer").
///
/// Baş harf avatarı + ad + tek satır durum; sağda İKİ eylem ikonu:
/// ⚡ tepki (KART AÇILMADAN — dokununca tepki sayfası, seçim anında
/// gider) ve 🪐 ilişki (dört eksenli okuma). Satırın kendisi arkadaş
/// detayını ("bugün aranızda") açar.
class _FriendTile extends ConsumerWidget {
  const _FriendTile({required this.friend});

  final Friend friend;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final durum = friend.streakVisible
        ? (friend.readToday ? l10n.readToday : l10n.notReadToday)
        : l10n.streakHidden;
    final durumRenk = friend.streakVisible && friend.readToday
        ? RythoColors.goldBright
        : RythoColors.parchmentDim;

    return GlassPanel(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 3),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      onTap: () => Navigator.of(context).push(MaterialPageRoute(
          builder: (_) => FriendDetailScreen(friend: friend))),
      child: Row(children: [
        CircleAvatar(
          radius: 17,
          backgroundColor: RythoColors.lilac.withValues(alpha: 0.16),
          child: Text(
              friend.name.isEmpty ? '?' : friend.name[0].toUpperCase(),
              style: RythoText.display(14, color: RythoColors.lilac)),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(friend.name,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: RythoText.body(14.5, w: FontWeight.w600)),
                const SizedBox(height: 1),
                Row(children: [
                  if (friend.sunSign != null)
                    Padding(
                      padding: const EdgeInsets.only(right: 6),
                      child: Text(friend.sunSign!,
                          style: RythoText.label(10.5,
                              color: RythoColors.lilac)),
                    ),
                  Flexible(
                    child: Text(durum,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: RythoText.body(11, color: durumRenk)),
                  ),
                ]),
              ]),
        ),
        // Tepki: kart açılmadan, iki dokunuş (⚡ → seçim).
        IconButton(
          tooltip: l10n.sendReaction,
          visualDensity: VisualDensity.compact,
          icon: const Text('⚡', style: TextStyle(fontSize: 16)),
          onPressed: () => showReactionSheet(context, ref, friend),
        ),
        // İlişki eksenleri (R2-L1) satırdan tek dokunuş uzakta.
        IconButton(
          tooltip: l10n.relationshipOpen,
          visualDensity: VisualDensity.compact,
          icon: const Text('🪐', style: TextStyle(fontSize: 15)),
          onPressed: () => Navigator.of(context).push(MaterialPageRoute(
              builder: (_) => RelationshipScreen(friend: friend))),
        ),
      ]),
    );
  }
}

class _RequestTile extends StatelessWidget {
  const _RequestTile({required this.friend});

  final Friend friend;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return GlassPanel(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 5),
      child: Row(children: [
        Expanded(child: Text(friend.name, style: RythoText.display(16))),
        TextButton(
          onPressed: () => removeFriend(friend.uid),
          child: Text(l10n.ignore,
              style: RythoText.label(12, color: RythoColors.parchmentDim)),
        ),
        const SizedBox(width: 4),
        SizedBox(
          width: 104,
          child: GoldButton(
            text: l10n.accept,
            onPressed: () => acceptFriendRequest(friend.uid),
          ),
        ),
      ]),
    );
  }
}

class _PendingTile extends StatelessWidget {
  const _PendingTile({required this.friend});

  final Friend friend;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return GlassPanel(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 5),
      child: Row(children: [
        Expanded(
          child: Text(friend.name,
              style: RythoText.body(14.5, color: RythoColors.parchmentDim)),
        ),
        Text(l10n.pending,
            style: RythoText.label(11, color: RythoColors.parchmentDim)),
        const SizedBox(width: 8),
        IconButton(
          tooltip: l10n.withdrawInvite,
          icon: const Icon(Icons.close_rounded, size: 18),
          onPressed: () => removeFriend(friend.uid),
        ),
      ]),
    );
  }
}

// ---------------------------------------------------------------------------
// Arkadaş ekleme
// ---------------------------------------------------------------------------

/// Bekleyen daveti ekleme sayfasını açarak ele alır.
///
/// Kendi davetini açmak anlamsız olduğu için sessizce yok sayılır — kullanıcı
/// kendi bağlantısını test ederken hata mesajıyla karşılaşmamalı.
void _handlePendingInvite(
    BuildContext context, WidgetRef ref, String? myUsername) {
  final invite = ref.watch(pendingInviteProvider);
  if (invite == null || myUsername == null) return;

  // Durum değişikliği build sırasında yapılamaz.
  WidgetsBinding.instance.addPostFrameCallback((_) {
    if (!context.mounted) return;
    ref.read(pendingInviteProvider.notifier).clear();
    if (invite == myUsername) return;
    _showAddFriendSheet(context, myUsername, prefill: invite);
  });
}

Future<void> _showAddFriendSheet(BuildContext context, String myUsername,
    {String? prefill}) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: RythoColors.inkLight,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(22)),
      side: BorderSide(color: RythoColors.glassStroke),
    ),
    // viewInsets sayfanın KENDİ context'inden okunmalı: dıştaki context
    // klavye açılınca yeniden kurulmuyor, dolayısıyla dolgu 0 kalıyor ve
    // giriş alanı klavyenin altında gizleniyordu.
    builder: (sheetContext) => Padding(
      padding: EdgeInsets.only(
          bottom: MediaQuery.of(sheetContext).viewInsets.bottom),
      child: _AddFriendSheet(myUsername: myUsername, prefill: prefill),
    ),
  );
}

class _AddFriendSheet extends StatefulWidget {
  const _AddFriendSheet({required this.myUsername, this.prefill});

  final String myUsername;

  /// Davet baglantisindan gelen kullanici adi; kutu dolu acilir.
  final String? prefill;

  @override
  State<_AddFriendSheet> createState() => _AddFriendSheetState();
}

class _AddFriendSheetState extends State<_AddFriendSheet> {
  final _controller = TextEditingController();
  String? _message;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    if (widget.prefill != null) _controller.text = widget.prefill!;
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    // l10n ve messenger await ÖNCESİ alınır: sonrasında context artık
    // güvenilir değil (use_build_context_synchronously).
    final l10n = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    final navigator = Navigator.of(context);

    setState(() {
      _busy = true;
      _message = null;
    });
    final username = _controller.text.trim().toLowerCase();
    try {
      if (username == widget.myUsername) {
        setState(() => _message = l10n.cannotAddSelf);
        return;
      }
      final uid = await uidForUsername(username);
      if (uid == null) {
        setState(() => _message = l10n.userNotFound(username));
        return;
      }
      await sendFriendRequest(uid);
      Analytics.friendInviteSent();
      if (!mounted) return;
      navigator.pop();
      messenger.showSnackBar(
          SnackBar(content: Text(l10n.inviteSent(username))));
    } catch (e) {
      if (mounted) setState(() => _message = friendlyError(e, l10n));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 20, 20, 24),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Text(l10n.addFriend.toUpperCase(),
              style: RythoText.mono(11, color: RythoColors.parchmentDim)),
          const SizedBox(height: 12),
          TextField(
            controller: _controller,
            autofocus: true,
            autocorrect: false,
            enableSuggestions: false,
            maxLength: 20,
            style: RythoText.body(15),
            onSubmitted: (_) => _send(),
            decoration: InputDecoration(
              prefixText: '@',
              hintText: l10n.usernameHint,
              counterText: '',
              errorText: _message,
              hintStyle: RythoText.body(15, color: RythoColors.parchmentDim),
            ),
          ),
          const SizedBox(height: 12),
          GoldButton(text: l10n.sendInvite, busy: _busy, onPressed: _send),
          const SizedBox(height: 10),
          TextButton.icon(
            onPressed: () async {
              await Clipboard.setData(
                  ClipboardData(text: inviteLinkFor(widget.myUsername)));
              if (context.mounted) Navigator.of(context).pop();
            },
            icon: const Icon(Icons.link_rounded, size: 18),
            label: Text(l10n.shareInviteInstead,
                style: RythoText.label(12)),
          ),
        ]),
      ),
    );
  }
}

/// Arkadaş menüsü: şikayet ve engelleme akışları korunur.
Future<void> showFriendSafetySheet(BuildContext context, Friend friend) async {
  final l10n = AppLocalizations.of(context);
  await showModalBottomSheet<void>(
    context: context,
    backgroundColor: RythoColors.inkLight,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(22)),
      side: BorderSide(color: RythoColors.glassStroke),
    ),
    builder: (sheetContext) => SafeArea(
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        ListTile(
          leading: const Icon(Icons.person_remove_rounded, size: 20),
          title: Text(l10n.removeFriend, style: RythoText.body(14)),
          onTap: () {
            Navigator.of(sheetContext).pop();
            removeFriend(friend.uid);
          },
        ),
        ListTile(
          leading: const Icon(Icons.block_rounded, size: 20),
          title: Text(l10n.blockUser, style: RythoText.body(14)),
          onTap: () async {
            Navigator.of(sheetContext).pop();
            await removeFriend(friend.uid);
            await blockUser(friend.uid);
          },
        ),
        ListTile(
          leading: const Icon(Icons.flag_outlined, size: 20),
          title: Text(l10n.reportUser, style: RythoText.body(14)),
          onTap: () {
            Navigator.of(sheetContext).pop();
            showReportSheet(context, targetType: 'user', targetId: friend.uid);
          },
        ),
        const SizedBox(height: 8),
      ]),
    ),
  );
}
