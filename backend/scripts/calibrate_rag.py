"""RAG alaka eşiğinin kalibrasyonu (RD4) — `calibrate_synastry.py` deseni.

`_MIN_RELEVANCE` eski 267 parçalık korpusa göre ölçülmüştü (ilgili
0,71-0,84; alakasız 0,49-0,56 → eşik 0,62). Kitap korpusuyla iki şey
değişti: parça sayısı ~14 kat arttı ve EN gömme metinleri artık TR
başlık + anahtar kelime taşıyor (karma dil mutlak kosinüsü düşürür).
Bu betik iki dağılımı yeniden ölçer; eşik ÖLÇÜMLE güncellenir, elle
değil.

Kabul ölçütü: alakasız_maks + 0,03 <= eşik <= ilgili_min - 0,03.
İki bant çakışırsa betik bunu açıkça söyler — eşik tek başına yetmiyor
demektir.

Çalıştırma:  GEMINI_API_KEY=... .venv/Scripts/python.exe scripts/calibrate_rag.py
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from services import chart_query, rag_service  # noqa: E402

#: Korpus-İÇİ sondalar: konu tohumları + gerçek kullanıcı soruları +
#: kitaba özgü sorgular. Hepsinin korpusta gerçek karşılığı var.
_ILGILI = {
    "tr": [
        chart_query.topic_seed("money", "tr"),
        chart_query.topic_seed("vocation", "tr"),
        chart_query.topic_seed("relationship", "tr"),
        chart_query.topic_seed("family", "tr"),
        chart_query.topic_seed("temperament", "tr"),
        chart_query.topic_seed("timing", "tr"),
        "Param neden hiç birikmiyor? Satürn Oğlak 2. ev",
        "Babamla aram düzelir mi? Güneş Kova 4. ev",
        "Evlilik ve ortaklık; Venüs Terazi 7. ev",
        "Meslek ve statü; Merkür Başak 10. ev",
        "Onuncu evin anlamı ve meslek göstergeleri",
        "Ayın burçlardaki etkisi ve karakter",
        "Gezegenlerin doğaları ve nitelikleri",
        "Yükselen burcun bedene ve mizaca etkisi",
        "Sabit yıldızların etkisi",
    ],
    "en": [
        chart_query.topic_seed("money", "en"),
        chart_query.topic_seed("vocation", "en"),
        chart_query.topic_seed("relationship", "en"),
        chart_query.topic_seed("family", "en"),
        chart_query.topic_seed("temperament", "en"),
        chart_query.topic_seed("timing", "en"),
        "Why can't I save money? Saturn Capricorn 2nd house",
        "Will things with my father improve? Sun Aquarius 4th house",
        "Marriage and partnership; Venus Libra 7th house",
        "Profession and station; Mercury Virgo 10th house",
        "The meaning of the tenth house and vocation",
        "The Moon in the signs and character",
        "The natures and qualities of the planets",
        "The rising sign, body and temperament",
        "The influence of the fixed stars",
    ],
}

#: Alakasız sondalar — `rag_service._MIN_RELEVANCE` docstring'indeki
#: fikstürlerin genişletilmiş hâli.
_ALAKASIZ = {
    "tr": [
        "wifi şifremi nasıl sıfırlarım",
        "arabanın lastiği ne zaman değişmeli",
        "en iyi makarna tarifi hangisi",
        "python'da liste nasıl sıralanır",
        "yarın hava yağmurlu mu",
        "vergi iadesi başvurusu nereden yapılır",
        "telefonun şarjı neden çabuk bitiyor",
        "futbol maçı kaçta başlıyor",
    ],
    "en": [
        "how do I reset my wifi password",
        "when should car tires be replaced",
        "what is the best pasta recipe",
        "how to sort a list in python",
        "will it rain tomorrow",
        "where do I file a tax refund",
        "why does my phone battery drain fast",
        "what time does the football match start",
    ],
}


def _skorla(lang: str, sorgular: list[str]) -> list[float]:
    taban = rag_service.base_for(lang)
    skorlar: list[float] = []
    for sorgu in sorgular:
        if not sorgu.strip():
            continue
        q = taban._embed_query(sorgu)
        if q is None:
            print(f"  UYARI: sorgu gömülemedi: {sorgu[:40]}")
            continue
        ham = taban._matrix @ q
        skorlar.append(float(ham.max()))
    return skorlar


def main() -> int:
    for lang in ("tr", "en"):
        taban = rag_service.base_for(lang)
        if not taban.semantic_ready():
            print(f"[{lang}] vektör modu hazır değil — önce "
                  "build_embeddings.py çalıştırılmalı")
            return 1
        ilgili = _skorla(lang, _ILGILI[lang])
        alakasiz = _skorla(lang, _ALAKASIZ[lang])
        i_min, i_maks = min(ilgili), max(ilgili)
        a_min, a_maks = min(alakasiz), max(alakasiz)
        print(f"\n[{lang}] parça={taban.diagnostics()['chunks']}")
        print(f"  ilgili   ({len(ilgili)}): min {i_min:.3f}  maks {i_maks:.3f}")
        print(f"  alakasız ({len(alakasiz)}): min {a_min:.3f}  maks {a_maks:.3f}")
        alt, ust = a_maks + 0.03, i_min - 0.03
        if alt <= ust:
            print(f"  ÖNERİLEN EŞİK BANDI: [{alt:.3f}, {ust:.3f}] — "
                  f"orta nokta {(alt + ust) / 2:.3f}")
        else:
            print(f"  UYARI: bantlar çakışıyor (alakasız maks {a_maks:.3f} "
                  f"> ilgili min {i_min:.3f} - 0.06) — eşik tek başına "
                  "yetmez, sorgu kalitesine bak")
        print(f"  mevcut _MIN_RELEVANCE = {rag_service._MIN_RELEVANCE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
