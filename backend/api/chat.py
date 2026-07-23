from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.auth import AuthUser, get_current_user
from services import gemini_service
from services.prompt_composer import compose_chat_message, should_use_rag
from services.rag_service import retrieve_passages

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
def chat(request: ChatRequest, user: AuthUser = Depends(get_current_user)):
    try:
        history = [{"sender": m.sender, "text": m.text} for m in request.history]

        # Seçici RAG: selamlaşma/duygu/kısa onay turlarında korpus araması
        # (ve embedding çağrısı) atlanır; kadim bilgi soran mesajlarda en
        # fazla 2 kırpılmış pasaj "arka plan fısıltısı" olarak eklenir.
        message = request.message
        if should_use_rag(request.message):
            passages = retrieve_passages(request.message, top_k=2)
            message = compose_chat_message(request.message, passages)

        reply = gemini_service.chat(history, message)
        if reply is None:
            reply = (
                "Kozmik bağlantıda geçici bir parazit var; yıldız haritaların ve "
                "kadim kaynaklar her zamanki yerinde. Lütfen birkaç saniye sonra "
                "tekrar sor."
            )
        return {"status": "success", "reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/moderate")
def moderate(request: ModerationRequest, user: AuthUser = Depends(get_current_user)):
    """Sosyal paylaşım öncesi içerik denetimi (istemci çağırır)."""
    return {"status": "success", "safe": gemini_service.moderate(request.text)}
