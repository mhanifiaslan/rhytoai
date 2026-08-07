/// Ülke seçicili telefon alanı (O4).
///
/// Eskiden numara tek serbest TextField'dı ("+90 5xx..."): ülke kodu elle
/// yazılıyor, boşluklu/sıfırlı yazımlar Firebase'e ham gidiyordu. Artık
/// ülke ARAMALI tam ekran listeden seçilir (assets/data/countries.json —
/// GeoNames countryInfo, 246 ülke; bayrak ISO kodundan emoji, asset yok)
/// ve E.164 çıktı burada derlenir: boşluklar atılır, ulusal baştaki sıfır
/// kırpılır ("+90 0532..." hatası kaynağında biter).
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;

import '../l10n/app_localizations.dart';
import '../theme/rytho_theme.dart';
import '../theme/rytho_tokens.dart';
import 'city_search_field.dart' show flagEmoji;
import 'fade_through_route.dart';

class Country {
  const Country(this.iso2, this.dialCode, this.nameEn, this.nameTr);

  final String iso2;
  final String dialCode;
  final String nameEn;
  final String nameTr;

  String nameFor(BuildContext context) =>
      Localizations.localeOf(context).languageCode == 'en'
          ? nameEn
          : nameTr;
}

/// countries.json — küçük (≈10 KB), ilk kullanımda bir kez yüklenir.
class CountryDirectory {
  CountryDirectory._(this.countries);

  final List<Country> countries;

  static CountryDirectory? _ornek;

  static Future<CountryDirectory> load() async {
    if (_ornek != null) return _ornek!;
    final ham = await rootBundle.loadString('assets/data/countries.json');
    final veri = jsonDecode(ham) as Map<String, dynamic>;
    return _ornek = CountryDirectory._([
      for (final c in veri['countries'] as List)
        Country(c[0] as String, c[1] as String, c[2] as String,
            c[3] as String),
    ]);
  }
}

/// E.164 derleyici: seçili ülke + ulusal numara.
///
/// Kullanıcı alışkanlıkları affedilir: boşluk/tire, baştaki sıfır
/// ("0532..."), hatta ülke kodunun ELLE tekrar yazılması ("+90 532..."
/// ya da "90532...") — hepsi aynı doğru numaraya derlenir. Bu önemli
/// çünkü Firebase yanlış derlenmiş numarayı da kabul edip "SMS
/// gönderildi" diyebiliyor; SMS hiç var olmayan numaraya gider ve
/// kullanıcının gördüğü şey "kod gelmiyor" olur.
String composeE164(Country country, String national) {
  // Rakam dışı her şey atılır ('+' dahil).
  var n = national.replaceAll(RegExp(r'\D'), '');
  // Ülke kodu ulusal alana da yazıldıysa kırpılır ("90532..." → "532...")
  // — kalan uzunluk gerçek bir ulusal numarayı andırıyorsa.
  final kod = country.dialCode;
  if (n.startsWith(kod) && n.length - kod.length >= 8) {
    n = n.substring(kod.length);
  }
  // Ulusal yazımın baştaki sıfırı uluslararası biçimde yer almaz.
  if (n.startsWith('0')) n = n.substring(1);
  return '+$kod$n';
}

/// Ülke + ulusal numara girişi; her değişimde E.164'ü bildirir.
class PhoneNumberField extends StatefulWidget {
  const PhoneNumberField({
    super.key,
    required this.onChanged,
    this.initialIso2 = 'TR',
  });

  /// Derlenmiş E.164 ("+90532...") — ulusal alan boşsa boş string.
  final ValueChanged<String> onChanged;

  final String initialIso2;

  @override
  State<PhoneNumberField> createState() => _PhoneNumberFieldState();
}

class _PhoneNumberFieldState extends State<PhoneNumberField> {
  final _ulusal = TextEditingController();
  Country? _ulke;

  @override
  void initState() {
    super.initState();
    CountryDirectory.load().then((d) {
      if (!mounted) return;
      setState(() => _ulke = d.countries.firstWhere(
            (c) => c.iso2 == widget.initialIso2,
            orElse: () => d.countries.first,
          ));
    });
  }

  @override
  void dispose() {
    _ulusal.dispose();
    super.dispose();
  }

  void _bildir() {
    final ulke = _ulke;
    final n = _ulusal.text.trim();
    widget.onChanged(ulke == null || n.isEmpty ? '' : composeE164(ulke, n));
  }

  Future<void> _ulkeSec() async {
    final secim = await Navigator.of(context).push<Country>(
        FadeThroughRoute(builder: (_) => const _CountrySearchScreen()));
    if (secim != null && mounted) {
      setState(() => _ulke = secim);
      _bildir();
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final ulke = _ulke;
    return Row(crossAxisAlignment: CrossAxisAlignment.center, children: [
      InkWell(
        onTap: _ulkeSec,
        borderRadius: BorderRadius.circular(14),
        child: Container(
          padding:
              const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
          decoration: BoxDecoration(
            color: RythoColors.inkLighter,
            border: Border.all(color: RythoColors.glassStroke),
            borderRadius: BorderRadius.circular(14),
          ),
          child: Text(
            ulke == null
                ? '…'
                : '${flagEmoji(ulke.iso2)} +${ulke.dialCode}',
            style: RythoText.mono(14, color: RythoColors.parchment),
          ),
        ),
      ),
      const SizedBox(width: 10),
      Expanded(
        child: TextField(
          controller: _ulusal,
          style: RythoType.body,
          keyboardType: TextInputType.phone,
          autofillHints: const [AutofillHints.telephoneNumber],
          decoration: InputDecoration(
            labelText: l10n.phoneFieldLabel,
            hintText: '5xx xxx xx xx',
          ),
          onChanged: (_) => _bildir(),
        ),
      ),
    ]);
  }
}

/// Aramalı tam ekran ülke listesi — şehir aramasıyla aynı dil.
class _CountrySearchScreen extends StatefulWidget {
  const _CountrySearchScreen();

  @override
  State<_CountrySearchScreen> createState() =>
      _CountrySearchScreenState();
}

class _CountrySearchScreenState extends State<_CountrySearchScreen> {
  final _controller = TextEditingController();
  CountryDirectory? _dizin;
  List<Country> _sonuclar = const [];

  @override
  void initState() {
    super.initState();
    CountryDirectory.load().then((d) {
      if (!mounted) return;
      setState(() {
        _dizin = d;
        _sonuclar = d.countries;
      });
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  String _katla(String s) => s
      .toLowerCase()
      .replaceAll('ı', 'i')
      .replaceAll('ş', 's')
      .replaceAll('ğ', 'g')
      .replaceAll('ç', 'c')
      .replaceAll('ö', 'o')
      .replaceAll('ü', 'u');

  void _ara(String q) {
    final dizin = _dizin;
    if (dizin == null) return;
    final k = _katla(q.trim());
    setState(() => _sonuclar = k.isEmpty
        ? dizin.countries
        : dizin.countries
            .where((c) =>
                _katla(c.nameTr).contains(k) ||
                _katla(c.nameEn).contains(k) ||
                c.dialCode.startsWith(k.replaceAll('+', '')))
            .toList());
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      backgroundColor: RythoColors.ink,
      appBar: AppBar(
        title: TextField(
          controller: _controller,
          autofocus: true,
          style: RythoType.body,
          onChanged: _ara,
          decoration: InputDecoration(
            hintText: l10n.countrySearchHint,
            border: InputBorder.none,
            hintStyle:
                RythoText.body(15, color: RythoColors.parchmentDim),
          ),
        ),
      ),
      body: _dizin == null
          ? const Center(child: CircularProgressIndicator())
          : ListView.builder(
              keyboardDismissBehavior:
                  ScrollViewKeyboardDismissBehavior.onDrag,
              itemCount: _sonuclar.length,
              itemBuilder: (context, i) {
                final c = _sonuclar[i];
                return ListTile(
                  leading: Text(flagEmoji(c.iso2),
                      style: const TextStyle(fontSize: 22)),
                  title: Text(c.nameFor(context),
                      style: RythoText.body(15, w: FontWeight.w600)),
                  trailing: Text('+${c.dialCode}',
                      style: RythoText.mono(13,
                          color: RythoColors.parchmentDim)),
                  onTap: () => Navigator.of(context).pop(c),
                );
              },
            ),
    );
  }
}
