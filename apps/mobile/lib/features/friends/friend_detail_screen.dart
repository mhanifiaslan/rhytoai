import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/analytics.dart';
import '../../core/api.dart';
import '../../core/friends.dart';
import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/glass.dart';
import '../../widgets/nebula_widgets.dart' show Pressable;
import 'friends_screen.dart' show showFriendSafetySheet;

/// Arkadaş detayı: bugüne özgü ikili dinamik + hazır tepki gönderme.
///
/// Kalıcı bir uyum skoru **bilinçli olarak gösterilmez**: skor ölçüm değil
/// gelenektir ve geri alınamaz bir damga gerçek ilişkilere zarar verir.
/// Okuma her gün yenilenir ve iki taraf da aynı metni görür.
class FriendDetailScreen extends ConsumerStatefulWidget {
  const FriendDetailScreen({super.key, required this.friend});

  final Friend friend;

  @override
  ConsumerState<FriendDetailScreen> createState() => _FriendDetailScreenState();
}

class _FriendDetailScreenState extends ConsumerState<FriendDetailScreen> {
  String? _reading;
  String? _error;
  bool _busy = false;
  String? _sentReaction;

  @override
  void initState() {
    super.initState();
    _loadDyad();
  }

  Future<void> _loadDyad() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final dio = ref.read(apiProvider);
      final response = await dio.post('/api/v1/reports/dyad',
          data: {'friend_uid': widget.friend.uid});
      if (!mounted) return;
      setState(() => _reading = response.data['data']['reading'] as String?);
      Analytics.reportGenerated('dyad');
    } catch (e) {
      if (mounted) setState(() => _error = friendlyError(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _react(String key) async {
    setState(() => _sentReaction = key);
    try {
      await sendReaction(widget.friend.uid, key);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(AppLocalizations.of(context)
                .reactionSent(kReactions[key]!.emoji))));
      }
    } catch (e) {
      if (mounted) {
        setState(() => _sentReaction = null);
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(friendlyError(e))));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final friend = widget.friend;
    return CosmicScaffold(
      appBar: AppBar(
        title: Text(friend.name),
        actions: [
          IconButton(
            icon: const Icon(Icons.more_vert, size: 20),
            onPressed: () => showFriendSafetySheet(context, friend),
          ),
        ],
      ),
      body: ListView(padding: const EdgeInsets.only(bottom: 40), children: [
        GlassPanel(
          label: l10n.friendLabel,
          child: Row(children: [
            Expanded(
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(friend.name, style: RythoText.display(20)),
                    if (friend.username != null) ...[
                      const SizedBox(height: 2),
                      Text('@${friend.username}',
                          style: RythoText.body(12.5,
                              color: RythoColors.parchmentDim)),
                    ],
                    const SizedBox(height: 8),
                    if (friend.streakVisible)
                      Text(
                        friend.readToday
                            ? l10n.readTodayDone
                            : l10n.notReadToday,
                        style: RythoText.body(12.5,
                            color: friend.readToday
                                ? RythoColors.goldBright
                                : RythoColors.parchmentDim),
                      )
                    else
                      Text(l10n.streakHiddenByFriend,
                          style: RythoText.body(12.5,
                              color: RythoColors.parchmentDim)),
                  ]),
            ),
            if (friend.sunSign != null)
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
                decoration: BoxDecoration(
                  color: RythoColors.lilac.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(999),
                  border: Border.all(
                      color: RythoColors.lilac.withValues(alpha: 0.3)),
                ),
                child: Text(friend.sunSign!,
                    style: RythoText.label(11.5, color: RythoColors.lilac)),
              ),
          ]),
        ),
        _DyadPanel(
          busy: _busy,
          reading: _reading,
          error: _error,
          onRetry: _loadDyad,
        ),
        const SectionDivider(),
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 4, 20, 10),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(l10n.sendReaction, style: RythoText.display(17)),
            const SizedBox(height: 4),
            Text(
              l10n.sendReactionBody,
              style: RythoText.body(12.5, color: RythoColors.parchmentDim),
            ),
          ]),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final entry in kReactions.entries)
                _ReactionChip(
                  emoji: entry.value.emoji,
                  label: reactionLabel(l10n, entry.key),
                  selected: _sentReaction == entry.key,
                  onTap: _sentReaction == null ? () => _react(entry.key) : null,
                ),
            ],
          ),
        ),
      ]),
    );
  }
}

/// Hazır tepki etiketleri dile göre çözülür.
///
/// Anahtarlar (`streak`, `shine` ...) Firestore kuralında da geçtiği için
/// sabittir; yalnızca gösterilen metin değişir.
String reactionLabel(AppLocalizations l10n, String key) => switch (key) {
      'streak' => l10n.reactionStreak,
      'thinking_of_you' => l10n.reactionThinkingOfYou,
      'shine' => l10n.reactionShine,
      'keep_going' => l10n.reactionKeepGoing,
      'congrats' => l10n.reactionCongrats,
      'same_frequency' => l10n.reactionSameFrequency,
      'good_night' => l10n.reactionGoodNight,
      'check_today' => l10n.reactionCheckToday,
      _ => key,
    };


class _DyadPanel extends StatelessWidget {
  const _DyadPanel({
    required this.busy,
    required this.reading,
    required this.error,
    required this.onRetry,
  });

  final bool busy;
  final String? reading;
  final String? error;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return GlassPanel(
      label: l10n.dyadLabel,
      glow: true,
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        if (busy)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 26),
            child: Center(child: AstrolabeSpinner()),
          )
        else if (error != null) ...[
          Text(l10n.dyadFailed, style: RythoText.body(14)),
          const SizedBox(height: 6),
          Text(error!,
              style: RythoText.body(11.5, color: RythoColors.parchmentDim)),
          const SizedBox(height: 12),
          GoldButton(text: l10n.retry, onPressed: onRetry, filled: false),
        ] else ...[
          Text(reading ?? '', style: RythoText.body(14.5, height: 1.6))
              .animate()
              .fadeIn(duration: 420.ms),
          const SizedBox(height: 12),
          Text(
            l10n.dyadDisclaimer,
            style: RythoText.body(11.5, color: RythoColors.parchmentDim),
          ),
        ],
      ]),
    );
  }
}

class _ReactionChip extends StatelessWidget {
  const _ReactionChip({
    required this.emoji,
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final String emoji;
  final String label;
  final bool selected;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Pressable(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 9),
        decoration: BoxDecoration(
          color: selected
              ? RythoColors.gold.withValues(alpha: 0.18)
              : RythoColors.glassFill,
          borderRadius: BorderRadius.circular(999),
          border: Border.all(
            color: selected
                ? RythoColors.gold.withValues(alpha: 0.5)
                : RythoColors.glassStroke,
          ),
        ),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          Text(emoji, style: const TextStyle(fontSize: 15)),
          const SizedBox(width: 6),
          Text(label,
              style: RythoText.label(12,
                  color: selected
                      ? RythoColors.goldBright
                      : RythoColors.parchment)),
        ]),
      ),
    );
  }
}
