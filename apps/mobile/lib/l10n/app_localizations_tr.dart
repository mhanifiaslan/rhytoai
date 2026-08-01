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

  @override
  String get chatTitle => 'Rytho AI';

  @override
  String get chatHint => 'Geleceğinle ilgili her şeyi sor...';

  @override
  String get chatEmptyBody =>
      'Haritan, yüzün, kaderin... Aklından geçen her soruyu sor.';

  @override
  String get chatFailed => 'Kozmik bağlantı koptu. Lütfen tekrar dene.';

  @override
  String get suggestCareer => 'Kariyer 💼';

  @override
  String get suggestLove => 'Aşk hayatı ❤️';

  @override
  String get suggestMonth => 'Bu ay beni ne bekliyor?';

  @override
  String get suggestFinance => 'Finansal şans 💰';

  @override
  String get suggestMarriage => 'Evlilik zamanı 💍';

  @override
  String get oracleTitle => 'Kehanet Odası';

  @override
  String get tabIChing => 'I CHING 🪙';

  @override
  String get tabBaZi => 'BAZI 🀄';

  @override
  String get onboardingTitle => 'Doğum Anın';

  @override
  String get onboardingBody =>
      'Haritanın çizilebilmesi için gökyüzünün o anki dizilişi gerekir. Saat ne kadar kesinse, yükselen o kadar doğrudur.';

  @override
  String get onboardingCity => 'Doğum şehri';

  @override
  String get genderFemale => 'Kadın';

  @override
  String get genderMale => 'Erkek';

  @override
  String get genderOther => 'Diğer';

  @override
  String get onboardingSubmit => 'Haritamı çiz ✨';

  @override
  String get onboardingFailed => 'Kayıt başarısız.';

  @override
  String get atlasTitle => 'Doğum Haritası Analizi';

  @override
  String get appHeadline => 'Kişisel Kozmik Zekân';

  @override
  String get consentNote =>
      'Devam ederek gizlilik ilkelerini kabul etmiş olursun.\nYorumlar içgörü amaçlıdır; tıbbi/finansal tavsiye değildir.';

  @override
  String get authNameRequired => 'Adını yaz.';

  @override
  String get authInvalidEmail => 'Geçerli bir e-posta yaz.';

  @override
  String get authWrongCredentials => 'E-posta veya şifre hatalı.';

  @override
  String get authEmailInUse => 'Bu e-posta zaten kayıtlı. Giriş yapmayı dene.';

  @override
  String get authWeakPassword => 'Şifre en az 6 karakter olmalı.';

  @override
  String get authTooManyRequests =>
      'Çok fazla deneme yapıldı. Biraz sonra tekrar dene.';

  @override
  String get authDisabled => 'E-posta ile giriş şu an kapalı.';

  @override
  String get authNetwork => 'Bağlantı kurulamadı. İnternetini kontrol et.';

  @override
  String get authFailed => 'Bir şeyler ters gitti. Tekrar dene.';

  @override
  String get displayName => 'Adın';

  @override
  String get passwordRepeat => 'Şifre (tekrar)';

  @override
  String get passwordsDoNotMatch => 'Şifreler eşleşmiyor.';

  @override
  String get enterEmailFirst => 'Önce e-posta adresini yaz.';

  @override
  String get resetLinkSent => 'Şifre sıfırlama bağlantısı gönderildi.';

  @override
  String get nameLabel => 'Ad';

  @override
  String get signAries => 'Koç';

  @override
  String get signTaurus => 'Boğa';

  @override
  String get signGemini => 'İkizler';

  @override
  String get signCancer => 'Yengeç';

  @override
  String get signLeo => 'Aslan';

  @override
  String get signVirgo => 'Başak';

  @override
  String get signLibra => 'Terazi';

  @override
  String get signScorpio => 'Akrep';

  @override
  String get signSagittarius => 'Yay';

  @override
  String get signCapricorn => 'Oğlak';

  @override
  String get signAquarius => 'Kova';

  @override
  String get signPisces => 'Balık';

  @override
  String get atlasPlanetPositions => 'Gezegen Konumları';

  @override
  String get atlasTraits => 'Kişilik Özellikleri';

  @override
  String get atlasAspects => 'Açılar';

  @override
  String get traitDetermination => 'Kararlılık';

  @override
  String get traitCommunication => 'İletişim';

  @override
  String get traitSensitivity => 'Duyarlılık';

  @override
  String moonIllumination(Object percent) {
    return 'aydınlanma %$percent';
  }

  @override
  String get reportPostTitle => 'GÖNDERİYİ ŞİKAYET ET';

  @override
  String get reportUserTitle => 'KULLANICIYI ŞİKAYET ET';

  @override
  String get reportNote => 'Şikayetin ekibimiz tarafından incelenir.';

  @override
  String get reportReasonSpam => 'Spam veya yanıltıcı içerik';

  @override
  String get reportReasonHarassment => 'Hakaret veya taciz';

  @override
  String get reportReasonInappropriate => 'Uygunsuz / rahatsız edici içerik';

  @override
  String get reportReasonOther => 'Diğer';

  @override
  String get reportSubmitted =>
      'Şikayetin alındı; en kısa sürede incelenecek. Teşekkürler.';

  @override
  String get reportFailed => 'Şikayet gönderilemedi.';

  @override
  String get recordLabel => '✨ Kayıt';

  @override
  String get aFriend => 'Bir arkadaşın';

  @override
  String get iChingIntro =>
      '3000 yıllık 64 heksagram matrisi. Sorunu yaz; paralar gerçek olasılık dağılımıyla atılır, hareketli çizgiler geleceğe köprü kurar.';

  @override
  String get iChingQuestionHint => 'Sorun nedir?';

  @override
  String get iChingMethodCoins => 'Üç Para 🪙';

  @override
  String get iChingMethodYarrow => 'Civanperçemi 🌿';

  @override
  String get iChingCastAction => 'Çekimi yap';

  @override
  String get iChingQuestionRequired => 'Önce kalbindeki soruyu yaz.';

  @override
  String get iChingCastFailed => 'Çekim yapılamadı.';

  @override
  String get iChingCoinsInAir => 'Paralar havada...';

  @override
  String iChingHexagramLabel(Object number) {
    return 'HEKSAGRAM $number';
  }

  @override
  String iChingTransformedTo(Object name, Object number) {
    return '→ dönüşüm: $name (#$number)';
  }

  @override
  String get iChingOracleNote => 'Rytho\'nun kehanet notu';

  @override
  String get baziHeadline => 'Kaderin Dört Sütunu';

  @override
  String baziChineseSign(Object animal, Object dayMaster) {
    return 'Çin burcun: $animal · $dayMaster';
  }

  @override
  String get baziFourPillars => 'Dört Sütun';

  @override
  String get baziPillarHour => 'SAAT';

  @override
  String get baziPillarDay => 'GÜN';

  @override
  String get baziPillarMonth => 'AY';

  @override
  String get baziPillarYear => 'YIL';

  @override
  String get baziElementBalance => 'Element Terazisi';

  @override
  String baziNourish(Object elements) {
    return 'Beslenecek element: $elements';
  }

  @override
  String get baziLuckPillars => 'Şans Sütunları (Da Yun)';

  @override
  String baziAgeRange(Object from, Object to) {
    return '$from–$to YAŞ';
  }

  @override
  String get baziFateNote => 'Rytho\'nun kader notu';

  @override
  String get traitEnergy => 'Enerji';

  @override
  String get traitPracticality => 'Pratiklik';

  @override
  String get defaultUserName => 'Gezgin';

  @override
  String retrogradeChip(Object planet) {
    return '$planet retro';
  }

  @override
  String get atlasReadingNote => '✨ Rytho\'nun okuma notu';

  @override
  String get notifications => 'Bildirimler';

  @override
  String get notifyDaily => 'Günlük okuma';

  @override
  String get notifyDailyBody =>
      'Sabahları bugünün gökyüzü hazır olduğunda haber ver.';

  @override
  String get notifyStreak => 'Seri hatırlatması';

  @override
  String get notifyStreakBody =>
      'Akşam, serin kırılmadan önce kısa bir hatırlatma.';

  @override
  String get notifyFriends => 'Arkadaş tepkileri';

  @override
  String get notifyFriendsBody =>
      'Bir arkadaşın sana tepki gönderdiğinde haber ver.';

  @override
  String get quietHours => 'Sessiz saatler';

  @override
  String get quietHoursBody => 'Bu aralıkta bildirim gönderilmez.';

  @override
  String quietHoursRange(Object from, Object to) {
    return '$from:00 – $to:00';
  }

  @override
  String get quietHoursOff => 'Kapalı';

  @override
  String get notificationsDisabledHint =>
      'Bildirimler cihaz ayarlarından kapalı. Açmak için sistem ayarlarına git.';

  @override
  String get enableNotifications => 'Bildirimleri aç';

  @override
  String get deleteAccount => 'Hesabı sil';

  @override
  String get deleteAccountTitle => 'Hesabını silmek üzeresin';

  @override
  String get deleteAccountBody =>
      'Bu işlem geri alınamaz. Silinecekler: doğum kaydın, sohbetten biriktirdiğimiz notlar, arkadaşlıkların, kullanıcı adın ve sana özel üretilmiş tüm okumalar.';

  @override
  String get deleteAccountKeeps =>
      'Gönderdiğin şikayet kayıtları saklanır; başkalarının güvenliğiyle ilgili oldukları için silinmez.';

  @override
  String get deleteAccountSubscription =>
      'Aboneliğin varsa uygulama mağazandan ayrıca iptal etmelisin; hesabı silmek aboneliği durdurmaz.';

  @override
  String get deleteAccountConfirmHint => 'Onaylamak için SİL yaz';

  @override
  String get deleteAccountConfirmWord => 'SİL';

  @override
  String get deleteAccountAction => 'Hesabımı kalıcı olarak sil';

  @override
  String get deleteAccountFailed => 'Hesap silinemedi. Lütfen tekrar dene.';

  @override
  String get deleteAccountReauth =>
      'Güvenlik için tekrar giriş yapman gerekiyor. Çıkış yapıp yeniden giriş yaptıktan sonra bu işlemi tekrarla.';

  @override
  String get cancel => 'Vazgeç';

  @override
  String get insightDisclaimer =>
      'Rytho gerçek gökyüzü hesabına dayanır ama yorum bir öngörü yöntemi değildir. Okumalar içgörü içindir; tıbbi, hukuki veya finansal tavsiye yerine geçmez. 13 yaş ve üzeri içindir.';

  @override
  String get shareReading => 'Paylaş';

  @override
  String get shareCardTagline => 'gerçek gökyüzü hesabıyla';

  @override
  String get shareFailed => 'Paylaşım kartı oluşturulamadı.';

  @override
  String get signInWithApple => 'Apple ile giriş';

  @override
  String get consentPrefix => 'Devam ederek ';

  @override
  String get consentAnd => ' ve ';

  @override
  String get consentSuffix => ' metinlerini kabul etmiş olursun.';

  @override
  String get insightNote =>
      'Yorumlar içgörü amaçlıdır; tıbbi, hukuki veya finansal tavsiye değildir.';

  @override
  String get ageConfirm => '13 yaşından büyüğüm';

  @override
  String get ageRequired =>
      'Devam etmek için yaş beyanını onaylaman gerekiyor.';

  @override
  String get passwordRuleHint => 'En az 8 karakter, harf ve rakam içermeli.';

  @override
  String get passwordTooShort => 'Şifre en az 8 karakter olmalı.';

  @override
  String get passwordTooSimple => 'Şifre harf ve rakam (veya sembol) içermeli.';

  @override
  String verificationSent(Object email) {
    return 'Doğrulama bağlantısı $email adresine gönderildi. Gelen kutunu kontrol et.';
  }

  @override
  String get resetLinkSentNeutral =>
      'Bu adres kayıtlıysa şifre sıfırlama bağlantısı gönderildi.';

  @override
  String get useGoogleInstead =>
      'Giriş yapılamadı. Şifren hatalı olabilir ya da bu hesap Google/Apple ile açılmış olabilir — aşağıdaki düğmeleri dene.';
}
