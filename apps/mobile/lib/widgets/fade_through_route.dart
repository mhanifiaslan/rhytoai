import 'package:flutter/material.dart';

import '../theme/rytho_tokens.dart';
import 'motion.dart';

/// İçerik açılış rotası (R12-B2): kart → okuma sayfası, kilit → paywall.
///
/// Koreografi: eski sayfa ilk ~90ms görünür kalır, sonra gelen sayfa
/// fade + hafif büyüme (0.96→1) ile üstünü örter — Material'ın
/// "fade through" deseni. Hero BİLEREK yok: metin ağırlıklı sayfalarda
/// paylaşılan öğenin stil değişimi titrer; geçişi sayfa bütünü taşır.
class FadeThroughRoute<T> extends PageRouteBuilder<T> {
  FadeThroughRoute({required WidgetBuilder builder, super.settings})
      : super(
          pageBuilder: (context, _, _) => builder(context),
          transitionDuration: const Duration(milliseconds: 350),
          reverseTransitionDuration: RythoMotion.base,
          transitionsBuilder: (context, animation, _, child) {
            if (reduceMotion(context)) return child;
            // İlk ~%26 boş: eski sayfanın "çekilme" payı (90ms/350ms).
            final gelen = CurvedAnimation(
                parent: animation,
                curve: const Interval(0.26, 1, curve: RythoMotion.enter));
            return FadeTransition(
              opacity: gelen,
              child: ScaleTransition(
                scale: Tween(begin: 0.96, end: 1.0).animate(gelen),
                child: child,
              ),
            );
          },
        );
}
