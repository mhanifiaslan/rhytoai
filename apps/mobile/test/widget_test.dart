import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/theme/rytho_theme.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test('tema kurulabiliyor', () {
    final theme = buildRythoTheme();
    expect(theme.scaffoldBackgroundColor, RythoColors.ink);
  });
}
