"""Marifetname katmani: gunun yoneticisi ve ayin menzili.

Bu ikisi korpusa girdi ama motor hesaplamiyordu. Korpusta olup hesaplanmayan
bilgi, modelin karsiligi olmayan bir sey hakkinda konusmasina davetiye —
"gok verisi uydurulmaz" ilkesiyle celisir.

Calistirma:  .venv\\Scripts\\python.exe -m pytest tests/test_sky_marifetname.py -q
"""
from __future__ import annotations

import datetime as dt
import re

import pytest

from services import prompts, sky_service


@pytest.fixture
def temiz_onbellek(tmp_path, monkeypatch):
    from core import cache, config
    monkeypatch.setattr(config, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(config, "CACHE_BACKEND", "file")
    cache._memory.clear()
    yield
    cache._memory.clear()


# --------------------------------------------------------------------------
# Gunun yoneticisi
# --------------------------------------------------------------------------

@pytest.mark.parametrize("gun,beklenen", [
    (dt.date(2026, 8, 9), "Sun"),       # Pazar
    (dt.date(2026, 8, 3), "Moon"),      # Pazartesi
    (dt.date(2026, 8, 4), "Mars"),      # Sali
    (dt.date(2026, 8, 5), "Mercury"),   # Carsamba
    (dt.date(2026, 8, 6), "Jupiter"),   # Persembe
    (dt.date(2026, 8, 7), "Venus"),     # Cuma
    (dt.date(2026, 8, 8), "Saturn"),    # Cumartesi
])
def test_gun_yoneticisi_marifetname_cetveliyle_ayni(gun, beklenen):
    assert sky_service.day_ruler(gun) == beklenen


def test_gun_yoneticisi_haftada_dolanir():
    baslangic = dt.date(2026, 8, 3)
    hafta = [sky_service.day_ruler(baslangic + dt.timedelta(days=i))
             for i in range(7)]
    assert len(set(hafta)) == 7, "yedi gun yedi ayri gezegen olmali"
    # Sekizinci gun basa doner
    assert sky_service.day_ruler(baslangic + dt.timedelta(days=7)) == hafta[0]


def test_gun_yoneticisi_anahtar_dondurur():
    """Ad degil anahtar: adlandirma istegin dilinde yapilir."""
    anahtar = sky_service.day_ruler(dt.date(2026, 8, 7))
    assert anahtar == "Venus"
    assert prompts.planet_name("tr", anahtar) == "Venüs"
    assert prompts.planet_name("en", anahtar) == "Venus"


def test_gun_yoneticisi_gokyuzu_yukunde_DEGIL(temiz_onbellek):
    """Gokyuzu yuku UTC'de hesaplanip TUM kullanicilarla paylasiliyor.

    Gun yoneticisi oraya gomulseydi, saat dilimi farki olan kullaniciya
    yanlis gun gosterilirdi. Bu yuzden yalnizca cagiran tarafta, kullanicinin
    YEREL tarihinden hesaplaniyor.
    """
    sky = sky_service.get_sky_now(include_nasa=False)
    assert "day_ruler" not in sky


# --------------------------------------------------------------------------
# Ayin menzili
# --------------------------------------------------------------------------

def test_yirmisekiz_menzil_vardir():
    assert len(sky_service._MANSIONS) == 28
    assert len(set(sky_service._MANSIONS)) == 28, "menzil adlari benzersiz olmali"


@pytest.mark.parametrize("lon,numara", [
    (0.0, 1),
    (12.8, 1),      # menzil genisligi ~12.857; hemen altinda
    (12.9, 2),      # hemen ustunde
    (180.0, 14),
    (359.9, 28),
])
def test_menzil_sinirlari(lon, numara):
    assert sky_service.moon_mansion(lon)["number"] == numara


def test_menzil_tam_tur_basa_doner():
    """Kayan nokta artigi son menzilin disina tasmamali."""
    assert sky_service.moon_mansion(360.0)["number"] == 1
    assert sky_service.moon_mansion(720.5)["number"] == 1
    for lon in (359.999, 359.9999, 360.0 - 1e-9):
        m = sky_service.moon_mansion(lon)
        assert 1 <= m["number"] <= 28


def test_her_boylam_bir_menzile_duser():
    for i in range(0, 3600):
        m = sky_service.moon_mansion(i / 10)
        assert 1 <= m["number"] <= 28
        assert m["name"] in sky_service._MANSIONS


def test_menzil_burctan_ince(temiz_onbellek):
    """Menzil ~12.9 derecelik dilim, burc 30 derecelik.

    Ayni burctaki iki ayri boylam cogunlukla iki ayri menzildir; bu olcunun
    varlik sebebi de bu.
    """
    a = sky_service.moon_mansion(2.0)    # Koc'un basi
    b = sky_service.moon_mansion(28.0)   # Koc'un sonu
    assert a["number"] != b["number"]


def test_menzil_gokyuzu_yukunde(temiz_onbellek):
    """Menzil konumdan bagimsiz (Ay'in boylami kuresel), o yuzden paylasimli
    yukte durabilir."""
    sky = sky_service.get_sky_now(include_nasa=False)
    menzil = sky.get("moon_mansion")
    assert menzil, "gokyuzu yukunde menzil yok"
    assert 1 <= menzil["number"] <= 28
    assert menzil["name"] in sky_service._MANSIONS


def test_onbellek_anahtari_surumlu(temiz_onbellek):
    """Yuk sekli degistiginde surum yukseltilmezse eski kayit yeni alan
    olmadan servis edilmeye devam eder ve degisiklik HIC gorunmez.
    Bu bir kez yasandi (ay evresi 'Dolunay'da takildi).

    Test eskiden surumu SABIT bir degere kilitliyordu (`== "sky-now-v3"`);
    o hâliyle her mesru yukseltmede kiriliyor ve gercek iddiayi (yukun her
    alani anahtarin arkasinda duruyor) hic sinamiyordu. Simdi anahtarin
    surumlu OLDUGU ve yukun bekledigimiz alanlari tasidigi sinaniyor —
    yeni alan eklendiginde bu liste de buyumeli, surum de artmali.
    """
    assert re.fullmatch(r"sky-now-v\d+", sky_service._SKY_CACHE_KEY)

    sky = sky_service.get_sky_now(include_nasa=False)
    for alan in ("timestamp_utc", "planets", "retrogrades", "moon_phase",
                 "moon_mansion", "aspects"):
        assert alan in sky, f"gokyuzu yukunde {alan} yok"
    # Ay evresi yuku (D1): oran + ait oldugu an birlikte tasinir.
    for alan in ("key", "emoji", "angle", "illumination", "as_of_utc"):
        assert alan in sky["moon_phase"], f"ay evresinde {alan} yok"


# --------------------------------------------------------------------------
# Sohbete iliştirilen blok
# --------------------------------------------------------------------------

def test_gokyuzu_blogu_iki_yeni_satiri_tasir(temiz_onbellek):
    from api.chat import _sky_summary

    blok = _sky_summary("tr", {"timezone": "Europe/Istanbul"})
    assert "Günün yöneticisi:" in blok
    assert "menzil" in blok

    en = _sky_summary("en", {"timezone": "Europe/Istanbul"})
    assert "Ruler of the day:" in en
    assert "Mansion of the Moon:" in en


def test_ingilizce_gokyuzu_blogu_turkce_icermez(temiz_onbellek):
    """Yeni satirlar da dil izolasyonuna tabi."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from test_language_isolation import turkce_kalinti
    from api.chat import _sky_summary

    blok = _sky_summary("en", {"timezone": "Europe/Istanbul"})
    assert not turkce_kalinti(blok), \
        f"Ingilizce gokyuzu blogunda Turkce: {turkce_kalinti(blok)}"


def test_profil_yoksa_blok_yine_uretilir(temiz_onbellek):
    """Saat dilimi bilinmiyorsa varsayilana dusulur; blok bos kalmaz."""
    from api.chat import _sky_summary

    assert "Günün yöneticisi:" in _sky_summary("tr", None)
    assert "Günün yöneticisi:" in _sky_summary("tr", {})
