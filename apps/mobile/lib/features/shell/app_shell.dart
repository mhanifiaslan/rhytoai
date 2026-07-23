import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart' show StateProvider;

import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/glass.dart';
import '../atlas/atlas_screen.dart';
import '../chat/chat_screen.dart';
import '../council/council_screen.dart';
import '../profile/profile_screen.dart';
import '../sky/sky_screen.dart';

/// Aktif sekme — ekranlar (örn. promo banner) sekme değiştirebilsin diye
/// Riverpod üzerinden paylaşılır. 0: Gökyüzü, 1: Atlas, 2: Meclis, 3: Profil.
final shellTabProvider = StateProvider<int>((_) => 0);

/// Ana kabuk: yıldız alanı zemin + 4 sekme + merkez degrade AI butonu
/// (Rytho sohbetini açar). Kehanet araçlarına ana ekran kartlarından gidilir.
class AppShell extends ConsumerWidget {
  const AppShell({super.key});

  static const _tabs = [
    (icon: Icons.home_outlined, activeIcon: Icons.home_rounded, label: 'Gökyüzü'),
    (icon: Icons.donut_large_outlined, activeIcon: Icons.donut_large_rounded, label: 'Atlas'),
    (icon: Icons.forum_outlined, activeIcon: Icons.forum_rounded, label: 'Meclis'),
    (icon: Icons.person_outline_rounded, activeIcon: Icons.person_rounded, label: 'Profil'),
  ];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final index = ref.watch(shellTabProvider);
    return CosmicScaffold(
      extendBody: true,
      body: Stack(children: [
        for (var i = 0; i < 4; i++)
          IgnorePointer(
            ignoring: index != i,
            child: AnimatedOpacity(
              opacity: index == i ? 1 : 0,
              duration: const Duration(milliseconds: 280),
              curve: Curves.easeOutCubic,
              child: AnimatedSlide(
                offset: index == i ? Offset.zero : const Offset(0, 0.012),
                duration: const Duration(milliseconds: 280),
                curve: Curves.easeOutCubic,
                child: const [
                  SkyScreen(),
                  AtlasScreen(),
                  CouncilScreen(),
                  ProfileScreen(),
                ][i],
              ),
            ),
          ),
      ]),
      bottomNavigationBar: CosmicDock(
        items: _tabs,
        index: index,
        onChanged: (i) => ref.read(shellTabProvider.notifier).state = i,
        onCenterTap: () => Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => const ChatScreen()),
        ),
      ),
    );
  }
}
