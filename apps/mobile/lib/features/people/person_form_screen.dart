/// Kişi ekleme / düzenleme formu (P-turu).
///
/// ## Neden doğum kaydı ekranından ayrı
///
/// Alanlar neredeyse aynı ama iki şey farklı ve ikisi de önemli:
///
/// 1. **Ad burada bir form alanı** — ve o alan telefondan çıkmıyor. Ekran
///    bunu SÖYLEMEK zorunda: kullanıcı üçüncü bir kişinin bilgisini
///    giriyor, nereye gittiğini bilme hakkı var.
/// 2. **İlişki türü** var ve dekoratif değil: eksen adlarını ve AI'nın
///    çerçevesini belirliyor (çocuğuyla "çekim" konuşulmaz).
///
/// Saat "bilmiyorum" birinci sınıf bir seçenek: eklenen kişilerin çoğunda
/// saat gerçekten bilinmiyor. Boş bırakıldığında sunucu Yükselen ve ev
/// üretmez ve bunu beyan eder (bkz. core/birth_record.dart baş yorumu).
library;

import 'package:dio/dio.dart' show DioException;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../core/api.dart';
import '../../core/people.dart';
import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import '../../theme/rytho_tokens.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/city_search_field.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/nebula_widgets.dart' show Pressable;

/// Türün ekrandaki adı. Sunucu bu adı bilmiyor — orada yalnız anahtar var.
String relationLabel(AppLocalizations l10n, String relation) =>
    switch (relation) {
      'partner' => l10n.relationPartner,
      'child' => l10n.relationChild,
      'parent' => l10n.relationParent,
      'sibling' => l10n.relationSibling,
      'friend' => l10n.relationFriend,
      'work' => l10n.relationWork,
      _ => l10n.relationOther,
    };

/// Tür simgesi — listede kişiyi bir bakışta ayırt etmek için.
IconData relationIcon(String relation) => switch (relation) {
      'partner' => Icons.favorite_rounded,
      'child' => Icons.child_care_rounded,
      'parent' => Icons.elderly_rounded,
      'sibling' => Icons.group_rounded,
      'friend' => Icons.emoji_people_rounded,
      'work' => Icons.work_outline_rounded,
      _ => Icons.person_outline_rounded,
    };

/// Türün emoji karşılığı (OB1) — METİN bağlamları için (mention listesi
/// gibi). `relationIcon` bir IconData'dır ve string'e basılırsa
/// "IconData(U+0E25B)" görünür — cihazda tam bu görüldü. Tek-glif
/// emojiler bilerek seçildi (ZWJ dizileri bazı klavye/işletim sistemi
/// bileşimlerinde ikiye ayrılıyor).
String relationEmoji(String relation) => switch (relation) {
      'partner' => '💞',
      'child' => '🧒',
      'parent' => '🧓',
      'sibling' => '👫',
      'friend' => '🙋',
      'work' => '💼',
      _ => '✨',
    };

class PersonFormScreen extends ConsumerStatefulWidget {
  const PersonFormScreen({super.key, this.existing});

  /// Doluysa düzenleme kipi.
  final Person? existing;

  @override
  ConsumerState<PersonFormScreen> createState() => _PersonFormScreenState();
}

class _PersonFormScreenState extends ConsumerState<PersonFormScreen> {
  late final TextEditingController _ad =
      TextEditingController(text: widget.existing?.label ?? '');
  late String _tur = widget.existing?.relation ?? 'partner';
  late DateTime _tarih = _ilkTarih();
  late TimeOfDay _saat = _ilkSaat();
  late bool _saatBiliniyor = widget.existing?.birthTime != null;
  late String _sehir = widget.existing?.birthCity ?? '';
  late String? _ulke = widget.existing?.birthNation;
  late String _cinsiyet = widget.existing?.gender ?? 'female';
  bool _mesgul = false;

  DateTime _ilkTarih() {
    final ham = widget.existing?.birthDate;
    if (ham == null || ham.isEmpty) return DateTime(1990, 1, 1);
    final p = ham.split('-');
    if (p.length != 3) return DateTime(1990, 1, 1);
    return DateTime(int.tryParse(p[0]) ?? 1990, int.tryParse(p[1]) ?? 1,
        int.tryParse(p[2]) ?? 1);
  }

  TimeOfDay _ilkSaat() {
    final ham = widget.existing?.birthTime;
    if (ham == null) return const TimeOfDay(hour: 12, minute: 0);
    final p = ham.split(':');
    return TimeOfDay(
        hour: int.tryParse(p.first) ?? 12,
        minute: int.tryParse(p.length > 1 ? p[1] : '0') ?? 0);
  }

  @override
  void dispose() {
    _ad.dispose();
    super.dispose();
  }

  Future<void> _tarihSec() async {
    final secilen = await showDatePicker(
      context: context,
      initialDate: _tarih,
      firstDate: DateTime(1900),
      lastDate: DateTime.now(),
    );
    if (secilen != null) setState(() => _tarih = secilen);
  }

  Future<void> _saatSec() async {
    final secilen = await showTimePicker(context: context, initialTime: _saat);
    if (secilen != null) {
      setState(() {
        _saat = secilen;
        _saatBiliniyor = true; // saat seçmek "biliyorum" demek
      });
    }
  }

  Future<void> _sehirSec() async {
    final secim = await showCitySearch(context, initialQuery: _sehir);
    if (secim == null) return;
    setState(() {
      _sehir = secim.name;
      // Serbest metin kaçışında ülke boş döner; bayat ülke kodu bırakmak
      // aynı adlı şehirlerde yanlış çözüme yol açar.
      _ulke = secim.nation.isEmpty ? null : secim.nation;
    });
  }

  Person get _guncel => Person(
        id: widget.existing?.id ?? '',
        relation: _tur,
        label: _ad.text.trim().isEmpty ? null : _ad.text.trim(),
        birthDate: '${_tarih.year.toString().padLeft(4, '0')}-'
            '${_tarih.month.toString().padLeft(2, '0')}-'
            '${_tarih.day.toString().padLeft(2, '0')}',
        birthTime: _saatBiliniyor
            ? '${_saat.hour.toString().padLeft(2, '0')}:'
                '${_saat.minute.toString().padLeft(2, '0')}'
            : null,
        birthCity: _sehir.trim(),
        birthNation: _ulke,
        gender: _cinsiyet,
      );

  Future<void> _kaydet() async {
    final l10n = AppLocalizations.of(context);
    final gezgin = Navigator.of(context);
    final mesajci = ScaffoldMessenger.of(context);
    if (_sehir.trim().isEmpty) {
      mesajci.showSnackBar(SnackBar(content: Text(l10n.birthCityEmpty)));
      return;
    }
    setState(() => _mesgul = true);
    try {
      final dio = ref.read(apiProvider);
      if (widget.existing == null) {
        await createPerson(dio, _guncel, label: _ad.text);
      } else {
        await updatePerson(dio, _guncel, label: _ad.text);
      }
      if (!mounted) return;
      ref.invalidate(personSlotsProvider);
      mesajci.showSnackBar(SnackBar(content: Text(l10n.peopleSaved)));
      gezgin.pop(true);
    } catch (e) {
      if (!mounted) return;
      setState(() => _mesgul = false);
      // KT4: 402'de interceptor ZATEN paywall açıyor — üstüne snackbar
      // basmak çift tepkiydi (iching_tab bu çakışmayı baştan engelliyordu,
      // burası engellemiyordu). Diğer hatalar friendlyError ile görünür.
      if (e is! DioException || e.response?.statusCode != 402) {
        mesajci.showSnackBar(
            SnackBar(content: Text(friendlyError(e, l10n))));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final dil = Localizations.localeOf(context).toLanguageTag();

    return CosmicScaffold(
      appBar: AppBar(
        title: Text(widget.existing == null
            ? l10n.peopleAddTitle
            : l10n.peopleEditTitle),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(RythoSpace.xl, RythoSpace.md,
              RythoSpace.xl, RythoSpace.xxl),
          children: [
            // --- Ad: CİHAZDA kalır, bunu söylemek zorundayız ---
            TextField(
              controller: _ad,
              textCapitalization: TextCapitalization.words,
              style: RythoText.body(15),
              decoration: InputDecoration(
                labelText: l10n.peopleLabelField,
                hintText: l10n.peopleLabelHint,
              ),
            ),
            const SizedBox(height: RythoSpace.sm),
            Text(l10n.peopleLabelNote,
                style: RythoText.body(11.5, color: RythoColors.copper)),
            const SizedBox(height: RythoSpace.xl),

            // --- İlişki türü: eksen adlarını ve AI çerçevesini belirler ---
            Text(l10n.peopleRelation, style: RythoType.label),
            const SizedBox(height: RythoSpace.sm),
            Wrap(
              spacing: RythoSpace.sm,
              runSpacing: RythoSpace.sm,
              children: [
                for (final tur in kRelations)
                  _TurCipi(
                    secili: _tur == tur,
                    icon: relationIcon(tur),
                    label: relationLabel(l10n, tur),
                    onTap: () => setState(() => _tur = tur),
                  ),
              ],
            ),
            const SizedBox(height: RythoSpace.xl),

            _AlanSatiri(
              label: l10n.birthDate,
              value: DateFormat('d MMMM yyyy', dil).format(_tarih),
              onTap: _tarihSec,
            ),
            const SizedBox(height: RythoSpace.md),
            _AlanSatiri(
              label: l10n.birthTime,
              value: !_saatBiliniyor
                  ? '—'
                  : '${_saat.hour.toString().padLeft(2, '0')}:'
                      '${_saat.minute.toString().padLeft(2, '0')}',
              onTap: _saatSec,
            ),
            CheckboxListTile(
              value: !_saatBiliniyor,
              onChanged: (v) => setState(() => _saatBiliniyor = !(v ?? false)),
              controlAffinity: ListTileControlAffinity.leading,
              contentPadding: EdgeInsets.zero,
              dense: true,
              title: Text(l10n.birthTimeUnknown,
                  style: RythoText.body(13, color: RythoColors.parchmentDim)),
            ),
            const SizedBox(height: RythoSpace.md),
            _AlanSatiri(
              label: l10n.onboardingCity,
              value: _sehir.isEmpty ? '—' : _sehir,
              onTap: _sehirSec,
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
                          color: _cinsiyet == g.$1 ? null : RythoColors.inkLight,
                          border: Border.all(
                              color: _cinsiyet == g.$1
                                  ? Colors.white.withValues(alpha: 0.2)
                                  : RythoColors.glassStroke),
                          borderRadius: BorderRadius.circular(RythoRadius.md),
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
            const SizedBox(height: RythoSpace.xl),

            // --- Rıza beyanı: bu kişi kullanıcı değil, onayı alınamıyor ---
            Container(
              padding: const EdgeInsets.all(RythoSpace.lg),
              decoration: BoxDecoration(
                color: RythoColors.inkLighter,
                border: Border.all(
                    color: RythoColors.copper.withValues(alpha: 0.35)),
                borderRadius: BorderRadius.circular(RythoRadius.md),
              ),
              child: Text(l10n.peopleConsent,
                  style:
                      RythoText.body(12, color: RythoColors.parchmentDim)),
            ),
            const SizedBox(height: RythoSpace.xl),

            GoldButton(
              text: l10n.save,
              busy: _mesgul,
              onPressed: _kaydet,
            ),
          ],
        ),
      ),
    );
  }
}

class _TurCipi extends StatelessWidget {
  const _TurCipi({
    required this.secili,
    required this.icon,
    required this.label,
    required this.onTap,
  });

  final bool secili;
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Pressable(
      onTap: onTap,
      child: AnimatedContainer(
        duration: RythoMotion.base,
        curve: Curves.easeOutCubic,
        padding: const EdgeInsets.symmetric(
            horizontal: RythoSpace.lg, vertical: 10),
        decoration: BoxDecoration(
          gradient: secili ? RythoColors.primaryGradient : null,
          color: secili ? null : RythoColors.inkLight,
          border: Border.all(
              color: secili
                  ? Colors.white.withValues(alpha: 0.2)
                  : RythoColors.glassStroke),
          borderRadius: BorderRadius.circular(RythoRadius.pill),
        ),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          Icon(icon,
              size: 15,
              color: secili ? Colors.white : RythoColors.lilac),
          const SizedBox(width: 6),
          Text(label,
              style: RythoText.body(13,
                  w: FontWeight.w600,
                  color: secili ? Colors.white : RythoColors.parchmentDim)),
        ]),
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
            const Icon(Icons.edit_outlined, size: 15, color: RythoColors.lilac),
          ],
        ),
      ),
    );
  }
}
