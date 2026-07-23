"""Firebase ID token doğrulama.

Üretimde (RYTHO_DEV_MODE=0) her istek `Authorization: Bearer <idToken>` başlığı
taşımak zorundadır. Lokal geliştirmede token yoksa anonim kullanıcı kabul edilir.
"""
import logging

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core import config

logger = logging.getLogger(__name__)

_firebase_ready = False


def _init_firebase() -> bool:
    global _firebase_ready
    if _firebase_ready:
        return True
    try:
        import firebase_admin
        if not firebase_admin._apps:
            # Cloud Run'da Application Default Credentials kullanılır.
            firebase_admin.initialize_app(
                options={"projectId": config.GOOGLE_CLOUD_PROJECT}
            )
        _firebase_ready = True
        return True
    except Exception as exc:  # pragma: no cover
        logger.warning("Firebase Admin başlatılamadı: %s", exc)
        return False


_bearer = HTTPBearer(auto_error=False)


class AuthUser:
    def __init__(self, uid: str, email: str | None = None, anonymous: bool = False):
        self.uid = uid
        self.email = email
        self.anonymous = anonymous


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthUser:
    if credentials is not None and _init_firebase():
        try:
            from firebase_admin import auth as fb_auth

            decoded = fb_auth.verify_id_token(credentials.credentials)
            return AuthUser(uid=decoded["uid"], email=decoded.get("email"))
        except Exception as exc:
            logger.info("Token doğrulanamadı: %s", exc)
            if not config.DEV_MODE:
                raise HTTPException(status_code=401, detail="Geçersiz kimlik belirteci")

    if config.DEV_MODE:
        return AuthUser(uid="dev-user", anonymous=True)

    raise HTTPException(status_code=401, detail="Kimlik doğrulama gerekli")
