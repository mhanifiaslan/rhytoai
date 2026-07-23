import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import 'package:flutter_animate/flutter_animate.dart';

import '../../core/api.dart';
import '../../core/providers.dart';
import '../../core/sound.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/nebula_widgets.dart';

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
class MessagesTab extends ConsumerWidget {
  const MessagesTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final uid = FirebaseAuth.instance.currentUser!.uid;
    // Engellenen kullanıcılarla olan sohbetler listelenmez.
    final blocked = ref.watch(blockedUsersProvider).value ?? const <String>{};
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
        final docs = snapshot.data!.docs.where((d) {
          final participants = List<String>.from(d.data()['participants']);
          return !participants.any(blocked.contains);
        }).toList();
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

  /// Gelen mesaj sesi için bilinen mesaj sayısı (-1: ilk yükleme bekleniyor).
  int _knownCount = -1;

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    _controller.clear();
    SoundFx.send();
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

              // Yeni gelen (karşı taraftan) mesajda "ding" çal.
              if (_knownCount == -1) {
                _knownCount = docs.length;
              } else if (docs.length > _knownCount) {
                final newest = docs.isNotEmpty ? docs.first.data() : null;
                if (newest != null && newest['senderId'] != uid) {
                  SoundFx.receive();
                }
                _knownCount = docs.length;
              }

              return ListView.builder(
                reverse: true,
                padding: const EdgeInsets.all(16),
                itemCount: docs.length,
                itemBuilder: (_, i) {
                  final message = docs[i].data();
                  final mine = message['senderId'] == uid;
                  final bubble = Container(
                    margin: const EdgeInsets.only(bottom: 10),
                    padding: const EdgeInsets.symmetric(
                        horizontal: 14, vertical: 10),
                    constraints: BoxConstraints(
                        maxWidth: MediaQuery.of(context).size.width * 0.75),
                    decoration: BoxDecoration(
                      color: mine ? Colors.white : null,
                      gradient:
                          mine ? null : RythoColors.primaryGradient,
                      borderRadius: BorderRadius.only(
                        topLeft: const Radius.circular(18),
                        topRight: const Radius.circular(18),
                        bottomLeft: Radius.circular(mine ? 18 : 5),
                        bottomRight: Radius.circular(mine ? 5 : 18),
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.2),
                          blurRadius: 8,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    child: Text(
                      message['text'] ?? '',
                      style: RythoText.body(14.5,
                          color: mine
                              ? const Color(0xFF1D1230)
                              : Colors.white),
                    ),
                  );
                  return Align(
                    alignment:
                        mine ? Alignment.centerRight : Alignment.centerLeft,
                    child: i == 0
                        ? bubble
                            .animate()
                            .fadeIn(duration: 220.ms)
                            .slideY(begin: 0.25, curve: Curves.easeOutBack)
                            .scale(
                                begin: const Offset(0.94, 0.94),
                                curve: Curves.easeOutBack,
                                duration: 280.ms)
                        : bubble,
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
                  decoration: InputDecoration(
                    hintText: 'Yaz...',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(24),
                      borderSide:
                          const BorderSide(color: RythoColors.glassStroke),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(24),
                      borderSide:
                          const BorderSide(color: RythoColors.glassStroke),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(24),
                      borderSide:
                          const BorderSide(color: RythoColors.purple),
                    ),
                  ),
                  onSubmitted: (_) => _send(),
                ),
              ),
              const SizedBox(width: 10),
              Pressable(
                onTap: _send,
                child: Container(
                  width: 44,
                  height: 44,
                  alignment: Alignment.center,
                  decoration: const BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: RythoColors.primaryGradient,
                    boxShadow: [
                      BoxShadow(color: RythoColors.goldGlow, blurRadius: 14),
                    ],
                  ),
                  child: const Icon(Icons.send_rounded,
                      size: 19, color: Colors.white),
                ),
              ),
            ]),
          ),
        ),
      ]),
    );
  }
}
