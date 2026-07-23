import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';

/// I Ching: soru sor → gerçek olasılık dağılımıyla çekim → heksagram +
/// hareketli çizgiler + Rytho yorumu.
class IChingTab extends ConsumerStatefulWidget {
  const IChingTab({super.key});

  @override
  ConsumerState<IChingTab> createState() => _IChingTabState();
}

class _IChingTabState extends ConsumerState<IChingTab> {
  final _controller = TextEditingController();
  String _method = 'coins';
  bool _busy = false;
  Map<String, dynamic>? _result;

  Future<void> _cast() async {
    final question = _controller.text.trim();
    if (question.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Önce kalbindeki soruyu yaz.')));
      return;
    }
    setState(() {
      _busy = true;
      _result = null;
    });
    try {
      final dio = ref.read(apiProvider);
      final response = await dio.post('/api/v1/reports/iching',
          data: {'question': question, 'method': _method});
      setState(() => _result = Map<String, dynamic>.from(response.data['data']));
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Çekim başarısız: $e')));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 110),
        children: [
      Text('Değişimler Kitabı', style: RythoText.display(28)),
      const SizedBox(height: 8),
      Text(
        '3000 yıllık 64 heksagram matrisi. Sorunu yaz; paralar gerçek '
        'olasılık dağılımıyla atılır, hareketli çizgiler geleceğe köprü kurar.',
        style: RythoText.body(13.5, color: RythoColors.parchmentDim),
      ),
      const SizedBox(height: 20),
      TextField(
        controller: _controller,
        style: RythoText.body(15),
        decoration: const InputDecoration(hintText: 'Sorun nedir?'),
      ),
      const SizedBox(height: 12),
      Row(children: [
        for (final m in const [('coins', 'ÜÇ PARA'), ('yarrow', 'CİVANPERÇEMİ')]) ...[
          Expanded(
            child: GestureDetector(
              onTap: () => setState(() => _method = m.$1),
              child: Container(
                height: 40,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  border: Border.all(
                      color: _method == m.$1 ? RythoColors.gold : RythoColors.line),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(m.$2,
                    style: RythoText.label(11,
                        color: _method == m.$1
                            ? RythoColors.goldBright
                            : RythoColors.parchmentDim)),
              ),
            ),
          ),
          if (m.$1 == 'coins') const SizedBox(width: 8),
        ],
      ]),
      const SizedBox(height: 16),
      GoldButton(text: 'Çekimi yap', busy: _busy, onPressed: _cast),
      if (_result != null) ...[
        const SectionDivider(),
        _HexagramView(result: _result!),
      ],
      const SizedBox(height: 32),
    ]);
  }
}

class _HexagramView extends StatelessWidget {
  const _HexagramView({required this.result});
  final Map<String, dynamic> result;

  @override
  Widget build(BuildContext context) {
    final cast = Map<String, dynamic>.from(result['cast']);
    final primary = Map<String, dynamic>.from(cast['primary']);
    final transformed = cast['transformed'] != null
        ? Map<String, dynamic>.from(cast['transformed'])
        : null;
    final lines = List<int>.from(cast['lines'] ?? []);
    final moving = List<int>.from(cast['moving_lines'] ?? []);

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [
        _HexagramGlyph(lines: lines, moving: moving),
        const SizedBox(width: 20),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('HEKSAGRAM ${primary['number']}',
                style: RythoText.mono(11, color: RythoColors.parchmentDim)),
            const SizedBox(height: 4),
            Text('${primary['name_tr']}', style: RythoText.display(26)),
            Text('${primary['name']} ${primary['name_cn']}',
                style: RythoText.body(13, color: RythoColors.parchmentDim)),
            if (transformed != null) ...[
              const SizedBox(height: 8),
              Text(
                '→ dönüşüm: ${transformed['name_tr']} (#${transformed['number']})',
                style: RythoText.mono(12, color: RythoColors.copper),
              ),
            ],
          ]),
        ),
      ]),
      const SizedBox(height: 20),
      MarginNote(title: 'Rytho\'nun kehanet notu', text: result['report'] ?? ''),
    ]);
  }
}

/// Heksagram çizimi: 6 çizgi alttan üste; hareketli çizgiler bakır renkte.
class _HexagramGlyph extends StatelessWidget {
  const _HexagramGlyph({required this.lines, required this.moving});
  final List<int> lines;
  final List<int> moving;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        for (var i = lines.length - 1; i >= 0; i--)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 3),
            child: SizedBox(
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
          ),
      ],
    );
  }

  Color _color(int lineNo) =>
      moving.contains(lineNo) ? RythoColors.copper : RythoColors.gold;
}
