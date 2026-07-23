import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../core/api.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/cosmic_scaffold.dart';

/// Doğum verisi kaydı: tarih, saat, şehir, cinsiyet.
/// Kaydederken backend'den Büyük Üçlü (Güneş/Ay/Yükselen) hesaplanıp
/// profile yazılır — sosyal katman bu rozetleri kullanır.
class OnboardingScreen extends ConsumerStatefulWidget {
  const OnboardingScreen({super.key});

  @override
  ConsumerState<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  DateTime _birthDate = DateTime(2000, 1, 1);
  TimeOfDay _birthTime = const TimeOfDay(hour: 12, minute: 0);
  final _cityController = TextEditingController(text: 'Istanbul');
  String _gender = 'female';
  bool _busy = false;

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _birthDate,
      firstDate: DateTime(1930),
      lastDate: DateTime.now(),
    );
    if (picked != null) setState(() => _birthDate = picked);
  }

  Future<void> _pickTime() async {
    final picked = await showTimePicker(context: context, initialTime: _birthTime);
    if (picked != null) setState(() => _birthTime = picked);
  }

  Future<void> _save() async {
    final user = FirebaseAuth.instance.currentUser!;
    setState(() => _busy = true);
    try {
      final profile = {
        'uid': user.uid,
        'displayName': user.displayName ?? 'Gezgin',
        'photoUrl': user.photoURL,
        'email': user.email,
        'birthDate': DateFormat('yyyy-MM-dd').format(_birthDate),
        'birthTime':
            '${_birthTime.hour.toString().padLeft(2, '0')}:${_birthTime.minute.toString().padLeft(2, '0')}',
        'birthCity': _cityController.text.trim(),
        'gender': _gender,
        'onboardingCompleted': true,
        'createdAt': FieldValue.serverTimestamp(),
      };

      // Büyük Üçlü'yü hesapla (başarısız olsa da onboarding tamamlanır)
      try {
        final dio = ref.read(apiProvider);
        final response = await dio.post('/api/v1/astrology/natal-chart',
            data: birthPayload(profile));
        final data = response.data['data'];
        profile['sunSign'] = data['sun_sign'];
        profile['moonSign'] = data['moon_sign'];
        profile['ascendant'] = data['ascendant'];
      } catch (_) {}

      await FirebaseFirestore.instance
          .collection('users')
          .doc(user.uid)
          .set(profile, SetOptions(merge: true));
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Kayıt başarısız: $e')));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final dateText = DateFormat('d MMMM yyyy', 'tr_TR').format(_birthDate);
    final timeText =
        '${_birthTime.hour.toString().padLeft(2, '0')}:${_birthTime.minute.toString().padLeft(2, '0')}';

    return CosmicScaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            const SizedBox(height: 16),
            Text('LEVHA 0 — KAYIT',
                style: RythoText.mono(11, color: RythoColors.parchmentDim)),
            const SizedBox(height: 8),
            Text('Doğum Anın', style: RythoText.display(34)),
            const SizedBox(height: 8),
            Text(
              'Haritanın çizilebilmesi için gökyüzünün o anki dizilişi gerekir. '
              'Saat ne kadar kesinse, yükselen o kadar doğrudur.',
              style: RythoText.body(14, color: RythoColors.parchmentDim),
            ),
            const SizedBox(height: 28),
            _FieldRow(label: 'TARİH', value: dateText, onTap: _pickDate),
            const SizedBox(height: 12),
            _FieldRow(label: 'SAAT', value: timeText, onTap: _pickTime),
            const SizedBox(height: 12),
            TextField(
              controller: _cityController,
              style: RythoText.body(15),
              decoration: const InputDecoration(labelText: 'DOĞUM ŞEHRİ'),
            ),
            const SizedBox(height: 20),
            Row(
              children: [
                for (final g in const [
                  ('female', 'Kadın'),
                  ('male', 'Erkek'),
                  ('other', 'Diğer'),
                ]) ...[
                  Expanded(
                    child: GestureDetector(
                      onTap: () => setState(() => _gender = g.$1),
                      child: Container(
                        height: 44,
                        alignment: Alignment.center,
                        decoration: BoxDecoration(
                          border: Border.all(
                              color: _gender == g.$1
                                  ? RythoColors.gold
                                  : RythoColors.line),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(g.$2,
                            style: RythoText.body(14,
                                color: _gender == g.$1
                                    ? RythoColors.goldBright
                                    : RythoColors.parchmentDim)),
                      ),
                    ),
                  ),
                  if (g.$1 != 'other') const SizedBox(width: 8),
                ],
              ],
            ),
            const SizedBox(height: 36),
            GoldButton(text: 'Haritamı çiz', busy: _busy, onPressed: _save),
          ],
        ),
      ),
    );
  }
}

class _FieldRow extends StatelessWidget {
  const _FieldRow({required this.label, required this.value, required this.onTap});
  final String label;
  final String value;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
        decoration: BoxDecoration(
          color: RythoColors.inkLighter,
          border: Border.all(color: RythoColors.line),
          borderRadius: BorderRadius.circular(4),
        ),
        child: Row(
          children: [
            Text(label, style: RythoText.label(12, color: RythoColors.parchmentDim)),
            const Spacer(),
            Text(value, style: RythoText.mono(14, color: RythoColors.parchment)),
          ],
        ),
      ),
    );
  }
}
