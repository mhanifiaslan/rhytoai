"""Google kimlik bilgisinin (ADC) çözülüp çözülmediğini arka planda yoklar.

Bu modül **üretimi kırdı ve o yüzden yeniden yazıldı.** Ne olduğu burada
yazılı duruyor, çünkü aynı hatayı tekrar yapmak çok kolay.

İlk sürüm şunu yapıyordu: kimlik bilgisini 3 saniyelik bir sınırla yokla,
sonuçlanmazsa "kimlik yok" say. Yerelde doğru çalıştı. Cloud Run'da soğuk
başlatma sırasında meta veri sunucusu 3 saniyeyi aştı ve sonuç şu oldu:

    11:37:33  ADC yoklaması 3.0 sn içinde sonuçlanmadı.
    11:38:02  Kimlik bilgisi yok; Firestore devre dışı.   -> webhook 500
    11:38:11  ADC çözülemedi. Tüm istekler 401 dönecek.

Abonelik webhook'ları düştü, kullanıcı ödeme yaptı ve ekranlar kilitli kaldı.

Hata tek bir cümlede: **"yoklama bitmedi" ile "kimlik yok" aynı şey sayıldı.**
Biri sonuçsuz, öteki olumsuz. Bu yüzden buradaki üç kural pazarlığa kapalı:

1. **Yoklama istek yolunu ASLA bloklamaz.** Tamamen arka planda çalışır;
   `available()` beklemez.
2. **Sonuç yoksa ERİŞİLEBİLİR varsayılır (fail-open).** Bilmemek, yokluk
   değildir. Üretimin çalışması, geliştirme ortamının hızından önce gelir.
3. **Yalnızca kesin olumsuz sonuç** (`google.auth.default()` hata fırlattı)
   erişimi kapatır — o da süreli.

Modülün varlık sebebi hâlâ geçerli: ADC bulunmayan bir makinede
`google.auth.default()` ölçülen 11,98 saniye sürüyor ve hem `core.auth` hem
`core.firestore` bunu ayrı ayrı çağırıyordu. Yoklama açılışta bir kez yapılıp
sonucu paylaşılıyor.
"""
from __future__ import annotations

import logging
import threading
import time

logger = logging.getLogger(__name__)

#: Olumsuz sonucun ömrü. Geçici bir sorun kimlik doğrulamayı süreç boyunca
#: kapatmasın diye süreli.
NEGATIVE_TTL_SECONDS = 60.0

_lock = threading.Lock()

#: None = yoklama henüz sonuçlanmadı. True/False = kesin sonuç.
_durum: bool | None = None
_gecersizlesme = 0.0
_calisiyor = False


def _yokla() -> None:
    """ADC'yi çöz ve sonucu kaydet. Arka planda koşar; kimseyi bekletmez."""
    global _durum, _gecersizlesme, _calisiyor
    sonuc = False
    try:
        import google.auth

        google.auth.default()
        sonuc = True
    except Exception as exc:
        logger.info("ADC çözülemedi: %s", exc)

    with _lock:
        _durum = sonuc
        _calisiyor = False
        if not sonuc:
            _gecersizlesme = time.monotonic() + NEGATIVE_TTL_SECONDS


def _baslat_gerekiyorsa() -> None:
    global _calisiyor
    with _lock:
        if _calisiyor or _durum is True:
            return
        _calisiyor = True
    threading.Thread(target=_yokla, daemon=True, name="adc-probe").start()


def available() -> bool:
    """Kimlik bilgisi çözülebiliyor mu?

    **Beklemez.** Yoklama sürüyorsa ya da hiç yapılmadıysa ``True`` döner:
    bilmemek yokluk değildir ve burada yanlış tarafa düşmenin bedeli üretimin
    durması oluyor.
    """
    global _durum
    with _lock:
        durum = _durum
        gecersizlesme = _gecersizlesme

    if durum is True:
        return True

    if durum is False:
        if time.monotonic() < gecersizlesme:
            return False
        # Süre doldu: yeniden yoklanacak, bu arada erişilebilir varsayılır.
        with _lock:
            _durum = None
        _baslat_gerekiyorsa()
        return True

    # Henüz sonuç yok.
    _baslat_gerekiyorsa()
    return True


def warm_up() -> None:
    """Yoklamayı açılışta başlatır. Açılışı bekletmez."""
    _baslat_gerekiyorsa()


def reset() -> None:
    """Durumu sıfırlar — yalnızca testler için."""
    global _durum, _gecersizlesme, _calisiyor
    with _lock:
        _durum = None
        _gecersizlesme = 0.0
        _calisiyor = False


def _bekle(timeout: float = 20.0) -> bool | None:
    """Yoklamanın sonuçlanmasını bekler — yalnızca testler için."""
    son = time.monotonic() + timeout
    while time.monotonic() < son:
        with _lock:
            if _durum is not None:
                return _durum
        time.sleep(0.01)
    return None
