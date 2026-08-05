import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:dio/dio.dart';

import '../../core/analytics.dart';
import '../../core/api.dart';
import '../../core/sound.dart';
import '../../core/wallet.dart';
import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import '../../theme/rytho_tokens.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/nebula_widgets.dart';

/// Çekim hakkı durumu (İ6): "bugünkü hak 1/1" rozeti — kota yalnız 402'de,
/// yani hak BİTİNCE görünür oluyordu. Salt-okur uç, hak düşmez.
final ichingStatusProvider =
    FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final dio = ref.watch(apiProvider);
  final yanit = await dio.get('/api/v1/reports/iching/status');
  return Map<String, dynamic>.from(yanit.data['data'] as Map);
});

/// I Ching: soru sor → gerçek olasılık dağılımıyla çekim → heksagram +
/// hareketli çizgiler + Rytho yorumu.
class IChingTab extends ConsumerStatefulWidget {
  const IChingTab({super.key});

  @override
  ConsumerState<IChingTab> createState() => _IChingTabState();
}

class _IChingTabState extends ConsumerState<IChingTab> {
  // Keepalive karışımı KALKTI (R10): ekran artık TabBarView içinde değil,
  // kendi sayfasında — sayfa yığındayken state zaten yaşıyor.
  final _controller = TextEditingController();
  String _method = 'coins';
  bool _busy = false;
  Map<String, dynamic>? _result;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _cast() async {
    final l10n = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    final question = _controller.text.trim();
    if (question.isEmpty) {
      messenger.showSnackBar(
          SnackBar(content: Text(l10n.iChingQuestionRequired)));
      return;
    }
    // Soru kapısı (R10→R11): bariz niyetsiz girişler istek atılmadan
    // çevrilir. Esas hüküm sunucuda LLM'de (iching_question_verdict);
    // burası yalnız gereksiz gidiş-dönüşü keser. Sunucunun 422 mesajı
    // (geçersiz metin / Sohbet'e yönlendirme) friendlyError ile aynen
    // gösterilir.
    if (!_meaningfulQuestion(question)) {
      messenger.showSnackBar(
          SnackBar(content: Text(l10n.iChingQuestionInvalid)));
      return;
    }
    setState(() {
      _busy = true;
      _result = null;
    });
    SoundFx.cast();
    try {
      final dio = ref.read(apiProvider);
      final response = await dio.post('/api/v1/reports/iching',
          data: {'question': question, 'method': _method});
      setState(() => _result = Map<String, dynamic>.from(response.data['data']));
      Analytics.ichingCast(_method);
      // Abone çekimi cüzdandan 2 token düşer; sohbetteki bakiye çipi
      // bayat kalmasın (İ0). Kota rozeti de tazelensin (İ6).
      ref.invalidate(walletProvider);
      ref.invalidate(ichingStatusProvider);
    } on DioException catch (e) {
      // 402'de interceptor zaten paywall'ı açıyor; arkasına bir de
      // SnackBar basmak aynı mesajı iki kez göstermekti (İ0).
      if (mounted && e.response?.statusCode != 402) {
        messenger.showSnackBar(
            SnackBar(content: Text(friendlyError(e, l10n))));
      }
    } catch (e) {
      if (mounted) {
        messenger.showSnackBar(
            SnackBar(content: Text(friendlyError(e, l10n))));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 110),
        children: [
      Text(l10n.iChingSubtitle, style: RythoText.display(28)),
      const SizedBox(height: 8),
      Text(
        l10n.iChingIntro,
        style: RythoText.body(13.5, color: RythoColors.parchmentDim),
      ),
      const SizedBox(height: 20),
      TextField(
        controller: _controller,
        style: RythoText.body(15),
        // Sunucu şemasıyla hizalı sınır (İ0): soru prompt'a ham giriyor.
        maxLength: 280,
        decoration: InputDecoration(
          hintText: l10n.iChingQuestionHint,
          counterText: '',
        ),
      ),
      const SizedBox(height: 12),
      Row(children: [
        for (final m in [
          ('coins', l10n.iChingMethodCoins),
          ('yarrow', l10n.iChingMethodYarrow)
        ]) ...[
          Expanded(
            // Pressable (İ6): basılınca ölçeklenir + haptik — çıplak
            // GestureDetector bunların ikisini de vermiyordu. Süreler
            // RythoMotion token'larından.
            child: Pressable(
              onTap: () => setState(() => _method = m.$1),
              child: AnimatedContainer(
                duration: RythoMotion.base,
                curve: Curves.easeOutCubic,
                height: 42,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  gradient:
                      _method == m.$1 ? RythoColors.primaryGradient : null,
                  color: _method == m.$1 ? null : RythoColors.inkLight,
                  border: Border.all(
                      color: _method == m.$1
                          ? Colors.white.withValues(alpha: 0.2)
                          : RythoColors.glassStroke),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Text(m.$2,
                    style: RythoText.label(12,
                        color: _method == m.$1
                            ? Colors.white
                            : RythoColors.parchmentDim)),
              ),
            ),
          ),
          if (m.$1 == 'coins') const SizedBox(width: 8),
        ],
      ]),
      const SizedBox(height: 16),
      GoldButton(text: l10n.iChingCastAction, busy: _busy, onPressed: _cast),
      // Kota rozeti (İ6): abone token bedelini, ücretsiz kullanıcı günlük
      // hakkını görür — hak yalnız 402'de değil, ÖNCE görünür.
      Consumer(builder: (context, ref, _) {
        final durum = ref.watch(ichingStatusProvider).value;
        if (durum == null) return const SizedBox(height: 8);
        final metin = durum['subscriber'] == true
            ? l10n.iChingQuotaTokens(durum['token_cost'] as int? ?? 2)
            : l10n.iChingQuotaFree(durum['free_remaining'] as int? ?? 0,
                durum['free_limit'] as int? ?? 1);
        return Padding(
          padding: const EdgeInsets.only(top: 8),
          child: Center(
            child: Text(metin,
                style:
                    RythoText.mono(10.5, color: RythoColors.parchmentDim)),
          ),
        );
      }),
      if (_busy) ...[
        const SizedBox(height: 36),
        const Center(child: _CoinToss()),
        const SizedBox(height: 12),
        Center(
          child: Text(l10n.iChingCoinsInAir,
              style: RythoText.mono(12, color: RythoColors.parchmentDim)),
        ),
      ],
      if (_result != null) ...[
        const SectionDivider(),
        _HexagramView(result: _result!)
            .animate()
            .fadeIn(duration: 500.ms)
            .slideY(begin: 0.04, curve: Curves.easeOutCubic),
      ],
      const SizedBox(height: 32),
    ]);
  }
}

/// Soru kutusuna niyet yerine yazılan tipik doldurmalar — sunucudaki
/// `_DOLGU_KELIMELER` listesinin aynası (iching_service.py). Karşılaştırma
/// küçük harfle; noktasız-I varyantları iki ayrı girdi olarak duruyor.
const _dolguKelimeler = {
  'merhaba', 'selam', 'selamlar', 'hello', 'hi', 'hey', 'naber',
  'nasılsın', 'nasilsin', 'iyi', 'misin', 'test', 'deneme', 'asdf',
  'qwerty', 'abc', 'ok', 'tamam', 'evet', 'hayır', 'hayir',
};

/// Soru gerçek bir niyet taşıyor mu — dolgu kelimeler ayıklandıktan sonra
/// en az iki kelime kalmalı. Günde tek çekim hakkı selamla harcanmasın.
bool _meaningfulQuestion(String question) {
  final kelimeler = question
      .toLowerCase()
      .replaceAll('\u0307', '') // İ küçülünce kalan birleşik nokta
      .split(RegExp(r"[^\p{L}\p{N}']+", unicode: true));
  final anlamli =
      kelimeler.where((k) => k.isNotEmpty && !_dolguKelimeler.contains(k));
  return anlamli.length >= 2;
}

/// Üç paranın 3D dönüş animasyonu — çekim sürerken oynar.
class _CoinToss extends StatefulWidget {
  const _CoinToss();

  @override
  State<_CoinToss> createState() => _CoinTossState();
}

class _CoinTossState extends State<_CoinToss>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
      vsync: this, duration: const Duration(milliseconds: 1100))
    ..repeat();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (_, _) => Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          for (var i = 0; i < 3; i++)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 10),
              child: Transform.translate(
                offset: Offset(
                    0,
                    -14 *
                        math.sin((_controller.value + i * 0.23) * math.pi)
                            .abs()),
                child: Transform(
                  alignment: Alignment.center,
                  transform: Matrix4.identity()
                    ..setEntry(3, 2, 0.002) // perspektif
                    ..rotateX((_controller.value + i * 0.23) * 2 * math.pi),
                  child: Container(
                  width: 34,
                  height: 34,
                  alignment: Alignment.center,
                  decoration: const BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [RythoColors.gold, RythoColors.magenta],
                    ),
                    boxShadow: [
                      BoxShadow(color: RythoColors.magentaGlow, blurRadius: 14),
                    ],
                  ),
                    child: Text('中',
                        style: TextStyle(
                            fontSize: 15,
                            color: RythoColors.ink.withValues(alpha: 0.85))),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

/// Çekim sonucu sahnesi (İ6): BaZi sekmesiyle aynı Plaque dilinde —
/// çift glif, hüküm/imge metinleri, hareketli çizgi pasajları, Liu Yao
/// dökümü ve gün bağlamı. Eski hâli yalnız ad + LLM yorumu gösteriyordu;
/// hüküm ve imge sunucudan geldiği hâlde ekrana hiç çıkmıyordu.
class _HexagramView extends StatelessWidget {
  const _HexagramView({required this.result});
  final Map<String, dynamic> result;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final cast = Map<String, dynamic>.from(result['cast']);
    final primary = Map<String, dynamic>.from(cast['primary']);
    final transformed = cast['transformed'] != null
        ? Map<String, dynamic>.from(cast['transformed'])
        : null;
    final nuclear = cast['nuclear'] != null
        ? Map<String, dynamic>.from(cast['nuclear'])
        : null;
    final liuYao = cast['liu_yao'] != null
        ? Map<String, dynamic>.from(cast['liu_yao'])
        : null;
    final context_ = cast['context'] != null
        ? Map<String, dynamic>.from(cast['context'])
        : null;
    final lines = List<int>.from(cast['lines'] ?? []);
    final values = List<int>.from(cast['line_values'] ?? []);
    final moving = List<int>.from(cast['moving_lines'] ?? []);
    final lineTexts =
        List<String>.from(primary['line_texts'] as List? ?? const []);
    final lower = Map<String, dynamic>.from(primary['lower_trigram'] ?? {});
    final upper = Map<String, dynamic>.from(primary['upper_trigram'] ?? {});

    var sira = 0;
    Duration gecikme() => Duration(milliseconds: 140 * sira++);
    Widget blok(Widget w) => w
        .animate(delay: gecikme())
        .fadeIn(duration: 380.ms)
        .slideY(begin: 0.06, curve: Curves.easeOutCubic);

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      blok(Plaque(
        margin: const EdgeInsets.symmetric(vertical: 8),
        label: l10n.iChingHexagramLabel(primary['number']),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start,
            children: [
          Row(crossAxisAlignment: CrossAxisAlignment.center, children: [
            // Çizgiler alttan yukarı sırayla belirir — çekimin kendisi
            // gibi (İ6 reveal sahnesi).
            _HexagramGlyph(
                lines: lines, moving: moving, values: values, reveal: true),
            if (transformed != null) ...[
              const Padding(
                padding: EdgeInsets.symmetric(horizontal: 12),
                child: Icon(Icons.arrow_forward_rounded,
                    size: 18, color: RythoColors.parchmentDim),
              ),
              _HexagramGlyph(
                  lines: List<int>.from(cast['lines'] ?? [])
                      .asMap()
                      .entries
                      .map((e) =>
                          moving.contains(e.key + 1) ? 1 - e.value : e.value)
                      .toList(),
                  moving: const []),
            ],
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('${primary['name_local'] ?? primary['name_tr']}',
                        style: RythoText.display(24)),
                    Text('${primary['name']} ${primary['name_cn']}',
                        style: RythoText.body(12.5,
                            color: RythoColors.parchmentDim)),
                    if (transformed != null) ...[
                      const SizedBox(height: 6),
                      Text(
                        l10n.iChingTransformedTo(
                            transformed['name_local'] ??
                                transformed['name_tr'],
                            transformed['number']),
                        style: RythoText.mono(11.5,
                            color: RythoColors.copper),
                      ),
                    ],
                  ]),
            ),
          ]),
          const SizedBox(height: 10),
          Text(
              l10n.iChingTrigramsLabel(
                  '${lower['name'] ?? ''} (${lower['element'] ?? ''})',
                  '${upper['name'] ?? ''} (${upper['element'] ?? ''})'),
              style: RythoText.body(11.5, color: RythoColors.parchmentDim)),
          if (nuclear != null)
            Text(
                l10n.iChingNuclearLabel(
                    nuclear['name_local'] ?? nuclear['name_tr'] ?? '',
                    nuclear['number'] as int),
                style:
                    RythoText.body(11.5, color: RythoColors.parchmentDim)),
          if (moving.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(l10n.iChingLegend,
                style: RythoText.mono(10, color: RythoColors.parchmentDim)),
          ],
        ]),
      )),
      blok(Plaque(
        margin: const EdgeInsets.symmetric(vertical: 8),
        label: l10n.iChingJudgmentTitle,
        child: Text(primary['judgment'] ?? '',
            style: RythoText.body(14, color: RythoColors.parchment)),
      )),
      blok(Plaque(
        margin: const EdgeInsets.symmetric(vertical: 8),
        label: l10n.iChingImageTitle,
        child: Text(primary['image'] ?? '',
            style: RythoText.body(13.5, color: RythoColors.parchmentDim)),
      )),
      // Hareketli çizgi METİNLERİ — okumanın ağırlık merkezi (İ1 verisi).
      if (moving.isNotEmpty && lineTexts.length == 6)
        blok(Plaque(
          label: l10n.iChingMovingTitle,
          child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                for (final n in moving)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color:
                                  RythoColors.copper.withValues(alpha: 0.14),
                              borderRadius: BorderRadius.circular(999),
                            ),
                            child: Text(l10n.iChingLineLabel(n),
                                style: RythoText.mono(10,
                                    color: RythoColors.copper)),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(lineTexts[n - 1],
                                style: RythoText.body(13,
                                    color: RythoColors.parchment)),
                          ),
                        ]),
                  ),
              ]),
        )),
      if (liuYao != null)
        blok(Plaque(
          label: l10n.iChingLiuYaoTitle,
          child: _LiuYaoTable(l10n: l10n, liuYao: liuYao, moving: moving),
        )),
      if ((context_?['day_pillar']?['label'] as String?)?.isNotEmpty ??
          false)
        blok(Padding(
          padding: const EdgeInsets.only(bottom: 4),
          child: Text(
              l10n.iChingDayLabel(context_!['day_pillar']['label'] as String),
              style: RythoText.mono(10.5, color: RythoColors.parchmentDim)),
        )),
      blok(const SectionDivider()),
      blok(MarginNote(
          title: l10n.iChingOracleNote, text: result['report'] ?? '')),
    ]);
  }
}

/// Liu Yao dökümü: alttan üste 6 satır — dal+gövde, akraba, işaretler.
class _LiuYaoTable extends StatelessWidget {
  const _LiuYaoTable(
      {required this.l10n, required this.liuYao, required this.moving});
  final AppLocalizations l10n;
  final Map<String, dynamic> liuYao;
  final List<int> moving;

  @override
  Widget build(BuildContext context) {
    final satirlar =
        List<Map<String, dynamic>>.from(liuYao['lines'] as List? ?? const []);
    final shi = liuYao['shi'] as int?;
    final ying = liuYao['ying'] as int?;
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(
          l10n.iChingPalaceLabel(
              '${liuYao['palace'] ?? ''}', shi ?? 0, ying ?? 0),
          style: RythoText.body(11.5, color: RythoColors.parchmentDim)),
      const SizedBox(height: 8),
      // Alttan üste — glifle aynı yön.
      for (final c in satirlar.reversed)
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 2),
          child: Row(children: [
            SizedBox(
              width: 22,
              child: Text('${c['position']}',
                  style: RythoText.mono(10,
                      color: c['position'] == shi
                          ? RythoColors.goldBright
                          : RythoColors.parchmentDim)),
            ),
            SizedBox(
              width: 76,
              child: Text('${c['stem'] ?? ''}${c['branch'] ?? ''}',
                  style: RythoText.mono(11,
                      color: (c['void'] == true)
                          ? RythoColors.parchmentDim
                          : RythoColors.parchment)),
            ),
            Expanded(
              child: Text('${c['relative_name'] ?? c['relative'] ?? ''}',
                  style: RythoText.body(11.5,
                      color: RythoColors.parchmentDim)),
            ),
            if (c['position'] == shi)
              _tag('shi', RythoColors.goldBright)
            else if (c['position'] == ying)
              _tag('ying', RythoColors.lilac),
            if (c['void'] == true)
              _tag(l10n.iChingVoidTag, RythoColors.parchmentDim),
            if (c['clash'] == true) _tag(l10n.iChingClashTag, RythoColors.copper),
          ]),
        ),
    ]);
  }

  Widget _tag(String metin, Color renk) => Container(
        margin: const EdgeInsets.only(left: 4),
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
        decoration: BoxDecoration(
          border: Border.all(color: renk.withValues(alpha: 0.5)),
          borderRadius: BorderRadius.circular(999),
        ),
        child: Text(metin, style: RythoText.mono(8.5, color: renk)),
      );
}

/// Heksagram çizimi: 6 çizgi alttan üste; hareketli çizgiler bakır renkte
/// ve ucunda klasik işaret taşır — ○ eski yang (9), × eski yin (6).
class _HexagramGlyph extends StatelessWidget {
  const _HexagramGlyph({
    required this.lines,
    required this.moving,
    this.values = const [],
    this.reveal = false,
  });
  final List<int> lines;
  final List<int> moving;

  /// 6/7/8/9 değerleri — işaret seçimi için; boşsa işaret çizilmez.
  final List<int> values;

  /// Çizgiler alttan yukarı sırayla belirsin mi (sonuç sahnesi).
  final bool reveal;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        for (var i = lines.length - 1; i >= 0; i--) _satir(i),
      ],
    );
  }

  Widget _satir(int i) {
    final cizgi = Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        SizedBox(
          width: 64,
          height: 6,
          child: lines[i] == 1
              ? Container(color: _color(i + 1))
              : Row(children: [
                  Expanded(child: Container(color: _color(i + 1))),
                  const SizedBox(width: 14),
                  Expanded(child: Container(color: _color(i + 1))),
                ]),
        ),
        SizedBox(
          width: 14,
          child: Text(_isaret(i),
              textAlign: TextAlign.center,
              style: RythoText.mono(9, color: RythoColors.copper)),
        ),
      ]),
    );
    if (!reveal) return cizgi;
    // Alttan üste: i=0 (en alt) önce belirir.
    return cizgi
        .animate(delay: (140 * i).ms)
        .fadeIn(duration: 260.ms)
        .slideX(begin: -0.08, curve: Curves.easeOutCubic);
  }

  String _isaret(int i) {
    if (i >= values.length || !moving.contains(i + 1)) return '';
    return values[i] == 9 ? '○' : '×';
  }

  Color _color(int lineNo) =>
      moving.contains(lineNo) ? RythoColors.copper : RythoColors.gold;
}
