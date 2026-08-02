/// Biyometrik işleme rızasının durumu ve yönetimi.
///
/// Rıza **bir kez** alınır, sunucuda saklanır ve profilden geri alınabilir.
///
/// İlk sürümde her çekimde soruluyordu; bu fazla temkinliydi ve iki şeyi
/// karıştırıyordu: rızanın **geri alınabilir** olması gerekiyor, her
/// seferinde yeniden sorulması değil.
///
/// Öbür uçtaki hata da geçerli değil: rızayı üyelik sözleşmesine ya da
/// gizlilik metnine gömmek işe yaramaz. Biyometrik veri özel nitelikli
/// (GDPR Md.9 / KVKK md.6) ve rızanın **ayrı, açık ve başka şartlarla
/// paketlenmemiş** olması gerekiyor.
///
/// Rıza istemcide DEĞİL sunucuda tutuluyor: ispat yükü bizde ve cihaz
/// hafızasındaki bir bayrak denetimde hiçbir şey ifade etmez. Ayrıca uç de
/// aynı kaydı kontrol ediyor, yani arayüzü atlamak işlemeyi açmıyor.
library;

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api.dart';

class FaceConsent {
  const FaceConsent({required this.granted, required this.version});

  final bool granted;

  /// Rıza metni sürümü. İşlenen veri ya da işleme biçimi değişirse sunucuda
  /// artıyor ve eski rıza geçersiz sayılıyor — "bir kez alıp ömür boyu
  /// kullanma" sorunu buradan çözülüyor.
  final int version;

  static const unknown = FaceConsent(granted: false, version: 0);
}

/// Sunucudaki rıza durumu.
final faceConsentProvider = FutureProvider<FaceConsent>((ref) async {
  final dio = ref.watch(apiProvider);
  try {
    final yanit = await dio.get<Map<String, dynamic>>('/api/v1/face/consent');
    return FaceConsent(
      granted: yanit.data?['granted'] == true,
      version: (yanit.data?['version'] as num?)?.toInt() ?? 0,
    );
  } on DioException {
    // Okunamadıysa rıza YOK varsayılır. "Vardır" varsaymak, biyometrik
    // işlemeyi rızasız açmak olurdu; hata durumunda güvenli taraf bu.
    return FaceConsent.unknown;
  }
});

Future<void> grantFaceConsent(Dio dio) =>
    dio.post('/api/v1/face/consent');

/// Rızayı geri alır. Sunucu aynı çağrıda üretilmiş okumaları da siliyor.
Future<int> withdrawFaceConsent(Dio dio) async {
  final yanit = await dio.delete<Map<String, dynamic>>('/api/v1/face/consent');
  return (yanit.data?['deletedReadings'] as num?)?.toInt() ?? 0;
}
