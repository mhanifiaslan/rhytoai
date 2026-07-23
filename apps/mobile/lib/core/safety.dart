import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';

import '../theme/rytho_theme.dart';

/// Kullanıcı güvenliği yardımcıları: şikayet (report) ve engelleme (block).
/// Şikayetler `reports` koleksiyonuna yazılır ve yalnızca konsoldan incelenir;
/// engellenenler `users/{uid}/blocked/{targetUid}` altında tutulur.

const List<String> kReportReasons = [
  'Spam veya yanıltıcı içerik',
  'Hakaret veya taciz',
  'Uygunsuz / rahatsız edici içerik',
  'Diğer',
];

/// Şikayeti Firestore'a yazar. targetType: 'post' | 'user'.
Future<void> submitReport({
  required String targetType,
  required String targetId,
  required String reason,
}) async {
  final uid = FirebaseAuth.instance.currentUser!.uid;
  await FirebaseFirestore.instance.collection('reports').add({
    'reporterId': uid,
    'targetType': targetType,
    'targetId': targetId,
    'reason': reason,
    'createdAt': FieldValue.serverTimestamp(),
  });
}

/// Sebep seçtiren cam görünümlü şikayet sayfası (bottom sheet).
Future<void> showReportSheet(
  BuildContext context, {
  required String targetType,
  required String targetId,
}) async {
  final messenger = ScaffoldMessenger.of(context);
  await showModalBottomSheet<void>(
    context: context,
    backgroundColor: RythoColors.inkLight,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(22)),
      side: BorderSide(color: RythoColors.glassStroke),
    ),
    builder: (sheetContext) => SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 20, 20, 24),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Text(
            targetType == 'post' ? 'GÖNDERİYİ ŞİKAYET ET' : 'KULLANICIYI ŞİKAYET ET',
            style: RythoText.mono(11, color: RythoColors.parchmentDim),
          ),
          const SizedBox(height: 6),
          Text('Şikayetin ekibimiz tarafından incelenir.',
              style: RythoText.body(12.5, color: RythoColors.parchmentDim)),
          const SizedBox(height: 10),
          for (final reason in kReportReasons)
            ListTile(
              dense: true,
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12)),
              leading: const Text('⚑',
                  style: TextStyle(color: RythoColors.copper, fontSize: 15)),
              title: Text(reason, style: RythoText.body(14)),
              onTap: () async {
                Navigator.of(sheetContext).pop();
                try {
                  await submitReport(
                    targetType: targetType,
                    targetId: targetId,
                    reason: reason,
                  );
                  messenger.showSnackBar(const SnackBar(
                      content: Text(
                          'Şikayetin alındı; en kısa sürede incelenecek. Teşekkürler.')));
                } catch (e) {
                  messenger.showSnackBar(
                      SnackBar(content: Text('Şikayet gönderilemedi: $e')));
                }
              },
            ),
        ]),
      ),
    ),
  );
}

DocumentReference<Map<String, dynamic>> _blockedRef(String targetUid) {
  final uid = FirebaseAuth.instance.currentUser!.uid;
  return FirebaseFirestore.instance
      .collection('users')
      .doc(uid)
      .collection('blocked')
      .doc(targetUid);
}

/// Kullanıcıyı engelle: akışta ve mesajlarda içeriği istemci tarafında gizlenir.
Future<void> blockUser(String targetUid) =>
    _blockedRef(targetUid).set({'at': FieldValue.serverTimestamp()});

/// Engeli kaldır.
Future<void> unblockUser(String targetUid) => _blockedRef(targetUid).delete();
