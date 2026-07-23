"""Basit dosya tabanlı TTL önbelleği.

Gemini yorumları kullanıcı+gün bazında önbelleklenir; aynı gün içinde aynı
sorgu için token maliyeti oluşmaz. Cloud Run'da instance diski geçicidir,
bu kabul edilebilir bir trade-off'tur (en kötü durumda yorum yeniden üretilir).
"""
import hashlib
import json
import time
from typing import Any

from core import config


def _path_for(key: str):
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]
    return config.CACHE_DIR / f"{digest}.json"


def get(key: str) -> Any | None:
    path = _path_for(key)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload["expires_at"] < time.time():
            path.unlink(missing_ok=True)
            return None
        return payload["value"]
    except Exception:
        return None


def set(key: str, value: Any, ttl_seconds: int = 24 * 3600) -> None:
    path = _path_for(key)
    payload = {"expires_at": time.time() + ttl_seconds, "value": value}
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
