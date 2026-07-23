import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import '../../core/analytics.dart';
import '../../core/api.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';

/// Yüz Okuma — fotoğraf çek/seç → MediaPipe 478 nokta ölçümü →
/// Mian Xiang + Kıyafetname sentez raporu. Fotoğraf sunucuda TUTULMAZ.
class FaceTab extends ConsumerStatefulWidget {
  const FaceTab({super.key});

  @override
  ConsumerState<FaceTab> createState() => _FaceTabState();
}

class _FaceTabState extends ConsumerState<FaceTab> {
  bool _busy = false;
  Map<String, dynamic>? _result;
  Uint8List? _imageBytes;

  Future<void> _analyze(ImageSource source) async {
    final picker = ImagePicker();
    final file = await picker.pickImage(
        source: source, maxWidth: 1280, imageQuality: 88);
    if (file == null) return;

    final Uint8List bytes = await file.readAsBytes();
    setState(() {
      _busy = true;
      _result = null;
      _imageBytes = bytes;
    });
    try {
      final dio = ref.read(apiProvider);
      final form = FormData.fromMap({
        'file': MultipartFile.fromBytes(bytes, filename: 'face.jpg'),
      });
      final response =
          await dio.post('/api/v1/face-reading/analyze', data: form);
      setState(
          () => _result = Map<String, dynamic>.from(response.data['data']));
      Analytics.faceAnalyzed();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Analiz başarısız: $e')));
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
      Text('İlm-i Sima', style: RythoText.display(28)),
      const SizedBox(height: 8),
      Text(
        'Mian Xiang ve Marifetname geleneği: yüzün 478 noktalık haritası '
        'çıkarılır; San Ting dengesi, Beş Element formu ve 12 Saray okunur. '
        'Fotoğrafın analizden hemen sonra silinir.',
        style: RythoText.body(13.5, color: RythoColors.parchmentDim),
      ),
      const SizedBox(height: 20),
      Row(children: [
        Expanded(
          child: GoldButton(
            text: 'Fotoğraf çek',
            busy: _busy,
            onPressed: () => _analyze(ImageSource.camera),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: GoldButton(
            text: 'Galeriden seç',
            busy: _busy,
            onPressed: () => _analyze(ImageSource.gallery),
          ),
        ),
      ]),
      if (_busy) ...[
        const SizedBox(height: 28),
        if (_imageBytes != null)
          Center(child: _ScanningImage(bytes: _imageBytes!))
        else
          const Center(child: AstrolabeSpinner(size: 56)),
        const SizedBox(height: 12),
        Center(
          child: Text('Hatlar ölçülüyor...',
              style: RythoText.mono(12, color: RythoColors.parchmentDim)),
        ),
      ],
      if (_result != null) ...[
        const SectionDivider(),
        _FaceResult(result: _result!),
      ],
      const SizedBox(height: 32),
    ]);
  }
}

/// Analiz sürerken fotoğrafın üzerinde gezinen altın tarama çizgisi.
class _ScanningImage extends StatefulWidget {
  const _ScanningImage({required this.bytes});
  final Uint8List bytes;

  @override
  State<_ScanningImage> createState() => _ScanningImageState();
}

class _ScanningImageState extends State<_ScanningImage>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
      vsync: this, duration: const Duration(milliseconds: 1600))
    ..repeat(reverse: true);

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    const height = 260.0;
    return ClipRRect(
      borderRadius: BorderRadius.circular(18),
      child: SizedBox(
        height: height,
        width: 200,
        child: Stack(fit: StackFit.expand, children: [
          Image.memory(widget.bytes, fit: BoxFit.cover),
          Container(color: RythoColors.ink.withValues(alpha: 0.35)),
          AnimatedBuilder(
            animation: _controller,
            builder: (_, _) {
              final y = Curves.easeInOut.transform(_controller.value) *
                  (height - 4);
              return Stack(children: [
                Positioned(
                  top: y - 30,
                  left: 0,
                  right: 0,
                  height: 60,
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [
                          Colors.transparent,
                          RythoColors.magenta.withValues(alpha: 0.22),
                          Colors.transparent,
                        ],
                      ),
                    ),
                  ),
                ),
                Positioned(
                  top: y,
                  left: 8,
                  right: 8,
                  height: 2,
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      color: RythoColors.lilac,
                      borderRadius: BorderRadius.circular(2),
                      boxShadow: const [
                        BoxShadow(
                            color: RythoColors.magentaGlow, blurRadius: 12),
                      ],
                    ),
                  ),
                ),
              ]);
            },
          ),
        ]),
      ),
    );
  }
}

class _FaceResult extends StatelessWidget {
  const _FaceResult({required this.result});
  final Map<String, dynamic> result;

  @override
  Widget build(BuildContext context) {
    final ratios = Map<String, dynamic>.from(result['san_ting_ratios'] ?? {});
    final palaces = List<Map<String, dynamic>>.from(result['palaces'] ?? []);

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Plaque(
        label: 'Ölçüm Cetveli',
        margin: EdgeInsets.zero,
        child: Column(children: [
          _row('Wu Xing elementi', result['wu_xing_element'] ?? '—'),
          _row('Mizaç', result['mizac'] ?? '—'),
          _row('Simetri', result['symmetry'] ?? '—'),
          _row('San Ting', result['san_ting_balance'] ?? '—'),
          const SizedBox(height: 10),
          Row(children: [
            for (final zone in const [
              ('upper', 'GÖK'),
              ('middle', 'İNSAN'),
              ('lower', 'YER'),
            ])
              Expanded(
                child: Column(children: [
                  Text(zone.$2,
                      style:
                          RythoText.mono(10, color: RythoColors.parchmentDim)),
                  const SizedBox(height: 4),
                  Text(
                    '%${(((ratios[zone.$1] ?? 0) as num) * 100).toStringAsFixed(0)}',
                    style: RythoText.mono(16),
                  ),
                ]),
              ),
          ]),
        ]),
      ),
      const SizedBox(height: 16),
      Plaque(
        label: '12 Saray',
        margin: EdgeInsets.zero,
        padding: EdgeInsets.zero,
        child: Column(children: [
          for (final p in palaces)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              decoration: BoxDecoration(
                border: p == palaces.last
                    ? null
                    : const Border(bottom: BorderSide(color: RythoColors.line)),
              ),
              child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(p['bright'] == true ? '✦' : '·',
                    style: RythoText.mono(13,
                        color: p['bright'] == true
                            ? RythoColors.gold
                            : RythoColors.parchmentDim)),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(p['name_tr'] ?? '', style: RythoText.body(14)),
                        const SizedBox(height: 2),
                        Text(p['assessment'] ?? '',
                            style: RythoText.body(12,
                                color: RythoColors.parchmentDim)),
                      ]),
                ),
              ]),
            ),
        ]),
      ),
      const SizedBox(height: 20),
      MarginNote(
          title: 'Rytho\'nun sima notu',
          text: result['face_reading_summary'] ?? result['summary'] ?? ''),
    ]);
  }

  Widget _row(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        SizedBox(
            width: 110,
            child: Text(label,
                style: RythoText.body(12.5, color: RythoColors.parchmentDim))),
        Expanded(child: Text(value, style: RythoText.body(13.5))),
      ]),
    );
  }
}
