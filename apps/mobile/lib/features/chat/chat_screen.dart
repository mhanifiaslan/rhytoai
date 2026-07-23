import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/cosmic_scaffold.dart';

/// Rytho ile sohbet — AI mesajları "marjinal not", kullanıcı mesajları
/// mürekkep bloğu olarak akar.
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

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _busy) return;
    _controller.clear();
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
      appBar: AppBar(title: const Text('Rytho')),
      body: Column(children: [
        Expanded(
          child: _messages.isEmpty
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text('✧', style: RythoText.display(40, color: RythoColors.gold)),
                      const SizedBox(height: 12),
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
                  ),
                )
              : ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.all(16),
                  itemCount: _messages.length + (_busy ? 1 : 0),
                  itemBuilder: (_, i) {
                    if (i == _messages.length) {
                      return const Padding(
                        padding: EdgeInsets.all(16),
                        child: Align(
                          alignment: Alignment.centerLeft,
                          child: AstrolabeSpinner(size: 28),
                        ),
                      );
                    }
                    final m = _messages[i];
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 16),
                      child: m.sender == 'AI'
                          ? MarginNote(text: m.text)
                          : Align(
                              alignment: Alignment.centerRight,
                              child: Container(
                                constraints: BoxConstraints(
                                    maxWidth:
                                        MediaQuery.of(context).size.width * 0.75),
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  color: RythoColors.inkLighter,
                                  borderRadius: BorderRadius.circular(4),
                                  border: Border.all(color: RythoColors.line),
                                ),
                                child: Text(m.text, style: RythoText.body(15)),
                              ),
                            ),
                    );
                  },
                ),
        ),
        Container(
          decoration: const BoxDecoration(
            border: Border(top: BorderSide(color: RythoColors.line)),
          ),
          padding: const EdgeInsets.fromLTRB(16, 10, 16, 10),
          child: SafeArea(
            child: Row(children: [
              Expanded(
                child: TextField(
                  controller: _controller,
                  style: RythoText.body(15),
                  minLines: 1,
                  maxLines: 4,
                  decoration: const InputDecoration(hintText: 'Sor...'),
                  onSubmitted: (_) => _send(),
                ),
              ),
              const SizedBox(width: 10),
              InkWell(
                onTap: _send,
                child: Container(
                  width: 44,
                  height: 44,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    border: Border.all(color: RythoColors.gold),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: const Text('✦',
                      style: TextStyle(color: RythoColors.goldBright, fontSize: 18)),
                ),
              ),
            ]),
          ),
        ),
      ]),
    );
  }
}
