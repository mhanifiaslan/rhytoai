"""Gemini LLM istemcisi — Cosmic Confidant personası.

Tüm LLM çağrıları bu modülden geçer. RAG bağlamı ve yapılandırılmış hesaplama
verileri report_service tarafından prompt'a gömülür; burası yalnızca model
iletişimi ve persona yönetiminden sorumludur.
"""
from __future__ import annotations

import logging

from core import config

logger = logging.getLogger(__name__)

_client = None
if config.GEMINI_API_KEY:
    try:
        from google import genai

        _client = genai.Client(api_key=config.GEMINI_API_KEY)
    except Exception as exc:  # pragma: no cover
        logger.warning("GenAI istemcisi başlatılamadı: %s", exc)

SYSTEM_INSTRUCTION = """
Sen "Rytho" adında, kadim bilgelik sistemlerini modern hassas hesaplamalarla
birleştiren bir Kozmik Rehbersin. Bilgin dört sütuna dayanır:

1. İSLAMİ İLM-İ SİMA VE KIYAFETNAME (Erzurumlu İbrahim Hakkı - Marifetname):
   Ahlat-ı Erbaa mizaçları (Demevi, Safrai, Sevdavi, Balgami) ve organ okuma.
2. ÇİN METAFİZİĞİ: Mian Xiang (San Ting, Wu Guan, 12 Saray), BaZi (Day Master,
   On Tanrı, Şans Sütunları), I Ching (64 heksagram, hareketli çizgiler).
3. VEDİK ASTROLOJİ (JYOTISH): Sidereal zodyak, Nakshatra'lar, Dasha dönemleri.
4. BATI ASTROLOJİSİ: Swiss Ephemeris / NASA JPL hassasiyetinde gezegen
   konumları, açılar, ev yerleşimleri, transitler.

ÜSLUP KURALLARI:
- Kullanıcıya "sen" diye hitap et; sıcak, bilge ve edebi bir dil kullan.
- Sana verilen HESAPLANMIŞ VERİLERE sadık kal; veri uydurma.
- KAYNAK PASAJLARI verildiyse onlardan beslen ve harmanla.
- Olumsuz göstergeleri asla yargı olarak sunma: her zorluğu "güç + gelişim
  alanı" çerçevesinde, yapıcı ve umut veren bir dille anlat.
- Kadercilik yok: "yıldızlar meylettirir, zorlamaz" ilkesiyle konuş.
- Tıbbi, hukuki veya finansal kesin tavsiye verme.
- Türkçe yanıt ver (kullanıcı başka dilde yazarsa o dile geç).
"""


def is_available() -> bool:
    return _client is not None


def generate(prompt: str, temperature: float = 0.9) -> str | None:
    """Tek atımlık üretim. Başarısız olursa None döner (çağıran fallback verir)."""
    if _client is None:
        return None
    try:
        response = _client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt,
            config={
                "system_instruction": SYSTEM_INSTRUCTION,
                "temperature": temperature,
            },
        )
        if response and response.text:
            return response.text.strip()
    except Exception as exc:
        logger.warning("Gemini üretim hatası: %s", exc)
    return None


def chat(history: list[dict], user_message: str) -> str | None:
    """Çok turlu sohbet. history: [{'sender': 'USER'|'AI', 'text': ...}]"""
    if _client is None:
        return None
    try:
        contents = []
        for msg in history[-20:]:
            role = "user" if msg.get("sender") == "USER" else "model"
            contents.append({"role": role, "parts": [{"text": msg.get("text", "")}]})
        contents.append({"role": "user", "parts": [{"text": user_message}]})

        response = _client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=contents,
            config={"system_instruction": SYSTEM_INSTRUCTION, "temperature": 0.9},
        )
        if response and response.text:
            return response.text.strip()
    except Exception as exc:
        logger.warning("Gemini sohbet hatası: %s", exc)
    return None


def moderate(text: str) -> bool:
    """Sosyal paylaşım içeriği için basit moderasyon. True = güvenli.
    LLM erişilemezse içerik güvenli varsayılır (istemci tarafı raporlama devrede)."""
    if _client is None:
        return True
    try:
        response = _client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=(
                "Aşağıdaki sosyal medya gönderisini denetle. Nefret söylemi, taciz, "
                "şiddet tehdidi, cinsel istismar veya spam içeriyorsa SADECE 'UNSAFE', "
                "aksi halde SADECE 'SAFE' yaz.\n\n---\n" + text[:2000]
            ),
            config={"temperature": 0.0},
        )
        return "UNSAFE" not in (response.text or "").upper()
    except Exception:
        return True
