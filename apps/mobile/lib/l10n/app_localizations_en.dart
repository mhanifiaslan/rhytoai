// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTagline =>
      'Ancient wisdom, met with precise sky calculation.\nYour chart is drawn; your path lights up. ✨';

  @override
  String get signInWithGoogle => 'Sign in with Google';

  @override
  String get orDivider => 'or';

  @override
  String get signIn => 'Sign in';

  @override
  String get signUp => 'Sign up';

  @override
  String get email => 'Email';

  @override
  String get password => 'Password';

  @override
  String get forgotPassword => 'Forgot password';

  @override
  String get tabSky => 'Sky';

  @override
  String get tabAtlas => 'Atlas';

  @override
  String get tabFriends => 'Friends';

  @override
  String get tabProfile => 'Profile';

  @override
  String get greetingMorning => 'Good morning';

  @override
  String get greetingDay => 'Good afternoon';

  @override
  String get greetingEvening => 'Good evening';

  @override
  String get greetingNight => 'Good night';

  @override
  String get todaysInsight => 'Today\'s Insight';

  @override
  String signToday(String sign) {
    return '$sign · today';
  }

  @override
  String get skyNow => 'In the Sky Right Now';

  @override
  String get iChing => 'I Ching';

  @override
  String get iChingSubtitle => 'Book of Changes';

  @override
  String get faceReadingTileSubtitle => 'The art of firasa';

  @override
  String get baZi => 'BaZi';

  @override
  String get baZiSubtitle => 'Four Pillars';

  @override
  String get personalReadingLocked => 'Your personal daily reading';

  @override
  String get personalReadingLockedBody =>
      'With Rytho+, readings are built from your own chart.';

  @override
  String personalReadingLockedBodyWithSign(String sign) {
    return 'The reading above is for every $sign. With Rytho+ it also accounts for your Moon and Rising.';
  }

  @override
  String get personalReadingTitle => 'For you';

  @override
  String get natalLockedTitle => 'Birth chart analysis';

  @override
  String get natalLockedBody =>
      'The full reading of your placements, houses and aspects unlocks with Rytho+.';

  @override
  String get baziLockedTitle => 'BaZi — Four Pillars';

  @override
  String get baziLockedBody =>
      'Day Master, Ten Gods and luck pillars unlock with Rytho+.';

  @override
  String get friendsTitle => 'Friends';

  @override
  String get addFriend => 'Add friend';

  @override
  String get usernameLabel => 'USERNAME';

  @override
  String get usernameHeadline => 'Let your friends find you';

  @override
  String get usernameBody =>
      'Pick a username. Friends are added by username or invite link; you can also enable contact matching under Privacy if you like.';

  @override
  String get usernameHint => 'username';

  @override
  String get claimUsername => 'Claim username';

  @override
  String get usernameInvalid =>
      '3-20 characters; lowercase letters, numbers and underscore only.';

  @override
  String get usernameEmpty => 'Username can\'t be empty.';

  @override
  String get usernameTaken => 'That username is taken — try another.';

  @override
  String get youLabel => 'YOU';

  @override
  String get streakVisibleOn =>
      'Friends can see your streak and whether you\'ve read today.';

  @override
  String get streakVisibleOff => 'Your streak is hidden from friends.';

  @override
  String get copyInviteLink => 'Copy invite link';

  @override
  String get inviteLinkCopied => 'Invite link copied.';

  @override
  String get shareInviteInstead => 'Share my invite link instead';

  @override
  String get sendInvite => 'Send invite';

  @override
  String inviteSent(String username) {
    return 'Invite sent to @$username.';
  }

  @override
  String userNotFound(String username) {
    return '@$username not found.';
  }

  @override
  String get cannotAddSelf => 'You can\'t add yourself.';

  @override
  String get inboxLabel => 'SENT TO YOU';

  @override
  String get noFriendsYet => 'No one here yet';

  @override
  String get noFriendsBody =>
      'Add a friend by username — see each other\'s streaks and read the dynamic between you every day.';

  @override
  String get incomingRequests => 'Incoming invites';

  @override
  String get yourFriends => 'Your friends';

  @override
  String get pendingInvites => 'Invites awaiting a reply';

  @override
  String get accept => 'Accept';

  @override
  String get ignore => 'Ignore';

  @override
  String get pending => 'Pending';

  @override
  String get withdrawInvite => 'Withdraw invite';

  @override
  String get readToday => 'Has read today';

  @override
  String get notReadToday => 'Hasn\'t read yet today';

  @override
  String get streakHidden => 'Streak hidden';

  @override
  String get friendLabel => 'YOUR FRIEND';

  @override
  String get streakHiddenByFriend => 'Keeps their streak private';

  @override
  String get readTodayDone => 'Has done today\'s reading';

  @override
  String get dyadLabel => 'BETWEEN YOU TODAY';

  @override
  String get dyadDisclaimer =>
      'This reading holds for today only and changes tomorrow. We don\'t give a fixed compatibility score.';

  @override
  String get dyadFailed => 'Couldn\'t load the reading.';

  @override
  String get sendReaction => 'Send a reaction';

  @override
  String get sendReactionBody =>
      'Pick one of the ready reactions — no writing, just a small hello.';

  @override
  String reactionSent(String emoji) {
    return '$emoji sent.';
  }

  @override
  String get removeFriend => 'Remove friend';

  @override
  String get blockUser => 'Block';

  @override
  String get reportUser => 'Report';

  @override
  String get reactionStreak => 'Keep the streak';

  @override
  String get reactionThinkingOfYou => 'Thinking of you';

  @override
  String get reactionShine => 'You\'re shining';

  @override
  String get reactionKeepGoing => 'Keep going';

  @override
  String get reactionCongrats => 'Congratulations';

  @override
  String get reactionSameFrequency => 'Same frequency';

  @override
  String get reactionGoodNight => 'Good night';

  @override
  String get reactionCheckToday => 'Check today';

  @override
  String get paywallTitle => 'Rytho+';

  @override
  String get paywallHeadline =>
      'The stars are the same for everyone.\nYou are not.';

  @override
  String get paywallBody =>
      'Your daily sign reading and the real sky data stay open on the free tier, always. Rytho+ builds every reading from your own chart.';

  @override
  String get paywallContinue => 'Continue with Rytho+';

  @override
  String get paywallChoosePlan => 'Choose a plan';

  @override
  String get restorePurchases => 'Restore purchases';

  @override
  String get noActiveSubscription => 'No active subscription found to restore.';

  @override
  String get purchaseFailed => 'The purchase couldn\'t be completed.';

  @override
  String get billingUnavailable => 'Purchases aren\'t available right now';

  @override
  String get billingNoPackages => 'No packages are configured in the store.';

  @override
  String get billingNotConfigured =>
      'Subscription keys aren\'t set in this build.';

  @override
  String get planWeekly => 'Weekly';

  @override
  String get planMonthly => 'Monthly';

  @override
  String get planAnnual => 'Annual';

  @override
  String get bestValue => 'BEST VALUE';

  @override
  String trialThenPrice(int count, String unit, String price) {
    return '$count $unit free, then $price';
  }

  @override
  String get unitDay => 'days';

  @override
  String get unitWeek => 'weeks';

  @override
  String get unitMonth => 'months';

  @override
  String get unitYear => 'years';

  @override
  String get subscriptionTerms =>
      'Your subscription renews automatically unless cancelled at least 24 hours before the period ends. If there is a free trial and you cancel before it ends, you won\'t be charged. You can cancel in your device\'s store account settings.';

  @override
  String get benefitDailyTitle => 'A daily reading built for you';

  @override
  String get benefitDailyBody =>
      'Your natal chart collided with today\'s sky — not a generic sun-sign horoscope.';

  @override
  String get benefitNatalTitle => 'Full birth chart report';

  @override
  String get benefitNatalBody =>
      'Planets, houses and aspects — not a one-off surface summary.';

  @override
  String get benefitDyadTitle => 'Daily dynamic with your friends';

  @override
  String get benefitDyadBody =>
      'A shared reading that renews each day. No fixed compatibility score.';

  @override
  String get benefitChatTitle => 'Unlimited chat';

  @override
  String get benefitChatBody => 'The more Rytho knows you, the deeper it goes.';

  @override
  String get benefitBaziTitle => 'BaZi and synastry';

  @override
  String get benefitBaziBody =>
      'Four Pillars analysis and chart-to-chart comparison.';

  @override
  String get profileTitle => 'Profile';

  @override
  String get settings => 'Settings';

  @override
  String get sounds => 'Sounds';

  @override
  String get privacy => 'Privacy';

  @override
  String get streakVisibleSetting => 'Let friends see my streak';

  @override
  String get streakVisibleSettingBody =>
      'When off, neither your streak nor whether you\'ve read today is shared.';

  @override
  String get language => 'Language';

  @override
  String get languageSystem => 'System language';

  @override
  String get languageTurkish => 'Türkçe';

  @override
  String get languageEnglish => 'English';

  @override
  String get about => 'About';

  @override
  String get aboutBody =>
      'Rytho joins Western astrology, BaZi and the I Ching to precise ephemeris calculation. Readings are for insight; they are not medical, legal or financial advice.';

  @override
  String get ephemerisCredit => 'Ephemeris: Swiss Ephemeris © Astrodienst AG';

  @override
  String get privacyPolicy => 'Privacy Policy';

  @override
  String get termsOfUse => 'Terms of Use';

  @override
  String get signOut => 'Sign out';

  @override
  String get dailyStreak => 'Daily Streak';

  @override
  String streakDays(int count) {
    return '$count days';
  }

  @override
  String get streakBody =>
      'Open your daily reading every day and watch the streak grow.';

  @override
  String get birthRecord => 'Birth Record';

  @override
  String get birthDate => 'Date';

  @override
  String get birthTime => 'Time';

  @override
  String get birthTimeUnknown => 'I don\'t know my birth time';

  @override
  String get birthCity => 'City';

  @override
  String get retry => 'Try again';

  @override
  String get errorGeneric =>
      'Something unexpected happened. Please try again shortly.';

  @override
  String get errorConnection =>
      'Couldn\'t connect. Check your internet and try again.';

  @override
  String get errorSkyUnavailable => 'The sky is out of reach right now.';

  @override
  String get promoTitle => 'Go beyond the stars ✨';

  @override
  String get promoBody => 'Explore the full analysis of your birth chart.';

  @override
  String get promoAction => 'Explore';

  @override
  String get chatTitle => 'Rytho AI';

  @override
  String get chatHint => 'Ask anything about what\'s ahead...';

  @override
  String get chatEmptyBody =>
      'Your chart, your patterns, your path — ask whatever is on your mind.';

  @override
  String get chatFailed => 'The connection dropped. Please try again.';

  @override
  String get suggestCareer => 'Career 💼';

  @override
  String get suggestLove => 'Love life ❤️';

  @override
  String get suggestMonth => 'What does this month hold?';

  @override
  String get suggestFinance => 'Money and work 💰';

  @override
  String get suggestMarriage => 'Commitment 💍';

  @override
  String get oracleTitle => 'Oracle Room';

  @override
  String get tabIChing => 'I CHING 🪙';

  @override
  String get tabBaZi => 'BAZI 🀄';

  @override
  String get onboardingTitle => 'Your Birth Moment';

  @override
  String get onboardingBody =>
      'Your chart needs the exact arrangement of the sky at that moment. The more precise the time, the more accurate your rising sign.';

  @override
  String get onboardingCity => 'Birth city';

  @override
  String get genderFemale => 'Female';

  @override
  String get genderMale => 'Male';

  @override
  String get genderOther => 'Other';

  @override
  String get onboardingSubmit => 'Draw my chart ✨';

  @override
  String get onboardingFailed => 'Couldn\'t save your details.';

  @override
  String get atlasTitle => 'Birth Chart Analysis';

  @override
  String get appHeadline => 'Your Personal Cosmic Intelligence';

  @override
  String get consentNote =>
      'By continuing you accept our privacy terms.\nReadings are for insight; they are not medical or financial advice.';

  @override
  String get authNameRequired => 'Enter your name.';

  @override
  String get authInvalidEmail => 'Enter a valid email address.';

  @override
  String get authWrongCredentials => 'Email or password is incorrect.';

  @override
  String get authEmailInUse =>
      'That email is already registered. Try signing in.';

  @override
  String get authWeakPassword => 'Password must be at least 6 characters.';

  @override
  String get authTooManyRequests =>
      'Too many attempts. Please try again shortly.';

  @override
  String get authDisabled => 'Email sign-in is currently unavailable.';

  @override
  String get authNetwork => 'Couldn\'t connect. Check your internet.';

  @override
  String get authFailed => 'Something went wrong. Please try again.';

  @override
  String get displayName => 'Your name';

  @override
  String get passwordRepeat => 'Password (repeat)';

  @override
  String get passwordsDoNotMatch => 'Passwords don\'t match.';

  @override
  String get enterEmailFirst => 'Enter your email address first.';

  @override
  String get resetLinkSent => 'Password reset link sent.';

  @override
  String get nameLabel => 'Name';

  @override
  String get signAries => 'Aries';

  @override
  String get signTaurus => 'Taurus';

  @override
  String get signGemini => 'Gemini';

  @override
  String get signCancer => 'Cancer';

  @override
  String get signLeo => 'Leo';

  @override
  String get signVirgo => 'Virgo';

  @override
  String get signLibra => 'Libra';

  @override
  String get signScorpio => 'Scorpio';

  @override
  String get signSagittarius => 'Sagittarius';

  @override
  String get signCapricorn => 'Capricorn';

  @override
  String get signAquarius => 'Aquarius';

  @override
  String get signPisces => 'Pisces';

  @override
  String get atlasPlanetPositions => 'Planetary Positions';

  @override
  String get atlasTraits => 'Character Traits';

  @override
  String get atlasAspects => 'Aspects';

  @override
  String get traitDetermination => 'Determination';

  @override
  String get traitCommunication => 'Communication';

  @override
  String get traitSensitivity => 'Sensitivity';

  @override
  String moonIllumination(Object percent) {
    return '$percent% illuminated';
  }

  @override
  String get reportPostTitle => 'REPORT THIS POST';

  @override
  String get reportUserTitle => 'REPORT THIS USER';

  @override
  String get reportNote => 'Our team reviews every report.';

  @override
  String get reportReasonSpam => 'Spam or misleading content';

  @override
  String get reportReasonHarassment => 'Insults or harassment';

  @override
  String get reportReasonInappropriate => 'Inappropriate or disturbing content';

  @override
  String get reportReasonOther => 'Something else';

  @override
  String get reportSubmitted =>
      'Report received — we\'ll look into it shortly. Thank you.';

  @override
  String get reportFailed => 'The report couldn\'t be sent.';

  @override
  String get recordLabel => '✨ Your details';

  @override
  String get aFriend => 'A friend';

  @override
  String get iChingIntro =>
      'The 64-hexagram matrix, three thousand years old. Write your question; the coins fall on real probability, and the moving lines bridge to what comes next.';

  @override
  String get iChingQuestionHint => 'What\'s on your mind?';

  @override
  String get iChingMethodCoins => 'Three Coins 🪙';

  @override
  String get iChingMethodYarrow => 'Yarrow Stalks 🌿';

  @override
  String get iChingCastAction => 'Cast';

  @override
  String get iChingQuestionRequired => 'Write your question first.';

  @override
  String get iChingCoinsInAir => 'Coins in the air...';

  @override
  String iChingHexagramLabel(Object number) {
    return 'HEXAGRAM $number';
  }

  @override
  String iChingTransformedTo(Object name, Object number) {
    return '→ changing into: $name (#$number)';
  }

  @override
  String get iChingOracleNote => 'Rytho\'s note on the cast';

  @override
  String get baziHeadline => 'The Four Pillars of Destiny';

  @override
  String baziChineseSign(Object animal, Object dayMaster) {
    return 'Your Chinese sign: $animal · $dayMaster';
  }

  @override
  String get baziFourPillars => 'Four Pillars';

  @override
  String get baziPillarHour => 'HOUR';

  @override
  String get baziPillarDay => 'DAY';

  @override
  String get baziPillarMonth => 'MONTH';

  @override
  String get baziPillarYear => 'YEAR';

  @override
  String get baziElementBalance => 'Elemental Balance';

  @override
  String baziNourish(Object elements) {
    return 'Element to nourish: $elements';
  }

  @override
  String get baziLuckPillars => 'Luck Pillars (Da Yun)';

  @override
  String get baziStrengthTitle => 'Strength Verdict';

  @override
  String get baziRatioLabel => 'support ratio';

  @override
  String get baziFavorable => 'Favorable elements';

  @override
  String get baziUnfavorable => 'Turning into burden';

  @override
  String baziClimateNote(String element) {
    return 'The season\'s climate calls for a regulator: $element';
  }

  @override
  String get baziBasisTitle => 'Basis of the verdict';

  @override
  String get baziSrcMonthCommand => 'Month command';

  @override
  String baziSrcRoot(String pillar, String stem) {
    return '$stem root in the $pillar branch';
  }

  @override
  String baziSrcStem(String pillar, String stem) {
    return '$stem stem in the $pillar';
  }

  @override
  String get baziStarsTitle => 'Stars (Shen Sha)';

  @override
  String get baziNoStars =>
      'No marked stars in this chart — the structure itself speaks.';

  @override
  String baziLuckStartLabel(int years, int months, String date) {
    return 'First period: age ${years}y ${months}m ($date)';
  }

  @override
  String baziThisYear(String label, String tenGod) {
    return 'This year\'s pillar: $label ($tenGod)';
  }

  @override
  String get baziCurrentTag => 'now';

  @override
  String baziAgeRange(Object from, Object to) {
    return 'AGE $from–$to';
  }

  @override
  String get baziFateNote => 'Rytho\'s note on your chart';

  @override
  String get traitEnergy => 'Energy';

  @override
  String get traitPracticality => 'Practicality';

  @override
  String get defaultUserName => 'Traveller';

  @override
  String retrogradeChip(Object planet) {
    return '$planet retrograde';
  }

  @override
  String get atlasReadingNote => '✨ Rytho\'s note on your chart';

  @override
  String get notifications => 'Notifications';

  @override
  String get notifyDaily => 'Daily reading';

  @override
  String get notifyDailyBody =>
      'Let me know each morning when today\'s sky is ready.';

  @override
  String get notifyStreak => 'Streak reminder';

  @override
  String get notifyStreakBody =>
      'A short evening nudge before your streak breaks.';

  @override
  String get notifyFriends => 'Friend reactions';

  @override
  String get notifyFriendsBody =>
      'Let me know when a friend sends you a reaction.';

  @override
  String get quietHours => 'Quiet hours';

  @override
  String get quietHoursBody => 'No notifications are sent during this window.';

  @override
  String quietHoursRange(Object from, Object to) {
    return '$from – $to';
  }

  @override
  String get quietHoursOff => 'Off';

  @override
  String get notificationsDisabledHint =>
      'Notifications are off in your device settings. Turn them on there to receive them.';

  @override
  String get enableNotifications => 'Turn on notifications';

  @override
  String get deleteAccount => 'Delete account';

  @override
  String get deleteAccountTitle => 'You\'re about to delete your account';

  @override
  String get deleteAccountBody =>
      'This cannot be undone. We will delete your birth record, the notes we built up from your conversations, your friendships, your username and every reading generated for you.';

  @override
  String get deleteAccountKeeps =>
      'Reports you filed are kept — they concern other people\'s safety, so we do not remove them.';

  @override
  String get deleteAccountSubscription =>
      'If you have a subscription you must also cancel it in your app store; deleting the account does not stop the billing.';

  @override
  String get deleteAccountConfirmHint => 'Type DELETE to confirm';

  @override
  String get deleteAccountConfirmWord => 'DELETE';

  @override
  String get deleteAccountAction => 'Permanently delete my account';

  @override
  String get deleteAccountFailed =>
      'The account could not be deleted. Please retry.';

  @override
  String get deleteAccountReauth =>
      'For security you need to sign in again. Sign out, sign back in, and repeat this step.';

  @override
  String get cancel => 'Cancel';

  @override
  String get insightDisclaimer =>
      'Rytho is built on real ephemeris calculation, but interpretation is not a method of prediction. Readings are for insight; they are not medical, legal or financial advice. For ages 13 and up.';

  @override
  String get shareReading => 'Share';

  @override
  String get shareCardTagline => 'from real ephemeris calculation';

  @override
  String get shareFailed => 'The share card could not be created.';

  @override
  String get signInWithApple => 'Sign in with Apple';

  @override
  String get consentPrefix => 'By continuing you accept the ';

  @override
  String get consentAnd => ' and the ';

  @override
  String get consentSuffix => '.';

  @override
  String get insightNote =>
      'Readings are for insight; they are not medical, legal or financial advice.';

  @override
  String get ageConfirm => 'I am over 13 years old';

  @override
  String get ageRequired => 'Please confirm your age to continue.';

  @override
  String get passwordRuleHint =>
      'At least 8 characters, with letters and numbers.';

  @override
  String get passwordTooShort => 'Password must be at least 8 characters.';

  @override
  String get passwordTooSimple =>
      'Password must mix letters with numbers or symbols.';

  @override
  String verificationSent(Object email) {
    return 'A verification link was sent to $email. Please check your inbox.';
  }

  @override
  String get resetLinkSentNeutral =>
      'If this address is registered, a reset link has been sent.';

  @override
  String get useGoogleInstead =>
      'Sign-in failed. Your password may be wrong, or this account may have been created with Google/Apple — try the buttons below.';

  @override
  String get faceReadingTitle => 'Face Reading';

  @override
  String get faceGuideNoFace => 'Bring your face into the frame';

  @override
  String get faceGuideTooFar => 'Move a little closer';

  @override
  String get faceGuideTooClose => 'Move back a little';

  @override
  String get faceGuideOffCentre => 'Centre your face';

  @override
  String get faceGuideTilted => 'Hold your head upright';

  @override
  String get faceGuideReady => 'Ready — hold still';

  @override
  String get faceGuideForehead => 'Uncover your forehead — push your hair back';

  @override
  String get faceScanning => 'Reading your features';

  @override
  String get faceScanNodes => 'Points settling';

  @override
  String get faceScanReading => 'Matching against firasa';

  @override
  String get faceCapture => 'Capture';

  @override
  String get faceRetake => 'Retake';

  @override
  String get faceConsentTitle => 'Face reading needs your consent';

  @override
  String get faceConsentBody =>
      'Face reading processes the camera frame or a photo you pick from your gallery ON YOUR DEVICE. The image is never sent to a server, never stored anywhere, and is discarded as soon as the reading is made (on the gallery path the copy handed to the app is deleted; your original photo is untouched). Only ratios derived from your features (e.g. forehead-to-chin height) are sent; those numbers cannot identify a person.';

  @override
  String get faceConsentCheckbox =>
      'I consent to my face image being processed on my device.';

  @override
  String get faceConsentContinue => 'I consent — continue';

  @override
  String get faceConsentLearnMore => 'Read the privacy policy';

  @override
  String get faceCameraDenied =>
      'Camera permission was not granted. Face reading needs camera access.';

  @override
  String get faceDetectFailed =>
      'No face detected. Make sure the light is good and your face is inside the frame.';

  @override
  String get faceReadingHint =>
      'The tradition says: a single sign decides nothing. What follows is a tendency, not a fate.';

  @override
  String get faceReadingLockedBody =>
      'A temperament reading from your features. The image is processed on your device and never sent anywhere.';

  @override
  String get faceReadingEntryBody =>
      'Scan your face and read your temperament through the firasa tradition.';

  @override
  String get faceGalleryButton => 'Choose from gallery';

  @override
  String get faceLensButton => 'Flip camera';

  @override
  String get faceStillAnalyzing => 'Analyzing photo…';

  @override
  String get faceStillNoFace =>
      'No face found in the photo. Try a well-lit, front-facing photo.';

  @override
  String get faceStillNoLandmarks =>
      'Facial features couldn\'t be traced. Try a photo where the face is fully visible, facing forward.';

  @override
  String get faceStillSingleFrameNote =>
      'This reading was measured from a single photo frame; a live capture gives steadier results.';

  @override
  String get faceWaitStage1 =>
      'Comparing your proportions with the tradition\'s measures…';

  @override
  String get faceWaitStage2 => 'Searching the firasa sources…';

  @override
  String get faceWaitStage3 => 'Writing your reading…';

  @override
  String get faceConsentSetting => 'Face reading consent';

  @override
  String get faceConsentSettingOn =>
      'Given. The image is processed on your device and never stored.';

  @override
  String get faceConsentSettingOff =>
      'Not given. You will be asked when you open face reading.';

  @override
  String get faceConsentWithdrawTitle => 'Withdraw consent';

  @override
  String get faceConsentWithdrawBody =>
      'Your face reading consent will be withdrawn and any firasa readings produced so far will be deleted. Your other readings (natal, BaZi, daily) are not affected.';

  @override
  String get faceConsentWithdrawConfirm => 'Withdraw and delete';

  @override
  String faceConsentWithdrawn(int count) {
    return 'Consent withdrawn, $count readings deleted.';
  }

  @override
  String get faceOpenSettings => 'Try again';

  @override
  String get faceCameraDeniedHint =>
      'If you declined, you can enable camera access for Rytho in your phone settings and come back.';

  @override
  String get save => 'Save';

  @override
  String get edit => 'Edit';

  @override
  String get birthRecordRowSubtitle => 'The basis of every reading';

  @override
  String get languageAndSounds => 'Language and sounds';

  @override
  String get addFriendNeedsUsername =>
      'Pick a username first — you can claim one in the panel below.';

  @override
  String get newConversation => 'New topic';

  @override
  String get chatEmptyTitle => 'Talk with Rytho';

  @override
  String get conversationDeleted => 'Conversation deleted.';

  @override
  String get contactMatchSetting => 'Suggest friends from my contacts';

  @override
  String get contactMatchSettingBody =>
      'Numbers are digested on your phone; your contacts are never uploaded. You only see each other if you\'ve both enabled this.';

  @override
  String get contactSuggestionsLabel => 'FROM YOUR CONTACTS';

  @override
  String get phoneSectionLabel => 'PHONE';

  @override
  String get phoneNotLinked => 'No verified number';

  @override
  String get phoneVerifyAction => 'Verify';

  @override
  String get phoneChangeAction => 'Change';

  @override
  String get phoneVerifyTitle => 'Verify your phone';

  @override
  String get phoneVerifyBody =>
      'Your number is verified via SMS and linked to your account. If you enable contact matching, friends can find you by this number; it\'s never stored in the clear or shared with anyone.';

  @override
  String get phoneFieldLabel => 'Phone number';

  @override
  String get phoneSendCode => 'Send code';

  @override
  String get phoneCodeLabel => 'SMS code';

  @override
  String get phoneConfirmCode => 'Verify';

  @override
  String phoneCodeSentTo(String number) {
    return 'A code was sent to $number.';
  }

  @override
  String get phoneChangeNumber => 'Change number';

  @override
  String get phoneLinkedDone => 'Your phone is verified.';

  @override
  String get phoneInvalid => 'Include the country code (e.g. +15551234567).';

  @override
  String get phoneCodeWrong => 'That code doesn\'t look right — try again.';

  @override
  String get phoneTakenError => 'This number is linked to another account.';

  @override
  String get phoneTooManyTries => 'Too many attempts. Please try again later.';

  @override
  String get deviceConflictTitle => 'Your subscription is on another device';

  @override
  String get deviceConflictBody =>
      'Rytho+ works on one device at a time, and it\'s currently registered to another one. Sign in again to continue here; you\'ll be asked whether to take over.';

  @override
  String get deviceConflictAction => 'Back to sign-in';

  @override
  String get deviceTakeoverTitle => 'Use on this device?';

  @override
  String get deviceTakeoverBody =>
      'Your subscription is registered to another device. If you take over, the other device will be signed out; your subscription works on one device at a time.';

  @override
  String get deviceTakeoverConfirm => 'Use here';

  @override
  String get tokenStoreTitle => 'Token Store';

  @override
  String get tokenBalanceLabel => 'YOUR BALANCE';

  @override
  String get tokenUnit => 'tokens';

  @override
  String get tokenAllowanceRow => 'Monthly allowance (renews each period)';

  @override
  String get tokenPurchasedRow => 'Purchased (rolls over)';

  @override
  String get tokenRolloverNote =>
      'Your monthly allowance renews each period and doesn\'t roll over; purchased tokens never expire.';

  @override
  String get tokenPacksHeader => 'Packs';

  @override
  String tokenPackAmount(int count) {
    return '$count tokens';
  }

  @override
  String get tokenBuy => 'Buy';

  @override
  String get tokenPurchaseDone => 'Pack added. Enjoy your readings ✨';

  @override
  String get tokenPacksUnavailable => 'Packs can\'t be listed right now';

  @override
  String get tokenPacksUnavailableBody =>
      'Couldn\'t reach the store. Please try again shortly.';

  @override
  String get tokenCostsNote =>
      'Chat message 1 · I Ching 2 · daily dyad 3 · deep reports and face reading 5 tokens. Revisiting a report you\'ve already generated is free.';

  @override
  String tokenBalanceChip(int count) {
    return '$count tokens';
  }

  @override
  String get atlasSections => 'What\'s in your chart';

  @override
  String get atlasTraitsSubtitle => 'Your element balance';

  @override
  String get atlasPlanetsSubtitle => 'Positions at your birth';

  @override
  String get atlasFullReport => 'Full report';

  @override
  String get atlasFullReportSubtitle => 'Rytho\'s reading';

  @override
  String atlasAspectsCount(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count aspects',
      one: '1 aspect',
      zero: 'No aspects',
    );
    return '$_temp0';
  }

  @override
  String retrogradeCount(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count planets retrograde',
      one: '1 planet retrograde',
    );
    return '$_temp0';
  }

  @override
  String get genericError => 'Something went wrong. Want to try again?';

  @override
  String get birthRecordEditBody =>
      'This is the foundation of your chart: your daily reading, natal report and everything the chat sees are calculated from it. Changing it recalculates your readings.';

  @override
  String get birthCityEmpty => 'Birth city can\'t be empty.';

  @override
  String get birthRecordSaved =>
      'Your birth record is updated. Readings will use your new chart.';

  @override
  String get birthRecordSavedNoChart =>
      'Your birth record is saved, but your chart couldn\'t be calculated right now. Your sign badges will come back once you\'re online.';

  @override
  String get accountSection => 'Account';

  @override
  String get accountSaved => 'Your account details are updated.';

  @override
  String get displayNameEmpty => 'Your name can\'t be empty.';

  @override
  String get usernameChangeNote =>
      'If you change it, your old username is released and someone else can take it.';

  @override
  String get emailChangeNote =>
      'Your email is the key to your sign-in; contact support to change it.';
}
