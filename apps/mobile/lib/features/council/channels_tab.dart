import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/glass.dart';
import 'feed_tab.dart';

/// Kanallar: tek yönlü yayın — yalnızca sahibi gönderir, herkes abone olur.
class ChannelsTab extends ConsumerWidget {
  const ChannelsTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final uid = FirebaseAuth.instance.currentUser!.uid;
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: StreamBuilder<QuerySnapshot<Map<String, dynamic>>>(
        stream: FirebaseFirestore.instance
            .collection('channels')
            .orderBy('createdAt', descending: true)
            .limit(50)
            .snapshots(),
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return Center(
                child: Text('Kanallar yüklenemedi: ${snapshot.error}',
                    style:
                        RythoText.body(13, color: RythoColors.parchmentDim)));
          }
          if (!snapshot.hasData) {
            return const Center(child: AstrolabeSpinner());
          }
          final docs = snapshot.data!.docs;
          if (docs.isEmpty) {
            return Center(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                Text('⌾', style: RythoText.display(32, color: RythoColors.gold)),
                const SizedBox(height: 8),
                Text('Henüz kanal yok.\nİlk yayını sen başlat.',
                    textAlign: TextAlign.center,
                    style:
                        RythoText.body(14, color: RythoColors.parchmentDim)),
              ]),
            );
          }
          return ListView.builder(
            padding: const EdgeInsets.only(top: 8, bottom: 140),
            itemCount: docs.length,
            itemBuilder: (_, i) => _ChannelCard(
              channelId: docs[i].id,
              channel: docs[i].data(),
              uid: uid,
            ),
          );
        },
      ),
      floatingActionButton: Padding(
        padding: const EdgeInsets.only(bottom: 78),
        child: FloatingActionButton(
          backgroundColor: RythoColors.gold,
          foregroundColor: RythoColors.ink,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          onPressed: () => _createChannel(context, uid),
          child: const Icon(Icons.podcasts_outlined),
        ),
      ),
    );
  }

  void _createChannel(BuildContext context, String uid) {
    final nameController = TextEditingController();
    final descController = TextEditingController();
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: RythoColors.inkLight,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(22)),
        side: BorderSide(color: RythoColors.glassStroke),
      ),
      builder: (sheetContext) => Padding(
        padding: EdgeInsets.only(
          left: 20,
          right: 20,
          top: 20,
          bottom: MediaQuery.of(sheetContext).viewInsets.bottom + 20,
        ),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Text('KANAL AÇ',
              style: RythoText.mono(11, color: RythoColors.parchmentDim)),
          const SizedBox(height: 14),
          TextField(
            controller: nameController,
            style: RythoText.body(15),
            maxLength: 60,
            decoration:
                const InputDecoration(hintText: 'Kanal adı (örn. Retro Günlüğü)'),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: descController,
            style: RythoText.body(14),
            maxLength: 200,
            decoration: const InputDecoration(hintText: 'Kısa açıklama'),
          ),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: GoldButton(
              text: 'Yayına başla',
              onPressed: () async {
                final name = nameController.text.trim();
                if (name.length < 3) return;
                Navigator.of(sheetContext).pop();
                final user = FirebaseAuth.instance.currentUser!;
                await FirebaseFirestore.instance.collection('channels').add({
                  'name': name,
                  'description': descController.text.trim(),
                  'ownerId': uid,
                  'ownerName': user.displayName ?? 'Gezgin',
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

class _ChannelCard extends StatelessWidget {
  const _ChannelCard({
    required this.channelId,
    required this.channel,
    required this.uid,
  });

  final String channelId;
  final Map<String, dynamic> channel;
  final String uid;

  @override
  Widget build(BuildContext context) {
    final subscribers = FirebaseFirestore.instance
        .collection('channels')
        .doc(channelId)
        .collection('subscribers');

    return GlassPanel(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      padding: const EdgeInsets.all(14),
      onTap: () => Navigator.of(context).push(MaterialPageRoute(
        builder: (_) => ChannelScreen(channelId: channelId, channel: channel),
      )),
      child: Row(children: [
        Container(
          width: 42,
          height: 42,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: RythoColors.inkLighter,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: RythoColors.glassEdge),
          ),
          child: const Text('⌾',
              style: TextStyle(color: RythoColors.goldBright, fontSize: 18)),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(channel['name'] ?? '', style: RythoText.body(15, w: FontWeight.w600)),
            if ((channel['description'] as String?)?.isNotEmpty == true)
              Text(channel['description'],
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style:
                      RythoText.body(12.5, color: RythoColors.parchmentDim)),
            StreamBuilder<QuerySnapshot>(
              stream: subscribers.snapshots(),
              builder: (_, s) => Text(
                  '${s.data?.size ?? 0} abone · ${channel['ownerName'] ?? ''}',
                  style:
                      RythoText.mono(10, color: RythoColors.parchmentDim)),
            ),
          ]),
        ),
        const SizedBox(width: 8),
        if (channel['ownerId'] != uid)
          StreamBuilder<DocumentSnapshot>(
            stream: subscribers.doc(uid).snapshots(),
            builder: (_, s) {
              final subscribed = s.data?.exists ?? false;
              return OutlinedButton(
                style: OutlinedButton.styleFrom(
                  side: BorderSide(
                      color: subscribed
                          ? RythoColors.line
                          : RythoColors.gold),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10)),
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                ),
                onPressed: () => subscribed
                    ? subscribers.doc(uid).delete()
                    : subscribers
                        .doc(uid)
                        .set({'at': FieldValue.serverTimestamp()}),
                child: Text(subscribed ? 'ABONE' : 'ABONE OL',
                    style: RythoText.label(9,
                        color: subscribed
                            ? RythoColors.parchmentDim
                            : RythoColors.goldBright)),
              );
            },
          ),
      ]),
    );
  }
}

/// Kanal sayfası: tek yönlü akış.
class ChannelScreen extends StatelessWidget {
  const ChannelScreen(
      {super.key, required this.channelId, required this.channel});
  final String channelId;
  final Map<String, dynamic> channel;

  @override
  Widget build(BuildContext context) {
    return CosmicScaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(channel['name'] ?? ''),
            Text('kanal · ${channel['ownerName'] ?? ''}',
                style: RythoText.mono(10, color: RythoColors.parchmentDim)),
          ],
        ),
      ),
      body: FeedTab(channelId: channelId, channelOwnerId: channel['ownerId']),
    );
  }
}
