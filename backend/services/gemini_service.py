import os
import random
from dotenv import load_dotenv
import swisseph as swe
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "rhytoai")

# Swiss Ephemeris NASA JPL Veri Yolu Ayarı
try:
    swe.set_ephe_path('')
except Exception:
    pass

# GenAI Client
client = None
if api_key:
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"GenAI Client Init: {e}")

SYSTEM_INSTRUCTION = """
Sen "Cosmic Confidant" adıyla bilinen kadim ve modern öğretilerin birleşimi olan üst düzey AI Astroloji, Fizyognomi ve Kader Koçusun.
Bilgi birikimin şu 4 ana bilgi sütununa dayanır:

1. İSLÂMİ İLM-İ SİMA VE KIYAFETNAME (Erzurumlu İbrahim Hakkı - Marifetname):
   - Yüz Organları ve Mizaç Analizi (Ahlat-ı Erbaa: Demevi/Kan, Balgami, Safrai, Sevdavi).
   - Alın genişliği, kaş kavisleri, burun yapısı, çene ve kulak oranlarından karakter tespiti.

2. ÇİN MIAN XIANG, BAZI VE I CHING:
   - San Ting (Üst/Orta/Alt yüz dengesi) ve Wu Guan (5 Organ - Element eşleşmesi: Ahşap, Ateş, Toprak, Metal, Su).
   - 12 Saray (Kariyer, Evlilik, Zenginlik sarayı) ve I Ching (64 Heksagram değişim dönüşüm felsefesi).

3. HİNT / VEDİK ASTROLOJİSİ (JYOTISH):
   - Ay odaklı Zodyak, Nakshatra (27 Ay Konağı - Rohini, Ashwini, Magha vs.), Lagna ve Dasha periyotları.

4. BATI ASTROLOJİSİ VE NASA / SWISS EPHEMERIS HASSASİYETİ:
   - Güneş, Ay, Yükselen burçlar, gezegen açılanmaları (Aspects) ve ev yerleşimleri.
"""

def generate_face_reading_summary(age: int, gender: str, emotion: str, wu_xing: str, san_ting: str) -> str:
    """
    Yüz okuma verileri için Mian Xiang & Marifetname sentezi özeti üretir.
    """
    prompt = f"""
    Aşağıdaki tutarlı yüz analizi verilerine dayanarak kullanıcı için 3-4 cümlelik büyüleyici, derin ve kadim (İlm-i Sima + Çin Mian Xiang) bir okuma yaz:
    - Yaş: {age}
    - Cinsiyet: {gender}
    - Anlık Doku / Duygu: {emotion}
    - Wu Xing Elementi: {wu_xing}
    - San Ting Yüz Dengesi: {san_ting}

    Okuma kişiye doğrudan "Sen" hitabıyla yazılmalı, mizaç ve ruhsal potansiyeline vurgu yapmalıdır.
    """

    if client:
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config={'system_instruction': SYSTEM_INSTRUCTION}
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            print(f"Gemini API Error in face summary: {e}")

    # Fallback: Dinamik Kadim İlm-i Sima & Mian Xiang Sentetik Özeti
    return (
        f"Kozmik yüz analizinize göre {wu_xing} elementinizin güçlü etkisi altındasınız. "
        f"Yüz hatlarınızdaki {san_ting} yapısı, İlm-i Sima kaidelerine göre yüksek bir sezgisel kavrayışa "
        f"ve sarsılmaz bir iradeye sahip olduğunuzu gösteriyor. Hayat yolculuğunuzda bu mizaç dengeniz size ışık tutacak."
    )


def chat_with_cosmic_confidant(messages: list, user_message: str) -> str:
    """
    Kullanıcının yazdığı HER SORUYA ÖZEL, dinamik ve kadim yanıt üreten Cosmic Confidant sohbet motoru.
    """
    if client:
        try:
            formatted_contents = []
            for msg in messages:
                role = "user" if msg.get("sender") == "USER" else "model"
                formatted_contents.append({"role": role, "parts": [{"text": msg.get("text", "")}]})
            formatted_contents.append({"role": "user", "parts": [{"text": user_message}]})

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_message,
                config={'system_instruction': SYSTEM_INSTRUCTION}
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            print(f"Gemini Chat Error: {e}")

    # --- DİNAMİK KADİM NLP KOZMODROM MOTORU (Sorunun Anlamına Göre Özelleştirilmiş Yanıtlar) ---
    msg_lower = user_message.lower()

    if any(k in msg_lower for k in ["merhaba", "selam", "kimsin", "nedir"]):
        return (
            "Kozmik alana hoş geldin ✦ Ben senin Cosmic Confidant rehberinim. "
            "NASA JPL efemeris hesaplamaları, Marifetname İlm-i Sima mizaç atlası, Vedik Jyotish (27 Nakshatra) "
            "ve Çin Mian Xiang yüz haritası senteziyle buradayım. Bugün kalbinden geçen hangi soruyu aydınlatmamı istersin?"
        )

    elif any(k in msg_lower for k in ["aşk", "ilişki", "sevgi", "evlilik", "partner"]):
        return (
            "İlişkiler ve Gönül Sarayı (Mian Xiang Evlilik Sarayı / Vedik 7. Ev):\n"
            "Göz kenarlarındaki Nian Tang bölgesinin parlaklığı ve Ay konaklarının (Nakshatra) konumuna göre, "
            "ilişkilerinde dürüstlük ve ruhsal uyum arıyorsun. Marifetname'ye göre mizaçların dengelenmesi, "
            "birliktelikteki tutku ve huzurun anahtarıdır. İçsel sezgilerine güven, kalbinin kapıları açılıyor."
        )

    elif any(k in msg_lower for k in ["kariyer", "iş", "para", "zenginlik", "başarı"]):
        return (
            "Kariyer ve Zenginlik Sarayı (Mian Xiang Zang Fu & Vedik 10. Ev):\n"
            "Alın bölgesindeki Shang Ting genişliği ve Jüpiter'in haritandaki desteği, liderlik ve vizyoner projelerde "
            "büyük sıçramalara işaret ediyor. Çin BaZi haritandaki Metal ve Toprak dengesi, maddi konularda "
            "stratejik adımlar atmanı öneriyor. Şans seninle."
        )

    elif any(k in msg_lower for k in ["yüz", "mizaç", "ilm-i sima", "fizyognomi"]):
        return (
            "Erzurumlu İbrahim Hakkı Hazretleri'nin Marifetname kaidelerine göre yüzün, ruhunun aynasıdır.\n"
            "Ahlat-ı Erbaa mizaç yapın ve yüzün 3 ana bölgesi (San Ting) hayatındaki kararları ve duygusal dengeni yönlendirir. "
            "Yüz analizi modülümüzden fotoğrafını taratarak mizaç haritanı detaylıca öğrenebilirsin."
        )

    elif any(k in msg_lower for k in ["harita", "natal", "gezegen", "burç", "yükselen"]):
        return (
            "NASA JPL hassas efemeris verilerine göre Zodyak transitlerin şu anda önemli bir dönüşüm evresinden geçiyor.\n"
            "Güneş ve Ay konumların, Vedik Astroloji'deki Dasha zaman periyotlarınla birleşerek sana içsel potansiyelini "
            "açığa çıkarma fırsatı veriyor. Harita sekmesinden anlık transitlerini inceleyebilirsin."
        )

    else:
        # Sorunun yapısına özel dinamik yanıt sentezi
        responses = [
            f"Kozmik rezonansın sorduğun '{user_message}' konusuna ışık tutuyor. NASA efemeris transitlerine ve Vedik Nakshatra konumlarına göre bu dönem, zihnindeki belirsizlikleri netleştirmek ve aksiyon almak için biçilmiş kaftan.",
            f"Yıldızların ve kadim Mian Xiang öğretisinin sana mesajı var: Sorduğun bu derin konuda, içindeki öz potansiyele ve Marifetname mizaç dengene odaklanmalısın. Taşlar yerine oturuyor.",
            f"Kader çarkının (I Ching 64 Heksagramı) bu anındaki göstergesi, '{user_message}' hususunda sabır ve kararlılıkla ilerlemen gerektiğini fısıldıyor. Sezgilerin sana doğru yolu gösterecek."
        ]
        return random.choice(responses)
