import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show PlatformException;
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:purchases_flutter/purchases_flutter.dart';

import '../../core/subscription.dart';
import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/glass.dart';
import '../profile/legal_page.dart';

/// RYTHO+ paywall.
///
/// Mağaza kuralları gereği bu ekranda şunlar **görünür olmak zorunda**:
/// fiyat, yenileme dönemi, denemenin ne zaman ücrete döneceği, iptalin nasıl
/// yapılacağı ve "Satın alımları geri yükle" seçeneği. Bunlar süsleme değil,
/// eksikse inceleme reddi sebebidir.
class PaywallScreen extends ConsumerStatefulWidget {
  const PaywallScreen({super.key, this.reason});

  /// Kilitli uçtan dönen açıklama ("… Rytho+ aboneliğine dahildir").
  final String? reason;

  @override
  ConsumerState<PaywallScreen> createState() => _PaywallScreenState();
}

class _PaywallScreenState extends ConsumerState<PaywallScreen> {
  Package? _selected;
  bool _busy = false;
  String? _error;

  /// Faydalar dile göre üretildiği için const olamaz.
  List<(String, String, String)> _benefits(AppLocalizations l10n) => [
        ('🌙', l10n.benefitDailyTitle, l10n.benefitDailyBody),
        ('🗺️', l10n.benefitNatalTitle, l10n.benefitNatalBody),
        ('💞', l10n.benefitDyadTitle, l10n.benefitDyadBody),
        ('💬', l10n.benefitChatTitle, l10n.benefitChatBody),
        ('🀄', l10n.benefitBaziTitle, l10n.benefitBaziBody),
      ];

  Future<void> _buy() async {
    final package = _selected;
    if (package == null) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final ok = await purchasePackage(ref, package);
      if (ok && mounted) Navigator.of(context).pop(true);
    } on PlatformException catch (e) {
      final code = PurchasesErrorHelper.getErrorCode(e);
      if (code != PurchasesErrorCode.purchaseCancelledError && mounted) {
        setState(() => _error =
            e.message ?? AppLocalizations.of(context).purchaseFailed);
      }
    } catch (e) {
      if (mounted) setState(() => _error = '$e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _restore() async {
    setState(() => _busy = true);
    try {
      final ok = await restorePurchases(ref);
      if (!mounted) return;
      if (ok) {
        Navigator.of(context).pop(true);
      } else {
        setState(() =>
            _error = AppLocalizations.of(context).noActiveSubscription);
      }
    } catch (e) {
      if (mounted) setState(() => _error = '$e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final offerings = ref.watch(offeringsProvider);
    final l10n = AppLocalizations.of(context);

    return CosmicScaffold(
      appBar: AppBar(
        title: Text(l10n.paywallTitle),
        leading: IconButton(
          icon: const Icon(Icons.close_rounded, size: 22),
          onPressed: () => Navigator.of(context).pop(false),
        ),
      ),
      body: ListView(padding: const EdgeInsets.only(bottom: 32), children: [
        if (widget.reason != null)
          GlassPanel(
            child: Text(widget.reason!,
                style: RythoText.body(14, color: RythoColors.goldBright)),
          ),
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 4),
          child: Text(l10n.paywallHeadline, style: RythoText.display(26)),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 16),
          child: Text(
            l10n.paywallBody,
            style: RythoText.body(13.5, color: RythoColors.parchmentDim),
          ),
        ),
        for (final (i, benefit) in _benefits(l10n).indexed)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 7),
            child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(benefit.$1, style: const TextStyle(fontSize: 19)),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(benefit.$2, style: RythoText.body(14.5, w: FontWeight.w700)),
                      const SizedBox(height: 2),
                      Text(benefit.$3,
                          style: RythoText.body(12.5,
                              color: RythoColors.parchmentDim)),
                    ]),
              ),
            ]),
          )
              .animate(delay: Duration(milliseconds: 60 * i))
              .fadeIn(duration: 320.ms)
              .slideX(begin: 0.05, curve: Curves.easeOutCubic),
        const SectionDivider(),
        offerings.when(
          loading: () => const Padding(
            padding: EdgeInsets.symmetric(vertical: 30),
            child: Center(child: AstrolabeSpinner()),
          ),
          error: (e, _) => _unavailable(l10n, '$e'),
          data: (packages) {
            if (packages.isEmpty) return _unavailable(l10n, null);
            _selected ??= _defaultPackage(packages);
            // Tek plan varsa seçim yapılacak bir şey yok; radyo düğmesi
            // göstermek kullanıcıya sahte bir karar sunar.
            final tekPlan = packages.length == 1;
            return Column(children: [
              for (final package in packages)
                _PlanTile(
                  package: package,
                  selected: identical(package, _selected) ||
                      package.identifier == _selected?.identifier,
                  showRadio: !tekPlan,
                  onTap: () => setState(() => _selected = package),
                ),
            ]);
          },
        ),
        if (_error != null)
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 8, 20, 0),
            child: Text(_error!,
                style: RythoText.body(12.5, color: RythoColors.magenta)),
          ),
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
          child: GoldButton(
            text: _selected == null
                ? l10n.paywallChoosePlan
                : l10n.paywallContinue,
            busy: _busy,
            onPressed: _selected == null ? null : _buy,
          ),
        ),
        Center(
          child: TextButton(
            onPressed: _busy ? null : _restore,
            child: Text(l10n.restorePurchases,
                style: RythoText.label(12, color: RythoColors.parchmentDim)),
          ),
        ),
        // Mağaza kuralı: iptal ve yenileme koşulları satın alma ekranında
        // açıkça yazmalı.
        Padding(
          padding: const EdgeInsets.fromLTRB(24, 8, 24, 8),
          child: Text(
            l10n.subscriptionTerms,
            style: RythoText.body(11.5, color: RythoColors.parchmentDim),
            textAlign: TextAlign.center,
          ),
        ),
        Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          TextButton(
            onPressed: () => Navigator.of(context).push(MaterialPageRoute(
                builder: (_) => LegalPage(
                    title: l10n.termsOfUse,
                    sections: termsOfUseSections(
                        Localizations.localeOf(context).languageCode)))),
            child: Text(l10n.termsOfUse, style: RythoText.label(11)),
          ),
          Text('·', style: RythoText.label(11, color: RythoColors.parchmentDim)),
          TextButton(
            onPressed: () => Navigator.of(context).push(MaterialPageRoute(
                builder: (_) => LegalPage(
                    title: l10n.privacyPolicy,
                    sections: privacyPolicySections(
                        Localizations.localeOf(context).languageCode)))),
            child: Text(l10n.privacyPolicy, style: RythoText.label(11)),
          ),
        ]),
      ]),
    );
  }

  /// Yıllık paket varsayılan seçili gelir (en iyi değer).
  Package _defaultPackage(List<Package> packages) {
    for (final package in packages) {
      if (package.packageType == PackageType.annual) return package;
    }
    return packages.first;
  }

  Widget _unavailable(AppLocalizations l10n, String? detail) => GlassPanel(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(l10n.billingUnavailable, style: RythoText.display(16)),
          const SizedBox(height: 6),
          Text(
            detail ??
                (billingConfigured
                    ? l10n.billingNoPackages
                    : l10n.billingNotConfigured),
            style: RythoText.body(12.5, color: RythoColors.parchmentDim),
          ),
        ]),
      );
}

class _PlanTile extends StatelessWidget {
  const _PlanTile({
    required this.package,
    required this.selected,
    required this.onTap,
    this.showRadio = true,
  });

  final Package package;
  final bool selected;
  final VoidCallback onTap;
  final bool showRadio;

  bool get _isAnnual => package.packageType == PackageType.annual;

  /// Deneme süresi varsa "3 gün ücretsiz, sonra X" — mağaza kuralı gereği
  /// denemenin ne zaman ücrete döndüğü satın alma ekranında yazmak zorunda.
  static String _priceLine(AppLocalizations l10n, StoreProduct product) {
    final intro = product.introductoryPrice;
    if (intro == null) return product.priceString;

    final unit = switch (intro.periodUnit) {
      PeriodUnit.day => l10n.unitDay,
      PeriodUnit.week => l10n.unitWeek,
      PeriodUnit.month => l10n.unitMonth,
      PeriodUnit.year => l10n.unitYear,
      _ => l10n.unitDay,
    };
    return l10n.trialThenPrice(
        intro.periodNumberOfUnits, unit, product.priceString);
  }

  @override
  Widget build(BuildContext context) {
    final product = package.storeProduct;
    final l10n = AppLocalizations.of(context);
    final title = switch (package.packageType) {
      PackageType.annual => l10n.planAnnual,
      PackageType.weekly => l10n.planWeekly,
      PackageType.monthly => l10n.planMonthly,
      _ => product.title,
    };

    return GlassPanel(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      glow: selected,
      onTap: onTap,
      child: Row(children: [
        if (showRadio) ...[
          Icon(
            selected
                ? Icons.radio_button_checked_rounded
                : Icons.radio_button_unchecked_rounded,
            size: 20,
            color: selected ? RythoColors.gold : RythoColors.parchmentDim,
          ),
          const SizedBox(width: 12),
        ],
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Text(title, style: RythoText.display(17)),
              if (_isAnnual) ...[
                const SizedBox(width: 8),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: RythoColors.gold.withValues(alpha: 0.16),
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text(l10n.bestValue,
                      style: RythoText.label(9, color: RythoColors.goldBright)),
                ),
              ],
            ]),
            const SizedBox(height: 2),
            Text(_priceLine(l10n, product),
                style: RythoText.body(12.5, color: RythoColors.parchmentDim)),
          ]),
        ),
      ]),
    );
  }
}
