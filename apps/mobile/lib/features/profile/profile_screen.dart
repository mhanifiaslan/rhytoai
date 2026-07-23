import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../../core/providers.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import '../council/feed_tab.dart' show PostCard;
import 'legal_page.dart';

/// SİCİL — birleşik profil: başkalarının gördüğü sayfa (rozetler, sayaçlar,
/// gönderiler) + kendi ayarların (doğum kaydı, bildirim, oturum).
class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  @override
  void initState() {
    super.initState();
    _registerFcm();
  }

  Future<void> _registerFcm() async {
    try {
      final messaging = FirebaseMessaging.instance;
      await messaging.requestPermission();
      final token = await messaging.getToken();
      final uid = FirebaseAuth.instance.currentUser?.uid;
      if (token != null && uid != null) {
        await FirebaseFirestore.instance
            .collection('users')
            .doc(uid)
            .set({'fcmToken': token}, SetOptions(merge: true));
      }
    } catch (_) {
      // Web/emülatörde izin yoksa sessizce geç
    }
  }

  @override
  Widget build(BuildContext context) {
    final profile = ref.watch(profileProvider).value ?? {};
    final user = FirebaseAuth.instance.currentUser;
    final uid = user?.uid;

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(title: const Text('Sicil')),
      body: ListView(
          padding: const EdgeInsets.only(top: 8, bottom: 110),
          children: [
        const SizedBox(height: 12),
        Center(
          child: Container(
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(color: RythoColors.goldGlow, blurRadius: 30),
              ],
            ),
            child: CircleAvatar(
              radius: 40,
              backgroundColor: RythoColors.inkLighter,
              backgroundImage: profile['photoUrl'] != null
                  ? NetworkImage(profile['photoUrl'])
                  : null,
              child: profile['photoUrl'] == null
                  ? Text('☽', style: RythoText.display(28))
                  : null,
            ),
          ),
        ),
        const SizedBox(height: 12),
        Center(
          child: Text(profile['displayName'] ?? user?.displayName ?? 'Gezgin',
              style: RythoText.display(28)),
        ),
        const SizedBox(height: 4),
        Center(
          child: Text(user?.email ?? '',
              style: RythoText.mono(11, color: RythoColors.parchmentDim)),
        ),
        const SizedBox(height: 14),
        Center(
          child: Wrap(spacing: 8, children: [
            for (final badge in [
              if (profile['sunSign'] != null) '☉ ${profile['sunSign']}',
              if (profile['moonSign'] != null) '☽ ${profile['moonSign']}',
              if (profile['ascendant'] != null) '↑ ${profile['ascendant']}',
            ])
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
                decoration: BoxDecoration(
                  color: RythoColors.glassFill,
                  border: Border.all(color: RythoColors.glassStroke),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Text(badge,
                    style: RythoText.mono(11, color: RythoColors.goldBright)),
              ),
          ]),
        ),
        if (uid != null) ...[
          const SizedBox(height: 14),
          _FollowCounters(uid: uid),
        ],
        Plaque(
          label: 'Doğum Kaydı',
          child: Column(children: [
            _row('Tarih', profile['birthDate'] ?? '—'),
            _row('Saat', profile['birthTime'] ?? '—'),
            _row('Şehir', profile['birthCity'] ?? '—'),
          ]),
        ),
        Plaque(
          label: 'Hakkında',
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(
              'Rytho; Batı astrolojisi, BaZi, I Ching ve İlm-i Sima geleneklerini '
              'hassas efemeris hesabıyla birleştirir. Yorumlar içgörü amaçlıdır; '
              'tıbbi, hukuki veya finansal tavsiye değildir.',
              style: RythoText.body(13, color: RythoColors.parchmentDim),
            ),
            const SizedBox(height: 10),
            Text('Efemeris: Swiss Ephemeris © Astrodienst AG',
                style: RythoText.mono(10, color: RythoColors.parchmentDim)),
            const SizedBox(height: 12),
            const Divider(height: 1),
            _legalLink(context, 'Gizlilik Politikası',
                () => const LegalPage(
                    title: 'Gizlilik Politikası',
                    sections: kPrivacyPolicySections)),
            const Divider(height: 1),
            _legalLink(context, 'Kullanım Şartları',
                () => const LegalPage(
                    title: 'Kullanım Şartları',
                    sections: kTermsOfUseSections)),
          ]),
        ),
        Padding(
          padding: const EdgeInsets.all(16),
          child: GoldButton(
            text: 'Oturumu kapat',
            onPressed: () async {
              try {
                await GoogleSignIn.instance.signOut();
              } catch (_) {}
              await FirebaseAuth.instance.signOut();
            },
          ),
        ),
        if (uid != null) ...[
          const SectionDivider(),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Text('Gönderilerin', style: RythoText.display(20)),
          ),
          const SizedBox(height: 6),
          StreamBuilder<QuerySnapshot<Map<String, dynamic>>>(
            stream: FirebaseFirestore.instance
                .collection('posts')
                .where('authorId', isEqualTo: uid)
                .orderBy('createdAt', descending: true)
                .limit(20)
                .snapshots(),
            builder: (_, snapshot) {
              final docs = snapshot.data?.docs ?? [];
              if (docs.isEmpty) {
                return Padding(
                  padding: const EdgeInsets.all(20),
                  child: Center(
                    child: Text('Meclis\'te henüz söz almadın.',
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
        const SizedBox(height: 24),
      ]),
    );
  }

  /// Hukuki metin sayfasını açan sade satır.
  Widget _legalLink(
      BuildContext context, String title, Widget Function() pageBuilder) {
    return InkWell(
      onTap: () => Navigator.of(context)
          .push(MaterialPageRoute(builder: (_) => pageBuilder())),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 12),
        child: Row(children: [
          Expanded(child: Text(title, style: RythoText.body(13.5))),
          Text('›',
              style: RythoText.body(16, color: RythoColors.parchmentDim)),
        ]),
      ),
    );
  }

  Widget _row(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(children: [
        SizedBox(
            width: 90,
            child: Text(label.toUpperCase(),
                style: RythoText.mono(10, color: RythoColors.parchmentDim))),
        Text(value, style: RythoText.body(14)),
      ]),
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
