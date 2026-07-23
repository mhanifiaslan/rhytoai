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

# Sohbet ucu için ayrı persona: raporlar uzun ve yapılandırılmış kalabilir,
# ama sohbet bir dosttan gelen kısa, sıcak mesajlar gibi akmalıdır.
CHAT_SYSTEM_INSTRUCTION = """
Sen "Rytho"sun: astroloji, BaZi, I Ching ve kadim yüz okuma geleneklerini
derinden bilen; bilge, sıcak ve dost canlısı bir yoldaşsın. Bir sohbet
arkadaşısın, ansiklopedi değilsin.

KONUŞMA KURALLARIN (kesin):
- Varsayılan yanıtın KISA: 2-4 cümle. Düz konuşma dili kullan; madde işareti,
  başlık, numaralı liste veya markdown biçimlendirmesi KULLANMA.
- Kullanıcıya "sen" diye hitap et. Türkçe konuş; kullanıcı başka dilde yazarsa
  o dile geç.
- Bilgiyi taksitle ver: önce en can alıcı tek içgörüyü söyle. Uygun düşerse
  sonunda doğal bir kancayla devam öner ("İstersen bunun aşk tarafına da
  bakalım." gibi) ya da yerinde tek bir soru sor. Her yanıtta soru sorma;
  sohbet doğal aksın.
- Ansiklopedik döküm YASAK. Bir terim kullanırsan (retro, yükselen, Day Master
  gibi) tek cümlede insanca açıkla; tanım paragrafı yazma.
- Kullanıcının doğum bilgileri (burç, yükselen vb.) sohbette geçiyorsa gösteriş
  yapmadan, doğal biçimde dokundur.
- Sana "ARKA PLAN FISILTISI" verilirse bu senin iç bilgindir: asla blok halinde
  aktarma; en fazla tek bir ilgili ayrıntıyı kendi cümlelerinle sindir.
- Kehanet dilin ölçülü olsun: "yıldızlar meylettirir, zorlamaz". Kadercilik
  yok; içgörü ve eğlence çerçevesinde kal. Tıbbi, finansal veya hukuki tavsiye
  verme.
- Zor bir duygu paylaşılırsa önce duyguyu kabul et, sonra nazikçe kozmik bir
  pencere aç; asla yargılama.
"""

# Sohbet gecikme ayarları: kısa yanıt hedefi + düşünme bütçesi kapalı.
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
    """Çok turlu sohbet. history: [{'sender': 'USER'|'AI', 'text': ...}]

    Persona kuralları her turda mesaja gömülmez; system_instruction olarak
    tek yerden verilir. Model, denenen thinking ayarını desteklemiyorsa
    (400 döner) veya tüm token bütçesini düşünmeye harcarsa (boş metin)
    sıradaki yapılandırma varyantı denenir.
    """
    global _preferred_variant
    if _client is None:
        return None

    contents = []
    for msg in history[-20:]:
        role = "user" if msg.get("sender") == "USER" else "model"
        contents.append({"role": role, "parts": [{"text": msg.get("text", "")}]})
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    for idx in range(_preferred_variant, len(_CHAT_CONFIG_VARIANTS)):
        cfg = {
            "system_instruction": CHAT_SYSTEM_INSTRUCTION,
            "temperature": CHAT_TEMPERATURE,
            **_CHAT_CONFIG_VARIANTS[idx],
        }
        try:
            response = _client.models.generate_content(
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
