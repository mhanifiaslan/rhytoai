"""Day Master gücü, mevsimsel durum ve yararlı element (Revize B3).

BaZi'nin özü "haritada hangi element eksik" değil, "Günün Efendisi bu
mevsimde, bu köklerle GÜÇLÜ mü zayıf mı" sorusudur — yararlı element
(yong shen) seçimi de bu hükme dayanır. Bu modül o hükmü verir.

## Tasarım ilkeleri

* **Deterministik ve denetlenebilir.** Hüküm bir puanlamadan çıkar ve
  puanların DÖKÜMÜ çıktıda durur: "neden güçlü" sorusunun cevabı her an
  gösterilebilir. LLM'e sordurulmaz — sorulsaydı aynı harita iki ayrı
  gün iki ayrı hüküm alabilirdi.
* **Ay komutu en ağır faktör.** Klasik kural: mevsim (ay dalı) Day
  Master'ı besliyorsa başka hiçbir şeye bakmadan güçlüye yaklaşır.
  Ağırlıklar v1 kalibrasyonudur; hükmü klasikçe bilinen altın haritalarla
  test edilir ve eşik değişimi calc_version artırımı gerektirir.
* **Bilinçli sınır:** sütunlar arası birleşme/dönüşüm (he/sanhe/chong)
  bu hesaba GİRMEZ. Kombinasyon hesabı klasiklerin en tartışmalı alanı;
  doğrulanamayan derinliği sessizce ürüne sızdırmak yerine kapsam beyanı
  veriyoruz (`scope_note_key` → prompt'a girer, model kombinasyon
  biliyormuş gibi konuşamaz).
"""
from __future__ import annotations

from typing import Any

#: Ay dalı → mevsim elementi. Toprak ayları (Chen/Wei/Xu/Chou) mevsim
#: geçişleridir ve toprağın hükümran olduğu dönemler sayılır.
SEASON_OF_BRANCH = {
    2: "wood", 3: "wood",          # Yin, Mao — ilkbahar
    5: "fire", 6: "fire",          # Si, Wu — yaz
    8: "metal", 9: "metal",        # Shen, You — sonbahar
    11: "water", 0: "water",       # Hai, Zi — kış
    4: "earth", 7: "earth", 10: "earth", 1: "earth",  # geçiş ayları
}

#: Mevsimsel durum puanları (旺相休囚死). Ay komutu 40 puanlık tek blok:
#: destek payı duruma göre, kalan (40 − puan) yük tarafına yazılır — ay
#: dalı hiçbir haritada "nötr" değildir.
STATE_POINTS = {"wang": 40, "xiang": 30, "xiu": 15, "qiu": 5, "si": 0}

#: Konum çarpanları: ay dalı mevsimsel komutu taşır (1.5), gün dalı Day
#: Master'ın kendi evi (1.2), saat 1.0, yıl en uzak (0.8).
POSITION_WEIGHT = {"month": 1.5, "day": 1.2, "hour": 1.0, "year": 0.8}

#: Hüküm eşikleri: destek oranı ≥ 0.58 güçlü, ≤ 0.42 zayıf, arası dengeli.
#: 0.5 çevresinde simetrik bant: dengeli hüküm "bilmiyorum"un dürüst
#: karşılığıdır ve düşük güvenle işaretlenir.
STRONG_THRESHOLD = 0.58
WEAK_THRESHOLD = 0.42


def season_state(season_element: str, target_element: str) -> str:
    """Elementin mevsim içindeki durumu — tek kuraldan türetilir.

    Mevsim elementi hükümran (wang); onun ürettiği destekli (xiang);
    onu üreten dinlenmede (xiu); onu kontrol eden kısıtlı (qiu);
    kontrol ettiği sönük (si).
    """
    from services.bazi_service import _element_relation
    if season_element == target_element:
        return "wang"
    iliski = _element_relation(season_element, target_element)
    return {"i_produce": "xiang",     # mevsim onu üretiyor
            "produces_me": "xiu",     # o mevsimi üretiyor
            "controls_me": "qiu",     # o mevsimi kontrol ediyor
            "i_control": "si"}[iliski]  # mevsim onu kontrol ediyor


def _iliski_tarafi(rel: str) -> str:
    """İlişki destek mi yük mü: aynı element ve beni üreten destekler;
    boşaltan (benim ürettiğim), servet (kontrol ettiğim) ve otorite
    (beni kontrol eden) Day Master'dan güç ALIR."""
    return "support" if rel in ("same", "produces_me") else "burden"


def assess_strength(pillars: dict[str, Any], day_stem: int,
                    distribution: dict[str, float]) -> dict[str, Any]:
    """Day Master gücü + yararlı element hükmü.

    `pillars` gizli kökleri iliştirilmiş olmalı (attach_hidden_stems).
    Dönen `components` listesi hükmün TAM dökümüdür — API'de görünür.
    """
    from services.bazi_service import STEMS, _element_relation

    dm_element = STEMS[day_stem]["element"]
    destek = 0.0
    yuk = 0.0
    components: list[dict[str, Any]] = []

    # 1) Ay komutu — en ağır tek faktör.
    ay = pillars.get("month")
    mevsim = SEASON_OF_BRANCH[ay["branch"]["index"]]
    durum = season_state(mevsim, dm_element)
    puan = STATE_POINTS[durum]
    destek += puan
    yuk += STATE_POINTS["wang"] - puan
    components.append({"source": "month_command", "state": durum,
                       "side": "support" if puan >= 20 else "burden",
                       "points": float(puan)})

    # 2) Kökler: her dalın gizli gövdeleri, ağırlık × konum çarpanı.
    for ad, p in pillars.items():
        if p is None:
            continue
        konum = POSITION_WEIGHT[ad]
        for h in p["branch"]["hidden"]:
            rel = _element_relation(dm_element, h["element"])
            taraf = _iliski_tarafi(rel)
            temel = {"same": 20.0, "produces_me": 12.0}.get(rel, 14.0)
            pts = round(temel * h["weight"] * konum, 1)
            if taraf == "support":
                destek += pts
            else:
                yuk += pts
            components.append({"source": f"root:{ad}:{h['pinyin']}",
                               "relation": rel, "side": taraf,
                               "points": pts})

    # 3) Gövdeler (gün gövdesi Day Master'ın kendisi — atlanır).
    for ad in ("year", "month", "hour"):
        p = pillars.get(ad)
        if p is None:
            continue
        elem = p["stem"]["element"]
        rel = _element_relation(dm_element, elem)
        taraf = _iliski_tarafi(rel)
        yakinlik = 2.0 if ad in ("month", "hour") else 0.0
        temel = {"same": 10.0, "produces_me": 8.0}.get(rel, 10.0)
        pts = temel + yakinlik
        if taraf == "support":
            destek += pts
        else:
            yuk += pts
        components.append({"source": f"stem:{ad}:{p['stem']['pinyin']}",
                           "relation": rel, "side": taraf, "points": pts})

    oran = destek / (destek + yuk) if (destek + yuk) > 0 else 0.5
    if oran >= STRONG_THRESHOLD:
        hukum = "strong"
    elif oran <= WEAK_THRESHOLD:
        hukum = "weak"
    else:
        hukum = "balanced"

    return {
        "verdict": hukum,
        "ratio": round(oran, 3),
        "support": round(destek, 1),
        "burden": round(yuk, 1),
        "season_state": durum,
        # En ağır bileşenler önce: UI/prompt "neden" sorusunu ilk üç
        # kalemden cevaplayabilsin.
        "components": sorted(components, key=lambda c: -c["points"]),
        **_useful_elements(hukum, dm_element, pillars, distribution),
        "scope_note_key": "combinations_ignored",
    }


def _useful_elements(hukum: str, dm_element: str,
                     pillars: dict[str, Any],
                     distribution: dict[str, float]) -> dict[str, Any]:
    """Yararlı element v1: denge kuralı + iklim ekseni.

    Bilinçli sığlık: Qiong Tong Bao Jian'ın 120 hücreli gövde×ay tablosu
    v1'e GİRMEZ — doğrulanabilir altın vektörü olmayan derinlik sızdırılmaz.
    İncelik korpusta yorum malzemesi olarak durur (B7); burada yalnız
    tartışmasız eksen var: kış haritası ısı, yaz haritası su ister.
    """
    from services.bazi_service import _ELEMENT_ORDER

    i = _ELEMENT_ORDER.index(dm_element)
    ureten = _ELEMENT_ORDER[(i - 1) % 5]      # beni üreten (kaynak)
    urettigim = _ELEMENT_ORDER[(i + 1) % 5]   # boşaltan (çıktı)
    kontrol_ettigim = _ELEMENT_ORDER[(i + 2) % 5]  # servet
    kontrol_eden = _ELEMENT_ORDER[(i + 3) % 5]     # otorite

    if hukum == "strong":
        # Boşaltan/servet/otorite adayları — haritada KÖKÜ olan öne:
        # yokluğu düzenleyici yapmak, olmayan ilacı yazmak olur.
        adaylar = sorted([urettigim, kontrol_ettigim, kontrol_eden],
                         key=lambda e: -distribution.get(e, 0.0))
        favorable = adaylar[:2]
        unfavorable = [dm_element, ureten]
        confidence = "normal"
    elif hukum == "weak":
        favorable = [ureten, dm_element]
        unfavorable = [kontrol_eden, urettigim]
        confidence = "normal"
    else:
        # Dengeli: kesin reçete YOK — düşük güvenle boş bırakılır; iklim
        # ekseni varsa tek dürüst öneri odur.
        favorable = []
        unfavorable = []
        confidence = "low"

    # İklim ekseni: ay dalı kışsa ateş düzenleyici, yazsa su.
    ay_dali = pillars["month"]["branch"]["index"]
    climate = None
    climate_element = None
    if ay_dali in (11, 0, 1):       # Hai, Zi, Chou
        climate, climate_element = "cold", "fire"
    elif ay_dali in (5, 6, 7):      # Si, Wu, Wei
        climate, climate_element = "hot", "water"

    return {
        "favorable_elements": favorable,
        "unfavorable_elements": unfavorable,
        "confidence": confidence,
        "climate": climate,
        "climate_element": climate_element,
    }
