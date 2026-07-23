import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../core/analytics.dart';
import '../../core/api.dart';
import '../../core/providers.dart';
import '../../core/safety.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/glass.dart';
import 'profile_page.dart';

enum FeedMode { following, explore }

/// X-modeli akış: "Takip" (takip edilenler + kendin) ve "Keşfet" (herkes).
/// channelId verilirse o kanalın tek yönlü akışı gösterilir.
class FeedTab extends ConsumerStatefulWidget {
  const FeedTab({super.key, this.channelId, this.channelOwnerId});

  final String? channelId;
  final String? channelOwnerId;

  @override
  ConsumerState<FeedTab> createState() => _FeedTabState();
}

class _FeedTabState extends ConsumerState<FeedTab> {
  FeedMode _mode = FeedMode.following;

  String get _uid => FirebaseAuth.instance.currentUser!.uid;
  bool get _isChannel => widget.channelId != null;

  @override
  Widget build(BuildContext context) {
    final canPost = !_isChannel || widget.channelOwnerId == _uid;
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: Column(children: [
        if (!_isChannel) ...[
          const SizedBox(height: 10),
          GlassSegments(
            labels: const ['Takip', 'Keşfet'],
            index: _mode.index,
            onChanged: (i) => setState(() => _mode = FeedMode.values[i]),
          ),
          const SizedBox(height: 4),
        ],
        Expanded(
          child: _isChannel
              ? _PostList(
                  query: FirebaseFirestore.instance
                      .collection('posts')
                      .where('channelId', isEqualTo: widget.channelId)
                      .orderBy('createdAt', descending: true)
                      .limit(50),
                  emptyText: 'Bu kanal henüz sessiz.',
                )
              : _mode == FeedMode.explore
                  ? _PostList(
                      query: FirebaseFirestore.instance
                          .collection('posts')
                          .where('channelId', isNull: true)
                          .orderBy('createdAt', descending: true)
                          .limit(50),
                      emptyText: 'Meclis henüz sessiz.\nİlk sözü sen söyle.',
                    )
                  : _FollowingFeed(uid: _uid),
        ),
      ]),
      floatingActionButton: canPost
          ? Padding(
              padding: EdgeInsets.only(bottom: _isChannel ? 0 : 78),
              child: FloatingActionButton(
                backgroundColor: RythoColors.gold,
                foregroundColor: RythoColors.ink,
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16)),
                onPressed: () => _openComposer(context),
                child: const Icon(Icons.edit_outlined),
              ),
            )
          : null,
    );
  }

  /// Yayın öncesi içerik denetimi. Moderasyon servisi ulaşılamazsa yayını
  /// engelleme (fail-open) ama durumu logla.
  Future<bool> _moderate(String text) async {
    try {
      final response = await ref
          .read(apiProvider)
          .post('/api/v1/chat/moderate', data: {'text': text});
      return response.data['safe'] != false;
    } catch (e) {
      debugPrint('Moderasyon çağrısı başarısız, fail-open uygulanıyor: $e');
      return true;
    }
  }

  void _openComposer(BuildContext context) {
    final controller = TextEditingController();
    var busy = false;
    String? warning;
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: RythoColors.inkLight,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(22)),
        side: BorderSide(color: RythoColors.glassStroke),
      ),
      builder: (sheetContext) => StatefulBuilder(
        builder: (sheetContext, setSheetState) => Padding(
          padding: EdgeInsets.only(
            left: 20,
            right: 20,
            top: 20,
            bottom: MediaQuery.of(sheetContext).viewInsets.bottom + 20,
          ),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Text(_isChannel ? 'KANALA YAYINLA' : 'MECLİSE SESLEN',
                style: RythoText.mono(11, color: RythoColors.parchmentDim)),
            const SizedBox(height: 14),
            TextField(
              controller: controller,
              style: RythoText.body(15),
              minLines: 3,
              maxLines: 6,
              maxLength: 2000,
              autofocus: true,
              decoration: const InputDecoration(
                  hintText: 'Gökyüzü bugün sana ne söyledi?'),
            ),
            if (warning != null) ...[
              const SizedBox(height: 8),
              Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('☾',
                    style: TextStyle(color: RythoColors.copper, fontSize: 14)),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(warning!,
                      style: RythoText.body(12.5, color: RythoColors.copper)),
                ),
              ]),
            ],
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: GoldButton(
                text: 'Yayınla',
                busy: busy,
                onPressed: () async {
                  final text = controller.text.trim();
                  if (text.isEmpty || busy) return;
                  setSheetState(() {
                    busy = true;
                    warning = null;
                  });
                  final safe = await _moderate(text);
                  if (!sheetContext.mounted) return;
                  if (!safe) {
                    setSheetState(() {
                      busy = false;
                      warning =
                          'Bu ifade Meclis\'in nezaket sınırlarını zorluyor '
                          'gibi görünüyor. Sözlerini biraz yumuşatıp tekrar '
                          'dener misin?';
                    });
                    return;
                  }
                  Navigator.of(sheetContext).pop();
                  final user = FirebaseAuth.instance.currentUser!;
                  final profile = ref.read(profileProvider).value ?? {};
                  await FirebaseFirestore.instance.collection('posts').add({
                    'authorId': user.uid,
                    'authorName': profile['displayName'] ?? 'Gezgin',
                    'authorPhoto': profile['photoUrl'],
                    'authorSign': profile['sunSign'],
                    'text': text,
                    'channelId': widget.channelId,
                    'createdAt': FieldValue.serverTimestamp(),
                  });
                  Analytics.postPublished(toChannel: _isChannel);
                },
              ),
            ),
          ]),
        ),
      ),
    );
  }
}

/// Takip akışı: following listesi + kendi gönderilerin.
/// İlk sürüm: ≤10 takip için `whereIn`; fazlası Keşfet'e yönlendirilir.
class _FollowingFeed extends StatelessWidget {
  const _FollowingFeed({required this.uid});
  final String uid;

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<QuerySnapshot<Map<String, dynamic>>>(
      stream: FirebaseFirestore.instance
          .collection('users')
          .doc(uid)
          .collection('following')
          .snapshots(),
      builder: (context, snapshot) {
        if (!snapshot.hasData) {
          return const Center(child: AstrolabeSpinner());
        }
        final ids = [uid, ...snapshot.data!.docs.map((d) => d.id)];
        // Firestore whereIn sınırı 10 — ilk 10 kimlikle sorgula
        final queryIds = ids.take(10).toList();
        return _PostList(
          query: FirebaseFirestore.instance
              .collection('posts')
              .where('channelId', isNull: true)
              .where('authorId', whereIn: queryIds)
              .orderBy('createdAt', descending: true)
              .limit(50),
          emptyText: ids.length == 1
              ? 'Henüz kimseyi takip etmiyorsun.\nKeşfet sekmesinden gökyüzü komşularını bul.'
              : 'Takip ettiklerin henüz sessiz.',
        );
      },
    );
  }
}

class _PostList extends ConsumerWidget {
  const _PostList({required this.query, required this.emptyText});
  final Query<Map<String, dynamic>> query;
  final String emptyText;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Engellenen kullanıcıların gönderileri istemci tarafında gizlenir.
    final blocked = ref.watch(blockedUsersProvider).value ?? const <String>{};
    return StreamBuilder<QuerySnapshot<Map<String, dynamic>>>(
      stream: query.snapshots(),
      builder: (context, snapshot) {
        if (snapshot.hasError) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Text('Akış yüklenemedi: ${snapshot.error}',
                  style: RythoText.body(13, color: RythoColors.parchmentDim)),
            ),
          );
        }
        if (!snapshot.hasData) {
          return const Center(child: AstrolabeSpinner());
        }
        final docs = snapshot.data!.docs
            .where((d) => !blocked.contains(d.data()['authorId']))
            .toList();
        if (docs.isEmpty) {
          return Center(
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              Text('✦', style: RythoText.display(32, color: RythoColors.gold)),
              const SizedBox(height: 8),
              Text(emptyText,
                  textAlign: TextAlign.center,
                  style: RythoText.body(14, color: RythoColors.parchmentDim)),
            ]),
          );
        }
        return ListView.builder(
          padding: const EdgeInsets.only(top: 8, bottom: 140),
          itemCount: docs.length,
          itemBuilder: (_, i) => PostCard(
            postId: docs[i].id,
            post: docs[i].data(),
          )
              .animate(delay: (i.clamp(0, 8) * 45).ms)
              .fadeIn(duration: 320.ms)
              .slideY(begin: 0.05, curve: Curves.easeOutCubic),
        );
      },
    );
  }
}

/// Cam gönderi kartı: avatar → profil sayfası, beğenide ✦ patlaması.
class PostCard extends ConsumerStatefulWidget {
  const PostCard({super.key, required this.postId, required this.post});
  final String postId;
  final Map<String, dynamic> post;

  @override
  ConsumerState<PostCard> createState() => _PostCardState();
}

class _PostCardState extends ConsumerState<PostCard> {
  int _likeBurst = 0;

  void _openProfile() {
    Navigator.of(context).push(MaterialPageRoute(
        builder: (_) => ProfilePage(uid: widget.post['authorId'])));
  }

  @override
  Widget build(BuildContext context) {
    final post = widget.post;
    final uid = FirebaseAuth.instance.currentUser!.uid;
    final createdAt = (post['createdAt'] as Timestamp?)?.toDate();
    final timeText = createdAt == null
        ? ''
        : DateFormat('d MMM HH:mm', 'tr_TR').format(createdAt);

    return GlassPanel(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      padding: const EdgeInsets.all(14),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          GestureDetector(
            onTap: _openProfile,
            child: CircleAvatar(
              radius: 17,
              backgroundColor: RythoColors.inkLighter,
              backgroundImage: post['authorPhoto'] != null
                  ? NetworkImage(post['authorPhoto'])
                  : null,
              child: post['authorPhoto'] == null
                  ? Text('☽', style: RythoText.mono(13))
                  : null,
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: GestureDetector(
              onTap: _openProfile,
              child:
                  Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(post['authorName'] ?? 'Gezgin',
                    style: RythoText.body(14, w: FontWeight.w600)),
                Text(
                  [
                    if (post['authorSign'] != null) '☉ ${post['authorSign']}',
                    timeText,
                  ].join('  ·  '),
                  style: RythoText.mono(10, color: RythoColors.parchmentDim),
                ),
              ]),
            ),
          ),
          if (post['authorId'] != uid)
            PopupMenuButton<String>(
              icon: const Icon(Icons.more_horiz,
                  size: 18, color: RythoColors.parchmentDim),
              color: RythoColors.inkLight,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(14),
                side: const BorderSide(color: RythoColors.glassStroke),
              ),
              onSelected: (value) async {
                final messenger = ScaffoldMessenger.of(context);
                if (value == 'report') {
                  await showReportSheet(context,
                      targetType: 'post', targetId: widget.postId);
                } else if (value == 'block') {
                  try {
                    await blockUser(post['authorId']);
                    messenger.showSnackBar(const SnackBar(
                        content: Text(
                            'Kullanıcı engellendi; içerikleri artık gösterilmeyecek.')));
                  } catch (e) {
                    messenger.showSnackBar(
                        SnackBar(content: Text('Engelleme başarısız: $e')));
                  }
                }
              },
              itemBuilder: (_) => [
                PopupMenuItem(
                    value: 'report',
                    child: Text('Şikayet et', style: RythoText.body(13.5))),
                PopupMenuItem(
                    value: 'block',
                    child: Text('Engelle', style: RythoText.body(13.5))),
              ],
            ),
        ]),
        const SizedBox(height: 10),
        Text(post['text'] ?? '', style: RythoText.body(14.5, height: 1.55)),
        const SizedBox(height: 10),
        StreamBuilder<QuerySnapshot>(
          stream: FirebaseFirestore.instance
              .collection('posts')
              .doc(widget.postId)
              .collection('likes')
              .snapshots(),
          builder: (_, snapshot) {
            final likes = snapshot.data?.docs ?? [];
            final liked = likes.any((d) => d.id == uid);
            return Row(children: [
              InkWell(
                borderRadius: BorderRadius.circular(8),
                onTap: () {
                  HapticFeedback.lightImpact();
                  final refDoc = FirebaseFirestore.instance
                      .collection('posts')
                      .doc(widget.postId)
                      .collection('likes')
                      .doc(uid);
                  if (liked) {
                    refDoc.delete();
                  } else {
                    refDoc.set({'at': FieldValue.serverTimestamp()});
                    setState(() => _likeBurst++);
                  }
                },
                child: Padding(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  child: Text(
                    liked ? '✦ ${likes.length}' : '✧ ${likes.length}',
                    style: RythoText.mono(13,
                        color: liked
                            ? RythoColors.goldBright
                            : RythoColors.parchmentDim),
                  )
                      .animate(key: ValueKey(_likeBurst))
                      .scale(
                          begin: const Offset(1, 1),
                          end: const Offset(1.5, 1.5),
                          duration: 140.ms,
                          curve: Curves.easeOut)
                      .then()
                      .scale(
                          begin: const Offset(1, 1),
                          end: const Offset(1 / 1.5, 1 / 1.5),
                          duration: 220.ms,
                          curve: Curves.elasticOut),
                ),
              ),
              const Spacer(),
              if (post['authorId'] != uid)
                InkWell(
                  onTap: _openProfile,
                  child: Text('PROFİL',
                      style: RythoText.label(10, color: RythoColors.copper)),
                ),
            ]);
          },
        ),
      ]),
    );
  }
}
