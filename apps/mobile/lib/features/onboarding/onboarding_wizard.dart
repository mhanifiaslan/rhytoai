/// Yıldız Yolu — ilk kurulum sihirbazı (O3).
///
/// Eski tek ekranlı onboarding'in yerini alır. Tasarım ilkeleri:
///
/// * **Adım başına tek soru** — bilişsel yük düşük, tamamlama yüksek.
/// * **Takımyıldız ilerleme** — her adım bir yıldız yakar; ilk yıldız
///   yanmış başlar (endowed progress). Finalde takımyıldız tamamlanır.
/// * **Anında mikro-ödül** — adım geçişinde yıldız pop'u + hafif haptik.
/// * **Dürüst atlama** — "Bilmiyorum" utandırmayan birinci sınıf seçenek;
///   neyin değişeceği bir cümleyle söylenir. Suçlayıcı dil yok.
/// * **Rıza baştan** — Google/Apple girişlerinde bugüne dek hiçbir onay
///   kutusu yoktu; ilk adım açık kabul kutusuyla bu boşluğu kapatır ve
///   kabul sunucuda ispatlanabilir kayda geçer (POST /account/consent).
/// * **Zirve sonda** — kayıt sırasında StagedWaiting (gerçek iş), sonra
///   mevcut Büyük Üçlü perdesi (AppShell köprüsü, R12-B1 düzeni korunur).
///
/// Taslak KALICI DEĞİL (bilinçli): akış 60-90 saniye; bayat "rıza
/// işaretliydi" taslağı rıza kanıtını zayıflatırdı.
library;

import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show HapticFeedback;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../core/analytics.dart';
import '../../core/api.dart';
import '../../core/birth_record.dart';
import '../../core/providers.dart'
    show OnboardOutcome, justOnboardedProvider;
import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/city_search_field.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/motion.dart';
import '../../core/notifications.dart'
    show ensureNotificationPermissionAsked;
import '../profile/legal_page.dart';
import '../profile/legal_texts.dart';
import '../profile/phone_verify_screen.dart';
import 'constellation_progress.dart';

/// İstemcinin gösterdiği şartlar/gizlilik metin sürümü — backend
/// `TERMS_CONSENT_VERSION` ile elle senkron (legal_texts güncellenince
/// ikisi birlikte artar).
const int kTermsConsentVersion = 1;

// `kPhoneStepEnabled` bayrağı SİLİNDİ (OT4, kullanıcı kararı): SMS ucu
// 2026-08-07'den beri canlı ve bu makinede üretilen yayın AAB'leri adımı
// zaten taşıyordu — bayrak yalnız test/temiz-checkout'u üretimden
// ayrıştıran ölü ağırlıktı. Adım artık herkese görünür ve "Sonra" ile
// atlanabilir; kullanıcı özellikleri aramak zorunda kalmadan kayıtta
// numarasını doğrular.

/// Sihirbaz adımları — sırası ürün sözleşmesidir ve testle sabitlidir
/// (OT4: `phone` artık bayraksız, herkese; `gender` sonrası, atlanabilir).
const List<String> kOnboardingSteps = [
  'welcome', 'date', 'time', 'place', 'gender', 'phone', 'notify',
];

class OnboardingWizard extends ConsumerStatefulWidget {
  const OnboardingWizard({super.key});

  @override
  ConsumerState<OnboardingWizard> createState() =>
      _OnboardingWizardState();
}

class _OnboardingWizardState extends ConsumerState<OnboardingWizard> {
  final _sayfa = PageController();
  int _adim = 0;

  // ---- taslak ----
  bool _riza = false;
  DateTime? _tarih;
  TimeOfDay _saat = const TimeOfDay(hour: 12, minute: 0);
  bool _saatBiliniyor = true;
  bool _saatSecildi = false;
  String? _sehir;
  String? _ulke;
  String _cinsiyet = 'female';
  bool _busy = false;

  static const _adimAdlari = kOnboardingSteps;

  int get _toplamAdim => _adimAdlari.length;

  /// Atlanabilir adımlar: zorunlu veri istemezler, alt düğme "Sonra" der.
  bool get _atlanabilirAdim =>
      _adimAdlari[_adim] == 'phone' || _adimAdlari[_adim] == 'notify';

  @override
  void initState() {
    super.initState();
    Analytics.onboardingStep('welcome');
  }

  @override
  void dispose() {
    _sayfa.dispose();
    super.dispose();
  }

  /// Adım ilerleyebilir mi — düğme durumu buradan.
  bool get _ilerleyebilir => switch (_adimAdlari[_adim]) {
        'welcome' => _riza,
        'date' => _tarih != null,
        'time' => !_saatBiliniyor || _saatSecildi,
        'place' => _sehir != null && _sehir!.trim().isNotEmpty,
        _ => true,
      };

  void _ileri() {
    if (!_ilerleyebilir || _busy) return;
    HapticFeedback.lightImpact();
    if (_adim == _toplamAdim - 1) {
      _bitir();
      return;
    }
    setState(() => _adim++);
    Analytics.onboardingStep(_adimAdlari[_adim]);
    _sayfa.animateToPage(_adim,
        duration: reduceMotion(context)
            ? Duration.zero
            : const Duration(milliseconds: 380),
        curve: Curves.easeOutCubic);
  }

  void _geri() {
    if (_adim == 0 || _busy) return;
    setState(() => _adim--);
    _sayfa.animateToPage(_adim,
        duration: reduceMotion(context)
            ? Duration.zero
            : const Duration(milliseconds: 320),
        curve: Curves.easeOutCubic);
  }

  Future<void> _bitir() async {
    final user = FirebaseAuth.instance.currentUser!;
    setState(() => _busy = true);
    // OT3: "Haritamı çiz ✨" yolculuğu bitirirken BİLDİRİM İZNİNİ DE
    // İSTER. Eski akışta izin yalnız adım içindeki düğmeye bağlıydı;
    // kullanıcı doğrudan bitir'e basınca hiç sorulmuyor, ikinci şans da
    // tanıtım paywall'ına yeniliyordu — "yeni kullanıcıya bildirim
    // gitmiyor"un kökü. Sonuç yolculuğu ASLA engellemez.
    try {
      await ensureNotificationPermissionAsked();
    } catch (e) {
      debugPrint('Onboarding bildirim izni istenemedi: $e');
    }
    // Büyük Üçlü perdesinin bayrağı yazım ÖNCESİ konur (R12-B1):
    // onboardingCompleted iner inmez _Gate bu ekranı söküp AppShell'i
    // takıyor — sonuç o anda hazır olmalı. Hata olursa geri iner.
    ref.read(justOnboardedProvider.notifier).state = OnboardOutcome.chartOk;
    try {
      // Kimlik alanları yalnızca ilk kurulumda yazılır; doğum verisi ve
      // Büyük Üçlü ortak yoldan gider (core/birth_record.dart) — profil
      // düzeltme ekranıyla aynı kod.
      await FirebaseFirestore.instance
          .collection('users')
          .doc(user.uid)
          .set({
        'uid': user.uid,
        'displayName': user.displayName ?? 'Gezgin',
        'photoUrl': user.photoURL,
        'email': user.email,
        'createdAt': FieldValue.serverTimestamp(),
      }, SetOptions(merge: true));

      // Kabul kaydı — EN İYİ ÇABA: uç ispat tutar, kilit değildir; kaydın
      // düşmesi kurulumun tamamını düşürmemeli (kutu işaretlenmeden bu
      // noktaya gelinemiyor).
      try {
        await ref.read(apiProvider).post('/api/v1/account/consent',
            data: {'version': kTermsConsentVersion});
      } catch (_) {}

      final sonuc = await saveBirthRecord(
        BirthRecord(
          date: _tarih!,
          time: !_saatBiliniyor
              ? null
              : '${_saat.hour.toString().padLeft(2, '0')}:'
                  '${_saat.minute.toString().padLeft(2, '0')}',
          city: _sehir!.trim(),
          gender: _cinsiyet,
          nation: _ulke,
        ),
        dio: ref.read(apiProvider),
      );
      if (sonuc == BirthSaveResult.savedWithoutChart) {
        // AppShell köprüsü dürüst bildirimi buradan okur (O3).
        ref.read(justOnboardedProvider.notifier).state =
            OnboardOutcome.chartMissing;
      }
      Analytics.onboardingStep('done');
    } catch (e) {
      ref.read(justOnboardedProvider.notifier).state = null;
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(AppLocalizations.of(context).onboardingFailed)));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _tarihSec() async {
    final secilen = await showDatePicker(
      context: context,
      initialDate: _tarih ?? DateTime(2000, 1, 1),
      firstDate: DateTime(1930),
      lastDate: DateTime.now(),
    );
    if (secilen != null) setState(() => _tarih = secilen);
  }

  Future<void> _saatSec() async {
    final secilen =
        await showTimePicker(context: context, initialTime: _saat);
    if (secilen != null) {
      setState(() {
        _saat = secilen;
        _saatSecildi = true;
        _saatBiliniyor = true;
      });
    }
  }

  Future<void> _sehirSec() async {
    final secim = await showCitySearch(context, initialQuery: _sehir);
    if (secim == null) return;
    setState(() {
      _sehir = secim.name;
      _ulke = secim.nation.isEmpty ? null : secim.nation;
    });
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return PopScope(
      // Geri tuşu adım geri gider; ilk adımda hiçbir şey yapmaz (çıkış
      // yok: sihirbaz zorunlu verinin toplandığı yer).
      canPop: false,
      onPopInvokedWithResult: (didPop, result) => _geri(),
      child: CosmicScaffold(
        body: SafeArea(
          child: Column(children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 8, 24, 0),
              child: Row(children: [
                SizedBox(
                  width: 40,
                  child: _adim > 0 && !_busy
                      ? IconButton(
                          onPressed: _geri,
                          icon: const Icon(Icons.arrow_back_rounded,
                              size: 20, color: RythoColors.parchmentDim),
                        )
                      : null,
                ),
                Expanded(
                  // İlk yıldız yanmış başlar: hesabını açtın bile.
                  child: ConstellationProgress(
                      total: _toplamAdim + 1, lit: _adim + 1),
                ),
                const SizedBox(width: 40),
              ]),
            ),
            Expanded(
              child: PageView(
                controller: _sayfa,
                // Kaydırmayla adım atlanamaz — adım başına tek soru
                // ilkesi; geçiş yalnız düğmeyle.
                physics: const NeverScrollableScrollPhysics(),
                children: [
                  _KarsilamaAdimi(
                    riza: _riza,
                    onRiza: (v) => setState(() => _riza = v),
                  ),
                  _AdimSayfasi(
                    emoji: '🌌',
                    baslik: l10n.wizardDateTitle,
                    govde: l10n.wizardDateBody,
                    child: _SecimSatiri(
                      label: l10n.birthDate,
                      value: _tarih == null
                          ? '—'
                          : DateFormat('d MMMM yyyy',
                                  Localizations.localeOf(context)
                                      .toLanguageTag())
                              .format(_tarih!),
                      onTap: _tarihSec,
                    ),
                  ),
                  _AdimSayfasi(
                    emoji: '🕰️',
                    baslik: l10n.wizardTimeTitle,
                    govde: l10n.wizardTimeBody,
                    child: Column(children: [
                      _SecimSatiri(
                        label: l10n.birthTime,
                        value: !_saatBiliniyor
                            ? '—'
                            : (_saatSecildi
                                ? '${_saat.hour.toString().padLeft(2, '0')}:'
                                    '${_saat.minute.toString().padLeft(2, '0')}'
                                : '—'),
                        onTap: _saatSec,
                      ),
                      const SizedBox(height: 12),
                      // "Bilmiyorum" birinci sınıf, utandırmayan seçenek.
                      // Neyin değişeceği dürüstçe söylenir; sunucu saatsiz
                      // doğumda ev/Yükselen üretmez ve bunu beyan eder.
                      CheckboxListTile(
                        value: !_saatBiliniyor,
                        onChanged: (v) => setState(
                            () => _saatBiliniyor = !(v ?? false)),
                        controlAffinity: ListTileControlAffinity.leading,
                        contentPadding: EdgeInsets.zero,
                        dense: true,
                        title: Text(l10n.birthTimeUnknown,
                            style: RythoText.body(13.5,
                                color: RythoColors.parchment)),
                        subtitle: Text(l10n.wizardTimeUnknownNote,
                            style: RythoText.body(11.5,
                                color: RythoColors.copper)),
                      ),
                    ]),
                  ),
                  _AdimSayfasi(
                    emoji: '🗺️',
                    baslik: l10n.wizardPlaceTitle,
                    govde: l10n.wizardPlaceBody,
                    child: _SecimSatiri(
                      label: l10n.onboardingCity,
                      value: _sehir == null
                          ? '—'
                          : '${_ulke == null ? '' : '${flagEmoji(_ulke!)} '}'
                              '$_sehir',
                      onTap: _sehirSec,
                    ),
                  ),
                  _AdimSayfasi(
                    emoji: '🌗',
                    baslik: l10n.wizardGenderTitle,
                    govde: l10n.wizardGenderBody,
                    child: _CinsiyetSecimi(
                      secili: _cinsiyet,
                      onSec: (g) => setState(() => _cinsiyet = g),
                    ),
                  ),
                  // Telefon (O4 → OT4: artık herkese): rehber
                  // eşleşmesinin kapısı — atlanabilir, hiçbir çekirdek
                  // özellik buna kilitlenmez (mağaza kuralı). Mevcut
                  // PhoneVerifyScreen olduğu gibi yeniden kullanılır.
                  _AdimSayfasi(
                    emoji: '🤝',
                    baslik: l10n.wizardPhoneTitle,
                    govde: l10n.wizardPhoneBody,
                    child: _TelefonAdimi(onVerified: () {
                      if (mounted) setState(() {});
                    }),
                  ),
                  // Bildirim izni: sürpriz sistem dialogu yerine önce
                  // değer önerisi (kabul oranını artıran sıra). İzin
                  // verilirse sky_screen'deki eski istem kendiliğinden
                  // devre dışı kalır; atlanırsa oradaki tek seferlik
                  // istem ikinci şans olarak yaşamaya devam eder.
                  _AdimSayfasi(
                    emoji: '🔔',
                    baslik: l10n.wizardNotifyTitle,
                    govde: l10n.wizardNotifyBody,
                    child: _BildirimAdimi(onDone: _ileri),
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 4, 24, 20),
              child: _busy
                  // Kayıt sırasında sahne (R12-B1): harita bu esnada
                  // GERÇEKTEN hesaplanıyor — aşamalar süs değil.
                  ? StagedWaiting(
                      stages: [
                        l10n.onboardingStage1,
                        l10n.onboardingStage2,
                        l10n.onboardingStage3,
                      ],
                      interval: const Duration(milliseconds: 1600),
                    )
                  : GoldButton(
                      // Atlanabilir adımda alt düğme DÜRÜST "Sonra"dır —
                      // asıl eylem adımın içindeki düğmede. Son adımda
                      // yolculuk "Haritamı çiz"le biter.
                      text: _adim == _toplamAdim - 1
                          ? l10n.wizardFinish
                          : (_atlanabilirAdim
                              ? l10n.wizardLater
                              : l10n.wizardNext),
                      onPressed: _ilerleyebilir ? _ileri : null,
                    ),
            ),
          ]),
        ),
      ),
    );
  }
}

/// Karşılama + rıza (adım 0). Yolun vaadi + tek zorunlu kutu.
class _KarsilamaAdimi extends StatelessWidget {
  const _KarsilamaAdimi({required this.riza, required this.onRiza});

  final bool riza;
  final ValueChanged<bool> onRiza;

  void _ac(BuildContext context, String title, LegalSections tr,
      LegalSections en) {
    final ingilizce =
        Localizations.localeOf(context).languageCode == 'en';
    Navigator.of(context).push(MaterialPageRoute(
        builder: (_) =>
            LegalPage(title: title, sections: ingilizce ? en : tr)));
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    var sira = 0;
    return ListView(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      children: [
        const SizedBox(height: 24),
        RythoReveal(
          index: sira++,
          slide: 0,
          child: Text('✨', style: const TextStyle(fontSize: 40)),
        ),
        const SizedBox(height: 12),
        RythoReveal(
          index: sira++,
          slide: 0.1,
          child:
              Text(l10n.wizardWelcomeTitle, style: RythoText.display(30)),
        ),
        const SizedBox(height: 10),
        RythoReveal(
          index: sira++,
          slide: 0,
          child: Text(l10n.wizardWelcomeBody,
              style: RythoText.body(14.5,
                  color: RythoColors.parchmentDim)),
        ),
        const SizedBox(height: 24),
        RythoReveal(
          index: sira++,
          slide: 0.06,
          child: Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: RythoColors.inkLighter,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: RythoColors.glassStroke),
            ),
            // ListTile mürekkep efektini en yakın Material'e çizer; dekorlu
            // kutu altında Material yoksa debug assert'i test düşürür.
            child: Material(
              type: MaterialType.transparency,
              child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                CheckboxListTile(
                  value: riza,
                  onChanged: (v) => onRiza(v ?? false),
                  controlAffinity: ListTileControlAffinity.leading,
                  contentPadding: EdgeInsets.zero,
                  dense: true,
                  // Tek kutu: şartlar + gizlilik + 13 yaş beyanı. Google/
                  // Apple girişinde bugüne dek hiçbir kutu yoktu (O3).
                  title: Text(l10n.wizardConsentLabel,
                      style: RythoText.body(13,
                          color: RythoColors.parchment)),
                ),
                Row(children: [
                  TextButton(
                    onPressed: () => _ac(context, l10n.termsOfUse,
                        kTermsOfUseTr, kTermsOfUseEn),
                    child: Text(l10n.termsOfUse,
                        style: RythoText.body(12,
                            color: RythoColors.lilac)),
                  ),
                  TextButton(
                    onPressed: () => _ac(context, l10n.privacyPolicy,
                        kPrivacyPolicyTr, kPrivacyPolicyEn),
                    child: Text(l10n.privacyPolicy,
                        style: RythoText.body(12,
                            color: RythoColors.lilac)),
                  ),
                ]),
              ],
              ),
            ),
          ),
        ),
        const SizedBox(height: 8),
        RythoReveal(
          index: sira++,
          slide: 0,
          child: Text(l10n.insightDisclaimer,
              style:
                  RythoText.body(11, color: RythoColors.parchmentDim)),
        ),
      ],
    );
  }
}

/// Ortak adım sayfası: emoji + başlık + tek cümle + giriş bileşeni.
class _AdimSayfasi extends StatelessWidget {
  const _AdimSayfasi({
    required this.emoji,
    required this.baslik,
    required this.govde,
    required this.child,
  });

  final String emoji;
  final String baslik;
  final String govde;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    var sira = 0;
    return ListView(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      children: [
        const SizedBox(height: 28),
        RythoReveal(
          index: sira++,
          slide: 0,
          child: Text(emoji, style: const TextStyle(fontSize: 36)),
        ),
        const SizedBox(height: 12),
        RythoReveal(
          index: sira++,
          slide: 0.1,
          child: Text(baslik, style: RythoText.display(26)),
        ),
        const SizedBox(height: 8),
        RythoReveal(
          index: sira++,
          slide: 0,
          child: Text(govde,
              style:
                  RythoText.body(14, color: RythoColors.parchmentDim)),
        ),
        const SizedBox(height: 24),
        RythoReveal(index: sira++, slide: 0.08, child: child),
      ],
    );
  }
}

class _SecimSatiri extends StatelessWidget {
  const _SecimSatiri(
      {required this.label, required this.value, required this.onTap});

  final String label;
  final String value;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        decoration: BoxDecoration(
          color: RythoColors.inkLighter,
          border: Border.all(color: RythoColors.glassStroke),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Row(children: [
          Text(label,
              style:
                  RythoText.label(12, color: RythoColors.parchmentDim)),
          const Spacer(),
          Text(value,
              style: RythoText.mono(15, color: RythoColors.parchment)),
          const SizedBox(width: 8),
          const Icon(Icons.edit_outlined,
              size: 15, color: RythoColors.lilac),
        ]),
      ),
    );
  }
}

class _CinsiyetSecimi extends StatelessWidget {
  const _CinsiyetSecimi({required this.secili, required this.onSec});

  final String secili;
  final ValueChanged<String> onSec;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Row(children: [
      for (final g in [
        ('female', l10n.genderFemale),
        ('male', l10n.genderMale),
        ('other', l10n.genderOther),
      ]) ...[
        Expanded(
          child: GestureDetector(
            onTap: () => onSec(g.$1),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 240),
              curve: Curves.easeOutCubic,
              height: 48,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                gradient:
                    secili == g.$1 ? RythoColors.primaryGradient : null,
                color: secili == g.$1 ? null : RythoColors.inkLight,
                border: Border.all(
                    color: secili == g.$1
                        ? Colors.white.withValues(alpha: 0.2)
                        : RythoColors.glassStroke),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Text(g.$2,
                  style: RythoText.body(14,
                      w: FontWeight.w600,
                      color: secili == g.$1
                          ? Colors.white
                          : RythoColors.parchmentDim)),
            ),
          ),
        ),
        if (g.$1 != 'other') const SizedBox(width: 8),
      ],
    ]);
  }
}

/// Telefon adımı içeriği (O4): mevcut PhoneVerifyScreen'i olduğu gibi
/// açar — doğrulama akışı TEK yerde kalır. Dönüşte durum tazelenir;
/// doğrulanmışsa yeşil onay görünür.
class _TelefonAdimi extends StatelessWidget {
  const _TelefonAdimi({required this.onVerified});

  final VoidCallback onVerified;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final dogrulandi =
        FirebaseAuth.instance.currentUser?.phoneNumber != null;
    if (dogrulandi) {
      return Row(children: [
        const Icon(Icons.check_circle_rounded,
            size: 20, color: RythoColors.goldBright),
        const SizedBox(width: 8),
        Text(l10n.wizardPhoneDone,
            style: RythoText.body(14, w: FontWeight.w600)),
      ]);
    }
    return GoldButton(
      text: l10n.wizardPhoneVerify,
      onPressed: () async {
        await Navigator.of(context).push(MaterialPageRoute(
            builder: (_) => const PhoneVerifyScreen()));
        onVerified();
      },
    );
  }
}

/// Bildirim izni adımı içeriği (O4): sistem dialogu ancak kullanıcı
/// değer önerisini okuyup istediğinde açılır. İzin istendiyse (sonuç ne
/// olursa olsun) tek seferlik bayrak işaretlenir — sky_screen bir daha
/// sormaz. Adım atlanırsa bayrak DOKUNULMAZ: oradaki istem ikinci şans.
class _BildirimAdimi extends StatefulWidget {
  const _BildirimAdimi({required this.onDone});

  final VoidCallback onDone;

  @override
  State<_BildirimAdimi> createState() => _BildirimAdimiState();
}

class _BildirimAdimiState extends State<_BildirimAdimi> {
  bool _busy = false;

  Future<void> _izinIste() async {
    setState(() => _busy = true);
    try {
      // OT3: ortak yardımcı — önce iste, bayrağı SONRA yaz (sıra tek
      // yerde). Bitir düğmesi de aynı yardımcıyı çağırdığı için hangi
      // yoldan çıkılırsa çıkılsın izin bir kez istenmiş olur.
      await ensureNotificationPermissionAsked();
    } catch (_) {
      // İzin akışı düşerse yolculuk düşmez; sky_screen ikinci şansı verir.
    }
    if (mounted) widget.onDone();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return GoldButton(
      text: l10n.wizardNotifyAllow,
      busy: _busy,
      onPressed: _busy ? null : _izinIste,
    );
  }
}
