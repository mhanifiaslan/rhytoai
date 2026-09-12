// Önekli: firebase_messaging'in `NotificationSettings` tipi bu ekranın
// kendi sınıf adıyla çakışıyor.
import 'package:firebase_messaging/firebase_messaging.dart' as fm;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/notifications.dart';
import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';

/// Bildirim tercihleri bölümü (Profil ekranı).
///
/// Üç anahtar ve bir sessiz saat aralığı. Hepsi `users/{uid}` dokümanına
/// yazılır; toplu gönderimi yapan sunucu tam olarak aynı alanları okur
/// (backend/services/notification_service.py).
///
/// Varsayılan AÇIK: kullanıcı sistem iznini zaten verdiyse günlük okumanın
/// bildirimini istiyor demektir. Sessiz saat varsayılanı 22:00–08:00 —
/// bu kategoride gece bildirimi, uygulamanın silinmesinin en hızlı yolu.
class NotificationSettings extends ConsumerWidget {
  const NotificationSettings({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final prefs = ref.watch(notificationPrefsProvider);

    return Plaque(
      label: l10n.notifications,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      child: Column(children: [
        const _PermissionBanner(),
        _Toggle(
          icon: Icons.wb_twilight_rounded,
          title: l10n.notifyDaily,
          body: l10n.notifyDailyBody,
          value: prefs.daily,
          onChanged: (v) => setNotificationPref('notifyDaily', v),
        ),
        _Toggle(
          icon: Icons.local_fire_department_outlined,
          title: l10n.notifyStreak,
          body: l10n.notifyStreakBody,
          value: prefs.streak,
          onChanged: (v) => setNotificationPref('notifyStreak', v),
        ),
        _Toggle(
          icon: Icons.favorite_outline_rounded,
          title: l10n.notifyFriends,
          body: l10n.notifyFriendsBody,
          value: prefs.friends,
          onChanged: (v) => setNotificationPref('notifyFriends', v),
        ),
        const Divider(height: 20),
        _QuietHours(prefs: prefs),
      ]),
    );
  }
}

/// OS izni kapalıysa dürüst uyarı (OT3).
///
/// Android'de izin yokken bile `getToken()` başarılı olduğu için sunucu
/// gönderiyor, sistem sessizce düşürüyor — kullanıcı buradaki anahtarları
/// açık görüp "bildirim gelmiyor" diyordu. Ayar ekranındaki bant, sorunun
/// UYGULAMADA değil sistem ayarında olduğunu söyler (yeni bağımlılık yok;
/// derin bağlantı yerine yol tarifi).
class _PermissionBanner extends StatelessWidget {
  const _PermissionBanner();

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return FutureBuilder<fm.NotificationSettings>(
      future: fm.FirebaseMessaging.instance.getNotificationSettings(),
      builder: (context, snap) {
        if (snap.data?.authorizationStatus !=
            fm.AuthorizationStatus.denied) {
          return const SizedBox.shrink();
        }
        return Container(
          margin: const EdgeInsets.only(top: 6, bottom: 8),
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: RythoColors.madder.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
                color: RythoColors.madder.withValues(alpha: 0.35)),
          ),
          child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Icon(Icons.notifications_off_outlined,
                size: 18, color: RythoColors.madder),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(l10n.notifPermissionOffTitle,
                        style: RythoText.body(13.5)),
                    const SizedBox(height: 2),
                    Text(l10n.notifPermissionOffBody,
                        style: RythoText.body(11.5,
                            color: RythoColors.parchmentDim)),
                  ]),
            ),
          ]),
        );
      },
    );
  }
}

class _Toggle extends StatelessWidget {
  const _Toggle({
    required this.icon,
    required this.title,
    required this.body,
    required this.value,
    required this.onChanged,
  });

  final IconData icon;
  final String title;
  final String body;
  final bool value;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(children: [
        Icon(icon, size: 18, color: RythoColors.lilac),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: RythoText.body(14)),
                Text(body,
                    style:
                        RythoText.body(11.5, color: RythoColors.parchmentDim)),
              ]),
        ),
        Switch(
          value: value,
          activeThumbColor: RythoColors.magenta,
          activeTrackColor: RythoColors.violet.withValues(alpha: 0.5),
          onChanged: onChanged,
        ),
      ]),
    );
  }
}

/// Sessiz saat aralığı seçimi.
///
/// Başlangıç ve bitiş eşitse sessiz saat KAPALI sayılır — sunucu da aynı
/// kuralı uyguluyor. Eşitliği "24 saat sessiz" saymak, kullanıcının hiç
/// bildirim almaması demek olurdu ve bunu fark etmesi imkânsız olurdu.
class _QuietHours extends StatelessWidget {
  const _QuietHours({required this.prefs});

  final NotificationPrefs prefs;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Row(children: [
      const Icon(Icons.bedtime_outlined, size: 18, color: RythoColors.lilac),
      const SizedBox(width: 10),
      Expanded(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(l10n.quietHours, style: RythoText.body(14)),
          Text(l10n.quietHoursBody,
              style: RythoText.body(11.5, color: RythoColors.parchmentDim)),
        ]),
      ),
      // Düğme esnemiyordu: soldaki açıklama `Expanded` içinde sıfıra inse
      // bile "22:00 – 08:00" / "Kapalı" + iç dolgu dar ekranda satırı
      // taşırıyordu.
      Flexible(
        child: TextButton(
          onPressed: () => _pick(context),
          child: Text(
            prefs.quietDisabled
                ? l10n.quietHoursOff
                : l10n.quietHoursRange(
                    prefs.quietFrom.toString().padLeft(2, '0'),
                    prefs.quietTo.toString().padLeft(2, '0')),
            style: RythoText.label(12, color: RythoColors.goldBright),
          ),
        ),
      ),
    ]);
  }

  Future<void> _pick(BuildContext context) async {
    final l10n = AppLocalizations.of(context);

    final baslangic = await showTimePicker(
      context: context,
      initialTime: TimeOfDay(hour: prefs.quietFrom, minute: 0),
      helpText: l10n.quietHours,
    );
    if (baslangic == null || !context.mounted) return;

    final bitis = await showTimePicker(
      context: context,
      initialTime: TimeOfDay(hour: prefs.quietTo, minute: 0),
      helpText: l10n.quietHours,
    );
    if (bitis == null) return;

    // Dakika yok sayılır: sunucu saat çözünürlüğünde çalışıyor ve dakika
    // hassasiyeti sözü vermek yanıltıcı olurdu.
    await setNotificationPref('quietFrom', baslangic.hour);
    await setNotificationPref('quietTo', bitis.hour);
  }
}
