// Seri sayacının İngilizce çoğulu (mağaza bulgusu).
//
// `streakDays` İngilizce ARB'de düz `{count} days`ti ve yayına hazır mağaza
// karesinde (store/play/shot-4-circle.png) kullanıcı adı rozetinde
// "🔥 1 days" yazıyordu. Aynı hata uygulamanın İLK gününde de çıkıyor.
// Türkçede çoğul eki olmadığı için TR tarafında görünmüyor — bekçi bu
// yüzden İngilizceyi sınıyor, Türkçe yalnızca gerilemeye karşı duruyor.
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/l10n/app_localizations_en.dart';
import 'package:rytho/l10n/app_localizations_tr.dart';

void main() {
  test('İngilizce: bir gün TEKİL', () {
    final en = AppLocalizationsEn();
    expect(en.streakDays(1), '1 day');
    expect(en.streakDays(0), '0 days');
    expect(en.streakDays(2), '2 days');
    expect(en.streakDays(37), '37 days');
  });

  test('Türkçe: sayı ne olursa olsun ek yok', () {
    final tr = AppLocalizationsTr();
    expect(tr.streakDays(1), '1 gün');
    expect(tr.streakDays(2), '2 gün');
    expect(tr.streakDays(37), '37 gün');
  });
}
