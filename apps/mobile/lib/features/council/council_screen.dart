import 'package:flutter/material.dart';

import '../../theme/rytho_theme.dart';
import 'feed_tab.dart';
import 'messages_tab.dart';
import 'networks_tab.dart';

/// MECLİS — sosyal katman: herkese açık akış, ağlar (topluluklar) ve DM.
class CouncilScreen extends StatefulWidget {
  const CouncilScreen({super.key});

  @override
  State<CouncilScreen> createState() => _CouncilScreenState();
}

class _CouncilScreenState extends State<CouncilScreen>
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
      appBar: AppBar(
        title: const Text('Meclis'),
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: RythoColors.gold,
          indicatorSize: TabBarIndicatorSize.label,
          dividerColor: RythoColors.line,
          labelStyle: RythoText.label(12, color: RythoColors.goldBright),
          unselectedLabelStyle:
              RythoText.label(12, color: RythoColors.parchmentDim),
          tabs: const [
            Tab(text: 'AKIŞ'),
            Tab(text: 'AĞLAR'),
            Tab(text: 'MESAJLAR'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: const [FeedTab(), NetworksTab(), MessagesTab()],
      ),
    );
  }
}
