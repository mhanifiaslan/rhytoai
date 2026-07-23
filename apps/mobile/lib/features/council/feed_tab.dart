import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../core/providers.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import 'synastry_sheet.dart';

/// Herkese açık kozmik akış. networkId'siz gönderiler burada yayınlanır.
class FeedTab extends ConsumerWidget {
  const FeedTab({super.key, this.networkId});

  /// null → herkese açık akış; dolu → ağ akışı.
  final String? networkId;

  Query<Map<String, dynamic>> _query() {
    var q = FirebaseFirestore.instance
        .collection('posts')
        .where('networkId', isNull: networkId == null);
    if (networkId != null) {
      q = FirebaseFirestore.instance
          .collection('posts')
          .where('networkId', isEqualTo: networkId);
    }
    return q.orderBy('createdAt', descending: true).limit(50);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: StreamBuilder<QuerySnapshot<Map<String, dynamic>>>(
        stream: _query().snapshots(),
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return Center(
              child: Text('Akış yüklenemedi: ${snapshot.error}',
                  style: RythoText.body(13, color: RythoColors.parchmentDim)),
            );
          }
          if (!snapshot.hasData) {
            return const Center(child: AstrolabeSpinner());
          }
          final docs = snapshot.data!.docs;
          if (docs.isEmpty) {
            return Center(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                Text('✦', style: RythoText.display(32, color: RythoColors.gold)),
                const SizedBox(height: 8),
                Text('Meclis henüz sessiz.\nİlk sözü sen söyle.',
                    textAlign: TextAlign.center,
                    style:
                        RythoText.body(14, color: RythoColors.parchmentDim)),
              ]),
            );
          }
          return ListView.builder(
            padding: const EdgeInsets.only(top: 8, bottom: 80),
            itemCount: docs.length,
            itemBuilder: (_, i) => PostCard(
              postId: docs[i].id,
              post: docs[i].data(),
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: RythoColors.gold,
        foregroundColor: RythoColors.ink,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
        onPressed: () => _openComposer(context, ref),
        child: const Icon(Icons.edit_outlined),
      ),
    );
  }

  void _openComposer(BuildContext context, WidgetRef ref) {
    final controller = TextEditingController();
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: RythoColors.inkLight,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(4)),
        side: BorderSide(color: RythoColors.line),
      ),
      builder: (sheetContext) => Padding(
        padding: EdgeInsets.only(
          left: 20,
          right: 20,
          top: 20,
          bottom: MediaQuery.of(sheetContext).viewInsets.bottom + 20,
        ),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Text('MECLİSE SESLEN',
              style: RythoText.mono(11, color: RythoColors.parchmentDim)),
          const SizedBox(height: 14),
          TextField(
            controller: controller,
            style: RythoText.body(15),
            minLines: 3,
            maxLines: 6,
            maxLength: 2000,
            autofocus: true,
            decoration:
                const InputDecoration(hintText: 'Gökyüzü bugün sana ne söyledi?'),
          ),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: GoldButton(
              text: 'Yayınla',
              onPressed: () async {
                final text = controller.text.trim();
                if (text.isEmpty) return;
                Navigator.of(sheetContext).pop();
                final user = FirebaseAuth.instance.currentUser!;
                final profile = ref.read(profileProvider).value ?? {};
                await FirebaseFirestore.instance.collection('posts').add({
                  'authorId': user.uid,
                  'authorName': profile['displayName'] ?? 'Gezgin',
                  'authorPhoto': profile['photoUrl'],
                  'authorSign': profile['sunSign'],
                  'text': text,
                  'networkId': networkId,
                  'createdAt': FieldValue.serverTimestamp(),
                });
              },
            ),
          ),
        ]),
      ),
    );
  }
}

class PostCard extends ConsumerWidget {
  const PostCard({super.key, required this.postId, required this.post});
  final String postId;
  final Map<String, dynamic> post;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final uid = FirebaseAuth.instance.currentUser!.uid;
    final createdAt = (post['createdAt'] as Timestamp?)?.toDate();
    final timeText = createdAt == null
        ? ''
        : DateFormat('d MMM HH:mm', 'tr_TR').format(createdAt);

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: RythoColors.inkLight,
        border: Border.all(color: RythoColors.line),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          GestureDetector(
            onTap: () => showUserSheet(context, post['authorId']),
            child: CircleAvatar(
              radius: 16,
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
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(post['authorName'] ?? 'Gezgin', style: RythoText.body(14)),
              Text(
                [
                  if (post['authorSign'] != null) '☉ ${post['authorSign']}',
                  timeText,
                ].join('  ·  '),
                style: RythoText.mono(10, color: RythoColors.parchmentDim),
              ),
            ]),
          ),
        ]),
        const SizedBox(height: 10),
        Text(post['text'] ?? '', style: RythoText.body(14.5, height: 1.55)),
        const SizedBox(height: 10),
        StreamBuilder<QuerySnapshot>(
          stream: FirebaseFirestore.instance
              .collection('posts')
              .doc(postId)
              .collection('likes')
              .snapshots(),
          builder: (_, snapshot) {
            final likes = snapshot.data?.docs ?? [];
            final liked = likes.any((d) => d.id == uid);
            return Row(children: [
              InkWell(
                onTap: () {
                  final refDoc = FirebaseFirestore.instance
                      .collection('posts')
                      .doc(postId)
                      .collection('likes')
                      .doc(uid);
                  liked ? refDoc.delete() : refDoc.set({'at': FieldValue.serverTimestamp()});
                },
                child: Text(
                  liked ? '✦ ${likes.length}' : '✧ ${likes.length}',
                  style: RythoText.mono(13,
                      color:
                          liked ? RythoColors.goldBright : RythoColors.parchmentDim),
                ),
              ),
              const Spacer(),
              if (post['authorId'] != uid)
                InkWell(
                  onTap: () => showUserSheet(context, post['authorId']),
                  child: Text('UYUM BAK',
                      style: RythoText.label(10, color: RythoColors.copper)),
                ),
            ]);
          },
        ),
      ]),
    );
  }
}
