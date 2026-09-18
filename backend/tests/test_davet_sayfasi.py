"""Davet karşılama sayfası (/i) — uygulama KURULU DEĞİLKEN görünen tek yüzey.

Sayfa tek dilli Türkçeydi: davet akışı kapalı testin sosyal katmanını ölçen
tek yol ve davetli tarafta uygulama kurulu değilse işletim sistemi App
Links'i çözemeyip bu sayfayı açıyor. İngilizce telefondaki davetli tamamen
Türkçe bir karşılama görüyordu. Uygulama kuruluysa sayfa hiç açılmadığı için
kusur iç testte görünmez — tam da yeni testçide çıkar. Aynı depoda doğru
desen vardı (web/auth/action/index.html), buraya uygulanmamıştı.

Çalıştırma:
    .venv\\Scripts\\python.exe -m pytest tests/test_davet_sayfasi.py -q
"""
from __future__ import annotations

import pathlib
import re

_KOK = pathlib.Path(__file__).resolve().parents[2]
_SAYFA = _KOK / "web" / "i" / "index.html"


def _metin() -> str:
    return _SAYFA.read_text(encoding="utf-8")


def _yorumsuz() -> str:
    """Sayfayı HTML yorumları ATILMIŞ hâlde döndürür.

    ⚠️ Bir kez bu teste kendi yorumumuz takıldı: kaldırılan düğmenin neden
    kaldırıldığını anlatan yorum `href="#"` dizesini kelimesi kelimesine
    içeriyordu ve "çalışmayan düğme yok" iddiası sahte hata verdi. Aynı
    tuzak `infra/build-aab.ps1` izin kapısında da yaşandı: bir şeyin
    YOKLUĞUNU arayan bekçi, o şeyi ANLATAN yorumu görmemeli.
    """
    return re.sub(r"(?s)<!--.*?-->", "", _metin())


def test_sayfa_dil_seciyor():
    metin = _metin()
    assert "navigator.language" in metin, (
        "dil seçimi yok: sayfa tarayıcı diline bakmalı "
        "(web/auth/action/index.html ile aynı desen)")
    assert "document.documentElement.lang" in metin
    for anahtar in ("tr: {", "en: {"):
        assert anahtar in metin, f"{anahtar} sözlüğü yok"


def test_gorunen_metinler_sozlukten_yaziliyor():
    """Gövdeye gömülü Türkçe kalırsa İngilizce dal onu değiştirmez."""
    metin = _metin()
    for kimlik in ("baslik", "govde", "play", "not", "username"):
        assert f"getElementById('{kimlik}')" in metin, (
            f"#{kimlik} sözlükten yazılmıyor")


def test_ingilizce_karsiliklar_var():
    metin = _metin()
    for beklenen in ("Get it on Google Play", "added you as a friend",
                     "You have an invitation on Rytho",
                     "A friend of yours"):
        assert beklenen in metin, f"İngilizce metin eksik: {beklenen!r}"


def test_calismayan_app_store_dugmesi_yok():
    """iOS kapsam dışı; hiçbir yere gitmeyen bir düğme çevrilmemiş metinden
    daha kötü bir ilk izlenim."""
    metin = _yorumsuz()
    assert 'id="appstore"' not in metin
    assert 'href="#"' not in metin
    assert "iPad|iPhone|iPod" not in metin, (
        "App Store düğmesi gitti, iOS sıralama script'i de gitmeli")


def test_davet_baglantisi_lang_tasimiyor():
    """Bilinçli: gönderenin dili alıcının dili değil. Bağlantıya `?lang=`
    eklenirse sayfa YANLIŞ dili seçer ve bu testin gerekçesi bozulur."""
    dart = (_KOK / "apps" / "mobile" / "lib" / "core"
            / "deep_links.dart").read_text(encoding="utf-8")
    assert "lang=" not in dart
