// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Turkish (`tr`).
class AppLocalizationsTr extends AppLocalizations {
  AppLocalizationsTr([String locale = 'tr']) : super(locale);

  @override
  String get appTagline =>
      'Kadim bilgelik, hassas gökyüzü hesabıyla buluşur.\nHaritan çizilir, yolun aydınlanır. ✨';

  @override
  String get signInWithGoogle => 'Google ile giriş';

  @override
  String get orDivider => 'ya da';

  @override
  String get signIn => 'Giriş yap';

  @override
  String get signUp => 'Üye ol';

  @override
  String get email => 'E-posta';

  @override
  String get password => 'Şifre';

  @override
  String get forgotPassword => 'Şifremi unuttum';

  @override
  String get tabSky => 'Gökyüzü';

  @override
  String get tabAtlas => 'Atlas';

  @override
  String get tabFriends => 'Arkadaşlar';

  @override
  String get tabProfile => 'Profil';

  @override
  String get greetingMorning => 'Günaydın';

  @override
  String get greetingDay => 'İyi günler';

  @override
  String get greetingEvening => 'İyi akşamlar';

  @override
  String get greetingNight => 'İyi geceler';

  @override
  String get todaysInsight => 'Bugünün İçgörüsü';

  @override
  String signToday(String sign) {
    return '$sign · bugün';
  }

  @override
  String get oracleTools => 'Kehanet Araçları';

  @override
  String get skyNow => 'Şu An Gökyüzünde';

  @override
  String get iChing => 'I Ching';

  @override
  String get iChingSubtitle => 'Değişimler Kitabı';

  @override
  String get baZi => 'BaZi';

  @override
  String get baZiSubtitle => 'Dört Sütun';

  @override
  String get personalReadingLocked => 'Sana özel günlük okuma';

  @override
  String get personalReadingLockedBody =>
      'Rytho+ ile yorumlar senin haritanla üretilir.';

  @override
  String personalReadingLockedBodyWithSign(String sign) {
    return 'Yukarısı tüm $sign burçları için. Rytho+ ile bu yorum senin Ay ve yükselenini de hesaba katar.';
  }

  @override
  String get personalReadingTitle => 'Sana özel';

  @override
  String get natalLockedTitle => 'Doğum haritası analizi';

  @override
  String get natalLockedBody =>
      'Gezegen konumların, evlerin ve açıların derin yorumu Rytho+ ile açılır.';

  @override
  String get baziLockedTitle => 'BaZi — Dört Sütun';

  @override
  String get baziLockedBody =>
      'Day Master, On Tanrı ve şans sütunları analizi Rytho+ ile açılır.';

  @override
  String get friendsTitle => 'Arkadaşlar';

  @override
  String get addFriend => 'Arkadaş ekle';

  @override
  String get usernameLabel => 'KULLANICI ADI';

  @override
  String get usernameHeadline => 'Arkadaşların seni bulabilsin';

  @override
  String get usernameBody =>
      'Bir kullanıcı adı seç. Rehberine erişmiyoruz; arkadaş eklemek yalnızca kullanıcı adı veya davet bağlantısıyla olur.';

  @override
  String get usernameHint => 'kullaniciadi';

  @override
  String get claimUsername => 'Kullanıcı adını al';

  @override
  String get usernameInvalid =>
      '3-20 karakter; yalnızca küçük harf, rakam ve alt çizgi.';

  @override
  String get usernameEmpty => 'Kullanıcı adı boş olamaz.';

  @override
  String get usernameTaken => 'Bu kullanıcı adı alınmış, başka bir tane dene.';

  @override
  String get youLabel => 'SEN';

  @override
  String get streakVisibleOn =>
      'Arkadaşların serini ve bugün okuyup okumadığını görebilir.';

  @override
  String get streakVisibleOff => 'Serin arkadaşlarından gizli.';

  @override
  String get copyInviteLink => 'Davet bağlantısını kopyala';

  @override
  String get inviteLinkCopied => 'Davet bağlantısı kopyalandı.';

  @override
  String get shareInviteInstead => 'Bunun yerine davet bağlantımı paylaş';

  @override
  String get sendInvite => 'Davet gönder';

  @override
  String inviteSent(String username) {
    return '@$username kullanıcısına davet gönderildi.';
  }

  @override
  String userNotFound(String username) {
    return '@$username bulunamadı.';
  }

  @override
  String get cannotAddSelf => 'Kendini ekleyemezsin.';

  @override
  String get inboxLabel => 'SANA GELENLER';

  @override
  String get noFriendsYet => 'Henüz kimse yok';

  @override
  String get noFriendsBody =>
      'Bir arkadaşını kullanıcı adıyla ekle; serilerinizi görün ve her gün aranızdaki dinamiği okuyun.';

  @override
  String get incomingRequests => 'Gelen davetler';

  @override
  String get yourFriends => 'Arkadaşların';

  @override
  String get pendingInvites => 'Yanıt bekleyen davetlerin';

  @override
  String get accept => 'Kabul et';

  @override
  String get ignore => 'Yoksay';

  @override
  String get pending => 'Bekliyor';

  @override
  String get withdrawInvite => 'Daveti geri al';

  @override
  String get readToday => 'Bugün okumasını yaptı';

  @override
  String get notReadToday => 'Bugün henüz okumadı';

  @override
  String get streakHidden => 'Serisi gizli';

  @override
  String get friendLabel => 'ARKADAŞIN';

  @override
  String get streakHiddenByFriend => 'Serisini gizli tutuyor';

  @override
  String get readTodayDone => 'Bugünkü okumasını yaptı';

  @override
  String get dyadLabel => 'BUGÜN ARANIZDA';

  @override
  String get dyadDisclaimer =>
      'Bu okuma yalnızca bugün için geçerlidir ve yarın değişir. Kalıcı bir uyum puanı vermiyoruz.';

  @override
  String get dyadFailed => 'Okuma alınamadı.';

  @override
  String get sendReaction => 'Bir tepki gönder';

  @override
  String get sendReactionBody =>
      'Hazır tepkilerden birini seç — mesaj yazma yok, sadece küçük bir selam.';

  @override
  String reactionSent(String emoji) {
    return '$emoji gönderildi.';
  }

  @override
  String get removeFriend => 'Arkadaşlıktan çıkar';

  @override
  String get blockUser => 'Engelle';

  @override
  String get reportUser => 'Şikayet et';

  @override
  String get reactionStreak => 'Seri devam';

  @override
  String get reactionThinkingOfYou => 'Seni düşündüm';

  @override
  String get reactionShine => 'Parlıyorsun';

  @override
  String get reactionKeepGoing => 'Devam et';

  @override
  String get reactionCongrats => 'Tebrikler';

  @override
  String get reactionSameFrequency => 'Aynı frekans';

  @override
  String get reactionGoodNight => 'İyi geceler';

  @override
  String get reactionCheckToday => 'Bugüne bak';

  @override
  String get paywallTitle => 'Rytho+';

  @override
  String get paywallHeadline => 'Yıldızlar herkese aynı,\nsen değilsin.';

  @override
  String get paywallBody =>
      'Ücretsiz katmanda günlük burç yorumun ve gerçek gökyüzü verisi her zaman açık kalır. Rytho+ ise yorumları senin haritanla üretir.';

  @override
  String get paywallContinue => 'Rytho+ ile devam et';

  @override
  String get paywallChoosePlan => 'Paket seç';

  @override
  String get restorePurchases => 'Satın alımları geri yükle';

  @override
  String get noActiveSubscription =>
      'Geri yüklenecek aktif bir abonelik bulunamadı.';

  @override
  String get purchaseFailed => 'Satın alma tamamlanamadı.';

  @override
  String get billingUnavailable => 'Satın alma şu an kullanılamıyor';

  @override
  String get billingNoPackages => 'Mağazada tanımlı paket bulunamadı.';

  @override
  String get billingNotConfigured =>
      'Bu derlemede abonelik anahtarları tanımlı değil.';

  @override
  String get planWeekly => 'Haftalık';

  @override
  String get planMonthly => 'Aylık';

  @override
  String get planAnnual => 'Yıllık';

  @override
  String get bestValue => 'EN İYİ DEĞER';

  @override
  String trialThenPrice(int count, String unit, String price) {
    return '$count $unit ücretsiz, sonra $price';
  }

  @override
  String get unitDay => 'gün';

  @override
  String get unitWeek => 'hafta';

  @override
  String get unitMonth => 'ay';

  @override
  String get unitYear => 'yıl';

  @override
  String get subscriptionTerms =>
      'Abonelik, dönem bitiminden en az 24 saat önce iptal edilmezse otomatik yenilenir. Deneme süresi varsa, süre dolmadan iptal edersen ücret alınmaz. İptali cihazının mağaza hesabı ayarlarından yapabilirsin.';

  @override
  String get benefitDailyTitle => 'Kişiye özel günlük okuma';

  @override
  String get benefitDailyBody =>
      'Natal haritan bugünün gökyüzüyle çarpışır — genel burç yorumu değil.';

  @override
  String get benefitNatalTitle => 'Derin doğum haritası raporu';

  @override
  String get benefitNatalBody =>
      'Gezegenler, evler ve açılar; tek seferlik yüzeysel özet değil.';

  @override
  String get benefitDyadTitle => 'Arkadaşlarınla günlük ikili dinamik';

  @override
  String get benefitDyadBody =>
      'Her gün yenilenen ortak okuma. Kalıcı uyum puanı yok.';

  @override
  String get benefitChatTitle => 'Sınırsız sohbet';

  @override
  String get benefitChatBody => 'Rytho seni tanıdıkça konuşma derinleşir.';

  @override
  String get benefitBaziTitle => 'BaZi ve sinastri';

  @override
  String get benefitBaziBody =>
      'Dört Sütun analizi ve ikili harita karşılaştırması.';

  @override
  String get profileTitle => 'Sicil';

  @override
  String get settings => 'Ayarlar';

  @override
  String get sounds => 'Sesler';

  @override
  String get privacy => 'Gizlilik';

  @override
  String get streakVisibleSetting => 'Serimi arkadaşlarım görsün';

  @override
  String get streakVisibleSettingBody =>
      'Kapalıyken serin ve bugün okuyup okumadığın paylaşılmaz.';

  @override
  String get language => 'Dil';

  @override
  String get languageSystem => 'Sistem dili';

  @override
  String get languageTurkish => 'Türkçe';

  @override
  String get languageEnglish => 'English';

  @override
  String get about => 'Hakkında';

  @override
  String get aboutBody =>
      'Rytho; Batı astrolojisi, BaZi ve I Ching geleneklerini hassas efemeris hesabıyla birleştirir. Yorumlar içgörü amaçlıdır; tıbbi, hukuki veya finansal tavsiye değildir.';

  @override
  String get ephemerisCredit => 'Efemeris: Swiss Ephemeris © Astrodienst AG';

  @override
  String get privacyPolicy => 'Gizlilik Politikası';

  @override
  String get termsOfUse => 'Kullanım Şartları';

  @override
  String get signOut => 'Oturumu kapat';

  @override
  String get dailyStreak => 'Günlük Seri';

  @override
  String streakDays(int count) {
    return '$count gün';
  }

  @override
  String get streakBody => 'Günlük okumayı her gün aç, serin büyüsün.';

  @override
  String get birthRecord => 'Doğum Kaydı';

  @override
  String get birthDate => 'Tarih';

  @override
  String get birthTime => 'Saat';

  @override
  String get birthCity => 'Şehir';

  @override
  String get retry => 'Tekrar dene';

  @override
  String get errorGeneric =>
      'Beklenmeyen bir sorun oluştu. Lütfen biraz sonra tekrar dene.';

  @override
  String get errorConnection =>
      'Bağlantı kurulamadı. İnternetini kontrol edip tekrar dene.';

  @override
  String get errorSkyUnavailable => 'Gökyüzüne şu an ulaşılamıyor.';

  @override
  String get promoTitle => 'Yıldızların ötesine geç ✨';

  @override
  String get promoBody =>
      'Doğum haritanın derin analizini ve kişilik raporunu keşfet.';

  @override
  String get promoAction => 'Keşfet';
}
