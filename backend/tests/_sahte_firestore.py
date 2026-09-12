"""Paylaşımlı bellek içi sahte Firestore (AD13).

test_admin_users'taki yol-farkında sahte buraya çıkarıldı ve panel v3'ün
sorgu yüzeyleriyle genişletildi: `where` (==, !=, <, <=, >, >=, in),
zincirli `order_by` (örtük `__name__` kuyruğu — gerçek Firestore gibi son
sıralamanın yönünde), `start_after` (liste / sözlük / anlık görüntü),
`limit`, `count()`, `collection_group`, `get_all`, `document(yol)`,
`update`, `delete` ve yazımda `Increment` / `DELETE_FIELD` dönüşümleri.

Sadakat sınırı: gerçek Firestore'un davranışı taklit edilir ama İNDEKS
ihtiyacı kontrol edilmez — indeksler infra/firestore.indexes.json'da ve
canlı dumanla doğrulanır. Sıralama alanı olmayan doküman gerçek
Firestore'da olduğu gibi sonuç dışı kalır; karışık tiplerde tip sırası
(None < bool < sayı < zaman < dizgi) uygulanır.

Kullanım:
    depo = SahteFirestore()
    depo.docs["users/u1"] = {...}
    monkeypatch.setattr("services.x.firestore_client.get_client", lambda: depo)
"""
from __future__ import annotations

import datetime as dt
from functools import cmp_to_key
from typing import Any

try:  # Dönüşüm nesneleri gerçek kitaplıktan — üretim kodu onları yazar.
    from google.cloud.firestore_v1.transforms import DELETE_FIELD, Increment
except Exception:  # pragma: no cover - kitaplık yoksa
    DELETE_FIELD = object()

    class Increment:  # type: ignore[no-redef]
        def __init__(self, value):
            self.value = value

try:
    from google.api_core.exceptions import NotFound
except Exception:  # pragma: no cover
    class NotFound(Exception):  # type: ignore[no-redef]
        pass


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------

def _alan_oku(veri: dict, yol: str) -> Any:
    """Noktalı alan yolu ("a.b") — yoksa None."""
    if yol == "__name__":
        return None
    deger: Any = veri
    for parca in yol.split("."):
        if not isinstance(deger, dict) or parca not in deger:
            return None
        deger = deger[parca]
    return deger


def _sira_anahtari(deger: Any) -> tuple:
    """Karışık tipleri Firestore tip sırasına göre karşılaştırılabilir kılar."""
    if deger is None:
        return (0, 0)
    if isinstance(deger, bool):
        return (1, int(deger))
    if isinstance(deger, (int, float)):
        return (2, float(deger))
    if isinstance(deger, dt.datetime):
        if deger.tzinfo is None:
            deger = deger.replace(tzinfo=dt.timezone.utc)
        return (3, deger.timestamp())
    if isinstance(deger, str):
        return (4, deger)
    return (5, repr(deger))


def _donustur(mevcut: Any, yeni: Any) -> Any:
    """Tek alanın yazım dönüşümü: Increment toplar, düz değer ezer."""
    if isinstance(yeni, Increment):
        try:
            return (mevcut or 0) + yeni.value
        except TypeError:
            return yeni.value
    return yeni


def _derin_birlestir(hedef: dict, veri: dict) -> dict:
    for anahtar, deger in veri.items():
        if deger is DELETE_FIELD:
            hedef.pop(anahtar, None)
        elif isinstance(deger, dict) and not isinstance(deger, Increment):
            alt = hedef.get(anahtar)
            hedef[anahtar] = _derin_birlestir(
                dict(alt) if isinstance(alt, dict) else {}, deger)
        else:
            hedef[anahtar] = _donustur(hedef.get(anahtar), deger)
    return hedef


def _duz_yaz(veri: dict) -> dict:
    """merge=False: dönüşümler boş dokümana uygulanır."""
    return _derin_birlestir({}, veri)


def _noktali_uygula(hedef: dict, yol: str, deger: Any) -> None:
    parcalar = yol.split(".")
    kova = hedef
    for parca in parcalar[:-1]:
        alt = kova.get(parca)
        if not isinstance(alt, dict):
            alt = {}
            kova[parca] = alt
        kova = alt
    son = parcalar[-1]
    if deger is DELETE_FIELD:
        kova.pop(son, None)
    elif isinstance(deger, dict):
        kova[son] = _derin_birlestir(
            dict(kova.get(son) or {}) if isinstance(kova.get(son), dict)
            else {}, deger)
    else:
        kova[son] = _donustur(kova.get(son), deger)


# ---------------------------------------------------------------------------
# Anlık görüntü / doküman referansı
# ---------------------------------------------------------------------------

class Anlik:
    def __init__(self, depo, yol: str, veri: dict | None):
        self._depo = depo
        self.reference = Dokuman(depo, yol)
        self.id = yol.rsplit("/", 1)[-1]
        self._veri = veri
        self.exists = veri is not None

    def to_dict(self):
        return dict(self._veri) if self._veri is not None else None

    def get(self, alan: str):
        return _alan_oku(self._veri or {}, alan)


class Dokuman:
    def __init__(self, depo, yol: str):
        self._depo = depo
        self.path = yol

    @property
    def id(self) -> str:
        return self.path.rsplit("/", 1)[-1]

    def get(self, transaction=None):
        return Anlik(self._depo, self.path, self._depo.docs.get(self.path))

    def set(self, veri: dict, merge: Any = False):
        self._depo.yazimlar.append(("set", self.path, dict(veri), merge))
        if merge is True:
            mevcut = dict(self._depo.docs.get(self.path) or {})
            self._depo.docs[self.path] = _derin_birlestir(mevcut, veri)
        elif merge:  # alan listesi: yalnız o üst alanlar ezilir
            mevcut = dict(self._depo.docs.get(self.path) or {})
            for alan in merge:
                if alan in veri:
                    mevcut[alan] = _duz_yaz({alan: veri[alan]})[alan]
            self._depo.docs[self.path] = mevcut
        else:
            self._depo.docs[self.path] = _duz_yaz(veri)

    def update(self, veri: dict):
        if self.path not in self._depo.docs:
            raise NotFound(f"Doküman yok: {self.path}")
        self._depo.yazimlar.append(("update", self.path, dict(veri), None))
        mevcut = dict(self._depo.docs[self.path])
        for yol, deger in veri.items():
            _noktali_uygula(mevcut, yol, deger)
        self._depo.docs[self.path] = mevcut

    def delete(self):
        self._depo.yazimlar.append(("delete", self.path, None, None))
        self._depo.docs.pop(self.path, None)

    def collection(self, ad: str):
        return Koleksiyon(self._depo, f"{self.path}/{ad}")


# ---------------------------------------------------------------------------
# Sorgu
# ---------------------------------------------------------------------------

class Sorgu:
    def __init__(self, depo, satirlar, siralar=None, imlec=None, n=None):
        self._depo = depo
        self._satirlar = list(satirlar)          # [(yol, veri)]
        self._siralar = list(siralar or [])      # [(alan, ters)]
        self._imlec = imlec                      # değer listesi ya da None
        self._n = n

    def _kopya(self, **degisim):
        alanlar = {"satirlar": self._satirlar, "siralar": self._siralar,
                   "imlec": self._imlec, "n": self._n}
        alanlar.update(degisim)
        return Sorgu(self._depo, alanlar["satirlar"], alanlar["siralar"],
                     alanlar["imlec"], alanlar["n"])

    # -- süzgeç --------------------------------------------------------
    def where(self, *args, filter=None):
        if filter is not None:
            alan, islem, deger = (filter.field_path, filter.op_string,
                                  filter.value)
        else:
            alan, islem, deger = args

        def uyar(satir) -> bool:
            x = _alan_oku(satir[1], alan)
            if islem == "==":
                return x == deger
            if islem == "!=":
                return x is not None and x != deger
            if islem == "in":
                return x in (deger or [])
            if islem == "array_contains":
                return isinstance(x, list) and deger in x
            if x is None:
                return False
            try:
                if islem == ">":
                    return x > deger
                if islem == ">=":
                    return x >= deger
                if islem == "<":
                    return x < deger
                if islem == "<=":
                    return x <= deger
            except TypeError:
                return False
            raise NotImplementedError(islem)
        return self._kopya(satirlar=[s for s in self._satirlar if uyar(s)])

    # -- sıralama / imleç / sınır ---------------------------------------
    def order_by(self, alan: str, direction: str = "ASCENDING"):
        return self._kopya(siralar=self._siralar
                           + [(alan, direction == "DESCENDING")])

    def limit(self, n: int):
        return self._kopya(n=n)

    def start_after(self, imlec):
        return self._kopya(imlec=imlec)

    # -- çözümleme -------------------------------------------------------
    def _etkin_siralar(self) -> list[tuple[str, bool]]:
        siralar = list(self._siralar)
        if not any(a == "__name__" for a, _ in siralar):
            # Firestore örtük `__name__` kuyruğunu son sıralamanın yönünde ekler.
            siralar.append(("__name__", siralar[-1][1] if siralar else False))
        return siralar

    def _deger(self, satir, alan: str) -> Any:
        if alan == "__name__":
            return satir[0].rsplit("/", 1)[-1]
        return _alan_oku(satir[1], alan)

    def _imlec_degerleri(self, siralar) -> list:
        imlec = self._imlec
        if isinstance(imlec, Anlik):
            return [imlec.id if a == "__name__" else imlec.get(a)
                    for a, _ in siralar]
        if isinstance(imlec, dict):
            return [imlec.get(a) for a, _ in siralar
                    if a in imlec][:len(siralar)]
        return list(imlec)

    def _cozumle(self):
        siralar = self._etkin_siralar()
        satirlar = [s for s in self._satirlar
                    if all(a == "__name__" or self._deger(s, a) is not None
                           for a, _ in siralar)]

        def kiyasla(x, y) -> int:
            for alan, ters in siralar:
                kx, ky = (_sira_anahtari(self._deger(x, alan)),
                          _sira_anahtari(self._deger(y, alan)))
                if kx == ky:
                    continue
                sonuc = -1 if kx < ky else 1
                return -sonuc if ters else sonuc
            return 0
        satirlar.sort(key=cmp_to_key(kiyasla))

        if self._imlec is not None:
            degerler = self._imlec_degerleri(siralar)

            def sonrasi(satir) -> bool:
                for (alan, ters), hedef in zip(siralar, degerler):
                    ks, kh = (_sira_anahtari(self._deger(satir, alan)),
                              _sira_anahtari(hedef))
                    if ks == kh:
                        continue
                    ileri = ks > kh
                    return (not ileri) if ters else ileri
                return False  # imlecin kendisi dahil değil
            satirlar = [s for s in satirlar if sonrasi(s)]

        if self._n is not None:
            satirlar = satirlar[:self._n]
        return satirlar

    def stream(self):
        return [Anlik(self._depo, yol, veri) for yol, veri in self._cozumle()]

    def get(self):
        return self.stream()

    def count(self):
        adet = len(self._cozumle())

        class _Sonuc:
            def get(self_inner):
                class _Deger:
                    value = adet
                return [[_Deger()]]
        return _Sonuc()


class Koleksiyon(Sorgu):
    _oto = 0

    def __init__(self, depo, yol: str):
        self._yol = yol
        super().__init__(depo, self._cocuklar(depo, yol))

    @staticmethod
    def _cocuklar(depo, yol: str):
        onek = yol + "/"
        return [(k, v) for k, v in depo.docs.items()
                if k.startswith(onek) and "/" not in k[len(onek):]]

    @property
    def id(self) -> str:
        return self._yol.rsplit("/", 1)[-1]

    def document(self, ad: str | None = None):
        if ad is None:
            Koleksiyon._oto += 1
            ad = f"oto-{Koleksiyon._oto}"
        return Dokuman(self._depo, f"{self._yol}/{ad}")


# ---------------------------------------------------------------------------
# İstemci
# ---------------------------------------------------------------------------

class SahteFirestore:
    """`docs`: yol -> veri. `yazimlar`: (tür, yol, veri, merge) izi —
    backfill'lerin "ikinci koşuda 0 yazım" sözü buradan ölçülür."""

    def __init__(self, docs: dict[str, dict] | None = None):
        self.docs: dict[str, dict] = dict(docs or {})
        self.yazimlar: list[tuple] = []

    def collection(self, ad: str):
        return Koleksiyon(self, ad)

    def document(self, yol: str):
        return Dokuman(self, yol)

    def collection_group(self, ad: str):
        satirlar = [(k, v) for k, v in self.docs.items()
                    if len(k.split("/")) >= 2 and k.split("/")[-2] == ad]
        return Sorgu(self, satirlar)

    def get_all(self, referanslar):
        return [ref.get() for ref in referanslar]

    def yazim_sayisi(self) -> int:
        return len(self.yazimlar)
