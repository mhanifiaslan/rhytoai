import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api.dart';
import '../../core/sound.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/nebula_widgets.dart';

/// Rytho AI sohbeti — v3: kullanıcı sağda beyaz balon, Rytho solda mor
/// degrade balon; öneri çipleri, "yazıyor" üç noktası, yaylanan giriş
/// animasyonları ve gönder/al sesleri.
class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final List<({String sender, String text})> _messages = [];
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  bool _busy = false;

  static const _suggestions = [
    'Kariyer 💼',
    'Aşk hayatı ❤️',
    'Bu ay beni ne bekliyor?',
    'Finansal şans 💰',
    'Evlilik zamanı 💍',
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
      final history = _messages
          .map((m) => {'sender': m.sender, 'text': m.text})
          .toList()
        ..removeLast();
      final response = await dio.post('/api/v1/chat',
          data: {'history': history, 'message': text});
      setState(() =>
          _messages.add((sender: 'AI', text: response.data['reply'] ?? '')));
      SoundFx.receive();
    } catch (e) {
      setState(() => _messages.add((
            sender: 'AI',
            text: 'Kozmik bağlantı koptu. Lütfen tekrar dene. ($e)'
          )));
    } finally {
      setState(() => _busy = false);
      _scrollDown();
    }
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
          const Text('Rytho AI'),
        ]),
      ),
      body: Column(children: [
        Expanded(
          child: _messages.isEmpty
              ? _EmptyState(onSuggestion: (s) => _send(s))
              : ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.all(16),
                  itemCount: _messages.length + (_busy ? 1 : 0),
                  itemBuilder: (_, i) {
                    if (i == _messages.length) {
                      return const Align(
                        alignment: Alignment.centerLeft,
                        child: Padding(
                          padding: EdgeInsets.only(bottom: 12),
                          child: TypingDots(),
                        ),
                      )
                          .animate()
                          .fadeIn(duration: 220.ms)
                          .slideY(begin: 0.2, curve: Curves.easeOutBack);
                    }
                    final m = _messages[i];
                    final mine = m.sender != 'AI';
                    return Align(
                      alignment:
                          mine ? Alignment.centerRight : Alignment.centerLeft,
                      child: _Bubble(text: m.text, mine: mine)
                          .animate()
                          .fadeIn(duration: 240.ms)
                          .slideY(begin: 0.25, curve: Curves.easeOutBack)
                          .scale(
                              begin: const Offset(0.92, 0.92),
                              curve: Curves.easeOutBack,
                              duration: 300.ms),
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
            itemCount: _suggestions.length,
            separatorBuilder: (_, _) => const SizedBox(width: 8),
            itemBuilder: (_, i) => Center(
              child: SuggestionChip(
                text: _suggestions[i],
                onTap: () => _send(_suggestions[i]),
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
              Container(
                width: 42,
                height: 42,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: RythoColors.inkLight,
                  border: Border.all(color: RythoColors.glassStroke),
                ),
                child: const Icon(Icons.add,
                    size: 20, color: RythoColors.parchmentDim),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: TextField(
                  controller: _controller,
                  style: RythoText.body(15),
                  minLines: 1,
                  maxLines: 4,
                  decoration: InputDecoration(
                    hintText: 'Geleceğinle ilgili her şeyi sor...',
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
              'Haritan, yüzün, kaderin... Aklından geçen her soruyu '
              'kadim kaynaklarla harmanlayarak yanıtlarım.',
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
