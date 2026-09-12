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

# LLM'e giden pahalı uçlar: daha sıkı kota.
#
# ## Neden yalnızca POST (KL-turu onarımı)
#
# Bu iki önek DAHA ÖNCE metot ayrımı yapmadan sıkı kotaya giriyordu ve
# altlarındaki UCUZ uçlar da aynı kovayı yakıyordu:
#   * `DELETE /api/v1/chat/conversations/{id}` — saf Firestore silme.
#     Kullanıcı sohbet listesinde 10 konuyu arka arkaya silince 429
#     görüyordu ("konuları silerken fazla istek" bulgusu, cihazdan).
#   * `GET /api/v1/reports/iching/status` — yalnız kota sayacı okur.
#   * `GET /api/v1/reports/signals` — günlük paylaşımlı önbellek; günde
#     en fazla bir üretim, gerisi okuma.
# Dahası: ÖNBELLEKTEN servis edilen rapor okumaları da (LLM hiç
# çalışmadan, jeton hiç düşmeden) aynı kovayı yiyordu — Atlas'ta birkaç
# detay ekranı gezen ABONE kullanıcı dakikada 10'u doldurup sohbete
# sıra gelmeden "yoğun talep" duvarına çarpıyordu.
#
# Üretim yapabilen her uç POST'tur (tek istisna GET /signals ve
# GET /horoscope — ikisi de gün/dönem başına tek üretimli paylaşımlı
# önbellek). Bu yüzden kural metoda bağlandı: okuma ve silme genel
# kotaya (dakikada 60) düşer, gerçek üretim sıkı kotada kalır.
LLM_PREFIXES = ("/api/v1/reports", "/api/v1/chat")

# LLM kotasından muaf tutulan uçlar.
# Burç yorumu kullanıcıdan bağımsızdır ve paylaşımlı önbellekten servis edilir:
# dönem başına burç başına en fazla bir LLM çağrısı yapılır, gerisi önbellek
# okumasıdır. Kullanıcı burç şeridinde çiplere dokundukça saniyeler içinde
# 10 isteği geçebiliyor; ücretsiz katmanın omurgasını buna kurban etmemek için
# genel kotaya (dakikada 60) tabi tutulur.
LLM_EXEMPT_PREFIXES = ("/api/v1/reports/horoscope",)
# 10 idi: sınıflandırma hatası yüzünden ucuz istekler de buradan yiyordu ve
# meşru gezinme duvara çarpıyordu. Asıl MALİYET kapısı artık jeton cüzdanı
# (RYTHO_TOKENS_ENFORCE=1 canlı); buradaki kota kaçak döngü ve kimliksiz
# sel koruması. 20, tek kullanıcının makul en yoğun dakikasının üstünde.
LLM_LIMIT_PER_MINUTE = 20
DEFAULT_LIMIT_PER_MINUTE = 60
WINDOW_SECONDS = 60.0

# Admin paneli kovası (AD2). Panel tek bir Authorization özetiyle çalışır
# ve bir sayfa açılışı 5-8 uç çağırır; Genel Bakış + Kullanıcılar + bir
# 360 gezintisi genel kotanın 60'ını bir dakikada bitiriyordu. Ayrı kova
# (`adm:` öneki) + kendi sınırı: panel trafiği mobil kotayı, mobil
# trafik panel kotasını YEMEZ. `/admin/collect` muaf kalır (EXEMPT_PATHS;
# scheduler'ın diğer işleriyle aynı başlığı paylaşıyor).
ADMIN_PREFIX = "/api/v1/admin/"
ADMIN_LIMIT_PER_MINUTE = 240

# Kota dışı tutulan hafif uçlar.
# RevenueCat webhook'u da muaftır: tüm olaylar aynı Authorization başlığıyla
# gelir, yani tek bir kovayı paylaşırlar ve yoğun anlarda abonelik olayları
# düşerdi. Uç zaten paylaşılan gizli anahtarla korunuyor.
# Zamanlayıcının toplu gönderim ucu da muaftır: tek bir Authorization başlığı
# taşıdığı için tüm çağrıları aynı kovayı paylaşır ve saatlik işler yoğun bir
# dakikada birbirini düşürebilirdi. Uç zaten paylaşılan gizli anahtarla korunuyor.
# İstatistik toplayıcı da muaftır (W5): scheduler'ın diğer uçlarıyla aynı
# Authorization başlığını (dolayısıyla aynı kovayı) paylaşır.
# Açılış yapılandırması da muaftır (PBZ): kimliksiz çağrıldığı için tüm
# istemciler NAT arkasında aynı IP kovasını paylaşabilir ve 429 istemcide
# "eşik okunamadı" sayılırdı — zorunlu güncelleme kapısı kotaya kurban
# edilmez.
EXEMPT_PATHS = {"/", "/healthz", "/health", "/docs", "/openapi.json", "/redoc",
                "/api/v1/billing/revenuecat", "/api/v1/notify/run",
                "/api/v1/admin/collect", "/api/v1/config/app"}

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

        # Yalnızca ÜRETEBİLEN istekler sıkı kotada (yukarıdaki gerekçe):
        # okuma/silme (GET, DELETE) genel kotaya düşer.
        is_llm = (request.method == "POST"
                  and path.startswith(LLM_PREFIXES)
                  and not path.startswith(LLM_EXEMPT_PREFIXES))
        is_admin = path.startswith(ADMIN_PREFIX)
        if is_admin:
            kova, limit = "adm", ADMIN_LIMIT_PER_MINUTE
        elif is_llm:
            kova, limit = "llm", LLM_LIMIT_PER_MINUTE
        else:
            kova, limit = "std", DEFAULT_LIMIT_PER_MINUTE
        # Admin, LLM ve genel kotalar ayrı sayaçlarda tutulur
        key = f"{kova}:{self._client_key(request)}"

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
