/// Doğum kaydını düzeltme ekranı.
///
/// ## Neden var
///
/// Doğum tarihi/saati/şehri yalnızca kurulumda bir kez yazılabiliyordu.
/// Yanlış giren kullanıcının tek çıkışı hesabı silmekti. Bu sadece bir
/// kolaylık eksiği değil, veri kalitesi kusuru: o veri günlük okumayı, natal
/// raporu, BaZi'yi ve sohbetin gördüğü haritayı besliyor. Yanlış doğum
/// verisiyle üretilen her yorum yanlış.
///
/// Ekran bilerek sade: tek iş yapar, değişikliğin neyi etkileyeceğini söyler,
/// bir şey değişmediyse kaydetmez.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../core/api.dart';
import '../../core/birth_record.dart';
import '../../core/providers.dart';
import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import '../../theme/rytho_tokens.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/cosmic_scaffold.dart';

class BirthRecordScreen extends ConsumerStatefulWidget {
  const BirthRecordScreen({super.key});

  @override
  ConsumerState<BirthRecordScreen> createState() => _BirthRecordScreenState();
}

class _BirthRecordScreenState extends ConsumerState<BirthRecordScreen> {
  BirthRecord? _baslangic;
  late DateTime _tarih;
  late TimeOfDay _saat;
  final _sehir = TextEditingController();
  late String _cinsiyet;
  bool _mesgul = false;

  /// Profil akışı ilk değeri getirdiğinde formu bir kez doldur. Sonraki
  /// yayınlarda doldurmayız — kullanıcının yazdığının üstüne yazmak olur.
  void _ilkDoldur(Map<String, dynamic>? profil) {
    if (_baslangic != null) return;
    final kayit = BirthRecord.fromProfile(profil);
    _baslangic = kayit;
    _tarih = kayit.date;
    final parcalar = kayit.time.split(':');
    _saat = TimeOfDay(
      hour: int.tryParse(parcalar.first) ?? 12,
      minute: int.tryParse(parcalar.last) ?? 0,
    );
    _sehir.text = kayit.city;
    _cinsiyet = kayit.gender;
  }

  BirthRecord get _guncel => BirthRecord(
        date: _tarih,
        time: '${_saat.hour.toString().padLeft(2, '0')}:'
            '${_saat.minute.toString().padLeft(2, '0')}',
        city: _sehir.text,
        gender: _cinsiyet,
      );

  bool get _degisti => _baslangic != null && !_baslangic!.sameAs(_guncel);

  @override
  void dispose() {
    _sehir.dispose();
    super.dispose();
  }

  Future<void> _tarihSec() async {
    final secilen = await showDatePicker(
      context: context,
      initialDate: _tarih,
      firstDate: DateTime(1930),
      lastDate: DateTime.now(),
    );
    if (secilen != null) setState(() => _tarih = secilen);
  }

  Future<void> _saatSec() async {
    final secilen = await showTimePicker(context: context, initialTime: _saat);
    if (secilen != null) setState(() => _saat = secilen);
  }

  Future<void> _kaydet() async {
    final l10n = AppLocalizations.of(context);
    final gezgin = Navigator.of(context);
    final mesajci = ScaffoldMessenger.of(context);
    if (_sehir.text.trim().isEmpty) {
      mesajci.showSnackBar(SnackBar(content: Text(l10n.birthCityEmpty)));
      return;
    }
    setState(() => _mesgul = true);
    try {
      final sonuc =
          await saveBirthRecord(_guncel, dio: ref.read(apiProvider));
      if (!mounted) return;
      mesajci.showSnackBar(SnackBar(
        content: Text(sonuc == BirthSaveResult.ok
            ? l10n.birthRecordSaved
            // Rozetler silindi; sebebini söylemezsek açıklanamayan bir
            // kayıp olur.
            : l10n.birthRecordSavedNoChart),
      ));
      gezgin.pop();
    } catch (e) {
      if (!mounted) return;
      setState(() => _mesgul = false);
      mesajci.showSnackBar(SnackBar(content: Text(friendlyError(e))));
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final profil = ref.watch(profileProvider).value;
    _ilkDoldur(profil);

    final dil = Localizations.localeOf(context).toLanguageTag();
    return CosmicScaffold(
      appBar: AppBar(title: Text(l10n.birthRecord)),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(RythoSpace.xl, RythoSpace.md,
              RythoSpace.xl, RythoSpace.xxl),
          children: [
            Text(l10n.birthRecordEditBody, style: RythoType.bodyDim),
            const SizedBox(height: RythoSpace.xl),
            _AlanSatiri(
              label: l10n.birthDate,
              value: DateFormat('d MMMM yyyy', dil).format(_tarih),
              onTap: _tarihSec,
            ),
            const SizedBox(height: RythoSpace.md),
            _AlanSatiri(
              label: l10n.birthTime,
              value: '${_saat.hour.toString().padLeft(2, '0')}:'
                  '${_saat.minute.toString().padLeft(2, '0')}',
              onTap: _saatSec,
            ),
            const SizedBox(height: RythoSpace.md),
            TextField(
              controller: _sehir,
              style: RythoType.body,
              onChanged: (_) => setState(() {}),
              decoration: InputDecoration(labelText: l10n.onboardingCity),
            ),
            const SizedBox(height: RythoSpace.lg),
            Row(
              children: [
                for (final g in [
                  ('female', l10n.genderFemale),
                  ('male', l10n.genderMale),
                  ('other', l10n.genderOther),
                ]) ...[
                  Expanded(
                    child: GestureDetector(
                      onTap: () => setState(() => _cinsiyet = g.$1),
                      child: AnimatedContainer(
                        duration: RythoMotion.base,
                        curve: Curves.easeOutCubic,
                        height: 46,
                        alignment: Alignment.center,
                        decoration: BoxDecoration(
                          gradient: _cinsiyet == g.$1
                              ? RythoColors.primaryGradient
                              : null,
                          color:
                              _cinsiyet == g.$1 ? null : RythoColors.inkLight,
                          border: Border.all(
                              color: _cinsiyet == g.$1
                                  ? Colors.white.withValues(alpha: 0.2)
                                  : RythoColors.glassStroke),
                          borderRadius:
                              BorderRadius.circular(RythoRadius.md),
                        ),
                        child: Text(g.$2,
                            style: RythoText.body(14,
                                w: FontWeight.w600,
                                color: _cinsiyet == g.$1
                                    ? Colors.white
                                    : RythoColors.parchmentDim)),
                      ),
                    ),
                  ),
                  if (g.$1 != 'other') const SizedBox(width: RythoSpace.sm),
                ],
              ],
            ),
            const SizedBox(height: RythoSpace.xxl),
            GoldButton(
              text: l10n.save,
              busy: _mesgul,
              // Değişiklik yoksa kaydetmek anlamsız bir ağ çağrısı ve
              // gereksiz bir "kaydedildi" mesajı olurdu.
              onPressed: _degisti ? _kaydet : null,
            ),
          ],
        ),
      ),
    );
  }
}

class _AlanSatiri extends StatelessWidget {
  const _AlanSatiri(
      {required this.label, required this.value, required this.onTap});

  final String label;
  final String value;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(RythoRadius.md),
      child: Container(
        padding: const EdgeInsets.symmetric(
            horizontal: RythoSpace.lg, vertical: 14),
        decoration: BoxDecoration(
          color: RythoColors.inkLighter,
          border: Border.all(color: RythoColors.glassStroke),
          borderRadius: BorderRadius.circular(RythoRadius.md),
        ),
        child: Row(
          children: [
            Text(label, style: RythoType.label),
            const Spacer(),
            Text(value, style: RythoText.mono(14)),
            const SizedBox(width: RythoSpace.sm),
            const Icon(Icons.edit_outlined,
                size: 15, color: RythoColors.lilac),
          ],
        ),
      ),
    );
  }
}
