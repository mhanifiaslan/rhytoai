// GECICI sonda: `flutter test` varlik paketini kuruyor mu?
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/widgets/cosmic_scaffold.dart';

void main() {
  testWidgets('Image.asset testte yuklenebiliyor', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: Builder(
        builder: (context) => MediaQuery(
          data: MediaQuery.of(context).copyWith(disableAnimations: true),
          child: CosmicScaffold(
            body: Center(
              child: Image.asset('assets/brand/rytho_logo_512.png',
                  width: 72, height: 72),
            ),
          ),
        ),
      ),
    ));
    await tester.pump();
    await tester.runAsync(() => Future<void>.delayed(
        const Duration(milliseconds: 300)));
    await tester.pump();
    expect(find.byType(Image), findsOneWidget);
  });
}
