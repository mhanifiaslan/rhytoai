import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_tr.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('tr'),
  ];

  /// No description provided for @appTagline.
  ///
  /// In tr, this message translates to:
  /// **'Kadim bilgelik, hassas gökyüzü hesabıyla buluşur.\nHaritan çizilir, yolun aydınlanır. ✨'**
  String get appTagline;

  /// No description provided for @signInWithGoogle.
  ///
  /// In tr, this message translates to:
  /// **'Google ile giriş'**
  String get signInWithGoogle;

  /// No description provided for @orDivider.
  ///
  /// In tr, this message translates to:
  /// **'ya da'**
  String get orDivider;

  /// No description provided for @signIn.
  ///
  /// In tr, this message translates to:
  /// **'Giriş yap'**
  String get signIn;

  /// No description provided for @signUp.
  ///
  /// In tr, this message translates to:
  /// **'Üye ol'**
  String get signUp;

  /// No description provided for @email.
  ///
  /// In tr, this message translates to:
  /// **'E-posta'**
  String get email;

  /// No description provided for @password.
  ///
  /// In tr, this message translates to:
  /// **'Şifre'**
  String get password;

  /// No description provided for @forgotPassword.
  ///
  /// In tr, this message translates to:
  /// **'Şifremi unuttum'**
  String get forgotPassword;

  /// No description provided for @tabSky.
  ///
  /// In tr, this message translates to:
  /// **'Gökyüzü'**
  String get tabSky;

  /// No description provided for @tabAtlas.
  ///
  /// In tr, this message translates to:
  /// **'Atlas'**
  String get tabAtlas;

  /// No description provided for @tabFriends.
  ///
  /// In tr, this message translates to:
  /// **'Arkadaşlar'**
  String get tabFriends;

  /// No description provided for @tabProfile.
  ///
  /// In tr, this message translates to:
  /// **'Profil'**
  String get tabProfile;

  /// No description provided for @greetingMorning.
  ///
  /// In tr, this message translates to:
  /// **'Günaydın'**
  String get greetingMorning;

  /// No description provided for @greetingDay.
  ///
  /// In tr, this message translates to:
  /// **'İyi günler'**
  String get greetingDay;

  /// No description provided for @greetingEvening.
  ///
  /// In tr, this message translates to:
  /// **'İyi akşamlar'**
  String get greetingEvening;

  /// No description provided for @greetingNight.
  ///
  /// In tr, this message translates to:
  /// **'İyi geceler'**
  String get greetingNight;

  /// No description provided for @todaysInsight.
  ///
  /// In tr, this message translates to:
  /// **'Bugünün İçgörüsü'**
  String get todaysInsight;

  /// No description provided for @signToday.
  ///
  /// In tr, this message translates to:
  /// **'{sign} · bugün'**
  String signToday(String sign);

  /// No description provided for @oracleTools.
  ///
  /// In tr, this message translates to:
  /// **'Kehanet Araçları'**
  String get oracleTools;

  /// No description provided for @skyNow.
  ///
  /// In tr, this message translates to:
  /// **'Şu An Gökyüzünde'**
  String get skyNow;

  /// No description provided for @iChing.
  ///
  /// In tr, this message translates to:
  /// **'I Ching'**
  String get iChing;

  /// No description provided for @iChingSubtitle.
  ///
  /// In tr, this message translates to:
  /// **'Değişimler Kitabı'**
  String get iChingSubtitle;

  /// No description provided for @baZi.
  ///
  /// In tr, this message translates to:
  /// **'BaZi'**
  String get baZi;

  /// No description provided for @baZiSubtitle.
  ///
  /// In tr, this message translates to:
  /// **'Dört Sütun'**
  String get baZiSubtitle;

  /// No description provided for @personalReadingLocked.
  ///
  /// In tr, this message translates to:
  /// **'Sana özel günlük okuma'**
  String get personalReadingLocked;

  /// No description provided for @personalReadingLockedBody.
  ///
  /// In tr, this message translates to:
  /// **'Rytho+ ile yorumlar senin haritanla üretilir.'**
  String get personalReadingLockedBody;

  /// No description provided for @personalReadingLockedBodyWithSign.
  ///
  /// In tr, this message translates to:
  /// **'Yukarısı tüm {sign} burçları için. Rytho+ ile bu yorum senin Ay ve yükselenini de hesaba katar.'**
  String personalReadingLockedBodyWithSign(String sign);

  /// No description provided for @personalReadingTitle.
  ///
  /// In tr, this message translates to:
  /// **'Sana özel'**
  String get personalReadingTitle;

  /// No description provided for @natalLockedTitle.
  ///
  /// In tr, this message translates to:
  /// **'Doğum haritası analizi'**
  String get natalLockedTitle;

  /// No description provided for @natalLockedBody.
  ///
  /// In tr, this message translates to:
  /// **'Gezegen konumların, evlerin ve açıların derin yorumu Rytho+ ile açılır.'**
  String get natalLockedBody;

  /// No description provided for @baziLockedTitle.
  ///
  /// In tr, this message translates to:
  /// **'BaZi — Dört Sütun'**
  String get baziLockedTitle;

  /// No description provided for @baziLockedBody.
  ///
  /// In tr, this message translates to:
  /// **'Day Master, On Tanrı ve şans sütunları analizi Rytho+ ile açılır.'**
  String get baziLockedBody;

  /// No description provided for @friendsTitle.
  ///
  /// In tr, this message translates to:
  /// **'Arkadaşlar'**
  String get friendsTitle;

  /// No description provided for @addFriend.
  ///
  /// In tr, this message translates to:
  /// **'Arkadaş ekle'**
  String get addFriend;

  /// No description provided for @usernameLabel.
  ///
  /// In tr, this message translates to:
  /// **'KULLANICI ADI'**
  String get usernameLabel;

  /// No description provided for @usernameHeadline.
  ///
  /// In tr, this message translates to:
  /// **'Arkadaşların seni bulabilsin'**
  String get usernameHeadline;

  /// No description provided for @usernameBody.
  ///
  /// In tr, this message translates to:
  /// **'Bir kullanıcı adı seç. Rehberine erişmiyoruz; arkadaş eklemek yalnızca kullanıcı adı veya davet bağlantısıyla olur.'**
  String get usernameBody;

  /// No description provided for @usernameHint.
  ///
  /// In tr, this message translates to:
  /// **'kullaniciadi'**
  String get usernameHint;

  /// No description provided for @claimUsername.
  ///
  /// In tr, this message translates to:
  /// **'Kullanıcı adını al'**
  String get claimUsername;

  /// No description provided for @usernameInvalid.
  ///
  /// In tr, this message translates to:
  /// **'3-20 karakter; yalnızca küçük harf, rakam ve alt çizgi.'**
  String get usernameInvalid;

  /// No description provided for @usernameEmpty.
  ///
  /// In tr, this message translates to:
  /// **'Kullanıcı adı boş olamaz.'**
  String get usernameEmpty;

  /// No description provided for @usernameTaken.
  ///
  /// In tr, this message translates to:
  /// **'Bu kullanıcı adı alınmış, başka bir tane dene.'**
  String get usernameTaken;

  /// No description provided for @youLabel.
  ///
  /// In tr, this message translates to:
  /// **'SEN'**
  String get youLabel;

  /// No description provided for @streakVisibleOn.
  ///
  /// In tr, this message translates to:
  /// **'Arkadaşların serini ve bugün okuyup okumadığını görebilir.'**
  String get streakVisibleOn;

  /// No description provided for @streakVisibleOff.
  ///
  /// In tr, this message translates to:
  /// **'Serin arkadaşlarından gizli.'**
  String get streakVisibleOff;

  /// No description provided for @copyInviteLink.
  ///
  /// In tr, this message translates to:
  /// **'Davet bağlantısını kopyala'**
  String get copyInviteLink;

  /// No description provided for @inviteLinkCopied.
  ///
  /// In tr, this message translates to:
  /// **'Davet bağlantısı kopyalandı.'**
  String get inviteLinkCopied;

  /// No description provided for @shareInviteInstead.
  ///
  /// In tr, this message translates to:
  /// **'Bunun yerine davet bağlantımı paylaş'**
  String get shareInviteInstead;

  /// No description provided for @sendInvite.
  ///
  /// In tr, this message translates to:
  /// **'Davet gönder'**
  String get sendInvite;

  /// No description provided for @inviteSent.
  ///
  /// In tr, this message translates to:
  /// **'@{username} kullanıcısına davet gönderildi.'**
  String inviteSent(String username);

  /// No description provided for @userNotFound.
  ///
  /// In tr, this message translates to:
  /// **'@{username} bulunamadı.'**
  String userNotFound(String username);

  /// No description provided for @cannotAddSelf.
  ///
  /// In tr, this message translates to:
  /// **'Kendini ekleyemezsin.'**
  String get cannotAddSelf;

  /// No description provided for @inboxLabel.
  ///
  /// In tr, this message translates to:
  /// **'SANA GELENLER'**
  String get inboxLabel;

  /// No description provided for @noFriendsYet.
  ///
  /// In tr, this message translates to:
  /// **'Henüz kimse yok'**
  String get noFriendsYet;

  /// No description provided for @noFriendsBody.
  ///
  /// In tr, this message translates to:
  /// **'Bir arkadaşını kullanıcı adıyla ekle; serilerinizi görün ve her gün aranızdaki dinamiği okuyun.'**
  String get noFriendsBody;

  /// No description provided for @incomingRequests.
  ///
  /// In tr, this message translates to:
  /// **'Gelen davetler'**
  String get incomingRequests;

  /// No description provided for @yourFriends.
  ///
  /// In tr, this message translates to:
  /// **'Arkadaşların'**
  String get yourFriends;

  /// No description provided for @pendingInvites.
  ///
  /// In tr, this message translates to:
  /// **'Yanıt bekleyen davetlerin'**
  String get pendingInvites;

  /// No description provided for @accept.
  ///
  /// In tr, this message translates to:
  /// **'Kabul et'**
  String get accept;

  /// No description provided for @ignore.
  ///
  /// In tr, this message translates to:
  /// **'Yoksay'**
  String get ignore;

  /// No description provided for @pending.
  ///
  /// In tr, this message translates to:
  /// **'Bekliyor'**
  String get pending;

  /// No description provided for @withdrawInvite.
  ///
  /// In tr, this message translates to:
  /// **'Daveti geri al'**
  String get withdrawInvite;

  /// No description provided for @readToday.
  ///
  /// In tr, this message translates to:
  /// **'Bugün okumasını yaptı'**
  String get readToday;

  /// No description provided for @notReadToday.
  ///
  /// In tr, this message translates to:
  /// **'Bugün henüz okumadı'**
  String get notReadToday;

  /// No description provided for @streakHidden.
  ///
  /// In tr, this message translates to:
  /// **'Serisi gizli'**
  String get streakHidden;

  /// No description provided for @friendLabel.
  ///
  /// In tr, this message translates to:
  /// **'ARKADAŞIN'**
  String get friendLabel;

  /// No description provided for @streakHiddenByFriend.
  ///
  /// In tr, this message translates to:
  /// **'Serisini gizli tutuyor'**
  String get streakHiddenByFriend;

  /// No description provided for @readTodayDone.
  ///
  /// In tr, this message translates to:
  /// **'Bugünkü okumasını yaptı'**
  String get readTodayDone;

  /// No description provided for @dyadLabel.
  ///
  /// In tr, this message translates to:
  /// **'BUGÜN ARANIZDA'**
  String get dyadLabel;

  /// No description provided for @dyadDisclaimer.
  ///
  /// In tr, this message translates to:
  /// **'Bu okuma yalnızca bugün için geçerlidir ve yarın değişir. Kalıcı bir uyum puanı vermiyoruz.'**
  String get dyadDisclaimer;

  /// No description provided for @dyadFailed.
  ///
  /// In tr, this message translates to:
  /// **'Okuma alınamadı.'**
  String get dyadFailed;

  /// No description provided for @sendReaction.
  ///
  /// In tr, this message translates to:
  /// **'Bir tepki gönder'**
  String get sendReaction;

  /// No description provided for @sendReactionBody.
  ///
  /// In tr, this message translates to:
  /// **'Hazır tepkilerden birini seç — mesaj yazma yok, sadece küçük bir selam.'**
  String get sendReactionBody;

  /// No description provided for @reactionSent.
  ///
  /// In tr, this message translates to:
  /// **'{emoji} gönderildi.'**
  String reactionSent(String emoji);

  /// No description provided for @removeFriend.
  ///
  /// In tr, this message translates to:
  /// **'Arkadaşlıktan çıkar'**
  String get removeFriend;

  /// No description provided for @blockUser.
  ///
  /// In tr, this message translates to:
  /// **'Engelle'**
  String get blockUser;

  /// No description provided for @reportUser.
  ///
  /// In tr, this message translates to:
  /// **'Şikayet et'**
  String get reportUser;

  /// No description provided for @reactionStreak.
  ///
  /// In tr, this message translates to:
  /// **'Seri devam'**
  String get reactionStreak;

  /// No description provided for @reactionThinkingOfYou.
  ///
  /// In tr, this message translates to:
  /// **'Seni düşündüm'**
  String get reactionThinkingOfYou;

  /// No description provided for @reactionShine.
  ///
  /// In tr, this message translates to:
  /// **'Parlıyorsun'**
  String get reactionShine;

  /// No description provided for @reactionKeepGoing.
  ///
  /// In tr, this message translates to:
  /// **'Devam et'**
  String get reactionKeepGoing;

  /// No description provided for @reactionCongrats.
  ///
  /// In tr, this message translates to:
  /// **'Tebrikler'**
  String get reactionCongrats;

  /// No description provided for @reactionSameFrequency.
  ///
  /// In tr, this message translates to:
  /// **'Aynı frekans'**
  String get reactionSameFrequency;

  /// No description provided for @reactionGoodNight.
  ///
  /// In tr, this message translates to:
  /// **'İyi geceler'**
  String get reactionGoodNight;

  /// No description provided for @reactionCheckToday.
  ///
  /// In tr, this message translates to:
  /// **'Bugüne bak'**
  String get reactionCheckToday;

  /// No description provided for @paywallTitle.
  ///
  /// In tr, this message translates to:
  /// **'Rytho+'**
  String get paywallTitle;

  /// No description provided for @paywallHeadline.
  ///
  /// In tr, this message translates to:
  /// **'Yıldızlar herkese aynı,\nsen değilsin.'**
  String get paywallHeadline;

  /// No description provided for @paywallBody.
  ///
  /// In tr, this message translates to:
  /// **'Ücretsiz katmanda günlük burç yorumun ve gerçek gökyüzü verisi her zaman açık kalır. Rytho+ ise yorumları senin haritanla üretir.'**
  String get paywallBody;

  /// No description provided for @paywallContinue.
  ///
  /// In tr, this message translates to:
  /// **'Rytho+ ile devam et'**
  String get paywallContinue;

  /// No description provided for @paywallChoosePlan.
  ///
  /// In tr, this message translates to:
  /// **'Paket seç'**
  String get paywallChoosePlan;

  /// No description provided for @restorePurchases.
  ///
  /// In tr, this message translates to:
  /// **'Satın alımları geri yükle'**
  String get restorePurchases;

  /// No description provided for @noActiveSubscription.
  ///
  /// In tr, this message translates to:
  /// **'Geri yüklenecek aktif bir abonelik bulunamadı.'**
  String get noActiveSubscription;

  /// No description provided for @purchaseFailed.
  ///
  /// In tr, this message translates to:
  /// **'Satın alma tamamlanamadı.'**
  String get purchaseFailed;

  /// No description provided for @billingUnavailable.
  ///
  /// In tr, this message translates to:
  /// **'Satın alma şu an kullanılamıyor'**
  String get billingUnavailable;

  /// No description provided for @billingNoPackages.
  ///
  /// In tr, this message translates to:
  /// **'Mağazada tanımlı paket bulunamadı.'**
  String get billingNoPackages;

  /// No description provided for @billingNotConfigured.
  ///
  /// In tr, this message translates to:
  /// **'Bu derlemede abonelik anahtarları tanımlı değil.'**
  String get billingNotConfigured;

  /// No description provided for @planWeekly.
  ///
  /// In tr, this message translates to:
  /// **'Haftalık'**
  String get planWeekly;

  /// No description provided for @planMonthly.
  ///
  /// In tr, this message translates to:
  /// **'Aylık'**
  String get planMonthly;

  /// No description provided for @planAnnual.
  ///
  /// In tr, this message translates to:
  /// **'Yıllık'**
  String get planAnnual;

  /// No description provided for @bestValue.
  ///
  /// In tr, this message translates to:
  /// **'EN İYİ DEĞER'**
  String get bestValue;

  /// No description provided for @trialThenPrice.
  ///
  /// In tr, this message translates to:
  /// **'{count} {unit} ücretsiz, sonra {price}'**
  String trialThenPrice(int count, String unit, String price);

  /// No description provided for @unitDay.
  ///
  /// In tr, this message translates to:
  /// **'gün'**
  String get unitDay;

  /// No description provided for @unitWeek.
  ///
  /// In tr, this message translates to:
  /// **'hafta'**
  String get unitWeek;

  /// No description provided for @unitMonth.
  ///
  /// In tr, this message translates to:
  /// **'ay'**
  String get unitMonth;

  /// No description provided for @unitYear.
  ///
  /// In tr, this message translates to:
  /// **'yıl'**
  String get unitYear;

  /// No description provided for @subscriptionTerms.
  ///
  /// In tr, this message translates to:
  /// **'Abonelik, dönem bitiminden en az 24 saat önce iptal edilmezse otomatik yenilenir. Deneme süresi varsa, süre dolmadan iptal edersen ücret alınmaz. İptali cihazının mağaza hesabı ayarlarından yapabilirsin.'**
  String get subscriptionTerms;

  /// No description provided for @benefitDailyTitle.
  ///
  /// In tr, this message translates to:
  /// **'Kişiye özel günlük okuma'**
  String get benefitDailyTitle;

  /// No description provided for @benefitDailyBody.
  ///
  /// In tr, this message translates to:
  /// **'Natal haritan bugünün gökyüzüyle çarpışır — genel burç yorumu değil.'**
  String get benefitDailyBody;

  /// No description provided for @benefitNatalTitle.
  ///
  /// In tr, this message translates to:
  /// **'Derin doğum haritası raporu'**
  String get benefitNatalTitle;

  /// No description provided for @benefitNatalBody.
  ///
  /// In tr, this message translates to:
  /// **'Gezegenler, evler ve açılar; tek seferlik yüzeysel özet değil.'**
  String get benefitNatalBody;

  /// No description provided for @benefitDyadTitle.
  ///
  /// In tr, this message translates to:
  /// **'Arkadaşlarınla günlük ikili dinamik'**
  String get benefitDyadTitle;

  /// No description provided for @benefitDyadBody.
  ///
  /// In tr, this message translates to:
  /// **'Her gün yenilenen ortak okuma. Kalıcı uyum puanı yok.'**
  String get benefitDyadBody;

  /// No description provided for @benefitChatTitle.
  ///
  /// In tr, this message translates to:
  /// **'Sınırsız sohbet'**
  String get benefitChatTitle;

  /// No description provided for @benefitChatBody.
  ///
  /// In tr, this message translates to:
  /// **'Rytho seni tanıdıkça konuşma derinleşir.'**
  String get benefitChatBody;

  /// No description provided for @benefitBaziTitle.
  ///
  /// In tr, this message translates to:
  /// **'BaZi ve sinastri'**
  String get benefitBaziTitle;

  /// No description provided for @benefitBaziBody.
  ///
  /// In tr, this message translates to:
  /// **'Dört Sütun analizi ve ikili harita karşılaştırması.'**
  String get benefitBaziBody;

  /// No description provided for @profileTitle.
  ///
  /// In tr, this message translates to:
  /// **'Sicil'**
  String get profileTitle;

  /// No description provided for @settings.
  ///
  /// In tr, this message translates to:
  /// **'Ayarlar'**
  String get settings;

  /// No description provided for @sounds.
  ///
  /// In tr, this message translates to:
  /// **'Sesler'**
  String get sounds;

  /// No description provided for @privacy.
  ///
  /// In tr, this message translates to:
  /// **'Gizlilik'**
  String get privacy;

  /// No description provided for @streakVisibleSetting.
  ///
  /// In tr, this message translates to:
  /// **'Serimi arkadaşlarım görsün'**
  String get streakVisibleSetting;

  /// No description provided for @streakVisibleSettingBody.
  ///
  /// In tr, this message translates to:
  /// **'Kapalıyken serin ve bugün okuyup okumadığın paylaşılmaz.'**
  String get streakVisibleSettingBody;

  /// No description provided for @language.
  ///
  /// In tr, this message translates to:
  /// **'Dil'**
  String get language;

  /// No description provided for @languageSystem.
  ///
  /// In tr, this message translates to:
  /// **'Sistem dili'**
  String get languageSystem;

  /// No description provided for @languageTurkish.
  ///
  /// In tr, this message translates to:
  /// **'Türkçe'**
  String get languageTurkish;

  /// No description provided for @languageEnglish.
  ///
  /// In tr, this message translates to:
  /// **'English'**
  String get languageEnglish;

  /// No description provided for @about.
  ///
  /// In tr, this message translates to:
  /// **'Hakkında'**
  String get about;

  /// No description provided for @aboutBody.
  ///
  /// In tr, this message translates to:
  /// **'Rytho; Batı astrolojisi, BaZi ve I Ching geleneklerini hassas efemeris hesabıyla birleştirir. Yorumlar içgörü amaçlıdır; tıbbi, hukuki veya finansal tavsiye değildir.'**
  String get aboutBody;

  /// No description provided for @ephemerisCredit.
  ///
  /// In tr, this message translates to:
  /// **'Efemeris: Swiss Ephemeris © Astrodienst AG'**
  String get ephemerisCredit;

  /// No description provided for @privacyPolicy.
  ///
  /// In tr, this message translates to:
  /// **'Gizlilik Politikası'**
  String get privacyPolicy;

  /// No description provided for @termsOfUse.
  ///
  /// In tr, this message translates to:
  /// **'Kullanım Şartları'**
  String get termsOfUse;

  /// No description provided for @signOut.
  ///
  /// In tr, this message translates to:
  /// **'Oturumu kapat'**
  String get signOut;

  /// No description provided for @dailyStreak.
  ///
  /// In tr, this message translates to:
  /// **'Günlük Seri'**
  String get dailyStreak;

  /// No description provided for @streakDays.
  ///
  /// In tr, this message translates to:
  /// **'{count} gün'**
  String streakDays(int count);

  /// No description provided for @streakBody.
  ///
  /// In tr, this message translates to:
  /// **'Günlük okumayı her gün aç, serin büyüsün.'**
  String get streakBody;

  /// No description provided for @birthRecord.
  ///
  /// In tr, this message translates to:
  /// **'Doğum Kaydı'**
  String get birthRecord;

  /// No description provided for @birthDate.
  ///
  /// In tr, this message translates to:
  /// **'Tarih'**
  String get birthDate;

  /// No description provided for @birthTime.
  ///
  /// In tr, this message translates to:
  /// **'Saat'**
  String get birthTime;

  /// No description provided for @birthCity.
  ///
  /// In tr, this message translates to:
  /// **'Şehir'**
  String get birthCity;

  /// No description provided for @retry.
  ///
  /// In tr, this message translates to:
  /// **'Tekrar dene'**
  String get retry;

  /// No description provided for @errorGeneric.
  ///
  /// In tr, this message translates to:
  /// **'Beklenmeyen bir sorun oluştu. Lütfen biraz sonra tekrar dene.'**
  String get errorGeneric;

  /// No description provided for @errorConnection.
  ///
  /// In tr, this message translates to:
  /// **'Bağlantı kurulamadı. İnternetini kontrol edip tekrar dene.'**
  String get errorConnection;

  /// No description provided for @errorSkyUnavailable.
  ///
  /// In tr, this message translates to:
  /// **'Gökyüzüne şu an ulaşılamıyor.'**
  String get errorSkyUnavailable;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'tr'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'tr':
      return AppLocalizationsTr();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
