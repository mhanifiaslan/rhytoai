"""Şehir → koordinat + saat dilimi çözümlemesi.

Astronomik hassasiyetin en kritik hata noktası konum/saat dilimidir.

Veri `data/gazetteer.json`'dan gelir — GeoNames cities15000 dump'ından
`scripts/build_gazetteer.py` ile üretilir (O1; ~34k şehir, 81 TR ilinin
tamamı, Türkçe egzonimler). Eski elle yazılmış ~81 anahtarlık sözlük ve
ölü GeoNames API dalı kaldırıldı: sözlük 81 ilin 48'ini tanımıyordu ve
"münih" gibi anahtarlar normalize hatasıyla hiç erişilemiyordu (anahtar
artık YÜKLEME anında normalize edildiği için o hata sınıfı yapısal
olarak kapalı).

Bulunamayan şehir ESKİSİ GİBİ İstanbul varsayılanına düşer ve
``fallback=True`` bayrağı taşır — motorlar bu bayrağı beyana çevirir
(geo_fallback_city / tst_fallback_city). Serbest metin her zaman kabul:
listede olmayan köy adı isteği düşürmez, dürüst beyanla hesaplanır.
"""
from __future__ import annotations

import json
import logging
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

_GAZETTEER_PATH = Path(__file__).resolve().parent.parent / "data" / "gazetteer.json"

#: Kayıt alanları: [ad, ülke, il, lat, lng, tz, nüfus]
_AD, _ULKE, _IL, _LAT, _LNG, _TZ, _NUFUS = range(7)


@dataclass
class GeoLocation:
    city: str
    nation: str
    lat: float
    lng: float
    tz_str: str

    # Şehir çözülemeyip İstanbul varsayılanına düşüldü mü (Revize B1).
    # BaZi Gerçek Güneş Zamanı boylamdan hesaplanır; yanlış boylamla TST
    # düzeltmesi hatayı BÜYÜTEBİLİR. Düşüş sessiz kalamaz — motor bu bayrağı
    # görüp beyan üretir.
    fallback: bool = False


def _normalize(s: str) -> str:
    """build_gazetteer.py ile AYNI kural — indeks bu anahtarla kurulu."""
    s = s.strip().lower().replace("ı", "i")
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


# Tembel modül önbelleği: gazetteer soğuk başlatmada DEĞİL ilk çözümde
# yüklenir (astro warm_up zaten arka planda tetikler). ~6 MB JSON,
# yükleme tek seferlik ve ölçülüp loglanır — "ölçülmeyen söylenmez".
_cities: list[list] | None = None
_index: dict[str, list[int]] | None = None


def _yukle() -> tuple[list[list], dict[str, list[int]]]:
    global _cities, _index
    if _cities is None or _index is None:
        t0 = time.perf_counter()
        veri = json.loads(_GAZETTEER_PATH.read_text(encoding="utf-8"))
        _cities, _index = veri["cities"], veri["index"]
        logger.info("Gazetteer yüklendi: %d şehir, %d indeks anahtarı, %.0f ms",
                    len(_cities), len(_index),
                    (time.perf_counter() - t0) * 1000)
    return _cities, _index


def resolve_city(city: str, nation: str | None = None) -> GeoLocation:
    """Şehir adını koordinata çevirir; bulunamazsa İstanbul + fallback.

    ``nation`` verilirse aynı adlı şehirler arasında o ülke tercih edilir
    (ör. Tripoli LB/LY); ülkede eşleşme yoksa filtre YOK SAYILIR — yanlış
    ülke bilgisi doğru şehri gölgelememeli. Aday listesi üretim anında
    başkent-önce + nüfus sırasıyla geldiği için ilk aday en olası olandır.
    """
    cities, index = _yukle()
    adaylar = index.get(_normalize(city), [])
    if adaylar:
        secilen = None
        if nation:
            for i in adaylar:
                if cities[i][_ULKE] == nation.upper():
                    secilen = cities[i]
                    break
        if secilen is None:
            secilen = cities[adaylar[0]]
        return GeoLocation(
            city=city, nation=nation or secilen[_ULKE],
            lat=float(secilen[_LAT]), lng=float(secilen[_LNG]),
            tz_str=secilen[_TZ])

    logger.warning("Şehir çözümlenemedi, İstanbul varsayılanı kullanılıyor: %s", city)
    return GeoLocation(city=city, nation=nation or "TR",
                       lat=41.0082, lng=28.9784, tz_str="Europe/Istanbul",
                       fallback=True)
