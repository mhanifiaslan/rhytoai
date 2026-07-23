import 'package:flutter/material.dart';

import '../../theme/rytho_theme.dart';
import '../atlas/atlas_screen.dart';
import '../council/council_screen.dart';
import '../oracle/oracle_screen.dart';
import '../profile/profile_screen.dart';
import '../sky/sky_screen.dart';

/// Ana kabuk: 5 sekme — Gökyüzü, Atlas, Kehanet, Meclis, Sicil.
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
    return Scaffold(
      body: IndexedStack(
        index: _index,
        children: const [
          SkyScreen(),
          AtlasScreen(),
          OracleScreen(),
          CouncilScreen(),
          ProfileScreen(),
        ],
      ),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          color: RythoColors.ink,
          border: Border(top: BorderSide(color: RythoColors.line)),
        ),
        child: SafeArea(
          child: SizedBox(
            height: 62,
            child: Row(
              children: [
                for (var i = 0; i < _tabs.length; i++)
                  Expanded(
                    child: InkWell(
                      onTap: () => setState(() => _index = i),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            _tabs[i].icon,
                            style: TextStyle(
                              fontSize: 18,
                              color: _index == i
                                  ? RythoColors.goldBright
                                  : RythoColors.parchmentDim,
                            ),
                          ),
                          const SizedBox(height: 3),
                          Text(
                            _tabs[i].label,
                            style: RythoText.label(9,
                                color: _index == i
                                    ? RythoColors.goldBright
                                    : RythoColors.parchmentDim),
                          ),
                          const SizedBox(height: 4),
                          AnimatedContainer(
                            duration: const Duration(milliseconds: 250),
                            curve: Curves.easeOutCubic,
                            height: 2,
                            width: _index == i ? 16 : 0,
                            color: RythoColors.gold,
                          ),
                        ],
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
