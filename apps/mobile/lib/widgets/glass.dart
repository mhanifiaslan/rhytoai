import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../theme/rytho_theme.dart';

/// Cam panel: arkasını bulanıklaştıran, üst kenarı ışıklı, yumuşak
/// konturlu yüzey. Plaque'ın v2 karşılığı.
class GlassPanel extends StatelessWidget {
  const GlassPanel({
    super.key,
    required this.child,
    this.label,
    this.padding = const EdgeInsets.all(16),
    this.margin = const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
    this.radius = 18,
    this.blur = 14,
    this.glow = false,
    this.onTap,
  });

  final Widget child;
  final String? label;
  final EdgeInsets padding;
  final EdgeInsets margin;
  final double radius;
  final double blur;
  final bool glow;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final borderRadius = BorderRadius.circular(radius);
    return Container(
      margin: margin,
      decoration: glow
          ? BoxDecoration(borderRadius: borderRadius, boxShadow: const [
              BoxShadow(color: RythoColors.goldGlow, blurRadius: 26, spreadRadius: -6),
            ])
          : null,
      child: ClipRRect(
        borderRadius: borderRadius,
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: blur, sigmaY: blur),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: onTap,
              borderRadius: borderRadius,
              child: Ink(
                decoration: BoxDecoration(
                  borderRadius: borderRadius,
                  gradient: const LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [Color(0x99141B33), Color(0x66141B33)],
                  ),
                  border: Border.all(color: RythoColors.glassStroke),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // Üst kenar ışığı
                    Container(
                      height: 1,
                      margin: EdgeInsets.symmetric(horizontal: radius * 0.8),
                      decoration: const BoxDecoration(
                        gradient: LinearGradient(colors: [
                          Colors.transparent,
                          RythoColors.glassEdge,
                          Colors.transparent,
                        ]),
                      ),
                    ),
                    if (label != null)
                      Padding(
                        padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
                        child: Text(label!.toUpperCase(),
                            style: RythoText.mono(11,
                                color: RythoColors.parchmentDim)),
                      ),
                    Padding(padding: padding, child: child),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Yüzen cam alt gezinme: aktif sekme altın glow + yay animasyonu.
class CosmicDock extends StatelessWidget {
  const CosmicDock({
    super.key,
    required this.items,
    required this.index,
    required this.onChanged,
  });

  final List<({String icon, String label})> items;
  final int index;
  final ValueChanged<int> onChanged;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 14,
        right: 14,
        bottom: MediaQuery.of(context).padding.bottom + 10,
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(26),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 18, sigmaY: 18),
          child: Container(
            height: 66,
            decoration: BoxDecoration(
              color: RythoColors.glassFill,
              borderRadius: BorderRadius.circular(26),
              border: Border.all(color: RythoColors.glassStroke),
            ),
            child: Row(children: [
              for (var i = 0; i < items.length; i++)
                Expanded(child: _DockItem(
                  icon: items[i].icon,
                  label: items[i].label,
                  active: index == i,
                  onTap: () {
                    HapticFeedback.selectionClick();
                    onChanged(i);
                  },
                )),
            ]),
          ),
        ),
      ),
    );
  }
}

class _DockItem extends StatelessWidget {
  const _DockItem({
    required this.icon,
    required this.label,
    required this.active,
    required this.onTap,
  });

  final String icon;
  final String label;
  final bool active;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: onTap,
      child: AnimatedScale(
        scale: active ? 1.0 : 0.92,
        duration: const Duration(milliseconds: 320),
        curve: Curves.easeOutBack,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            AnimatedContainer(
              duration: const Duration(milliseconds: 320),
              curve: Curves.easeOutCubic,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 3),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(12),
                boxShadow: active
                    ? const [BoxShadow(color: RythoColors.goldGlow, blurRadius: 18)]
                    : null,
              ),
              child: Text(
                icon,
                style: TextStyle(
                  fontSize: 19,
                  color: active
                      ? RythoColors.goldBright
                      : RythoColors.parchmentDim,
                ),
              ),
            ),
            const SizedBox(height: 2),
            Text(label,
                style: RythoText.label(9,
                    color: active
                        ? RythoColors.goldBright
                        : RythoColors.parchmentDim)),
          ],
        ),
      ),
    );
  }
}

/// Cam görünümlü segment seçici (Takip/Keşfet vb.)
class GlassSegments extends StatelessWidget {
  const GlassSegments({
    super.key,
    required this.labels,
    required this.index,
    required this.onChanged,
  });

  final List<String> labels;
  final int index;
  final ValueChanged<int> onChanged;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 40,
      margin: const EdgeInsets.symmetric(horizontal: 16),
      padding: const EdgeInsets.all(3),
      decoration: BoxDecoration(
        color: RythoColors.glassFill,
        borderRadius: BorderRadius.circular(13),
        border: Border.all(color: RythoColors.glassStroke),
      ),
      child: Row(children: [
        for (var i = 0; i < labels.length; i++)
          Expanded(
            child: GestureDetector(
              onTap: () {
                HapticFeedback.selectionClick();
                onChanged(i);
              },
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 260),
                curve: Curves.easeOutCubic,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: index == i ? RythoColors.inkLighter : Colors.transparent,
                  borderRadius: BorderRadius.circular(10),
                  border: index == i
                      ? Border.all(color: RythoColors.glassEdge)
                      : null,
                ),
                child: Text(labels[i].toUpperCase(),
                    style: RythoText.label(11,
                        color: index == i
                            ? RythoColors.goldBright
                            : RythoColors.parchmentDim)),
              ),
            ),
          ),
      ]),
    );
  }
}
