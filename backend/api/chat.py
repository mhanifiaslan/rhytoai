import logging
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from core.auth import AuthUser, get_current_user
from core.entitlements import FREE_CHAT_PER_DAY, enforce_daily_quota
from services import gemini_service, memory_extractor, memory_service
from services.prompt_composer import compose_chat_message, should_use_rag
from services.rag_service import retrieve_passages
from services.safety_rules import forbidden_topic

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


@router.post("")
@router.post("/")
def chat(request: ChatRequest, background: BackgroundTasks,
         user: AuthUser = Depends(get_current_user)):
    """Sohbet: ucretsiz katmanda gunde [FREE_CHAT_PER_DAY] mesaj, abonede sinirsiz.

    Kota LLM cagrisindan ONCE dusulur; aksi halde hata donen istekler de
    kullaniciya bedava mesaj kazandirirdi.
    """
    # Yasak alan kapısı kotadan ÖNCE: reddedilen bir soru kullanıcının günlük
    # hakkını yemez.
    blocked = forbidden_topic(request.message)
    if blocked is not None:
        kategori, reply = blocked
        logger.info("Yasak alan reddedildi: %s", kategori)
        return {"status": "success", "reply": reply, "blocked": kategori}

    enforce_daily_quota(user, "chat", FREE_CHAT_PER_DAY)
    try:
        history = [{"sender": m.sender, "text": m.text} for m in request.history]

        # Seçici RAG: selamlaşma/duygu/kısa onay turlarında korpus araması
        # (ve embedding çağrısı) atlanır; kadim bilgi soran mesajlarda en
        # fazla 2 kırpılmış pasaj "arka plan fısıltısı" olarak eklenir.
        passages = []
        if should_use_rag(request.message):
            passages = retrieve_passages(request.message, top_k=2)

        # Kullanıcı hafızası: "seni tanıyor" hissinin kaynağı burası. Okuma
        # ucuz (tek Firestore dokümanı) ve RAG'den bağımsız olarak her turda
        # yapılır — kullanıcı hakkında bilinenler her mesajda geçerlidir.
        memory = memory_service.memory_context(user.uid)

        message = compose_chat_message(request.message, passages, memory=memory)

        reply = gemini_service.chat(history, message)
        if reply is None:
            reply = (
                "Kozmik bağlantıda geçici bir parazit var; yıldız haritaların ve "
                "kadim kaynaklar her zamanki yerinde. Lütfen birkaç saniye sonra "
                "tekrar sor."
            )
        # Olgu çıkarımı yanıttan SONRA, arka planda: kullanıcı ikinci bir LLM
        # çağrısını beklemez. Kendi içinde kotalı ve hataya dayanıklı.
        background.add_task(
            memory_extractor.extract_and_store, user.uid, history, request.message
        )

        return {"status": "success", "reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/moderate")
def moderate(request: ModerationRequest, user: AuthUser = Depends(get_current_user)):
    """Sosyal paylaşım öncesi içerik denetimi (istemci çağırır)."""
    return {"status": "success", "safe": gemini_service.moderate(request.text)}
