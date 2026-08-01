import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';

import '../l10n/app_localizations.dart';
import '../theme/rytho_theme.dart';

/// Kullanıcı güvenliği yardımcıları: şikayet (report) ve engelleme (block).
/// Şikayetler `reports` koleksiyonuna yazılır ve yalnızca konsoldan incelenir;
/// engellenenler `users/{uid}/blocked/{targetUid}` altında tutulur.

/// Şikayet sebepleri. Anahtar Firestore'a yazılır ve **dilden bağımsızdır**;
/// kullanıcıya gösterilen etiket [reportReasonLabel] ile çözülür. Etiketi
/// kaydetseydik aynı sebep dile göre iki farklı değerle birikirdi ve
/// incelemede gruplanamazdı.
const List<String> kReportReasons = [
  'spam',
  'harassment',
  'inappropriate',
  'other',
];

String reportReasonLabel(AppLocalizations l10n, String key) => switch (key) {
      'spam' => l10n.reportReasonSpam,
      'harassment' => l10n.reportReasonHarassment,
      'inappropriate' => l10n.reportReasonInappropriate,
      _ => l10n.reportReasonOther,
    };

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
  final l10n = AppLocalizations.of(context);
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
            targetType == 'post' ? l10n.reportPostTitle : l10n.reportUserTitle,
            style: RythoText.mono(11, color: RythoColors.parchmentDim),
          ),
          const SizedBox(height: 6),
          Text(l10n.reportNote,
              style: RythoText.body(12.5, color: RythoColors.parchmentDim)),
          const SizedBox(height: 10),
          for (final reason in kReportReasons)
            ListTile(
              dense: true,
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12)),
              leading: const Text('⚑',
                  style: TextStyle(color: RythoColors.copper, fontSize: 15)),
              title: Text(reportReasonLabel(l10n, reason),
                  style: RythoText.body(14)),
              onTap: () async {
                Navigator.of(sheetContext).pop();
                try {
                  await submitReport(
                    targetType: targetType,
                    targetId: targetId,
                    reason: reason,
                  );
                  messenger.showSnackBar(
                      SnackBar(content: Text(l10n.reportSubmitted)));
                } catch (_) {
                  messenger.showSnackBar(
                      SnackBar(content: Text(l10n.reportFailed)));
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
