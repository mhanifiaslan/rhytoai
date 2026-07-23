import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../../core/providers.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';

/// SİCİL — profil: rozetler, doğum kaydı, bildirim kaydı, oturum.
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

    return Scaffold(
      appBar: AppBar(title: const Text('Sicil')),
      body: ListView(padding: const EdgeInsets.symmetric(vertical: 8), children: [
        const SizedBox(height: 12),
        Center(
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
        const SizedBox(height: 16),
        Center(
          child: Wrap(spacing: 8, children: [
            for (final badge in [
              if (profile['sunSign'] != null) '☉ ${profile['sunSign']}',
              if (profile['moonSign'] != null) '☽ ${profile['moonSign']}',
              if (profile['ascendant'] != null) '↑ ${profile['ascendant']}',
            ])
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  border: Border.all(color: RythoColors.gold),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Text(badge,
                    style: RythoText.mono(12, color: RythoColors.goldBright)),
              ),
          ]),
        ),
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
        const SizedBox(height: 24),
      ]),
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
