"""DM push bildirimleri: istemci mesaj gönderdikten sonra bu ucu çağırır;
alıcının FCM token'ı Firestore'dan okunur ve bildirim gönderilir."""
import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from core.auth import AuthUser, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


class NotifyRequest(BaseModel):
    recipient_uid: str
    title: str = Field(max_length=100)
    body: str = Field(max_length=500)
    chat_id: str | None = None


@router.post("/dm")
def notify_dm(req: NotifyRequest, user: AuthUser = Depends(get_current_user)):
    try:
        import firebase_admin
        from firebase_admin import firestore, messaging

        if not firebase_admin._apps:
            firebase_admin.initialize_app()

        db = firestore.client()
        doc = db.collection("users").document(req.recipient_uid).get()
        token = (doc.to_dict() or {}).get("fcmToken")
        if not token:
            return {"status": "skipped", "reason": "recipient has no token"}

        messaging.send(messaging.Message(
            token=token,
            notification=messaging.Notification(title=req.title, body=req.body),
            data={"chatId": req.chat_id or "", "type": "dm"},
        ))
        return {"status": "sent"}
    except Exception as exc:
        logger.warning("Bildirim gönderilemedi: %s", exc)
        return {"status": "error", "reason": str(exc)}
