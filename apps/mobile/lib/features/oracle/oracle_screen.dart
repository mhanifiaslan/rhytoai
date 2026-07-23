import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../theme/rytho_theme.dart';
import '../../widgets/cosmic_scaffold.dart';
import 'bazi_tab.dart';
import 'face_tab.dart';
import 'iching_tab.dart';

/// KEHANET — üç kadim disiplin: I Ching, BaZi, Yüz Okuma.
/// v3'te ana ekrandaki "Kehanet Araçları" kartlarından push edilir;
/// [initialTab] ile doğrudan ilgili disipline açılır.
class OracleScreen extends ConsumerStatefulWidget {
  const OracleScreen({super.key, this.initialTab = 0});

  final int initialTab;

  @override
  ConsumerState<OracleScreen> createState() => _OracleScreenState();
}

class _OracleScreenState extends ConsumerState<OracleScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabController = TabController(
      length: 3, vsync: this, initialIndex: widget.initialTab.clamp(0, 2));

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return CosmicScaffold(
      appBar: AppBar(
        title: const Text('Kehanet Odası'),
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: RythoColors.magenta,
          indicatorSize: TabBarIndicatorSize.label,
          dividerColor: RythoColors.line,
          labelStyle: RythoText.label(12, color: RythoColors.parchment),
          unselectedLabelStyle:
              RythoText.label(12, color: RythoColors.parchmentDim),
          labelColor: RythoColors.parchment,
          unselectedLabelColor: RythoColors.parchmentDim,
          tabs: const [
            Tab(text: 'I CHING 🪙'),
            Tab(text: 'BAZI 🀄'),
            Tab(text: 'YÜZ 🔮'),
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
