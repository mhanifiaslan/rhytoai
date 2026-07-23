"""Merkezi yapılandırma — tüm ortam değişkenleri buradan okunur."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BACKEND_DIR.parent

GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
GOOGLE_CLOUD_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT", "rhytoai")
GOOGLE_CLOUD_LOCATION: str = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# 1 => Firebase token yoksa da isteklere izin ver (lokal gelistirme)
DEV_MODE: bool = os.getenv("RYTHO_DEV_MODE", "1") == "1"

GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "gemini-embedding-2")

# Bilgi tabanı dizini: Docker imajında /app/knowledge, lokalde repo kökü.
_knowledge_env = os.getenv("KNOWLEDGE_DIR", "").strip()
if _knowledge_env:
    KNOWLEDGE_DIR = Path(_knowledge_env)
elif (BACKEND_DIR / "knowledge").exists():
    KNOWLEDGE_DIR = BACKEND_DIR / "knowledge"
else:
    KNOWLEDGE_DIR = REPO_DIR / "knowledge"

CACHE_DIR = Path(os.getenv("RYTHO_CACHE_DIR", str(BACKEND_DIR / "cache")))
CACHE_DIR.mkdir(parents=True, exist_ok=True)

GEONAMES_USERNAME: str | None = os.getenv("GEONAMES_USERNAME")
