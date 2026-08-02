import logging
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from core.auth import AuthUser, get_current_user
from core.entitlements import FREE_CHAT_PER_DAY, enforce_daily_quota
from core.i18n import get_language
from core.messages import text
from services import (
    chart_context,
    chart_query,
    gemini_service,
    memory_extractor,
    memory_service,
    notification_service,
    profile_service,
    prompts,
    sky_service,
)
from services.prompt_composer import compose_chat_message, should_use_rag
from services.rag_service import retrieve_passages
from services.safety_rules import forbidden_topic
from services.sky_service import get_sky_now

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatMessageItem(BaseModel):
    sender: str  # USER | AI
    text: str


class ChatRequest(BaseModel):
    history: List[ChatMessageItem] = []
    message: str


class ModerationRequest(BaseModel):
    text: str


def _sky_summary(lang: str, profile: dict | None = None) -> str:
    """Bugünün gökyüzünün kompakt özeti; hata durumunda boş döner.

    Gökyüzü sohbetin çalışması için zorunlu değil — alınamazsa sohbet
    haritasız/gökyüzsüz ama çalışır durumda devam eder.

    Etiketler dile bağlı: bu blok prompt'a giriyor ve İngilizce bir prompt'un
    içinde Türkçe etiketler modelin dili karıştırmasına yol açıyordu.

    ``profile`` yalnızca **saat dilimi** için kullanılır: günün yöneticisi
    kullanıcının yerel tarihine bağlıdır ve gökyüzü yükü UTC'de hesaplanıp
    tüm kullanıcılarla paylaşıldığı için oraya gömülemez.
    """
    try:
        sky = prompts.localize_sky(lang, get_sky_now())
    except Exception as exc:
        logger.warning("Gökyüzü alınamadı: %s", exc)
        return ""

    p = prompts.get(lang)
    moon = sky.get("moon_phase") or {}
    retros = ", ".join(sky.get("retrogrades", [])) or p.NONE_LABEL
    aspects = "; ".join(
        f"{a['p1']}-{a['p2']} {a['aspect']}" for a in (sky.get("aspects") or [])[:3]
    )

    satirlar = [
        p.SKY_MOON.format(name=moon.get("name"),
                          illumination=moon.get("illumination")),
        p.SKY_RETROS.format(retros=retros),
    ]
    if aspects:
        satirlar.append(p.SKY_ASPECTS.format(aspects=aspects))

    # Marifetname katmanı: korpusa girdiği hâlde motorda karşılığı olmayan
    # iki bilgi buradan geliyor. Karşılığı olmasaydı model bunlar hakkında
    # dayanaksız konuşurdu.
    yerel_gun = notification_service.local_now(profile or {}).date()
    satirlar.append(p.SKY_DAY_RULER.format(
        planet=prompts.planet_name(lang, sky_service.day_ruler(yerel_gun))))
    menzil = sky.get("moon_mansion") or {}
    if menzil:
        satirlar.append(p.SKY_MOON_MANSION.format(
            number=menzil.get("number"), name=menzil.get("name")))

    return "\n".join(satirlar)


@router.post("")
@router.post("/")
def chat(request: ChatRequest, background: BackgroundTasks,
         user: AuthUser = Depends(get_current_user),
         lang: str = Depends(get_language)):
    """Sohbet: ucretsiz katmanda gunde [FREE_CHAT_PER_DAY] mesaj, abonede sinirsiz.

    Kota LLM cagrisindan ONCE dusulur; aksi halde hata donen istekler de
    kullaniciya bedava mesaj kazandirirdi.
    """
    # Yasak alan kapısı kotadan ÖNCE: reddedilen bir soru kullanıcının günlük
    # hakkını yemez.
    blocked = forbidden_topic(request.message, lang=lang)
    if blocked is not None:
        kategori, reply = blocked
        logger.info("Yasak alan reddedildi: %s", kategori)
        return {"status": "success", "reply": reply, "blocked": kategori}

    enforce_daily_quota(user, "chat", FREE_CHAT_PER_DAY, lang=lang)
    try:
        history = [{"sender": m.sender, "text": m.text} for m in request.history]

        # Profil bir kez okunur, iki yerde kullanılır: haritayı prompt'a
        # iliştirmek ve bilgi tabanı sorgusunu kurmak.
        profile = profile_service.get_profile(user.uid)
        facts = chart_context.chart_facts(user.uid, profile) if profile else None

        # Seçici RAG: selamlaşma/duygu/kısa onay turlarında korpus araması
        # (ve embedding çağrısı) atlanır; kadim bilgi soran mesajlarda en
        # fazla 2 kırpılmış pasaj "arka plan fısıltısı" olarak eklenir.
        #
        # Arama artık kullanıcının CÜMLESİYLE değil, cümlenin konusu +
        # haritanın o konuyla ilgili faktörleriyle yapılıyor. "İşimle ilgili
        # ne yapmalıyım?" diye aramak kadim metinde hiçbir şeye denk gelmez;
        # "meslek, statü + Satürn 10. evde + Güneş Kare Mars" gelir.
        passages = []
        if should_use_rag(request.message, lang):
            sorgu = chart_query.build_query(request.message, facts, lang=lang)
            passages = retrieve_passages(sorgu, top_k=2, lang=lang)

        # Kullanıcı hafızası: "seni tanıyor" hissinin kaynağı burası. Okuma
        # ucuz (tek Firestore dokümanı) ve RAG'den bağımsız olarak her turda
        # yapılır — kullanıcı hakkında bilinenler her mesajda geçerlidir.
        memory = memory_service.memory_context(user.uid)

        # Kullanıcının haritası. Uzun süre yalnızca Güneş/Ay/Yükselen
        # geçiyordu; artık ev yerleşimleri, element dengesi, doğum açıları ve
        # bugün haritaya dokunan transitler de geliyor — cevabın "herkese
        # uyan" olmaktan çıkması bu ayrıntılara bağlı. Efemeris hesabı
        # önbellekli, LLM maliyeti yok.
        chart = chart_context.chart_whisper(
            user.uid, profile, lang=lang, facts=facts)

        # Bugünün gökyüzü paylaşımlı önbellekten gelir (kullanıcı başına
        # maliyeti yok) ve sohbetin "şu an" ile bağını kurar.
        sky = _sky_summary(lang, profile)

        message = compose_chat_message(request.message, passages,
                                       memory=memory, chart=chart, sky=sky,
                                       lang=lang)

        reply = gemini_service.chat(history, message, lang=lang)
        if reply is None:
            reply = text("llm_unavailable", lang)
        # Olgu çıkarımı yanıttan SONRA, arka planda: kullanıcı ikinci bir LLM
        # çağrısını beklemez. Kendi içinde kotalı ve hataya dayanıklı.
        background.add_task(
            memory_extractor.extract_and_store, user.uid, history, request.message
        )

        return {"status": "success", "reply": reply}
    except Exception as e:
        logger.exception("Sohbet ucunda hata", exc_info=e)
        raise HTTPException(status_code=500, detail=text("internal", lang))


@router.post("/moderate")
def moderate(request: ModerationRequest, user: AuthUser = Depends(get_current_user)):
    """Sosyal paylaşım öncesi içerik denetimi (istemci çağırır)."""
    return {"status": "success", "safe": gemini_service.moderate(request.text)}
