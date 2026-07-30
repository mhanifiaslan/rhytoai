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
  String get oracleTools => 'Oracle Tools';

  @override
  String get skyNow => 'In the Sky Right Now';

  @override
  String get iChing => 'I Ching';

  @override
  String get iChingSubtitle => 'Book of Changes';

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
      'Pick a username. We don\'t touch your contacts — friends are added by username or invite link only.';

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
}
