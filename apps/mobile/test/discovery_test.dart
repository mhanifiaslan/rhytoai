// Günlük keşif halkası bekçileri (OB4).
//
// Üç değişmez: gün devri maskeyi sıfırlar; işaretleme idempotenttir ve
// kalıcıdır; 3/3 kutlaması GÜNDE BİR kez tetiklenir (uygulama yeniden
// başlatılınca tekrarlamaz — bayrak SharedPreferences'ta).
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/core/discovery.dart';
import 'package:shared_preferences/shared_preferences.dart';

DateTime _gun1() => DateTime(2026, 8, 27, 14);
DateTime _gun2() => DateTime(2026, 8, 28, 9);

Future<void> _bekle() async {
  // Notifier'ın async _load/mark zinciri mikro görevlerde biter.
  await Future<void>.delayed(Duration.zero);
  await Future<void>.delayed(Duration.zero);
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('discoveryMaskFor: gün eşleşmesi ve bozuk biçim', () {
    expect(discoveryMaskFor('2026-08-27:5', '2026-08-27'), 5);
    expect(discoveryMaskFor('2026-08-26:5', '2026-08-27'), 0); // dün
    expect(discoveryMaskFor(null, '2026-08-27'), 0);
    expect(discoveryMaskFor('çöp', '2026-08-27'), 0);
    expect(discoveryMaskFor('2026-08-27:çöp', '2026-08-27'), 0);
    // Maske 3 bitle sınırlı — bozuk büyük değer taşmaz.
    expect(discoveryMaskFor('2026-08-27:255', '2026-08-27'),
        kDiscoveryAllMask);
  });

  test('işaretleme kalıcı ve idempotent', () async {
    SharedPreferences.setMockInitialValues({});
    final n = DiscoveryNotifier(clock: _gun1);
    await _bekle();

    await n.mark(DiscoveryTask.daily);
    await n.mark(DiscoveryTask.daily); // ikinci çağrı sessiz
    expect(n.state.contains(DiscoveryTask.daily), isTrue);
    expect(n.state.done, 1);
    expect(n.state.justCompleted, isFalse);

    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getString(kDiscoveryStateKey), '2026-08-27:1');

    // Yeniden başlatma: yeni notifier aynı günü okur.
    final n2 = DiscoveryNotifier(clock: _gun1);
    await _bekle();
    expect(n2.state.mask, 1);
  });

  test('gün devri maskeyi sıfırlar', () async {
    SharedPreferences.setMockInitialValues(
        {kDiscoveryStateKey: '2026-08-27:7'});
    final n = DiscoveryNotifier(clock: _gun2);
    await _bekle();
    expect(n.state.mask, 0); // dünün 3/3'ü bugüne taşınmaz

    await n.mark(DiscoveryTask.chat);
    expect(n.state.mask, 2);
    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getString(kDiscoveryStateKey), '2026-08-28:2');
  });

  test('3/3 kutlaması günde bir kez', () async {
    SharedPreferences.setMockInitialValues({});
    final n = DiscoveryNotifier(clock: _gun1);
    await _bekle();

    await n.mark(DiscoveryTask.daily);
    await n.mark(DiscoveryTask.chat);
    expect(n.state.justCompleted, isFalse);
    await n.mark(DiscoveryTask.circle);
    expect(n.state.complete, isTrue);
    expect(n.state.justCompleted, isTrue); // tam bu güncellemeyle

    n.ackCelebration();
    expect(n.state.justCompleted, isFalse);

    // Uygulama yeniden başlar: maske dolu, kutlama BAYRAKLI — tekrarlamaz.
    final n2 = DiscoveryNotifier(clock: _gun1);
    await _bekle();
    expect(n2.state.complete, isTrue);
    expect(n2.state.justCompleted, isFalse);
    await n2.mark(DiscoveryTask.circle);
    expect(n2.state.justCompleted, isFalse);
  });
}
