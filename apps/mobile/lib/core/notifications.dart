import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_timezone/flutter_timezone.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../features/shell/app_shell.dart' show shellTabProvider;
import 'locale.dart';
import 'providers.dart';

/// Bildirim izni, cihaz bilgisi senkronu ve tercihler.
///
/// Bildirim metni **sunucuda** üretiliyor (backend/services/notification_service.py),
/// bu yüzden sunucunun üç şeyi bilmesi gerekir ve üçü de profile yazılır:
///
/// 1. **FCM token** — nereye gönderileceği.
/// 2. **Saat dilimi** — bildirimin kullanıcının sabahına denk gelmesi için.
///    Doğum şehri kullanılamaz; kişi doğduğu yerde yaşamıyor olabilir.
/// 3. **Dil** — sunucu istek başlığı görmediği için `Accept-Language` burada
///    işe yaramaz.
///
/// İzin isteme zamanı da bilinçli: uygulama ilk açılışta değil, kullanıcı
/// onboarding'i bitirip ilk değeri gördükten sonra sorulur. Değer görmeden
/// sorulan izin reddediliyor ve bir daha sorulamıyor.

/// Bildirim tercihleri — profildeki alanların yazılabilir görünümü.
class NotificationPrefs {
  const NotificationPrefs({
    this.daily = true,
    this.streak = true,
    this.friends = true,
    this.quietFrom = 22,
    this.quietTo = 8,
  });

  final bool daily;
  final bool streak;
  final bool friends;
  final int quietFrom;
  final int quietTo;

  factory NotificationPrefs.fromProfile(Map<String, dynamic>? profile) {
    final p = profile ?? const {};
    return NotificationPrefs(
      // Alan yoksa AÇIK sayılır; sunucu tarafı da aynı varsayımı yapıyor.
      daily: p['notifyDaily'] != false,
      streak: p['notifyStreak'] != false,
      friends: p['notifyFriends'] != false,
      quietFrom: (p['quietFrom'] as num?)?.toInt() ?? 22,
      quietTo: (p['quietTo'] as num?)?.toInt() ?? 8,
    );
  }

  bool get quietDisabled => quietFrom == quietTo;
}

final notificationPrefsProvider = Provider<NotificationPrefs>((ref) {
  return NotificationPrefs.fromProfile(ref.watch(profileProvider).value);
});

Future<void> setNotificationPref(String field, Object? value) async {
  final uid = FirebaseAuth.instance.currentUser?.uid;
  if (uid == null) return;
  await FirebaseFirestore.instance
      .collection('users')
      .doc(uid)
      .set({field: value}, SetOptions(merge: true));
}

/// Cihazın IANA saat dilimi ("Europe/Istanbul").
///
/// `DateTime.now().timeZoneName` kullanılamaz: platforma göre "+03" ya da
/// "GMT+03:00" gibi kısaltmalar döner ve sunucudaki ZoneInfo bunları
/// çözemez. Ayrıca ham UTC farkı da yeterli değil — yaz saati değişiminde
/// uygulamayı açmayan kullanıcının bildirimi bir saat kayardı.
Future<String?> _deviceTimezone() async {
  try {
    // flutter_timezone 5.x düz string değil TimezoneInfo döndürüyor;
    // sunucunun beklediği IANA adı `identifier` alanında.
    final bilgi = await FlutterTimezone.getLocalTimezone();
    return bilgi.identifier;
  } catch (e) {
    debugPrint('Saat dilimi okunamadı: $e');
    return null;
  }
}

/// Sunucunun bildirim gönderebilmesi için gereken cihaz bilgisini yazar.
///
/// Her açılışta çağrılır: token yenilenebilir, kullanıcı seyahat edebilir,
/// yaz saati değişebilir, dil değişebilir.
Future<void> syncNotificationContext({String? languageCode}) async {
  final uid = FirebaseAuth.instance.currentUser?.uid;
  if (uid == null) return;

  final guncelleme = <String, dynamic>{};

  final tz = await _deviceTimezone();
  if (tz != null && tz.isNotEmpty) guncelleme['timezone'] = tz;
  if (languageCode != null) guncelleme['language'] = languageCode;

  try {
    // Token yalnızca izin verilmişse alınabilir; izin yoksa sessizce geçilir
    // ve kullanıcı izni sonradan verdiğinde bir sonraki açılışta yazılır.
    final token = await FirebaseMessaging.instance.getToken();
    if (token != null) guncelleme['fcmToken'] = token;
  } catch (e) {
    debugPrint('FCM token alınamadı: $e');
  }

  if (guncelleme.isEmpty) return;
  try {
    await FirebaseFirestore.instance
        .collection('users')
        .doc(uid)
        .set(guncelleme, SetOptions(merge: true));
  } catch (e) {
    debugPrint('Bildirim bağlamı yazılamadı: $e');
  }
}

const String _kPermissionAskedKey = 'notificationPermissionAsked';

/// İzin daha önce istendi mi?
///
/// İşletim sistemi izni zaten bir kez soruyor; bu bayrak bizim tarafımızda
/// gereksiz çağrıyı ve her açılışta senkron denemesini engelliyor.
Future<bool> notificationPromptShown() async {
  try {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_kPermissionAskedKey) ?? false;
  } catch (_) {
    // Okunamazsa sormuş gibi davran: kullanıcıyı her açılışta izin
    // diyaloğuyla karşılaştırma riski, bir kez sormamaktan kötü.
    return true;
  }
}

Future<void> markNotificationPromptShown() async {
  try {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kPermissionAskedKey, true);
  } catch (_) {}
}

/// Bildirim iznini ister ve sonucu döndürür.
///
/// Ayrı bir fonksiyon: izin isteme ANI ürün kararıdır (bkz. sınıf açıklaması)
/// ve senkronizasyondan bağımsız tetiklenir.
Future<bool> requestNotificationPermission() async {
  try {
    final ayar = await FirebaseMessaging.instance.requestPermission();
    final verildi =
        ayar.authorizationStatus == AuthorizationStatus.authorized ||
            ayar.authorizationStatus == AuthorizationStatus.provisional;
    if (verildi) await syncNotificationContext();
    return verildi;
  } catch (e) {
    debugPrint('Bildirim izni istenemedi: $e');
    return false;
  }
}

/// Token yenilendiğinde profili güncel tutar.
///
/// FCM token'ı kendiliğinden dönebiliyor; dinlenmezse kullanıcı sessizce
/// bildirim almaz hâle gelir ve bunu kimse fark etmez.
void listenForTokenRefresh() {
  FirebaseMessaging.instance.onTokenRefresh.listen((token) async {
    final uid = FirebaseAuth.instance.currentUser?.uid;
    if (uid == null) return;
    try {
      await FirebaseFirestore.instance
          .collection('users')
          .doc(uid)
          .set({'fcmToken': token}, SetOptions(merge: true));
    } catch (e) {
      debugPrint('Yenilenen token yazılamadı: $e');
    }
  });
}

// ---------------------------------------------------------------------------
// Ön plan bildirimi
//
// Android'de FCM'in `notification` yükü YALNIZCA uygulama arka plandayken
// sistem tepsisinde gösterilir. Uygulama açıkken bildirim `onMessage`'a
// teslim edilir ve göstermek uygulamanın işidir — bu yapılmazsa bildirim
// sessizce düşer ve kullanıcı hiçbir şey görmez.
//
// Kanal ayrıca arka plan için de önemli: Android 8+ bildirimi bir kanala
// bağlar ve FCM'in varsayılan kanalı "default" öneme sahiptir. Yüksek
// öncelikli kanal olmadan bildirim ekranın üstünde belirmez, sessizce
// tepsiye düşer.
// ---------------------------------------------------------------------------

const AndroidNotificationChannel _kChannel = AndroidNotificationChannel(
  'rytho_default',
  'Rytho',
  description: 'Günlük okuma, seri hatırlatması ve arkadaş tepkileri.',
  importance: Importance.high,
);

final FlutterLocalNotificationsPlugin _localNotifications =
    FlutterLocalNotificationsPlugin();

bool _yerelBildirimHazir = false;

/// Yerel bildirim altyapısını kurar (kanal + dokunma yönlendirmesi).
Future<void> _initLocalNotifications(ValueChanged<int> onSelectTab) async {
  if (_yerelBildirimHazir) return;
  _yerelBildirimHazir = true;

  try {
    await _localNotifications.initialize(
      settings: const InitializationSettings(
        android: AndroidInitializationSettings('@mipmap/ic_launcher'),
        iOS: DarwinInitializationSettings(),
      ),
      onDidReceiveNotificationResponse: (yanit) {
        final ham = yanit.payload;
        if (ham == null || ham.isEmpty) return;
        // Yük, gönderildiği gibi düz `anahtar=deger` çiftleri.
        final veri = <String, dynamic>{};
        for (final parca in ham.split('&')) {
          final i = parca.indexOf('=');
          if (i > 0) veri[parca.substring(0, i)] = parca.substring(i + 1);
        }
        onSelectTab(tabForNotification(veri));
      },
    );

    await _localNotifications
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(_kChannel);
  } catch (e) {
    debugPrint('Yerel bildirim kurulamadı: $e');
  }
}

/// Ön planda gelen bildirimi ekranda gösterir.
Future<void> _showForeground(RemoteMessage mesaj) async {
  final bildirim = mesaj.notification;
  if (bildirim == null) return;

  final yuk = mesaj.data.entries.map((e) => '${e.key}=${e.value}').join('&');
  try {
    await _localNotifications.show(
      // Kimlik olarak zaman damgası: aynı anda birden fazla bildirim
      // gelirse birbirinin üstüne yazmasın. 32 bit sınırına sığması için
      // saniye çözünürlüğünde ve mod alınmış.
      id: (DateTime.now().millisecondsSinceEpoch ~/ 1000) % 0x7FFFFFFF,
      title: bildirim.title,
      body: bildirim.body,
      notificationDetails: NotificationDetails(
        android: AndroidNotificationDetails(
          _kChannel.id,
          _kChannel.name,
          channelDescription: _kChannel.description,
          importance: Importance.high,
          priority: Priority.high,
        ),
        iOS: const DarwinNotificationDetails(),
      ),
      payload: yuk,
    );
  } catch (e) {
    debugPrint('Ön plan bildirimi gösterilemedi: $e');
  }
}

/// Bildirime dokunulduğunda hangi sekmenin açılacağı.
///
/// Sunucu her bildirime `type` alanı koyuyor (daily / streak / friend).
/// Eşleşmeyen bir tür gelirse ana ekranda kalınır — bilinmeyen bir değer
/// yüzünden uygulama boş bir ekrana düşmemeli.
int tabForNotification(Map<String, dynamic> data) {
  switch (data['type']) {
    case 'friend':
      return 2; // Arkadaşlar
    case 'daily':
    case 'streak':
    default:
      return 0; // Gökyüzü
  }
}

/// Bildirim alımını ve dokunma yönlendirmesini kurar.
///
/// Üç yol da bağlanır, çünkü Android üçünü farklı ele alıyor:
/// - **Ön plan:** sistem hiçbir şey göstermez, biz gösteririz.
/// - **Arka plan:** sistem gösterir, dokunma `onMessageOpenedApp`'e gelir.
/// - **Kapalı:** sistem gösterir, dokunma uygulamayı açar ve
///   `getInitialMessage` ile okunur.
Future<void> handleNotificationTaps(
    ValueChanged<int> onSelectTab) async {
  await _initLocalNotifications(onSelectTab);

  // Ön planda gelen bildirim: göstermezsek kullanıcı hiçbir şey görmez.
  FirebaseMessaging.onMessage.listen(_showForeground);

  try {
    final ilk = await FirebaseMessaging.instance.getInitialMessage();
    if (ilk != null) onSelectTab(tabForNotification(ilk.data));
  } catch (e) {
    debugPrint('Açılış bildirimi okunamadı: $e');
  }

  FirebaseMessaging.onMessageOpenedApp.listen((mesaj) {
    onSelectTab(tabForNotification(mesaj.data));
  });
}

/// Bildirim altyapısını oturuma bağlar.
///
/// [billingIdentityProvider] ile aynı desen: izlenmezse hiç kurulmaz.
/// Oturum açıldığında (ve dil değiştiğinde) cihaz bilgisi sunucuya yazılır,
/// token yenilemesi dinlenir ve bildirime dokunma yönlendirmesi kurulur.
final notificationSyncProvider = Provider<void>((ref) {
  var dinleyiciKuruldu = false;

  ref.listen<AsyncValue<User?>>(authStateProvider, (previous, next) {
    final user = next.value;
    if (user == null) return;

    // Dil profile yazılır: bildirim sunucuda üretildiği için istemcinin
    // Accept-Language başlığı oraya ulaşmıyor.
    final dil = ref.read(localeProvider)?.languageCode ??
        WidgetsBinding.instance.platformDispatcher.locale.languageCode;
    syncNotificationContext(languageCode: dil);

    if (dinleyiciKuruldu) return;
    dinleyiciKuruldu = true;
    listenForTokenRefresh();
    handleNotificationTaps((tab) {
      ref.read(shellTabProvider.notifier).state = tab;
    });
  }, fireImmediately: true);

  // Dil değişimini de yansıt: kullanıcı İngilizceye geçtiyse bildirimler de
  // İngilizce gelmeli.
  ref.listen<Locale?>(localeProvider, (previous, next) {
    if (FirebaseAuth.instance.currentUser == null) return;
    syncNotificationContext(
      languageCode: next?.languageCode ??
          WidgetsBinding.instance.platformDispatcher.locale.languageCode,
    );
  });
});
