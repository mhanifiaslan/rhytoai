"""RythoAI Backend — Kozmik hesaplama ve AI yorum motoru.

Cloud Run üzerinde çalışacak şekilde tasarlanmıştır:
- CORS açık (Flutter Web dahil tüm istemciler)
- Firebase ID token doğrulama (RYTHO_DEV_MODE=0 iken zorunlu)
- /healthz canlılık ucu
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.astrology import router as astrology_router
from api.bazi import router as bazi_router
from api.chat import router as chat_router
from api.face_reading import router as face_reading_router
from api.iching import router as iching_router
from api.notify import router as notify_router
from api.reports import router as reports_router
from api.sky import router as sky_router

logging.basicConfig(level=logging.INFO)

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
