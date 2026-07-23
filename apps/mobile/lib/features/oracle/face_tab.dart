import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

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

  Future<void> _analyze(ImageSource source) async {
    final picker = ImagePicker();
    final file = await picker.pickImage(
        source: source, maxWidth: 1280, imageQuality: 88);
    if (file == null) return;

    setState(() {
      _busy = true;
      _result = null;
    });
    try {
      final Uint8List bytes = await file.readAsBytes();
      final dio = ref.read(apiProvider);
      final form = FormData.fromMap({
        'file': MultipartFile.fromBytes(bytes, filename: 'face.jpg'),
      });
      final response =
          await dio.post('/api/v1/face-reading/analyze', data: form);
      setState(
          () => _result = Map<String, dynamic>.from(response.data['data']));
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
        const SizedBox(height: 40),
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
