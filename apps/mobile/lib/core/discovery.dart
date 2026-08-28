/// Günlük keşif halkası (OB4) — cihaz-yerel, hafif oyunlaştırma.
///
/// Kullanıcı isteği: "modern oyunlaştırma mekanikleri ile kullanıcı
/// merakını ve sadakatini arttırmalıyız." Kullanıcı kararı (OB-turu):
/// v1 yalnız GÜNLÜK KEŞİF HALKASI — rozet/XP/seviye yok.
///
/// Üç günlük görev, üç halka dilimi:
///   * [DiscoveryTask.daily]  — günün gökyüzünü açtı (seri dokunuşu),
///   * [DiscoveryTask.chat]   — Rytho ile konuştu (başarılı gönderim),
///   * [DiscoveryTask.circle] — çevresinden birine baktı (ilişki/kişi/
///     arkadaş detayı).
///
/// TAMAMEN CİHAZ-YEREL: SharedPreferences, sıfır Firestore/sunucu —
/// bu bir ölçüm değil, günlük ritüelin görsel hatırlatıcısı. Cihaz
/// değişince sıfırlanması kabul edilmiş sınırdır (plan: kapsam dışı).
library;

import 'package:flutter_riverpod/legacy.dart' show StateNotifier, StateNotifierProvider;
import 'package:intl/intl.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Günlük görevler. `index` bit konumudur — sıra DEĞİŞTİRİLEMEZ
/// (kayıtlı maskeler anlamını yitirir).
enum DiscoveryTask { daily, chat, circle }

/// Tüm görevler işaretli maske: 0b111.
const int kDiscoveryAllMask = 0x7;

/// Kayıt anahtarları. Durum "yyyy-MM-dd:mask" biçiminde tek dizedir;
/// gün değişince maske kendiliğinden sıfırdan başlar. Kutlama günü ayrı
/// anahtarda tutulur ki 3/3 kutlaması uygulama yeniden başlatılınca
/// TEKRARLAMASIN (günde bir).
const String kDiscoveryStateKey = 'discovery-state';
const String kDiscoveryCelebratedKey = 'discovery-celebrated';

/// Günün keşif durumu.
class DiscoveryState {
  const DiscoveryState(
      {required this.day, required this.mask, this.justCompleted = false});

  /// Yerel gün (yyyy-MM-dd).
  final String day;

  /// Tamamlanan görevlerin bit maskesi.
  final int mask;

  /// Bu güncellemeyle 3/3 tamamlandı ve BUGÜN daha önce kutlanmadı —
  /// UI bir kez kutlar (StarBurst + ses + snackbar) ve [DiscoveryNotifier
  /// .ackCelebration] çağırır.
  final bool justCompleted;

  bool contains(DiscoveryTask task) => (mask & (1 << task.index)) != 0;

  /// Tamamlanan görev sayısı (0-3).
  int get done => DiscoveryTask.values.where(contains).length;

  bool get complete => mask == kDiscoveryAllMask;
}

/// Kayıtlı "yyyy-MM-dd:mask" değerini bugünün maskesine çözer; gün
/// farklıysa ya da biçim bozuksa 0. SAF — test edilebilir.
int discoveryMaskFor(String? stored, String today) {
  if (stored == null) return 0;
  final ayrim = stored.lastIndexOf(':');
  if (ayrim <= 0) return 0;
  if (stored.substring(0, ayrim) != today) return 0;
  final mask = int.tryParse(stored.substring(ayrim + 1)) ?? 0;
  return mask & kDiscoveryAllMask;
}

class DiscoveryNotifier extends StateNotifier<DiscoveryState> {
  DiscoveryNotifier({DateTime Function()? clock})
      : _clock = clock ?? DateTime.now,
        super(const DiscoveryState(day: '', mask: 0)) {
    _load();
  }

  final DateTime Function() _clock;

  String get _today => DateFormat('yyyy-MM-dd').format(_clock());

  Future<void> _load() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final gun = _today;
      final mask = discoveryMaskFor(prefs.getString(kDiscoveryStateKey), gun);
      if (mounted) state = DiscoveryState(day: gun, mask: mask);
    } catch (_) {
      // Prefs okunamazsa halka boş çizilir; işlev kaybı yok.
    }
  }

  /// Görevi işaretler — idempotent: aynı görev günde bir kez sayılır,
  /// tekrar çağrılar sessizdir. Gün değiştiyse maske sıfırdan başlar.
  Future<void> mark(DiscoveryTask task) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final gun = _today;
      var mask = discoveryMaskFor(prefs.getString(kDiscoveryStateKey), gun);
      final bit = 1 << task.index;
      if (mask & bit != 0) {
        // Zaten işaretli; yalnız gün devri görünür olsun.
        if (mounted && (state.day != gun || state.mask != mask)) {
          state = DiscoveryState(day: gun, mask: mask);
        }
        return;
      }
      mask |= bit;
      await prefs.setString(kDiscoveryStateKey, '$gun:$mask');

      var kutla = false;
      if (mask == kDiscoveryAllMask &&
          prefs.getString(kDiscoveryCelebratedKey) != gun) {
        await prefs.setString(kDiscoveryCelebratedKey, gun);
        kutla = true;
      }
      if (mounted) {
        state = DiscoveryState(day: gun, mask: mask, justCompleted: kutla);
      }
    } catch (_) {}
  }

  /// UI kutlamayı gösterdikten sonra bayrağı düşürür.
  void ackCelebration() {
    if (state.justCompleted) {
      state = DiscoveryState(day: state.day, mask: state.mask);
    }
  }
}

final discoveryProvider =
    StateNotifierProvider<DiscoveryNotifier, DiscoveryState>(
        (ref) => DiscoveryNotifier());
