"""Swiss Ephemeris veri yolu — tek başlatıcı (T0).

İki motor var (kerykeion + sky_service'in doğrudan swisseph'i) ve ikisinin
hangi efemeris verisini kullandığı bugüne dek belirsizdi:

- kerykeion her özne kuruluşunda KENDİ paket klasörünü ``set_ephe_path``
  yapıyor, ama o klasörde gezegen (sepl) ve Ay (semo) dosyaları YOK —
  yalnız asteroit + sabit yıldız var. Swiss Ephemeris bu durumda sessizce
  Moshier analitik hesabına düşer; 1800-2200 arası fark görünmezdir ama
  1200-1800 doğumlarda hassasiyet düşer ve Chiron/Lilith (asteroit dosyası
  1800-2400 aralıklı) kerykeion tarafından sessizce listeden silinir.
- sky_service hiç yol kurmuyordu; hangi veriyle çalıştığı o süreçte daha
  önce kerykeion'un çağrılıp çağrılmadığına bağlıydı.

Çözüm iki bacak:
1. Repo'daki ``backend/ephe/*.se1`` dosyaları kerykeion'un sweph klasörüne
   KOPYALANIR (idempotent) — kerykeion kendi yolunu her seferinde yeniden
   kurduğu için tek güvenilir yol bu.
2. Doğrudan swisseph kullanıcıları için ``swe.set_ephe_path(backend/ephe)``.

Veri dosyaları: ``sepl_18.se1`` (gezegenler 1800-2400) + ``semo_18.se1``
(Ay) — kaynak: Astrodienst'in resmi dağıtımı
(github.com/aloistr/swisseph, ephe/). Lisans yönetimi ürün sahibinde.
"""
from __future__ import annotations

import importlib.util
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

EPHE_DIR = Path(__file__).resolve().parent.parent / "ephe"

_hazir = False


def ensure() -> None:
    """Efemeris veri yolunu bir kez kurar. Ucuz ve idempotent.

    kerykeion'u İÇE AKTARMAZ (212 ms'lik modül bedeli soğuk başlatmada
    ödenmesin) — paket klasörünü ``find_spec`` ile bulur.
    """
    global _hazir
    if _hazir:
        return
    _hazir = True

    # 1) kerykeion'un sweph klasörüne kopya.
    try:
        spec = importlib.util.find_spec("kerykeion")
        if spec and spec.origin:
            hedef = Path(spec.origin).parent / "sweph"
            if hedef.is_dir():
                for kaynak in EPHE_DIR.glob("*.se1"):
                    kopya = hedef / kaynak.name
                    if (not kopya.exists()
                            or kopya.stat().st_size != kaynak.stat().st_size):
                        shutil.copy2(kaynak, kopya)
                        logger.info("Efemeris dosyası kopyalandı: %s",
                                    kaynak.name)
    except Exception as exc:  # pragma: no cover - dosya sistemi durumu
        logger.warning("Efemeris kopyalanamadı (Moshier'e düşülür): %s", exc)

    # 2) Doğrudan swisseph kullanıcıları (sky_service) için yol.
    try:
        import swisseph as swe

        swe.set_ephe_path(str(EPHE_DIR))
    except Exception as exc:  # pragma: no cover
        logger.warning("set_ephe_path başarısız: %s", exc)
