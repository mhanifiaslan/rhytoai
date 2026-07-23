"""RythoAI Backend — Kozmik hesaplama ve AI yorum motoru.

Cloud Run üzerinde çalışacak şekilde tasarlanmıştır:
- CORS açık (Flutter Web dahil tüm istemciler)
- Firebase ID token doğrulama (RYTHO_DEV_MODE=0 iken zorunlu)
- /healthz canlılık ucu
"""
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.astrology import router as astrology_router
from api.bazi import router as bazi_router
from api.chat import router as chat_router
from api.face_reading import router as face_reading_router
from api.iching import router as iching_router
from api.notify import router as notify_router
from api.reports import router as reports_router
from api.sky import router as sky_router
from core.ratelimit import RateLimitMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RythoAI Cosmic Engine",
    version="2.0.0",
    description=(
        "Swiss Ephemeris tabanlı astroloji, BaZi, I Ching, yüz analizi (Mian Xiang "
        "+ Kıyafetname) ve RAG destekli Gemini yorum servisi."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# İstek kotası: LLM uçları 10/dk, diğerleri 60/dk (bkz. core/ratelimit.py)
app.add_middleware(RateLimitMiddleware)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Temel güvenlik başlıkları — API yanıtlarının tarayıcıda kötüye
    kullanılmasını zorlaştırır."""
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault(
        "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
    )
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Beklenmeyen hatalarda stack trace sızdırmadan Türkçe 500 yanıtı döner;
    ayrıntı yalnızca sunucu loguna yazılır."""
    logger.exception("İşlenmeyen hata: %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "detail": (
                "Beklenmeyen bir kozmik parazit oluştu. Ekibimiz durumu "
                "inceliyor; lütfen kısa bir süre sonra tekrar dene."
            ),
        },
    )

app.include_router(astrology_router, prefix="/api/v1/astrology", tags=["Astrology"])
app.include_router(bazi_router, prefix="/api/v1/bazi", tags=["BaZi"])
app.include_router(iching_router, prefix="/api/v1/iching", tags=["I Ching"])
app.include_router(face_reading_router, prefix="/api/v1/face-reading", tags=["Face Reading"])
app.include_router(sky_router, prefix="/api/v1/sky", tags=["Sky"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(reports_router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(notify_router, prefix="/api/v1/notify", tags=["Notify"])


@app.get("/")
def read_root():
    return {"service": "RythoAI Cosmic Engine", "version": "2.0.0", "docs": "/docs"}


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
