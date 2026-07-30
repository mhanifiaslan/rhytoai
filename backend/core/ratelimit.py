"""Bellek içi kayan pencere istek kotası (rate limiting).

Cloud Run tek instance varsayımıyla bellek içi sözlük yeterlidir; birden çok
instance açılırsa limit instance başına uygulanır (yumuşak sınır — kabul
edilebilir). Anahtar olarak Firebase ID token'ının özeti, yoksa istemci IP'si
kullanılır; token'ın kendisi bellekte tutulmaz.
"""
import hashlib
import time
from collections import deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from core.i18n import resolve_language
from core.messages import text

# LLM'e giden pahalı uçlar: daha sıkı kota
LLM_PREFIXES = ("/api/v1/reports", "/api/v1/chat")

# LLM kotasından muaf tutulan uçlar.
# Burç yorumu kullanıcıdan bağımsızdır ve paylaşımlı önbellekten servis edilir:
# dönem başına burç başına en fazla bir LLM çağrısı yapılır, gerisi önbellek
# okumasıdır. Kullanıcı burç şeridinde çiplere dokundukça saniyeler içinde
# 10 isteği geçebiliyor; ücretsiz katmanın omurgasını buna kurban etmemek için
# genel kotaya (dakikada 60) tabi tutulur.
LLM_EXEMPT_PREFIXES = ("/api/v1/reports/horoscope",)
LLM_LIMIT_PER_MINUTE = 10
DEFAULT_LIMIT_PER_MINUTE = 60
WINDOW_SECONDS = 60.0

# Kota dışı tutulan hafif uçlar.
# RevenueCat webhook'u da muaftır: tüm olaylar aynı Authorization başlığıyla
# gelir, yani tek bir kovayı paylaşırlar ve yoğun anlarda abonelik olayları
# düşerdi. Uç zaten paylaşılan gizli anahtarla korunuyor.
EXEMPT_PATHS = {"/", "/healthz", "/health", "/docs", "/openapi.json", "/redoc",
                "/api/v1/billing/revenuecat"}

# Kota mesajı dile göre core/messages.py'den gelir. Burası middleware olduğu
# için FastAPI bağımlılığı kullanılamaz; başlık doğrudan okunur.


class RateLimitMiddleware(BaseHTTPMiddleware):
    """uid/IP başına dakikalık kayan pencere kotası."""

    def __init__(self, app):
        super().__init__(app)
        # anahtar -> istek zaman damgaları (kayan pencere)
        self._hits: dict[str, deque[float]] = {}
        self._last_prune = time.monotonic()

    @staticmethod
    def _client_key(request: Request) -> str:
        auth = request.headers.get("authorization")
        if auth:
            # Token içeriğini saklamamak için özetini kullan
            return hashlib.sha256(auth.encode()).hexdigest()[:16]
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "anon"

    def _prune(self, now: float) -> None:
        """Boşalan kayıtları at — bellek büyümesini engelle."""
        if now - self._last_prune < 300:
            return
        self._last_prune = now
        stale = [key for key, dq in self._hits.items()
                 if not dq or now - dq[-1] > WINDOW_SECONDS]
        for key in stale:
            self._hits.pop(key, None)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if request.method == "OPTIONS" or path in EXEMPT_PATHS:
            return await call_next(request)

        is_llm = (path.startswith(LLM_PREFIXES)
                  and not path.startswith(LLM_EXEMPT_PREFIXES))
        limit = LLM_LIMIT_PER_MINUTE if is_llm else DEFAULT_LIMIT_PER_MINUTE
        # LLM ve genel kotalar ayrı sayaçlarda tutulur
        key = f"{'llm' if is_llm else 'std'}:{self._client_key(request)}"

        now = time.monotonic()
        self._prune(now)
        dq = self._hits.setdefault(key, deque())
        while dq and now - dq[0] > WINDOW_SECONDS:
            dq.popleft()

        if len(dq) >= limit:
            retry_after = max(1, int(WINDOW_SECONDS - (now - dq[0])) + 1)
            lang = resolve_language(request.headers.get("accept-language"))
            return JSONResponse(
                status_code=429,
                content={"status": "error", "detail": text("rate_limited", lang)},
                headers={"Retry-After": str(retry_after)},
            )

        dq.append(now)
        return await call_next(request)
