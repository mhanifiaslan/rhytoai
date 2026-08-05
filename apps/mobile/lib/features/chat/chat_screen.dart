import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:firebase_auth/firebase_auth.dart';

import '../../core/api.dart';
import '../../core/conversations.dart';
import '../../core/sound.dart';
import '../../core/wallet.dart';
import '../../theme/rytho_theme.dart';
import '../../theme/rytho_tokens.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/nebula_widgets.dart';
import '../paywall/token_store_screen.dart';
import '../../l10n/app_localizations.dart';

/// Rytho AI sohbeti — v4 (Revize R4): KONU bazlı.
///
/// [conversationId] verilirse konuşma arşivden tohumlanır ve kaldığı
/// yerden sürer; verilmezse ilk mesajla yeni konu açılır (kimliği sunucu
/// döndürür, buradan izlenir). Mesaj balonu davranışı aynı: kullanıcı
/// sağda beyaz, Rytho solda mor degrade.
class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key, this.conversationId});

  final String? conversationId;

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final List<({String sender, String text})> _messages = [];
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  bool _busy = false;

  /// Sürdürülen konunun kimliği; ilk yanıtta sunucudan gelir.
  String? _conversationId;

  /// Arşiv tohumu yükleniyor mu (yalnızca var olan konu açılırken).
  bool _seeding = false;

  @override
  void initState() {
    super.initState();
    _conversationId = widget.conversationId;
    if (_conversationId != null) _seed();
  }

  /// Arşivden TEK SEFERLİK tohum. Stream değil — sunucu her turu saniyeler
  /// sonra arka planda arşive yazıyor; canlı dinleseydik her mesaj ekranda
  /// iki kez belirirdi (yerel + arşiv kopyası).
  Future<void> _seed() async {
    final uid = FirebaseAuth.instance.currentUser?.uid;
    final id = _conversationId;
    if (uid == null || id == null) return;
    setState(() => _seeding = true);
    try {
      final gecmis = await loadConversation(uid, id);
      if (!mounted) return;
      setState(() {
        _messages.insertAll(
            0, gecmis.map((m) => (sender: m.sender, text: m.text)));
      });
      _scrollDown();
    } catch (e) {
      debugPrint('Konu tohumu yüklenemedi: $e');
    } finally {
      if (mounted) setState(() => _seeding = false);
    }
  }

  /// Yeni konu: yerel durum sıfırlanır; ilk mesaj sunucuda yeni konu açar.
  ///
  /// "+" ikonunun İŞLEVİ bu. Eski sürümde ikon çıplak bir Container'dı —
  /// handler'ı hiç yoktu, dokununca ripple bile vermiyordu. Kaldırmak
  /// yerine tam da eksik olan işlev verildi (kullanıcının sorusuna cevap).
  void _newConversation() {
    HapticFeedback.selectionClick();
    setState(() {
      _messages.clear();
      _conversationId = null;
    });
  }

  /// Öneri çipleri dile göre üretildiği için const olamaz.
  List<String> _suggestions(AppLocalizations l10n) => [
        l10n.suggestCareer,
        l10n.suggestLove,
        l10n.suggestMonth,
        l10n.suggestFinance,
        l10n.suggestMarriage,
      ];

  Future<void> _send([String? preset]) async {
    final text = (preset ?? _controller.text).trim();
    if (text.isEmpty || _busy) return;
    _controller.clear();
    HapticFeedback.lightImpact();
    SoundFx.send();
    setState(() {
      _messages.add((sender: 'USER', text: text));
      _busy = true;
    });
    _scrollDown();

    try {
      final dio = ref.read(apiProvider);
      // Bağlam penceresi: sunucu zaten son 20 turla sınırlıyor; uzun
      // arşivli konuda tamamını taşımak boşuna bant genişliği.
      final history = _messages
          .map((m) => {'sender': m.sender, 'text': m.text})
          .toList()
        ..removeLast();
      final son20 = history.length > 20
          ? history.sublist(history.length - 20)
          : history;
      final response = await dio.post('/api/v1/chat', data: {
        'history': son20,
        'message': text,
        'conversation_id': _conversationId,
      });
      final veri = response.data as Map;
      setState(() {
        _messages.add((sender: 'AI', text: veri['reply'] ?? ''));
        // Yeni konunun kimliği ilk yanıtla gelir; sonraki mesajlar aynı
        // konuya yazılır ve liste ekranında görünür.
        _conversationId =
            (veri['conversation_id'] as String?) ?? _conversationId;
      });
      SoundFx.receive();
    } catch (e) {
      if (!mounted) return;
      setState(() => _messages.add((
            sender: 'AI',
            text: friendlyError(e, AppLocalizations.of(context))
          )));
    } finally {
      if (mounted) setState(() => _busy = false);
      _scrollDown();
    }
  }

  @override
  void dispose() {
    // Sızıntı düzeltmesi: her açılış/kapanışta iki controller askıda
    // kalıyordu.
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollDown() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOutCubic,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return CosmicScaffold(
      appBar: AppBar(
        title: Row(mainAxisSize: MainAxisSize.min, children: [
          Container(
            width: 30,
            height: 30,
            alignment: Alignment.center,
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              gradient: RythoColors.primaryGradient,
            ),
            child: const Text('✦',
                style: TextStyle(fontSize: 14, color: Colors.white)),
          ),
          const SizedBox(width: 10),
          Text(AppLocalizations.of(context).chatTitle),
        ]),
        actions: [
          // Bakiye çipi — "kalan hakkın" ilk kez bir yüzeye kavuşuyor.
          // Dokununca token mağazası: bakiyeyi GÖREN kullanıcı, bitmeden
          // doldurabilmeli. Abone olmayan ve paketi olmayan kullanıcıda
          // toplam 0 görünür; günlük ücretsiz hak zaten çipin konusu değil.
          Consumer(builder: (context, ref, _) {
            final cuzdan = ref.watch(walletProvider).value;
            if (cuzdan == null || cuzdan.total <= 0) {
              return const SizedBox.shrink();
            }
            return Padding(
              padding: const EdgeInsets.only(right: RythoSpace.md),
              child: Pressable(
                onTap: () => Navigator.of(context).push(MaterialPageRoute(
                  builder: (_) => const TokenStoreScreen(),
                  fullscreenDialog: true,
                )),
                child: Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: RythoSpace.md, vertical: 6),
                  decoration: BoxDecoration(
                    color: RythoColors.inkLighter,
                    borderRadius: BorderRadius.circular(RythoRadius.pill),
                    border: Border.all(color: RythoColors.glassStroke),
                  ),
                  child: Row(mainAxisSize: MainAxisSize.min, children: [
                    const Text('🪙', style: TextStyle(fontSize: 13)),
                    const SizedBox(width: RythoSpace.xs),
                    // Her mesajda bakiye düşüyor; sayı yumuşak geçişle
                    // değişsin ki harcama fark edilsin (madde 12 — ölçülü
                    // mikro animasyon, süre RythoMotion'dan).
                    AnimatedSwitcher(
                      duration: RythoMotion.base,
                      transitionBuilder: (child, anim) => FadeTransition(
                        opacity: anim,
                        child: SlideTransition(
                          position: Tween(
                                  begin: const Offset(0, 0.5),
                                  end: Offset.zero)
                              .animate(anim),
                          child: child,
                        ),
                      ),
                      child: Text(
                        AppLocalizations.of(context)
                            .tokenBalanceChip(cuzdan.total),
                        key: ValueKey(cuzdan.total),
                        style: RythoType.dataSmall,
                      ),
                    ),
                  ]),
                ),
              ),
            );
          }),
        ],
      ),
      body: Column(children: [
        Expanded(
          child: _seeding
              ? const Center(child: AstrolabeSpinner())
              : _messages.isEmpty
              ? _EmptyState(onSuggestion: (s) => _send(s))
              : ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.all(16),
                  itemCount: _messages.length + (_busy ? 1 : 0),
                  itemBuilder: (_, i) {
                    // Dots → balon morph'u (R12-C2): yanıt geldiğinde
                    // "yazıyor" noktalarının durduğu indekse AI balonu
                    // gelir (itemCount değişmez!) — hücre AnimatedSwitcher
                    // içinde olduğundan noktalar sönerken balon AYNI
                    // köşeden büyür. Sarmalayıcı HER hücrede sabit durur;
                    // koşullu sarmak komşu hücrelerin giriş animasyonunu
                    // yeniden oynatırdı.
                    final Key anahtar;
                    final Widget icerik;
                    if (i == _messages.length) {
                      anahtar = const ValueKey('dots');
                      icerik = const Align(
                        alignment: Alignment.centerLeft,
                        child: Padding(
                          padding: EdgeInsets.only(bottom: 12),
                          child: TypingDots(),
                        ),
                      )
                          .animate()
                          .fadeIn(duration: 220.ms)
                          .slideY(begin: 0.2, curve: Curves.easeOutBack);
                    } else {
                      final m = _messages[i];
                      final mine = m.sender != 'AI';
                      anahtar = ValueKey('m-$i');
                      icerik = Align(
                        alignment: mine
                            ? Alignment.centerRight
                            : Alignment.centerLeft,
                        child: _Bubble(text: m.text, mine: mine)
                            .animate()
                            .fadeIn(duration: 240.ms)
                            .slideY(begin: 0.25, curve: Curves.easeOutBack)
                            .scale(
                                begin: const Offset(0.92, 0.92),
                                curve: Curves.easeOutBack,
                                duration: 300.ms),
                      );
                    }
                    return AnimatedSwitcher(
                      duration: RythoMotion.base,
                      transitionBuilder: (child, anim) => FadeTransition(
                        opacity: anim,
                        child: ScaleTransition(
                          scale: Tween(begin: 0.9, end: 1.0).animate(
                              CurvedAnimation(
                                  parent: anim, curve: RythoMotion.settle)),
                          alignment: Alignment.bottomLeft,
                          child: child,
                        ),
                      ),
                      child: KeyedSubtree(key: anahtar, child: icerik),
                    );
                  },
                ),
        ),
        // Öneri çipleri
        SizedBox(
          height: 42,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            itemCount: _suggestions(l10n).length,
            separatorBuilder: (_, _) => const SizedBox(width: 8),
            itemBuilder: (_, i) => Center(
              child: SuggestionChip(
                text: _suggestions(l10n)[i],
                onTap: () => _send(_suggestions(l10n)[i]),
              ),
            ),
          ),
        ),
        const SizedBox(height: 8),
        // Giriş alanı: + / metin / degrade gönder
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 10),
          child: SafeArea(
            child: Row(children: [
              // "+" = YENİ KONU. Bir dönem handler'sız çıplak Container'dı
              // — dokununca hiçbir şey olmuyordu (kullanıcı fark etti).
              Pressable(
                onTap: _newConversation,
                child: Tooltip(
                  message: l10n.newConversation,
                  child: Container(
                    width: 42,
                    height: 42,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: RythoColors.inkLight,
                      border: Border.all(color: RythoColors.glassStroke),
                    ),
                    child: const Icon(Icons.add_comment_outlined,
                        size: 19, color: RythoColors.lilac),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: TextField(
                  controller: _controller,
                  style: RythoText.body(15),
                  minLines: 1,
                  maxLines: 4,
                  decoration: InputDecoration(
                    hintText: l10n.chatHint,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(24),
                      borderSide:
                          const BorderSide(color: RythoColors.glassStroke),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(24),
                      borderSide:
                          const BorderSide(color: RythoColors.glassStroke),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(24),
                      borderSide:
                          const BorderSide(color: RythoColors.purple),
                    ),
                  ),
                  onSubmitted: (_) => _send(),
                ),
              ),
              const SizedBox(width: 10),
              Pressable(
                onTap: _send,
                child: Container(
                  width: 46,
                  height: 46,
                  alignment: Alignment.center,
                  decoration: const BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: RythoColors.primaryGradient,
                    boxShadow: [
                      BoxShadow(
                          color: RythoColors.goldGlow, blurRadius: 16),
                    ],
                  ),
                  child: const Icon(Icons.send_rounded,
                      size: 20, color: Colors.white),
                ),
              ),
            ]),
          ),
        ),
      ]),
    );
  }
}

/// Sohbet balonu: kullanıcı beyaz (koyu metin), Rytho mor degrade (beyaz).
class _Bubble extends StatelessWidget {
  const _Bubble({required this.text, required this.mine});
  final String text;
  final bool mine;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 11),
      constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.78),
      decoration: BoxDecoration(
        color: mine ? Colors.white : null,
        gradient: mine ? null : RythoColors.primaryGradient,
        borderRadius: BorderRadius.only(
          topLeft: const Radius.circular(20),
          topRight: const Radius.circular(20),
          bottomLeft: Radius.circular(mine ? 20 : 6),
          bottomRight: Radius.circular(mine ? 6 : 20),
        ),
        boxShadow: [
          BoxShadow(
            color: mine
                ? Colors.black.withValues(alpha: 0.25)
                : RythoColors.goldGlow,
            blurRadius: 12,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Text(
        text,
        style: RythoText.body(14.5,
            color: mine ? const Color(0xFF1D1230) : Colors.white,
            height: 1.5),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.onSuggestion});
  final ValueChanged<String> onSuggestion;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 76,
            height: 76,
            alignment: Alignment.center,
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              gradient: RythoColors.primaryGradient,
              boxShadow: [
                BoxShadow(color: RythoColors.magentaGlow, blurRadius: 34),
              ],
            ),
            child: const Text('✦',
                style: TextStyle(fontSize: 32, color: Colors.white)),
          )
              .animate(onPlay: (c) => c.repeat(reverse: true))
              .scale(
                  begin: const Offset(1, 1),
                  end: const Offset(1.06, 1.06),
                  duration: 1400.ms,
                  curve: Curves.easeInOut),
          const SizedBox(height: 18),
          Text('Rytho AI', style: RythoText.display(24)),
          const SizedBox(height: 8),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 48),
            child: Text(
              l10n.chatEmptyBody,
              textAlign: TextAlign.center,
              style: RythoText.body(14, color: RythoColors.parchmentDim),
            ),
          ),
        ],
      )
          .animate()
          .fadeIn(duration: 400.ms)
          .slideY(begin: 0.06, curve: Curves.easeOutCubic),
    );
  }
}
