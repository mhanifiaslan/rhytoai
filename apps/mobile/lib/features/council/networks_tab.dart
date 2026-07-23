import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';

import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import 'feed_tab.dart';

/// Ağlar (takımyıldızlar): topluluk kur, katıl, ağ akışında paylaş.
class NetworksTab extends StatelessWidget {
  const NetworksTab({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: StreamBuilder<QuerySnapshot<Map<String, dynamic>>>(
        stream: FirebaseFirestore.instance
            .collection('networks')
            .orderBy('createdAt', descending: true)
            .limit(50)
            .snapshots(),
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return Center(
                child: Text('Ağlar yüklenemedi: ${snapshot.error}',
                    style: RythoText.body(13, color: RythoColors.parchmentDim)));
          }
          if (!snapshot.hasData) return const Center(child: AstrolabeSpinner());
          final docs = snapshot.data!.docs;
          if (docs.isEmpty) {
            return Center(
              child: Text('Henüz kurulmuş bir ağ yok.\nİlk takımyıldızı sen kur.',
                  textAlign: TextAlign.center,
                  style: RythoText.body(14, color: RythoColors.parchmentDim)),
            );
          }
          return ListView.builder(
            padding: const EdgeInsets.only(top: 8, bottom: 80),
            itemCount: docs.length,
            itemBuilder: (_, i) =>
                _NetworkTile(networkId: docs[i].id, network: docs[i].data()),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: RythoColors.gold,
        foregroundColor: RythoColors.ink,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
        onPressed: () => _createNetwork(context),
        child: const Icon(Icons.add),
      ),
    );
  }

  void _createNetwork(BuildContext context) {
    final nameController = TextEditingController();
    final descController = TextEditingController();
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
          Text('YENİ TAKIMYILDIZ',
              style: RythoText.mono(11, color: RythoColors.parchmentDim)),
          const SizedBox(height: 14),
          TextField(
            controller: nameController,
            style: RythoText.body(15),
            maxLength: 60,
            decoration: const InputDecoration(hintText: 'Ağın adı'),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: descController,
            style: RythoText.body(15),
            maxLength: 200,
            decoration:
                const InputDecoration(hintText: 'Bu ağ kimleri toplar?'),
          ),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: GoldButton(
              text: 'Ağı kur',
              onPressed: () async {
                final name = nameController.text.trim();
                if (name.length < 3) return;
                Navigator.of(sheetContext).pop();
                final uid = FirebaseAuth.instance.currentUser!.uid;
                final doc =
                    await FirebaseFirestore.instance.collection('networks').add({
                  'name': name,
                  'description': descController.text.trim(),
                  'creatorId': uid,
                  'createdAt': FieldValue.serverTimestamp(),
                });
                await doc.collection('members').doc(uid).set(
                    {'joinedAt': FieldValue.serverTimestamp()});
              },
            ),
          ),
        ]),
      ),
    );
  }
}

class _NetworkTile extends StatelessWidget {
  const _NetworkTile({required this.networkId, required this.network});
  final String networkId;
  final Map<String, dynamic> network;

  @override
  Widget build(BuildContext context) {
    final uid = FirebaseAuth.instance.currentUser!.uid;
    final membersRef = FirebaseFirestore.instance
        .collection('networks')
        .doc(networkId)
        .collection('members');

    return StreamBuilder<QuerySnapshot>(
      stream: membersRef.snapshots(),
      builder: (context, snapshot) {
        final members = snapshot.data?.docs ?? [];
        final isMember = members.any((d) => d.id == uid);
        return InkWell(
          onTap: isMember
              ? () => Navigator.of(context).push(MaterialPageRoute(
                    builder: (_) => NetworkFeedScreen(
                        networkId: networkId,
                        name: network['name'] ?? 'Ağ'),
                  ))
              : null,
          child: Container(
            margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: RythoColors.inkLight,
              border: Border.all(
                  color: isMember ? RythoColors.gold : RythoColors.line),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Row(children: [
              Expanded(
                child:
                    Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(network['name'] ?? '', style: RythoText.display(19)),
                  if ((network['description'] as String?)?.isNotEmpty == true)
                    Text(network['description'],
                        style: RythoText.body(12.5,
                            color: RythoColors.parchmentDim)),
                  const SizedBox(height: 4),
                  Text('${members.length} üye',
                      style:
                          RythoText.mono(11, color: RythoColors.parchmentDim)),
                ]),
              ),
              TextButton(
                onPressed: () {
                  final me = membersRef.doc(uid);
                  isMember
                      ? me.delete()
                      : me.set({'joinedAt': FieldValue.serverTimestamp()});
                },
                child: Text(isMember ? 'AYRIL' : 'KATIL',
                    style: RythoText.label(11,
                        color: isMember
                            ? RythoColors.parchmentDim
                            : RythoColors.goldBright)),
              ),
            ]),
          ),
        );
      },
    );
  }
}

/// Ağın kendi akışı — FeedTab'i networkId ile yeniden kullanır.
class NetworkFeedScreen extends StatelessWidget {
  const NetworkFeedScreen(
      {super.key, required this.networkId, required this.name});
  final String networkId;
  final String name;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(name)),
      body: FeedTab(networkId: networkId),
    );
  }
}
