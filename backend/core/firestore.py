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

from core import config, gcp_credentials

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

    # `firestore.client()` kimlik bilgisi yoksa ADC çözümlemesine giriyor ve
    # bu çağrı ölçülen ortamda ~12 saniye sürüyordu. Yoklama o beklemeyi
    # önlüyor.
    #
    # `_failed` BURADA KURULMUYOR ve bu kritik. İlk sürümde kuruluyordu ve
    # kalıcı bir mandal olduğu için tek bir sonuçsuz yoklama Firestore'u
    # instance ömrü boyunca kapatıyordu: üretimde abonelik webhook'ları 500
    # döndü, kullanıcı ödeme yaptı ve ekranlar kilitli kaldı.
    #
    # Kalıcı mandal yalnızca istemci GERÇEKTEN kurulamadığında kurulur
    # (aşağıdaki `except`). Kimlik bilgisinin o an görünmemesi geçici olabilir
    # ve `gcp_credentials` zaten süreli olarak yeniden yokluyor.
    if not gcp_credentials.available():
        logger.warning("Kimlik bilgisi henüz yok; Firestore bu istekte atlandı.")
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
