import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../theme/rytho_theme.dart';
import 'bazi_tab.dart';
import 'face_tab.dart';
import 'iching_tab.dart';

/// KEHANET — üç kadim disiplin: I Ching, BaZi, Yüz Okuma.
class OracleScreen extends ConsumerStatefulWidget {
  const OracleScreen({super.key});

  @override
  ConsumerState<OracleScreen> createState() => _OracleScreenState();
}

class _OracleScreenState extends ConsumerState<OracleScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabController =
      TabController(length: 3, vsync: this);

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: const Text('Kehanet Odası'),
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: RythoColors.gold,
          indicatorSize: TabBarIndicatorSize.label,
          dividerColor: RythoColors.line,
          labelStyle: RythoText.label(12, color: RythoColors.goldBright),
          unselectedLabelStyle:
              RythoText.label(12, color: RythoColors.parchmentDim),
          tabs: const [
            Tab(text: 'I CHING'),
            Tab(text: 'BAZI'),
            Tab(text: 'YÜZ'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: const [IChingTab(), BaziTab(), FaceTab()],
      ),
    );
  }
}
