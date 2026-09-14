"""Abonelik fiyatı env'inin okunması — sessiz sıfırın bekçisi.

Canlıda ölçülen kusur (2026-09-14): `deploy-backend.ps1` Cloud Run'a
`RYTHO_SUB_PRICES_USD={"rytho_plus_monthly":4.4}` yazıyor ama gcloud'un
argüman ayrıştırıcısı çift tırnakları soyuyor; sunucuya
`{rytho_plus_monthly:4.4}` iniyor. Bu geçerli JSON değil → eski
ayrıştırıcı sessizce varsayılana (0.0) düşüyordu → **panelde MRR = 0**.
Hiçbir hata, hiçbir log. Denetimde ancak env'i elle okuyunca görüldü.

Bu dosya üç biçimin de okunduğunu ve gerçekten bozuk girdide
varsayılana düşülüp UYARI yazıldığını sabitler.
"""
import importlib
import logging

import pytest

import core.config as config


def _oku(monkeypatch, deger: str | None):
    if deger is None:
        monkeypatch.delenv("RYTHO_SUB_PRICES_USD", raising=False)
    else:
        monkeypatch.setenv("RYTHO_SUB_PRICES_USD", deger)
    importlib.reload(config)
    return config.SUBSCRIPTION_PRICES_USD


@pytest.fixture(autouse=True)
def _modulu_geri_yukle(monkeypatch):
    """Her testten sonra modül gerçek ortamla yeniden yüklenir — reload
    global bir nesneyi değiştirdiği için sızıntı bırakmamalı."""
    yield
    monkeypatch.undo()
    importlib.reload(config)


@pytest.mark.parametrize(
    "ham",
    [
        '{"rytho_plus_monthly": 4.4}',          # asıl JSON
        "{rytho_plus_monthly:4.4}",             # gcloud tırnakları soymuş
        "rytho_plus_monthly=4.4",               # düz çift
        "  {rytho_plus_monthly : 4.4}  ",       # boşluklu
        "{'rytho_plus_monthly': 4.4}",          # tek tırnak
    ],
)
def test_uc_bicim_de_okunur(monkeypatch, ham):
    assert _oku(monkeypatch, ham) == {"rytho_plus_monthly": 4.4}


def test_coklu_urun_iki_ayracla_da_okunur(monkeypatch):
    beklenen = {"rytho_plus_monthly": 4.4, "rytho_plus_yearly": 44.0}
    assert _oku(monkeypatch, "{rytho_plus_monthly:4.4,rytho_plus_yearly:44}") == beklenen
    assert _oku(monkeypatch, "rytho_plus_monthly=4.4;rytho_plus_yearly=44") == beklenen


def test_tanimsizken_varsayilan_sifir(monkeypatch):
    assert _oku(monkeypatch, None) == {
        "rytho_plus_monthly": 0.0,
        "rytho_plus_yearly": 0.0,
    }


def test_gercekten_bozuk_girdi_varsayilana_duser_ve_UYARIR(monkeypatch, caplog):
    """Sessiz sıfır bir daha bir turu yakmasın: fiyat çözülemediyse
    Cloud Logging'de görünür bir WARNING olmalı."""
    with caplog.at_level(logging.WARNING, logger="core.config"):
        sonuc = _oku(monkeypatch, "zırva")
    assert sonuc == {"rytho_plus_monthly": 0.0, "rytho_plus_yearly": 0.0}
    assert any("RYTHO_SUB_PRICES_USD" in k.message for k in caplog.records), (
        "bozuk fiyat env'i sessizce yutulmamalı"
    )


def test_sayi_olmayan_deger_bozuk_sayilir(monkeypatch, caplog):
    with caplog.at_level(logging.WARNING, logger="core.config"):
        sonuc = _oku(monkeypatch, "{rytho_plus_monthly:bedava}")
    assert sonuc == {"rytho_plus_monthly": 0.0, "rytho_plus_yearly": 0.0}
