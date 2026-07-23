"""Rapor / Prompt Mühendisliği Servisi.

Ham hesaplama çıktıları (astroloji, BaZi, yüz, I Ching, gökyüzü) doğrudan
LLM'e verilmez; burada yapılandırılmış prompt şablonlarına dönüştürülür,
RAG bağlamı eklenir, Gemini'ye gönderilir ve sonuç kullanıcı+gün bazında
önbelleklenir (maliyet kontrolü).
"""
from __future__ import annotations

import datetime as dt
import json
import logging
from typing import Any

from core import cache
from services import gemini_service
from services.rag_service import retrieve_context

logger = logging.getLogger(__name__)


def _cached_generate(cache_key: str, prompt: str, fallback: str,
                     ttl_seconds: int = 24 * 3600) -> dict[str, Any]:
    cached = cache.get(cache_key)
    if cached is not None:
        return {"text": cached, "cached": True}

    text = gemini_service.generate(prompt)
    if text:
        cache.set(cache_key, text, ttl_seconds=ttl_seconds)
        return {"text": text, "cached": False}
    return {"text": fallback, "cached": False, "fallback": True}


def daily_reading(user_id: str, natal: dict[str, Any], sky: dict[str, Any]) -> dict[str, Any]:
    """Kişiye özel günlük kozmik yorum: natal harita x güncel gökyüzü."""
    today = dt.date.today().isoformat()
    cache_key = f"daily-{user_id}-{today}"

    rag = retrieve_context(
        f"{natal.get('sun_sign', '')} güneş {natal.get('moon_sign', '')} ay burcu "
        f"gezegen transit yorumu mizaç"
    )
    retros = ", ".join(sky.get("retrogrades", [])) or "yok"
    aspects = "; ".join(
        f"{a['p1']}-{a['p2']} {a['aspect']}" for a in sky.get("aspects", [])[:5]
    )
    moon = sky.get("moon_phase", {})

    prompt = f"""
GÖREV: Kullanıcı için bugüne özel, 150-200 kelimelik bir "günlük kozmik okuma" yaz.

HESAPLANMIŞ NATAL VERİ:
- Güneş: {natal.get('sun_sign')} | Ay: {natal.get('moon_sign')} | Yükselen: {natal.get('ascendant')}

BUGÜNÜN GERÇEK GÖKYÜZÜ (Swiss Ephemeris + NASA JPL):
- Tarih: {today}
- Ay evresi: {moon.get('name')} {moon.get('emoji')} (aydınlanma %{moon.get('illumination')})
- Retro gezegenler: {retros}
- Günün önemli açıları: {aspects}

KAYNAK PASAJLARI:
{rag}

Yorum, natal konumlar ile bugünkü gökyüzünü ÇARPIŞTIRSIN; genel geçer burç
yorumu olmasın. Somut bir günlük tema + bir pratik öneri ver.
"""
    fallback = (
        f"Bugün Ay {moon.get('name', 'yolculuğunda')} evresinde ilerliyor. "
        f"{natal.get('sun_sign', 'Güneş burcun')} özün ve {natal.get('ascendant', 'yükselenin')} "
        "dış dünyaya açılan kapınla, bugün iç sesinle dış adımlarını hizalamak için güçlü bir gün. "
        "Küçük ama kararlı bir adım at; gökyüzü sabırlı olanı ödüllendiriyor."
    )
    return _cached_generate(cache_key, prompt, fallback)


def natal_report(user_id: str, natal: dict[str, Any]) -> dict[str, Any]:
    """Derinlemesine doğum haritası raporu (kullanıcı başına bir kez, 30 gün önbellek)."""
    cache_key = f"natal-report-{user_id}-{natal.get('sun_sign')}-{natal.get('ascendant')}"

    points = "\n".join(
        f"- {p['name_tr']}: {p['sign_tr']} {p['position']}° "
        f"(Ev {p.get('house') or '?'}{', Retro' if p.get('retrograde') else ''})"
        for p in natal.get("points", [])[:12]
    )
    aspects = "\n".join(
        f"- {a['p1_tr']} {a['aspect_tr']} {a['p2_tr']} (orb {a['orbit']}°)"
        for a in natal.get("aspects", [])[:10]
    )
    rag = retrieve_context(
        f"{natal.get('sun_sign')} güneş burcu mizaç gezegen ev yerleşimi karakter analizi"
    )

    prompt = f"""
GÖREV: Aşağıdaki natal harita verilerinden 400-500 kelimelik derin bir doğum
haritası analizi yaz. Bölümler: (1) Öz Kimlik (Güneş/Ay/Yükselen üçlüsü),
(2) Gezegen vurguları, (3) Önemli açılar ve iç dinamikler, (4) Yaşam teması
ve potansiyel.

NATAL HARİTA (Swiss Ephemeris hassasiyetinde):
Güneş: {natal.get('sun_sign')} | Ay: {natal.get('moon_sign')} | Yükselen: {natal.get('ascendant')}

GEZEGENLER:
{points}

AÇILAR:
{aspects}

KAYNAK PASAJLARI (kadim gelenekten harmanla):
{rag}
"""
    fallback = (
        f"Güneşin {natal.get('sun_sign')}, Ayın {natal.get('moon_sign')} ve yükselenin "
        f"{natal.get('ascendant')}. Bu üçlü; öz kimliğin, duygusal dünyan ve dışa dönük "
        "maskenin haritasını çizer. Detaylı yorum için lütfen daha sonra tekrar dene."
    )
    return _cached_generate(cache_key, prompt, fallback, ttl_seconds=30 * 24 * 3600)


def face_report(user_id: str, face: dict[str, Any]) -> dict[str, Any]:
    """Yüz analizi verilerinden Mian Xiang + Kıyafetname sentez raporu."""
    cache_key = f"face-report-{user_id}-{json.dumps(face.get('measurements', {}), sort_keys=True)[:64]}"

    rag = retrieve_context(
        f"Mian Xiang San Ting yüz okuma {face.get('wu_xing_element', '')} element "
        f"Kıyafetname mizaç {face.get('mizac', '')}"
    )
    palaces = "\n".join(
        f"- {p['name_tr']}: {p['assessment']}" for p in face.get("palaces", [])[:6]
    )

    prompt = f"""
GÖREV: Aşağıdaki GERÇEK yüz ölçümü verilerinden 250-300 kelimelik bir kadim
yüz okuması yaz (Mian Xiang + Marifetname İlm-i Sima sentezi). "Sen" diye hitap et.

ÖLÇÜLMÜŞ VERİLER (MediaPipe 468-nokta yüz haritası):
- San Ting dengesi: {face.get('san_ting_balance')}
- San Ting oranları: {face.get('san_ting_ratios')}
- Wu Xing yüz elementi: {face.get('wu_xing_element')} — {face.get('wu_xing_reason', '')}
- Marifetname mizacı: {face.get('mizac')}
- Yüz simetrisi: {face.get('symmetry')}
- Tahmini yaş/duygu: {face.get('age', '?')} / {face.get('emotion', 'nötr')}

12 SARAY DEĞERLENDİRMESİ:
{palaces}

KAYNAK PASAJLARI:
{rag}

Yorum pozitif psikoloji çerçevesinde olsun: her özellik güç + gelişim alanı.
Sonda tek cümlelik bir "kadim tavsiye" ver.
"""
    fallback = face.get("summary", "Yüz hatların kadim haritalara göre dengeli bir mizacı işaret ediyor.")
    return _cached_generate(cache_key, prompt, fallback, ttl_seconds=7 * 24 * 3600)


def bazi_report(user_id: str, bazi: dict[str, Any]) -> dict[str, Any]:
    """BaZi haritasından kader analizi raporu."""
    cache_key = f"bazi-report-{user_id}-{bazi['pillars']['day']['label']}"

    pillars = " | ".join(f"{k}: {v['label']}" for k, v in bazi["pillars"].items())
    luck = "; ".join(
        f"{lp['from_age']}-{lp['to_age']} yaş: {lp['label']} ({lp['ten_god']['name']})"
        for lp in bazi.get("luck_pillars", [])[:4]
    )
    rag = retrieve_context(f"BaZi Day Master {bazi['day_master']['element']} element On Tanrı şans sütunu")

    prompt = f"""
GÖREV: Aşağıdaki BaZi (Dört Sütun) verilerinden 250-300 kelimelik kader haritası
analizi yaz.

HESAPLANMIŞ BAZI HARİTASI (gerçek güneş terimleriyle):
- Dört Sütun: {pillars}
- Günün Efendisi (Day Master): {bazi['day_master']['description']}
- Çin burcu: {bazi['zodiac_animal']}
- Element dağılımı: {bazi['element_distribution']} (baskın: {bazi['dominant_element']},
  eksik: {bazi.get('missing_elements') or 'yok'})
- On Tanrı: yıl={bazi['ten_gods']['year']['name']}, ay={bazi['ten_gods']['month']['name']},
  saat={bazi['ten_gods']['hour']['name']}
- Şans Sütunları: {luck}

KAYNAK PASAJLARI:
{rag}

Bölümler: (1) Öz element ve doğa, (2) Element dengesi ve beslenmesi gereken alan,
(3) Önümüzdeki şans dönemi teması.
"""
    fallback = (
        f"Günün Efendin {bazi['day_master']['element']} elementi: {bazi['day_master']['polarity']} "
        f"doğanın özü bu. Baskın elementin {bazi['dominant_element']}. Detaylı yorum için tekrar dene."
    )
    return _cached_generate(cache_key, prompt, fallback, ttl_seconds=30 * 24 * 3600)


def iching_reading(user_id: str, cast: dict[str, Any]) -> dict[str, Any]:
    """I Ching çekimini kullanıcının sorusuna bağlayan yorum."""
    primary = cast["primary"]
    cache_key = f"iching-{user_id}-{primary['number']}-{cast.get('question', '')[:48]}-{'-'.join(map(str, cast.get('moving_lines', [])))}"

    transformed_text = ""
    if cast.get("transformed"):
        t = cast["transformed"]
        transformed_text = (
            f"\nHAREKETLİ ÇİZGİLER {cast['moving_lines']} → DÖNÜŞEN HEKSAGRAM: "
            f"#{t['number']} {t['name_tr']} ({t['name']})\nHüküm: {t['judgment']}"
        )

    rag = retrieve_context(f"I Ching heksagram {primary['name_tr']} değişim eşzamanlılık yorumu")

    prompt = f"""
GÖREV: Kullanıcının sorusunu, çekilen I Ching heksagramının 3000 yıllık metnine
bağlayan 150-200 kelimelik bir kehanet yorumu yaz.

KULLANICININ SORUSU: "{cast.get('question')}"

ÇEKİM SONUCU ({cast.get('method')} yöntemi, gerçek olasılık dağılımıyla):
- Heksagram #{primary['number']}: {primary['name_tr']} ({primary['name']} {primary['name_cn']}) {primary['unicode']}
- Hüküm: {primary['judgment']}
- İmge: {primary['image']}
- Trigramlar: {primary['lower_trigram']['name_tr']} altında, {primary['upper_trigram']['name_tr']} üstte{transformed_text}

KAYNAK PASAJLARI:
{rag}

Yorum SORUYA ÖZGÜ olsun; hareketli çizgi varsa 'şu andan geleceğe dönüşüm' vurgusu yap.
"""
    fallback = (
        f"#{primary['number']} {primary['name_tr']} {primary['unicode']}: {primary['judgment']} "
        + (f"Dönüşen heksagram: {cast['transformed']['name_tr']} — değişim yolda." if cast.get("transformed") else "")
    )
    return _cached_generate(cache_key, prompt, fallback, ttl_seconds=3600)


def synastry_report(user_id: str, synastry: dict[str, Any]) -> dict[str, Any]:
    """İki kişi arasındaki kozmik uyum raporu."""
    p1, p2 = synastry["person1"], synastry["person2"]
    cache_key = f"synastry-{user_id}-{p1['name']}-{p2['name']}-{synastry['relationship_score'].get('score')}"

    aspects = "\n".join(
        f"- {a['p1_tr']} ({p1['name']}) {a['aspect_tr']} {a['p2_tr']} ({p2['name']}) orb {a['orbit']}°"
        for a in synastry.get("aspects", [])[:8]
    )
    rag = retrieve_context("sinastri uyum aşk ilişki gezegen açıları evlilik")

    prompt = f"""
GÖREV: İki kişi arasındaki sinastri (astrolojik uyum) verilerinden 200-250
kelimelik bir kozmik uyum raporu yaz.

KİŞİLER:
- {p1['name']}: Güneş {p1['sun']['sign_tr']}, Ay {p1['moon']['sign_tr']}
- {p2['name']}: Güneş {p2['sun']['sign_tr']}, Ay {p2['moon']['sign_tr']}

UYUM SKORU: {synastry['relationship_score'].get('score')} ({synastry['relationship_score'].get('description')})

ÖNEMLİ KARŞILIKLI AÇILAR:
{aspects}

KAYNAK PASAJLARI:
{rag}

Bölümler: (1) Genel rezonans, (2) Güçlü bağ noktaları, (3) Dikkat ve büyüme alanı.
İki tarafı da eşit sıcaklıkta ele al.
"""
    fallback = (
        f"{p1['name']} ({p1['sun']['sign_tr']}) ile {p2['name']} ({p2['sun']['sign_tr']}) arasında "
        f"uyum skoru {synastry['relationship_score'].get('score', '—')}. Detaylı yorum için tekrar dene."
    )
    return _cached_generate(cache_key, prompt, fallback, ttl_seconds=7 * 24 * 3600)
