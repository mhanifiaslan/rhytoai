import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../../core/friends.dart' show setStreakVisible;
import '../../core/providers.dart';
import '../../core/sound.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/nebula_widgets.dart';
import 'legal_page.dart';

/// SİCİL — kendi profilin: rozetler, günlük seri, doğum kaydı, gizlilik ve
/// uygulama ayarları, hukuki metinler ve oturum işlemleri.
///
/// Bu ekran yalnızca kullanıcının kendisine gösterilir; `users/{uid}` dokümanı
/// doğum verisi içerdiği için Firestore'da da yalnızca sahibine okunabilir.
/// Arkadaşların gördüğü alanlar ayrı bir karttan gelir (`publicProfiles/{uid}`).
class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  bool _soundsEnabled = true;

  @override
  void initState() {
    super.initState();
    _registerFcm();
    SoundFx.loadEnabled().then((v) {
      if (mounted) setState(() => _soundsEnabled = v);
    });
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
      backgroundColor: Colors.transparent,
      appBar: AppBar(title: const Text('Sicil')),
      body: ListView(
          padding: const EdgeInsets.only(top: 8, bottom: 110),
          children: [
        const SizedBox(height: 12),
        Center(
          child: Container(
            padding: const EdgeInsets.all(3),
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              gradient: RythoColors.primaryGradient,
              boxShadow: [
                BoxShadow(color: RythoColors.magentaGlow, blurRadius: 26),
              ],
            ),
            child: CircleAvatar(
              radius: 40,
              backgroundColor: RythoColors.inkLight,
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
              style: RythoText.display(26)),
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
              if (profile['sunSign'] != null)
                (emoji: '☀️', text: profile['sunSign'] as String),
              if (profile['moonSign'] != null)
                (emoji: '🌙', text: profile['moonSign'] as String),
              if (profile['ascendant'] != null)
                (emoji: '⬆️', text: profile['ascendant'] as String),
            ])
              Builder(builder: (_) {
                // Profildeki değerler sembol içeriyor ("Kova ♒"), birebir
                // eşleşme tutmaz — rozet rengi bu yüzden hep varsayılana
                // düşüyordu.
                final signIndex = signIndexOf(badge.text);
                final color = signIndex >= 0
                    ? RythoColors.signColors[signIndex]
                    : RythoColors.lilac;
                return Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.14),
                    border: Border.all(color: color.withValues(alpha: 0.5)),
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text('${badge.emoji} ${badge.text}',
                      style: RythoText.body(12, w: FontWeight.w700)),
                );
              }),
          ]),
        ),
        // Takipçi/takip sayaçları kaldırıldı: tek yönlü takip yerine karşılıklı
        // arkadaşlık modeli kullanılıyor (bkz. features/friends).
        // Günlük seri kartı 🔥
        Plaque(
          label: 'Günlük Seri',
          child: Row(children: [
            const Text('🔥', style: TextStyle(fontSize: 30)),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${(profile['streakCount'] as num?)?.toInt() ?? 0} gün',
                      style: RythoText.display(20),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Günlük okumayı her gün aç, serin büyüsün.',
                      style: RythoText.body(12,
                          color: RythoColors.parchmentDim),
                    ),
                  ]),
            ),
            StreakBadge(
                count: (profile['streakCount'] as num?)?.toInt() ?? 0),
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
        // Ayarlar: sesler aç/kapa
        Plaque(
          label: 'Ayarlar',
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
          child: Row(children: [
            const Icon(Icons.music_note_outlined,
                size: 18, color: RythoColors.lilac),
            const SizedBox(width: 10),
            Expanded(
                child: Text('Sesler', style: RythoText.body(14))),
            Switch(
              value: _soundsEnabled,
              activeThumbColor: RythoColors.magenta,
              activeTrackColor: RythoColors.violet.withValues(alpha: 0.5),
              onChanged: (v) {
                setState(() => _soundsEnabled = v);
                SoundFx.setEnabled(v);
                if (v) SoundFx.like();
              },
            ),
          ]),
        ),
        // Gizlilik: arkadaşlara ne göründüğü. Tüm görünürlük ayarları
        // varsayılan olarak KAPALIDIR ve yalnızca buradan açılır.
        Plaque(
          label: 'Gizlilik',
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
          child: Column(children: [
            Row(children: [
              const Icon(Icons.local_fire_department_outlined,
                  size: 18, color: RythoColors.lilac),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Serimi arkadaşlarım görsün',
                          style: RythoText.body(14)),
                      Text(
                        'Kapalıyken serin ve bugün okuyup okumadığın paylaşılmaz.',
                        style: RythoText.body(11.5,
                            color: RythoColors.parchmentDim),
                      ),
                    ]),
              ),
              Switch(
                value: profile['streakVisible'] == true,
                activeThumbColor: RythoColors.magenta,
                activeTrackColor: RythoColors.violet.withValues(alpha: 0.5),
                onChanged: (v) => setStreakVisible(v),
              ),
            ]),
          ]),
        ),
        Plaque(
          label: 'Hakkında',
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(
              'Rytho; Batı astrolojisi, BaZi ve I Ching geleneklerini hassas '
              'efemeris hesabıyla birleştirir. Yorumlar içgörü amaçlıdır; '
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
        // "Gönderilerin" bölümü kaldırıldı: kullanıcı üretimi serbest metin
        // v1 kapsamı dışında. Yerine Faz 5'te arkadaş katmanı (seri, hazır
        // tepkiler, günlük ikili dinamik) gelecek.
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

