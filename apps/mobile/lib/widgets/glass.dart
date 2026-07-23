import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../theme/rytho_theme.dart';

/// v3 kart: koyu mor dolgu, 20px köşe, %6 beyaz kontur, üst kenar ışığı.
/// Adı tarihsel — artık blur zorunlu değil (blur: 0 varsayılan davranış
/// için performans dostu düz dolgu kullanılır).
class GlassPanel extends StatelessWidget {
  const GlassPanel({
    super.key,
    required this.child,
    this.label,
    this.padding = const EdgeInsets.all(16),
    this.margin = const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
    this.radius = 22,
    this.blur = 0,
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
    Widget content = Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: borderRadius,
        child: Ink(
          decoration: BoxDecoration(
            borderRadius: borderRadius,
            color: RythoColors.glassFill,
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
                  child: Text(label!,
                      style: RythoText.label(11,
                          color: RythoColors.parchmentDim)),
                ),
              Padding(padding: padding, child: child),
            ],
          ),
        ),
      ),
    );

    if (blur > 0) {
      content = BackdropFilter(
        filter: ImageFilter.blur(sigmaX: blur, sigmaY: blur),
        child: content,
      );
    }

    return Container(
      margin: margin,
      decoration: glow
          ? BoxDecoration(borderRadius: borderRadius, boxShadow: const [
              BoxShadow(color: RythoColors.goldGlow, blurRadius: 26, spreadRadius: -6),
            ])
          : null,
      child: ClipRRect(borderRadius: borderRadius, child: content),
    );
  }
}

/// v3 alt gezinme: ince koyu saydam bar, 4 sade outline ikon + ORTADA
/// yukarı taşan, degrade dolgulu, glow'lu dairesel AI butonu.
class CosmicDock extends StatelessWidget {
  const CosmicDock({
    super.key,
    required this.items,
    required this.index,
    required this.onChanged,
    required this.onCenterTap,
  });

  /// 4 öğe beklenir: ilk 2'si merkezin solunda, son 2'si sağında.
  final List<({IconData icon, IconData activeIcon, String label})> items;
  final int index;
  final ValueChanged<int> onChanged;
  final VoidCallback onCenterTap;

  @override
  Widget build(BuildContext context) {
    final bottomPad = MediaQuery.of(context).padding.bottom;
    return SizedBox(
      height: 86 + bottomPad,
      child: Stack(clipBehavior: Clip.none, alignment: Alignment.bottomCenter, children: [
        // Bar
        Positioned(
          left: 0,
          right: 0,
          bottom: 0,
          height: 64 + bottomPad,
          child: ClipRect(
            child: BackdropFilter(
              filter: ImageFilter.blur(sigmaX: 16, sigmaY: 16),
              child: Container(
                padding: EdgeInsets.only(bottom: bottomPad),
                decoration: const BoxDecoration(
                  color: Color(0xCC120B1C),
                  border: Border(top: BorderSide(color: RythoColors.glassStroke)),
                ),
                child: Row(children: [
                  for (var i = 0; i < 2; i++)
                    Expanded(child: _DockItem(
                      item: items[i],
                      active: index == i,
                      onTap: () {
                        HapticFeedback.selectionClick();
                        onChanged(i);
                      },
                    )),
                  // Merkez buton boşluğu
                  const SizedBox(width: 72),
                  for (var i = 2; i < items.length; i++)
                    Expanded(child: _DockItem(
                      item: items[i],
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
        ),
        // Merkez AI butonu — yukarı taşar, sürekli yumuşak glow pulse
        Positioned(
          bottom: 26 + bottomPad,
          child: _CenterAiButton(onTap: onCenterTap),
        ),
      ]),
    );
  }
}

/// Degrade dolgulu, glow'lu, nefes alan merkez AI butonu (✦).
class _CenterAiButton extends StatefulWidget {
  const _CenterAiButton({required this.onTap});
  final VoidCallback onTap;

  @override
  State<_CenterAiButton> createState() => _CenterAiButtonState();
}

class _CenterAiButtonState extends State<_CenterAiButton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulse = AnimationController(
      vsync: this, duration: const Duration(milliseconds: 1600))
    ..repeat(reverse: true);
  bool _pressed = false;

  @override
  void dispose() {
    _pulse.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => setState(() => _pressed = true),
      onTapCancel: () => setState(() => _pressed = false),
      onTapUp: (_) {
        setState(() => _pressed = false);
        HapticFeedback.mediumImpact();
        widget.onTap();
      },
      child: AnimatedBuilder(
        animation: _pulse,
        builder: (_, _) {
          final t = Curves.easeInOut.transform(_pulse.value);
          final scale = (_pressed ? 0.94 : 1.0) * (1.0 + 0.06 * t);
          return Transform.scale(
            scale: scale,
            child: Container(
              width: 62,
              height: 62,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RythoColors.primaryGradient,
                border: Border.all(color: Colors.white.withValues(alpha: 0.25), width: 1.4),
                boxShadow: [
                  BoxShadow(
                    color: RythoColors.magentaGlow,
                    blurRadius: 22 + 12 * t,
                    spreadRadius: 1 + 2 * t,
                  ),
                  const BoxShadow(
                    color: RythoColors.goldGlow,
                    blurRadius: 40,
                    spreadRadius: -2,
                  ),
                ],
              ),
              child: const Text('✦',
                  style: TextStyle(fontSize: 26, color: Colors.white)),
            ),
          );
        },
      ),
    );
  }
}

class _DockItem extends StatelessWidget {
  const _DockItem({
    required this.item,
    required this.active,
    required this.onTap,
  });

  final ({IconData icon, IconData activeIcon, String label}) item;
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
            ShaderMask(
              shaderCallback: (bounds) => (active
                      ? RythoColors.primaryGradient
                      : const LinearGradient(colors: [
                          RythoColors.parchmentDim,
                          RythoColors.parchmentDim,
                        ]))
                  .createShader(bounds),
              child: Icon(active ? item.activeIcon : item.icon,
                  size: 23, color: Colors.white),
            ),
            const SizedBox(height: 3),
            Text(item.label,
                style: RythoText.label(9.5,
                    color: active
                        ? RythoColors.parchment
                        : RythoColors.parchmentDim)),
          ],
        ),
      ),
    );
  }
}

/// Segment seçici (Takip/Keşfet vb.) — aktif segment degrade dolgulu.
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
      height: 42,
      margin: const EdgeInsets.symmetric(horizontal: 16),
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: RythoColors.glassFill,
        borderRadius: BorderRadius.circular(16),
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
                  gradient: index == i ? RythoColors.primaryGradient : null,
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: index == i
                      ? const [BoxShadow(color: RythoColors.goldGlow, blurRadius: 14)]
                      : null,
                ),
                child: Text(labels[i],
                    style: RythoText.label(12,
                        color: index == i
                            ? Colors.white
                            : RythoColors.parchmentDim)),
              ),
            ),
          ),
      ]),
    );
  }
}
