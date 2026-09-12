// Kapı bekçisi (TC-turu denetim bulgusu): 426/409 kapısı `_Gate`'in `home`
// alt ağacını değiştirir; üstte basılı bir rota (sohbet, yüz okuma, kehanet)
// varsa yeni ekran onun ALTINDA kalır ve "Bu cihazda kullan" düğmesine
// ulaşılamazdı. `GateRootGuard` kapı kapandığı an yığını köke indirir.
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart' show StateProvider;
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/core/app_config.dart' show mustForceUpdateProvider;
import 'package:rytho/core/device_session.dart';
import 'package:rytho/core/gate_guard.dart';

/// Zorunlu güncelleme kapısının test anahtarı; gerçek sağlayıcı açılış
/// okuması + PackageInfo ister.
final _zorla = StateProvider<bool>((_) => false);

const _kok = Key('kok');
const _basili = Key('basili');

class _Harness {
  _Harness() : key = GlobalKey<NavigatorState>();
  final GlobalKey<NavigatorState> key;
  late final ProviderContainer kap;

  Widget build() {
    kap = ProviderContainer(overrides: [
      mustForceUpdateProvider.overrideWith((ref) => ref.watch(_zorla)),
    ]);
    return UncontrolledProviderScope(
      container: kap,
      child: GateRootGuard(
        navigatorKey: key,
        child: MaterialApp(
          navigatorKey: key,
          home: const Scaffold(body: Text('kök', key: _kok)),
        ),
      ),
    );
  }

  Future<void> bas(WidgetTester tester) async {
    key.currentState!.push(MaterialPageRoute<void>(
        builder: (_) => const Scaffold(body: Text('basılı', key: _basili))));
    await tester.pumpAndSettle();
    expect(find.byKey(_basili), findsOneWidget);
    expect(find.byKey(_kok), findsNothing);
  }
}

void main() {
  testWidgets('409 kapısı kapanınca basılı rota iner, kök görünür',
      (tester) async {
    final h = _Harness();
    await tester.pumpWidget(h.build());
    await h.bas(tester);

    h.kap.read(deviceConflictProvider.notifier).state =
        DeviceConflict(platform: 'iOS', claimedAt: DateTime.utc(2026, 9, 12));
    await tester.pumpAndSettle();

    expect(find.byKey(_basili), findsNothing);
    expect(find.byKey(_kok), findsOneWidget);
  });

  testWidgets('426 kapısı kapanınca da iner', (tester) async {
    final h = _Harness();
    await tester.pumpWidget(h.build());
    await h.bas(tester);

    h.kap.read(_zorla.notifier).state = true;
    await tester.pumpAndSettle();

    expect(find.byKey(_basili), findsNothing);
    expect(find.byKey(_kok), findsOneWidget);
  });

  testWidgets('üstteki diyalog da iner (kapı ekranı hiçbir şeyin altında '
      'kalmaz)', (tester) async {
    final h = _Harness();
    await tester.pumpWidget(h.build());
    showDialog<void>(
        context: h.key.currentContext!,
        builder: (_) => const AlertDialog(content: Text('diyalog')));
    await tester.pumpAndSettle();
    expect(find.text('diyalog'), findsOneWidget);

    h.kap.read(deviceConflictProvider.notifier).state = const DeviceConflict();
    await tester.pumpAndSettle();

    expect(find.text('diyalog'), findsNothing);
    expect(find.byKey(_kok), findsOneWidget);
  });

  testWidgets('yalnız KAPANIŞ kenarı: kapı zaten kapalıyken bayrağın '
      'yeniden yazılması yığına dokunmaz', (tester) async {
    final h = _Harness();
    await tester.pumpWidget(h.build());
    h.kap.read(deviceConflictProvider.notifier).state =
        const DeviceConflict(platform: 'android');
    await tester.pumpAndSettle();
    await h.bas(tester);

    // Uçuştaki ikinci 409'un başka bir başlıkla yazılması gibi.
    h.kap.read(deviceConflictProvider.notifier).state =
        const DeviceConflict(platform: 'iOS');
    await tester.pumpAndSettle();

    expect(find.byKey(_basili), findsOneWidget);
  });

  testWidgets('basılı rota yokken kapanış zararsız', (tester) async {
    final h = _Harness();
    await tester.pumpWidget(h.build());

    h.kap.read(deviceConflictProvider.notifier).state = const DeviceConflict();
    await tester.pumpAndSettle();

    expect(find.byKey(_kok), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('kapı açılınca (devralma başarılı) yığına dokunulmaz',
      (tester) async {
    final h = _Harness();
    await tester.pumpWidget(h.build());
    h.kap.read(deviceConflictProvider.notifier).state = const DeviceConflict();
    await tester.pumpAndSettle();
    h.kap.read(deviceConflictProvider.notifier).state = null;
    await tester.pumpAndSettle();
    await h.bas(tester);

    // Açılışın kendisi hiçbir şeyi indirmemeli; rota durur.
    expect(find.byKey(_basili), findsOneWidget);
  });
}
