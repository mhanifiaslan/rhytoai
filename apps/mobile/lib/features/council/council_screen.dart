import 'package:flutter/material.dart';

import '../../theme/rytho_theme.dart';
import 'channels_tab.dart';
import 'feed_tab.dart';
import 'messages_tab.dart';

/// MECLİS — sosyal katman: X-modeli akış (Takip/Keşfet), kanallar ve DM.
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
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: const Text('Meclis'),
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: RythoColors.magenta,
          indicatorSize: TabBarIndicatorSize.label,
          dividerColor: RythoColors.line,
          labelColor: RythoColors.parchment,
          unselectedLabelColor: RythoColors.parchmentDim,
          labelStyle: RythoText.label(12),
          unselectedLabelStyle:
              RythoText.label(12, color: RythoColors.parchmentDim),
          tabs: const [
            Tab(text: 'Akış'),
            Tab(text: 'Kanallar'),
            Tab(text: 'Mesajlar'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: const [FeedTab(), ChannelsTab(), MessagesTab()],
      ),
    );
  }
}
