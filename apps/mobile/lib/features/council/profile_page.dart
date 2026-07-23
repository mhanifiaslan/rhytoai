import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/analytics.dart';
import '../../core/api.dart';
import '../../core/providers.dart';
import '../../core/safety.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/glass.dart';
import '../../widgets/nebula_widgets.dart';
import 'feed_tab.dart' show PostCard;
import 'messages_tab.dart';

/// X-modeli profil sayfası: rozetler, takipçi sayaçları, takip et/bırak,
/// kozmik uyum, mesaj ve kullanıcının gönderileri.
class ProfilePage extends ConsumerStatefulWidget {
  const ProfilePage({super.key, required this.uid});
  final String uid;

  @override
  ConsumerState<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends ConsumerState<ProfilePage> {
  Map<String, dynamic>? _profile;
  String? _synastry;
  bool _synastryBusy = false;

  String get _myUid => FirebaseAuth.instance.currentUser!.uid;
  bool get _isMe => widget.uid == _myUid;

  @override
  void initState() {
    super.initState();
    FirebaseFirestore.instance
        .collection('users')
        .doc(widget.uid)
        .get()
        .then((doc) {
      if (mounted) setState(() => _profile = doc.data());
    });
  }

  Future<void> _toggleFollow(bool following) async {
    final firestore = FirebaseFirestore.instance;
    final batch = firestore.batch();
    final followingRef = firestore
        .collection('users')
        .doc(_myUid)
        .collection('following')
        .doc(widget.uid);
    final followerRef = firestore
        .collection('users')
        .doc(widget.uid)
        .collection('followers')
        .doc(_myUid);
    if (following) {
      batch.delete(followingRef);
      batch.delete(followerRef);
    } else {
      final stamp = {'at': FieldValue.serverTimestamp()};
      batch.set(followingRef, stamp);
      batch.set(followerRef, stamp);
    }
    await batch.commit();
    if (!following) Analytics.userFollowed();
  }

  Future<void> _loadSynastry() async {
    final myProfile = (await FirebaseFirestore.instance
            .collection('users')
            .doc(_myUid)
            .get())
        .data();
    if (myProfile == null || _profile == null) return;
    setState(() => _synastryBusy = true);
    try {
      final dio = ref.read(apiProvider);
      final response = await dio.post('/api/v1/reports/synastry', data: {
        'person1': birthPayload(myProfile),
        'person2': birthPayload(_profile!),
      });
      setState(() => _synastry = response.data['data']['report']);
      Analytics.reportGenerated('synastry');
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Uyum hesaplanamadı: $e')));
      }
    } finally {
      if (mounted) setState(() => _synastryBusy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final profile = _profile;
    final blocked =
        ref.watch(blockedUsersProvider).value ?? const <String>{};
    final isBlocked = blocked.contains(widget.uid);
    return CosmicScaffold(
      appBar: AppBar(
        title: Text(profile?['displayName'] ?? ''),
        actions: [
          if (!_isMe)
            PopupMenuButton<String>(
              icon: const Icon(Icons.more_vert,
                  size: 20, color: RythoColors.parchmentDim),
              color: RythoColors.inkLight,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(14),
                side: const BorderSide(color: RythoColors.glassStroke),
              ),
              onSelected: (value) async {
                final messenger = ScaffoldMessenger.of(context);
                if (value == 'report') {
                  await showReportSheet(context,
                      targetType: 'user', targetId: widget.uid);
                } else if (value == 'block') {
                  try {
                    if (isBlocked) {
                      await unblockUser(widget.uid);
                      messenger.showSnackBar(const SnackBar(
                          content: Text('Engel kaldırıldı.')));
                    } else {
                      await blockUser(widget.uid);
                      messenger.showSnackBar(const SnackBar(
                          content: Text(
                              'Kullanıcı engellendi; içerikleri artık gösterilmeyecek.')));
                    }
                  } catch (e) {
                    messenger.showSnackBar(
                        SnackBar(content: Text('İşlem başarısız: $e')));
                  }
                }
              },
              itemBuilder: (_) => [
                PopupMenuItem(
                    value: 'report',
                    child: Text('Şikayet et', style: RythoText.body(13.5))),
                PopupMenuItem(
                    value: 'block',
                    child: Text(isBlocked ? 'Engeli kaldır' : 'Engelle',
                        style: RythoText.body(13.5))),
              ],
            ),
        ],
      ),
      body: profile == null
          ? const Center(child: AstrolabeSpinner())
          : ListView(
              padding: const EdgeInsets.only(bottom: 40),
              children: [
                const SizedBox(height: 8),
                Center(
                  child: Container(
                    padding: const EdgeInsets.all(3),
                    decoration: const BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: RythoColors.primaryGradient,
                      boxShadow: [
                        BoxShadow(
                            color: RythoColors.magentaGlow, blurRadius: 26),
                      ],
                    ),
                    child: CircleAvatar(
                      radius: 40,
                      backgroundColor: RythoColors.inkLight,
                      backgroundImage: profile['photoUrl'] != null
                          ? NetworkImage(profile['photoUrl'])
                          : null,
                      child: profile['photoUrl'] == null
                          ? Text('☽', style: RythoText.display(26))
                          : null,
                    ),
                  ),
                ).animate().scale(
                    begin: const Offset(0.9, 0.9),
                    curve: Curves.easeOutBack,
                    duration: 400.ms),
                const SizedBox(height: 12),
                Center(
                    child: Text(profile['displayName'] ?? 'Gezgin',
                        style: RythoText.display(28))),
                const SizedBox(height: 6),
                Center(
                  child: Wrap(spacing: 8, children: [
                    for (final badge in [
                      if (profile['sunSign'] != null)
                        (emoji: '☀️', text: profile['sunSign'] as String),
                      if (profile['moonSign'] != null)
                        (emoji: '🌙', text: profile['moonSign'] as String),
                      if (profile['ascendant'] != null)
                        (emoji: '⬆️', text: profile['ascendant'] as String),
                    ])
                      Builder(builder: (_) {
                        final signIndex = kSignNamesTr.indexOf(badge.text);
                        final color = signIndex >= 0
                            ? RythoColors.signColors[signIndex]
                            : RythoColors.lilac;
                        return Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(
                            color: color.withValues(alpha: 0.14),
                            border: Border.all(
                                color: color.withValues(alpha: 0.5)),
                            borderRadius: BorderRadius.circular(999),
                          ),
                          child: Text('${badge.emoji} ${badge.text}',
                              style:
                                  RythoText.body(12, w: FontWeight.w700)),
                        );
                      }),
                  ]),
                ),
                if ((profile['bio'] as String?)?.isNotEmpty == true) ...[
                  const SizedBox(height: 12),
                  Center(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 40),
                      child: Text(profile['bio'],
                          textAlign: TextAlign.center,
                          style: RythoText.body(13.5,
                              color: RythoColors.parchmentDim)),
                    ),
                  ),
                ],
                const SizedBox(height: 14),
                _FollowCounters(uid: widget.uid),
                const SizedBox(height: 14),
                if (!_isMe)
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Column(children: [
                      StreamBuilder<DocumentSnapshot>(
                        stream: FirebaseFirestore.instance
                            .collection('users')
                            .doc(_myUid)
                            .collection('following')
                            .doc(widget.uid)
                            .snapshots(),
                        builder: (_, snapshot) {
                          final following = snapshot.data?.exists ?? false;
                          return GoldButton(
                            text: following ? 'Takibi bırak' : 'Takip et',
                            filled: !following,
                            onPressed: () => _toggleFollow(following),
                          );
                        },
                      ),
                      const SizedBox(height: 10),
                      Row(children: [
                        Expanded(
                          child: GoldButton(
                            text: 'Kozmik uyum',
                            busy: _synastryBusy,
                            onPressed:
                                _synastry == null ? _loadSynastry : null,
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: GoldButton(
                            text: 'Mesaj',
                            onPressed: () => openChat(context, widget.uid,
                                profile['displayName'] ?? 'Gezgin'),
                          ),
                        ),
                      ]),
                    ]),
                  ),
                if (_synastry != null)
                  GlassPanel(
                    label: 'İki haritanın söyleşisi',
                    child: Text(_synastry!,
                        style: RythoText.body(15, height: 1.65)),
                  ),
                const SectionDivider(),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Text('Gönderiler', style: RythoText.display(20)),
                ),
                const SizedBox(height: 6),
                StreamBuilder<QuerySnapshot<Map<String, dynamic>>>(
                  stream: FirebaseFirestore.instance
                      .collection('posts')
                      .where('authorId', isEqualTo: widget.uid)
                      .orderBy('createdAt', descending: true)
                      .limit(30)
                      .snapshots(),
                  builder: (_, snapshot) {
                    final docs = snapshot.data?.docs ?? [];
                    if (docs.isEmpty) {
                      return Padding(
                        padding: const EdgeInsets.all(24),
                        child: Center(
                          child: Text('Henüz gönderi yok.',
                              style: RythoText.body(13,
                                  color: RythoColors.parchmentDim)),
                        ),
                      );
                    }
                    return Column(children: [
                      for (final doc in docs)
                        PostCard(postId: doc.id, post: doc.data()),
                    ]);
                  },
                ),
              ],
            ),
    );
  }
}

class _FollowCounters extends StatelessWidget {
  const _FollowCounters({required this.uid});
  final String uid;

  Widget _counter(String label, Stream<int> stream) {
    return StreamBuilder<int>(
      stream: stream,
      builder: (_, snapshot) => Column(children: [
        Text('${snapshot.data ?? 0}', style: RythoText.display(20)),
        Text(label, style: RythoText.mono(10, color: RythoColors.parchmentDim)),
      ]),
    );
  }

  @override
  Widget build(BuildContext context) {
    final users = FirebaseFirestore.instance.collection('users').doc(uid);
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        _counter('TAKİPÇİ',
            users.collection('followers').snapshots().map((s) => s.size)),
        const SizedBox(width: 40),
        _counter('TAKİP',
            users.collection('following').snapshots().map((s) => s.size)),
      ],
    );
  }
}
