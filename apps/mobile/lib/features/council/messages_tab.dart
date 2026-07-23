import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../core/api.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/cosmic_scaffold.dart';

String _chatIdFor(String a, String b) {
  final ids = [a, b]..sort();
  return ids.join('_');
}

/// Sohbeti aç (yoksa oluştur).
Future<void> openChat(
    BuildContext context, String otherUid, String otherName) async {
  final me = FirebaseAuth.instance.currentUser!;
  final chatId = _chatIdFor(me.uid, otherUid);
  final chatRef = FirebaseFirestore.instance.collection('chats').doc(chatId);
  final snapshot = await chatRef.get();
  if (!snapshot.exists) {
    await chatRef.set({
      'participants': [me.uid, otherUid],
      'participantNames': {me.uid: me.displayName ?? 'Gezgin', otherUid: otherName},
      'updatedAt': FieldValue.serverTimestamp(),
      'lastMessage': '',
    });
  }
  if (context.mounted) {
    Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => ChatDetailScreen(
          chatId: chatId, otherUid: otherUid, otherName: otherName),
    ));
  }
}

/// DM listesi.
class MessagesTab extends StatelessWidget {
  const MessagesTab({super.key});

  @override
  Widget build(BuildContext context) {
    final uid = FirebaseAuth.instance.currentUser!.uid;
    return StreamBuilder<QuerySnapshot<Map<String, dynamic>>>(
      stream: FirebaseFirestore.instance
          .collection('chats')
          .where('participants', arrayContains: uid)
          .orderBy('updatedAt', descending: true)
          .snapshots(),
      builder: (context, snapshot) {
        if (snapshot.hasError) {
          return Center(
              child: Text('Mesajlar yüklenemedi: ${snapshot.error}',
                  style: RythoText.body(13, color: RythoColors.parchmentDim)));
        }
        if (!snapshot.hasData) return const Center(child: AstrolabeSpinner());
        final docs = snapshot.data!.docs;
        if (docs.isEmpty) {
          return Center(
            child: Text(
              'Henüz bir söyleşin yok.\nAkıştan birinin profiline dokunup\n"Mesaj gönder" diyebilirsin.',
              textAlign: TextAlign.center,
              style: RythoText.body(14, color: RythoColors.parchmentDim),
            ),
          );
        }
        return ListView.builder(
          padding: const EdgeInsets.symmetric(vertical: 8),
          itemCount: docs.length,
          itemBuilder: (_, i) {
            final chat = docs[i].data();
            final participants = List<String>.from(chat['participants']);
            final otherUid =
                participants.firstWhere((p) => p != uid, orElse: () => uid);
            final names =
                Map<String, dynamic>.from(chat['participantNames'] ?? {});
            final otherName = names[otherUid] ?? 'Gezgin';
            final updatedAt = (chat['updatedAt'] as Timestamp?)?.toDate();

            return ListTile(
              onTap: () => Navigator.of(context).push(MaterialPageRoute(
                builder: (_) => ChatDetailScreen(
                    chatId: docs[i].id, otherUid: otherUid, otherName: otherName),
              )),
              leading: CircleAvatar(
                backgroundColor: RythoColors.inkLighter,
                child: Text('☽', style: RythoText.mono(14)),
              ),
              title: Text(otherName, style: RythoText.body(15)),
              subtitle: Text(
                chat['lastMessage'] ?? '',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: RythoText.body(12.5, color: RythoColors.parchmentDim),
              ),
              trailing: updatedAt == null
                  ? null
                  : Text(DateFormat('d MMM', 'tr_TR').format(updatedAt),
                      style:
                          RythoText.mono(10, color: RythoColors.parchmentDim)),
            );
          },
        );
      },
    );
  }
}

/// Birebir sohbet ekranı.
class ChatDetailScreen extends ConsumerStatefulWidget {
  const ChatDetailScreen({
    super.key,
    required this.chatId,
    required this.otherUid,
    required this.otherName,
  });

  final String chatId;
  final String otherUid;
  final String otherName;

  @override
  ConsumerState<ChatDetailScreen> createState() => _ChatDetailScreenState();
}

class _ChatDetailScreenState extends ConsumerState<ChatDetailScreen> {
  final _controller = TextEditingController();

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    _controller.clear();
    final me = FirebaseAuth.instance.currentUser!;
    final chatRef =
        FirebaseFirestore.instance.collection('chats').doc(widget.chatId);

    await chatRef.collection('messages').add({
      'senderId': me.uid,
      'text': text,
      'createdAt': FieldValue.serverTimestamp(),
    });
    await chatRef.update({
      'lastMessage': text,
      'updatedAt': FieldValue.serverTimestamp(),
    });

    // Push bildirimi (başarısız olursa sessizce geç)
    try {
      await ref.read(apiProvider).post('/api/v1/notify/dm', data: {
        'recipient_uid': widget.otherUid,
        'title': me.displayName ?? 'Yeni mesaj',
        'body': text.length > 120 ? '${text.substring(0, 120)}…' : text,
        'chat_id': widget.chatId,
      });
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    final uid = FirebaseAuth.instance.currentUser!.uid;
    return CosmicScaffold(
      appBar: AppBar(title: Text(widget.otherName)),
      body: Column(children: [
        Expanded(
          child: StreamBuilder<QuerySnapshot<Map<String, dynamic>>>(
            stream: FirebaseFirestore.instance
                .collection('chats')
                .doc(widget.chatId)
                .collection('messages')
                .orderBy('createdAt', descending: true)
                .limit(100)
                .snapshots(),
            builder: (context, snapshot) {
              if (!snapshot.hasData) {
                return const Center(child: AstrolabeSpinner());
              }
              final docs = snapshot.data!.docs;
              return ListView.builder(
                reverse: true,
                padding: const EdgeInsets.all(16),
                itemCount: docs.length,
                itemBuilder: (_, i) {
                  final message = docs[i].data();
                  final mine = message['senderId'] == uid;
                  return Align(
                    alignment:
                        mine ? Alignment.centerRight : Alignment.centerLeft,
                    child: Container(
                      margin: const EdgeInsets.only(bottom: 10),
                      padding: const EdgeInsets.all(11),
                      constraints: BoxConstraints(
                          maxWidth: MediaQuery.of(context).size.width * 0.75),
                      decoration: BoxDecoration(
                        color: mine
                            ? RythoColors.inkLighter.withValues(alpha: 0.85)
                            : RythoColors.glassFill,
                        borderRadius: BorderRadius.only(
                          topLeft: const Radius.circular(16),
                          topRight: const Radius.circular(16),
                          bottomLeft: Radius.circular(mine ? 16 : 4),
                          bottomRight: Radius.circular(mine ? 4 : 16),
                        ),
                        border: Border.all(
                            color: mine
                                ? RythoColors.glassStroke
                                : RythoColors.gold.withValues(alpha: 0.5),
                            width: mine ? 1 : 0.6),
                      ),
                      child: Text(message['text'] ?? '',
                          style: RythoText.body(14.5)),
                    ),
                  );
                },
              );
            },
          ),
        ),
        Container(
          decoration: const BoxDecoration(
            border: Border(top: BorderSide(color: RythoColors.line)),
          ),
          padding: const EdgeInsets.fromLTRB(16, 10, 16, 10),
          child: SafeArea(
            child: Row(children: [
              Expanded(
                child: TextField(
                  controller: _controller,
                  style: RythoText.body(15),
                  decoration: const InputDecoration(hintText: 'Yaz...'),
                  onSubmitted: (_) => _send(),
                ),
              ),
              const SizedBox(width: 10),
              InkWell(
                onTap: _send,
                child: Container(
                  width: 44,
                  height: 44,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    border: Border.all(color: RythoColors.gold),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: const Text('✦',
                      style: TextStyle(
                          color: RythoColors.goldBright, fontSize: 18)),
                ),
              ),
            ]),
          ),
        ),
      ]),
    );
  }
}
