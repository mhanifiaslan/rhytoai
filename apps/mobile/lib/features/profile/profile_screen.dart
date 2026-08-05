import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../../theme/rytho_tokens.dart';
import '../../widgets/common.dart';
import '../../widgets/glass.dart' show SkeletonPanel;
import 'account_screen.dart';
import 'birth_record_screen.dart';
import 'delete_account.dart';
import 'profile_sections.dart';
import '../paywall/redeem_code_dialog.dart';
import '../../core/providers.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/nebula_widgets.dart';
import '../../l10n/app_localizations.dart';

/// SİCİL — kendi profilin: kimlik, günlük seri ve **altı ayar satırı**.
///
/// ## Yeniden kurgulandı
///
/// Önceki hâl ~1400 px'di: yedi kart ve satır içine serpiştirilmiş on dört
/// kontrol. Kullanıcının tarifi "aşağı doğru uzayan bir liste" idi ve önerisi
/// de doğruydu — "aynı kategoriler bir başlıkta toplanılarak tıklanınca alt
/// seçenekler çıkabilir".
///
/// Gruplama aslında **vardı**; sorun tek seviyeli olmasıydı. Yedi başlık
/// hepsi açık hâlde alt alta duruyordu, yani gruplama hiçbir şey gizlemiyor,
/// yalnızca araya başlık koyuyordu. Şimdi her grup kendi sayfasında
/// (bkz. profile_sections.dart).
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
  // Bildirim izni buradan İSTENMİYOR: profil ekranını açmak izin sormak için
  // yanlış an. İzin, kullanıcı ilk değeri gördükten sonra ana ekranda
  // isteniyor (bkz. core/notifications.dart ve sky_screen).

  @override
  Widget build(BuildContext context) {
    final profilAsync = ref.watch(profileProvider);
    final profile = profilAsync.value ?? {};
    final user = FirebaseAuth.instance.currentUser;
    final l10n = AppLocalizations.of(context);

    // Profil henüz yüklenmediyse iskelet (R12-B3): eskiden bu ekran boş
    // haritayla ("yok" gibi görünen alanlarla) açılıyordu.
    if (profilAsync.isLoading && profile.isEmpty) {
      return Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(title: Text(l10n.profileTitle)),
        body: ListView(
            padding: const EdgeInsets.only(top: 20, bottom: 110),
            children: const [
              SkeletonPanel(height: 140),
              SkeletonPanel(height: 84),
              SkeletonPanel(height: 220),
            ]),
      );
    }

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
        // ---------- İKİ SEVİYELİ AYARLAR ----------
        //
        // Önceki hâl: yedi kart ve satır içine serpiştirilmiş on dört
        // kontrol, ~1400 px. Gruplama vardı ama TEK SEVİYELİYDİ — her grup
        // açıktı, hepsi aynı anda görünüyordu. Gruplamanın işe yaraması için
        // kapanabilmesi gerekiyor.
        //
        // Doğum kaydı ve hesap ayrıca DÜZELTİLEBİLİR oldu; daha önce ikisi
        // de bir kez yazılıp kilitleniyordu.
        Plaque(
          padding: const EdgeInsets.symmetric(vertical: RythoSpace.xs),
          child: Column(children: [
            SettingsRow(
              icon: Icons.cake_outlined,
              title: l10n.birthRecord,
              subtitle: l10n.birthRecordRowSubtitle,
              value: profile['birthDate'] as String?,
              onTap: () => _ac(const BirthRecordScreen()),
            ),
            const Divider(height: 1, indent: RythoSpace.lg),
            SettingsRow(
              icon: Icons.person_outline_rounded,
              title: l10n.accountSection,
              value: profile['username'] != null
                  ? '@${profile['username']}'
                  : profile['displayName'] as String?,
              onTap: () => _ac(const AccountScreen()),
            ),
            const Divider(height: 1, indent: RythoSpace.lg),
            SettingsRow(
              icon: Icons.notifications_none_rounded,
              title: l10n.notifications,
              onTap: () => _ac(const NotificationSettingsScreen()),
            ),
            const Divider(height: 1, indent: RythoSpace.lg),
            SettingsRow(
              icon: Icons.lock_outline_rounded,
              title: l10n.privacy,
              onTap: () => _ac(const PrivacySettingsScreen()),
            ),
            const Divider(height: 1, indent: RythoSpace.lg),
            SettingsRow(
              icon: Icons.tune_rounded,
              title: l10n.languageAndSounds,
              onTap: () => _ac(const AppearanceSettingsScreen()),
            ),
            const Divider(height: 1, indent: RythoSpace.lg),
            // Ortak kodu (W9): jeton bonusu + gelir atfı. Kalıcı giriş
            // noktası burası; paywall'da da küçük bir link var.
            SettingsRow(
              icon: Icons.redeem_rounded,
              title: l10n.redeemCodeTitle,
              onTap: () => showRedeemCodeDialog(context, ref),
            ),
            const Divider(height: 1, indent: RythoSpace.lg),
            SettingsRow(
              icon: Icons.info_outline_rounded,
              title: l10n.about,
              onTap: () => _ac(const AboutScreen()),
            ),
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
        // Hesap silme (Apple 5.1.1(v) / Google Play zorunluluğu).
        // Çıkış yapmakla karıştırılmaması için ayrı ve sönük duruyor; ama
        // "gömülü olmamalı" kuralı gereği ana profil ekranında, ek bir
        // menünün arkasında değil.
        Center(
          child: TextButton(
            onPressed: () => showDeleteAccountSheet(context),
            child: Text(
              l10n.deleteAccount,
              style: RythoText.label(12, color: RythoColors.parchmentDim),
            ),
          ),
        ),
        // "Gönderilerin" bölümü kaldırıldı: kullanıcı üretimi serbest metin
        // v1 kapsamı dışında. Yerine Faz 5'te arkadaş katmanı (seri, hazır
        // tepkiler, günlük ikili dinamik) gelecek.
        const SizedBox(height: 24),
      ]),
    );
  }

  void _ac(Widget sayfa) =>
      Navigator.of(context).push(MaterialPageRoute(builder: (_) => sayfa));

}

// `_row` ve `_FaceConsentRow` KALDIRILDI (Tasarım A4). Etiket-değer
// satırı `LabelValueRow`'a, rıza satırı da gizlilik alt sayfasına
// taşındı (bkz. profile_sections.dart).
