import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Küçük, yumuşak UI sesleri — tools/generate_sounds.py ile sentezlenen
/// WAV'lar (assets/sounds/). Ses seviyesi düşük tutulur; Profil'deki
/// "Sesler" anahtarıyla kapatılabilir (shared_preferences, varsayılan açık).
class SoundFx {
  SoundFx._();

  static const _prefKey = 'soundsEnabled';
  static bool _enabled = true;
  static bool _loaded = false;

  static bool get enabled => _enabled;

  static Future<void> _ensureLoaded() async {
    if (_loaded) return;
    _loaded = true;
    try {
      final prefs = await SharedPreferences.getInstance();
      _enabled = prefs.getBool(_prefKey) ?? true;
    } catch (_) {}
  }

  static Future<void> setEnabled(bool value) async {
    _enabled = value;
    _loaded = true;
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool(_prefKey, value);
    } catch (_) {}
  }

  /// Senkron okuma için başlangıçta çağrılabilir.
  static Future<bool> loadEnabled() async {
    await _ensureLoaded();
    return _enabled;
  }

  static Future<void> _play(String asset, double volume) async {
    await _ensureLoaded();
    if (!_enabled) return;
    try {
      // Her çalış için kısa ömürlü oyuncu: üst üste binen sesler kesilmez.
      final player = AudioPlayer();
      player.onPlayerComplete.listen((_) => player.dispose());
      await player.play(AssetSource('sounds/$asset'), volume: volume);
    } catch (e) {
      debugPrint('SoundFx çalınamadı ($asset): $e');
    }
  }

  /// Mesaj gönderildi — kısa yumuşak "pop".
  static Future<void> send() => _play('message_send.wav', 0.4);

  /// Yeni mesaj geldi — iki tonlu nazik "ding".
  static Future<void> receive() => _play('message_receive.wav', 0.4);

  /// I Ching çekimi — mistik kısa "chime".
  static Future<void> cast() => _play('cast.wav', 0.45);

  /// Beğeni — çok kısa "tick".
  static Future<void> like() => _play('like.wav', 0.3);
}
