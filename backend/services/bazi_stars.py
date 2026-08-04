"""Shen Sha (神煞) — sembolik yıldızlar, v1 alt kümesi (Revize B4).

Beş yıldız seçildi: hepsi TEK SATIRLIK, tablo-denetlenebilir kurallar.
San Ming Tong Hui yüzlerce yıldız listeler; çoğunun kuralı kaynaktan
kaynağa oynar ve yorum yükü ağırdır. Bu beşi hem kuralı tartışmasız hem
okuma değeri yüksek olanlar: Tian Yi Gui Ren (koruyucu soylu), Tao Hua
(şeftali çiçeği), Yi Ma (sefer atı), Wen Chang (edebiyat) ve Kong Wang
(boşluk — formülle, tablosuz).

Her bulgu HANGİ kuraldan (basis) ve HANGİ sütunda bulunduğunu taşır:
denetlenebilirlik, "model uydurdu mu" sorusunun cevabını çıktının
kendisinde tutmaktır. Boş liste meşru bir sonuçtur ve öyle gösterilir.
"""
from __future__ import annotations

from typing import Any

#: Tian Yi Gui Ren — gövde → soylu dalları. Klasik kafiyeden
#: (甲戊庚牛羊 / 乙己鼠猴鄉 / 丙丁豬雞位 / 壬癸兔蛇藏 / 六辛逢馬虎).
#: Xin'in {Wu, Yin} aldığı yaygın sürüm seçildi ve testle donduruldu.
TIAN_YI: dict[int, tuple[int, int]] = {
    0: (1, 7), 4: (1, 7), 6: (1, 7),   # Jia, Wu, Geng → Chou, Wei
    1: (0, 8), 5: (0, 8),              # Yi, Ji → Zi, Shen
    2: (11, 9), 3: (11, 9),            # Bing, Ding → Hai, You
    8: (3, 5), 9: (3, 5),              # Ren, Gui → Mao, Si
    7: (6, 2),                         # Xin → Wu, Yin
}

#: Üçlü su/ateş/metal/ağaç gruplarından hedef dal: Tao Hua (grubun
#: "banyo" noktası) ve Yi Ma (grubun karşıt hareket noktası).
_TRINE_GROUPS: list[tuple[set[int], int, int]] = [
    # (grup dalları, tao_hua hedefi, yi_ma hedefi)
    ({8, 0, 4}, 9, 2),    # Shen-Zi-Chen (su)  → You / Yin
    ({2, 6, 10}, 3, 8),   # Yin-Wu-Xu (ateş)   → Mao / Shen
    ({5, 9, 1}, 6, 11),   # Si-You-Chou (metal)→ Wu / Hai
    ({11, 3, 7}, 0, 5),   # Hai-Mao-Wei (ağaç) → Zi / Si
]

#: Wen Chang — gün gövdesi → dal.
WEN_CHANG: dict[int, int] = {
    0: 5, 1: 6, 2: 8, 3: 9, 4: 8,
    5: 9, 6: 11, 7: 0, 8: 2, 9: 3,
}

#: Çıktıdaki yıldız anahtarları — prompt tabloları bu kümeyi kapsamalı
#: (dil izolasyon testi buradan okur).
STAR_KEYS = ("tian_yi", "tao_hua", "yi_ma", "wen_chang", "kong_wang")


def void_branches(day_cycle: int) -> tuple[int, int]:
    """Kong Wang: gün sütununun xun'unda (10'luk blok) boş kalan iki dal.

    60'lık döngüde her xun 10 gövde-dal çifti kapsar ama 12 dal vardır;
    açıkta kalan iki dal o xun'un "boşluğu"dur. Formül tablo istemez:
    xun başından 10 ve 11 adım ötedeki dallar.
    """
    xun_start = day_cycle - day_cycle % 10
    return ((xun_start + 10) % 12, (xun_start + 11) % 12)


def find_shen_sha(pillars: dict[str, Any],
                  day_cycle: int) -> list[dict[str, Any]]:
    """Natal sütunlarda beş yıldızı arar.

    `pillars` motorun ürettiği sözlük (saat None olabilir). Dönen her
    kayıt: {key, basis, branch(pinyin), pillar} — kural ve konum açıkta.
    """
    from services.bazi_service import BRANCHES

    dallar = {ad: p["branch"]["index"]
              for ad, p in pillars.items() if p is not None}
    gun_govde = pillars["day"]["stem"]["index"]
    yil_govde = pillars["year"]["stem"]["index"]
    gun_dal = dallar["day"]
    yil_dal = dallar["year"]

    bulgular: list[dict[str, Any]] = []

    def ekle(key: str, basis: str, hedef: int) -> None:
        for ad, dal_idx in dallar.items():
            if dal_idx == hedef:
                bulgular.append({
                    "key": key,
                    "basis": basis,
                    "branch": BRANCHES[hedef]["pinyin"],
                    "pillar": ad,
                })

    # Tian Yi: hem gün hem yıl gövdesinden aranır (klasik kullanım ikisi).
    for basis, govde in (("day_stem", gun_govde), ("year_stem", yil_govde)):
        for hedef in TIAN_YI[govde]:
            ekle("tian_yi", basis, hedef)

    # Tao Hua ve Yi Ma: hem yıl hem gün dalının üçlü grubundan.
    for basis, dal in (("day_branch", gun_dal), ("year_branch", yil_dal)):
        for grup, tao, yima in _TRINE_GROUPS:
            if dal in grup:
                ekle("tao_hua", basis, tao)
                ekle("yi_ma", basis, yima)

    # Wen Chang: yalnız gün gövdesinden.
    ekle("wen_chang", "day_stem", WEN_CHANG[gun_govde])

    # Kong Wang: gün sütununun xun boşlukları; gün dalı kendi xun'unda
    # boş olamaz, diğer sütunlarda aranır.
    for hedef in void_branches(day_cycle):
        for ad, dal_idx in dallar.items():
            if ad != "day" and dal_idx == hedef:
                bulgular.append({
                    "key": "kong_wang",
                    "basis": "day_pillar",
                    "branch": BRANCHES[hedef]["pinyin"],
                    "pillar": ad,
                })

    # Aynı yıldızın aynı sütunda iki temelden bulunması (ör. yıl ve gün
    # dalı aynı gruptaysa) tek kayda indirgenir — liste okuma yüzeyi,
    # kanıt defteri değil; basis ilk bulunandan kalır.
    tekil: dict[tuple[str, str], dict[str, Any]] = {}
    for b in bulgular:
        tekil.setdefault((b["key"], b["pillar"]), b)
    return list(tekil.values())
