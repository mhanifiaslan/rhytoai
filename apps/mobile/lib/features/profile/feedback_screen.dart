/// Uygulama içi geri bildirim (GB-turu).
///
/// Kullanıcının bize ulaşabildiği tek yer mağaza yorumuydu; oradan ne
/// cihaz ne sürüm ne de hangi ekranda olduğu öğreniliyordu, yanıt da
/// verilemiyordu. Bu ekran üç şeyi sabitler:
///
/// 1. Gövde küçük ve kapalı kümeli: `type` (bug/suggestion/other), `text`
///    (10..2000) ve isteğe bağlı `screen` (sabit ekran kodu). Sürüm, cihaz
///    ve dil zaten her istekte başlıkla gider (`X-App-Build`, `X-Device-*`,
///    `Accept-Language`) — burada tekrar yazılmaz, kullanıcıya söylenir.
/// 2. Yanıt bildirimle döner (`type=feedback`); dokunuş yalnız uygulamayı
///    açar (bkz. core/notifications.dart).
/// 3. Hata metni sunucunun `detail`'idir (429 günlük tavan dahil) —
///    `friendlyError` ile; ham DioException hiç ekrana çıkmaz.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/analytics.dart';
import '../../core/api.dart' show apiProvider, friendlyError;
import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import '../../theme/rytho_tokens.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/glass.dart';
import '../../widgets/motion.dart';
import '../../widgets/nebula_widgets.dart' show Pressable;

/// Sunucu sözleşmesindeki tür kodları — segment sırasıyla aynı.
const List<String> kFeedbackTypes = ['bug', 'suggestion', 'other'];

/// Ekran kodları (sözleşme: `screen` ≤ 60 karakter, serbest). Kapalı küme
/// bilinçli: sunucu tarafında sayılabilsin, kullanıcı yazmak zorunda
/// kalmasın.
const List<String> kFeedbackScreens = [
  'sky',
  'atlas',
  'chat',
  'circle',
  'oracle',
  'profile',
  'other',
];

/// Gönder düğmesinin açıldığı en kısa metin.
const int kFeedbackMinChars = 10;

/// Sunucunun kabul ettiği en uzun metin.
const int kFeedbackMaxChars = 2000;

class FeedbackScreen extends ConsumerStatefulWidget {
  const FeedbackScreen({super.key, this.screen});

  /// Hangi ekrandan açıldığı ([kFeedbackScreens] kodu); listede yoksa
  /// seçim boş kalır ve kullanıcı kendisi seçer.
  final String? screen;

  @override
  ConsumerState<FeedbackScreen> createState() => _FeedbackScreenState();
}

class _FeedbackScreenState extends ConsumerState<FeedbackScreen> {
  final _metin = TextEditingController();
  int _tur = 0;
  String? _ekran;
  bool _mesgul = false;
  bool _gonderildi = false;

  @override
  void initState() {
    super.initState();
    final s = widget.screen;
    if (s != null && kFeedbackScreens.contains(s)) _ekran = s;
    _metin.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _metin.dispose();
    super.dispose();
  }

  String get _temiz => _metin.text.trim();

  bool get _gonderilebilir =>
      _temiz.length >= kFeedbackMinChars && _temiz.length <= kFeedbackMaxChars;

  Future<void> _gonder() async {
    if (!_gonderilebilir || _mesgul) return;
    final l10n = AppLocalizations.of(context);
    final mesajci = ScaffoldMessenger.of(context);
    FocusScope.of(context).unfocus();
    setState(() => _mesgul = true);
    final tur = kFeedbackTypes[_tur];
    try {
      await ref.read(apiProvider).post(
        '/api/v1/account/feedback',
        data: {
          'type': tur,
          'text': _temiz,
          // Anahtar HİÇ gitmesin: sunucu `screen: null`u boş dize sanmasın.
          if (_ekran != null) 'screen': _ekran,
        },
      );
      Analytics.feedbackSent(tur);
      if (!mounted) return;
      setState(() => _gonderildi = true);
    } catch (e) {
      // 429 (günlük tavan) dahil: `detail` kullanıcının dilinde geliyor.
      if (!mounted) return;
      mesajci.showSnackBar(SnackBar(content: Text(friendlyError(e, l10n))));
    } finally {
      if (mounted) setState(() => _mesgul = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return CosmicScaffold(
      appBar: AppBar(title: Text(l10n.feedbackTitle)),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.only(
              top: RythoSpace.md, bottom: RythoSpace.xxl),
          children: _gonderildi ? _tesekkur(l10n) : _form(l10n),
        ),
      ),
    );
  }

  List<Widget> _form(AppLocalizations l10n) {
    final uzunluk = _temiz.length;
    final kisa = uzunluk > 0 && uzunluk < kFeedbackMinChars;
    return [
      RythoReveal(
        index: 0,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(
              RythoSpace.xl, 0, RythoSpace.xl, RythoSpace.lg),
          child: Text(l10n.feedbackLead, style: RythoType.bodyDim),
        ),
      ),
      RythoReveal(
        index: 1,
        child: GlassSegments(
          labels: [
            l10n.feedbackTypeBug,
            l10n.feedbackTypeSuggestion,
            l10n.feedbackTypeOther,
          ],
          index: _tur,
          onChanged: (i) => setState(() => _tur = i),
        ),
      ),
      RythoReveal(
        index: 2,
        child: GlassPanel(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(l10n.feedbackScreenLabel, style: RythoType.label),
              const SizedBox(height: RythoSpace.sm),
              Wrap(
                spacing: RythoSpace.sm,
                runSpacing: RythoSpace.sm,
                children: [
                  for (final kod in kFeedbackScreens)
                    _EkranCipi(
                      text: _ekranAdi(l10n, kod),
                      selected: _ekran == kod,
                      // Aynı çipe ikinci dokunuş seçimi kaldırır: alan
                      // isteğe bağlı, "hiçbiri" de geçerli bir cevap.
                      onTap: () => setState(
                          () => _ekran = _ekran == kod ? null : kod),
                    ),
                ],
              ),
              const SizedBox(height: RythoSpace.lg),
              TextField(
                controller: _metin,
                minLines: 4,
                maxLines: 8,
                maxLength: kFeedbackMaxChars,
                textCapitalization: TextCapitalization.sentences,
                style: RythoText.body(15),
                decoration: InputDecoration(
                  hintText: l10n.feedbackHint,
                  hintStyle:
                      RythoText.body(15, color: RythoColors.parchmentDim),
                  helperText: kisa ? l10n.feedbackTooShort : null,
                  helperStyle: RythoText.body(12, color: RythoColors.madder),
                  counterStyle:
                      RythoText.mono(10.5, color: RythoColors.parchmentDim),
                ),
              ),
              const SizedBox(height: RythoSpace.sm),
              Text(l10n.feedbackPrivacy, style: RythoType.caption),
            ],
          ),
        ),
      ),
      RythoReveal(
        index: 3,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(
              RythoSpace.lg, RythoSpace.md, RythoSpace.lg, 0),
          child: GoldButton(
            text: l10n.feedbackSend,
            busy: _mesgul,
            onPressed: _gonderilebilir ? _gonder : null,
          ),
        ),
      ),
    ];
  }

  List<Widget> _tesekkur(AppLocalizations l10n) {
    return [
      RythoReveal(
        index: 0,
        child: GlassPanel(
          glow: true,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(children: [
                Text('✦',
                    style:
                        RythoText.display(22, color: RythoColors.goldBright)),
                const SizedBox(width: RythoSpace.sm),
                Expanded(
                  child: Text(l10n.feedbackThanksTitle,
                      style: RythoText.display(17)),
                ),
              ]),
              const SizedBox(height: RythoSpace.md),
              Text(l10n.feedbackThanksBody, style: RythoType.bodyDim),
              const SizedBox(height: RythoSpace.xl),
              GoldButton(
                text: l10n.feedbackClose,
                filled: false,
                onPressed: () => Navigator.of(context).maybePop(),
              ),
            ],
          ),
        ),
      ),
    ];
  }

  String _ekranAdi(AppLocalizations l10n, String kod) => switch (kod) {
        'sky' => l10n.tabSky,
        'atlas' => l10n.tabAtlas,
        'chat' => l10n.feedbackScreenChat,
        'circle' => l10n.circleTitle,
        'oracle' => l10n.feedbackScreenOracle,
        'profile' => l10n.tabProfile,
        _ => l10n.feedbackScreenOther,
      };
}

/// Seçilebilir çip — `SuggestionChip` görünümü + seçili durum. Seçili olan
/// degrade DEĞİL, ince altın kontur alır: bu bir durum göstergesi, eylem
/// değil (bkz. GlassSegments açıklaması).
class _EkranCipi extends StatelessWidget {
  const _EkranCipi({
    required this.text,
    required this.selected,
    required this.onTap,
  });

  final String text;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      selected: selected,
      child: Pressable(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding:
              const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          decoration: BoxDecoration(
            color: selected
                ? RythoColors.goldBright.withValues(alpha: 0.14)
                : RythoColors.inkLight,
            borderRadius: BorderRadius.circular(999),
            border: Border.all(
                color: selected
                    ? RythoColors.goldBright.withValues(alpha: 0.7)
                    : RythoColors.lilac.withValues(alpha: 0.30)),
          ),
          child: Text(text,
              style: RythoText.body(12.5,
                  w: FontWeight.w600,
                  color: selected
                      ? RythoColors.parchment
                      : RythoColors.parchmentDim)),
        ),
      ),
    );
  }
}
