import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/features/face/face_motion.dart';

/// Hareket ölçümü — sıcak–soğuk ekseninin tek dürüst kaynağı.
///
/// Testlerin çoğu ölçümün NE ÖLÇMEDİĞİNİ koruyor: rijit baş hareketi ifade
/// sayılmamalı, kısa örnek raporlanmamalı, aykırı kare sonucu uçurmamalı.
List<Offset> _yuz({double kayma = 0, double ifade = 0}) => [
      for (var i = 0; i < 12; i++)
        Offset(
          100 + i * 10.0 + kayma + (i.isEven ? ifade : -ifade),
          200 + (i % 4) * 12.0 + kayma,
        ),
    ];

void main() {
  group('temel ölçüm', () {
    test('hiç hareket yoksa hız sıfır', () {
      final t = MotionTracker();
      for (var i = 0; i < 40; i++) {
        t.addFrame(
          points: _yuz(),
          faceWidth: 120,
          timestampMs: i * 60,
          locked: false,
        );
      }
      expect(t.metrics.motionRate, closeTo(0, 1e-6));
      expect(t.metrics.confident, isTrue);
    });

    test('ifade hareketi ölçülür', () {
      final t = MotionTracker();
      for (var i = 0; i < 40; i++) {
        t.addFrame(
          points: _yuz(ifade: (i % 2) * 8.0),
          faceWidth: 120,
          timestampMs: i * 60,
          locked: false,
        );
      }
      expect(t.metrics.motionRate, greaterThan(0.3));
    });
  });

  group('rijit baş hareketi ifade SAYILMAZ', () {
    test('tüm yüz birlikte kayarsa hız sıfır kalır', () {
      // Kullanıcı başını çevirdiğinde TÜM noktalar kayıyor; bu ifade
      // hareketi değil. Merkez kayması düşülmezse bu test 0 dönmezdi.
      final t = MotionTracker();
      for (var i = 0; i < 40; i++) {
        t.addFrame(
          points: _yuz(kayma: i * 6.0),
          faceWidth: 120,
          timestampMs: i * 60,
          locked: false,
        );
      }
      expect(t.metrics.motionRate, closeTo(0, 1e-6));
    });
  });

  group('ölçek bağımsızlık', () {
    test('yüz genişliği değişince hız değişmez', () {
      double olc(double genislik, double olcek) {
        final t = MotionTracker();
        for (var i = 0; i < 40; i++) {
          t.addFrame(
            points: [
              for (final p in _yuz(ifade: (i % 2) * 8.0))
                Offset(p.dx * olcek, p.dy * olcek)
            ],
            faceWidth: genislik,
            timestampMs: i * 60,
            locked: false,
          );
        }
        return t.metrics.motionRate;
      }

      expect(olc(120, 1.0), closeTo(olc(240, 2.0), 1e-6));
    });
  });

  group('serbest ve kilitli evre ayrı', () {
    test('kilit evresi ayrı sayılır', () {
      final t = MotionTracker();
      for (var i = 0; i < 30; i++) {
        t.addFrame(
          points: _yuz(ifade: (i % 2) * 12.0),
          faceWidth: 120,
          timestampMs: i * 60,
          locked: false,
        );
      }
      for (var i = 30; i < 60; i++) {
        t.addFrame(
          points: _yuz(ifade: (i % 2) * 1.0),
          faceWidth: 120,
          timestampMs: i * 60,
          locked: true,
        );
      }
      final m = t.metrics;
      expect(m.motionRate, greaterThan(m.stillness),
          reason: 'serbest evre kilit evresinden hareketli olmali');
      expect(m.stillness, greaterThan(0));
    });
  });

  group('güven', () {
    test('kısa örnek güvenilir sayılmaz', () {
      final t = MotionTracker();
      for (var i = 0; i < 8; i++) {
        t.addFrame(
          points: _yuz(ifade: (i % 2) * 8.0),
          faceWidth: 120,
          timestampMs: i * 60,
          locked: false,
        );
      }
      expect(t.metrics.sampleSeconds, lessThan(kMinSampleSeconds));
      expect(t.metrics.confident, isFalse);
    });

    test('güvenilir değilse eğilim belirsiz', () {
      const az = MotionMetrics(
          motionRate: 0.9, stillness: 0.9, sampleSeconds: 0.4);
      expect(heatLean(az), HeatLean.unclear,
          reason: 'az veriyle olcum uydurmaktansa olcemedim demek dogru');
    });
  });

  group('aykırı kare sonucu uçurmaz', () {
    test('tek bir tespit sıçraması ortancayı bozmaz', () {
      final t = MotionTracker();
      for (var i = 0; i < 40; i++) {
        // 20. karede yüz aniden 400 piksel zıplıyor (tespit hatası)
        final ifade = i == 20 ? 400.0 : 0.0;
        t.addFrame(
          points: _yuz(ifade: ifade),
          faceWidth: 120,
          timestampMs: i * 60,
          locked: false,
        );
      }
      // Ortalama alsaydik bu deger uçardi; ortanca sabit kaliyor.
      expect(t.metrics.motionRate, lessThan(0.05));
    });

    test('bozuk zaman damgası kareyi eler', () {
      final t = MotionTracker();
      t.addFrame(points: _yuz(), faceWidth: 120, timestampMs: 0, locked: false);
      // Aynı zaman damgası (dt = 0) ve geriye giden saat
      t.addFrame(points: _yuz(ifade: 9), faceWidth: 120, timestampMs: 0, locked: false);
      t.addFrame(points: _yuz(ifade: 9), faceWidth: 120, timestampMs: -500, locked: false);
      expect(t.metrics.sampleSeconds, 0);
    });

    test('nokta sayısı değişirse kare atlanır', () {
      final t = MotionTracker();
      t.addFrame(points: _yuz(), faceWidth: 120, timestampMs: 0, locked: false);
      t.addFrame(
          points: _yuz().take(5).toList(),
          faceWidth: 120,
          timestampMs: 60,
          locked: false);
      expect(t.metrics.sampleSeconds, 0);
    });
  });

  group('sıcak–soğuk eğilimi', () {
    MotionMetrics m(double hiz) =>
        MotionMetrics(motionRate: hiz, stillness: 0, sampleSeconds: 3);

    test('hızlı hareket sıcak tarafa', () {
      expect(heatLean(m(0.30)), HeatLean.fast);
    });

    test('ağır hareket soğuk tarafa', () {
      expect(heatLean(m(0.03)), HeatLean.slow);
    });

    test('arada kalan ölçümde taraf seçilmez', () {
      // Esikler arasindaki bosluk BILEREK genis: arada kalan bir olcum icin
      // taraf secmektense hicbir sey sylememek dogru.
      expect(heatLean(m(0.12)), HeatLean.unclear);
    });

    test('hiç hareket ölçülmediyse belirsiz', () {
      expect(heatLean(m(0)), HeatLean.unclear);
    });
  });

  group('gizlilik', () {
    test('json yalnızca hız taşır, koordinat taşımaz', () {
      const m = MotionMetrics(
          motionRate: 0.234567, stillness: 0.0345, sampleSeconds: 3.2);
      final j = m.toJson();
      expect(j.keys, containsAll(['motionRate', 'stillness', 'motionSeconds']));
      expect(j.values.every((v) => v < 10), isTrue);
      // Uc ondaliga yuvarlanir; daha fazla hassasiyet okumayi iyilestirmez.
      for (final v in j.values) {
        expect((v * 1000) % 1, closeTo(0, 1e-9));
      }
    });
  });
}
