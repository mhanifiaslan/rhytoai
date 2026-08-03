/// Konu listesi — sohbetin yeni giriş kapısı (Revize R4).
///
/// Kullanıcının isteği birebir: "mesajlar konu konu en yeniden eskiye göre
/// sıralanmalı, kaldığı yerden devam edebilmeli veyahut yeni bir konu ile
/// yeni mesajlaşmalar yapılabilmeli." Karta dokun → kaldığı yerden;
/// "+" → yeni konu. Konu 30 gün kullanılmazsa sunucu temizler.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../core/api.dart' show apiProvider, friendlyError;
import '../../core/conversations.dart';
import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import '../../theme/rytho_tokens.dart';
import '../../widgets/atlas_widgets.dart';
import '../../widgets/common.dart';
import '../../widgets/cosmic_scaffold.dart';
import '../../widgets/glass.dart';
import 'chat_screen.dart';

class ConversationListScreen extends ConsumerWidget {
  const ConversationListScreen({super.key});

  void _ac(BuildContext context, {String? conversationId}) {
    Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => ChatScreen(conversationId: conversationId),
    ));
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final konular = ref.watch(conversationsProvider);

    return CosmicScaffold(
      appBar: AppBar(
        title: Text(l10n.chatTitle),
        actions: [
          IconButton(
            tooltip: l10n.newConversation,
            icon: const Icon(Icons.add_comment_outlined, size: 21),
            onPressed: () => _ac(context),
          ),
        ],
      ),
      body: SafeArea(
        child: konular.when(
          loading: () => const Center(child: AstrolabeSpinner()),
          error: (e, _) => Padding(
            padding: const EdgeInsets.all(RythoSpace.xl),
            child: ErrorCard(message: friendlyError(e, l10n)),
          ),
          data: (liste) => liste.isEmpty
              ? EmptyState(
                  emoji: '✦',
                  title: l10n.chatEmptyTitle,
                  description: l10n.chatEmptyBody,
                  action: GoldButton(
                    text: l10n.newConversation,
                    onPressed: () => _ac(context),
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.fromLTRB(RythoSpace.lg,
                      RythoSpace.sm, RythoSpace.lg, RythoSpace.xxl),
                  itemCount: liste.length,
                  itemBuilder: (_, i) {
                    final konu = liste[i];
                    return Dismissible(
                      key: ValueKey(konu.id),
                      direction: DismissDirection.endToStart,
                      background: Container(
                        alignment: Alignment.centerRight,
                        padding: const EdgeInsets.only(right: RythoSpace.xl),
                        decoration: BoxDecoration(
                          color: RythoColors.madder.withValues(alpha: 0.25),
                          borderRadius:
                              BorderRadius.circular(RythoRadius.card),
                        ),
                        child: const Icon(Icons.delete_outline_rounded,
                            color: RythoColors.madder),
                      ),
                      // Silme SUNUCUDAN; başarısızsa kart geri gelir —
                      // ekrandan kaybolup arşivde yaşamaya devam eden bir
                      // konu, "sildim sanmıştım" sürprizi doğururdu.
                      confirmDismiss: (_) async {
                        try {
                          await deleteConversation(
                              ref.read(apiProvider), konu.id);
                          return true;
                        } catch (e) {
                          if (context.mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                    content:
                                        Text(friendlyError(e, l10n))));
                          }
                          return false;
                        }
                      },
                      child: GlassPanel(
                        margin:
                            const EdgeInsets.only(bottom: RythoSpace.md),
                        onTap: () =>
                            _ac(context, conversationId: konu.id),
                        child: Row(children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment:
                                  CrossAxisAlignment.start,
                              children: [
                                Text(konu.title,
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                    style: RythoType.cardTitle),
                                const SizedBox(height: 2),
                                Text(
                                  konu.updatedAt != null
                                      ? DateFormat(
                                              'd MMM · HH:mm',
                                              Localizations.localeOf(
                                                      context)
                                                  .toLanguageTag())
                                          .format(konu.updatedAt!)
                                      : '',
                                  style: RythoType.caption,
                                ),
                              ],
                            ),
                          ),
                          const Icon(Icons.chevron_right_rounded,
                              size: 20, color: RythoColors.parchmentDim),
                        ]),
                      ),
                    );
                  },
                ),
        ),
      ),
    );
  }
}
