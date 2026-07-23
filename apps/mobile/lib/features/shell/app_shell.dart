import 'package:flutter/material.dart';

import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/glass.dart';
import '../atlas/atlas_screen.dart';
import '../council/council_screen.dart';
import '../oracle/oracle_screen.dart';
import '../profile/profile_screen.dart';
import '../sky/sky_screen.dart';

/// Ana kabuk: yıldız alanı zemin + 5 sekmeli yüzen cam dock.
class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int _index = 0;

  static const _tabs = [
    (icon: '☉', label: 'GÖKYÜZÜ'),
    (icon: '𝛑', label: 'ATLAS'),
    (icon: '䷀', label: 'KEHANET'),
    (icon: '✦', label: 'MECLİS'),
    (icon: '☽', label: 'SİCİL'),
  ];

  @override
  Widget build(BuildContext context) {
    return CosmicScaffold(
      extendBody: true,
      body: Stack(children: [
        for (var i = 0; i < 5; i++)
          IgnorePointer(
            ignoring: _index != i,
            child: AnimatedOpacity(
              opacity: _index == i ? 1 : 0,
              duration: const Duration(milliseconds: 280),
              curve: Curves.easeOutCubic,
              child: AnimatedSlide(
                offset: _index == i ? Offset.zero : const Offset(0, 0.012),
                duration: const Duration(milliseconds: 280),
                curve: Curves.easeOutCubic,
                child: const [
                  SkyScreen(),
                  AtlasScreen(),
                  OracleScreen(),
                  CouncilScreen(),
                  ProfileScreen(),
                ][i],
              ),
            ),
          ),
      ]),
      bottomNavigationBar: CosmicDock(
        items: _tabs,
        index: _index,
        onChanged: (i) => setState(() => _index = i),
      ),
    );
  }
}
