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

# 1 => DEV_MODE'un anonim "dev-user"i admin sayilir (W4). AYRI bayrak,
# bilerek: DEV_MODE tek basina yonetim yetkisi VEREMEZ — verseydi her yerel
# calistirma admin uclarini acardi. Uretimde ASLA 1 olmamali.
DEV_ADMIN: bool = os.getenv("RYTHO_DEV_ADMIN", "0") == "1"

# SABİT SÜRÜM — takma ad DEĞİL (S-turu).
#
# Varsayılan `gemini-flash-latest` idi ve bu bir takma ad: arkasındaki model
# haber vermeden değişiyor. Değişti de. Ölçülen sonuç: `thinking_budget: 0`
# artık uygulanmıyor, `thinking_level: "minimal"` ise 400 veriyor. Aynı soru
# 6 kez soruldu, **3'ü** düşünme bütçeyi yiyip kesildi ve kullanıcıya yarım
# cümle gösterildi. Yani bir gece içinde, biz hiçbir şey değiştirmeden,
# sohbetin yarısı bozuldu.
#
# Aday karşılaştırması (aynı soru, aynı ayar, 4'er çağrı):
#
#     gemini-flash-latest   2/4 kesik   ort. 191 token boşa düşünme
#     gemini-3.7-flash      2/4 kesik   ort. 196 token boşa düşünme
#     gemini-3.5-flash      0/4 kesik   0 düşünme   en düşük gecikme
#
# `gemini-3.5-flash` düşünme kontrolüne uyan tek aday. Yan fayda maliyet:
# düşünme token'ları ÇIKTI fiyatından faturalanıyor ($2,50/M), yani boşa
# düşünme sohbet turu başına ~%24 ek gider demekti.
#
# Model yükseltmesi artık BİLİNÇLİ bir karar: `GEMINI_MODEL` ortam
# değişkeniyle denenir, ölçülür, sonra varsayılan değiştirilir.
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
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

# Cloud Scheduler'in toplu bildirim ucunu tetiklerken tasidigi paylasilan
# gizli anahtar. Tanimsizken uc 503 doner: acik birakmak, herkesin tum
# kullanicilara bildirim gonderebilmesi demek olurdu.
NOTIFY_SCHEDULER_SECRET: str | None = os.getenv("NOTIFY_SCHEDULER_SECRET")


def _int_env(ad: str, varsayilan: int) -> int:
    """Bozuk değerde varsayılana düşer — sürüm kapısı FAIL-OPEN kalmalı:
    yanlış yazılmış bir env yüzünden tüm kullanıcıları kilitlemek,
    kapının önleyeceği her sorundan daha kötüdür."""
    try:
        return int(os.getenv(ad, str(varsayilan)))
    except ValueError:
        return varsayilan


# Zorunlu güncelleme kapısı (F3): istemci versionCode'u bundan KÜÇÜKSE
# uygulama güncelleme ekranına kilitlenir. 0 = kimse engellenmez.
# Kalıcı değer infra/deploy-backend.ps1'deki --set-env-vars satırında —
# gcloud ile elle verilen değer bir sonraki deploy'da silinir.
MIN_APP_BUILD: int = _int_env("RYTHO_MIN_BUILD", 0)
