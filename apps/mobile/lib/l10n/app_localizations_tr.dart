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
  String get skyNow => 'Şu An Gökyüzünde';

  @override
  String get iChing => 'I Ching';

  @override
  String get iChingSubtitle => 'Değişimler Kitabı';

  @override
  String get birthHexagram => 'Doğum Kapısı';

  @override
  String get birthHexagramSubtitle => '64 kapı';

  @override
  String get birthHexagramTitle => 'Doğum Heksagramı';

  @override
  String birthHexagramGateLine(int gate, int line) {
    return 'Kapı $gate · $line. çizgi';
  }

  @override
  String birthHexagramGateOnly(int gate) {
    return 'Kapı $gate';
  }

  @override
  String birthHexagramSunAt(String deg) {
    return 'Doğumda Güneş: $deg°';
  }

  @override
  String birthHexagramBoundary(int a, int b) {
    return 'Doğum saati bilinmediği için kapın $a ya da $b olabilir.';
  }

  @override
  String get birthHexagramLockedBody =>
      'Doğum anındaki Güneş\'in 64 kapı çarkındaki yeri — kalıcı karakter kapın. Rytho+ ile açılır.';

  @override
  String get birthHexagramNote => 'Rytho\'nun kapı okuması';

  @override
  String get birthHexagramGatePassage => 'Kapının Dokusu';

  @override
  String get faceReadingTileSubtitle => 'Firaset sanatı';

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
      'Bir kullanıcı adı seç. Arkadaş eklemek kullanıcı adı ve davet bağlantısıyla olur; istersen Gizlilik bölümünden rehber eşleşmesini de açabilirsin.';

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
  String get birthTimeUnknown => 'Doğum saatimi bilmiyorum';

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
  String get onboardingStage1 => 'Gökyüzü konumlanıyor';

  @override
  String get onboardingStage2 => 'Evler hesaplanıyor';

  @override
  String get onboardingStage3 => 'Haritan çiziliyor';

  @override
  String get bigThreeTitle => 'Göğün sana üç mührü';

  @override
  String get bigThreeSun => 'GÜNEŞ';

  @override
  String get bigThreeMoon => 'AY';

  @override
  String get bigThreeAscendant => 'YÜKSELEN';

  @override
  String get bigThreeStart => 'Yolculuğa başla';

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
  String get iChingQuestionInvalid =>
      'Kâhin bu metinde yorumlayacağı bir soru bulamadı — niyetini kendi yaşamınla ilgili bir cümleyle yaz.';

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
  String iChingQuotaFree(int left, int limit) {
    return 'Bugünkü hak: $left/$limit';
  }

  @override
  String iChingQuotaTokens(int n) {
    return 'Çekim bedeli: $n token';
  }

  @override
  String get iChingJudgmentTitle => 'Hüküm';

  @override
  String get iChingImageTitle => 'İmge';

  @override
  String get iChingMovingTitle => 'Hareketli Çizgiler';

  @override
  String get iChingLiuYaoTitle => 'Liu Yao';

  @override
  String iChingNuclearLabel(String name, int n) {
    return 'çekirdek: $name (#$n)';
  }

  @override
  String get iChingLegend =>
      '○ eski yang (9) · × eski yin (6) — dönen çizgiler';

  @override
  String iChingLineLabel(int n) {
    return '$n. çizgi';
  }

  @override
  String iChingPalaceLabel(String name, int shi, int ying) {
    return 'Saray: $name · özne (shi) $shi. çizgi · karşılık (ying) $ying. çizgi';
  }

  @override
  String get iChingVoidTag => 'boşluk';

  @override
  String get iChingClashTag => 'çarpışma';

  @override
  String iChingDayLabel(String day) {
    return 'Çekim günü: $day';
  }

  @override
  String iChingTrigramsLabel(String lower, String upper) {
    return '$lower altında, $upper üstte';
  }

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
  String get baziStrengthTitle => 'Güç Hükmü';

  @override
  String get baziRatioLabel => 'destek oranı';

  @override
  String get baziFavorable => 'Yararlı elementler';

  @override
  String get baziUnfavorable => 'Yüke dönüşenler';

  @override
  String baziClimateNote(String element) {
    return 'Mevsim iklimi düzenleyici ister: $element';
  }

  @override
  String get baziBasisTitle => 'Hükmün dayanağı';

  @override
  String get baziSrcMonthCommand => 'Ay komutu';

  @override
  String baziSrcRoot(String pillar, String stem) {
    return '$pillar dalındaki $stem kökü';
  }

  @override
  String baziSrcStem(String pillar, String stem) {
    return '$pillar gövdesi $stem';
  }

  @override
  String get baziStarsTitle => 'Yıldızlar (Shen Sha)';

  @override
  String get baziNoStars =>
      'Bu haritada işaretli yıldız yok — yapının kendisi konuşuyor.';

  @override
  String baziLuckStartLabel(int years, int months, String date) {
    return 'İlk dönem: $years yaş $months ay ($date)';
  }

  @override
  String baziThisYear(String label, String tenGod) {
    return 'Bu yılın sütunu: $label ($tenGod)';
  }

  @override
  String get baziCurrentTag => 'şimdi';

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

  @override
  String get faceReadingTitle => 'Yüz Okuma';

  @override
  String get faceGuideNoFace => 'Yüzünü çerçeveye al';

  @override
  String get faceGuideTooFar => 'Biraz yaklaş';

  @override
  String get faceGuideTooClose => 'Biraz uzaklaş';

  @override
  String get faceGuideOffCentre => 'Yüzünü ortala';

  @override
  String get faceGuideTilted => 'Başını dik tut';

  @override
  String get faceGuideReady => 'Hazır — sabit dur';

  @override
  String get faceGuideForehead => 'Alnını aç — saçını geriye al';

  @override
  String get faceScanning => 'Yüz hatların okunuyor';

  @override
  String get faceScanNodes => 'Noktalar yerleşiyor';

  @override
  String get faceScanReading => 'Firaset ile eşleştiriliyor';

  @override
  String get faceCapture => 'Çek';

  @override
  String get faceRetake => 'Yeniden çek';

  @override
  String get faceConsentTitle => 'Yüz okuma için onayın gerekiyor';

  @override
  String get faceConsentBody =>
      'Yüz okuma, kameradan aldığı kareyi ya da galeriden seçtiğin fotoğrafı CİHAZINDA işler. Görüntü sunucuya gönderilmez, hiçbir yerde saklanmaz ve işlem biter bitmez silinir (galeri yolunda uygulamaya verilen kopya silinir; asıl fotoğrafına dokunulmaz). Sunucuya yalnızca yüz hatlarından türetilen oranlar (ör. alın/çene yükseklik oranı) gider; bu sayılar kişiyi tanımaya yaramaz.';

  @override
  String get faceConsentCheckbox =>
      'Yüz görüntümün cihazımda işlenmesine onay veriyorum.';

  @override
  String get faceConsentContinue => 'Onaylıyorum ve devam et';

  @override
  String get faceConsentLearnMore => 'Gizlilik politikasını oku';

  @override
  String get faceCameraDenied =>
      'Kamera izni verilmedi. Yüz okuma için kameraya erişim gerekiyor.';

  @override
  String get faceDetectFailed =>
      'Yüz tespit edilemedi. Işığın yeterli olduğundan ve yüzünün çerçevede olduğundan emin ol.';

  @override
  String get faceReadingHint =>
      'Gelenek der ki: tek bir belirti hüküm vermez. Aşağıdaki okuma bir eğilimdir, kader değildir.';

  @override
  String get faceReadingLockedBody =>
      'Yüz hatlarından mizaç okuması. Görüntü cihazında işlenir, hiçbir yere gönderilmez.';

  @override
  String get faceReadingEntryBody =>
      'Yüzünü tarat, firaset geleneğine göre mizacını oku.';

  @override
  String get faceGalleryButton => 'Galeriden seç';

  @override
  String get faceLensButton => 'Kamerayı çevir';

  @override
  String get faceStillAnalyzing => 'Fotoğraf inceleniyor…';

  @override
  String get faceStillNoFace =>
      'Fotoğrafta yüz bulunamadı. Önden, iyi aydınlatılmış bir fotoğraf dene.';

  @override
  String get faceStillNoLandmarks =>
      'Yüz hatları seçilemedi. Yüzün tam göründüğü, önden bir fotoğraf dene.';

  @override
  String get faceStillSingleFrameNote =>
      'Bu okuma tek bir fotoğraf karesinden ölçüldü; canlı çekim daha kararlı sonuç verir.';

  @override
  String get faceWaitStage1 =>
      'Oranlar geleneğin ölçüleriyle karşılaştırılıyor…';

  @override
  String get faceWaitStage2 => 'Firaset kaynakları taranıyor…';

  @override
  String get faceWaitStage3 => 'Okuman yazılıyor…';

  @override
  String get faceConsentSetting => 'Yüz okuma rızası';

  @override
  String get faceConsentSettingOn =>
      'Verildi. Görüntü cihazında işlenir, saklanmaz.';

  @override
  String get faceConsentSettingOff =>
      'Verilmedi. Yüz okumaya girdiğinde sorulur.';

  @override
  String get faceConsentWithdrawTitle => 'Rızayı geri al';

  @override
  String get faceConsentWithdrawBody =>
      'Yüz okuma rızan geri alınacak ve şimdiye kadar üretilmiş firaset okumaların silinecek. Diğer okumaların (natal, BaZi, günlük) etkilenmez.';

  @override
  String get faceConsentWithdrawConfirm => 'Geri al ve sil';

  @override
  String faceConsentWithdrawn(int count) {
    return 'Rıza geri alındı, $count okuma silindi.';
  }

  @override
  String get faceOpenSettings => 'Tekrar dene';

  @override
  String get faceCameraDeniedHint =>
      'İzni reddettiysen, telefon ayarlarından Rytho için kamera iznini açıp buraya dönebilirsin.';

  @override
  String get save => 'Kaydet';

  @override
  String get edit => 'Düzenle';

  @override
  String get birthRecordRowSubtitle => 'Tüm okumaların temeli';

  @override
  String get languageAndSounds => 'Dil ve sesler';

  @override
  String get addFriendNeedsUsername =>
      'Önce bir kullanıcı adı almalısın — hemen aşağıdaki panelden seçebilirsin.';

  @override
  String get newConversation => 'Yeni konu';

  @override
  String get chatEmptyTitle => 'Rytho ile konuş';

  @override
  String get conversationDeleted => 'Konu silindi.';

  @override
  String get contactMatchSetting => 'Rehberimden arkadaş öner';

  @override
  String get contactMatchSettingBody =>
      'Numaralar telefonunda özetlenir; rehberin sunucuya gönderilmez. Yalnızca ikiniz de bu ayarı açtıysanız birbirinizi görürsünüz.';

  @override
  String get contactSuggestionsLabel => 'REHBERİNDEN';

  @override
  String get phoneSectionLabel => 'TELEFON';

  @override
  String get phoneNotLinked => 'Doğrulanmış numara yok';

  @override
  String get phoneVerifyAction => 'Doğrula';

  @override
  String get phoneChangeAction => 'Değiştir';

  @override
  String get phoneVerifyTitle => 'Telefonunu doğrula';

  @override
  String get phoneVerifyBody =>
      'Numaran SMS ile doğrulanır ve hesabına bağlanır. Rehber eşleşmesini açarsan arkadaşların seni bu numarayla bulabilir; numaran hiçbir zaman açık şekilde saklanmaz ve kimseyle paylaşılmaz.';

  @override
  String get phoneFieldLabel => 'Telefon numarası';

  @override
  String get phoneSendCode => 'Kod gönder';

  @override
  String get phoneCodeLabel => 'SMS kodu';

  @override
  String get phoneConfirmCode => 'Doğrula';

  @override
  String phoneCodeSentTo(String number) {
    return '$number numarasına kod gönderildi.';
  }

  @override
  String get phoneChangeNumber => 'Numarayı değiştir';

  @override
  String get phoneLinkedDone => 'Telefonun doğrulandı.';

  @override
  String get phoneInvalid => 'Numarayı ülke koduyla yaz (örn. +905xxxxxxxxx).';

  @override
  String get phoneCodeWrong => 'Kod yanlış görünüyor, tekrar dene.';

  @override
  String get phoneTakenError => 'Bu numara başka bir hesaba bağlı.';

  @override
  String get phoneTooManyTries =>
      'Çok fazla deneme yapıldı. Biraz sonra tekrar dene.';

  @override
  String get deviceConflictTitle => 'Aboneliğin başka bir cihazda';

  @override
  String get deviceConflictBody =>
      'Rytho+ aboneliğin tek cihazda kullanılabilir ve şu an başka bir cihazda kayıtlı. Bu cihazda devam etmek için yeniden giriş yap; girişte cihazı devralmak isteyip istemediğin sorulacak.';

  @override
  String get deviceConflictAction => 'Giriş ekranına dön';

  @override
  String get deviceTakeoverTitle => 'Bu cihazda kullan?';

  @override
  String get deviceTakeoverBody =>
      'Aboneliğin başka bir cihazda kayıtlı. Devralırsan diğer cihaz oturumdan çıkarılır; aboneliğin tek cihazda çalışır.';

  @override
  String get deviceTakeoverConfirm => 'Bu cihazda kullan';

  @override
  String get tokenStoreTitle => 'Token Mağazası';

  @override
  String get tokenBalanceLabel => 'BAKİYEN';

  @override
  String get tokenUnit => 'token';

  @override
  String get tokenAllowanceRow => 'Aylık hak (dönem sonunda yenilenir)';

  @override
  String get tokenPurchasedRow => 'Satın alınan (aya devreder)';

  @override
  String get tokenRolloverNote =>
      'Aylık hak dönem sonunda yenilenir ve devretmez; satın aldığın tokenlar hiç yanmaz.';

  @override
  String get tokenPacksHeader => 'Paketler';

  @override
  String tokenPackAmount(int count) {
    return '$count token';
  }

  @override
  String get tokenBuy => 'Satın al';

  @override
  String get tokenPurchaseDone => 'Paket yüklendi. İyi okumalar ✨';

  @override
  String get tokenPacksUnavailable => 'Paketler şu an listelenemiyor';

  @override
  String get tokenPacksUnavailableBody =>
      'Mağaza bağlantısı kurulamadı. Biraz sonra tekrar dene.';

  @override
  String get tokenCostsNote =>
      'Sohbet mesajı 1 · I Ching 2 · ikili dinamik 3 · derin raporlar ve yüz okuma 5 token. Daha önce ürettiğin bir rapora yeniden bakmak ücretsizdir.';

  @override
  String tokenBalanceChip(int count) {
    return '$count token';
  }

  @override
  String get atlasSections => 'Haritanda ne var';

  @override
  String get atlasTraitsSubtitle => 'Element dağılımın';

  @override
  String get atlasPlanetsSubtitle => 'Doğduğun andaki konumlar';

  @override
  String get atlasFullReport => 'Tam rapor';

  @override
  String get atlasFullReportSubtitle => 'Rytho\'nun okuması';

  @override
  String atlasAspectsCount(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count açı',
      one: '1 açı',
      zero: 'Açı yok',
    );
    return '$_temp0';
  }

  @override
  String retrogradeCount(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count gezegen retro',
      one: '1 gezegen retro',
    );
    return '$_temp0';
  }

  @override
  String get genericError => 'Bir şeyler ters gitti. Tekrar dener misin?';

  @override
  String get birthRecordEditBody =>
      'Bu bilgiler haritanın temeli: günlük okuman, natal raporun ve sohbetin gördüğü her şey buradan hesaplanıyor. Değiştirirsen okumaların yeniden hesaplanır.';

  @override
  String get birthCityEmpty => 'Doğum şehri boş olamaz.';

  @override
  String get birthRecordSaved =>
      'Doğum kaydın güncellendi. Okumaların yeni haritana göre hesaplanacak.';

  @override
  String get birthRecordSavedNoChart =>
      'Doğum kaydın güncellendi ama haritan şu an hesaplanamadı. Burç rozetlerin bağlantı gelince geri dönecek.';

  @override
  String get accountSection => 'Hesap';

  @override
  String get accountSaved => 'Hesap bilgilerin güncellendi.';

  @override
  String get displayNameEmpty => 'Adın boş olamaz.';

  @override
  String get usernameChangeNote =>
      'Değiştirirsen eski kullanıcı adın serbest kalır ve başkası alabilir.';

  @override
  String get emailChangeNote =>
      'E-posta adresin oturumunun anahtarı; değiştirmek için destekle iletişime geç.';
}
