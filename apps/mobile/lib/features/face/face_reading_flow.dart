/// Yüz okuma akışı: (gerekiyorsa rıza) → çekim → okuma.
///
/// Rıza **bir kez** alınır ve sunucuda saklanır; her çekimde sorulmaz.
/// İlk sürümde her seferinde soruluyordu ve bu fazla temkinliydi: rızanın
/// **geri alınabilir** olması gerekiyor, her seferinde yeniden sorulması
/// değil. Geri alma Profil > Gizlilik'te.
///
/// Öbür uçtaki hata da geçerli değil — rızayı üyelik sözleşmesine ya da
/// gizlilik metnine gömmek işe yaramaz. Biyometrik veri özel nitelikli
/// (GDPR Md.9 / KVKK md.6) ve rıza **ayrı, açık ve başka şartlarla
/// paketlenmemiş** olmalı. O yüzden ayrı ekran ve ayrı onay kutusu var.
library;

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api.dart';
import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart' show AstrolabeSpinner;
import '../../widgets/glass.dart';
import '../profile/legal_page.dart' show LegalPage, privacyPolicySections;
import 'face_api.dart';
import 'face_capture_screen.dart';
import 'face_consent.dart';

/// Akışın giriş noktası — ve **akışın tek sahibi**.
///
/// Üç adım burada sırayla yürütülüyor: rıza → çekim → okuma. Her adım kendi
/// rotasında açılıyor ve sonucunu buraya döndürüyor.
///
/// Bu yapı iki gerçek kusurdan sonra böyle kuruldu:
///
/// 1. İlk sürümde rıza durumu burada BEKLENİYORDU; kullanıcı karta dokunuyor
///    ve ağ turu bitene kadar hiçbir şey olmuyordu. Artık ekran hemen açılıyor,
///    bekleme onun içinde görünüyor.
/// 2. Sonraki sürümde rıza kapısı kameraya kendisi geçiyor ve bunu
///    `pushReplacement` ile yapıp `await` ediyordu. `pushReplacement` kapının
///    kendi rotasını YOK EDİYOR: State rotası silindikten sonra uyanıyordu ve
///    uygulama `'_dependents.isEmpty': is not true` diye çöküyordu. Üstelik
///    kapının future'ı o anda `null` ile kapandığı için çekim sonucu buraya
///    hiç ulaşmıyor, okuma ekranı hiç açılmıyordu.
///
/// Kural: **hiçbir ekran kendi rotasını değiştirip onu beklemez.** Ekranlar
/// yalnızca `pop` ile değer döndürür; sırayı burası kurar.
Future<void> startFaceReading(BuildContext context, WidgetRef ref) async {
  final riza = await Navigator.of(context).push<bool>(
    MaterialPageRoute(builder: (_) => const FaceConsentGate()),
  );
  if (riza != true || !context.mounted) return;

  final sonuc = await Navigator.of(context).push<FaceCaptureResult>(
    MaterialPageRoute(builder: (_) => const FaceCaptureScreen()),
  );
  if (sonuc == null || !context.mounted) return;

  await Navigator.of(context).push(MaterialPageRoute(
    builder: (_) => FaceReadingScreen(result: sonuc),
  ));
}

/// Rıza kapısı: durumu çözer, gerekiyorsa sorar ve **yalnızca `true`/`null`
/// döndürür.**
///
/// Bu ekran kamerayı AÇMAZ. Bir tek şeye karar verir: rıza var mı? Sırayı
/// kuran [startFaceReading]. Bölüşüm böyle olmasaydı — ve bir süre öyle
/// değildi — kapı kendi rotasını `pushReplacement` ile yok edip onu
/// beklerdi; State rotası silindikten sonra uyanır ve uygulama
/// `'_dependents.isEmpty': is not true` diye çökerdi.
///
/// Rıza durumu **bir kez okunur** (`ref.read`), izlenmez: bu ekranın işi tek
/// bir karar vermek, sonrasında durumun değişmesi onu ilgilendirmiyor.
/// İzleseydi, onay yazıldığında gelen `invalidate` kapıyı yeniden kurar ve
/// ikinci bir gezinme doğardı.
class FaceConsentGate extends ConsumerStatefulWidget {
  const FaceConsentGate({super.key});

  @override
  ConsumerState<FaceConsentGate> createState() => _FaceConsentGateState();
}

enum _Asama { cozuluyor, riza }

class _FaceConsentGateState extends ConsumerState<FaceConsentGate> {
  _Asama _asama = _Asama.cozuluyor;
  bool _kapandi = false;

  @override
  void initState() {
    super.initState();
    _durumuCoz();
  }

  Future<void> _durumuCoz() async {
    FaceConsent durum;
    try {
      // Zaman sınırı gerçek bir kusura karşı: Dio'nun alım zaman aşımı 120
      // saniye ve sunucu yanıt vermezse kullanıcı o kadar süre dönen bir
      // göstergeye bakıyordu. Sınır dolarsa rıza sorulur — bekletmek yerine
      // güvenli tarafa düşülür.
      durum = await ref
          .read(faceConsentProvider.future)
          .timeout(const Duration(seconds: 12));
    } catch (_) {
      // Durum okunamazsa rıza YOK sayılır ve sorulur; sessizce geçmek
      // biyometrik işlemeyi rızasız açmak olurdu.
      durum = FaceConsent.unknown;
    }
    if (!mounted) return;
    if (durum.granted) {
      _tamam();
    } else {
      setState(() => _asama = _Asama.riza);
    }
  }

  /// Kapıyı olumlu kapatır. Tek seferlik: `pop` iki kez çağrılırsa altındaki
  /// rota da kapanır.
  void _tamam() {
    if (_kapandi || !mounted) return;
    _kapandi = true;
    Navigator.of(context).pop(true);
  }

  @override
  Widget build(BuildContext context) {
    if (_asama == _Asama.riza) {
      return _ConsentForm(onGranted: _tamam);
    }
    return Scaffold(
      appBar:
          AppBar(title: Text(AppLocalizations.of(context).faceReadingTitle)),
      body: const Center(child: CircularProgressIndicator()),
    );
  }
}

// ---------------------------------------------------------------------------
// Rıza
// ---------------------------------------------------------------------------

/// Rıza formu. **Gezinmez** — onay yazıldığında [onGranted] çağırır.
///
/// Bu ayrım kasıtlı: gezinmeyi kapı yönetiyor. Formun hem sağlayıcıya hem
/// gezinmeye dokunması, çöken sürümün ta kendisiydi.
class _ConsentForm extends ConsumerStatefulWidget {
  const _ConsentForm({required this.onGranted});

  final VoidCallback onGranted;

  @override
  ConsumerState<_ConsentForm> createState() => _ConsentFormState();
}

class _ConsentFormState extends ConsumerState<_ConsentForm> {
  bool _onaylandi = false;
  bool _kaydediliyor = false;
  String? _hata;

  /// Onayı sunucuya yazar ve kararı kapıya devreder.
  Future<void> _onayla() async {
    setState(() {
      _kaydediliyor = true;
      _hata = null;
    });
    try {
      await grantFaceConsent(ref.read(apiProvider));
      // Profil > Gizlilik ekranı bu sağlayıcıyı izliyor; oradaki durum güncel
      // kalsın. Bu kapı artık İZLEMEDİĞİ için yeniden kurulma olmuyor.
      ref.invalidate(faceConsentProvider);
      if (!mounted) return;
      widget.onGranted();
    } catch (e) {
      // Hata SNACKBAR değil ekranda: snackbar kaybolup gidiyor ve kullanıcı
      // neden geri atıldığını anlamıyordu.
      if (!mounted) return;
      setState(() {
        _kaydediliyor = false;
        _hata = friendlyError(e, AppLocalizations.of(context));
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.faceReadingTitle)),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 28),
          children: [
            Text(l10n.faceConsentTitle, style: RythoText.display(20)),
            const SizedBox(height: 16),
            GlassPanel(
              child: Text(l10n.faceConsentBody,
                  style: RythoText.body(14, color: RythoColors.parchment)),
            ),
            const SizedBox(height: 8),
            TextButton(
              onPressed: () => Navigator.of(context).push(MaterialPageRoute(
                builder: (_) => LegalPage(
                  title: l10n.privacyPolicy,
                  sections: privacyPolicySections(
                      Localizations.localeOf(context).languageCode),
                ),
              )),
              child: Text(l10n.faceConsentLearnMore),
            ),
            const SizedBox(height: 8),
            // Ayrı onay kutusu: "devam"a basmayı rıza saymak açık rıza
            // değildir. Varsayılan KAPALI.
            CheckboxListTile(
              value: _onaylandi,
              onChanged: (v) => setState(() => _onaylandi = v ?? false),
              controlAffinity: ListTileControlAffinity.leading,
              contentPadding: EdgeInsets.zero,
              title: Text(l10n.faceConsentCheckbox,
                  style: RythoText.body(13.5)),
            ),
            if (_hata != null) ...[
              const SizedBox(height: 4),
              Text(_hata!,
                  style: RythoText.body(13, color: RythoColors.madder)),
            ],
            const SizedBox(height: 12),
            FilledButton(
              onPressed: (_onaylandi && !_kaydediliyor) ? _onayla : null,
              child: _kaydediliyor
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : Text(l10n.faceConsentContinue),
            ),
          ],
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Okuma
// ---------------------------------------------------------------------------

class FaceReadingScreen extends ConsumerStatefulWidget {
  const FaceReadingScreen({super.key, required this.result});

  final FaceCaptureResult result;

  @override
  ConsumerState<FaceReadingScreen> createState() => _FaceReadingScreenState();
}

class _FaceReadingScreenState extends ConsumerState<FaceReadingScreen> {
  late final Future<String> _okuma =
      fetchFirasaReading(ref.read(apiProvider), widget.result);

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.faceReadingTitle)),
      body: SafeArea(
        child: FutureBuilder<String>(
          future: _okuma,
          builder: (context, snap) {
            if (snap.connectionState != ConnectionState.done) {
              return const _FirasaWaiting();
            }
            if (snap.hasError) {
              return Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text(friendlyError(snap.error ?? Exception(), l10n),
                      textAlign: TextAlign.center,
                      style: RythoText.body(14)),
                ),
              );
            }
            return ListView(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 28),
              children: [
                // Geleneğin kendi sınırı okumanın ÜSTÜNDE duruyor, altında
                // değil: kullanıcı metni okumadan önce neye baktığını bilmeli.
                Text(l10n.faceReadingHint,
                    style: RythoText.body(12.5,
                        color: RythoColors.parchmentDim)),
                // Galeri fotoğrafında saç çizgisi TEK kareden ölçülüyor
                // (kamerada 3+ örneğin medyanı). Ölçümün dayanağı zayıfsa
                // bu söylenmek zorunda — "gerçek veriler ne diyorsa onu
                // söylemek" beyandaki payı da kapsıyor.
                if (widget.result.singleFrame) ...[
                  const SizedBox(height: 6),
                  Text(l10n.faceStillSingleFrameNote,
                      style: RythoText.body(12.5,
                          color: RythoColors.parchmentDim)),
                ],
                const SizedBox(height: 16),
                GlassPanel(
                  child: Text(snap.data ?? '',
                      style: RythoText.body(15, color: RythoColors.parchment)),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}

/// Okuma beklerken görünen sahne — çıplak spinner değil (Revize R5,
/// madde 8: "Firaset ile eşleştiriliyor" ekranı sıkıcıydı).
///
/// Çekimdeki tarama sahnesinin görsel dilini sürdürüyor: usturlap
/// döngüsü + sırayla değişen aşama metinleri. Metinler gerçek işi
/// anlatıyor (oranlar karşılaştırılıyor → kaynaklar taranıyor → okuma
/// yazılıyor); uydurma bir yüzde çubuğu YOK — sürecin süresi LLM'e bağlı
/// ve bilinmiyor, bilmediğimiz şeyi biliyormuş gibi göstermiyoruz.
class _FirasaWaiting extends StatefulWidget {
  const _FirasaWaiting();

  @override
  State<_FirasaWaiting> createState() => _FirasaWaitingState();
}

class _FirasaWaitingState extends State<_FirasaWaiting> {
  int _asama = 0;
  Timer? _sayac;

  @override
  void initState() {
    super.initState();
    // Son aşamada DURUYOR: dönüp başa saran metin "takıldı" hissi verir.
    _sayac = Timer.periodic(const Duration(milliseconds: 2600), (t) {
      if (!mounted) return;
      if (_asama >= 2) {
        t.cancel();
        return;
      }
      setState(() => _asama++);
    });
  }

  @override
  void dispose() {
    _sayac?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final metin = switch (_asama) {
      0 => l10n.faceWaitStage1,
      1 => l10n.faceWaitStage2,
      _ => l10n.faceWaitStage3,
    };
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const AstrolabeSpinner(),
          const SizedBox(height: 20),
          AnimatedSwitcher(
            duration: const Duration(milliseconds: 380),
            transitionBuilder: (child, anim) => FadeTransition(
              opacity: anim,
              child: SlideTransition(
                position: Tween(
                        begin: const Offset(0, 0.3), end: Offset.zero)
                    .animate(CurvedAnimation(
                        parent: anim, curve: Curves.easeOutCubic)),
                child: child,
              ),
            ),
            child: Text(
              metin,
              key: ValueKey(_asama),
              textAlign: TextAlign.center,
              style: RythoText.body(14, color: RythoColors.parchmentDim),
            ),
          ),
        ],
      ),
    );
  }
}
