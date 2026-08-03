/// Sohbet arşivi — istemci okuma katmanı (Revize R4).
///
/// Yazma tarafı tamamen SUNUCUDA (`backend/services/chat_history.py`):
/// istemci `conversations` altına yazamaz (rules `write: false`), yalnızca
/// kendi konularını okur. Silme bile uçtan (`DELETE /chat/conversations`).
///
/// Desen `friends.dart`'taki stream sağlayıcılarının aynısı: oturum
/// değişince akış kapanır, açıkken Firestore canlı dinlenir.
library;

import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'providers.dart' show authStateProvider;

/// Konu özeti — liste ekranının satırı.
class Conversation {
  const Conversation({
    required this.id,
    required this.title,
    this.updatedAt,
    this.messageCount = 0,
  });

  final String id;
  final String title;
  final DateTime? updatedAt;
  final int messageCount;
}

/// Arşivlenmiş tek mesaj.
class ArchivedMessage {
  const ArchivedMessage({required this.sender, required this.text});

  final String sender; // USER | AI
  final String text;
}

/// Konular — en yeniden eskiye (kullanıcının istediği sıralama).
final conversationsProvider =
    StreamProvider.autoDispose<List<Conversation>>((ref) {
  final user = ref.watch(authStateProvider).value;
  if (user == null) return Stream.value(const []);

  return FirebaseFirestore.instance
      .collection('users')
      .doc(user.uid)
      .collection('conversations')
      .orderBy('updatedAt', descending: true)
      .limit(20)
      .snapshots()
      .map((s) => [
            for (final d in s.docs)
              Conversation(
                id: d.id,
                title: (d.data()['title'] as String?) ?? '…',
                updatedAt: (d.data()['updatedAt'] as Timestamp?)?.toDate(),
                messageCount:
                    (d.data()['messageCount'] as num?)?.toInt() ?? 0,
              ),
          ]);
});

/// Bir konunun mesajları — TEK SEFERLİK okuma, stream DEĞİL.
///
/// Bilinçli: sohbet ekranı mesajları yerelde biriktiriyor ve sunucu aynı
/// turu saniyeler sonra arka planda arşive yazıyor. Canlı dinleseydik her
/// tur ekranda İKİ KEZ belirirdi (yerel + arşivden gelen kopya). Arşiv
/// yalnızca AÇILIŞTA tohum verir; sonrası yerel.
Future<List<ArchivedMessage>> loadConversation(String uid, String id) async {
  final kar = await FirebaseFirestore.instance
      .collection('users')
      .doc(uid)
      .collection('conversations')
      .doc(id)
      .collection('messages')
      .orderBy('createdAt')
      .get();
  return [
    for (final d in kar.docs)
      ArchivedMessage(
        sender: (d.data()['sender'] as String?) ?? 'AI',
        text: (d.data()['text'] as String?) ?? '',
      ),
  ];
}

/// Konuyu sunucu üzerinden siler (istemcinin yazma izni yok).
Future<void> deleteConversation(Dio dio, String id) async {
  await dio.delete('/api/v1/chat/conversations/$id');
}
