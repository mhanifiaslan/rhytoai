"""P-turu testleri: kullanicinin kendi ekledigi kisiler.

Bu turun iki hassas yeri var ve ikisi de sessizce bozulabilir:

1. **Ad sunucuya yazilmamali.** Uclerinden birinin (istemci, sema, servis)
   gevsemesi ucuncu bir kisinin kimligini sunucuya sizdirir. Test kaydin
   ICINE bakiyor, ucun donusune degil.
2. **Kontenjan.** Jetonlu yuzeylerin tavani aylik jeton hakki; jetonsuz
   ILISKI OKUMASI'nin tavani ise YALNIZCA bu kontenjan. Kalkarsa maliyetin
   ust siniri kalmaz.

Calistirma:  .venv\\Scripts\\python.exe -m pytest tests/test_people.py -q
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from core import entitlements
from services import people_service, prompts


# --------------------------------------------------------------------------
# Asgari sahte Firestore (auto-id destekli — people_service document() cagiriyor)
# --------------------------------------------------------------------------

class _Anlik:
    def __init__(self, kimlik, veri, referans):
        self.id = kimlik
        self._veri = veri
        self.reference = referans

    @property
    def exists(self):
        return self._veri is not None

    def to_dict(self):
        return dict(self._veri) if self._veri is not None else None


class _Dokuman:
    def __init__(self, store, yol):
        self._store = store
        self._yol = yol

    @property
    def id(self):
        """Gercek DocumentReference'ta var; auto-id yolunda kayit kimligi
        BURADAN okunuyor (people_service.create_person)."""
        return self._yol.rsplit("/", 1)[-1]

    def collection(self, ad):
        return _Koleksiyon(self._store, f"{self._yol}/{ad}")

    def get(self):
        return _Anlik(self._yol.rsplit("/", 1)[-1],
                      self._store.veriler.get(self._yol), self)

    def set(self, veri, merge=False):
        self._store.veriler[self._yol] = dict(veri)

    def delete(self):
        self._store.veriler.pop(self._yol, None)


class _Koleksiyon:
    def __init__(self, store, yol):
        self._store = store
        self._yol = yol

    def document(self, kimlik=None):
        if kimlik is None:
            self._store.sayac += 1
            kimlik = f"auto{self._store.sayac}"
        return _Dokuman(self._store, f"{self._yol}/{kimlik}")

    def stream(self):
        sonuc = []
        for yol, veri in list(self._store.veriler.items()):
            ust, _, kimlik = yol.rpartition("/")
            if ust == self._yol:
                sonuc.append(_Anlik(kimlik, veri, _Dokuman(self._store, yol)))
        return sonuc


class SahteFirestore:
    def __init__(self, veriler=None):
        self.veriler = dict(veriler or {})
        self.sayac = 0

    def collection(self, ad):
        return _Koleksiyon(self, ad)


ESIN = {"relation": "partner", "birthDate": "1990-03-12",
        "birthTime": "07:05", "birthCity": "Ankara", "gender": "female"}
COCUK = {"relation": "child", "birthDate": "2015-06-01",
         "birthCity": "Izmir", "gender": "male"}


@pytest.fixture
def store(monkeypatch):
    s = SahteFirestore()
    monkeypatch.setattr(people_service.firestore_client, "get_client",
                        lambda: s)
    # Gercek harita hesabi bu testlerin konusu degil ve yavas.
    monkeypatch.setattr(people_service, "_buyuk_uclu",
                        lambda kayit: {"sunSign": "Balık"})
    return s


@pytest.fixture
def ucretsiz(monkeypatch):
    monkeypatch.setattr(entitlements, "is_subscriber", lambda uid: False)
    monkeypatch.setattr(people_service.entitlements, "is_subscriber",
                        lambda uid: False)


@pytest.fixture
def abone(monkeypatch):
    monkeypatch.setattr(entitlements, "is_subscriber", lambda uid: True)
    monkeypatch.setattr(people_service.entitlements, "is_subscriber",
                        lambda uid: True)


# --------------------------------------------------------------------------
# 1. Ad sunucuya YAZILMAZ
# --------------------------------------------------------------------------

class TestAdSunucudaDurmaz:
    def test_sizmis_ad_alani_kayda_girmez(self, store, ucretsiz):
        """Istemci bir sekilde `displayName` yollarsa dokumana GIRMEMELI.

        Beyaz liste yerine kara liste kullansaydik, ileride eklenen her
        alan sessizce sunucuya akardi.
        """
        kayit = people_service.create_person(
            "ben", {**ESIN, "displayName": "Ayşe", "name": "Ayşe"})
        assert "displayName" not in kayit
        assert "name" not in kayit
        yazilan = store.veriler["users/ben/people/auto1"]
        assert "displayName" not in yazilan
        assert "name" not in yazilan
        # Kaydin tamaminda "Ayşe" gecmemeli — hicbir alana sizmamis olsun.
        assert "Ayşe" not in str(yazilan)

    def test_prompt_adi_iliski_etiketi(self):
        """AI kisiyi adiyla degil ILISKI ETIKETIYLE anar."""
        kw = people_service.birth_kwargs(COCUK, name="çocuğun")
        assert kw["name"] == "çocuğun"


# --------------------------------------------------------------------------
# 2. Kontenjan — jetonsuz yuzeylerin TEK tavani
# --------------------------------------------------------------------------

class TestKontenjan:
    def test_ucretsiz_ikinci_kiside_402(self, store, ucretsiz):
        people_service.create_person("ben", ESIN)
        with pytest.raises(HTTPException) as hata:
            people_service.create_person("ben", COCUK)
        assert hata.value.status_code == 402
        assert hata.value.headers["X-Paywall-Reason"] == "people"

    def test_abone_onbirinci_kiside_402(self, store, abone):
        for _ in range(people_service.PLUS_PERSON_SLOTS):
            people_service.create_person("ben", COCUK)
        with pytest.raises(HTTPException) as hata:
            people_service.create_person("ben", COCUK)
        assert hata.value.status_code == 402

    def test_aboneye_rytho_plus_onerilmez(self, store, abone):
        """Kontenjani dolan ABONEYE 'Rytho+ al' demek sacma olurdu."""
        for _ in range(people_service.PLUS_PERSON_SLOTS):
            people_service.create_person("ben", COCUK)
        with pytest.raises(HTTPException) as hata:
            people_service.create_person("ben", COCUK)
        assert "Rytho+" not in hata.value.detail

    def test_ucretsize_rytho_plus_onerilir(self, store, ucretsiz):
        people_service.create_person("ben", ESIN)
        with pytest.raises(HTTPException) as hata:
            people_service.create_person("ben", COCUK)
        assert "Rytho+" in hata.value.detail

    def test_kontenjan_kullaniciya_ozel(self, store, ucretsiz):
        """Bir kullanicinin kontenjani baskasini etkilemez."""
        people_service.create_person("ben", ESIN)
        people_service.create_person("baskasi", ESIN)  # kendi ilk kisisi
        assert len(people_service.list_people("ben")) == 1
        assert len(people_service.list_people("baskasi")) == 1


# --------------------------------------------------------------------------
# 3. Sahiplik
# --------------------------------------------------------------------------

class TestSahiplik:
    def test_baskasinin_kisisi_okunamaz(self, store, ucretsiz):
        """`get_person` sahiplik dogrulamasinin TEK yolu (bkz. api/reports).

        Kayit cagiranin kendi agacindan okundugu icin baskasinin
        person_id'si burada hicbir zaman bulunamaz.
        """
        people_service.create_person("baskasi", ESIN)
        assert people_service.get_person("baskasi", "auto1") is not None
        assert people_service.get_person("ben", "auto1") is None

    def test_baskasinin_kisisi_silinemez(self, store, ucretsiz):
        people_service.create_person("baskasi", ESIN)
        assert people_service.delete_person("ben", "auto1") is False
        assert "users/baskasi/people/auto1" in store.veriler


# --------------------------------------------------------------------------
# 4. Saat-bilinmiyor disiplini (R9 dersinin kisi tarafi)
# --------------------------------------------------------------------------

class TestSaatsizDisiplin:
    def test_saat_verilmezse_alan_hic_yazilmaz(self, store, ucretsiz):
        """'12:00 varsayalim' ile 'bilinmiyor' ayrimi kayitta korunmali —
        hour_known bu alanin VARLIGINDAN turetiliyor."""
        kayit = people_service.create_person("ben", COCUK)
        assert "birthTime" not in kayit
        assert "birthTime" not in store.veriler["users/ben/people/auto1"]

    def test_saatsiz_kayit_hour_known_false(self):
        assert people_service.birth_kwargs(COCUK)["hour_known"] is False
        assert people_service.birth_kwargs(ESIN)["hour_known"] is True

    def test_saat_iki_haneye_normallesir(self, store, ucretsiz):
        """Kayitta tek bicim dursun: "7:05" -> "07:05". birth_kwargs saati
        `split(":")` ile ayirdigi icin bicim kaymasi sessiz hataya acik."""
        kayit = people_service.create_person(
            "ben", {**ESIN, "birthTime": "7:05"})
        assert kayit["birthTime"] == "07:05"

    def test_saat_tek_haneli_dakika_reddedilir(self, store, ucretsiz):
        with pytest.raises(HTTPException) as hata:
            people_service.create_person("ben", {**ESIN, "birthTime": "7:5"})
        assert hata.value.status_code == 400


# --------------------------------------------------------------------------
# 5. Dogrulama
# --------------------------------------------------------------------------

class TestDogrulama:
    @pytest.mark.parametrize("bozuk", [
        {"relation": "lover", "birthDate": "1990-03-12", "birthCity": "Ankara"},
        {"relation": "child", "birthDate": "2023-02-30", "birthCity": "Ankara"},
        {"relation": "child", "birthDate": "12-03-1990", "birthCity": "Ankara"},
        {"relation": "child", "birthDate": "2020-01-01", "birthCity": "   "},
        {"relation": "child", "birthDate": "2020-01-01", "birthCity": "Ankara",
         "birthTime": "25:00"},
    ])
    def test_bozuk_girdi_reddedilir(self, bozuk):
        with pytest.raises(HTTPException) as hata:
            people_service._dogrula(bozuk, "tr")
        assert hata.value.status_code == 400

    def test_tur_kumesi_kapali(self):
        """Serbest metin bir tur adi olarak sunucuya giremez: tur, eksen
        adlarini ve AI cercevesini belirliyor."""
        for tur in people_service.RELATIONS:
            temiz = people_service._dogrula(
                {**COCUK, "relation": tur}, "tr")
            assert temiz["relation"] == tur

    def test_ulke_kodu_buyuk_harfe_cevrilir(self):
        temiz = people_service._dogrula({**COCUK, "birthNation": "tr"}, "tr")
        assert temiz["birthNation"] == "TR"


# --------------------------------------------------------------------------
# 6. Duzeltme
# --------------------------------------------------------------------------

class TestDuzeltme:
    def test_saat_kaldirilinca_alan_dokumandan_duser(self, store, ucretsiz):
        """Kullanici 'saati aslinda bilmiyorum' derse kayit da unutmali;
        merge kullanilsaydi eski saat dokumanda kalirdi."""
        people_service.create_person("ben", ESIN)
        people_service.update_person("ben", "auto1",
                                     {**ESIN, "birthTime": None})
        assert "birthTime" not in store.veriler["users/ben/people/auto1"]

    def test_olmayan_kisi_duzeltilemez(self, store, ucretsiz):
        with pytest.raises(HTTPException) as hata:
            people_service.update_person("ben", "yok", ESIN)
        assert hata.value.status_code == 404


# --------------------------------------------------------------------------
# 7. Iliski turune gore eksen dili
# --------------------------------------------------------------------------

class TestIliskiTuruDili:
    """Ekranda "Cocugunuzla cekim: guclu" YAZAMAZ.

    "Cekim" ekseni Venus/Mars/Pluto temaslarindan hesaplaniyor ve bu
    temaslar aile haritalarinda da var. Olcum dogru; sunum yanlisti.
    Cozum olcumu gizlemek DEGIL, dogru adiyla sunmak.
    """

    #: (dil, tur, o dilde ASLA gorunmemesi gereken eksen adi)
    YASAK = [("tr", "child", "Çekim"), ("tr", "parent", "Çekim"),
             ("tr", "work", "Çekim"),
             ("en", "child", "Attraction"), ("en", "parent", "Attraction"),
             ("en", "work", "Attraction")]

    @pytest.mark.parametrize("dil,tur,yasak", YASAK)
    def test_aile_ve_iste_cekim_adi_kullanilmaz(self, dil, tur, yasak):
        ad = prompts.axis_name(dil, "attraction", tur)
        assert ad != yasak
        assert ad, "eksen adsiz kalmamali"

    def test_es_ve_arkadasta_ad_degismez(self):
        """Asiri duzeltme de bir hata olurdu: esiyle 'cekim' dogru sozcuk."""
        assert prompts.axis_name("tr", "attraction", "partner") == "Çekim"
        assert prompts.axis_name("tr", "attraction", "friend") == "Çekim"

    def test_tur_verilmezse_bugunku_davranis(self):
        """Arkadas yolu (tur YOK) hicbir sey degistirmemeli."""
        for eksen in ("communication", "emotional", "attraction", "bond"):
            assert (prompts.axis_name("tr", eksen)
                    == prompts.get("tr").SYNASTRY_AXIS_NAMES[eksen])

    def test_olcum_turden_ETKILENMEZ(self):
        """Degisen yalniz AD: seviye, ton ve dayanak aciler aynen kalir."""
        ham = {"calc_version": "3", "axes": [
            {"axis": "attraction", "level": "strong", "tone": "flowing",
             "basis": [{"p1": "Venus", "p2": "Mars", "aspect": "trine",
                        "orb": 1.2}]},
        ]}
        cocuk = prompts.localize_relationship_axes("tr", ham, "child")
        arkadas = prompts.localize_relationship_axes("tr", ham, None)
        c, a = cocuk["axes"][0], arkadas["axes"][0]
        assert c["axis_local"] != a["axis_local"]      # ad degisti
        assert c["level_local"] == a["level_local"]    # olcum degismedi
        assert c["tone_local"] == a["tone_local"]
        assert c["basis"] == a["basis"]

    @pytest.mark.parametrize("dil", ["tr", "en"])
    def test_her_tur_icin_etiket_var(self, dil):
        """Eksik etiket, AI'nin kisiyi adsiz anmasina yol acardi."""
        for tur in people_service.RELATIONS:
            etiket = prompts.relation_label(dil, tur)
            assert etiket and etiket != tur

    @pytest.mark.parametrize("tur", ["child", "parent", "sibling", "work"])
    def test_hassas_turlerde_cerceve_kisiti_var(self, tur):
        """Ad degismesi yetmez: modelin de romantik cerceveyi birakmasi
        gerekiyor, yoksa cumle icinde geri gelir."""
        for dil in ("tr", "en"):
            assert prompts.relation_frame(dil, tur)

    def test_cerceve_prompta_giriyor(self):
        """Tablo dolu olup prompt'a girmemesi sessiz bir kusur olurdu."""
        p = prompts.get("tr")
        metin = p.RELATIONSHIP.format(
            me="Ben", friend="çocuğun", axes="- x",
            frame=prompts.relation_frame("tr", "child"))
        assert "EBEVEYN–ÇOCUK" in metin

    def test_arkadas_promptunda_cerceve_bos(self):
        p = prompts.get("tr")
        metin = p.RELATIONSHIP.format(
            me="Ben", friend="Erkan", axes="- x",
            frame=prompts.relation_frame("tr", None))
        assert "EBEVEYN" not in metin


# --------------------------------------------------------------------------
# 8. Geriye donuk uyum
# --------------------------------------------------------------------------

class TestGeriyeDonukUyum:
    """Kullanici yeni surumu yuklemeden ONCE sunucu deploy ediliyor.

    Cihazdaki 1.7.0+23 yalnizca `friend_uid` gonderiyor; sema onu kabul
    etmezse ilisiki ekrani CANLIDA kirilir. Bu, R9'da bir kez yasanan
    "sunucu degisti, istemci eski" sinifinin ta kendisi.
    """

    def test_eski_istemci_govdesi_kabul_edilir(self):
        from api.reports import RelationshipRequest

        eski = RelationshipRequest(**{"friend_uid": "abc123"})
        assert eski.friend_uid == "abc123"
        assert eski.person_id is None

    def test_yeni_istemci_govdesi_kabul_edilir(self):
        from api.reports import RelationshipRequest

        yeni = RelationshipRequest(**{"person_id": "p1"})
        assert yeni.person_id == "p1"

    def test_dyad_anahtari_arkadasta_ESKISIYLE_AYNI(self, monkeypatch):
        """Onbellek anahtari degisseydi tum mevcut ikili okumalar duserdi
        ve kullanicilar ayni gunu YENIDEN 3 jetonla uretirdi."""
        import datetime as dt

        from services import report_service, synastry_service
        import services.profile_service as ps

        monkeypatch.setattr(ps, "get_profile",
                            lambda uid: {"displayName": uid,
                                         "birthDate": "1990-01-01",
                                         "birthCity": "Ankara"})
        gun = dt.date(2026, 8, 18)
        karsi = synastry_service.friend_counterpart("uid-a", "uid-b")
        # 1.7.0'daki bicim: dyad-{sirali ilk}-{sirali ikinci}-{tarih}
        assert (report_service.dyad_key_for(karsi.key, gun)
                == f"dyad-uid-a-uid-b-{gun.isoformat()}")
