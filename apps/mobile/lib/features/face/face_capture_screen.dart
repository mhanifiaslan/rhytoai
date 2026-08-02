/// Yüz okuma çekim ekranı — kılavuz, tespit ve sinematik tarama.
///
/// Akış: canlı önizleme → çerçeveleme kılavuzu → deklanşör yalnızca kadraj
/// hazırken etkin → çekim → tespit → tarama animasyonu → oranlar.
///
/// **Görüntü bu ekrandan çıkmaz.** Çekilen kare belleğe alınır, ML Kit ile
/// cihazda işlenir, oranlar çıkarılır ve kare atılır. Diske yazılmaz,
/// sunucuya gönderilmez.
library;

import 'dart:async';
import 'dart:io';
import 'dart:math' as math;

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';

import '../../l10n/app_localizations.dart';
import '../../theme/rytho_theme.dart';
import 'face_detection.dart';
import 'face_geometry.dart';
import 'face_scan_overlay.dart';

/// Çekim sonucunda dışarı verilen şey: yalnızca oranlar.
typedef FaceCaptureResult = FaceRatios;

class FaceCaptureScreen extends StatefulWidget {
  const FaceCaptureScreen({super.key});

  @override
  State<FaceCaptureScreen> createState() => _FaceCaptureScreenState();
}

enum _Asama { hazirlaniyor, izinYok, onizleme, tarama, hata }

class _FaceCaptureScreenState extends State<FaceCaptureScreen>
    with TickerProviderStateMixin {
  CameraController? _kamera;
  late final FaceDetector _dedektor = createFaceDetector();

  _Asama _asama = _Asama.hazirlaniyor;
  FrameQuality _kalite = FrameQuality.noFace;

  /// Kilit birikimi: yüz üst üste kaç karedir hazır konumda.
  ///
  /// Tek karelik "hazır" ile deklanşörü açmak, kullanıcı daha yerleşmeden
  /// tetikleniyor ve kadraj bulanık çıkıyordu. Kilidin dolması ~0.5 sn sürüyor.
  double _kilit = 0;

  /// Aynı anda iki kare işlemeyi engeller. ML Kit çağrısı ~30-80 ms;
  /// kilit olmadan kuyruk birikiyor ve önizleme donuyor.
  bool _isliyor = false;

  late final AnimationController _nabiz = AnimationController(
    vsync: this,
    duration: const Duration(seconds: 3),
  )..repeat();

  late final AnimationController _tarama = AnimationController(
    vsync: this,
    duration: ScanTiming.total,
  );

  List<Offset> _noktalar = const [];
  Size _goruntuBoyutu = Size.zero;

  @override
  void initState() {
    super.initState();
    _baslat();
  }

  Future<void> _baslat() async {
    try {
      final kameralar = await availableCameras();
      final on = kameralar.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.front,
        orElse: () => kameralar.first,
      );

      // Yüksek çözünürlük gerekmiyor: oranlar ölçek bağımsız ve düşük
      // çözünürlük hem tespiti hızlandırıyor hem telefonu ısıtmıyor.
      final kontrolcu = CameraController(
        on,
        ResolutionPreset.medium,
        enableAudio: false,
        imageFormatGroup: Platform.isAndroid
            ? ImageFormatGroup.nv21
            : ImageFormatGroup.bgra8888,
      );
      await kontrolcu.initialize();
      if (!mounted) return;

      _kamera = kontrolcu;
      await kontrolcu.startImageStream(_kareGeldi);
      if (!mounted) return;
      setState(() => _asama = _Asama.onizleme);
    } on CameraException catch (e) {
      if (!mounted) return;
      setState(() => _asama = e.code.contains('Permission')
          ? _Asama.izinYok
          : _Asama.hata);
    } catch (_) {
      if (!mounted) return;
      setState(() => _asama = _Asama.hata);
    }
  }

  Future<void> _kareGeldi(CameraImage kare) async {
    if (_isliyor || _asama != _Asama.onizleme) return;
    _isliyor = true;
    try {
      final kamera = _kamera;
      if (kamera == null) return;

      final girdi = inputImageFromCamera(
        image: kare,
        camera: kamera.description,
        deviceOrientationDegrees: 0,
      );
      if (girdi == null) return;

      final yuzler = await _dedektor.processImage(girdi);
      if (!mounted) return;

      final yuz = yuzler.isEmpty ? null : yuzler.first;
      final kalite = assessFrame(
        faceBox: yuz?.boundingBox,
        previewSize: Size(kare.width.toDouble(), kare.height.toDouble()),
        headAngleZ: yuz?.headEulerAngleZ ?? 0,
      );

      // Kilit birikimi: hazır kaldıkça dolar, bozulunca hızla boşalır.
      final yeniKilit = kalite == FrameQuality.ready
          ? (_kilit + 0.14).clamp(0.0, 1.0)
          : (_kilit - 0.35).clamp(0.0, 1.0);

      if (kalite != _kalite || (yeniKilit - _kilit).abs() > 0.01) {
        setState(() {
          _kalite = kalite;
          _kilit = yeniKilit;
        });
      }
    } catch (_) {
      // Tek bir bozuk kare akışı düşürmemeli; sonraki kare denenir.
    } finally {
      _isliyor = false;
    }
  }

  Future<void> _cek() async {
    final kamera = _kamera;
    if (kamera == null || _kilit < 1.0) return;

    HapticFeedback.mediumImpact();
    setState(() => _asama = _Asama.tarama);

    try {
      await kamera.stopImageStream();
      final dosya = await kamera.takePicture();

      final girdi = InputImage.fromFilePath(dosya.path);
      final yuzler = await _dedektor.processImage(girdi);

      // Kare artık gerekli değil: DISKTEN SIL. camera paketi geçici dosyaya
      // yazıyor; bırakılsa cihazda kalıcı bir yüz fotoğrafı birikirdi.
      unawaited(File(dosya.path).delete().catchError((_) => File(dosya.path)));

      if (!mounted) return;
      if (yuzler.isEmpty) {
        setState(() => _asama = _Asama.hata);
        return;
      }

      final yuz = yuzler.first;
      final lm = landmarksFromFace(yuz);
      if (lm == null) {
        setState(() => _asama = _Asama.hata);
        return;
      }

      setState(() {
        _noktalar = scanNodes(yuz);
        _goruntuBoyutu = Size(
          yuz.boundingBox.width * 3,
          yuz.boundingBox.height * 3,
        );
      });

      await _tarama.forward(from: 0);
      if (!mounted) return;

      Navigator.of(context).pop<FaceCaptureResult>(computeRatios(lm));
    } catch (_) {
      if (!mounted) return;
      setState(() => _asama = _Asama.hata);
    }
  }

  @override
  void dispose() {
    _nabiz.dispose();
    _tarama.dispose();
    _kamera?.dispose();
    _dedektor.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      backgroundColor: RythoColors.ink,
      body: Stack(
        fit: StackFit.expand,
        children: [
          if (_kamera?.value.isInitialized ?? false)
            _onizleme()
          else
            const ColoredBox(color: RythoColors.ink),
          if (_asama == _Asama.onizleme) _kilavuz(),
          if (_asama == _Asama.tarama) _taramaKatmani(),
          _ustBar(l10n),
          if (_asama == _Asama.onizleme) _altBar(l10n),
          if (_asama == _Asama.tarama) _taramaMetni(l10n),
          if (_asama == _Asama.izinYok || _asama == _Asama.hata)
            _hataKatmani(l10n),
        ],
      ),
    );
  }

  /// Önizleme `BoxFit.cover` ile ekranı kaplar; katmandaki nokta ölçekleme
  /// de aynı dönüşümü varsayıyor (bkz. FaceScanPainter._olcekle).
  Widget _onizleme() {
    final kamera = _kamera!;
    return FittedBox(
      fit: BoxFit.cover,
      child: SizedBox(
        width: kamera.value.previewSize?.height ?? 1,
        height: kamera.value.previewSize?.width ?? 1,
        child: CameraPreview(kamera),
      ),
    );
  }

  Widget _kilavuz() => AnimatedBuilder(
        animation: _nabiz,
        builder: (_, _) => CustomPaint(
          painter: FaceGuidePainter(
            quality: _kalite,
            pulse: _nabiz.value,
            lockProgress: _kilit,
          ),
        ),
      );

  Widget _taramaKatmani() => AnimatedBuilder(
        animation: _tarama,
        builder: (_, _) => CustomPaint(
          painter: FaceScanPainter(
            points: _noktalar,
            progress: _tarama.value,
            imageSize: _goruntuBoyutu,
          ),
        ),
      );

  Widget _ustBar(AppLocalizations l10n) => SafeArea(
        child: Align(
          alignment: Alignment.topLeft,
          child: IconButton(
            icon: const Icon(Icons.close_rounded, color: RythoColors.parchment),
            onPressed: () => Navigator.of(context).maybePop(),
          ),
        ),
      );

  Widget _altBar(AppLocalizations l10n) => SafeArea(
        child: Align(
          alignment: Alignment.bottomCenter,
          child: Padding(
            padding: const EdgeInsets.only(bottom: 36),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // Tek seferde TEK yönerge. "Ortala ve yaklaş ve başını
                // düzelt" üç ayrı iş demek; kimse okumuyor.
                AnimatedSwitcher(
                  duration: const Duration(milliseconds: 220),
                  child: Text(
                    _yonerge(l10n, _kalite),
                    key: ValueKey(_kalite),
                    style: const TextStyle(
                      color: RythoColors.parchment,
                      fontSize: 16,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
                const SizedBox(height: 22),
                _deklansor(),
              ],
            ),
          ),
        ),
      );

  /// Deklanşör yalnızca kilit dolduğunda etkin.
  ///
  /// Kapalıyken de görünür duruyor ve dolum halkası taşıyor: düğmenin niye
  /// çalışmadığı görünür olmalı, aksi halde uygulama bozuk sanılıyor.
  Widget _deklansor() {
    final hazir = _kilit >= 1.0;
    return Semantics(
      button: true,
      enabled: hazir,
      child: GestureDetector(
        onTap: hazir ? _cek : null,
        child: SizedBox(
          width: 78,
          height: 78,
          child: Stack(
            alignment: Alignment.center,
            children: [
              CircularProgressIndicator(
                value: _kilit,
                strokeWidth: 3,
                backgroundColor: RythoColors.line,
                valueColor: const AlwaysStoppedAnimation(ScanPalette.locked),
              ),
              AnimatedContainer(
                duration: const Duration(milliseconds: 180),
                width: hazir ? 58 : 48,
                height: hazir ? 58 : 48,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: hazir
                      ? RythoColors.parchment
                      : RythoColors.parchmentDim.withValues(alpha: 0.4),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _taramaMetni(AppLocalizations l10n) => SafeArea(
        child: Align(
          alignment: Alignment.bottomCenter,
          child: Padding(
            padding: const EdgeInsets.only(bottom: 56),
            child: AnimatedBuilder(
              animation: _tarama,
              builder: (_, _) {
                final t = _tarama.value;
                final metin = t < 0.42
                    ? l10n.faceScanning
                    : t < 0.85
                        ? l10n.faceScanNodes
                        : l10n.faceScanReading;
                return Text(
                  metin,
                  style: TextStyle(
                    color: RythoColors.parchment
                        .withValues(alpha: 0.6 + 0.4 * math.sin(t * math.pi)),
                    fontSize: 15,
                    letterSpacing: 1.2,
                  ),
                );
              },
            ),
          ),
        ),
      );

  Widget _hataKatmani(AppLocalizations l10n) => ColoredBox(
        color: RythoColors.ink,
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(28),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  _asama == _Asama.izinYok
                      ? l10n.faceCameraDenied
                      : l10n.faceDetectFailed,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                      color: RythoColors.parchment, fontSize: 16),
                ),
                const SizedBox(height: 20),
                if (_asama == _Asama.hata)
                  FilledButton(
                    onPressed: () {
                      setState(() {
                        _asama = _Asama.hazirlaniyor;
                        _kilit = 0;
                        _noktalar = const [];
                      });
                      _baslat();
                    },
                    child: Text(l10n.faceRetake),
                  ),
              ],
            ),
          ),
        ),
      );

  static String _yonerge(AppLocalizations l10n, FrameQuality q) => switch (q) {
        FrameQuality.noFace => l10n.faceGuideNoFace,
        FrameQuality.tooFar => l10n.faceGuideTooFar,
        FrameQuality.tooClose => l10n.faceGuideTooClose,
        FrameQuality.offCentre => l10n.faceGuideOffCentre,
        FrameQuality.tilted => l10n.faceGuideTilted,
        FrameQuality.ready => l10n.faceGuideReady,
      };
}
