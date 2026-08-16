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

  /// No description provided for @atlasYearChart.
  ///
  /// In tr, this message translates to:
  /// **'Doğum gününden doğum gününe'**
  String get atlasYearChart;

  /// No description provided for @atlasYearChartSubtitle.
  ///
  /// In tr, this message translates to:
  /// **'Yıl haritan (güneş dönüşü)'**
  String get atlasYearChartSubtitle;

  /// No description provided for @atlasInnerCalendar.
  ///
  /// In tr, this message translates to:
  /// **'Önündeki günler'**
  String get atlasInnerCalendar;

  /// No description provided for @atlasInnerCalendarSubtitle.
  ///
  /// In tr, this message translates to:
  /// **'İç takvim: transit + progresyon'**
  String get atlasInnerCalendarSubtitle;

  /// No description provided for @wizardWelcomeTitle.
  ///
  /// In tr, this message translates to:
  /// **'Yolculuk başlıyor'**
  String get wizardWelcomeTitle;

  /// No description provided for @wizardWelcomeBody.
  ///
  /// In tr, this message translates to:
  /// **'Birkaç adımda haritanı çizeceğiz: doğduğun an, gökyüzünün o anki hâli. Her adımda bir yıldız yanacak.'**
  String get wizardWelcomeBody;

  /// No description provided for @wizardConsentLabel.
  ///
  /// In tr, this message translates to:
  /// **'Kullanım Şartları\'nı ve Gizlilik Politikası\'nı okudum, kabul ediyorum. 13 yaşından büyüğüm.'**
  String get wizardConsentLabel;

  /// No description provided for @wizardDateTitle.
  ///
  /// In tr, this message translates to:
  /// **'Hangi gün doğdun?'**
  String get wizardDateTitle;

  /// No description provided for @wizardDateBody.
  ///
  /// In tr, this message translates to:
  /// **'Gökyüzü her gün başka bir düzendeydi — seninki hangisiydi?'**
  String get wizardDateBody;

  /// No description provided for @wizardTimeTitle.
  ///
  /// In tr, this message translates to:
  /// **'Saat kaçtı?'**
  String get wizardTimeTitle;

  /// No description provided for @wizardTimeBody.
  ///
  /// In tr, this message translates to:
  /// **'Doğum saati Yükselen\'ini ve evlerini belirler. Bilmiyorsan sorun değil — dürüstçe onsuz hesaplarız.'**
  String get wizardTimeBody;

  /// No description provided for @wizardTimeUnknownNote.
  ///
  /// In tr, this message translates to:
  /// **'Saatsiz doğumda Yükselen ve evler hesaplanmaz; okuma gezegen düzeyinde kalır.'**
  String get wizardTimeUnknownNote;

  /// No description provided for @wizardPlaceTitle.
  ///
  /// In tr, this message translates to:
  /// **'Nerede doğdun?'**
  String get wizardPlaceTitle;

  /// No description provided for @wizardPlaceBody.
  ///
  /// In tr, this message translates to:
  /// **'Konum, gökyüzünün sana göre nasıl durduğunu belirler — ufkun neresinde ne yükseliyordu?'**
  String get wizardPlaceBody;

  /// No description provided for @wizardGenderTitle.
  ///
  /// In tr, this message translates to:
  /// **'Son bir dokunuş'**
  String get wizardGenderTitle;

  /// No description provided for @wizardGenderBody.
  ///
  /// In tr, this message translates to:
  /// **'BaZi (Dört Sütun) hesabı şans dönemlerini cinsiyete göre yönlendirir.'**
  String get wizardGenderBody;

  /// No description provided for @wizardNext.
  ///
  /// In tr, this message translates to:
  /// **'Devam ✦'**
  String get wizardNext;

  /// No description provided for @wizardFinish.
  ///
  /// In tr, this message translates to:
  /// **'Haritamı çiz ✨'**
  String get wizardFinish;

  /// No description provided for @wizardLater.
  ///
  /// In tr, this message translates to:
  /// **'Sonra'**
  String get wizardLater;

  /// No description provided for @wizardPhoneTitle.
  ///
  /// In tr, this message translates to:
  /// **'Arkadaşlarını bul'**
  String get wizardPhoneTitle;

  /// No description provided for @wizardPhoneBody.
  ///
  /// In tr, this message translates to:
  /// **'Numaranı doğrularsan rehberindeki Rytho kullanıcılarını görebilirsin. Numara paylaşılmaz; yalnız eşleşme için kullanılır. İstersen bu adımı sonraya bırak.'**
  String get wizardPhoneBody;

  /// No description provided for @wizardPhoneVerify.
  ///
  /// In tr, this message translates to:
  /// **'Numaramı doğrula'**
  String get wizardPhoneVerify;

  /// No description provided for @wizardPhoneDone.
  ///
  /// In tr, this message translates to:
  /// **'Numaran doğrulandı'**
  String get wizardPhoneDone;

  /// No description provided for @wizardNotifyTitle.
  ///
  /// In tr, this message translates to:
  /// **'Günün okuması hazır olunca?'**
  String get wizardNotifyTitle;

  /// No description provided for @wizardNotifyBody.
  ///
  /// In tr, this message translates to:
  /// **'Günlük okuman ve serin için nazik bir hatırlatma gönderelim mi? Sessiz saatlerini Profil\'den ayarlayabilirsin.'**
  String get wizardNotifyBody;

  /// No description provided for @wizardNotifyAllow.
  ///
  /// In tr, this message translates to:
  /// **'Haber ver 🔔'**
  String get wizardNotifyAllow;

  /// No description provided for @countrySearchHint.
  ///
  /// In tr, this message translates to:
  /// **'Ülke ara…'**
  String get countrySearchHint;

  /// No description provided for @phoneSmsDisabled.
  ///
  /// In tr, this message translates to:
  /// **'SMS doğrulama şu an açık değil. Daha sonra tekrar dene.'**
  String get phoneSmsDisabled;

  /// No description provided for @phoneTemporarilyBlocked.
  ///
  /// In tr, this message translates to:
  /// **'Çok sayıda deneme yüzünden doğrulama geçici olarak durduruldu. Birkaç saat sonra tekrar dene.'**
  String get phoneTemporarilyBlocked;

  /// No description provided for @purchaseEntitlementMissing.
  ///
  /// In tr, this message translates to:
  /// **'Ödeme tamamlandı ama abonelik doğrulanamadı. \"Satın alımları geri yükle\"yi dene; sürerse bize yaz — ödemen güvende.'**
  String get purchaseEntitlementMissing;

  /// No description provided for @avatarEditTitle.
  ///
  /// In tr, this message translates to:
  /// **'Fotoğrafı yerleştir'**
  String get avatarEditTitle;

  /// No description provided for @avatarEditHint.
  ///
  /// In tr, this message translates to:
  /// **'Sürükleyerek konumlandır, iki parmakla yakınlaştır.'**
  String get avatarEditHint;

  /// No description provided for @avatarUpdated.
  ///
  /// In tr, this message translates to:
  /// **'Profil fotoğrafın güncellendi ✨'**
  String get avatarUpdated;

  /// No description provided for @avatarChangeFailed.
  ///
  /// In tr, this message translates to:
  /// **'Fotoğraf yüklenemedi. Bağlantını kontrol edip tekrar dene.'**
  String get avatarChangeFailed;

  /// No description provided for @phoneAppNotVerified.
  ///
  /// In tr, this message translates to:
  /// **'Uygulama doğrulaması başarısız oldu. Uygulamayı güncelleyip tekrar dene.'**
  String get phoneAppNotVerified;

  /// No description provided for @citySearchHint.
  ///
  /// In tr, this message translates to:
  /// **'Şehir ara…'**
  String get citySearchHint;

  /// No description provided for @citySearchPrompt.
  ///
  /// In tr, this message translates to:
  /// **'Doğduğun şehrin adını yazmaya başla — 34 bin şehir arasından bul.'**
  String get citySearchPrompt;

  /// No description provided for @citySearchNoResults.
  ///
  /// In tr, this message translates to:
  /// **'Listede bulunamadı — yazdığın adla da kaydedebilirsin.'**
  String get citySearchNoResults;

  /// No description provided for @citySearchUseAsTyped.
  ///
  /// In tr, this message translates to:
  /// **'\"{query}\" olarak kaydet'**
  String citySearchUseAsTyped(String query);

  /// No description provided for @residenceCityTitle.
  ///
  /// In tr, this message translates to:
  /// **'Yaşadığın şehir'**
  String get residenceCityTitle;

  /// No description provided for @residenceCityRowSubtitle.
  ///
  /// In tr, this message translates to:
  /// **'Yıl haritası buraya kurulur'**
  String get residenceCityRowSubtitle;

  /// No description provided for @residenceCityBody.
  ///
  /// In tr, this message translates to:
  /// **'Yıl haritası, doğum gününde bulunduğun yere kurulur — şehir Yükselen\'i ve evleri değiştirir. Boş bırakırsan doğum şehrin kullanılır.'**
  String get residenceCityBody;

  /// No description provided for @solarReturnTitle.
  ///
  /// In tr, this message translates to:
  /// **'Yıl Haritası'**
  String get solarReturnTitle;

  /// No description provided for @solarReturnWaitStage1.
  ///
  /// In tr, this message translates to:
  /// **'Güneş\'in dönüş anı hesaplanıyor…'**
  String get solarReturnWaitStage1;

  /// No description provided for @solarReturnWaitStage2.
  ///
  /// In tr, this message translates to:
  /// **'Yılın okuması yazılıyor…'**
  String get solarReturnWaitStage2;

  /// No description provided for @solarReturnLockedBody.
  ///
  /// In tr, this message translates to:
  /// **'Güneş\'in doğum boylamına döndüğü ana kurulan yıl haritası ve Rytho\'nun yıl okuması Rytho+ ile açılır.'**
  String get solarReturnLockedBody;

  /// No description provided for @solarReturnMoment.
  ///
  /// In tr, this message translates to:
  /// **'Dönüş anı'**
  String get solarReturnMoment;

  /// No description provided for @solarReturnNext.
  ///
  /// In tr, this message translates to:
  /// **'Sonraki dönüş: {date}'**
  String solarReturnNext(String date);

  /// No description provided for @solarReturnIdentity.
  ///
  /// In tr, this message translates to:
  /// **'Yılın kimliği'**
  String get solarReturnIdentity;

  /// No description provided for @solarReturnAsc.
  ///
  /// In tr, this message translates to:
  /// **'Yıl Yükseleni'**
  String get solarReturnAsc;

  /// No description provided for @solarReturnSunHouse.
  ///
  /// In tr, this message translates to:
  /// **'Güneş\'in yıl evi'**
  String get solarReturnSunHouse;

  /// No description provided for @solarReturnHouseN.
  ///
  /// In tr, this message translates to:
  /// **'{n}. ev'**
  String solarReturnHouseN(int n);

  /// No description provided for @solarReturnMoon.
  ///
  /// In tr, this message translates to:
  /// **'Yıl Ay\'ı'**
  String get solarReturnMoon;

  /// No description provided for @solarReturnNote.
  ///
  /// In tr, this message translates to:
  /// **'Rytho\'nun yıl okuması'**
  String get solarReturnNote;

  /// No description provided for @innerCalendarTitle.
  ///
  /// In tr, this message translates to:
  /// **'İç Takvim'**
  String get innerCalendarTitle;

  /// No description provided for @innerCalendarWaitStage1.
  ///
  /// In tr, this message translates to:
  /// **'Progres harita ilerletiliyor…'**
  String get innerCalendarWaitStage1;

  /// No description provided for @innerCalendarWaitStage2.
  ///
  /// In tr, this message translates to:
  /// **'30 günün gökyüzü taranıyor…'**
  String get innerCalendarWaitStage2;

  /// No description provided for @innerCalendarLockedBody.
  ///
  /// In tr, this message translates to:
  /// **'Progres Ay\'ın iç mevsimi ve 30 günlük kişisel transit takvimi Rytho+ ile açılır.'**
  String get innerCalendarLockedBody;

  /// No description provided for @innerCalendarProgMoon.
  ///
  /// In tr, this message translates to:
  /// **'Progres Ay — iç mevsimin'**
  String get innerCalendarProgMoon;

  /// No description provided for @innerCalendarNextSign.
  ///
  /// In tr, this message translates to:
  /// **'{date} → yeni burca geçiş'**
  String innerCalendarNextSign(String date);

  /// No description provided for @innerCalendarActive.
  ///
  /// In tr, this message translates to:
  /// **'Şu an etkin'**
  String get innerCalendarActive;

  /// No description provided for @innerCalendarUpcoming.
  ///
  /// In tr, this message translates to:
  /// **'Önümüzdeki 30 gün'**
  String get innerCalendarUpcoming;

  /// No description provided for @innerCalendarQuiet.
  ///
  /// In tr, this message translates to:
  /// **'Bu pencerede kesinleşen açı yok — gökyüzü sakin.'**
  String get innerCalendarQuiet;

  /// No description provided for @innerCalendarArc.
  ///
  /// In tr, this message translates to:
  /// **'Yaşam yayı (solar arc)'**
  String get innerCalendarArc;

  /// No description provided for @innerCalendarNote.
  ///
  /// In tr, this message translates to:
  /// **'Rytho\'nun iç mevsim okuması'**
  String get innerCalendarNote;

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

  /// No description provided for @birthHexagram.
  ///
  /// In tr, this message translates to:
  /// **'Doğum Kapısı'**
  String get birthHexagram;

  /// No description provided for @birthHexagramSubtitle.
  ///
  /// In tr, this message translates to:
  /// **'64 kapı'**
  String get birthHexagramSubtitle;

  /// No description provided for @birthHexagramTitle.
  ///
  /// In tr, this message translates to:
  /// **'Doğum Heksagramı'**
  String get birthHexagramTitle;

  /// No description provided for @birthHexagramGateLine.
  ///
  /// In tr, this message translates to:
  /// **'Kapı {gate} · {line}. çizgi'**
  String birthHexagramGateLine(int gate, int line);

  /// No description provided for @birthHexagramGateOnly.
  ///
  /// In tr, this message translates to:
  /// **'Kapı {gate}'**
  String birthHexagramGateOnly(int gate);

  /// No description provided for @birthHexagramSunAt.
  ///
  /// In tr, this message translates to:
  /// **'Doğumda Güneş: {deg}°'**
  String birthHexagramSunAt(String deg);

  /// No description provided for @birthHexagramBoundary.
  ///
  /// In tr, this message translates to:
  /// **'Doğum saati bilinmediği için kapın {a} ya da {b} olabilir.'**
  String birthHexagramBoundary(int a, int b);

  /// No description provided for @birthHexagramLockedBody.
  ///
  /// In tr, this message translates to:
  /// **'Doğum anındaki Güneş\'in 64 kapı çarkındaki yeri — kalıcı karakter kapın. Rytho+ ile açılır.'**
  String get birthHexagramLockedBody;

  /// No description provided for @birthHexagramNote.
  ///
  /// In tr, this message translates to:
  /// **'Rytho\'nun kapı okuması'**
  String get birthHexagramNote;

  /// No description provided for @birthHexagramGatePassage.
  ///
  /// In tr, this message translates to:
  /// **'Kapının Dokusu'**
  String get birthHexagramGatePassage;

  /// No description provided for @faceReadingTileSubtitle.
  ///
  /// In tr, this message translates to:
  /// **'Firaset sanatı'**
  String get faceReadingTileSubtitle;

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

  /// No description provided for @iChingLockedTitle.
  ///
  /// In tr, this message translates to:
  /// **'İ Ching — Değişimler Kitabı'**
  String get iChingLockedTitle;

  /// No description provided for @iChingLockedBody.
  ///
  /// In tr, this message translates to:
  /// **'Soru sor, gerçek olasılıklarla çekim yap, Rytho yorumuyla oku — Rytho+ ile açılır.'**
  String get iChingLockedBody;

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
  /// **'Bir kullanıcı adı seç. Arkadaş eklemek kullanıcı adı ve davet bağlantısıyla olur; istersen Gizlilik bölümünden rehber eşleşmesini de açabilirsin.'**
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
  /// **'Ayda 300 AI kredisi'**
  String get benefitChatTitle;

  /// No description provided for @benefitChatBody.
  ///
  /// In tr, this message translates to:
  /// **'Sohbette, raporlarda ve çekimlerde dilediğin gibi harca; Rytho seni tanıdıkça konuşma derinleşir.'**
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

  /// No description provided for @birthTimeUnknown.
  ///
  /// In tr, this message translates to:
  /// **'Doğum saatimi bilmiyorum'**
  String get birthTimeUnknown;

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

  /// No description provided for @promoTitle.
  ///
  /// In tr, this message translates to:
  /// **'Yıldızların ötesine geç ✨'**
  String get promoTitle;

  /// No description provided for @promoBody.
  ///
  /// In tr, this message translates to:
  /// **'Doğum haritanın derin analizini ve kişilik raporunu keşfet.'**
  String get promoBody;

  /// No description provided for @promoAction.
  ///
  /// In tr, this message translates to:
  /// **'Keşfet'**
  String get promoAction;

  /// No description provided for @chatTitle.
  ///
  /// In tr, this message translates to:
  /// **'Rytho AI'**
  String get chatTitle;

  /// No description provided for @chatHint.
  ///
  /// In tr, this message translates to:
  /// **'Geleceğinle ilgili her şeyi sor...'**
  String get chatHint;

  /// No description provided for @chatEmptyBody.
  ///
  /// In tr, this message translates to:
  /// **'Haritan, yüzün, kaderin... Aklından geçen her soruyu sor.'**
  String get chatEmptyBody;

  /// No description provided for @chatFailed.
  ///
  /// In tr, this message translates to:
  /// **'Kozmik bağlantı koptu. Lütfen tekrar dene.'**
  String get chatFailed;

  /// No description provided for @suggestCareer.
  ///
  /// In tr, this message translates to:
  /// **'Kariyer 💼'**
  String get suggestCareer;

  /// No description provided for @suggestLove.
  ///
  /// In tr, this message translates to:
  /// **'Aşk hayatı ❤️'**
  String get suggestLove;

  /// No description provided for @suggestMonth.
  ///
  /// In tr, this message translates to:
  /// **'Bu ay beni ne bekliyor?'**
  String get suggestMonth;

  /// No description provided for @suggestFinance.
  ///
  /// In tr, this message translates to:
  /// **'Finansal şans 💰'**
  String get suggestFinance;

  /// No description provided for @suggestMarriage.
  ///
  /// In tr, this message translates to:
  /// **'Evlilik zamanı 💍'**
  String get suggestMarriage;

  /// No description provided for @onboardingTitle.
  ///
  /// In tr, this message translates to:
  /// **'Doğum Anın'**
  String get onboardingTitle;

  /// No description provided for @onboardingBody.
  ///
  /// In tr, this message translates to:
  /// **'Haritanın çizilebilmesi için gökyüzünün o anki dizilişi gerekir. Saat ne kadar kesinse, yükselen o kadar doğrudur.'**
  String get onboardingBody;

  /// No description provided for @onboardingCity.
  ///
  /// In tr, this message translates to:
  /// **'Doğum şehri'**
  String get onboardingCity;

  /// No description provided for @genderFemale.
  ///
  /// In tr, this message translates to:
  /// **'Kadın'**
  String get genderFemale;

  /// No description provided for @genderMale.
  ///
  /// In tr, this message translates to:
  /// **'Erkek'**
  String get genderMale;

  /// No description provided for @genderOther.
  ///
  /// In tr, this message translates to:
  /// **'Diğer'**
  String get genderOther;

  /// No description provided for @onboardingSubmit.
  ///
  /// In tr, this message translates to:
  /// **'Haritamı çiz ✨'**
  String get onboardingSubmit;

  /// No description provided for @onboardingFailed.
  ///
  /// In tr, this message translates to:
  /// **'Kayıt başarısız.'**
  String get onboardingFailed;

  /// No description provided for @onboardingStage1.
  ///
  /// In tr, this message translates to:
  /// **'Gökyüzü konumlanıyor'**
  String get onboardingStage1;

  /// No description provided for @onboardingStage2.
  ///
  /// In tr, this message translates to:
  /// **'Evler hesaplanıyor'**
  String get onboardingStage2;

  /// No description provided for @onboardingStage3.
  ///
  /// In tr, this message translates to:
  /// **'Haritan çiziliyor'**
  String get onboardingStage3;

  /// No description provided for @bigThreeTitle.
  ///
  /// In tr, this message translates to:
  /// **'Göğün sana üç mührü'**
  String get bigThreeTitle;

  /// No description provided for @bigThreeSun.
  ///
  /// In tr, this message translates to:
  /// **'GÜNEŞ'**
  String get bigThreeSun;

  /// No description provided for @bigThreeMoon.
  ///
  /// In tr, this message translates to:
  /// **'AY'**
  String get bigThreeMoon;

  /// No description provided for @bigThreeAscendant.
  ///
  /// In tr, this message translates to:
  /// **'YÜKSELEN'**
  String get bigThreeAscendant;

  /// No description provided for @bigThreeStart.
  ///
  /// In tr, this message translates to:
  /// **'Yolculuğa başla'**
  String get bigThreeStart;

  /// No description provided for @profileSubscriptionRow.
  ///
  /// In tr, this message translates to:
  /// **'Abonelik ve krediler'**
  String get profileSubscriptionRow;

  /// No description provided for @subscriptionScreenTitle.
  ///
  /// In tr, this message translates to:
  /// **'Abonelik ve Krediler'**
  String get subscriptionScreenTitle;

  /// No description provided for @subPlanLabel.
  ///
  /// In tr, this message translates to:
  /// **'PLAN'**
  String get subPlanLabel;

  /// No description provided for @subPlanFree.
  ///
  /// In tr, this message translates to:
  /// **'Ücretsiz'**
  String get subPlanFree;

  /// No description provided for @subPlanFreeBody.
  ///
  /// In tr, this message translates to:
  /// **'Kişiye özel günlük okuma, natal rapor, BaZi, Yıl Haritası ve İç Takvim Rytho+ ile açılır.'**
  String get subPlanFreeBody;

  /// No description provided for @subPlanMonthly.
  ///
  /// In tr, this message translates to:
  /// **'Aylık Rytho+'**
  String get subPlanMonthly;

  /// No description provided for @subPlanYearly.
  ///
  /// In tr, this message translates to:
  /// **'Yıllık Rytho+'**
  String get subPlanYearly;

  /// No description provided for @subGoPlus.
  ///
  /// In tr, this message translates to:
  /// **'Rytho+\'a geç'**
  String get subGoPlus;

  /// No description provided for @subStatusLabel.
  ///
  /// In tr, this message translates to:
  /// **'Durum'**
  String get subStatusLabel;

  /// No description provided for @subStatusTrial.
  ///
  /// In tr, this message translates to:
  /// **'Deneme sürümü'**
  String get subStatusTrial;

  /// No description provided for @subRenewsLabel.
  ///
  /// In tr, this message translates to:
  /// **'Yenilenme'**
  String get subRenewsLabel;

  /// No description provided for @subEndsLabel.
  ///
  /// In tr, this message translates to:
  /// **'Sona erme'**
  String get subEndsLabel;

  /// No description provided for @subManage.
  ///
  /// In tr, this message translates to:
  /// **'Aboneliği yönet'**
  String get subManage;

  /// No description provided for @subRestoreDone.
  ///
  /// In tr, this message translates to:
  /// **'Aboneliğin geri yüklendi ✨'**
  String get subRestoreDone;

  /// No description provided for @subMonthlyAllowanceRow.
  ///
  /// In tr, this message translates to:
  /// **'Aylık hak'**
  String get subMonthlyAllowanceRow;

  /// No description provided for @subAllowanceResetsRow.
  ///
  /// In tr, this message translates to:
  /// **'Hak tazelenir'**
  String get subAllowanceResetsRow;

  /// No description provided for @subBuyTokens.
  ///
  /// In tr, this message translates to:
  /// **'Kredi paketi al'**
  String get subBuyTokens;

  /// No description provided for @atlasWaitStage1.
  ///
  /// In tr, this message translates to:
  /// **'Gezegenler yerleşiyor'**
  String get atlasWaitStage1;

  /// No description provided for @atlasWaitStage2.
  ///
  /// In tr, this message translates to:
  /// **'Açılar okunuyor'**
  String get atlasWaitStage2;

  /// No description provided for @atlasWaitStage3.
  ///
  /// In tr, this message translates to:
  /// **'Raporun yazılıyor'**
  String get atlasWaitStage3;

  /// No description provided for @baziWaitStage1.
  ///
  /// In tr, this message translates to:
  /// **'Dört sütun kuruluyor'**
  String get baziWaitStage1;

  /// No description provided for @baziWaitStage2.
  ///
  /// In tr, this message translates to:
  /// **'Elementler tartılıyor'**
  String get baziWaitStage2;

  /// No description provided for @baziWaitStage3.
  ///
  /// In tr, this message translates to:
  /// **'Kader notun yazılıyor'**
  String get baziWaitStage3;

  /// No description provided for @atlasTitle.
  ///
  /// In tr, this message translates to:
  /// **'Doğum Haritası Analizi'**
  String get atlasTitle;

  /// No description provided for @appHeadline.
  ///
  /// In tr, this message translates to:
  /// **'Kişisel Kozmik Zekân'**
  String get appHeadline;

  /// No description provided for @consentNote.
  ///
  /// In tr, this message translates to:
  /// **'Devam ederek gizlilik ilkelerini kabul etmiş olursun.\nYorumlar içgörü amaçlıdır; tıbbi/finansal tavsiye değildir.'**
  String get consentNote;

  /// No description provided for @authNameRequired.
  ///
  /// In tr, this message translates to:
  /// **'Adını yaz.'**
  String get authNameRequired;

  /// No description provided for @authInvalidEmail.
  ///
  /// In tr, this message translates to:
  /// **'Geçerli bir e-posta yaz.'**
  String get authInvalidEmail;

  /// No description provided for @authWrongCredentials.
  ///
  /// In tr, this message translates to:
  /// **'E-posta veya şifre hatalı.'**
  String get authWrongCredentials;

  /// No description provided for @authEmailInUse.
  ///
  /// In tr, this message translates to:
  /// **'Bu e-posta zaten kayıtlı. Giriş yapmayı dene.'**
  String get authEmailInUse;

  /// No description provided for @authWeakPassword.
  ///
  /// In tr, this message translates to:
  /// **'Şifre en az 6 karakter olmalı.'**
  String get authWeakPassword;

  /// No description provided for @authTooManyRequests.
  ///
  /// In tr, this message translates to:
  /// **'Çok fazla deneme yapıldı. Biraz sonra tekrar dene.'**
  String get authTooManyRequests;

  /// No description provided for @authDisabled.
  ///
  /// In tr, this message translates to:
  /// **'E-posta ile giriş şu an kapalı.'**
  String get authDisabled;

  /// No description provided for @authNetwork.
  ///
  /// In tr, this message translates to:
  /// **'Bağlantı kurulamadı. İnternetini kontrol et.'**
  String get authNetwork;

  /// No description provided for @authFailed.
  ///
  /// In tr, this message translates to:
  /// **'Bir şeyler ters gitti. Tekrar dene.'**
  String get authFailed;

  /// No description provided for @authReauthNeeded.
  ///
  /// In tr, this message translates to:
  /// **'Google hesabının bu cihazda yeniden doğrulanması gerekiyor. Telefonunun Ayarlar → Google bölümüne girip hesabını doğrula (gerekirse hesabı kaldırıp yeniden ekle), sonra tekrar dene.'**
  String get authReauthNeeded;

  /// No description provided for @displayName.
  ///
  /// In tr, this message translates to:
  /// **'Adın'**
  String get displayName;

  /// No description provided for @passwordRepeat.
  ///
  /// In tr, this message translates to:
  /// **'Şifre (tekrar)'**
  String get passwordRepeat;

  /// No description provided for @passwordsDoNotMatch.
  ///
  /// In tr, this message translates to:
  /// **'Şifreler eşleşmiyor.'**
  String get passwordsDoNotMatch;

  /// No description provided for @enterEmailFirst.
  ///
  /// In tr, this message translates to:
  /// **'Önce e-posta adresini yaz.'**
  String get enterEmailFirst;

  /// No description provided for @resetLinkSent.
  ///
  /// In tr, this message translates to:
  /// **'Şifre sıfırlama bağlantısı gönderildi.'**
  String get resetLinkSent;

  /// No description provided for @nameLabel.
  ///
  /// In tr, this message translates to:
  /// **'Ad'**
  String get nameLabel;

  /// No description provided for @signAries.
  ///
  /// In tr, this message translates to:
  /// **'Koç'**
  String get signAries;

  /// No description provided for @signTaurus.
  ///
  /// In tr, this message translates to:
  /// **'Boğa'**
  String get signTaurus;

  /// No description provided for @signGemini.
  ///
  /// In tr, this message translates to:
  /// **'İkizler'**
  String get signGemini;

  /// No description provided for @signCancer.
  ///
  /// In tr, this message translates to:
  /// **'Yengeç'**
  String get signCancer;

  /// No description provided for @signLeo.
  ///
  /// In tr, this message translates to:
  /// **'Aslan'**
  String get signLeo;

  /// No description provided for @signVirgo.
  ///
  /// In tr, this message translates to:
  /// **'Başak'**
  String get signVirgo;

  /// No description provided for @signLibra.
  ///
  /// In tr, this message translates to:
  /// **'Terazi'**
  String get signLibra;

  /// No description provided for @signScorpio.
  ///
  /// In tr, this message translates to:
  /// **'Akrep'**
  String get signScorpio;

  /// No description provided for @signSagittarius.
  ///
  /// In tr, this message translates to:
  /// **'Yay'**
  String get signSagittarius;

  /// No description provided for @signCapricorn.
  ///
  /// In tr, this message translates to:
  /// **'Oğlak'**
  String get signCapricorn;

  /// No description provided for @signAquarius.
  ///
  /// In tr, this message translates to:
  /// **'Kova'**
  String get signAquarius;

  /// No description provided for @signPisces.
  ///
  /// In tr, this message translates to:
  /// **'Balık'**
  String get signPisces;

  /// No description provided for @atlasPlanetPositions.
  ///
  /// In tr, this message translates to:
  /// **'Gezegen Konumları'**
  String get atlasPlanetPositions;

  /// No description provided for @atlasTraits.
  ///
  /// In tr, this message translates to:
  /// **'Kişilik Özellikleri'**
  String get atlasTraits;

  /// No description provided for @atlasAspects.
  ///
  /// In tr, this message translates to:
  /// **'Açılar'**
  String get atlasAspects;

  /// No description provided for @traitDetermination.
  ///
  /// In tr, this message translates to:
  /// **'Kararlılık'**
  String get traitDetermination;

  /// No description provided for @traitCommunication.
  ///
  /// In tr, this message translates to:
  /// **'İletişim'**
  String get traitCommunication;

  /// No description provided for @traitSensitivity.
  ///
  /// In tr, this message translates to:
  /// **'Duyarlılık'**
  String get traitSensitivity;

  /// No description provided for @moonIllumination.
  ///
  /// In tr, this message translates to:
  /// **'aydınlanma %{percent}'**
  String moonIllumination(Object percent);

  /// No description provided for @moonIlluminationAsOf.
  ///
  /// In tr, this message translates to:
  /// **'{time} itibarıyla — oran gün içinde değişir'**
  String moonIlluminationAsOf(String time);

  /// No description provided for @reportPostTitle.
  ///
  /// In tr, this message translates to:
  /// **'GÖNDERİYİ ŞİKAYET ET'**
  String get reportPostTitle;

  /// No description provided for @reportUserTitle.
  ///
  /// In tr, this message translates to:
  /// **'KULLANICIYI ŞİKAYET ET'**
  String get reportUserTitle;

  /// No description provided for @reportNote.
  ///
  /// In tr, this message translates to:
  /// **'Şikayetin ekibimiz tarafından incelenir.'**
  String get reportNote;

  /// No description provided for @reportReasonSpam.
  ///
  /// In tr, this message translates to:
  /// **'Spam veya yanıltıcı içerik'**
  String get reportReasonSpam;

  /// No description provided for @reportReasonHarassment.
  ///
  /// In tr, this message translates to:
  /// **'Hakaret veya taciz'**
  String get reportReasonHarassment;

  /// No description provided for @reportReasonInappropriate.
  ///
  /// In tr, this message translates to:
  /// **'Uygunsuz / rahatsız edici içerik'**
  String get reportReasonInappropriate;

  /// No description provided for @reportReasonOther.
  ///
  /// In tr, this message translates to:
  /// **'Diğer'**
  String get reportReasonOther;

  /// No description provided for @reportSubmitted.
  ///
  /// In tr, this message translates to:
  /// **'Şikayetin alındı; en kısa sürede incelenecek. Teşekkürler.'**
  String get reportSubmitted;

  /// No description provided for @reportFailed.
  ///
  /// In tr, this message translates to:
  /// **'Şikayet gönderilemedi.'**
  String get reportFailed;

  /// No description provided for @recordLabel.
  ///
  /// In tr, this message translates to:
  /// **'✨ Kayıt'**
  String get recordLabel;

  /// No description provided for @aFriend.
  ///
  /// In tr, this message translates to:
  /// **'Bir arkadaşın'**
  String get aFriend;

  /// No description provided for @iChingIntro.
  ///
  /// In tr, this message translates to:
  /// **'3000 yıllık 64 heksagram matrisi. Sorunu yaz; paralar gerçek olasılık dağılımıyla atılır, hareketli çizgiler geleceğe köprü kurar.'**
  String get iChingIntro;

  /// No description provided for @iChingQuestionHint.
  ///
  /// In tr, this message translates to:
  /// **'Sorun nedir?'**
  String get iChingQuestionHint;

  /// No description provided for @iChingMethodCoins.
  ///
  /// In tr, this message translates to:
  /// **'Üç Para 🪙'**
  String get iChingMethodCoins;

  /// No description provided for @iChingMethodYarrow.
  ///
  /// In tr, this message translates to:
  /// **'Civanperçemi 🌿'**
  String get iChingMethodYarrow;

  /// No description provided for @iChingCastAction.
  ///
  /// In tr, this message translates to:
  /// **'Çekimi yap'**
  String get iChingCastAction;

  /// No description provided for @iChingQuestionRequired.
  ///
  /// In tr, this message translates to:
  /// **'Önce kalbindeki soruyu yaz.'**
  String get iChingQuestionRequired;

  /// No description provided for @iChingQuestionInvalid.
  ///
  /// In tr, this message translates to:
  /// **'Kâhin bu metinde yorumlayacağı bir soru bulamadı — niyetini kendi yaşamınla ilgili bir cümleyle yaz.'**
  String get iChingQuestionInvalid;

  /// No description provided for @iChingCoinsInAir.
  ///
  /// In tr, this message translates to:
  /// **'Paralar havada...'**
  String get iChingCoinsInAir;

  /// No description provided for @iChingHexagramLabel.
  ///
  /// In tr, this message translates to:
  /// **'HEKSAGRAM {number}'**
  String iChingHexagramLabel(Object number);

  /// No description provided for @iChingTransformedTo.
  ///
  /// In tr, this message translates to:
  /// **'→ dönüşüm: {name} (#{number})'**
  String iChingTransformedTo(Object name, Object number);

  /// No description provided for @iChingOracleNote.
  ///
  /// In tr, this message translates to:
  /// **'Rytho\'nun kehanet notu'**
  String get iChingOracleNote;

  /// No description provided for @iChingQuotaFree.
  ///
  /// In tr, this message translates to:
  /// **'Bugünkü hak: {left}/{limit}'**
  String iChingQuotaFree(int left, int limit);

  /// No description provided for @iChingQuotaTokens.
  ///
  /// In tr, this message translates to:
  /// **'Çekim bedeli: {n} kredi'**
  String iChingQuotaTokens(int n);

  /// No description provided for @iChingJudgmentTitle.
  ///
  /// In tr, this message translates to:
  /// **'Hüküm'**
  String get iChingJudgmentTitle;

  /// No description provided for @iChingImageTitle.
  ///
  /// In tr, this message translates to:
  /// **'İmge'**
  String get iChingImageTitle;

  /// No description provided for @iChingMovingTitle.
  ///
  /// In tr, this message translates to:
  /// **'Hareketli Çizgiler'**
  String get iChingMovingTitle;

  /// No description provided for @iChingLiuYaoTitle.
  ///
  /// In tr, this message translates to:
  /// **'Liu Yao'**
  String get iChingLiuYaoTitle;

  /// No description provided for @iChingNuclearLabel.
  ///
  /// In tr, this message translates to:
  /// **'çekirdek: {name} (#{n})'**
  String iChingNuclearLabel(String name, int n);

  /// No description provided for @iChingLegend.
  ///
  /// In tr, this message translates to:
  /// **'○ eski yang (9) · × eski yin (6) — dönen çizgiler'**
  String get iChingLegend;

  /// No description provided for @iChingLineLabel.
  ///
  /// In tr, this message translates to:
  /// **'{n}. çizgi'**
  String iChingLineLabel(int n);

  /// No description provided for @iChingPalaceLabel.
  ///
  /// In tr, this message translates to:
  /// **'Saray: {name} · özne (shi) {shi}. çizgi · karşılık (ying) {ying}. çizgi'**
  String iChingPalaceLabel(String name, int shi, int ying);

  /// No description provided for @iChingVoidTag.
  ///
  /// In tr, this message translates to:
  /// **'boşluk'**
  String get iChingVoidTag;

  /// No description provided for @iChingClashTag.
  ///
  /// In tr, this message translates to:
  /// **'çarpışma'**
  String get iChingClashTag;

  /// No description provided for @iChingDayLabel.
  ///
  /// In tr, this message translates to:
  /// **'Çekim günü: {day}'**
  String iChingDayLabel(String day);

  /// No description provided for @iChingTrigramsLabel.
  ///
  /// In tr, this message translates to:
  /// **'{lower} altında, {upper} üstte'**
  String iChingTrigramsLabel(String lower, String upper);

  /// No description provided for @baziHeadline.
  ///
  /// In tr, this message translates to:
  /// **'Kaderin Dört Sütunu'**
  String get baziHeadline;

  /// No description provided for @baziChineseSign.
  ///
  /// In tr, this message translates to:
  /// **'Çin burcun: {animal} · {dayMaster}'**
  String baziChineseSign(Object animal, Object dayMaster);

  /// No description provided for @baziFourPillars.
  ///
  /// In tr, this message translates to:
  /// **'Dört Sütun'**
  String get baziFourPillars;

  /// No description provided for @baziPillarHour.
  ///
  /// In tr, this message translates to:
  /// **'SAAT'**
  String get baziPillarHour;

  /// No description provided for @baziPillarDay.
  ///
  /// In tr, this message translates to:
  /// **'GÜN'**
  String get baziPillarDay;

  /// No description provided for @baziPillarMonth.
  ///
  /// In tr, this message translates to:
  /// **'AY'**
  String get baziPillarMonth;

  /// No description provided for @baziPillarYear.
  ///
  /// In tr, this message translates to:
  /// **'YIL'**
  String get baziPillarYear;

  /// No description provided for @baziElementBalance.
  ///
  /// In tr, this message translates to:
  /// **'Element Terazisi'**
  String get baziElementBalance;

  /// No description provided for @baziNourish.
  ///
  /// In tr, this message translates to:
  /// **'Beslenecek element: {elements}'**
  String baziNourish(Object elements);

  /// No description provided for @baziLuckPillars.
  ///
  /// In tr, this message translates to:
  /// **'Şans Sütunları (Da Yun)'**
  String get baziLuckPillars;

  /// No description provided for @baziStrengthTitle.
  ///
  /// In tr, this message translates to:
  /// **'Güç Hükmü'**
  String get baziStrengthTitle;

  /// No description provided for @baziRatioLabel.
  ///
  /// In tr, this message translates to:
  /// **'destek oranı'**
  String get baziRatioLabel;

  /// No description provided for @baziFavorable.
  ///
  /// In tr, this message translates to:
  /// **'Yararlı elementler'**
  String get baziFavorable;

  /// No description provided for @baziUnfavorable.
  ///
  /// In tr, this message translates to:
  /// **'Yüke dönüşenler'**
  String get baziUnfavorable;

  /// No description provided for @baziClimateNote.
  ///
  /// In tr, this message translates to:
  /// **'Mevsim iklimi düzenleyici ister: {element}'**
  String baziClimateNote(String element);

  /// No description provided for @baziBasisTitle.
  ///
  /// In tr, this message translates to:
  /// **'Hükmün dayanağı'**
  String get baziBasisTitle;

  /// No description provided for @baziSrcMonthCommand.
  ///
  /// In tr, this message translates to:
  /// **'Ay komutu'**
  String get baziSrcMonthCommand;

  /// No description provided for @baziSrcRoot.
  ///
  /// In tr, this message translates to:
  /// **'{pillar} dalındaki {stem} kökü'**
  String baziSrcRoot(String pillar, String stem);

  /// No description provided for @baziSrcStem.
  ///
  /// In tr, this message translates to:
  /// **'{pillar} gövdesi {stem}'**
  String baziSrcStem(String pillar, String stem);

  /// No description provided for @baziStarsTitle.
  ///
  /// In tr, this message translates to:
  /// **'Yıldızlar (Shen Sha)'**
  String get baziStarsTitle;

  /// No description provided for @baziNoStars.
  ///
  /// In tr, this message translates to:
  /// **'Bu haritada işaretli yıldız yok — yapının kendisi konuşuyor.'**
  String get baziNoStars;

  /// No description provided for @baziLuckStartLabel.
  ///
  /// In tr, this message translates to:
  /// **'İlk dönem: {years} yaş {months} ay ({date})'**
  String baziLuckStartLabel(int years, int months, String date);

  /// No description provided for @baziThisYear.
  ///
  /// In tr, this message translates to:
  /// **'Bu yılın sütunu: {label} ({tenGod})'**
  String baziThisYear(String label, String tenGod);

  /// No description provided for @baziCurrentTag.
  ///
  /// In tr, this message translates to:
  /// **'şimdi'**
  String get baziCurrentTag;

  /// No description provided for @baziAgeRange.
  ///
  /// In tr, this message translates to:
  /// **'{from}–{to} YAŞ'**
  String baziAgeRange(Object from, Object to);

  /// No description provided for @baziFateNote.
  ///
  /// In tr, this message translates to:
  /// **'Rytho\'nun kader notu'**
  String get baziFateNote;

  /// No description provided for @traitEnergy.
  ///
  /// In tr, this message translates to:
  /// **'Enerji'**
  String get traitEnergy;

  /// No description provided for @traitPracticality.
  ///
  /// In tr, this message translates to:
  /// **'Pratiklik'**
  String get traitPracticality;

  /// No description provided for @defaultUserName.
  ///
  /// In tr, this message translates to:
  /// **'Gezgin'**
  String get defaultUserName;

  /// No description provided for @retrogradeChip.
  ///
  /// In tr, this message translates to:
  /// **'{planet} retro'**
  String retrogradeChip(Object planet);

  /// No description provided for @atlasReadingNote.
  ///
  /// In tr, this message translates to:
  /// **'✨ Rytho\'nun okuma notu'**
  String get atlasReadingNote;

  /// No description provided for @notifications.
  ///
  /// In tr, this message translates to:
  /// **'Bildirimler'**
  String get notifications;

  /// No description provided for @notifyDaily.
  ///
  /// In tr, this message translates to:
  /// **'Günlük okuma'**
  String get notifyDaily;

  /// No description provided for @notifyDailyBody.
  ///
  /// In tr, this message translates to:
  /// **'Sabahları bugünün gökyüzü hazır olduğunda haber ver.'**
  String get notifyDailyBody;

  /// No description provided for @notifyStreak.
  ///
  /// In tr, this message translates to:
  /// **'Seri hatırlatması'**
  String get notifyStreak;

  /// No description provided for @notifyStreakBody.
  ///
  /// In tr, this message translates to:
  /// **'Akşam, serin kırılmadan önce kısa bir hatırlatma.'**
  String get notifyStreakBody;

  /// No description provided for @notifyFriends.
  ///
  /// In tr, this message translates to:
  /// **'Arkadaş tepkileri'**
  String get notifyFriends;

  /// No description provided for @notifyFriendsBody.
  ///
  /// In tr, this message translates to:
  /// **'Bir arkadaşın sana tepki gönderdiğinde haber ver.'**
  String get notifyFriendsBody;

  /// No description provided for @quietHours.
  ///
  /// In tr, this message translates to:
  /// **'Sessiz saatler'**
  String get quietHours;

  /// No description provided for @quietHoursBody.
  ///
  /// In tr, this message translates to:
  /// **'Bu aralıkta bildirim gönderilmez.'**
  String get quietHoursBody;

  /// No description provided for @quietHoursRange.
  ///
  /// In tr, this message translates to:
  /// **'{from}:00 – {to}:00'**
  String quietHoursRange(Object from, Object to);

  /// No description provided for @quietHoursOff.
  ///
  /// In tr, this message translates to:
  /// **'Kapalı'**
  String get quietHoursOff;

  /// No description provided for @notificationsDisabledHint.
  ///
  /// In tr, this message translates to:
  /// **'Bildirimler cihaz ayarlarından kapalı. Açmak için sistem ayarlarına git.'**
  String get notificationsDisabledHint;

  /// No description provided for @enableNotifications.
  ///
  /// In tr, this message translates to:
  /// **'Bildirimleri aç'**
  String get enableNotifications;

  /// No description provided for @deleteAccount.
  ///
  /// In tr, this message translates to:
  /// **'Hesabı sil'**
  String get deleteAccount;

  /// No description provided for @deleteAccountTitle.
  ///
  /// In tr, this message translates to:
  /// **'Hesabını silmek üzeresin'**
  String get deleteAccountTitle;

  /// No description provided for @deleteAccountBody.
  ///
  /// In tr, this message translates to:
  /// **'Bu işlem geri alınamaz. Silinecekler: doğum kaydın, sohbetten biriktirdiğimiz notlar, arkadaşlıkların, kullanıcı adın ve sana özel üretilmiş tüm okumalar.'**
  String get deleteAccountBody;

  /// No description provided for @deleteAccountKeeps.
  ///
  /// In tr, this message translates to:
  /// **'Gönderdiğin şikayet kayıtları saklanır; başkalarının güvenliğiyle ilgili oldukları için silinmez.'**
  String get deleteAccountKeeps;

  /// No description provided for @deleteAccountSubscription.
  ///
  /// In tr, this message translates to:
  /// **'Aboneliğin varsa uygulama mağazandan ayrıca iptal etmelisin; hesabı silmek aboneliği durdurmaz.'**
  String get deleteAccountSubscription;

  /// No description provided for @deleteAccountConfirmHint.
  ///
  /// In tr, this message translates to:
  /// **'Onaylamak için SİL yaz'**
  String get deleteAccountConfirmHint;

  /// No description provided for @deleteAccountConfirmWord.
  ///
  /// In tr, this message translates to:
  /// **'SİL'**
  String get deleteAccountConfirmWord;

  /// No description provided for @deleteAccountAction.
  ///
  /// In tr, this message translates to:
  /// **'Hesabımı kalıcı olarak sil'**
  String get deleteAccountAction;

  /// No description provided for @deleteAccountFailed.
  ///
  /// In tr, this message translates to:
  /// **'Hesap silinemedi. Lütfen tekrar dene.'**
  String get deleteAccountFailed;

  /// No description provided for @deleteAccountReauth.
  ///
  /// In tr, this message translates to:
  /// **'Güvenlik için tekrar giriş yapman gerekiyor. Çıkış yapıp yeniden giriş yaptıktan sonra bu işlemi tekrarla.'**
  String get deleteAccountReauth;

  /// No description provided for @cancel.
  ///
  /// In tr, this message translates to:
  /// **'Vazgeç'**
  String get cancel;

  /// No description provided for @insightDisclaimer.
  ///
  /// In tr, this message translates to:
  /// **'Rytho gerçek gökyüzü hesabına dayanır ama yorum bir öngörü yöntemi değildir. Okumalar içgörü içindir; tıbbi, hukuki veya finansal tavsiye yerine geçmez. 13 yaş ve üzeri içindir.'**
  String get insightDisclaimer;

  /// No description provided for @shareReading.
  ///
  /// In tr, this message translates to:
  /// **'Paylaş'**
  String get shareReading;

  /// No description provided for @shareCardTagline.
  ///
  /// In tr, this message translates to:
  /// **'gerçek gökyüzü hesabıyla'**
  String get shareCardTagline;

  /// No description provided for @shareFailed.
  ///
  /// In tr, this message translates to:
  /// **'Paylaşım kartı oluşturulamadı.'**
  String get shareFailed;

  /// No description provided for @signInWithApple.
  ///
  /// In tr, this message translates to:
  /// **'Apple ile giriş'**
  String get signInWithApple;

  /// No description provided for @consentPrefix.
  ///
  /// In tr, this message translates to:
  /// **'Devam ederek '**
  String get consentPrefix;

  /// No description provided for @consentAnd.
  ///
  /// In tr, this message translates to:
  /// **' ve '**
  String get consentAnd;

  /// No description provided for @consentSuffix.
  ///
  /// In tr, this message translates to:
  /// **' metinlerini kabul etmiş olursun.'**
  String get consentSuffix;

  /// No description provided for @insightNote.
  ///
  /// In tr, this message translates to:
  /// **'Yorumlar içgörü amaçlıdır; tıbbi, hukuki veya finansal tavsiye değildir.'**
  String get insightNote;

  /// No description provided for @ageConfirm.
  ///
  /// In tr, this message translates to:
  /// **'13 yaşından büyüğüm'**
  String get ageConfirm;

  /// No description provided for @ageRequired.
  ///
  /// In tr, this message translates to:
  /// **'Devam etmek için yaş beyanını onaylaman gerekiyor.'**
  String get ageRequired;

  /// No description provided for @passwordRuleHint.
  ///
  /// In tr, this message translates to:
  /// **'En az 8 karakter, harf ve rakam içermeli.'**
  String get passwordRuleHint;

  /// No description provided for @passwordTooShort.
  ///
  /// In tr, this message translates to:
  /// **'Şifre en az 8 karakter olmalı.'**
  String get passwordTooShort;

  /// No description provided for @passwordTooSimple.
  ///
  /// In tr, this message translates to:
  /// **'Şifre harf ve rakam (veya sembol) içermeli.'**
  String get passwordTooSimple;

  /// No description provided for @verificationSent.
  ///
  /// In tr, this message translates to:
  /// **'Doğrulama bağlantısı {email} adresine gönderildi. Gelen kutunu kontrol et.'**
  String verificationSent(Object email);

  /// No description provided for @resetLinkSentNeutral.
  ///
  /// In tr, this message translates to:
  /// **'Bu adres kayıtlıysa şifre sıfırlama bağlantısı gönderildi.'**
  String get resetLinkSentNeutral;

  /// No description provided for @useGoogleInstead.
  ///
  /// In tr, this message translates to:
  /// **'Giriş yapılamadı. Şifren hatalı olabilir ya da bu hesap Google/Apple ile açılmış olabilir — aşağıdaki düğmeleri dene.'**
  String get useGoogleInstead;

  /// No description provided for @faceReadingTitle.
  ///
  /// In tr, this message translates to:
  /// **'Yüz Okuma'**
  String get faceReadingTitle;

  /// No description provided for @faceGuideNoFace.
  ///
  /// In tr, this message translates to:
  /// **'Yüzünü çerçeveye al'**
  String get faceGuideNoFace;

  /// No description provided for @faceGuideTooFar.
  ///
  /// In tr, this message translates to:
  /// **'Biraz yaklaş'**
  String get faceGuideTooFar;

  /// No description provided for @faceGuideTooClose.
  ///
  /// In tr, this message translates to:
  /// **'Biraz uzaklaş'**
  String get faceGuideTooClose;

  /// No description provided for @faceGuideOffCentre.
  ///
  /// In tr, this message translates to:
  /// **'Yüzünü ortala'**
  String get faceGuideOffCentre;

  /// No description provided for @faceGuideTilted.
  ///
  /// In tr, this message translates to:
  /// **'Başını dik tut'**
  String get faceGuideTilted;

  /// No description provided for @faceGuideReady.
  ///
  /// In tr, this message translates to:
  /// **'Hazır — sabit dur'**
  String get faceGuideReady;

  /// No description provided for @faceGuideForehead.
  ///
  /// In tr, this message translates to:
  /// **'Alnını aç — saçını geriye al'**
  String get faceGuideForehead;

  /// No description provided for @faceScanning.
  ///
  /// In tr, this message translates to:
  /// **'Yüz hatların okunuyor'**
  String get faceScanning;

  /// No description provided for @faceScanNodes.
  ///
  /// In tr, this message translates to:
  /// **'Noktalar yerleşiyor'**
  String get faceScanNodes;

  /// No description provided for @faceScanReading.
  ///
  /// In tr, this message translates to:
  /// **'Firaset ile eşleştiriliyor'**
  String get faceScanReading;

  /// No description provided for @faceCapture.
  ///
  /// In tr, this message translates to:
  /// **'Çek'**
  String get faceCapture;

  /// No description provided for @faceRetake.
  ///
  /// In tr, this message translates to:
  /// **'Yeniden çek'**
  String get faceRetake;

  /// No description provided for @faceConsentTitle.
  ///
  /// In tr, this message translates to:
  /// **'Yüz okuma için onayın gerekiyor'**
  String get faceConsentTitle;

  /// No description provided for @faceConsentBody.
  ///
  /// In tr, this message translates to:
  /// **'Yüz okuma, kameradan aldığı kareyi ya da galeriden seçtiğin fotoğrafı CİHAZINDA işler. Görüntü sunucuya gönderilmez, hiçbir yerde saklanmaz ve işlem biter bitmez silinir (galeri yolunda uygulamaya verilen kopya silinir; asıl fotoğrafına dokunulmaz). Sunucuya yalnızca yüz hatlarından türetilen oranlar (ör. alın/çene yükseklik oranı) gider; bu sayılar kişiyi tanımaya yaramaz.'**
  String get faceConsentBody;

  /// No description provided for @faceConsentCheckbox.
  ///
  /// In tr, this message translates to:
  /// **'Yüz görüntümün cihazımda işlenmesine onay veriyorum.'**
  String get faceConsentCheckbox;

  /// No description provided for @faceConsentContinue.
  ///
  /// In tr, this message translates to:
  /// **'Onaylıyorum ve devam et'**
  String get faceConsentContinue;

  /// No description provided for @faceConsentLearnMore.
  ///
  /// In tr, this message translates to:
  /// **'Gizlilik politikasını oku'**
  String get faceConsentLearnMore;

  /// No description provided for @faceCameraDenied.
  ///
  /// In tr, this message translates to:
  /// **'Kamera izni verilmedi. Yüz okuma için kameraya erişim gerekiyor.'**
  String get faceCameraDenied;

  /// No description provided for @faceDetectFailed.
  ///
  /// In tr, this message translates to:
  /// **'Yüz tespit edilemedi. Işığın yeterli olduğundan ve yüzünün çerçevede olduğundan emin ol.'**
  String get faceDetectFailed;

  /// No description provided for @faceReadingHint.
  ///
  /// In tr, this message translates to:
  /// **'Gelenek der ki: tek bir belirti hüküm vermez. Aşağıdaki okuma bir eğilimdir, kader değildir.'**
  String get faceReadingHint;

  /// No description provided for @faceReadingLockedBody.
  ///
  /// In tr, this message translates to:
  /// **'Yüz hatlarından mizaç okuması. Görüntü cihazında işlenir, hiçbir yere gönderilmez.'**
  String get faceReadingLockedBody;

  /// No description provided for @faceReadingEntryBody.
  ///
  /// In tr, this message translates to:
  /// **'Yüzünü tarat, firaset geleneğine göre mizacını oku.'**
  String get faceReadingEntryBody;

  /// No description provided for @faceGalleryButton.
  ///
  /// In tr, this message translates to:
  /// **'Galeriden seç'**
  String get faceGalleryButton;

  /// No description provided for @faceLensButton.
  ///
  /// In tr, this message translates to:
  /// **'Kamerayı çevir'**
  String get faceLensButton;

  /// No description provided for @faceStillAnalyzing.
  ///
  /// In tr, this message translates to:
  /// **'Fotoğraf inceleniyor…'**
  String get faceStillAnalyzing;

  /// No description provided for @faceStillNoFace.
  ///
  /// In tr, this message translates to:
  /// **'Fotoğrafta yüz bulunamadı. Önden, iyi aydınlatılmış bir fotoğraf dene.'**
  String get faceStillNoFace;

  /// No description provided for @faceStillNoLandmarks.
  ///
  /// In tr, this message translates to:
  /// **'Yüz hatları seçilemedi. Yüzün tam göründüğü, önden bir fotoğraf dene.'**
  String get faceStillNoLandmarks;

  /// No description provided for @faceStillSingleFrameNote.
  ///
  /// In tr, this message translates to:
  /// **'Bu okuma tek bir fotoğraf karesinden ölçüldü; canlı çekim daha kararlı sonuç verir.'**
  String get faceStillSingleFrameNote;

  /// No description provided for @faceWaitStage1.
  ///
  /// In tr, this message translates to:
  /// **'Oranlar geleneğin ölçüleriyle karşılaştırılıyor…'**
  String get faceWaitStage1;

  /// No description provided for @faceWaitStage2.
  ///
  /// In tr, this message translates to:
  /// **'Firaset kaynakları taranıyor…'**
  String get faceWaitStage2;

  /// No description provided for @faceWaitStage3.
  ///
  /// In tr, this message translates to:
  /// **'Okuman yazılıyor…'**
  String get faceWaitStage3;

  /// No description provided for @faceConsentSetting.
  ///
  /// In tr, this message translates to:
  /// **'Yüz okuma rızası'**
  String get faceConsentSetting;

  /// No description provided for @faceConsentSettingOn.
  ///
  /// In tr, this message translates to:
  /// **'Verildi. Görüntü cihazında işlenir, saklanmaz.'**
  String get faceConsentSettingOn;

  /// No description provided for @faceConsentSettingOff.
  ///
  /// In tr, this message translates to:
  /// **'Verilmedi. Yüz okumaya girdiğinde sorulur.'**
  String get faceConsentSettingOff;

  /// No description provided for @faceConsentWithdrawTitle.
  ///
  /// In tr, this message translates to:
  /// **'Rızayı geri al'**
  String get faceConsentWithdrawTitle;

  /// No description provided for @faceConsentWithdrawBody.
  ///
  /// In tr, this message translates to:
  /// **'Yüz okuma rızan geri alınacak ve şimdiye kadar üretilmiş firaset okumaların silinecek. Diğer okumaların (natal, BaZi, günlük) etkilenmez.'**
  String get faceConsentWithdrawBody;

  /// No description provided for @faceConsentWithdrawConfirm.
  ///
  /// In tr, this message translates to:
  /// **'Geri al ve sil'**
  String get faceConsentWithdrawConfirm;

  /// No description provided for @faceConsentWithdrawn.
  ///
  /// In tr, this message translates to:
  /// **'Rıza geri alındı, {count} okuma silindi.'**
  String faceConsentWithdrawn(int count);

  /// No description provided for @faceOpenSettings.
  ///
  /// In tr, this message translates to:
  /// **'Tekrar dene'**
  String get faceOpenSettings;

  /// No description provided for @faceCameraDeniedHint.
  ///
  /// In tr, this message translates to:
  /// **'İzni reddettiysen, telefon ayarlarından Rytho için kamera iznini açıp buraya dönebilirsin.'**
  String get faceCameraDeniedHint;

  /// No description provided for @save.
  ///
  /// In tr, this message translates to:
  /// **'Kaydet'**
  String get save;

  /// No description provided for @edit.
  ///
  /// In tr, this message translates to:
  /// **'Düzenle'**
  String get edit;

  /// No description provided for @birthRecordRowSubtitle.
  ///
  /// In tr, this message translates to:
  /// **'Tüm okumaların temeli'**
  String get birthRecordRowSubtitle;

  /// No description provided for @languageAndSounds.
  ///
  /// In tr, this message translates to:
  /// **'Dil ve sesler'**
  String get languageAndSounds;

  /// No description provided for @addFriendNeedsUsername.
  ///
  /// In tr, this message translates to:
  /// **'Önce bir kullanıcı adı almalısın — hemen aşağıdaki panelden seçebilirsin.'**
  String get addFriendNeedsUsername;

  /// No description provided for @newConversation.
  ///
  /// In tr, this message translates to:
  /// **'Yeni konu'**
  String get newConversation;

  /// No description provided for @chatEmptyTitle.
  ///
  /// In tr, this message translates to:
  /// **'Rytho ile konuş'**
  String get chatEmptyTitle;

  /// No description provided for @conversationDeleted.
  ///
  /// In tr, this message translates to:
  /// **'Konu silindi.'**
  String get conversationDeleted;

  /// No description provided for @contactMatchSetting.
  ///
  /// In tr, this message translates to:
  /// **'Rehberimden arkadaş öner'**
  String get contactMatchSetting;

  /// No description provided for @contactMatchSettingBody.
  ///
  /// In tr, this message translates to:
  /// **'Numaralar telefonunda özetlenir; rehberin sunucuya gönderilmez. Yalnızca ikiniz de bu ayarı açtıysanız birbirinizi görürsünüz.'**
  String get contactMatchSettingBody;

  /// No description provided for @contactSuggestionsLabel.
  ///
  /// In tr, this message translates to:
  /// **'REHBERİNDEN'**
  String get contactSuggestionsLabel;

  /// No description provided for @contactMatchOffTitle.
  ///
  /// In tr, this message translates to:
  /// **'Rehberindekileri bul'**
  String get contactMatchOffTitle;

  /// No description provided for @contactMatchOffBody.
  ///
  /// In tr, this message translates to:
  /// **'Rehber eşleşmesini açarsan Rytho kullanan tanıdıkların burada görünür. Numaralar cihazında şifrelenir; rehberin hiçbir zaman sunucuda saklanmaz.'**
  String get contactMatchOffBody;

  /// No description provided for @contactMatchEnable.
  ///
  /// In tr, this message translates to:
  /// **'Eşleşmeyi aç'**
  String get contactMatchEnable;

  /// No description provided for @contactMatchPhoneTitle.
  ///
  /// In tr, this message translates to:
  /// **'Önce numaranı doğrula'**
  String get contactMatchPhoneTitle;

  /// No description provided for @contactMatchPhoneBody.
  ///
  /// In tr, this message translates to:
  /// **'Eşleşme telefon numarası üzerinden çalışır. Numaranı doğruladığında tanıdıkların seni bulabilir, sen de onları görebilirsin.'**
  String get contactMatchPhoneBody;

  /// No description provided for @contactMatchVerifyPhone.
  ///
  /// In tr, this message translates to:
  /// **'Numaranı doğrula'**
  String get contactMatchVerifyPhone;

  /// No description provided for @contactMatchPermTitle.
  ///
  /// In tr, this message translates to:
  /// **'Rehber izni gerekiyor'**
  String get contactMatchPermTitle;

  /// No description provided for @contactMatchPermBody.
  ///
  /// In tr, this message translates to:
  /// **'Tanıdıklarını bulmak için rehber okuma izni gerekli. İzni reddettiysen telefonunun Ayarlar → Uygulamalar → Rytho bölümünden açabilirsin.'**
  String get contactMatchPermBody;

  /// No description provided for @contactMatchRetry.
  ///
  /// In tr, this message translates to:
  /// **'Tekrar dene'**
  String get contactMatchRetry;

  /// No description provided for @contactMatchEmptyBody.
  ///
  /// In tr, this message translates to:
  /// **'Rehberinden kimse henüz görünmüyor. Eşleşme için arkadaşının da Rytho\'da numarasını doğrulamış ve rehber eşleşmesini açmış olması gerekir.'**
  String get contactMatchEmptyBody;

  /// No description provided for @contactsTitle.
  ///
  /// In tr, this message translates to:
  /// **'Rehberin'**
  String get contactsTitle;

  /// No description provided for @contactsSearchHint.
  ///
  /// In tr, this message translates to:
  /// **'Rehberinde ara'**
  String get contactsSearchHint;

  /// No description provided for @contactsActiveSection.
  ///
  /// In tr, this message translates to:
  /// **'Uygulamada'**
  String get contactsActiveSection;

  /// No description provided for @contactsInviteSection.
  ///
  /// In tr, this message translates to:
  /// **'Rytho\'da görünmüyor'**
  String get contactsInviteSection;

  /// No description provided for @contactsInviteFootnote.
  ///
  /// In tr, this message translates to:
  /// **'Numarasını doğrulamamış arkadaşların da burada görünebilir.'**
  String get contactsInviteFootnote;

  /// No description provided for @contactsInvite.
  ///
  /// In tr, this message translates to:
  /// **'Davet et'**
  String get contactsInvite;

  /// No description provided for @contactsAlreadyFriend.
  ///
  /// In tr, this message translates to:
  /// **'Arkadaşın'**
  String get contactsAlreadyFriend;

  /// No description provided for @contactsNoSearchResult.
  ///
  /// In tr, this message translates to:
  /// **'Aramayla eşleşen kişi yok.'**
  String get contactsNoSearchResult;

  /// No description provided for @contactsInviteNeedsUsername.
  ///
  /// In tr, this message translates to:
  /// **'Davet için önce bir kullanıcı adı al.'**
  String get contactsInviteNeedsUsername;

  /// No description provided for @inviteShareMessage.
  ///
  /// In tr, this message translates to:
  /// **'Seni Rytho\'ya davet ediyorum — kişisel kozmik zekân. Beni buradan ekleyebilirsin: {link}'**
  String inviteShareMessage(Object link);

  /// No description provided for @contactsFindEntry.
  ///
  /// In tr, this message translates to:
  /// **'Rehberinden arkadaş bul'**
  String get contactsFindEntry;

  /// No description provided for @contactsFindActive.
  ///
  /// In tr, this message translates to:
  /// **'{count} kişi uygulamada'**
  String contactsFindActive(int count);

  /// No description provided for @contactsFindEnable.
  ///
  /// In tr, this message translates to:
  /// **'Rehber eşleşmesini aç'**
  String get contactsFindEnable;

  /// No description provided for @contactsFindVerifyPhone.
  ///
  /// In tr, this message translates to:
  /// **'Bulmak için numaranı doğrula'**
  String get contactsFindVerifyPhone;

  /// No description provided for @phoneSectionLabel.
  ///
  /// In tr, this message translates to:
  /// **'TELEFON'**
  String get phoneSectionLabel;

  /// No description provided for @phoneNotLinked.
  ///
  /// In tr, this message translates to:
  /// **'Doğrulanmış numara yok'**
  String get phoneNotLinked;

  /// No description provided for @phoneVerifyAction.
  ///
  /// In tr, this message translates to:
  /// **'Doğrula'**
  String get phoneVerifyAction;

  /// No description provided for @phoneChangeAction.
  ///
  /// In tr, this message translates to:
  /// **'Değiştir'**
  String get phoneChangeAction;

  /// No description provided for @phoneVerifyTitle.
  ///
  /// In tr, this message translates to:
  /// **'Telefonunu doğrula'**
  String get phoneVerifyTitle;

  /// No description provided for @phoneVerifyBody.
  ///
  /// In tr, this message translates to:
  /// **'Numaran SMS ile doğrulanır ve hesabına bağlanır. Rehber eşleşmesini açarsan arkadaşların seni bu numarayla bulabilir; numaran hiçbir zaman açık şekilde saklanmaz ve kimseyle paylaşılmaz.'**
  String get phoneVerifyBody;

  /// No description provided for @phoneFieldLabel.
  ///
  /// In tr, this message translates to:
  /// **'Telefon numarası'**
  String get phoneFieldLabel;

  /// No description provided for @phoneSendCode.
  ///
  /// In tr, this message translates to:
  /// **'Kod gönder'**
  String get phoneSendCode;

  /// No description provided for @phoneCodeLabel.
  ///
  /// In tr, this message translates to:
  /// **'SMS kodu'**
  String get phoneCodeLabel;

  /// No description provided for @phoneConfirmCode.
  ///
  /// In tr, this message translates to:
  /// **'Doğrula'**
  String get phoneConfirmCode;

  /// No description provided for @phoneCodeSentTo.
  ///
  /// In tr, this message translates to:
  /// **'{number} numarasına kod gönderildi.'**
  String phoneCodeSentTo(String number);

  /// No description provided for @phoneChangeNumber.
  ///
  /// In tr, this message translates to:
  /// **'Numarayı değiştir'**
  String get phoneChangeNumber;

  /// No description provided for @phoneLinkedDone.
  ///
  /// In tr, this message translates to:
  /// **'Telefonun doğrulandı.'**
  String get phoneLinkedDone;

  /// No description provided for @phoneInvalid.
  ///
  /// In tr, this message translates to:
  /// **'Numarayı ülke koduyla yaz (örn. +905xxxxxxxxx).'**
  String get phoneInvalid;

  /// No description provided for @phoneCodeWrong.
  ///
  /// In tr, this message translates to:
  /// **'Kod yanlış görünüyor, tekrar dene.'**
  String get phoneCodeWrong;

  /// No description provided for @phoneTakenError.
  ///
  /// In tr, this message translates to:
  /// **'Bu numara başka bir hesaba bağlı.'**
  String get phoneTakenError;

  /// No description provided for @phoneTooManyTries.
  ///
  /// In tr, this message translates to:
  /// **'Çok fazla deneme yapıldı. Biraz sonra tekrar dene.'**
  String get phoneTooManyTries;

  /// No description provided for @deviceConflictTitle.
  ///
  /// In tr, this message translates to:
  /// **'Aboneliğin başka bir cihazda'**
  String get deviceConflictTitle;

  /// No description provided for @deviceConflictBody.
  ///
  /// In tr, this message translates to:
  /// **'Rytho+ aboneliğin tek cihazda kullanılabilir ve şu an başka bir cihazda kayıtlı. Bu cihazda devam etmek için yeniden giriş yap; giriş yaptıktan hemen sonra aboneliği bu cihaza taşımak isteyip istemediğin sorulacak.'**
  String get deviceConflictBody;

  /// No description provided for @deviceConflictAction.
  ///
  /// In tr, this message translates to:
  /// **'Giriş ekranına dön'**
  String get deviceConflictAction;

  /// No description provided for @deviceTakeoverTitle.
  ///
  /// In tr, this message translates to:
  /// **'Bu cihazda kullan?'**
  String get deviceTakeoverTitle;

  /// No description provided for @deviceTakeoverBody.
  ///
  /// In tr, this message translates to:
  /// **'Aboneliğin başka bir cihazda kayıtlı. Devralırsan diğer cihaz oturumdan çıkarılır; aboneliğin tek cihazda çalışır.'**
  String get deviceTakeoverBody;

  /// No description provided for @deviceTakeoverConfirm.
  ///
  /// In tr, this message translates to:
  /// **'Bu cihazda kullan'**
  String get deviceTakeoverConfirm;

  /// No description provided for @forceUpdateTitle.
  ///
  /// In tr, this message translates to:
  /// **'Yeni sürüm gerekli'**
  String get forceUpdateTitle;

  /// No description provided for @forceUpdateBody.
  ///
  /// In tr, this message translates to:
  /// **'Rytho\'nun bu sürümü artık desteklenmiyor. Devam etmek için uygulamayı güncelle — yıldızlar bekliyor.'**
  String get forceUpdateBody;

  /// No description provided for @forceUpdateAction.
  ///
  /// In tr, this message translates to:
  /// **'Google Play\'de güncelle'**
  String get forceUpdateAction;

  /// No description provided for @signInMethodsRow.
  ///
  /// In tr, this message translates to:
  /// **'Giriş yöntemleri'**
  String get signInMethodsRow;

  /// No description provided for @signInMethodsTitle.
  ///
  /// In tr, this message translates to:
  /// **'Giriş yöntemleri'**
  String get signInMethodsTitle;

  /// No description provided for @signInMethodsBody.
  ///
  /// In tr, this message translates to:
  /// **'Hesabına birden fazla giriş yolu bağlayabilirsin: hangi yöntemle girersen gir aynı hesaba ulaşırsın.'**
  String get signInMethodsBody;

  /// No description provided for @providerPhone.
  ///
  /// In tr, this message translates to:
  /// **'Telefon'**
  String get providerPhone;

  /// No description provided for @linkAction.
  ///
  /// In tr, this message translates to:
  /// **'Bağla'**
  String get linkAction;

  /// No description provided for @linkAlreadyLinked.
  ///
  /// In tr, this message translates to:
  /// **'Bu giriş yöntemi zaten hesabına bağlı.'**
  String get linkAlreadyLinked;

  /// No description provided for @linkCredentialInUse.
  ///
  /// In tr, this message translates to:
  /// **'Bu kimlik başka bir hesaba bağlı. Önce o hesaptan çözülmesi gerekir.'**
  String get linkCredentialInUse;

  /// No description provided for @linkRequiresRecentLogin.
  ///
  /// In tr, this message translates to:
  /// **'Güvenlik için yakın zamanlı giriş gerekiyor: çıkış yapıp yeniden girdikten sonra tekrar dene.'**
  String get linkRequiresRecentLogin;

  /// No description provided for @linkPasswordDone.
  ///
  /// In tr, this message translates to:
  /// **'Şifre kaydedildi. Artık e-posta ve şifreyle de girebilirsin ✨'**
  String get linkPasswordDone;

  /// No description provided for @linkGoogleDone.
  ///
  /// In tr, this message translates to:
  /// **'Google hesabın bağlandı ✨'**
  String get linkGoogleDone;

  /// No description provided for @setPasswordSection.
  ///
  /// In tr, this message translates to:
  /// **'ŞİFRE OLUŞTUR'**
  String get setPasswordSection;

  /// No description provided for @setPasswordBody.
  ///
  /// In tr, this message translates to:
  /// **'Bir e-posta ve şifre belirlersen Google/Apple olmadan da giriş yapabilirsin.'**
  String get setPasswordBody;

  /// No description provided for @setPasswordAction.
  ///
  /// In tr, this message translates to:
  /// **'Şifreyi kaydet'**
  String get setPasswordAction;

  /// No description provided for @changePasswordSection.
  ///
  /// In tr, this message translates to:
  /// **'ŞİFREYİ DEĞİŞTİR'**
  String get changePasswordSection;

  /// No description provided for @changePasswordBody.
  ///
  /// In tr, this message translates to:
  /// **'Yeni şifreni belirle. Değişiklik anında geçerli olur.'**
  String get changePasswordBody;

  /// No description provided for @changePasswordAction.
  ///
  /// In tr, this message translates to:
  /// **'Şifreyi değiştir'**
  String get changePasswordAction;

  /// No description provided for @purchaseAlreadyOwned.
  ///
  /// In tr, this message translates to:
  /// **'Bu Google hesabında zaten etkin bir abonelik var — satın alımların geri yükleniyor…'**
  String get purchaseAlreadyOwned;

  /// No description provided for @purchaseItemUnavailable.
  ///
  /// In tr, this message translates to:
  /// **'Ürün mağazada bulunamadı. Play Store\'da test kanalına katılan Google hesabının seçili olduğundan emin olup tekrar dene.'**
  String get purchaseItemUnavailable;

  /// No description provided for @purchaseStoreProblem.
  ///
  /// In tr, this message translates to:
  /// **'Google Play şu an satın almayı tamamlayamadı. Birkaç dakika sonra tekrar dene.'**
  String get purchaseStoreProblem;

  /// No description provided for @tokenStoreTitle.
  ///
  /// In tr, this message translates to:
  /// **'Kredi Mağazası'**
  String get tokenStoreTitle;

  /// No description provided for @tokenBalanceLabel.
  ///
  /// In tr, this message translates to:
  /// **'BAKİYEN'**
  String get tokenBalanceLabel;

  /// No description provided for @tokenUnit.
  ///
  /// In tr, this message translates to:
  /// **'kredi'**
  String get tokenUnit;

  /// No description provided for @tokenAllowanceRow.
  ///
  /// In tr, this message translates to:
  /// **'Aylık hak (dönem sonunda yenilenir)'**
  String get tokenAllowanceRow;

  /// No description provided for @tokenPurchasedRow.
  ///
  /// In tr, this message translates to:
  /// **'Satın alınan (aya devreder)'**
  String get tokenPurchasedRow;

  /// No description provided for @tokenRolloverNote.
  ///
  /// In tr, this message translates to:
  /// **'Aylık hakkın dönem sonunda yenilenir ve devretmez; satın aldığın krediler hiç yanmaz.'**
  String get tokenRolloverNote;

  /// No description provided for @tokenPacksHeader.
  ///
  /// In tr, this message translates to:
  /// **'Paketler'**
  String get tokenPacksHeader;

  /// No description provided for @tokenPackAmount.
  ///
  /// In tr, this message translates to:
  /// **'{count} kredi'**
  String tokenPackAmount(int count);

  /// No description provided for @tokenBuy.
  ///
  /// In tr, this message translates to:
  /// **'Satın al'**
  String get tokenBuy;

  /// No description provided for @tokenPurchaseDone.
  ///
  /// In tr, this message translates to:
  /// **'Paket yüklendi. İyi okumalar ✨'**
  String get tokenPurchaseDone;

  /// No description provided for @tokenPacksUnavailable.
  ///
  /// In tr, this message translates to:
  /// **'Paketler şu an listelenemiyor'**
  String get tokenPacksUnavailable;

  /// No description provided for @tokenPacksUnavailableBody.
  ///
  /// In tr, this message translates to:
  /// **'Mağaza bağlantısı kurulamadı. Biraz sonra tekrar dene.'**
  String get tokenPacksUnavailableBody;

  /// No description provided for @tokenCostsNote.
  ///
  /// In tr, this message translates to:
  /// **'Sohbet mesajı 1 · I Ching 2 · ikili dinamik 3 · derin raporlar ve yüz okuma 5 kredi. Daha önce ürettiğin bir rapora yeniden bakmak ücretsizdir.'**
  String get tokenCostsNote;

  /// No description provided for @tokenBalanceChip.
  ///
  /// In tr, this message translates to:
  /// **'{count} kredi'**
  String tokenBalanceChip(int count);

  /// No description provided for @atlasSections.
  ///
  /// In tr, this message translates to:
  /// **'Haritanda ne var'**
  String get atlasSections;

  /// No description provided for @atlasTraitsSubtitle.
  ///
  /// In tr, this message translates to:
  /// **'Element dağılımın'**
  String get atlasTraitsSubtitle;

  /// No description provided for @atlasPlanetsSubtitle.
  ///
  /// In tr, this message translates to:
  /// **'Doğduğun andaki konumlar'**
  String get atlasPlanetsSubtitle;

  /// No description provided for @atlasFullReport.
  ///
  /// In tr, this message translates to:
  /// **'Tam rapor'**
  String get atlasFullReport;

  /// No description provided for @atlasFullReportSubtitle.
  ///
  /// In tr, this message translates to:
  /// **'Rytho\'nun okuması'**
  String get atlasFullReportSubtitle;

  /// No description provided for @atlasAspectsCount.
  ///
  /// In tr, this message translates to:
  /// **'{count, plural, =0{Açı yok} =1{1 açı} other{{count} açı}}'**
  String atlasAspectsCount(int count);

  /// No description provided for @retrogradeCount.
  ///
  /// In tr, this message translates to:
  /// **'{count, plural, =1{1 gezegen retro} other{{count} gezegen retro}}'**
  String retrogradeCount(int count);

  /// No description provided for @genericError.
  ///
  /// In tr, this message translates to:
  /// **'Bir şeyler ters gitti. Tekrar dener misin?'**
  String get genericError;

  /// No description provided for @birthRecordEditBody.
  ///
  /// In tr, this message translates to:
  /// **'Bu bilgiler haritanın temeli: günlük okuman, natal raporun ve sohbetin gördüğü her şey buradan hesaplanıyor. Değiştirirsen okumaların yeniden hesaplanır.'**
  String get birthRecordEditBody;

  /// No description provided for @birthCityEmpty.
  ///
  /// In tr, this message translates to:
  /// **'Doğum şehri boş olamaz.'**
  String get birthCityEmpty;

  /// No description provided for @birthRecordSaved.
  ///
  /// In tr, this message translates to:
  /// **'Doğum kaydın güncellendi. Okumaların yeni haritana göre hesaplanacak.'**
  String get birthRecordSaved;

  /// No description provided for @birthRecordSavedNoChart.
  ///
  /// In tr, this message translates to:
  /// **'Doğum kaydın güncellendi ama haritan şu an hesaplanamadı. Burç rozetlerin bağlantı gelince geri dönecek.'**
  String get birthRecordSavedNoChart;

  /// No description provided for @accountSection.
  ///
  /// In tr, this message translates to:
  /// **'Hesap'**
  String get accountSection;

  /// No description provided for @accountSaved.
  ///
  /// In tr, this message translates to:
  /// **'Hesap bilgilerin güncellendi.'**
  String get accountSaved;

  /// No description provided for @displayNameEmpty.
  ///
  /// In tr, this message translates to:
  /// **'Adın boş olamaz.'**
  String get displayNameEmpty;

  /// No description provided for @usernameChangeNote.
  ///
  /// In tr, this message translates to:
  /// **'Değiştirirsen eski kullanıcı adın serbest kalır ve başkası alabilir.'**
  String get usernameChangeNote;

  /// No description provided for @emailChangeNote.
  ///
  /// In tr, this message translates to:
  /// **'E-posta adresin oturumunun anahtarı; değiştirmek için destekle iletişime geç.'**
  String get emailChangeNote;

  /// No description provided for @signalsSection.
  ///
  /// In tr, this message translates to:
  /// **'Bugün gökyüzünde senin için'**
  String get signalsSection;

  /// No description provided for @signalWhy.
  ///
  /// In tr, this message translates to:
  /// **'Neye dayanıyor?'**
  String get signalWhy;

  /// No description provided for @signalAsk.
  ///
  /// In tr, this message translates to:
  /// **'Rytho\'ya sor'**
  String get signalAsk;

  /// No description provided for @signalAskPrefill.
  ///
  /// In tr, this message translates to:
  /// **'Şu sinyali benim için açar mısın: {headline}'**
  String signalAskPrefill(String headline);

  /// No description provided for @signalUpcoming.
  ///
  /// In tr, this message translates to:
  /// **'En yakın kesinleşme: {date}'**
  String signalUpcoming(String date);

  /// No description provided for @basisSheetTitle.
  ///
  /// In tr, this message translates to:
  /// **'Bu sinyal nereden geliyor?'**
  String get basisSheetTitle;

  /// No description provided for @basisSky.
  ///
  /// In tr, this message translates to:
  /// **'Gökyüzünde'**
  String get basisSky;

  /// No description provided for @basisNatal.
  ///
  /// In tr, this message translates to:
  /// **'Haritanda'**
  String get basisNatal;

  /// No description provided for @basisAspect.
  ///
  /// In tr, this message translates to:
  /// **'Açı'**
  String get basisAspect;

  /// No description provided for @basisOrb.
  ///
  /// In tr, this message translates to:
  /// **'Orb (ölçülen)'**
  String get basisOrb;

  /// No description provided for @basisMovement.
  ///
  /// In tr, this message translates to:
  /// **'Hareket'**
  String get basisMovement;

  /// No description provided for @basisExact.
  ///
  /// In tr, this message translates to:
  /// **'Kesinleşme'**
  String get basisExact;

  /// No description provided for @basisHouse.
  ///
  /// In tr, this message translates to:
  /// **'{house}. ev'**
  String basisHouse(int house);

  /// No description provided for @basisSynthesis.
  ///
  /// In tr, this message translates to:
  /// **'Rytho\'nun yorumu'**
  String get basisSynthesis;

  /// No description provided for @basisFootnote.
  ///
  /// In tr, this message translates to:
  /// **'Buradaki her alan hesaplanmış gökyüzü verisidir: konumlar efemeristen, açı ve orb ölçümden gelir. Rytho\'nun yorumu bu ölçümlerin üzerine kurulur — ölçülmeyen söylenmez.'**
  String get basisFootnote;

  /// No description provided for @relationshipOpen.
  ///
  /// In tr, this message translates to:
  /// **'İlişkiyi incele'**
  String get relationshipOpen;

  /// No description provided for @relationshipOpenSubtitle.
  ///
  /// In tr, this message translates to:
  /// **'İki haritanız nerede kolaylaşıyor, nerede emek istiyor'**
  String get relationshipOpenSubtitle;

  /// No description provided for @relationshipTitle.
  ///
  /// In tr, this message translates to:
  /// **'Sen & {name}'**
  String relationshipTitle(String name);

  /// No description provided for @relationshipBirthMissing.
  ///
  /// In tr, this message translates to:
  /// **'Bu okuma için ikinizin de doğum kaydı gerekiyor. Arkadaşın kaydını tamamladığında burası dolacak.'**
  String get relationshipBirthMissing;

  /// No description provided for @relationshipBasisTitle.
  ///
  /// In tr, this message translates to:
  /// **'Bu eksenin dayanağı'**
  String get relationshipBasisTitle;

  /// No description provided for @atlasSectionAbout.
  ///
  /// In tr, this message translates to:
  /// **'Bana dair'**
  String get atlasSectionAbout;

  /// No description provided for @atlasSectionTime.
  ///
  /// In tr, this message translates to:
  /// **'Zaman'**
  String get atlasSectionTime;

  /// No description provided for @atlasSectionOther.
  ///
  /// In tr, this message translates to:
  /// **'Diğer sistemler'**
  String get atlasSectionOther;

  /// No description provided for @atlasFreeChartNote.
  ///
  /// In tr, this message translates to:
  /// **'Çarkın, yerleşimlerin ve açıların ücretsiz. Rytho\'nun derin okuması Rytho+ ile açılır.'**
  String get atlasFreeChartNote;

  /// No description provided for @relationshipAskPrefill.
  ///
  /// In tr, this message translates to:
  /// **'{name} ile ilişkimizde {axis} ekseni hakkında konuşalım.'**
  String relationshipAskPrefill(String name, String axis);
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
