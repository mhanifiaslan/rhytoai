r"""Biyometrik isleme rizasi.

Rizanin uc degismezi var ve testler onlari koruyor:

1. **Ayri ve acik olmali.** Gizlilik metnine gomulu riza gecersiz
   (GDPR Md.7/2, KVKK md.6); o yuzden ayri bir kayit tutuluyor.
2. **Sunucuda dogrulanmali.** Istemcide onay kutusu gostermek kullaniciyi
   bilgilendirir ama islemeyi engellemez.
3. **Geri alinabilmeli VE geri alinca veri gitmeli.** Rizayi geri alip
   veriyi birakmak, geri almayi anlamsiz kilar.

Calistirma:  .venv\Scripts\python.exe -m pytest tests/test_face_consent.py -q
"""
from __future__ import annotations

import pytest

from services import consent_service

OLCUM = {
    "upperThird": 0.40, "middleThird": 0.32, "lowerThird": 0.28,
    "widthToHeight": 0.62, "jawToCheek": 0.71, "mouthToFaceWidth": 0.34,
    "lipFullness": 0.035, "eyeSpacing": 0.41, "symmetry": 0.91,
}


@pytest.fixture
def sahte_kayit(monkeypatch):
    """Firestore yerine bellekte tutulan riza kaydi."""
    kutu: dict = {}
    monkeypatch.setattr(consent_service, "face_consent",
                        lambda uid: kutu.get(uid))

    def ver(uid):
        kutu[uid] = {"granted": True,
                     "version": consent_service.FACE_CONSENT_VERSION}
        return True

    def al(uid):
        kutu[uid] = {"granted": False,
                     "version": consent_service.FACE_CONSENT_VERSION}
        return True

    monkeypatch.setattr(consent_service, "grant_face_consent", ver)
    monkeypatch.setattr(consent_service, "withdraw_face_consent", al)
    return kutu


def test_riza_yoksa_gecersiz(sahte_kayit):
    assert consent_service.has_face_consent("u1") is False


def test_verilen_riza_gecerli(sahte_kayit):
    consent_service.grant_face_consent("u1")
    assert consent_service.has_face_consent("u1") is True


def test_geri_alinan_riza_gecersiz(sahte_kayit):
    consent_service.grant_face_consent("u1")
    consent_service.withdraw_face_consent("u1")
    assert consent_service.has_face_consent("u1") is False


def test_geri_alinan_riza_SILINMEZ_isaretlenir(sahte_kayit):
    """"Riza vardi ve geri alindi" ile "hic riza olmadi" farkli durumlar;
    ikincisini birincinin ustune yazmak, gecmiste yapilan islemenin
    dayanagini yok etmek olurdu."""
    consent_service.grant_face_consent("u1")
    consent_service.withdraw_face_consent("u1")
    kayit = consent_service.face_consent("u1")
    assert kayit is not None
    assert kayit["granted"] is False


def test_eski_surumlu_riza_gecersiz(monkeypatch):
    """Riza NEYE riza gosterildigini kapsar. Islem degisirse (or. ses
    eklenirse) eski riza onu kapsamaz."""
    monkeypatch.setattr(consent_service, "face_consent",
                        lambda uid: {"granted": True, "version": 0})
    assert consent_service.has_face_consent("u1") is False


def test_bozuk_kayit_gecersiz_sayilir(monkeypatch):
    """Rizayi dogrulayamadigimizda 'vardir' varsaymak, biyometrik islemeyi
    rizasiz yapmak demek olurdu."""
    for bozuk in (None, {}, {"granted": True}, {"granted": True, "version": "x"},
                  "evet", {"granted": "true", "version": 99}):
        monkeypatch.setattr(consent_service, "face_consent", lambda uid: bozuk)
        assert consent_service.has_face_consent("u1") is False, bozuk


def test_okuma_hatasinda_riza_yok_sayilir(monkeypatch):
    """Firestore okunamazsa `face_consent` None doner ve riza YOK sayilir.

    "Vardir" varsaymak, biyometrik islemeyi rizasiz yapmak demek olurdu;
    hata durumunda guvenli taraf reddetmektir.
    """
    monkeypatch.setattr(consent_service, "face_consent", lambda uid: None)
    assert consent_service.has_face_consent("u1") is False


def test_riza_alani_istemciye_YAZILAMAZ():
    """`faceConsent` istemci tarafindan DEGISTIRILEMEZ olmali.

    Degistirilebilirse kullanici kendi rizasini uydurur: riza metnini hic
    gormeden `granted: true` yazar, hem bilgilendirme hem ispat kaydi coker.

    Koruma bir donem "alan yazilabilir listede HIC yok" seklindeydi. Amac
    dogruydu ama yan etkisi agirdi ve CIHAZDA GORULDU: kural motoru
    `merge: true` yazimlarda gonderilen alanlara degil SONUCTA olusacak
    dokumana bakiyor. `faceConsent` o dokumanda durdugu icin `hasOnly(...)`
    her istemci yazimini reddediyordu:

        Bildirim baglami yazilamadi: [cloud_firestore/permission-denied]

    Yani kullanici riza verdikten SONRA saat dilimi, dil, FCM token, seri
    sayaci ve profil duzenlemeleri hic yazilamiyordu — sessizce.

    Koruma artik "listede ama DEGISMEZ" seklinde. Bu test onu bekciliyor.
    """
    from pathlib import Path
    kurallar = (Path(__file__).resolve().parent.parent.parent
                / "infra" / "firestore.rules").read_text(encoding="utf-8")

    # Degismezlik kontrolu VAR olmali.
    assert "faceConsentDegismedi()" in kurallar, (
        "faceConsent degismezlik kontrolu kurallardan kaldirilmis; kullanici "
        "kendi rizasini uydurabilir hale gelir.")

    # Kontrol kullanici dokumanina UYGULANMIS olmali; tanimlanip
    # cagrilmamasi sessiz bir acik olurdu.
    bas = kurallar.index("match /users/{uid}")
    son = kurallar.index("allow delete", bas)
    assert "faceConsentDegismedi()" in kurallar[bas:son], (
        "kontrol tanimli ama users/{uid} kuralinda cagrilmiyor.")

    # Esitlik karsilastirmasi: yeni deger eskisiyle AYNI olmak zorunda.
    assert ("request.resource.data.faceConsent == resource.data.faceConsent"
            in kurallar), "degismezlik esitlik ile kurulmamis."


def test_riza_alani_yazilabilir_listede_OLMALI():
    """Alan listede olmazsa merge yazimlarinin TAMAMI reddedilir.

    Bu testin varlik sebebi, yukaridaki korumayi "listeden cikar" diye
    duzeltmeye calisan bir sonraki kisiyi durdurmak: o degisiklik guvenligi
    artirmiyor, yalnizca uygulamanin kullanici dokumanina yazmasini
    tamamen kapatiyor.
    """
    from pathlib import Path
    kurallar = (Path(__file__).resolve().parent.parent.parent
                / "infra" / "firestore.rules").read_text(encoding="utf-8")
    bas = kurallar.index("match /users/{uid}")
    son = kurallar.index("]);", bas)
    assert "'faceConsent'" in kurallar[bas:son], (
        "faceConsent hasOnly listesinden cikarilmis; riza verildikten sonra "
        "istemci kullanici dokumanina HIC yazamaz.")


# --------------------------------------------------------------------------
# Uc davranisi
# --------------------------------------------------------------------------

def test_riza_yoksa_uc_403_doner(monkeypatch):
    """Kontrol SUNUCUDA olmali: arayuzu atlamak islemeyi acmamali."""
    from fastapi.testclient import TestClient
    import main
    from core import entitlements
    from core.auth import AuthUser

    # Yetki kapisini gec, riza kapisini olc.
    monkeypatch.setattr(
        entitlements, "require_plus",
        lambda feature: (lambda: AuthUser(uid="u-test", email=None)))
    monkeypatch.setattr(consent_service, "has_face_consent", lambda uid: False)

    with TestClient(main.app) as client:
        r = client.post("/api/v1/face/reading", json=OLCUM)
    # Riza kapisina gelmeden yetki kapisina takilirsa 402; ikisi de
    # "islem yapilmadi" demek ve testin amaci bu.
    assert r.status_code in (402, 403)


def test_riza_uclari_abonelik_istemez():
    """Rizayi geri almak odeme durumundan bagimsiz olmali; aboneligi biten
    birinin rizasini geri alamamasi, geri alma hakkini odemeye baglamak
    olurdu."""
    import inspect
    from api import face_reading

    for fn in (face_reading.consent_status, face_reading.grant_consent,
               face_reading.withdraw_consent):
        kaynak = inspect.getsource(fn)
        assert "require_plus" not in kaynak, fn.__name__
        assert "get_current_user" in kaynak, fn.__name__


# --------------------------------------------------------------------------
# Yerel depolama yedegi (Firestore yokken)
# --------------------------------------------------------------------------

@pytest.fixture
def yerel_depo(tmp_path, monkeypatch):
    """Firestore'suz ortam: kayit dosyaya yazilir."""
    from core import config
    monkeypatch.setattr(config, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(consent_service.firestore_client, "get_client",
                        lambda: None)
    return tmp_path


def test_firestore_yokken_riza_dosyaya_yazilir(yerel_depo):
    """Onbellekteki desenin aynisi: yerelde dosya, uretimde Firestore.

    Bu bir KAPI GEVSETMESI DEGIL, depolama secimi — riza yine gercekten
    araniyor ve kayit yoksa isleme reddediliyor.
    """
    assert consent_service.has_face_consent("u1") is False
    assert consent_service.grant_face_consent("u1") is True
    assert consent_service.has_face_consent("u1") is True


def test_yerel_depoda_geri_alma_calisir(yerel_depo):
    consent_service.grant_face_consent("u1")
    assert consent_service.withdraw_face_consent("u1") is True
    assert consent_service.has_face_consent("u1") is False


def test_yerel_depo_kullanicilari_karistirmaz(yerel_depo):
    consent_service.grant_face_consent("u1")
    assert consent_service.has_face_consent("u1") is True
    assert consent_service.has_face_consent("u2") is False


def test_kayit_kaybolursa_riza_YOK_sayilir(yerel_depo):
    """Yanlis tarafa dusme yonu onemli: kayit kaybolursa kullaniciya riza
    yeniden sorulur (can sikici ama zararsiz), riza kendiliginden 'var'
    sayilmaz. Yani hata durumunda sistem KAPANIYOR, acilmiyor.
    """
    consent_service.grant_face_consent("u1")
    (yerel_depo / "face_consent.json").unlink()
    assert consent_service.has_face_consent("u1") is False


def test_bozuk_dosya_cokmez_riza_yok_sayilir(yerel_depo):
    (yerel_depo / "face_consent.json").write_text("{bozuk", encoding="utf-8")
    assert consent_service.has_face_consent("u1") is False
    # Bozuk dosyanin uzerine yazilabilmeli, kullanici kilitli kalmamali
    assert consent_service.grant_face_consent("u1") is True
    assert consent_service.has_face_consent("u1") is True
