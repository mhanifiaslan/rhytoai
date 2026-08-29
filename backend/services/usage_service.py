"""AI kullanım telemetrisi — her GERÇEK LLM çağrısının izi (AP-turu).

## Neden var

Bu ana kadar model çağrısı başına token/maliyet HİÇ ölçülmüyordu;
maliyet çalışması (docs/maliyet-calismasi.md) statik tahminlerle
yaşıyordu ve "AI geliri − AI maliyeti" sorusunun canlı cevabı yoktu.
Bu modül her başarılı ``generate_content`` dönüşünde ``usageEvents``
koleksiyonuna küçük bir kayıt düşer; admin paneli (AI sekmesi +
Kullanıcı 360) buradan beslenir.

## Duruş

* **Asla isteği düşürmez** — tamamı try/except; telemetri yan üründür.
* **Senkron best-effort** — çağıran uçlar senkron ``def`` (threadpool'da
  koşarlar), tek Firestore yazımı ~50-100 ms; saniyeler süren LLM
  çağrısının yanında görünmez. Thread/BackgroundTasks BİLEREK yok:
  Cloud Run yanıt döndükten sonra CPU'yu kısar, arka planda bırakılan
  yazım yarım kalabilir.
* **Yalnız gerçek çağrılar** — uygulama önbelleği isabetinde
  gemini_service hiç çağrılmadığı için buraya da düşmez; kesilme
  retry'ında HER çağrı ayrı kayıttır (ikisi de faturalanır).

## Ölçek notu

Bugünkü ölçekte (onlarca çağrı/gün) çağrı başına bir yazım ihmal.
Kullanıcı sayısı binlere çıkarsa örnekleme ya da günlük toplama
(rollup) bu modüle eklenir; okuyan uçlar `day` alanı üzerinden zaten
gün bazlı çalışıyor.
"""
from __future__ import annotations

import datetime as dt
import logging

from core import firestore as firestore_client

logger = logging.getLogger(__name__)

# Birim fiyatlar (USD / milyon token) — docs/maliyet-calismasi.md §1.
# Düşünme token'ları ÇIKTI fiyatından faturalanır (S-turu ölçümü);
# önbelleklenmiş girdi indirimi ihmal (cached hep 0 bekleniyor).
_USD_PER_M_INPUT = 0.30
_USD_PER_M_OUTPUT = 2.50


def _int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def record(feature: str, model: str, response, latency_ms: int,
           uid: str | None = None) -> None:
    """Tek çağrının izini yazar; hata yalnız loglanır."""
    try:
        client = firestore_client.get_client()
        if client is None:
            return

        md = getattr(response, "usage_metadata", None)
        prompt_t = _int(getattr(md, "prompt_token_count", 0))
        output_t = _int(getattr(md, "candidates_token_count", 0))
        thinking_t = _int(getattr(md, "thoughts_token_count", 0))
        cached_t = _int(getattr(md, "cached_content_token_count", 0))

        est_cost = (prompt_t * _USD_PER_M_INPUT
                    + (output_t + thinking_t) * _USD_PER_M_OUTPUT) / 1_000_000

        now = dt.datetime.now(dt.timezone.utc)
        client.collection("usageEvents").document().set({
            "uid": uid,
            "feature": feature or "unknown",
            "model": model,
            "promptTokens": prompt_t,
            "outputTokens": output_t,
            "thinkingTokens": thinking_t,
            "cachedTokens": cached_t,
            "estCostUsd": round(est_cost, 8),
            "latencyMs": int(latency_ms),
            "at": now,
            # adminStats günüyle hizalı gün anahtarı (UTC) — gün sorguları
            # aralık filtresi yerine eşitlikle çalışsın (indekssiz).
            "day": now.date().isoformat(),
        })
    except Exception as exc:
        logger.info("Kullanım kaydı yazılamadı (%s): %s", feature, exc)
