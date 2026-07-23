from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.auth import AuthUser, get_current_user
from services import gemini_service
from services.rag_service import retrieve_context

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

        # RAG: soruya uygun kadim pasajları bağlama ekle
        context = retrieve_context(request.message, top_k=2)
        message = request.message
        if context:
            message = (
                f"KAYNAK PASAJLARI (yanıtında harmanla, alıntı formatı kullanma):\n"
                f"{context}\n\n---\nKULLANICININ MESAJI: {request.message}"
            )

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
