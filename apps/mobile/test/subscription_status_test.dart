// Deneme dönemi durum sözleşmesi (OT6).
//
// Sunucu /billing/status'ta denemeyi `active=true` + `trial_days_left`
// ile bildirir; istemci TARİH HESABI YAPMAZ (kural tek yerde, sunucuda).
// Bu sayede tüm kilitler (subscriptionProvider'ı okuyan her ekran)
// deneme boyunca kendiliğinden açılır.
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/core/subscription.dart';

void main() {
  test('trial_days_left ayrıştırılır', () {
    final durum = SubscriptionStatus.fromJson({
      'active': true,
      'is_trial': true,
      'trial_days_left': 2,
    });
    expect(durum.active, isTrue); // kilitler deneme boyunca açık
    expect(durum.isTrial, isTrue);
    expect(durum.trialDaysLeft, 2);
  });

  test('deneme yokken alan null — paywall bandı çizilmez', () {
    final durum = SubscriptionStatus.fromJson({'active': false});
    expect(durum.trialDaysLeft, isNull);
    expect(SubscriptionStatus.none.trialDaysLeft, isNull);
  });
}
