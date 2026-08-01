"""Ortak Firestore istemcisi.

Firestore istemcisi birden çok serviste (önbellek, kullanıcı hafızası,
bildirim) gerekiyor; her birinde ayrı tembel başlatma kopyası tutmak yerine
tek yerden veriliyor.

Cloud Run'da Application Default Credentials kullanılır. İstemci
oluşturulamazsa ``None`` döner — çağıranlar bu durumda özelliği sessizce
devre dışı bırakır, isteği düşürmez.
"""
from __future__ import annotations

import logging
import threading

from core import config

logger = logging.getLogger(__name__)

_client = None
_lock = threading.Lock()
_failed = False


def get_client():
    """Firestore istemcisini döndürür; kurulamazsa ``None``."""
    global _client, _failed
    if _client is not None:
        return _client
    if _failed:
        return None

    with _lock:
        if _client is None and not _failed:
            try:
                import firebase_admin
                from firebase_admin import firestore

                if not firebase_admin._apps:
                    firebase_admin.initialize_app(
                        options={"projectId": config.GOOGLE_CLOUD_PROJECT}
                    )
                _client = firestore.client()
            except Exception as exc:
                logger.warning("Firestore istemcisi kurulamadı: %s", exc)
                _failed = True
    return _client
