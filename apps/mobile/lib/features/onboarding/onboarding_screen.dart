import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../core/api.dart';
import '../../core/birth_record.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../l10n/app_localizations.dart';

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
      // Kimlik alanları yalnızca ilk kurulumda yazılır; doğum verisi ve Büyük
      // Üçlü ortak yoldan gider (bkz. core/birth_record.dart) — sonradan
      // düzeltme ekranıyla aynı kod.
      await FirebaseFirestore.instance.collection('users').doc(user.uid).set({
        'uid': user.uid,
        'displayName': user.displayName ?? 'Gezgin',
        'photoUrl': user.photoURL,
        'email': user.email,
        'createdAt': FieldValue.serverTimestamp(),
      }, SetOptions(merge: true));

      await saveBirthRecord(
        BirthRecord(
          date: _birthDate,
          time: '${_birthTime.hour.toString().padLeft(2, '0')}:'
              '${_birthTime.minute.toString().padLeft(2, '0')}',
          city: _cityController.text,
          gender: _gender,
        ),
        dio: ref.read(apiProvider),
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(AppLocalizations.of(context).onboardingFailed)));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final dateText = DateFormat('d MMMM yyyy',
            Localizations.localeOf(context).toLanguageTag())
        .format(_birthDate);
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
            Text(l10n.recordLabel,
                style: RythoText.label(12, color: RythoColors.lilac))
                .animate(delay: next())
                .fadeIn(duration: 360.ms),
            const SizedBox(height: 8),
            Text(l10n.onboardingTitle, style: RythoText.display(32))
                .animate(delay: next())
                .fadeIn(duration: 360.ms)
                .slideY(begin: 0.1, curve: Curves.easeOutCubic),
            const SizedBox(height: 8),
            Text(
              l10n.onboardingBody,
              style: RythoText.body(14, color: RythoColors.parchmentDim),
            ).animate(delay: next()).fadeIn(duration: 360.ms),
            const SizedBox(height: 28),
            _FieldRow(label: l10n.birthDate, value: dateText, onTap: _pickDate)
                .animate(delay: next())
                .fadeIn(duration: 360.ms)
                .slideY(begin: 0.08, curve: Curves.easeOutCubic),
            const SizedBox(height: 12),
            _FieldRow(label: l10n.birthTime, value: timeText, onTap: _pickTime)
                .animate(delay: next())
                .fadeIn(duration: 360.ms)
                .slideY(begin: 0.08, curve: Curves.easeOutCubic),
            const SizedBox(height: 12),
            TextField(
              controller: _cityController,
              style: RythoText.body(15),
              decoration: InputDecoration(labelText: l10n.onboardingCity),
            ).animate(delay: next()).fadeIn(duration: 360.ms).slideY(
                begin: 0.08, curve: Curves.easeOutCubic),
            const SizedBox(height: 20),
            Row(
              children: [
                for (final g in [
                  ('female', l10n.genderFemale),
                  ('male', l10n.genderMale),
                  ('other', l10n.genderOther),
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
            GoldButton(text: l10n.onboardingSubmit, busy: _busy, onPressed: _save)
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
