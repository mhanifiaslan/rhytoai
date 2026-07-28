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

# Önbellek arka ucu: "firestore" | "file".
# Cloud Run'da instance diski geçici ve instance'lar arası paylaşımsızdır; burç
# yorumu gibi kullanıcıdan bağımsız içerikler ancak paylaşımlı bir arka uçla
# "tüm kullanıcılar için tek LLM çağrısı" garantisini verebilir.
# Varsayılan DEV_MODE'a bağlanır: lokalde dosya, üretimde Firestore.
CACHE_BACKEND: str = os.getenv(
    "RYTHO_CACHE_BACKEND", "file" if DEV_MODE else "firestore"
).strip().lower()

# Firestore önbellek koleksiyonu. Bu koleksiyona `expiresAt` alanı üzerinden
# native TTL politikası tanımlanmalıdır; aksi halde süresi dolan dokümanlar
# yalnızca okuma anında temizlenir.
CACHE_COLLECTION: str = os.getenv("RYTHO_CACHE_COLLECTION", "aiCache")

GEONAMES_USERNAME: str | None = os.getenv("GEONAMES_USERNAME")

# RevenueCat webhook'u icin paylasilan gizli anahtar. RevenueCat panelinde
# webhook'a "Authorization" basligi olarak tanimlanir. Tanimsizsa webhook ucu
# tum istekleri reddeder — abonelik durumu yazan tek yol bu oldugu icin
# dogrulamasiz calismasina izin verilmez.
REVENUECAT_WEBHOOK_SECRET: str | None = os.getenv("REVENUECAT_WEBHOOK_SECRET")
