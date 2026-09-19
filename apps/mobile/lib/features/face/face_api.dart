/// Firaset okuması için sunucu çağrısı.
///
/// Gönderilen tek şey **oranlardır**. Bu dosyada `File`, `bytes`, `image`
/// ya da `MultipartFile` geçmemesi kasıtlı: yüz görüntüsünün ağa çıkmadığını
/// koda bakarak doğrulayabilmek gerekiyor.
library;

import 'package:dio/dio.dart';

import '../../core/api.dart' show RaporUretilemedi;
import 'face_capture_screen.dart';

/// Ölçümleri uca gönderir ve okumayı döndürür.
///
/// Hata yönetimi çağırana bırakılıyor: uygulamanın ortak `describeApiError`
/// katmanı 402'yi paywall'a çeviriyor ve firasetin de o yoldan geçmesi
/// gerekiyor (özellik Rytho+ kapsamında).
Future<String> fetchFirasaReading(Dio dio, FaceCaptureResult sonuc) async {
  final yanit = await dio.post<Map<String, dynamic>>(
    '/api/v1/face/reading',
    data: sonuc.toJson(),
  );
  // Yedek metin firaset okumasi SAYILMAZ (gz-2): uc cumlelik hazir paragrafi
  // okuma gibi gostermek, jetonun iade edildigini de saklamak olurdu.
  if (yanit.data?['fallback'] == true) {
    throw RaporUretilemedi(jetonIadeEdildi: yanit.data?['refunded'] == true);
  }
  return (yanit.data?['reading'] as String?)?.trim() ?? '';
}
