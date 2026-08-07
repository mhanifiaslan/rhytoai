/// Profil fotoğrafı değiştirme akışı (U1).
///
/// Galeriden seç → TAM EKRAN konumlandırma (sürükle + iki parmakla
/// yakınlaştır, dairesel maske) → 512px kare olarak yakala → Firebase
/// Storage `avatars/{uid}/avatar.png` → `users/{uid}.photoUrl` güncelle
/// + publicProfiles senkronu (arkadaş kartları da yeni fotoğrafı görsün).
///
/// Kırpma HARİCİ PAKETSİZ: InteractiveViewer zaten pan/zoom'un kendisi;
/// kare görünüm RepaintBoundary ile piksel olarak yakalanır. Harici
/// kırpıcı paketleri (uCrop vb.) platform aktivitesi + izin + tema
/// senkronu ister — bu akışın ihtiyacı bir "yerleştir ve kaydet".
library;

import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_storage/firebase_storage.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:image_picker/image_picker.dart';

import '../../core/friends.dart' show syncPublicProfile;
import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import '../../widgets/atlas_widgets.dart';

/// Akışın tamamı: seçim iptalinde ya da hatada sessizce false döner;
/// başarıda photoUrl yazılmıştır (çağıran snackbar gösterir).
Future<bool> changeAvatar(BuildContext context) async {
  final user = FirebaseAuth.instance.currentUser;
  if (user == null) return false;

  final secim = await ImagePicker().pickImage(
    source: ImageSource.gallery,
    // Kaynak boyut sınırlanır: 4000px'lik ham fotoğrafı belleğe almak
    // gereksiz; konumlandırma 1200px'te de aynı hassasiyette.
    maxWidth: 1200,
    maxHeight: 1200,
  );
  if (secim == null || !context.mounted) return false;

  final bytes = await secim.readAsBytes();
  if (!context.mounted) return false;

  final kirpilmis = await Navigator.of(context).push<Uint8List>(
    MaterialPageRoute(
        builder: (_) => _AvatarCropScreen(imageBytes: bytes),
        fullscreenDialog: true),
  );
  if (kirpilmis == null || !context.mounted) return false;

  // Yükleme + profil yazımı. Storage kuralı: sahibi yazar, <5MB, image/*.
  final ref = FirebaseStorage.instance
      .ref('avatars/${user.uid}/avatar.png');
  await ref.putData(
      kirpilmis, SettableMetadata(contentType: 'image/png'));
  final url = await ref.getDownloadURL();

  await FirebaseFirestore.instance
      .collection('users')
      .doc(user.uid)
      .set({'photoUrl': url}, SetOptions(merge: true));
  // Arkadaş kartlarındaki kopya da tazelensin (friends.dart photoUrl'i
  // publicProfiles'a taşıyor).
  await syncPublicProfile();
  return true;
}

/// Tam ekran konumlandırma: kare yakalama alanı + dairesel maske önizleme.
class _AvatarCropScreen extends StatefulWidget {
  const _AvatarCropScreen({required this.imageBytes});

  final Uint8List imageBytes;

  @override
  State<_AvatarCropScreen> createState() => _AvatarCropScreenState();
}

class _AvatarCropScreenState extends State<_AvatarCropScreen> {
  final _yakalama = GlobalKey();
  bool _mesgul = false;

  Future<void> _kaydet() async {
    setState(() => _mesgul = true);
    try {
      final sinir = _yakalama.currentContext!.findRenderObject()!
          as RenderRepaintBoundary;
      // Görünür kare ~300 lojik px; 512 piksel çıktı için oran.
      final resim = await sinir.toImage(
          pixelRatio: 512 / _kareKenari(context));
      final veri = await resim.toByteData(format: ui.ImageByteFormat.png);
      if (!mounted || veri == null) return;
      Navigator.of(context).pop(veri.buffer.asUint8List());
    } catch (_) {
      if (mounted) setState(() => _mesgul = false);
    }
  }

  double _kareKenari(BuildContext context) =>
      MediaQuery.sizeOf(context).width - 48;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final kenar = _kareKenari(context);

    return Scaffold(
      backgroundColor: RythoColors.ink,
      appBar: AppBar(title: Text(l10n.avatarEditTitle)),
      body: SafeArea(
        child: Column(children: [
          const Spacer(),
          // Yakalanan alan KARE; daire yalnız önizleme maskesi (avatar
          // zaten dairesel gösteriliyor — kare saklamak ileride farklı
          // biçimlere de izin verir).
          Stack(alignment: Alignment.center, children: [
            RepaintBoundary(
              key: _yakalama,
              child: SizedBox(
                width: kenar,
                height: kenar,
                child: ClipRect(
                  child: InteractiveViewer(
                    minScale: 1,
                    maxScale: 5,
                    boundaryMargin: EdgeInsets.all(kenar),
                    child: Image.memory(widget.imageBytes,
                        fit: BoxFit.cover, width: kenar, height: kenar),
                  ),
                ),
              ),
            ),
            // Dairesel maske: dokunuşları yutmasın.
            IgnorePointer(
              child: CustomPaint(
                size: Size(kenar, kenar),
                painter: _DaireMaskesi(),
              ),
            ),
          ]),
          const SizedBox(height: 16),
          Text(l10n.avatarEditHint,
              style: RythoText.body(12.5, color: RythoColors.parchmentDim)),
          const Spacer(),
          Padding(
            padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
            child: GoldButton(
                text: l10n.save,
                busy: _mesgul,
                onPressed: _mesgul ? null : _kaydet),
          ),
        ]),
      ),
    );
  }
}

/// Kare alanın dışını karartıp daire penceresi bırakan maske.
class _DaireMaskesi extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final dis = Path()
      ..addRect(Offset.zero & size)
      ..addOval(Rect.fromCircle(
          center: size.center(Offset.zero),
          radius: size.shortestSide / 2))
      ..fillType = PathFillType.evenOdd;
    canvas.drawPath(
        dis, Paint()..color = RythoColors.ink.withValues(alpha: 0.62));
    canvas.drawCircle(
        size.center(Offset.zero),
        size.shortestSide / 2,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.5
          ..color = RythoColors.goldBright.withValues(alpha: 0.6));
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
