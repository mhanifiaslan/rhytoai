/// Firaset okuması için sunucu çağrısı.
///
/// Gönderilen tek şey **oranlardır**. Bu dosyada `File`, `bytes`, `image`
/// ya da `MultipartFile` geçmemesi kasıtlı: yüz görüntüsünün ağa çıkmadığını
/// koda bakarak doğrulayabilmek gerekiyor.
library;

import 'package:dio/dio.dart';

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
  return (yanit.data?['reading'] as String?)?.trim() ?? '';
}
