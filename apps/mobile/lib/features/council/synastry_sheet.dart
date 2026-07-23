import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';
import 'messages_tab.dart';

/// Bir kullanıcıya dokununca açılan profil sayfası: rozetler,
/// kozmik uyum (sinastri) raporu ve DM başlatma.
Future<void> showUserSheet(BuildContext context, String uid) {
  return showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    backgroundColor: RythoColors.inkLight,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(4)),
      side: BorderSide(color: RythoColors.line),
    ),
    builder: (_) => DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.6,
      maxChildSize: 0.95,
      builder: (_, scrollController) =>
          UserSheet(uid: uid, scrollController: scrollController),
    ),
  );
}

class UserSheet extends ConsumerStatefulWidget {
  const UserSheet({super.key, required this.uid, required this.scrollController});
  final String uid;
  final ScrollController scrollController;

  @override
  ConsumerState<UserSheet> createState() => _UserSheetState();
}

class _UserSheetState extends ConsumerState<UserSheet> {
  Map<String, dynamic>? _other;
  String? _synastry;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    FirebaseFirestore.instance
        .collection('users')
        .doc(widget.uid)
        .get()
        .then((doc) {
      if (mounted) setState(() => _other = doc.data());
    });
  }

  Future<void> _loadSynastry() async {
    final me = FirebaseAuth.instance.currentUser!;
    final myProfile = (await FirebaseFirestore.instance
            .collection('users')
            .doc(me.uid)
            .get())
        .data();
    if (myProfile == null || _other == null) return;

    setState(() => _busy = true);
    try {
      final dio = ref.read(apiProvider);
      final response = await dio.post('/api/v1/reports/synastry', data: {
        'person1': birthPayload(myProfile),
        'person2': birthPayload(_other!),
      });
      setState(() => _synastry = response.data['data']['report']);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Uyum hesaplanamadı: $e')));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final other = _other;
    if (other == null) {
      return const SizedBox(height: 300, child: Center(child: AstrolabeSpinner()));
    }
    final myUid = FirebaseAuth.instance.currentUser!.uid;

    return ListView(
      controller: widget.scrollController,
      padding: const EdgeInsets.all(24),
      children: [
        Center(
          child: CircleAvatar(
            radius: 34,
            backgroundColor: RythoColors.inkLighter,
            backgroundImage:
                other['photoUrl'] != null ? NetworkImage(other['photoUrl']) : null,
            child: other['photoUrl'] == null
                ? Text('☽', style: RythoText.display(24))
                : null,
          ),
        ),
        const SizedBox(height: 12),
        Center(
            child:
                Text(other['displayName'] ?? 'Gezgin', style: RythoText.display(26))),
        const SizedBox(height: 6),
        Center(
          child: Text(
            [
              if (other['sunSign'] != null) '☉ ${other['sunSign']}',
              if (other['moonSign'] != null) '☽ ${other['moonSign']}',
              if (other['ascendant'] != null) '↑ ${other['ascendant']}',
            ].join('   '),
            style: RythoText.mono(12, color: RythoColors.parchmentDim),
          ),
        ),
        if ((other['bio'] as String?)?.isNotEmpty == true) ...[
          const SizedBox(height: 12),
          Center(
            child: Text(other['bio'],
                textAlign: TextAlign.center,
                style: RythoText.body(13.5, color: RythoColors.parchmentDim)),
          ),
        ],
        const SizedBox(height: 24),
        if (widget.uid != myUid)
          Row(children: [
            Expanded(
              child: GoldButton(
                text: 'Kozmik uyum',
                busy: _busy,
                onPressed: _synastry == null ? _loadSynastry : null,
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: GoldButton(
                text: 'Mesaj gönder',
                onPressed: () {
                  Navigator.of(context).pop();
                  openChat(context, widget.uid,
                      other['displayName'] ?? 'Gezgin');
                },
              ),
            ),
          ]),
        if (_synastry != null) ...[
          const SectionDivider(),
          MarginNote(title: 'İki haritanın söyleşisi', text: _synastry!),
        ],
        const SizedBox(height: 24),
      ],
    );
  }
}
