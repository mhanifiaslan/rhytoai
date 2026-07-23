import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../theme/rytho_theme.dart';

/// Basınca 0.96'ya küçülen + hafif haptic veren sarmalayıcı — v3 hareket
/// dilinin standart "dokunuş" tepkisi.
class Pressable extends StatefulWidget {
  const Pressable({super.key, required this.child, this.onTap});
  final Widget child;
  final VoidCallback? onTap;

  @override
  State<Pressable> createState() => _PressableState();
}

class _PressableState extends State<Pressable> {
  bool _pressed = false;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTapDown: widget.onTap != null ? (_) => setState(() => _pressed = true) : null,
      onTapCancel: () => setState(() => _pressed = false),
      onTapUp: widget.onTap != null
          ? (_) {
              setState(() => _pressed = false);
              HapticFeedback.lightImpact();
              widget.onTap!();
            }
          : null,
      child: AnimatedScale(
        scale: _pressed ? 0.96 : 1.0,
        duration: const Duration(milliseconds: 120),
        curve: Curves.easeOut,
        child: widget.child,
      ),
    );
  }
}

/// Burç glifleri (Koç→Balık).
const kSignGlyphs = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓'];

/// Türkçe burç adları (Koç→Balık).
const kSignNamesTr = [
  'Koç', 'Boğa', 'İkizler', 'Yengeç', 'Aslan', 'Başak',
  'Terazi', 'Akrep', 'Yay', 'Oğlak', 'Kova', 'Balık',
];

/// Yuvarlak burç çipi: renkli degrade daire içinde glif + altta ad.
class ZodiacChip extends StatelessWidget {
  const ZodiacChip({
    super.key,
    required this.signIndex,
    this.selected = false,
    this.onTap,
    this.size = 52,
  });

  final int signIndex; // 0 = Koç ... 11 = Balık
  final bool selected;
  final VoidCallback? onTap;
  final double size;

  @override
  Widget build(BuildContext context) {
    final color = RythoColors.signColors[signIndex % 12];
    return Pressable(
      onTap: onTap,
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        AnimatedContainer(
          duration: const Duration(milliseconds: 260),
          curve: Curves.easeOutCubic,
          width: size,
          height: size,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                color.withValues(alpha: selected ? 0.55 : 0.28),
                RythoColors.inkLight,
              ],
            ),
            border: Border.all(
              color: selected ? color : Colors.white.withValues(alpha: 0.10),
              width: selected ? 1.6 : 1,
            ),
            boxShadow: selected
                ? [BoxShadow(color: color.withValues(alpha: 0.45), blurRadius: 16)]
                : null,
          ),
          child: Text(kSignGlyphs[signIndex % 12],
              style: TextStyle(fontSize: size * 0.42, color: color)),
        ),
        const SizedBox(height: 5),
        Text(kSignNamesTr[signIndex % 12],
            style: RythoText.body(10.5,
                color: selected ? RythoColors.parchment : RythoColors.parchmentDim,
                w: selected ? FontWeight.w700 : FontWeight.w500)),
      ]),
    );
  }
}

/// Degrade promo/motivasyon banner'ı — hafif shimmer döngüsüyle yaşar.
class PromoBanner extends StatelessWidget {
  const PromoBanner({
    super.key,
    required this.title,
    required this.subtitle,
    required this.buttonText,
    required this.onTap,
    this.margin = const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
  });

  final String title;
  final String subtitle;
  final String buttonText;
  final VoidCallback onTap;
  final EdgeInsets margin;

  @override
  Widget build(BuildContext context) {
    return Pressable(
      onTap: onTap,
      child: Container(
        margin: margin,
        padding: const EdgeInsets.fromLTRB(18, 16, 18, 16),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(24),
          gradient: RythoColors.primaryGradient,
          boxShadow: const [
            BoxShadow(color: RythoColors.goldGlow, blurRadius: 24, spreadRadius: -6),
          ],
        ),
        child: Stack(children: [
          // Sağda dekoratif çark
          Positioned(
            right: -26,
            top: -22,
            bottom: -22,
            child: Opacity(
              opacity: 0.22,
              child: Text('☸',
                  style: TextStyle(
                      fontSize: 110,
                      color: Colors.white.withValues(alpha: 0.9))),
            ),
          ),
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(title,
                style: RythoText.display(17,
                    color: Colors.white, w: FontWeight.w700)),
            const SizedBox(height: 5),
            Padding(
              padding: const EdgeInsets.only(right: 64),
              child: Text(subtitle,
                  style: RythoText.body(12.5,
                      color: Colors.white.withValues(alpha: 0.9))),
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 7),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(999),
              ),
              child: Text(buttonText,
                  style: RythoText.label(11.5, color: RythoColors.inkDeep)),
            ),
          ]),
        ]),
      )
          .animate(onPlay: (c) => c.repeat())
          .shimmer(
              delay: 2400.ms,
              duration: 1600.ms,
              color: Colors.white.withValues(alpha: 0.18)),
    );
  }
}

/// Animasyonlu degrade ilerleme çubuğu — 800ms'de dolar.
class GradientProgressBar extends StatelessWidget {
  const GradientProgressBar({
    super.key,
    required this.label,
    required this.percent,
    this.delay = Duration.zero,
    this.color,
  });

  final String label;
  final int percent; // 0..100
  final Duration delay;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final accent = color ?? RythoColors.magenta;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Text(label, style: RythoText.body(13, w: FontWeight.w600)),
          const Spacer(),
          Text('%$percent', style: RythoText.mono(12, color: accent))
              .animate(delay: delay)
              .fadeIn(duration: 500.ms),
        ]),
        const SizedBox(height: 7),
        LayoutBuilder(
          builder: (_, constraints) => Stack(children: [
            Container(
              height: 7,
              width: constraints.maxWidth,
              decoration: BoxDecoration(
                color: RythoColors.inkLighter,
                borderRadius: BorderRadius.circular(4),
              ),
            ),
            Container(
              height: 7,
              width: constraints.maxWidth * (percent.clamp(0, 100) / 100),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                    colors: [RythoColors.violet, accent]),
                borderRadius: BorderRadius.circular(4),
                boxShadow: [
                  BoxShadow(
                      color: accent.withValues(alpha: 0.4), blurRadius: 8),
                ],
              ),
            )
                .animate(delay: delay)
                .scaleX(
                    begin: 0,
                    end: 1,
                    alignment: Alignment.centerLeft,
                    duration: 800.ms,
                    curve: Curves.easeOutCubic),
          ]),
        ),
      ]),
    );
  }
}

/// "Yazıyor..." üç nokta animasyonu — sohbette Rytho yanıt beklerken.
class TypingDots extends StatefulWidget {
  const TypingDots({super.key});

  @override
  State<TypingDots> createState() => _TypingDotsState();
}

class _TypingDotsState extends State<TypingDots>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
      vsync: this, duration: const Duration(milliseconds: 900))
    ..repeat();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        gradient: RythoColors.primaryGradient,
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(20),
          topRight: Radius.circular(20),
          bottomLeft: Radius.circular(6),
          bottomRight: Radius.circular(20),
        ),
      ),
      child: AnimatedBuilder(
        animation: _controller,
        builder: (_, _) => Row(mainAxisSize: MainAxisSize.min, children: [
          for (var i = 0; i < 3; i++)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 2.5),
              child: Opacity(
                opacity: 0.35 +
                    0.65 *
                        (0.5 +
                            0.5 *
                                _wave(_controller.value, i)),
                child: const CircleAvatar(radius: 3.4, backgroundColor: Colors.white),
              ),
            ),
        ]),
      ),
    );
  }

  double _wave(double t, int i) {
    final phase = (t - i * 0.18) % 1.0;
    return phase < 0.5 ? (phase * 2) : (2 - phase * 2);
  }
}

/// Günlük seri rozeti: 🔥 + gün sayısı.
class StreakBadge extends StatelessWidget {
  const StreakBadge({super.key, required this.count, this.compact = true});
  final int count;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    if (count <= 0) return const SizedBox.shrink();
    return Container(
      padding: EdgeInsets.symmetric(horizontal: compact ? 10 : 14, vertical: compact ? 5 : 8),
      decoration: BoxDecoration(
        color: RythoColors.gold.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: RythoColors.gold.withValues(alpha: 0.4)),
      ),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Text('🔥', style: TextStyle(fontSize: compact ? 12 : 15)),
        const SizedBox(width: 4),
        Text('$count gün',
            style: RythoText.label(compact ? 11 : 13, color: RythoColors.goldBright)),
      ]),
    ).animate().scale(
        begin: const Offset(0.7, 0.7),
        curve: Curves.easeOutBack,
        duration: 400.ms);
  }
}

/// Öneri çipi: sohbette tıklanınca gönderilen hazır sorular.
class SuggestionChip extends StatelessWidget {
  const SuggestionChip({super.key, required this.text, required this.onTap});
  final String text;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Pressable(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: RythoColors.inkLight,
          borderRadius: BorderRadius.circular(999),
          border: Border.all(color: RythoColors.lilac.withValues(alpha: 0.30)),
        ),
        child: Text(text, style: RythoText.body(12.5, w: FontWeight.w600)),
      ),
    );
  }
}

/// Küçük bilgi çipi (gezegen konumu, retro vb.): koyu mor dolgu,
/// ince parlak kontur.
class InfoChip extends StatelessWidget {
  const InfoChip({super.key, required this.text, this.color});
  final String text;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final accent = color ?? RythoColors.lilac;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: RythoColors.inkLighter,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: accent.withValues(alpha: 0.35)),
      ),
      child: Text(text,
          style: RythoText.body(12, color: RythoColors.parchment, w: FontWeight.w600)),
    );
  }
}
