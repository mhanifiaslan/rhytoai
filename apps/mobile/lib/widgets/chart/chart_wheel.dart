/// Etkileşimli çark (HI-turu HA6) — NatalWheel'in varisi.
///
/// Jest ve çizim AYNI [WheelLayout] nesnesini tüketir: dokunduğun şey
/// çizilen şeydir (eski çarkın "Venüs'e dokun, Merkür açılsın" kusuru
/// sınıf olarak öldü). Pinch-zoom kendi durumumuzla yapılır —
/// InteractiveViewer BİLEREK yok: raster katmanı büyüttüğü için metin
/// 4x'te bulanıyor (bilinen #88467 ölçek sıçraması da cabası); burada
/// zoom "geometriyi büyüt" demek, metin her ölçekte NET kalır.
///
/// Serbest DÖNDÜRME yok: Asc-solda konvansiyonu çarkı okunur kılan
/// şeydir; hiçbir profesyonel yazılım döndürmez.
library;

import 'dart:ui' as ui;

import 'package:flutter/material.dart';

import '../../l10n/app_localizations.dart';
import '../motion.dart';
import 'chart_data.dart';
import 'wheel_layout.dart';
import 'wheel_painter.dart';

class ChartWheel extends StatefulWidget {
  const ChartWheel({
    super.key,
    required this.data,
    required this.size,
    this.onPlanetTap,
    this.onAspectTap,
    this.filter = WheelAspectFilter.all,
    this.maxOrb = 8.0,
    this.showMinors = false,
    this.selection = WheelSelection.none,
    this.interactive = true,
    this.animate = true,
  });

  final ChartData data;
  final double size;

  final void Function(GlyphPlacement placement)? onPlanetTap;
  final void Function(ChartAspect aspect)? onAspectTap;

  final WheelAspectFilter filter;
  final double maxOrb;
  final bool showMinors;
  final WheelSelection selection;

  /// false: gömülü küçük çark (zoom/pan kapalı, dokunma açık kalır).
  final bool interactive;

  /// false: dışa aktarım/kayıt kipi — süpürme animasyonu YOK, ilk kare
  /// TAM çizilir (renderCard progress≈0'da boş kare yakalıyordu).
  final bool animate;

  @override
  State<ChartWheel> createState() => _ChartWheelState();
}

class _ChartWheelState extends State<ChartWheel>
    with SingleTickerProviderStateMixin {
  late final AnimationController _sweep = AnimationController(
      vsync: this, duration: const Duration(milliseconds: 1400));

  double _zoom = 1.0;
  Offset _pan = Offset.zero;
  double _zoomBasi = 1.0;

  WheelLayout? _layout;
  ui.Picture? _static;
  final _textCache = GlyphTextCache();
  Object? _layoutKey;

  @override
  void initState() {
    super.initState();
    if (widget.animate) {
      _sweep.forward();
    } else {
      _sweep.value = 1.0;
    }
  }

  @override
  void dispose() {
    _sweep.dispose();
    _static = null;
    super.dispose();
  }

  /// Geometri yalnız (veri, boyut, zoom) değişince yeniden hesaplanır;
  /// statik katman da onunla birlikte kaydedilir.
  WheelLayout _ensureLayout() {
    final key = (widget.data, widget.size, _zoom);
    if (_layout == null || _layoutKey != key) {
      _layoutKey = key;
      _layout = WheelLayout.compute(
          Size.square(widget.size * _zoom), widget.data,
          zoom: _zoom);
      _static = recordStaticLayer(_layout!, _textCache);
    }
    return _layout!;
  }

  Offset _toScene(Offset local) => local - _pan;

  void _onTapUp(TapUpDetails d) {
    final hit = _ensureLayout().hitTest(_toScene(d.localPosition));
    if (hit == null) return;
    if (hit.placement != null) {
      widget.onPlanetTap?.call(hit.placement!);
    } else if (hit.segment != null) {
      widget.onAspectTap?.call(hit.segment!.aspect);
    }
  }

  void _onScaleStart(ScaleStartDetails d) {
    _zoomBasi = _zoom;
  }

  void _onScaleUpdate(ScaleUpdateDetails d) {
    if (!widget.interactive) return;
    setState(() {
      final yeniZoom = (_zoomBasi * d.scale).clamp(1.0, 4.0);
      if (yeniZoom != _zoom) {
        // Odak sabit kalsın: parmakların ortasındaki nokta zoom sonrası
        // da aynı yerel konuma düşer.
        final odak = d.localFocalPoint;
        _pan = odak - (odak - _pan) * (yeniZoom / _zoom);
        _zoom = yeniZoom;
      }
      _pan = _clampPan(_pan + d.focalPointDelta);
    });
  }

  Offset _clampPan(Offset p) {
    final tasma = widget.size * (_zoom - 1);
    return Offset(p.dx.clamp(-tasma, 0.0), p.dy.clamp(-tasma, 0.0));
  }

  void _resetZoom() {
    if (!widget.interactive) return;
    setState(() {
      _zoom = 1.0;
      _pan = Offset.zero;
    });
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final hareketsiz = reduceMotion(context);
    if (hareketsiz && _sweep.value < 1.0) _sweep.value = 1.0;

    final layout = _ensureLayout();

    return Semantics(
      label: l10n.chartWheelSemantics(
          layout.data.rings.length, layout.data.aspects.length),
      child: ExcludeSemantics(
        child: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTapUp: _onTapUp,
          onDoubleTap: _resetZoom,
          onScaleStart: widget.interactive ? _onScaleStart : null,
          onScaleUpdate: widget.interactive ? _onScaleUpdate : null,
          child: ClipRect(
            child: SizedBox(
              width: widget.size,
              height: widget.size,
              child: AnimatedBuilder(
                animation: _sweep,
                builder: (_, _) => CustomPaint(
                  size: Size.square(widget.size),
                  painter: _PannedPainter(
                    pan: _pan,
                    inner: RythoWheelPainter(
                      layout: layout,
                      staticLayer: _static!,
                      textCache: _textCache,
                      progress: hareketsiz
                          ? 1.0
                          : Curves.easeOutCubic.transform(_sweep.value),
                      filter: widget.filter,
                      maxOrb: widget.maxOrb,
                      showMinors: widget.showMinors,
                      selection: widget.selection,
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Pan kaydırmasını uygular; isabet testi [_ChartWheelState._toScene] ile
/// AYNI dönüşümü kullanır — çizim ve dokunma yine tek kaynaktan.
class _PannedPainter extends CustomPainter {
  _PannedPainter({required this.pan, required this.inner});

  final Offset pan;
  final RythoWheelPainter inner;

  @override
  void paint(Canvas canvas, Size size) {
    canvas.save();
    canvas.translate(pan.dx, pan.dy);
    inner.paint(canvas, size);
    canvas.restore();
  }

  @override
  bool shouldRepaint(_PannedPainter old) =>
      old.pan != pan || old.inner.shouldRepaint(inner);
}
