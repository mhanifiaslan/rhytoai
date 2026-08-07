"""GeoNames dump'ından gazetteer + mobil şehir/ülke listeleri üretir (O1).

Neden: eski gazetteer elle yazılmış ~81 anahtardı — 81 TR ilinden yalnız
33'ü vardı, gerisi sessizce İstanbul'a düşüyordu; "münih/brüksel/zürih"
anahtarları normalize hatasıyla hiç erişilemiyordu. Kullanıcı kararı:
GeoNames verisi İNDİRİLİP kendi veritabanımıza alınır (API değil) ve
yalnız astrolojinin gerektirdiği detay taşınır: şehir düzeyinde ad,
ülke, il, koordinat, saat dilimi. Listede olmayan yer serbest metinle
yazılabilir; sunucu onu bugünkü gibi fallback+beyanla karşılar.

Kaynak: https://download.geonames.org/export/dump/
  - cities15000.zip  (nüfusu 15.000+ tüm yerleşimler, ~30k kayıt)
  - admin1CodesASCII.txt (il/eyalet adları — "Ereğli, Konya" ayrımı)
  - countryInfo.txt  (ISO2 + telefon kodu + ülke adı)
Lisans: CC-BY 4.0 — künye knowledge/SOURCES.md'de, uygulama içi atıf
hukuk sayfasında. Veri koda değil data dosyalarına gider.

Çıktılar (üçü de AYNI çalışmadan — mobil liste sunucunun çözebildiğinin
alt kümesidir, ayrışamaz):
  backend/data/gazetteer.json          (çözümleme: ad→koordinat+tz)
  apps/mobile/assets/data/cities.json  (arama UI: ad/ülke/il/nüfus)
  apps/mobile/assets/data/countries.json (ülke adı TR+EN + telefon kodu)

Kullanım:
    .venv/Scripts/python.exe scripts/build_gazetteer.py [--skip-download]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import unicodedata
import zipfile
from datetime import date
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent          # backend/
REPO = ROOT.parent
RAW = ROOT / "data" / "raw"
GAZETTEER_OUT = ROOT / "data" / "gazetteer.json"
CITIES_OUT = REPO / "apps" / "mobile" / "assets" / "data" / "cities.json"
COUNTRIES_OUT = REPO / "apps" / "mobile" / "assets" / "data" / "countries.json"

BASE = "https://download.geonames.org/export/dump"

#: Küratörlü ek eş adlar: alternatenames sütununda bulunamayan, sütun
#: sırası/kesmesi yüzünden kaçabilecek ya da il adı ≠ merkez adı olan
#: durumlar. Bu tablo GARANTİ katmanıdır: organik indeksleme ne yaparsa
#: yapsın buradaki adlar her zaman çözülür (doğrulama assert'leri de
#: bunun üstünde koşar). Anahtar: kullanıcı yazımı, değer: GeoNames adı.
_EXTRA_ALTNAMES: dict[str, str] = {
    # İl adı ≠ merkez adı + yaygın kısaltmalar
    "kocaeli": "İzmit",
    "sakarya": "Adapazarı",
    "hatay": "Antakya",
    "antep": "Gaziantep",
    "urfa": "Şanlıurfa",
    "maras": "Kahramanmaraş",
    "afyon": "Afyonkarahisar",
    "lefkosa": "Nicosia",
    # Türkçe egzonimler (garanti)
    "londra": "London",
    "moskova": "Moscow",
    "kahire": "Cairo",
    "viyana": "Vienna",
    "riyad": "Riyadh",
    "zürih": "Zürich",
    "münih": "Munich",
    "brüksel": "Brussels",
    "pekin": "Beijing",
    "atina": "Athens",
    "mekke": "Mecca",
    "bakü": "Baku",
    "tahran": "Tehran",
    "new york": "New York City",
}

#: 81 il — merkez adı il adından farklıysa parantezsiz merkez adı esas.
#: Doğrulama: bu adların HEPSİ üretilen indekste çözülmeli.
_TR_ILLERI = [
    "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Amasya", "Ankara",
    "Antalya", "Artvin", "Aydın", "Balıkesir", "Bilecik", "Bingöl",
    "Bitlis", "Bolu", "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum",
    "Denizli", "Diyarbakır", "Edirne", "Elazığ", "Erzincan", "Erzurum",
    "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane", "Hakkari", "Hatay",
    "Isparta", "Mersin", "İstanbul", "İzmir", "Kars", "Kastamonu",
    "Kayseri", "Kırklareli", "Kırşehir", "Kocaeli", "Konya", "Kütahya",
    "Malatya", "Manisa", "Kahramanmaraş", "Mardin", "Muğla", "Muş",
    "Nevşehir", "Niğde", "Ordu", "Rize", "Sakarya", "Samsun", "Siirt",
    "Sinop", "Sivas", "Tekirdağ", "Tokat", "Trabzon", "Tunceli",
    "Şanlıurfa", "Uşak", "Van", "Yozgat", "Zonguldak", "Aksaray",
    "Bayburt", "Karaman", "Kırıkkale", "Batman", "Şırnak", "Bartın",
    "Ardahan", "Iğdır", "Yalova", "Karabük", "Kilis", "Osmaniye",
    "Düzce",
]

#: Eski elle yazılmış gazetteer'in TÜM anahtarları — geriye uyumluluk:
#: bugüne kadar çözülen hiçbir ad çözülmez hâle gelmemeli.
_ESKI_ANAHTARLAR = [
    "istanbul", "ankara", "izmir", "bursa", "antalya", "adana", "konya",
    "gaziantep", "sanliurfa", "mersin", "diyarbakir", "kayseri",
    "eskisehir", "samsun", "denizli", "malatya", "trabzon", "erzurum",
    "van", "batman", "elazig", "kahramanmaras", "manisa", "sivas",
    "balikesir", "aydin", "tekirdag", "sakarya", "mugla", "mardin",
    "hatay", "ordu", "kocaeli", "izmit", "london", "londra", "new york",
    "los angeles", "paris", "berlin", "amsterdam", "moscow", "moskova",
    "dubai", "tokyo", "beijing", "pekin", "delhi", "mumbai", "cairo",
    "kahire", "baku", "bakü", "tashkent", "sydney", "sao paulo",
    "mexico city", "toronto", "chicago", "athens", "atina", "sofia",
    "tahran", "tehran", "riyadh", "riyad", "mecca", "mekke", "frankfurt",
    "munich", "münih", "vienna", "viyana", "brussels", "brüksel",
    "stockholm", "zurich", "zürih", "lefkosa", "nicosia",
]

#: Türkçe egzonim doğrulama listesi (kesme riskine karşı bekçi).
_EGZONIMLER = ["münih", "brüksel", "zürih", "kahire", "moskova", "pekin",
               "atina", "viyana", "riyad", "mekke", "bakü", "tahran",
               "londra"]

#: Ülke adlarının Türkçesi (ISO2 → ad). Tam liste değil; eksik kalan
#: ülke İngilizce adıyla görünür — yanlış değil, yalnız çevrilmemiş.
_ULKE_TR: dict[str, str] = {
    "TR": "Türkiye", "DE": "Almanya", "US": "Amerika Birleşik Devletleri",
    "GB": "Birleşik Krallık", "FR": "Fransa", "NL": "Hollanda",
    "BE": "Belçika", "AT": "Avusturya", "CH": "İsviçre", "SE": "İsveç",
    "NO": "Norveç", "DK": "Danimarka", "FI": "Finlandiya", "IT": "İtalya",
    "ES": "İspanya", "PT": "Portekiz", "GR": "Yunanistan",
    "BG": "Bulgaristan", "RO": "Romanya", "HU": "Macaristan",
    "PL": "Polonya", "CZ": "Çekya", "SK": "Slovakya", "SI": "Slovenya",
    "HR": "Hırvatistan", "RS": "Sırbistan", "BA": "Bosna-Hersek",
    "MK": "Kuzey Makedonya", "AL": "Arnavutluk", "XK": "Kosova",
    "ME": "Karadağ", "RU": "Rusya", "UA": "Ukrayna", "BY": "Belarus",
    "MD": "Moldova", "GE": "Gürcistan", "AM": "Ermenistan",
    "AZ": "Azerbaycan", "KZ": "Kazakistan", "UZ": "Özbekistan",
    "TM": "Türkmenistan", "KG": "Kırgızistan", "TJ": "Tacikistan",
    "IR": "İran", "IQ": "Irak", "SY": "Suriye", "LB": "Lübnan",
    "IL": "İsrail", "PS": "Filistin", "JO": "Ürdün",
    "SA": "Suudi Arabistan", "AE": "Birleşik Arap Emirlikleri",
    "QA": "Katar", "KW": "Kuveyt", "BH": "Bahreyn", "OM": "Umman",
    "YE": "Yemen", "EG": "Mısır", "LY": "Libya", "TN": "Tunus",
    "DZ": "Cezayir", "MA": "Fas", "SD": "Sudan", "ET": "Etiyopya",
    "SO": "Somali", "KE": "Kenya", "NG": "Nijerya", "GH": "Gana",
    "ZA": "Güney Afrika", "TZ": "Tanzanya", "UG": "Uganda",
    "CN": "Çin", "JP": "Japonya", "KR": "Güney Kore", "KP": "Kuzey Kore",
    "IN": "Hindistan", "PK": "Pakistan", "BD": "Bangladeş",
    "AF": "Afganistan", "LK": "Sri Lanka", "NP": "Nepal", "MM": "Myanmar",
    "TH": "Tayland", "VN": "Vietnam", "MY": "Malezya", "SG": "Singapur",
    "ID": "Endonezya", "PH": "Filipinler", "AU": "Avustralya",
    "NZ": "Yeni Zelanda", "CA": "Kanada", "MX": "Meksika",
    "BR": "Brezilya", "AR": "Arjantin", "CL": "Şili", "CO": "Kolombiya",
    "PE": "Peru", "VE": "Venezuela", "UY": "Uruguay", "EC": "Ekvador",
    "BO": "Bolivya", "PY": "Paraguay", "CU": "Küba",
    "DO": "Dominik Cumhuriyeti", "CY": "Kıbrıs", "MT": "Malta",
    "IS": "İzlanda", "IE": "İrlanda", "LU": "Lüksemburg", "EE": "Estonya",
    "LV": "Letonya", "LT": "Litvanya", "MN": "Moğolistan",
}


def _normalize(s: str) -> str:
    """geo_service._normalize ile AYNI kural — indeks bu anahtarla kurulur."""
    s = s.strip().lower().replace("ı", "i")
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def _indir(ad: str) -> Path:
    RAW.mkdir(parents=True, exist_ok=True)
    hedef = RAW / ad
    if hedef.exists():
        print(f"  {ad}: mevcut ({hedef.stat().st_size:,} B), atlanıyor")
        return hedef
    print(f"  {ad} indiriliyor…")
    with httpx.stream("GET", f"{BASE}/{ad}", timeout=120,
                      follow_redirects=True) as r:
        r.raise_for_status()
        with open(hedef, "wb") as f:
            for parca in r.iter_bytes():
                f.write(parca)
    print(f"  {ad}: {hedef.stat().st_size:,} B")
    return hedef


def _latin_mi(s: str) -> bool:
    """Alternatif ad indekse girmeye değer mi — Latin dışı yazılar
    (Kiril/Arap/Çin...) Türkçe kullanıcı aramasında anahtar olamaz."""
    n = _normalize(s)
    return bool(n) and all(c.isascii() and (c.isalpha() or c in " -'.")
                           for c in n)


def calistir(indirme_atla: bool) -> None:
    print("== GeoNames dump'ları ==")
    if not indirme_atla:
        _indir("cities15000.zip")
        _indir("admin1CodesASCII.txt")
        _indir("countryInfo.txt")

    # --- admin1 kodu → il/eyalet adı ---
    admin1: dict[str, str] = {}
    for satir in (RAW / "admin1CodesASCII.txt").read_text(
            encoding="utf-8").splitlines():
        parcalar = satir.split("\t")
        if len(parcalar) >= 2:
            admin1[parcalar[0]] = parcalar[1]

    # --- şehirler ---
    with zipfile.ZipFile(RAW / "cities15000.zip") as z:
        metin = z.read("cities15000.txt").decode("utf-8")

    kayitlar: list[dict] = []
    for satir in metin.splitlines():
        c = satir.split("\t")
        if len(c) < 18:
            continue
        ad, ulke = c[1], c[8]
        kayitlar.append({
            "name": ad,
            "ascii": c[2],
            "alts": c[3].split(",") if c[3] else [],
            "lat": round(float(c[4]), 4),
            "lng": round(float(c[5]), 4),
            "feature": c[7],
            "country": ulke,
            "admin1": admin1.get(f"{ulke}.{c[10]}", ""),
            "pop": int(c[14] or 0),
            "tz": c[17],
        })

    # Sıralama: başkentler önce (aynı adlı iki şehirde başkent kazansın),
    # sonra nüfus — indeksteki aday listeleri bu sırayı miras alır.
    kayitlar.sort(key=lambda k: (k["feature"] != "PPLC", -k["pop"]))

    # --- indeks: normalize ad → aday kayıt indeksleri ---
    indeks: dict[str, list[int]] = {}

    def ekle(anahtar: str, i: int) -> None:
        n = _normalize(anahtar)
        if not n or len(n) < 2:
            return
        liste = indeks.setdefault(n, [])
        if i not in liste:
            liste.append(i)

    for i, k in enumerate(kayitlar):
        ekle(k["name"], i)
        ekle(k["ascii"], i)
        # Alternatif adlar: Latin olanlar, kayıt başına en fazla 40 YENİ
        # anahtar (indeks şişmesin; megakentlerde 100+ alternatif var).
        # Sayaç yalnız gerçekten yeni normalize anahtar eklendiğinde artar
        # — yineleyen yazımlar hakkı yemez. Türkçe egzonimlerin garantisi
        # bu sınırda değil _EXTRA_ALTNAMES tablosunda.
        gorulen = {_normalize(k["name"]), _normalize(k["ascii"])}
        sayac = 0
        for alt in k["alts"]:
            if not _latin_mi(alt):
                continue
            n = _normalize(alt)
            if n in gorulen:
                continue
            gorulen.add(n)
            ekle(alt, i)
            sayac += 1
            if sayac >= 40:
                break

    # Ad → İLK kayıt (liste başkent-önce + nüfus sıralı olduğundan ilk
    # görülen en olası şehirdir). Sondan yazan sözlük kurma hatası
    # "moskova"yı Moscow-Idaho'ya bağlamıştı — aynı adlı kasabalar çok.
    ad_indeksi: dict[str, int] = {}
    for i, k in enumerate(kayitlar):
        ad_indeksi.setdefault(_normalize(k["name"]), i)
    for takma, gercek in _EXTRA_ALTNAMES.items():
        hedef = ad_indeksi.get(_normalize(gercek))
        if hedef is not None:
            ekle(takma, hedef)
            # Küratörlü ad öncelikli olsun: listenin başına al.
            indeks[_normalize(takma)].remove(hedef)
            indeks[_normalize(takma)].insert(0, hedef)

    # --- doğrulamalar (yazmadan ÖNCE — bozuk veri dosyaya inmesin) ---
    print("== Doğrulamalar ==")
    hatalar: list[str] = []

    def cozuluyor(ad: str, ulke: str | None = None) -> bool:
        adaylar = indeks.get(_normalize(ad), [])
        if ulke:
            adaylar = [i for i in adaylar
                       if kayitlar[i]["country"] == ulke] or adaylar
        return bool(adaylar)

    for il in _TR_ILLERI:
        if not cozuluyor(il, "TR"):
            hatalar.append(f"TR ili çözülemedi: {il}")
    for ad in _EGZONIMLER:
        if not cozuluyor(ad):
            hatalar.append(f"egzonim çözülemedi: {ad}")
    for ad in _ESKI_ANAHTARLAR:
        if not cozuluyor(ad):
            hatalar.append(f"eski gazetteer anahtarı çözülemedi: {ad}")
    if hatalar:
        for h in hatalar:
            print(f"  HATA: {h}")
        sys.exit(1)
    print(f"  81 il OK, egzonimler OK, eski {len(_ESKI_ANAHTARLAR)} "
          "anahtar OK")

    meta = {"source": "GeoNames (geonames.org), CC-BY 4.0",
            "dataset": "cities15000",
            "snapshotDate": date.today().isoformat(),
            "count": len(kayitlar)}

    # --- backend/data/gazetteer.json ---
    GAZETTEER_OUT.parent.mkdir(parents=True, exist_ok=True)
    gazetteer = {
        "meta": meta,
        # [ad, ülke, il, lat, lng, tz, nüfus]
        "cities": [[k["name"], k["country"], k["admin1"], k["lat"],
                    k["lng"], k["tz"], k["pop"]] for k in kayitlar],
        "index": indeks,
    }
    GAZETTEER_OUT.write_text(
        json.dumps(gazetteer, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")
    print(f"  gazetteer.json: {len(kayitlar):,} kayıt, "
          f"{GAZETTEER_OUT.stat().st_size / 1e6:.1f} MB")

    # --- apps/mobile/assets/data/cities.json ---
    # Mobil yalnız GÖSTERİM için veri taşır: ad, ülke, il, nüfus.
    # Koordinat/tz gitmez — çözüm sunucuda, aynı kümeden (alt küme garantisi
    # yapısal: iki dosya aynı kayıtlardan üretiliyor).
    CITIES_OUT.parent.mkdir(parents=True, exist_ok=True)
    CITIES_OUT.write_text(
        json.dumps({"meta": meta,
                    "cities": [[k["name"], k["country"], k["admin1"],
                                k["pop"]] for k in kayitlar]},
                   ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")
    print(f"  cities.json: {CITIES_OUT.stat().st_size / 1e6:.1f} MB")

    # --- countries.json ---
    ulkeler: list[list[str]] = []
    for satir in (RAW / "countryInfo.txt").read_text(
            encoding="utf-8").splitlines():
        if satir.startswith("#"):
            continue
        c = satir.split("\t")
        if len(c) < 16 or not c[0]:
            continue
        iso2, ad_en, telefon = c[0], c[4], c[12]
        # NANP tuhaflığı: "1-809 and 1-829" → ilk kod alınır.
        telefon = telefon.split(" ")[0].split("-")[0].strip()
        if not telefon:
            continue
        ulkeler.append([iso2, telefon, ad_en, _ULKE_TR.get(iso2, ad_en)])
    ulkeler.sort(key=lambda u: u[3])
    COUNTRIES_OUT.write_text(
        json.dumps({"meta": {"source": meta["source"],
                             "snapshotDate": meta["snapshotDate"]},
                    "countries": ulkeler},
                   ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")
    print(f"  countries.json: {len(ulkeler)} ülke, "
          f"{COUNTRIES_OUT.stat().st_size / 1e3:.0f} KB")
    print("Tamam.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--skip-download", action="store_true",
                   help="data/raw altındaki mevcut dosyaları kullan")
    calistir(p.parse_args().skip_download)
