import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rytho/core/api.dart';
import 'package:rytho/l10n/app_localizations_tr.dart';

/// Sunucu hatasinin kullaniciya nasil gorundugu.
///
/// Cihaz testinde riza ekraninda kirmizi bir **"Not Found"** yazisi cikti.
/// Sebep: `friendlyError` sunucunun `detail` alanina kosulsuz guveniyordu.
/// Bizim uclarimiz `detail`'i kullanicinin dilinde uretiyor ama YONLENDIRME
/// duzeyindeki hatalari (var olmayan uc, yanlis metot) FastAPI kendi uretiyor
/// ve onlar Ingilizce cerceve sabitleri.

DioException _hata({int? kod, dynamic govde, DioExceptionType? tur}) {
  final istek = RequestOptions(path: '/api/v1/face/consent');
  return DioException(
    requestOptions: istek,
    type: tur ?? DioExceptionType.badResponse,
    response: kod == null
        ? null
        : Response(requestOptions: istek, statusCode: kod, data: govde),
  );
}

/// Türkçe arayüz: aşağıdaki metin beklentileri bu dile göre yazıldı.
/// `friendlyError` artık l10n'i ZORUNLU alıyor — opsiyonelken sekiz çağrı
/// yeri onu geçmiyor ve İngilizce cihaza Türkçe metin düşüyordu.
final _tr = AppLocalizationsTr();

void main() {
  test('cerceveden gelen "Not Found" kullaniciya GOSTERILMEZ', () {
    final mesaj = friendlyError(
        _hata(kod: 404, govde: {'detail': 'Not Found'}), _tr);

    expect(mesaj, isNot(contains('Not Found')),
        reason: 'cerceve sabiti kullaniciya oldugu gibi cikmamali');
    expect(mesaj, contains('Beklenmeyen'));
  });

  test('cerceveden gelen "Method Not Allowed" da gosterilmez', () {
    final mesaj = friendlyError(
        _hata(kod: 405, govde: {'detail': 'Method Not Allowed'}), _tr);
    expect(mesaj, isNot(contains('Method Not Allowed')));
  });

  test('KENDI urettigimiz detail oldugu gibi gosterilir', () {
    // Kendi 404'lerimiz de var (ornegin hexagram bulunamadi) ve onlar
    // `text()` ile yerellestiriliyor; onlari elemek dogru olmaz.
    const bizim = 'Bu hexagram bulunamadi.';
    expect(friendlyError(_hata(kod: 404, govde: {'detail': bizim}), _tr), bizim);
  });

  test('paywall detail\'i korunur', () {
    const paywall = 'Bu ozellik Rytho+ aboneligine dahildir.';
    expect(
        friendlyError(_hata(kod: 402, govde: {'detail': paywall}), _tr),
        paywall);
  });

  test('baglanti hatasi ayri mesaj verir', () {
    final mesaj =
        friendlyError(_hata(tur: DioExceptionType.connectionError), _tr);
    expect(mesaj, contains('Bağlantı'));
  });

  test('Dio disi hatalar genel mesaja duser', () {
    expect(friendlyError(StateError('bir sey'), _tr), contains('Beklenmeyen'));
  });
}
