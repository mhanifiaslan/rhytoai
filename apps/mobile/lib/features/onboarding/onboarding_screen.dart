import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
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

    var stagger = 0;
    Duration next() => Duration(milliseconds: 70 * stagger++);

    return CosmicScaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            const SizedBox(height: 16),
            Text('✨ Kayıt',
                style: RythoText.label(12, color: RythoColors.lilac))
                .animate(delay: next())
                .fadeIn(duration: 360.ms),
            const SizedBox(height: 8),
            Text('Doğum Anın', style: RythoText.display(32))
                .animate(delay: next())
                .fadeIn(duration: 360.ms)
                .slideY(begin: 0.1, curve: Curves.easeOutCubic),
            const SizedBox(height: 8),
            Text(
              'Haritanın çizilebilmesi için gökyüzünün o anki dizilişi gerekir. '
              'Saat ne kadar kesinse, yükselen o kadar doğrudur.',
              style: RythoText.body(14, color: RythoColors.parchmentDim),
            ).animate(delay: next()).fadeIn(duration: 360.ms),
            const SizedBox(height: 28),
            _FieldRow(label: 'Tarih', value: dateText, onTap: _pickDate)
                .animate(delay: next())
                .fadeIn(duration: 360.ms)
                .slideY(begin: 0.08, curve: Curves.easeOutCubic),
            const SizedBox(height: 12),
            _FieldRow(label: 'Saat', value: timeText, onTap: _pickTime)
                .animate(delay: next())
                .fadeIn(duration: 360.ms)
                .slideY(begin: 0.08, curve: Curves.easeOutCubic),
            const SizedBox(height: 12),
            TextField(
              controller: _cityController,
              style: RythoText.body(15),
              decoration: const InputDecoration(labelText: 'Doğum şehri'),
            ).animate(delay: next()).fadeIn(duration: 360.ms).slideY(
                begin: 0.08, curve: Curves.easeOutCubic),
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
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 240),
                        curve: Curves.easeOutCubic,
                        height: 46,
                        alignment: Alignment.center,
                        decoration: BoxDecoration(
                          gradient: _gender == g.$1
                              ? RythoColors.primaryGradient
                              : null,
                          color:
                              _gender == g.$1 ? null : RythoColors.inkLight,
                          border: Border.all(
                              color: _gender == g.$1
                                  ? Colors.white.withValues(alpha: 0.2)
                                  : RythoColors.glassStroke),
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: Text(g.$2,
                            style: RythoText.body(14,
                                w: FontWeight.w600,
                                color: _gender == g.$1
                                    ? Colors.white
                                    : RythoColors.parchmentDim)),
                      ),
                    ),
                  ),
                  if (g.$1 != 'other') const SizedBox(width: 8),
                ],
              ],
            ).animate(delay: next()).fadeIn(duration: 360.ms).slideY(
                begin: 0.08, curve: Curves.easeOutCubic),
            const SizedBox(height: 36),
            GoldButton(text: 'Haritamı çiz ✨', busy: _busy, onPressed: _save)
                .animate(delay: next())
                .fadeIn(duration: 360.ms)
                .slideY(begin: 0.08, curve: Curves.easeOutCubic),
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
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: RythoColors.inkLighter,
          border: Border.all(color: RythoColors.glassStroke),
          borderRadius: BorderRadius.circular(16),
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
