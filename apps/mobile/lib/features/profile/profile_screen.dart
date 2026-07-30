import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../../core/friends.dart' show setStreakVisible;
import '../../core/locale.dart';
import '../../core/providers.dart';
import '../../core/sound.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/nebula_widgets.dart';
import '../../l10n/app_localizations.dart';
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
    final l10n = AppLocalizations.of(context);

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(title: Text(l10n.profileTitle)),
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
          child: Text(
              profile['displayName'] ??
                  user?.displayName ??
                  l10n.defaultUserName,
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
                // Firestore'daki değer Türkçe ("Kova ♒"); rozet metni arayüz
                // diline çevrilir, tanınmazsa geldiği gibi gösterilir.
                final ad = signIndex >= 0
                    ? signDisplayName(l10n, signIndex)
                    : badge.text;
                return Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.14),
                    border: Border.all(color: color.withValues(alpha: 0.5)),
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text('${badge.emoji} $ad',
                      style: RythoText.body(12, w: FontWeight.w700)),
                );
              }),
          ]),
        ),
        // Takipçi/takip sayaçları kaldırıldı: tek yönlü takip yerine karşılıklı
        // arkadaşlık modeli kullanılıyor (bkz. features/friends).
        // Günlük seri kartı 🔥
        Plaque(
          label: l10n.dailyStreak,
          child: Row(children: [
            const Text('🔥', style: TextStyle(fontSize: 30)),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      l10n.streakDays(
                          (profile['streakCount'] as num?)?.toInt() ?? 0),
                      style: RythoText.display(20),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      l10n.streakBody,
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
          label: l10n.birthRecord,
          child: Column(children: [
            _row(l10n.birthDate, profile['birthDate'] ?? '—'),
            _row(l10n.birthTime, profile['birthTime'] ?? '—'),
            _row(l10n.birthCity, profile['birthCity'] ?? '—'),
          ]),
        ),
        // Ayarlar: sesler aç/kapa
        Plaque(
          label: l10n.settings,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
          child: Row(children: [
            const Icon(Icons.music_note_outlined,
                size: 18, color: RythoColors.lilac),
            const SizedBox(width: 10),
            Expanded(
                child: Text(l10n.sounds, style: RythoText.body(14))),
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
        // Dil: arayüz metinlerini VE backend'in ürettiği yorumların dilini
        // birlikte belirler (Accept-Language ile taşınır, bkz. core/locale.dart).
        Plaque(
          label: l10n.language,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
          child: Column(children: [
            for (final secim in <(String, Locale?)>[
              (l10n.languageSystem, null),
              (l10n.languageTurkish, const Locale('tr')),
              (l10n.languageEnglish, const Locale('en')),
            ])
              Builder(builder: (_) {
                final secili = ref.watch(localeProvider)?.languageCode ==
                    secim.$2?.languageCode;
                return ListTile(
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                  title: Text(secim.$1, style: RythoText.body(14)),
                  trailing: Icon(
                    secili
                        ? Icons.radio_button_checked_rounded
                        : Icons.radio_button_unchecked_rounded,
                    size: 20,
                    color: secili
                        ? RythoColors.magenta
                        : RythoColors.parchmentDim,
                  ),
                  onTap: () => ref.read(localeProvider.notifier).set(secim.$2),
                );
              }),
          ]),
        ),
        // Gizlilik: arkadaşlara ne göründüğü. Tüm görünürlük ayarları
        // varsayılan olarak KAPALIDIR ve yalnızca buradan açılır.
        Plaque(
          label: l10n.privacy,
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
                      Text(l10n.streakVisibleSetting,
                          style: RythoText.body(14)),
                      Text(
                        l10n.streakVisibleSettingBody,
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
          label: l10n.about,
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(
              l10n.aboutBody,
              style: RythoText.body(13, color: RythoColors.parchmentDim),
            ),
            const SizedBox(height: 10),
            Text(l10n.ephemerisCredit,
                style: RythoText.mono(10, color: RythoColors.parchmentDim)),
            const SizedBox(height: 12),
            const Divider(height: 1),
            _legalLink(
                context,
                l10n.privacyPolicy,
                () => LegalPage(
                    title: l10n.privacyPolicy,
                    sections: privacyPolicySections(
                        Localizations.localeOf(context).languageCode))),
            const Divider(height: 1),
            _legalLink(
                context,
                l10n.termsOfUse,
                () => LegalPage(
                    title: l10n.termsOfUse,
                    sections: termsOfUseSections(
                        Localizations.localeOf(context).languageCode))),
          ]),
        ),
        Padding(
          padding: const EdgeInsets.all(16),
          child: GoldButton(
            text: l10n.signOut,
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

