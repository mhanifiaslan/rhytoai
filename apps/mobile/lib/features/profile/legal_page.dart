import 'package:flutter/material.dart';

import '../../theme/rytho_theme.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/glass.dart';

/// Sade cam panelli hukuki metin görüntüleyici.
/// Metinlerin kaynağı: docs/legal/*.md (özet, paragraf halinde).
class LegalPage extends StatelessWidget {
  const LegalPage({super.key, required this.title, required this.sections});

  final String title;

  /// (başlık | null, gövde) çiftleri — başlıksız girdiler düz paragraftır.
  final List<(String?, String)> sections;

  @override
  Widget build(BuildContext context) {
    return CosmicScaffold(
      appBar: AppBar(title: Text(title)),
      body: ListView(
        padding: const EdgeInsets.only(top: 8, bottom: 40),
        children: [
          GlassPanel(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                for (final (heading, body) in sections) ...[
                  if (heading != null) ...[
                    const SizedBox(height: 14),
                    Text(heading.toUpperCase(),
                        style: RythoText.mono(11,
                            color: RythoColors.goldBright)),
                    const SizedBox(height: 6),
                  ],
                  Text(body,
                      style: RythoText.body(13.5,
                          height: 1.6, color: RythoColors.parchmentDim)),
                  const SizedBox(height: 6),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Gizlilik politikası (özet — tam metin: docs/legal/gizlilik-politikasi.md).
const List<(String?, String)> kPrivacyPolicySections = [
  (
    null,
    'Son güncelleme: 23 Temmuz 2026. Bu politika, KVKK ve GDPR çerçevesinde '
        'hangi verileri neden işlediğimizi ve haklarını açıklar.'
  ),
  (
    'Hesap bilgileri',
    'Google ile girişte ad, e-posta ve profil fotoğrafın; hesabını oluşturmak '
        've oturumunu doğrulamak için işlenir.'
  ),
  (
    'Doğum verisi',
    'Doğum tarihi, saati ve şehri; natal harita, BaZi ve günlük okuma '
        'hesaplamaları için işlenir ve profilinde saklanır. Reklam veya '
        'profilleme amacıyla üçüncü taraflarla paylaşılmaz.'
  ),
  (
    'Yüz fotoğrafı',
    'Yüz analizi için gönderdiğin fotoğraf, analiz tamamlanır tamamlanmaz '
        'sunucudan SİLİNİR; hiçbir yerde saklanmaz, yedeklenmez ve üçüncü '
        'taraflarla paylaşılmaz. Kalan tek çıktı sayısal oran ölçümleri ve '
        'metin yorumdur.'
  ),
  (
    'Sosyal içerik',
    'Gönderiler, beğeniler, takip ilişkileri ve mesajlar sosyal özelliklerin '
        'çalışması için saklanır. Mesajlar yalnızca katılımcılara görünür.'
  ),
  (
    'Yapay zeka ile işleme',
    'Okumalar Google Gemini ile üretilir; doğum haritası özetin Google Cloud '
        'altyapısında işlenir. Yorumlar eğlence ve içgörü amaçlıdır; tıbbi, '
        'hukuki veya finansal tavsiye değildir.'
  ),
  (
    'Alt işleyiciler',
    'Verilerin Google Firebase ve Google Cloud Platform (us-central1) '
        'altyapısında barındırılır ve işlenir (Google LLC).'
  ),
  (
    'Veri silme',
    'Hesabının ve tüm verilerinin silinmesi için kayıtlı e-posta adresinden '
        'aslan.mh@gmail.com adresine yazman yeterlidir; talep en geç 30 gün '
        'içinde sonuçlandırılır.'
  ),
];

/// Kullanım şartları (özet — tam metin: docs/legal/kullanim-sartlari.md).
const List<(String?, String)> kTermsOfUseSections = [
  (
    null,
    'Son güncelleme: 23 Temmuz 2026. Rytho\'yu kullanarak bu şartları kabul '
        'etmiş olursun.'
  ),
  (
    'Eğlence ve içgörü amaçlıdır',
    'Tüm okumalar, raporlar ve sohbet yanıtları yalnızca eğlence ve kişisel '
        'içgörü amaçlıdır. Hiçbir içerik tıbbi, hukuki, finansal veya '
        'psikolojik tavsiye değildir; bu tür kararlar için ilgili alanın '
        'uzmanına danış.'
  ),
  (
    'Hesap ve yaş sınırı',
    'Uygulama için Google hesabıyla giriş gerekir ve en az 13 yaşında '
        'olmalısın.'
  ),
  (
    'Topluluk kuralları',
    'Hakaret, taciz, nefret söylemi, spam, müstehcen veya yasa dışı içerik '
        'yasaktır. Gönderiler yayın öncesi otomatik denetimden geçer; ihlaller '
        'şikayet, engelleme ve hesap kapatma ile sonuçlanabilir.'
  ),
  (
    'Fikri mülkiyet',
    'Uygulamanın tasarımı ve yazılımı Rytho\'ya aittir. Paylaştığın içerikler '
        'sana aittir. Efemeris hesaplarında Swiss Ephemeris (© Astrodienst AG) '
        'kullanılır.'
  ),
  (
    'Sorumluluk sınırı',
    'Hizmet "olduğu gibi" sunulur; kesintisiz çalışacağı garanti edilmez. '
        'Yorumlara dayanarak alınan kararlardan Rytho sorumlu tutulamaz.'
  ),
  (
    'İletişim',
    'Sorular ve talepler için: aslan.mh@gmail.com'
  ),
];
