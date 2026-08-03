"""Gemini LLM istemcisi — Cosmic Confidant personası.

Tüm LLM çağrıları bu modülden geçer. RAG bağlamı ve yapılandırılmış hesaplama
verileri report_service tarafından prompt'a gömülür; burası yalnızca model
iletişimi ve persona yönetiminden sorumludur.
"""
from __future__ import annotations

import logging

from core import config, i18n
from services import prompts

logger = logging.getLogger(__name__)

_client = None
_client_kuruldu = False


def _get_client():
    """İstemciyi ilk ihtiyaç anında kurar.

    `from google import genai` açılıştaki **en pahalı tek kalem**: ölçümde
    624 ms, `import main`'in toplam 1,6 saniyesinin üçte biri. Modül düzeyinde
    yapılınca her soğuk başlatma bunu ödüyordu ve Cloud Run'da soğuk başlatma
    kullanıcının gördüğü "bekliyor bekliyor" hâlinin ta kendisi.

    Sonuç önbelleklenir — başarısızlık da. Anahtar yoksa ya da istemci
    kurulamıyorsa her çağrıda yeniden denemek anlamsız.

    Bedeli ilk isteğin ödememesi için `warm_up()` açılışta arka planda çağrılır.
    """
    global _client, _client_kuruldu
    if _client_kuruldu:
        return _client
    _client_kuruldu = True
    if not config.GEMINI_API_KEY:
        return None
    try:
        from google import genai

        _client = genai.Client(api_key=config.GEMINI_API_KEY)
    except Exception as exc:  # pragma: no cover
        logger.warning("GenAI istemcisi başlatılamadı: %s", exc)
    return _client


def warm_up() -> None:
    """İstemciyi arka planda hazırlar — açılışta çağrılır, açılışı bekletmez."""
    import threading

    threading.Thread(target=_get_client, daemon=True, name="genai-warmup").start()

#: Geriye dönük uyum ve varsayılan dil için. Diller `services/prompts`
#: altında; persona metinleri artık orada tutuluyor.
SYSTEM_INSTRUCTION = prompts.get(i18n.DEFAULT).SYSTEM_INSTRUCTION
CHAT_SYSTEM_INSTRUCTION = prompts.get(i18n.DEFAULT).CHAT_SYSTEM_INSTRUCTION

CHAT_MAX_OUTPUT_TOKENS = 300
CHAT_TEMPERATURE = 0.85

# Düşünme (thinking) kapatma varyantları, tercih sırasıyla:
# 1) Gemini 3 ailesi: thinking_level="minimal"
# 2) Gemini 2.5 ailesi: thinking_budget=0
# 3) Düşünme kapatılamıyorsa: bütçeyi geniş tut ki düşünme tokenları kısa
#    yanıtın token limitini yutmasın (aksi halde yanıt ortadan kesilir).
_CHAT_CONFIG_VARIANTS: tuple[dict, ...] = (
    {"thinking_config": {"thinking_level": "minimal"},
     "max_output_tokens": CHAT_MAX_OUTPUT_TOKENS},
    {"thinking_config": {"thinking_budget": 0},
     "max_output_tokens": CHAT_MAX_OUTPUT_TOKENS},
    {"max_output_tokens": 1024},
)

# Çalıştığı bilinen varyant hatırlanır; her istekte yeniden denenmez.
_preferred_variant = 0


def is_available() -> bool:
    return _get_client() is not None


def generate(prompt: str, temperature: float = 0.9,
             lang: str | None = None) -> str | None:
    """Tek atımlık üretim. Başarısız olursa None döner (çağıran fallback verir).

    Persona dile göre seçilir: İngilizce yorum Türkçe persona ile üretilirse
    ton ve dil karışır.
    """
    client = _get_client()
    if client is None:
        return None
    try:
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt,
            config={
                "system_instruction": prompts.get(lang).SYSTEM_INSTRUCTION,
                "temperature": temperature,
            },
        )
        if response and response.text:
            return response.text.strip()
    except Exception as exc:
        logger.warning("Gemini üretim hatası: %s", exc)
    return None


def extract_json(prompt: str, schema: dict | None = None) -> str | None:
    """Persona'sız, düşük sıcaklıkta yapılandırılmış üretim.

    Olgu çıkarımı gibi işler için: Rytho personası (sıcak, edebi, "sen" dili)
    burada zararlıdır — istenen şey yorum değil, veri. Bu yüzden
    ``SYSTEM_INSTRUCTION`` uygulanmaz ve sıcaklık düşük tutulur.
    """
    client = _get_client()
    if client is None:
        return None
    try:
        cfg: dict = {"temperature": 0.1, "response_mime_type": "application/json"}
        if schema is not None:
            cfg["response_schema"] = schema
        response = client.models.generate_content(
            model=config.GEMINI_MODEL, contents=prompt, config=cfg
        )
        if response and response.text:
            return response.text.strip()
    except Exception as exc:
        logger.warning("Yapılandırılmış üretim hatası: %s", exc)
    return None


def chat(history: list[dict], user_message: str,
         lang: str | None = None) -> str | None:
    """Çok turlu sohbet. history: [{'sender': 'USER'|'AI', 'text': ...}]

    Persona kuralları her turda mesaja gömülmez; system_instruction olarak
    tek yerden verilir. Model, denenen thinking ayarını desteklemiyorsa
    (400 döner) veya tüm token bütçesini düşünmeye harcarsa (boş metin)
    sıradaki yapılandırma varyantı denenir.
    """
    global _preferred_variant
    client = _get_client()
    if client is None:
        return None

    contents = []
    for msg in history[-20:]:
        role = "user" if msg.get("sender") == "USER" else "model"
        contents.append({"role": role, "parts": [{"text": msg.get("text", "")}]})
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    for idx in range(_preferred_variant, len(_CHAT_CONFIG_VARIANTS)):
        cfg = {
            "system_instruction": prompts.get(lang).CHAT_SYSTEM_INSTRUCTION,
            "temperature": CHAT_TEMPERATURE,
            **_CHAT_CONFIG_VARIANTS[idx],
        }
        try:
            response = client.models.generate_content(
                model=config.GEMINI_MODEL, contents=contents, config=cfg,
            )
            if response and response.text:
                _preferred_variant = idx
                return response.text.strip()
            logger.info("Sohbet varyantı %d boş metin döndürdü, sıradaki denenecek", idx)
        except Exception as exc:
            logger.info("Sohbet varyantı %d başarısız (%s), sıradaki denenecek", idx, exc)
    logger.warning("Tüm sohbet yapılandırma varyantları başarısız oldu")
    return None


# `moderate()` KALDIRILDI (Revize R0): tek çağıranı, hiçbir istemcinin
# kullanmadığı kotasız `/chat/moderate` ucuydu — ayrıntı api/chat.py'de.
