"""Paket geneli test kancaları — kapı hermetikliği (PBZ-turu).

`AppGateMiddleware` HER TestClient isteğinde canlı: `/api/v1/` altındaki
muaf olmayan yol `X-App-Build` başlığını eşiğe vurur. Eşik okuması
(`app_gate.current_min_build`) memo boşken `core.firestore.get_client`'a
gider; geliştirici makinesinde ADC varsa bu GERÇEK projenin
`config/app.minBuild` dokümanıdır (`GOOGLE_CLOUD_PROJECT` varsayılanı
üretim). Panelden eşik > 0 yazıldığı an, başlık göndermeyen ve kapıyı hiç
düşünmeyen her test (uç, kota, kimlik testleri...) 426 ile düşerdi —
kapı testleri dışındaki hiçbir test kapıdan haberdar değil ve olmamalı.

Pin: eşiğin doküman ayağı, Firestore istemcisi SAHTELENMEMİŞKEN okumadan
0 döner — hiçbir test istemeden gerçek ADC'ye gidemez. Env tabanı da 0'a
sabitlenir (kabuktaki `RYTHO_MIN_BUILD` aynı şekilde her testi kilitlerdi)
ve iki memo her testin önünde/arkasında sıfırlanır.

Çıkış (kapıyı BİLEREK sınayan testler): `core.firestore.get_client`'ı
kendi sahtesiyle ya da `lambda: None` ile değiştiren test gerçek okuma
mantığını olduğu gibi çalıştırır — test_app_gate `esik`, test_app_config
`hermetik`, test_admin_min_build `depo`, test_auth_gate `ayna` zaten
böyle yapıyor. Pin yalnız Firestore'u düşünmeyen testi korur; bekçisi
test_app_gate `test_pin_firestore_sahtelenmemisken_esik_sifir`.
"""
from __future__ import annotations

import pytest

from core import app_gate, config
from core import firestore as firestore_client
from services import account_service

#: Toplama anında yakalanır: henüz hiçbir fixture koşmadı, bu gerçek
#: istemci kurucusudur. Kıyas kimlikle (`is`) — sahte istemci kuran her
#: test modül niteliğini değiştirmiş olur.
_GERCEK_GET_CLIENT = firestore_client.get_client


@pytest.fixture(autouse=True)
def kapi_hermetik(monkeypatch):
    gercek_doc_min_build = app_gate._doc_min_build

    def korumali_doc_min_build() -> int:
        # Sahte istemci kurulduysa gerçek mantık; kurulmadıysa dokümanı
        # OKUMADAN 0 — ADC'ye gidilmez.
        if firestore_client.get_client is _GERCEK_GET_CLIENT:
            return 0
        return gercek_doc_min_build()

    app_gate.reset_memo()
    monkeypatch.setattr(app_gate, "_doc_min_build", korumali_doc_min_build)
    monkeypatch.setattr(config, "MIN_APP_BUILD", 0)
    yield
    app_gate.reset_memo()


class _BosKova:
    """Hiçbir dosyası olmayan kova: `list_blobs` boş döner, silme olmaz."""

    def list_blobs(self, prefix: str = ""):  # noqa: ARG002
        return ()


@pytest.fixture(autouse=True)
def depolama_hermetik(monkeypatch):
    """Hiçbir test istemeden GERÇEK Cloud Storage kovasına gitmesin.

    `delete_account` 2026-09-18'den beri `avatars/{uid}/` önekini de
    siliyor (hesabı silinmiş kullanıcının fotoğrafı kovada kalıyordu).
    Çağrıyı `account_service._delete_storage_files` yapıyor ve uid'i
    sahteleyen 18 mevcut silme testi kovayı sahtelemiyor.

    Bugün o testler KAZARA güvenli: `firebase_admin` uygulaması testte
    hiç başlatılmadığı için `storage.bucket()` anında fırlıyor ve
    fonksiyonun best-effort `except`i yutuyor ("The default Firebase app
    does not exist" uyarısı log'a düşüyor). Ama bu tek bir satıra bağlı:
    ileride bir test ya da içe aktarma yan etkisi varsayılan uygulamayı
    başlatırsa, makinede ADC varken aynı 18 test ÜRETİM kovasında
    `list_blobs` + `delete` koşar. Kaza ile güvenli olan şey güvence
    değildir; pin bunu yapısal hâle getiriyor.

    `kapi_hermetik`in Firestore pini ile aynı doktrin ve aynı çıkış yolu:
    kovayı BİLEREK sınayan test `_kova`'yı kendi sahtesiyle değiştirir
    (test_account_deletion `kova`) ve o yama bunun ÜSTÜNE yazdığı için
    kazanır.
    """
    monkeypatch.setattr(account_service, "_kova", _BosKova)
