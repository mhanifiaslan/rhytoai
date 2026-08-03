/// Burç yorumlarının tam ekran hikâye okuyucusu.
///
/// ## Neden var
///
/// Gökyüzü'nün üst şeridindeki burç yuvarlakları Instagram/WhatsApp hikâye
/// halkalarına benziyordu ama öyle davranmıyordu: dokununca ekranın **200 px
/// aşağısındaki** bir bölümün metni değişiyordu. Arada alakasız bir tanıtım
/// bandı da duruyordu, yani neden-sonuç bağı büsbütün kopuktu. Kullanıcının
/// tarifi buydu:
///
/// > "üst satırdaki burç yuvarlakları tıklanınca içgörü kısmında metinleri
/// > çıkıyor halbuki bu tasarımın whatsapp ya da instagram benzeri bir durum
/// > gösterme şekli olması gerekiyor."
///
/// Görsel vaat neyse davranış o olmalı. Halka gibi görünen şey hikâye açar.
///
/// ## Otomatik ilerleme — süre metinden hesaplanır
///
/// İlk sürüm elle ilerliyordu; kullanıcı bunu eksik buldu ve haklıydı, çünkü
/// hikâye vaadinin yarısı zaten kendiliğinden akmasıdır.
///
/// Ama Instagram'ın 5 saniyesi buraya olduğu gibi taşınamaz: orada içerik bir
/// görsel, burada ~150 kelimelik bir metin. Sabit süre koysaydık okuma
/// ortasında sayfa kayardı. Bu yüzden süre **kelime sayısından** hesaplanıyor
/// (bkz. [okumaSuresi]) ve ekrana parmak değdiği an duruyor — kaydırmak,
/// basılı tutmak, seçmek: hepsi okuma sayılır.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../core/api.dart' show friendlyError;
import '../../core/providers.dart';
import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import '../../theme/rytho_tokens.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/nebula_widgets.dart';
import '../share/share_card.dart';

/// Dakikada okunan kelime — Türkçe için ölçülen aralığın alt ucu (200-250).
/// Alt uç bilinçli: hızlı okuyan zaten kaydırır, yavaş okuyanın metni
/// altından kaymamalı.
const int kKelimeDakika = 200;

/// Bir hikâye sayfasının ekranda kalma süresi.
///
/// Alt sınır kısa metnin bir anda geçip gitmesini, üst sınır da uzun metnin
/// hikâyeyi durmuş gibi göstermesini engelliyor.
Duration okumaSuresi(String metin) {
  final kelime = metin.trim().isEmpty
      ? 0
      : metin.trim().split(RegExp(r'\s+')).length;
  final saniye = kelime * 60 / kKelimeDakika;
  return Duration(milliseconds: (saniye.clamp(6, 30) * 1000).round());
}

class SignStoryScreen extends ConsumerStatefulWidget {
  const SignStoryScreen({
    super.key,
    required this.order,
    required this.initialIndex,
  });

  /// Burç sırası — şeritte görünenle **aynı** olmalı, yoksa kaydırınca
  /// beklenmedik burca geçilir.
  final List<int> order;

  /// [order] içindeki başlangıç konumu (burç numarası değil).
  final int initialIndex;

  @override
  ConsumerState<SignStoryScreen> createState() => _SignStoryScreenState();
}

class _SignStoryScreenState extends ConsumerState<SignStoryScreen>
    with SingleTickerProviderStateMixin {
  late final PageController _sayfa =
      PageController(initialPage: widget.initialIndex);
  late final AnimationController _sure =
      AnimationController(vsync: this, duration: const Duration(seconds: 10))
        ..addStatusListener(_bittiMi);

  late int _konum = widget.initialIndex;

  /// Bu konumun sayacı kuruldu mu. Metin async geldiği için sayaç ancak
  /// metin elimize geçtiğinde başlayabilir.
  int? _kurulanKonum;

  /// Parmak ekrandayken ilerleme durur.
  bool _elde = false;

  void _bittiMi(AnimationStatus durum) {
    if (durum != AnimationStatus.completed) return;
    if (_konum + 1 < widget.order.length) {
      _gec(_konum + 1);
    }
    // Son burçta ekranı KAPATMIYORUZ. Instagram son hikâyeden sonra çıkar
    // ama orada içerik 5 saniyelik bir görsel; burada okuma ortasında
    // kullanıcıyı ekrandan atmak olurdu.
  }

  @override
  void dispose() {
    _sure.dispose();
    _sayfa.dispose();
    super.dispose();
  }

  void _gec(int hedef) {
    if (hedef < 0 || hedef >= widget.order.length) return;
    _sayfa.animateToPage(hedef,
        duration: RythoMotion.base, curve: Curves.easeOutCubic);
  }

  /// Metin geldiğinde bu sayfanın sayacını kurar ve başlatır.
  void _sayaciKur(String metin) {
    if (_kurulanKonum == _konum) return;
    _kurulanKonum = _konum;
    _sure
      ..stop()
      ..duration = okumaSuresi(metin)
      ..value = 0;
    if (!_elde) _sure.forward();
  }

  void _duraklat(bool duruyor) {
    if (_elde == duruyor) return;
    _elde = duruyor;
    if (duruyor) {
      _sure.stop();
    } else if (_kurulanKonum == _konum) {
      _sure.forward();
    }
  }

  @override
  Widget build(BuildContext context) {
    final burc = widget.order[_konum];
    final renk = RythoColors.signColors[burc % 12];

    // Aktif sayfanın metni gelir gelmez sayaç kurulur. Sayacı sayfanın
    // içinden kurmak, PageView komşu sayfaları da inşa ettiği için yanlış
    // sayfanın süresini işletirdi.
    final aktif = ref.watch(signHoroscopeProvider(kSignKeys[burc]));
    if (aktif.hasValue) {
      final metin = (aktif.value?['reading'] as String?) ?? '';
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) _sayaciKur(metin);
      });
    }

    return Scaffold(
      backgroundColor: RythoColors.ink,
      body: Listener(
        // Parmak değdiği an durur, kalkınca devam eder: kaydırmak da,
        // basılı tutmak da okuma sayılır.
        onPointerDown: (_) => _duraklat(true),
        onPointerUp: (_) => _duraklat(false),
        onPointerCancel: (_) => _duraklat(false),
        child: Stack(
          children: [
            // Zemin seçili burcun rengini alır: hangi hikâyede olduğun
            // metni okumadan belli olur.
            AnimatedContainer(
              duration: RythoMotion.slow,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    renk.withValues(alpha: 0.30),
                    RythoColors.ink,
                    RythoColors.ink,
                  ],
                ),
              ),
            ),
            SafeArea(
              child: Column(
                children: [
                  AnimatedBuilder(
                    animation: _sure,
                    builder: (_, _) => _IlerlemeCubugu(
                      adet: widget.order.length,
                      konum: _konum,
                      oran: _sure.value,
                      renk: renk,
                      onTap: _gec,
                    ),
                  ),
                  _Baslik(
                    signIndex: burc,
                    onClose: () => Navigator.of(context).pop(),
                  ),
                  Expanded(
                    child: PageView.builder(
                      controller: _sayfa,
                      itemCount: widget.order.length,
                      onPageChanged: (i) {
                        // Sayaç sıfırlanır; yeni sayfanın metni gelince
                        // kendi süresiyle yeniden kurulur.
                        _sure.stop();
                        _sure.value = 0;
                        _kurulanKonum = null;
                        setState(() => _konum = i);
                      },
                      itemBuilder: (_, i) =>
                          _BurcSayfasi(signIndex: widget.order[i]),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Üstteki bölmeli çubuk. Geçilenler dolu, içinde bulunulan **dolmakta**,
/// gelecekler boş — Instagram'daki gibi.
class _IlerlemeCubugu extends StatelessWidget {
  const _IlerlemeCubugu({
    required this.adet,
    required this.konum,
    required this.oran,
    required this.renk,
    required this.onTap,
  });

  final int adet;
  final int konum;

  /// İçinde bulunulan bölmenin doluluğu, 0–1.
  final double oran;
  final Color renk;
  final ValueChanged<int> onTap;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(
          RythoSpace.md, RythoSpace.md, RythoSpace.md, RythoSpace.xs),
      child: Row(
        children: [
          for (var i = 0; i < adet; i++)
            Expanded(
              child: GestureDetector(
                onTap: () => onTap(i),
                behavior: HitTestBehavior.opaque,
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 2),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(RythoRadius.pill),
                    child: LinearProgressIndicator(
                      value: i < konum
                          ? 1
                          : i == konum
                              ? oran
                              : 0,
                      minHeight: 3,
                      backgroundColor:
                          RythoColors.parchment.withValues(alpha: 0.22),
                      valueColor: AlwaysStoppedAnimation(renk),
                    ),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

/// Üst başlık: küçük sembol + burç adı solda, kapatma sağda.
///
/// İlk sürümde sembol 56 punto ve ortalıydı; kullanıcı "üstte solda daha
/// minimal durabilir" dedi. Doğrusu da bu: sayfanın işi metni okutmak,
/// başlık kimlik bildirir, gösteri yapmaz.
class _Baslik extends StatelessWidget {
  const _Baslik({required this.signIndex, required this.onClose});

  final int signIndex;
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final renk = RythoColors.signColors[signIndex % 12];

    return Padding(
      padding: const EdgeInsets.fromLTRB(
          RythoSpace.xl, RythoSpace.xs, RythoSpace.sm, RythoSpace.xs),
      child: Row(
        children: [
          Container(
            width: 30,
            height: 30,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: renk.withValues(alpha: 0.20),
              border: Border.all(color: renk.withValues(alpha: 0.55)),
            ),
            child: Text(kSignGlyphs[signIndex],
                style: TextStyle(fontSize: 15, color: renk)),
          ),
          const SizedBox(width: RythoSpace.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(signDisplayName(l10n, signIndex),
                    style: RythoType.cardTitle),
                Text(
                  DateFormat('d MMMM',
                          Localizations.localeOf(context).toLanguageTag())
                      .format(DateTime.now()),
                  style: RythoType.caption,
                ),
              ],
            ),
          ),
          IconButton(
            tooltip: MaterialLocalizations.of(context).closeButtonTooltip,
            icon: const Icon(Icons.close_rounded,
                color: RythoColors.parchment),
            onPressed: onClose,
          ),
        ],
      ),
    );
  }
}

/// Tek burcun hikâye sayfası.
class _BurcSayfasi extends ConsumerWidget {
  const _BurcSayfasi({required this.signIndex});

  final int signIndex;

  Future<void> _paylas(BuildContext context, AppLocalizations l10n,
      Map<String, dynamic> data) async {
    final moon = data['moon_phase'] as Map<String, dynamic>?;
    // Karta yalnızca burç, tarih, alıntı ve ay evresi girer — ham doğum
    // verisi ASLA.
    await shareReadingCard(
      context,
      signName: signDisplayName(l10n, signIndex),
      signGlyph: kSignGlyphs[signIndex],
      reading: data['reading'] ?? '',
      dateLabel: DateFormat(
              'd MMMM yyyy', Localizations.localeOf(context).toLanguageTag())
          .format(DateTime.now()),
      moonEmoji: moon?['emoji'] as String?,
      moonName: moon?['name'] as String?,
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final yorum = ref.watch(signHoroscopeProvider(kSignKeys[signIndex]));

    return ListView(
      padding: const EdgeInsets.fromLTRB(
          RythoSpace.xl, RythoSpace.md, RythoSpace.xl, RythoSpace.xxl),
      children: [
        yorum.when(
          loading: () => const Padding(
            padding: EdgeInsets.only(top: RythoSpace.xxl),
            child: Center(child: AstrolabeSpinner()),
          ),
          error: (e, _) => Padding(
            padding: const EdgeInsets.only(top: RythoSpace.lg),
            child: Column(children: [
              Text(friendlyError(e, l10n),
                  style: RythoType.bodyDim, textAlign: TextAlign.center),
              const SizedBox(height: RythoSpace.lg),
              GoldButton(
                text: l10n.faceOpenSettings,
                filled: false,
                onPressed: () => ref
                    .invalidate(signHoroscopeProvider(kSignKeys[signIndex])),
              ),
            ]),
          ),
          data: (data) => Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Hikâye sayfasında KIRPMA YOK — akıştan buraya çıkarılmasının
              // sebebi zaten metnin tamamının okunabilmesi.
              Text(data['reading'] ?? '', style: RythoType.reading),
              const SizedBox(height: RythoSpace.xl),
              Center(
                child: GoldButton(
                  text: l10n.shareReading,
                  filled: false,
                  icon: const Icon(Icons.ios_share_rounded,
                      size: 16, color: RythoColors.parchment),
                  onPressed: () => _paylas(context, l10n, data),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
