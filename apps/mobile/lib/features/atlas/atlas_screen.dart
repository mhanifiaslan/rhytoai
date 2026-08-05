import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers.dart';
import '../../theme/rytho_theme.dart';
import '../../theme/rytho_tokens.dart';
import '../../widgets/common.dart';
import '../../widgets/glass.dart';
import '../../widgets/natal_wheel.dart';
import '../../widgets/nebula_widgets.dart';
import '../../widgets/reading_card.dart';
import '../face/face_reading_flow.dart';
import '../oracle/oracle_screen.dart';
import '../paywall/paywall_screen.dart';
import 'birth_hexagram_screen.dart';
import '../paywall/plus_locked_card.dart';
import 'atlas_detail_screens.dart';
import '../../widgets/motion.dart';
import '../../core/subscription.dart' show subscriptionProvider;
import '../../core/api.dart' show friendlyError;
import '../../l10n/app_localizations.dart';

/// ATLAS — **haritan**. Dizin ekranı.
///
/// ## Yeniden kurgulandı
///
/// Önceki hâli ~2000 px'di: çark, kişi kartı, gezegen ızgarası, kişilik
/// çubukları, katlanır açı listesi ve sınırsız uzunlukta AI raporu alt alta
/// duruyordu. Kullanıcının tarifi "her şey her yerde hissi var, tam bir kaos"
/// idi ve teşhis "çok özellik var" değildi — **hepsinin aynı seviyede
/// durmasıydı**.
///
/// Şimdi: üstte çark (haritanın bir bakışta özeti), altında dört giriş. Her
/// giriş kendi sayfasını açıyor (bkz. atlas_detail_screens.dart).
///
/// Kişi kartı buradan tamamen kalktı; doğum verisi profile taşındı ve orada
/// **düzenlenebilir** oldu (bkz. features/profile/birth_record_screen.dart).
class AtlasScreen extends ConsumerStatefulWidget {
  const AtlasScreen({super.key});

  @override
  ConsumerState<AtlasScreen> createState() => _AtlasScreenState();
}

class _AtlasScreenState extends ConsumerState<AtlasScreen> {
  Map<String, dynamic>? _selectedPlanet;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final natal = ref.watch(natalReportProvider);

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(title: Text(l10n.atlasTitle)),
      // Kehanet satırı natal raporun DIŞINDA duruyor.
      //
      // Yüz okuma önce `data != null` dalının içindeydi; sonuç şuydu: natal
      // rapor kilitliyken firaset girişi de hiç görünmüyordu. Oysa üç araç
      // da natal rapordan bağımsız çalışıyor (İching ücretsiz bile).
      //
      // Madde 11 (Revize R6): İching + BaZi Gökyüzü'nden BURAYA taşındı —
      // Yüz Okuma ile tek satır. Gökyüzü'nden ARAÇLAR bölümü kalktı.
      body: Column(children: [
        const Padding(
          padding: EdgeInsets.fromLTRB(16, 8, 16, 0),
          child: _DivinationRow(),
        ),
        Expanded(
          child: natal.when(
            // Rapor LLM üretimi — bekleyiş uzun. Çıplak kadran yerine sahne
            // (R12-B3): aşamalar gerçek işi anlatıyor, yüzde çubuğu yok.
            loading: () => StagedWaiting(stages: [
              l10n.atlasWaitStage1,
              l10n.atlasWaitStage2,
              l10n.atlasWaitStage3,
            ]),
            error: (e, _) => Center(
              child: Padding(
                padding: const EdgeInsets.all(32),
                child: Text(friendlyError(e, l10n),
                    style:
                        RythoText.body(14, color: RythoColors.parchmentDim)),
              ),
            ),
            data: (data) {
              if (data == null) {
                return PlusLockedCard(
                  emoji: '🗺️',
                  title: l10n.natalLockedTitle,
                  description: l10n.natalLockedBody,
                  centered: true,
                );
              }
          final chart = Map<String, dynamic>.from(data['chart']);
          final points = List<Map<String, dynamic>>.from(chart['points'] ?? []);
          final houses = List<Map<String, dynamic>>.from(chart['houses'] ?? []);
          final aspects = List<Map<String, dynamic>>.from(chart['aspects'] ?? []);
          // Hesap beyanları (T0): ör. şehir çözülemedi → Yükselen yaklaşık.
          // Sunucu metni isteğin dilinde üretir; burada yalnız gösterilir.
          final beyanlar =
              List<String>.from(chart['disclosure_texts'] ?? const []);

          var stagger = 0;
          Duration next() => Duration(milliseconds: 70 * stagger++);

          void ac(Widget sayfa) => Navigator.of(context)
              .push(MaterialPageRoute(builder: (_) => sayfa));

          return ListView(
            padding:
                const EdgeInsets.only(bottom: RythoSpace.dockClearance),
            children: [
              const SizedBox(height: RythoSpace.sm),
              // Beyan notu — BirthHexagram sınır beyanıyla aynı dil (bakır).
              if (beyanlar.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 4, 20, 4),
                  child: Text(beyanlar.join('\n'),
                      style:
                          RythoText.body(11.5, color: RythoColors.copper)),
                ),
              // Natal çark
              GlassPanel(
                padding: const EdgeInsets.all(8),
                child: Column(children: [
                  Center(
                    child: NatalWheel(
                      points: points,
                      houses: houses,
                      aspects: aspects,
                      size: MediaQuery.of(context).size.width - 72,
                      onPlanetTap: (p) => setState(() => _selectedPlanet = p),
                    ),
                  ),
                  AnimatedSize(
                    duration: const Duration(milliseconds: 260),
                    curve: Curves.easeOutCubic,
                    child: _selectedPlanet == null
                        ? const SizedBox(width: double.infinity)
                        : Container(
                            width: double.infinity,
                            margin: const EdgeInsets.fromLTRB(8, 4, 8, 8),
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: RythoColors.inkLighter,
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(
                                  color: RythoColors.lilac
                                      .withValues(alpha: 0.3)),
                            ),
                            child: Row(children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      planetSignLabel(
                                          context, _selectedPlanet!),
                                      style: RythoText.body(15,
                                          w: FontWeight.w700),
                                    ),
                                    Text(
                                      '${(_selectedPlanet!['position'] as num).toStringAsFixed(1)}°'
                                      '${_selectedPlanet!['house'] != null ? ' · ${_selectedPlanet!['house']}' : ''}'
                                      '${_selectedPlanet!['retrograde'] == true ? ' · retro' : ''}',
                                      style: RythoText.mono(12,
                                          color: RythoColors.parchmentDim),
                                    ),
                                  ],
                                ),
                              ),
                              IconButton(
                                icon: const Icon(Icons.close,
                                    size: 16, color: RythoColors.parchmentDim),
                                onPressed: () =>
                                    setState(() => _selectedPlanet = null),
                              ),
                            ]),
                          ),
                  ),
                ]),
              ).animate(delay: next()).fadeIn(duration: 380.ms).slideY(
                  begin: 0.06, curve: Curves.easeOutCubic),
              // ---------- DİZİN ----------
              //
              // Kişi kartı BURADAN KALKTI: doğum verisi profile taşındı ve
              // orada düzenlenebilir oldu. Aynı bilginin iki yerde durması
              // kullanıcının "profilimde olan bilgiler de var" şikayetinin
              // kaynağıydı; üstelik burada salt okunurdu.
              SectionHeader(l10n.atlasSections)
                  .animate(delay: next())
                  .fadeIn(duration: 360.ms),
              Padding(
                padding: const EdgeInsets.symmetric(
                    horizontal: RythoSpace.lg),
                child: Column(children: [
                  Row(children: [
                    Expanded(
                      child: _AtlasTile(
                        emoji: '🎭',
                        title: l10n.atlasTraits,
                        subtitle: l10n.atlasTraitsSubtitle,
                        onTap: () => ac(AtlasTraitsScreen(points: points)),
                      ),
                    ),
                    const SizedBox(width: RythoSpace.md),
                    Expanded(
                      child: _AtlasTile(
                        emoji: '🪐',
                        title: l10n.atlasPlanetPositions,
                        subtitle: l10n.atlasPlanetsSubtitle,
                        onTap: () => ac(AtlasPlanetsScreen(points: points)),
                      ),
                    ),
                  ]),
                  const SizedBox(height: RythoSpace.md),
                  Row(children: [
                    Expanded(
                      child: _AtlasTile(
                        emoji: '📐',
                        title: l10n.atlasAspects,
                        subtitle: l10n.atlasAspectsCount(aspects.length),
                        onTap: () => ac(AtlasAspectsScreen(aspects: aspects)),
                      ),
                    ),
                    const SizedBox(width: RythoSpace.md),
                    Expanded(
                      child: _AtlasTile(
                        emoji: '📜',
                        title: l10n.atlasFullReport,
                        subtitle: l10n.atlasFullReportSubtitle,
                        // Tam rapor sınırsız uzunlukta bir metin; akışta
                        // yeri yok, kendi okuma sayfasında.
                        onTap: () => ac(ReadingScreen(
                          title: l10n.atlasFullReport,
                          label: l10n.atlasReadingNote,
                          body: data['report'] ?? '',
                        )),
                      ),
                    ),
                  ]),
                ]),
              ).animate(delay: next()).fadeIn(duration: 380.ms).slideY(
                  begin: 0.06, curve: Curves.easeOutCubic),
            ],
          );
            },
          ),
        ),
      ]),
    );
  }
}

/// Gezegen + burç etiketi, arayüz diline göre.
///
/// Backend her iki adı da döndürüyor (`name` İngilizce, `name_tr` Türkçe);
/// burç adı yalnızca Türkçe geldiği için indekse çevrilip yerelleştiriliyor.
String planetSignLabel(BuildContext context, Map<String, dynamic> p) {
  final l10n = AppLocalizations.of(context);
  final ingilizce = Localizations.localeOf(context).languageCode == 'en';
  final signIndex = kSignNamesTr.indexOf(p['sign_tr'] ?? '');
  final gezegen = (ingilizce ? p['name'] : p['name_tr']) ?? p['name'] ?? '';
  final burc = signIndex >= 0
      ? signDisplayName(l10n, signIndex)
      : (p['sign_tr'] ?? '');
  return '$gezegen — $burc';
}

/// Açıdaki iki gezegen: "Güneş — Satürn" / "Sun — Saturn".
///
/// Natal harita ucu her iki adı da döndürüyor (`p1` İngilizce, `p1_tr`).
String aspectPairLabel(BuildContext context, Map<String, dynamic> a) {
  final ingilizce = Localizations.localeOf(context).languageCode == 'en';
  final p1 = (ingilizce ? a['p1'] : a['p1_tr']) ?? a['p1'] ?? '';
  final p2 = (ingilizce ? a['p2'] : a['p2_tr']) ?? a['p2'] ?? '';
  return '$p1 — $p2';
}

/// Açı türü: "Kare" / "Square".
///
/// İngilizce alan kerykeion'dan küçük harfle geliyor ("square"), gösterirken
/// baş harfi büyütülür.
String aspectKindLabel(BuildContext context, Map<String, dynamic> a) {
  final ingilizce = Localizations.localeOf(context).languageCode == 'en';
  if (!ingilizce) return (a['aspect_tr'] ?? a['aspect'] ?? '').toString();
  final ham = (a['aspect'] ?? '').toString();
  if (ham.isEmpty) return '';
  return ham[0].toUpperCase() + ham.substring(1);
}

// `localizedSign` KALDIRILDI: tek çağıran `_PersonCard`'dı, o da profile
// taşındı. Analiz aracı kullanılmayan üst düzey fonksiyonu uyarmıyor, bu
// yüzden elle temizlendi.

/// Atlas dizin karosu — emoji + başlık + tek satır alt bilgi.
///
/// `_PersonCard`, `_PlanetGrid`, `_TraitBars` ve `_FoldSection` buradan
/// kalktı. İlki profile taşındı (orada düzenlenebilir), diğer üçü kendi
/// sayfalarına (bkz. atlas_detail_screens.dart). Katlanır bölüm de gitti:
/// aynı ekranda hem katlanan hem katlanmayan bölümler olması, neyin nereye
/// açılacağını tahmin edilemez kılıyordu.
class _AtlasTile extends StatelessWidget {
  const _AtlasTile({
    required this.emoji,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  final String emoji;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Pressable(
      onTap: onTap,
      child: Container(
        height: 104,
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: RythoColors.glassFill,
          borderRadius: BorderRadius.circular(RythoRadius.card),
          border: Border.all(color: RythoColors.glassStroke),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(emoji, style: const TextStyle(fontSize: 22)),
            const Spacer(),
            Text(title,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: RythoType.cardTitle),
            const SizedBox(height: 2),
            Text(subtitle,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: RythoType.caption),
          ],
        ),
      ),
    );
  }
}

/// Kehanet satırı: Yüz Okuma · İching · BaZi · Doğum Kapısı — eşit karolar.
///
/// Madde 11 (Revize R6): İching + BaZi Gökyüzü'ndeki ARAÇLAR bölümünden
/// buraya taşındı; kullanıcının istediği "tek satırda yan yana" düzen bu.
/// R10: sekmeli `OracleScreen` kalktı — her karo kendi bağımsız sayfasını
/// açıyor (karodan sonra sayfada aynı iki seçeneğin sekme olarak tekrar
/// çıkması kafa karıştırıyordu).
///
/// Yüz Okuma karosu ücretli uca **istek atmadan** kilit gösteriyor: abone
/// olmayan biri karoda 🔒 görür, dokununca paywall açılır, kamera hiç
/// başlamaz. Kamerayı açıp sonunda 402 almak, kullanıcıya yüzünü boşuna
/// taratmak olurdu. (Eski tam genişlik `FaceReadingEntry` kartının kuralı,
/// karo biçiminde devam ediyor.)
class _DivinationRow extends ConsumerWidget {
  const _DivinationRow();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final abonelik = ref.watch(subscriptionProvider);
    final faceAcik = abonelik.value?.active ?? false;

    void paywall() => Navigator.of(context).push(MaterialPageRoute(
          builder: (_) => const PaywallScreen(),
          fullscreenDialog: true,
        ));

    void ac(Widget sayfa) => Navigator.of(context)
        .push(MaterialPageRoute(builder: (_) => sayfa));

    return SizedBox(
      height: 100,
      child: Row(children: [
        Expanded(
          child: _DivinationTile(
            emoji: '👁️',
            title: l10n.faceReadingTitle,
            subtitle: l10n.faceReadingTileSubtitle,
            locked: !faceAcik,
            onTap: () =>
                faceAcik ? startFaceReading(context, ref) : paywall(),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _DivinationTile(
            emoji: '🪙',
            title: l10n.iChing,
            subtitle: l10n.iChingSubtitle,
            onTap: () => ac(const IChingScreen()),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _DivinationTile(
            emoji: '🀄',
            title: l10n.baZi,
            subtitle: l10n.baZiSubtitle,
            onTap: () => ac(const BaziScreen()),
          ),
        ),
        const SizedBox(width: 10),
        // Doğum Kapısı (İ5): çekim değil kimlik katmanı — abone değilken
        // kilit rozeti, dokununca paywall (Yüz Okuma karosuyla aynı kural).
        Expanded(
          child: _DivinationTile(
            emoji: '☯',
            title: l10n.birthHexagram,
            subtitle: l10n.birthHexagramSubtitle,
            locked: !faceAcik,
            onTap: () =>
                faceAcik ? ac(const BirthHexagramScreen()) : paywall(),
          ),
        ),
      ]),
    );
  }
}

/// Kehanet karosu — Gökyüzü'ndeki eski `_OracleCard`'ın üçlü satıra
/// sıkıştırılmış hâli. Üç karo yan yana ~110 px genişlik bırakır; alt yazı
/// tek satıra kırpılır, başlık taşarsa üç nokta alır.
class _DivinationTile extends StatelessWidget {
  const _DivinationTile({
    required this.emoji,
    required this.title,
    required this.subtitle,
    required this.onTap,
    this.locked = false,
  });

  final String emoji;
  final String title;
  final String subtitle;
  final VoidCallback onTap;
  final bool locked;

  @override
  Widget build(BuildContext context) {
    return Pressable(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: RythoColors.glassFill,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: RythoColors.glassStroke),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Text(emoji, style: const TextStyle(fontSize: 22)),
            const Spacer(),
            if (locked)
              const Icon(Icons.lock_rounded,
                  size: 13, color: RythoColors.parchmentDim),
          ]),
          const Spacer(),
          Text(title,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: RythoText.body(13.5, w: FontWeight.w700)),
          const SizedBox(height: 2),
          Text(subtitle,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: RythoText.body(10.5, color: RythoColors.parchmentDim)),
        ]),
      ),
    );
  }
}
