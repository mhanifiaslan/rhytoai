/// Hukuki metinler (gizlilik politikası ve kullanım şartları), dile göre.
///
/// Bu metinler ÜRÜNÜN BUGÜNKÜ HÂLİNE göre yazılmıştır; eski sürümden birebir
/// çevrilmemiştir. Eski metin artık var olmayan özellikleri (yüz fotoğrafı
/// analizi, gönderi akışı, takip ilişkileri, birebir mesajlaşma) anlatıyordu
/// ve buna karşılık yeni veri kategorilerini (sohbetten damıtılan kullanıcı
/// hafızası, abonelik durumu, arkadaş katmanı) hiç kapsamıyordu. Yanlış
/// beyan, eksik beyandan daha büyük bir uyum riski.
///
/// UYARI: Bunlar mühendislik tarafından hazırlanmış taslaklardır. Yayın
/// öncesi KVKK/GDPR açısından bir hukukçu tarafından gözden geçirilmelidir.
library;

/// (başlık | null, gövde) çiftleri — başlıksız girdiler düz paragraftır.
typedef LegalSections = List<(String?, String)>;

const String kLegalLastUpdatedTr = '2 Ağustos 2026';
const String kLegalLastUpdatedEn = '2 August 2026';
const String kLegalContact = 'aslan.mh@gmail.com';

// ---------------------------------------------------------------------------
// Gizlilik Politikası — Türkçe
// ---------------------------------------------------------------------------

const LegalSections kPrivacyPolicyTr = [
  (
    null,
    'Son güncelleme: $kLegalLastUpdatedTr. Bu politika, Rytho\'yu kullanırken '
        'hangi verileri neden işlediğimizi, kimlerle paylaştığımızı ve '
        'haklarını açıklar.'
  ),
  (
    'Hesap bilgileri',
    'Google ile veya e-posta ile giriş yaptığında adın, e-posta adresin ve '
        'varsa profil fotoğrafın işlenir. Amaç: hesabını oluşturmak ve '
        'oturumunu doğrulamak. Hukuki dayanak: sözleşmenin ifası.'
  ),
  (
    'Telefon numarası (isteğe bağlı)',
    'Telefonunu doğrularsan numaran SMS ile doğrulanır ve kimlik '
        'sağlayıcımızda (Firebase Authentication) hesabına bağlanır. '
        'Sunucularımızda numaranın kendisi DEĞİL, geri döndürülemez bir '
        'özeti (SHA-256) tutulur; bu özet yalnızca bir numaranın tek hesaba '
        'bağlı kalmasını sağlamak ve — açarsan — rehber eşleşmesinde '
        'kullanılır. Numaranı doğrulamak zorunlu değildir; doğrulamazsan '
        'uygulamanın geri kalanı aynen çalışır.'
  ),
  (
    'Abonelik ve tek cihaz',
    'Rytho+ aboneliği aynı anda tek cihazda kullanılır. Bunu sağlamak için '
        'cihazında rastgele üretilmiş bir tanımlayıcı saklanır ve '
        'isteklerinle birlikte gönderilir. Bu tanımlayıcı donanım kimliği '
        'değildir, reklam veya takip amacıyla kullanılmaz; uygulamayı silip '
        'yeniden kurduğunda değişir.'
  ),
  (
    'Doğum verisi',
    'Doğum tarihin, saatin ve şehrin; natal harita, BaZi ve günlük okuma '
        'hesaplamaları için işlenir ve hesabında saklanır. Bu üçlü hassas bir '
        'kombinasyondur: hiçbir başka kullanıcı bu verilere erişemez. '
        'Arkadaşların yalnızca senin görünür kıldığın türetilmiş bilgileri '
        '(adın, kullanıcı adın, güneş burcun, açtıysan serin) görebilir. '
        'Doğum verisi reklam veya profilleme amacıyla üçüncü taraflarla '
        'paylaşılmaz ve satılmaz.'
  ),
  (
    'Sohbet ve kullanıcı hafızası',
    'Sohbet mesajların yanıt üretmek üzere yapay zeka sağlayıcımıza '
        'iletilir.\n\n'
        'Konuşmaların kaldığın yerden sürebilmesi için mesajların konu konu '
        'hesabına bağlı olarak SAKLANIR. Bu arşiv yalnızca sana görünür; '
        'başka kullanıcılara gösterilmez, reklam veya profilleme için '
        'kullanılmaz. Bir konuyu istediğin an silebilirsin; 30 gün boyunca '
        'hiç açılmayan konular mesajlarıyla birlikte otomatik silinir. '
        'Hesabını sildiğinde tüm konuşmaların da silinir.\n\n'
        'Ayrıca seni sonraki konuşmalarda daha iyi anlayabilmek için '
        'konuşmadan kısa ve yapılandırılmış olgular damıtılır (örneğin '
        'tekrar eden bir tema, dile getirdiğin bir hedef, tercih ettiğin '
        'anlatım tonu). Bu olgular yalnızca kapalı bir kategori kümesine '
        'oturur, hesabına bağlı olarak saklanır ve başka kullanıcılara '
        'gösterilmez. Sağlık durumu, tanı veya ilaç bilgisi bu kapsamda '
        'TUTULMAZ.'
  ),
  (
    'Yüz okuma',
    'Yüz okuma özelliği KAMERAYI kullanır ama FOTOĞRAF ÇEKMEZ. Kamera '
        'görüntüsü telefonundan çıkmaz: yüz hatlarının tespiti de, saç '
        'çizgisinin bulunması da tamamen cihazında, çevrimdışı çalışan '
        'modellerle yapılır. Görüntü sunucularımıza gönderilmez, buluta '
        'yüklenmez ve telefonunun diskine dahi yazılmaz — işlem bittiği anda '
        'bellekten silinir.\n\n'
        'Sunucuya yalnızca yüz hatlarından TÜRETİLMİŞ ORANLAR gider (örneğin '
        'alın yüksekliğinin yüz yüksekliğine oranı). Bu sayılar iki ondalığa '
        'yuvarlanır ve kişiyi tanımaya yaramaz: "0,34" değeri milyonlarca '
        'insanda aynıdır. Yüz tanıma, kimlik doğrulama veya kişi eşleştirme '
        'YAPILMAZ; bu sayılardan yüzün geri üretilmesi mümkün değildir.\n\n'
        'Oranlar ve üretilen okuma hesabına bağlı olarak saklanır, başka '
        'kullanıcılara gösterilmez. Bu özellik ayrı ve açık rızanla '
        'çalışır; rızanı Profil > Gizlilik bölümünden istediğin an geri '
        'alabilirsin. Geri aldığında oranların ve o oranlardan üretilmiş '
        'okumalar silinir.\n\n'
        'Yüz okuma bir eğlence ve kendini tanıma aracıdır. Sağlık, işe alım, '
        'kredi, sigorta ya da benzeri hiçbir kararda kullanılmaz ve '
        'kullanılmamalıdır.'
  ),
  (
    'Arkadaş katmanı',
    'Kullanıcı adın, karşılıklı onaylı arkadaşlıkların ve gönderdiğin hazır '
        'tepkiler saklanır. Uygulamada kullanıcılar birbirine serbest metin '
        'gönderemez; yalnızca önceden tanımlı bir tepki kümesinden seçim '
        'yapılabilir.\n\n'
        'Rehberine varsayılan olarak ERİŞİLMEZ. "Rehberimden arkadaş öner" '
        'ayarını açarsan rehberindeki telefon numaraları CİHAZINDA geri '
        'döndürülemez özetlere (SHA-256) çevrilir ve yalnızca bu özetler '
        'eşleştirme için sunucuya gönderilir; ad, soyad veya başka hiçbir '
        'rehber alanı okunmaz ve gönderilmez. Özet listesi eşleştirme '
        'yapıldıktan sonra atılır, sunucuda saklanmaz. Eşleşme '
        'KARŞILIKLIDIR: yalnızca ikiniz de bu ayarı açtıysanız birbirinizi '
        'görürsünüz. Ayarı kapattığın an görünmez olursun.'
  ),
  (
    'Bildirimler',
    'Bildirimleri açtığında cihazının bildirim kimliği (FCM token), saat '
        'dilimin ve seçtiğin arayüz dili hesabına bağlı olarak saklanır. Saat '
        'dilimi, bildirimin senin yerel sabahına denk gelmesi için gerekir; '
        'konum bilgin alınmaz, yalnızca cihazının bildirdiği saat dilimi adı '
        '(örneğin "Europe/Istanbul") kaydedilir. Bildirim metinleri '
        'sunucumuzda üretilir ve burcuna göre hazırlanır; bu metinler kişiye '
        'özel değildir ve sohbet geçmişin bildirim üretiminde kullanılmaz. '
        'Bildirim türlerini ve sessiz saatleri Profil > Bildirimler '
        'bölümünden kapatabilir, cihaz ayarlarından tümüyle kaldırabilirsin. '
        'Uygulamayı sildiğinde bildirim kimliği geçersizleşir ve ilk '
        'başarısız gönderimde kaydımızdan silinir.'
  ),
  (
    'Abonelik',
    'Satın alma işlemi cihazının uygulama mağazası üzerinden yürütülür; '
        'ödeme bilgilerini biz görmeyiz ve saklamayız. Abonelik durumunu '
        '(aktif/pasif, dönem sonu) RevenueCat aracılığıyla alır ve hesabına '
        'bağlı olarak saklarız.'
  ),
  (
    'Yapay zeka ile işleme',
    'Okumalar ve sohbet yanıtları Google Gemini ile üretilir. Modele '
        'gönderilenler: hesaplanmış gök verisi, doğum haritandan türetilen '
        'konumlar (doğum tarihin/saatin değil), varsa kullanıcı hafızandan '
        'kısa bağlam ve mesajın. Yorumlar içgörü amaçlıdır; tıbbi, hukuki '
        'veya finansal tavsiye değildir.'
  ),
  (
    'Alt işleyiciler',
    'Google LLC (Firebase Authentication, Cloud Firestore, Cloud Run, '
        'Gemini API) ve RevenueCat, Inc. (abonelik yönetimi). Veriler '
        'ağırlıklı olarak Google Cloud us-central1 bölgesinde işlenir; bu, '
        'verilerin Türkiye ve AB dışına aktarılması anlamına gelir.'
  ),
  (
    'Saklama süresi',
    'Hesap ve doğum verilerin hesabın var olduğu sürece saklanır. Yapay '
        'zeka yanıt önbelleği en fazla 30 gün tutulur. Hesabını sildiğinde '
        'tüm veriler kalıcı olarak silinir.'
  ),
  (
    'Haklarının kullanımı',
    'Verilerine erişme, düzeltme, silme, işlemeyi kısıtlama ve taşınabilirlik '
        'haklarına sahipsin. Hesabını uygulama içinden silebilirsin; '
        'dilersen $kLegalContact adresine de yazabilirsin. Talepler en geç '
        '30 gün içinde sonuçlandırılır.'
  ),
  (
    'Yaş sınırı',
    'Rytho 13 yaşın altındakilere yönelik değildir ve bilerek bu yaş grubundan '
        'veri toplamayız.'
  ),
  (
    'İletişim',
    'Gizlilikle ilgili sorular için: $kLegalContact'
  ),
];

// ---------------------------------------------------------------------------
// Kullanım Şartları — Türkçe
// ---------------------------------------------------------------------------

const LegalSections kTermsOfUseTr = [
  (
    null,
    'Son güncelleme: $kLegalLastUpdatedTr. Rytho\'yu kullanarak bu şartları '
        'kabul etmiş olursun.'
  ),
  (
    'İçgörü amaçlıdır',
    'Tüm okumalar, raporlar ve sohbet yanıtları kişisel içgörü amaçlıdır. '
        'Hiçbir içerik tıbbi, hukuki, finansal veya psikolojik tavsiye '
        'değildir. Uygulama sağlık, hastalık, hamilelik, ölüm ve yatırım '
        'konularında öngörüde bulunmayı bilinçli olarak REDDEDER; bu tür '
        'kararlar için ilgili alanın uzmanına danış.'
  ),
  (
    'Astroloji hakkında dürüst not',
    'Gökyüzü hesaplamaları gerçek astronomik veriye dayanır (Swiss '
        'Ephemeris). Ancak bu konumlardan kişilik veya olay çıkarımı '
        'geleneksel bir yorum pratiğidir; bilimsel olarak doğrulanmış bir '
        'öngörü yöntemi değildir.'
  ),
  (
    'Hesap ve yaş sınırı',
    'Kullanım için hesap oluşturman gerekir ve en az 13 yaşında olmalısın. '
        'Hesap bilgilerinin güvenliğinden sen sorumlusun.'
  ),
  (
    'Abonelik',
    'Rytho+ aboneliği, dönem bitiminden en az 24 saat önce iptal edilmezse '
        'otomatik yenilenir. Ücretlendirme ve iptal cihazının uygulama '
        'mağazası hesabı üzerinden yürür. Deneme süresi sunulduysa, süre '
        'dolmadan iptal edersen ücret alınmaz.'
  ),
  (
    'Davranış kuralları',
    'Uygulamada kullanıcılar birbirine serbest metin gönderemez; etkileşim '
        'önceden tanımlı tepkilerle sınırlıdır. Buna rağmen rahatsız edici '
        'davranışla karşılaşırsan kullanıcıyı engelleyebilir ve şikayet '
        'edebilirsin. Hizmeti kötüye kullanan hesaplar kapatılabilir.'
  ),
  (
    'Fikri mülkiyet',
    'Uygulamanın tasarımı, yazılımı ve bilgi tabanı Rytho\'ya aittir. '
        'Efemeris hesaplarında Swiss Ephemeris (© Astrodienst AG) kullanılır.'
  ),
  (
    'Sorumluluk sınırı',
    'Hizmet "olduğu gibi" sunulur; kesintisiz veya hatasız çalışacağı '
        'garanti edilmez. Yorumlara dayanarak aldığın kararlardan Rytho '
        'sorumlu tutulamaz.'
  ),
  (
    'İletişim',
    'Sorular ve talepler için: $kLegalContact'
  ),
];

// ---------------------------------------------------------------------------
// Privacy Policy — English
// ---------------------------------------------------------------------------

const LegalSections kPrivacyPolicyEn = [
  (
    null,
    'Last updated: $kLegalLastUpdatedEn. This policy explains what data we '
        'process when you use Rytho, why we process it, who we share it with, '
        'and what rights you have.'
  ),
  (
    'Account information',
    'When you sign in with Google or with an email address, we process your '
        'name, email address and profile photo if you have one. Purpose: to '
        'create your account and verify your session. Legal basis: '
        'performance of a contract.'
  ),
  (
    'Phone number (optional)',
    'If you verify your phone, the number is confirmed via SMS and linked '
        'to your account by our identity provider (Firebase Authentication). '
        'Our servers store an irreversible digest (SHA-256) of the number, '
        'NOT the number itself; the digest is used only to keep one number '
        'bound to one account and — if you enable it — for contact '
        'matching. Verification is optional; without it, the rest of the '
        'app works unchanged.'
  ),
  (
    'Subscription and single device',
    'A Rytho+ subscription works on one device at a time. To enforce this, '
        'a randomly generated identifier is stored on your device and sent '
        'with your requests. It is not a hardware identifier, is never used '
        'for advertising or tracking, and changes if you reinstall the app.'
  ),
  (
    'Birth data',
    'Your date, time and city of birth are processed to calculate your natal '
        'chart, BaZi chart and daily readings, and are stored on your '
        'account. This combination is sensitive: no other user can access it. '
        'Friends only see derived information you have chosen to make visible '
        '(your name, username, sun sign, and your streak if you enable it). '
        'Birth data is never shared with third parties for advertising or '
        'profiling, and is never sold.'
  ),
  (
    'Chat and user memory',
    'Your chat messages are sent to our AI provider to generate a reply.\n\n'
        'So that conversations can continue where you left off, your '
        'messages ARE stored against your account, organised by topic. This '
        'archive is visible only to you; it is never shown to other users '
        'and never used for advertising or profiling. You can delete any '
        'topic at any time; topics untouched for 30 days are deleted '
        'automatically together with their messages. Deleting your account '
        'deletes all conversations.\n\n'
        'In addition, short structured facts are distilled from the '
        'conversation so that later conversations can understand you better '
        '— for example a recurring theme, a goal you mentioned, or the tone '
        'you prefer. These facts fit a closed set of categories, are stored '
        'against your account, and are never shown to other users. Health '
        'conditions, diagnoses and medication are explicitly NOT retained.'
  ),
  (
    'The friends layer',
    'We store your username, your mutually accepted friendships and the '
        'preset reactions you send. Users cannot send each other free text in '
        'this app; interaction is limited to a fixed set of reactions.\n\n'
        'By default we do NOT access your contacts. If you enable "Suggest '
        'friends from my contacts", the phone numbers in your address book '
        'are converted to irreversible digests (SHA-256) ON YOUR DEVICE and '
        'only those digests are sent for matching; names and every other '
        'contact field are never read or transmitted. The digest list is '
        'discarded after matching and never stored on our servers. Matching '
        'is MUTUAL: you only see each other if you have both enabled the '
        'setting. Turning it off makes you invisible immediately.'
  ),
  (
    'Face reading',
    'The face reading feature uses the CAMERA but does NOT take a photo. The '
        'camera image never leaves your phone: both the facial landmark '
        'detection and the hairline measurement run entirely on your device, '
        'with offline models. The image is not sent to our servers, not '
        'uploaded to any cloud, and not even written to your phone '
        'storage — it is discarded from memory as soon as the measurement '
        'finishes.\n\n'
        'Only DERIVED RATIOS are sent to the server (for example, forehead '
        'height as a fraction of face height). These numbers are rounded to '
        'two decimals and cannot identify you: a value of "0.34" is shared by '
        'millions of people. No face recognition, identity verification or '
        'person matching is performed, and your face cannot be reconstructed '
        'from these numbers.\n\n'
        'The ratios and the resulting reading are stored against your account '
        'and are never shown to other users. The feature runs only with your '
        'separate, explicit consent, which you can withdraw at any time from '
        'Profile > Privacy. Withdrawing deletes your ratios and any readings '
        'produced from them.\n\n'
        'Face reading is a form of entertainment and self-reflection. It is '
        'not used, and must not be used, for any decision about health, '
        'employment, credit, insurance or anything similar.'
  ),
  (
    'Notifications',
    'If you turn notifications on, we store your device\'s notification token '
        '(FCM), your time zone and your chosen interface language against your '
        'account. The time zone is what lets a notification land in your own '
        'morning; we do not collect your location, only the time zone name '
        'your device reports (for example "Europe/Istanbul"). Notification '
        'text is generated on our servers per sun sign — it is not '
        'individually personalised, and your chat history is never used to '
        'produce it. You can switch types off and set quiet hours under '
        'Profile > Notifications, or turn them off entirely in your device '
        'settings. If you delete the app the token stops working and we drop '
        'it on the first failed delivery.'
  ),
  (
    'Subscriptions',
    'Purchases are handled by your device\'s app store. We never see or store '
        'your payment details. We receive your subscription status (active or '
        'inactive, period end) through RevenueCat and store it against your '
        'account.'
  ),
  (
    'AI processing',
    'Readings and chat replies are generated with Google Gemini. What is sent '
        'to the model: calculated sky data, positions derived from your chart '
        '(not your birth date or time), a short amount of context from your '
        'user memory if any, and your message. Readings are for insight; they '
        'are not medical, legal or financial advice.'
  ),
  (
    'Sub-processors',
    'Google LLC (Firebase Authentication, Cloud Firestore, Cloud Run, Gemini '
        'API) and RevenueCat, Inc. (subscription management). Data is '
        'processed primarily in the Google Cloud us-central1 region, which '
        'means it is transferred outside the EU and the United Kingdom.'
  ),
  (
    'Retention',
    'Your account and birth data are kept for as long as your account exists. '
        'AI response caches are kept for at most 30 days. When you delete '
        'your account, all of it is permanently deleted.'
  ),
  (
    'Your rights',
    'You have the right to access, correct, delete, restrict the processing '
        'of, and port your data. You can delete your account from inside the '
        'app, or write to $kLegalContact. Requests are resolved within 30 days '
        'at the latest.'
  ),
  (
    'Age limit',
    'Rytho is not directed at children under 13, and we do not knowingly '
        'collect data from that age group.'
  ),
  (
    'Contact',
    'For privacy questions: $kLegalContact'
  ),
];

// ---------------------------------------------------------------------------
// Terms of Use — English
// ---------------------------------------------------------------------------

const LegalSections kTermsOfUseEn = [
  (
    null,
    'Last updated: $kLegalLastUpdatedEn. By using Rytho you accept these '
        'terms.'
  ),
  (
    'For insight only',
    'All readings, reports and chat replies are for personal insight. Nothing '
        'in the app is medical, legal, financial or psychological advice. The '
        'app deliberately DECLINES to make predictions about health, illness, '
        'pregnancy, death or investments; for those decisions, consult a '
        'qualified professional.'
  ),
  (
    'An honest note about astrology',
    'The sky calculations are based on real astronomical data (Swiss '
        'Ephemeris). Drawing conclusions about personality or events from '
        'those positions, however, is a traditional interpretive practice — '
        'not a scientifically validated method of prediction.'
  ),
  (
    'Account and age limit',
    'You need an account to use the app and you must be at least 13 years '
        'old. You are responsible for keeping your account credentials safe.'
  ),
  (
    'Subscription',
    'A Rytho+ subscription renews automatically unless it is cancelled at '
        'least 24 hours before the end of the period. Billing and cancellation '
        'are handled through your device\'s app store account. If a free trial '
        'is offered and you cancel before it ends, you will not be charged.'
  ),
  (
    'Conduct',
    'Users cannot send each other free text in this app; interaction is '
        'limited to preset reactions. Even so, if someone behaves in a way '
        'that troubles you, you can block and report them. Accounts that '
        'abuse the service may be closed.'
  ),
  (
    'Intellectual property',
    'The design, software and knowledge base of the app belong to Rytho. '
        'Ephemeris calculations use Swiss Ephemeris (© Astrodienst AG).'
  ),
  (
    'Limitation of liability',
    'The service is provided "as is"; we do not guarantee it will run without '
        'interruption or error. Rytho is not liable for decisions you make on '
        'the basis of its readings.'
  ),
  (
    'Contact',
    'For questions and requests: $kLegalContact'
  ),
];

// ---------------------------------------------------------------------------

/// Dile göre gizlilik politikası bölümleri.
LegalSections privacyPolicySections(String languageCode) =>
    languageCode == 'en' ? kPrivacyPolicyEn : kPrivacyPolicyTr;

/// Dile göre kullanım şartları bölümleri.
LegalSections termsOfUseSections(String languageCode) =>
    languageCode == 'en' ? kTermsOfUseEn : kTermsOfUseTr;
