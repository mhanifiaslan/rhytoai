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

const String kLegalLastUpdatedTr = '29 Temmuz 2026';
const String kLegalLastUpdatedEn = '29 July 2026';
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
        'iletilir. Konuşmaların HAM METNİ sunucularımızda saklanmaz. Bunun '
        'yerine, seni sonraki konuşmalarda daha iyi anlayabilmek için '
        'konuşmadan kısa ve yapılandırılmış olgular damıtılır (örneğin '
        'tekrar eden bir tema, dile getirdiğin bir hedef, tercih ettiğin '
        'anlatım tonu). Bu olgular yalnızca kapalı bir kategori kümesine '
        'oturur, hesabına bağlı olarak saklanır ve başka kullanıcılara '
        'gösterilmez. Sağlık durumu, tanı veya ilaç bilgisi bu kapsamda '
        'TUTULMAZ.'
  ),
  (
    'Arkadaş katmanı',
    'Kullanıcı adın, karşılıklı onaylı arkadaşlıkların ve gönderdiğin hazır '
        'tepkiler saklanır. Uygulamada kullanıcılar birbirine serbest metin '
        'gönderemez; yalnızca önceden tanımlı bir tepki kümesinden seçim '
        'yapılabilir. Rehberine erişilmez.'
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
    'Your chat messages are sent to our AI provider to generate a reply. We '
        'do NOT store the raw text of your conversations on our servers. '
        'Instead, short structured facts are distilled from the conversation '
        'so that later conversations can understand you better — for example '
        'a recurring theme, a goal you mentioned, or the tone you prefer. '
        'These facts fit a closed set of categories, are stored against your '
        'account, and are never shown to other users. Health conditions, '
        'diagnoses and medication are explicitly NOT retained.'
  ),
  (
    'The friends layer',
    'We store your username, your mutually accepted friendships and the '
        'preset reactions you send. Users cannot send each other free text in '
        'this app; interaction is limited to a fixed set of reactions. We do '
        'not access your contacts.'
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
