"""Korpus vektörlerini DERLEME ZAMANINDA üretir.

Neden gerekli: vektörler daha önce çalışma zamanında üretilip
`config.CACHE_DIR`'a yazılıyordu ve o dizin Cloud Run'da **geçici disk**.
Korpus 12 parçayken bu görünmüyordu; gerçek bir kitapla (~900 parça) her
soğuk başlatma 900 embedding çağrısı demek — gecikme, fatura, ve ilk
isteklerde aramanın sessizce anahtar kelime moduna düşmesi.

Bu betik vektörleri `knowledge/embeddings/{dil}.json` altına yazar; dosya
imaja kopyalanır ve çalışma zamanında yalnızca OKUNUR.

Artımlıdır: her parça kendi metninin sağlamasıyla anahtarlandığı için
korpusa bir bölüm eklemek yalnızca yeni parçaları vektörletir.

Kullanım:
    GEMINI_API_KEY=... .venv/Scripts/python.exe scripts/build_embeddings.py
    ... --check      (vektörletmeden yalnızca kapsama raporu; CI için)
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import config, i18n  # noqa: E402
from services import rag_service  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("build_embeddings")


def dil_isle(lang: str, sadece_kontrol: bool) -> bool:
    """Bir dilin vektörlerini günceller. Kapsama tamsa ``True``."""
    chunks = rag_service._load_chunks(lang)
    if not chunks:
        logger.warning("[%s] korpus bos, atlaniyor.", lang)
        return True

    # Model degistiyse read_artifact bos doner; tum korpus yeniden vektorlenir.
    vektorler = dict(rag_service.read_artifact(lang))
    eksik = [c for c in chunks if c.chunk_id not in vektorler]

    logger.info("[%s] %d parca, %d eksik vektor.",
                lang, len(chunks), len(eksik))

    if sadece_kontrol:
        if eksik:
            logger.error("[%s] KAPSAMA EKSIK: %d parcanin vektoru yok.",
                         lang, len(eksik))
        return not eksik

    if eksik:
        if not config.GEMINI_API_KEY:
            logger.error("[%s] GEMINI_API_KEY yok; vektor uretilemez.", lang)
            return False
        taban = rag_service.base_for(lang)
        yeni = taban._embed_texts([c.text for c in eksik])
        if not yeni:
            logger.error("[%s] Embedding uretilemedi.", lang)
            return False
        for chunk, emb in zip(eksik, yeni):
            vektorler[chunk.chunk_id] = np.asarray(emb, dtype=np.float32)

    # Korpustan cikarilan parcalarin vektorleri temizlenir; aksi halde dosya
    # her duzenlemede buyur ve imaj siser.
    gecerli = {c.chunk_id for c in chunks}
    atilan = [k for k in vektorler if k not in gecerli]
    for k in atilan:
        del vektorler[k]
    if atilan:
        logger.info("[%s] %d bayat vektor temizlendi.", lang, len(atilan))

    # Yazma sirasi korpus sirasi olsun: artefakti gozle incelemek kolaylasir.
    sirali = {c.chunk_id: vektorler[c.chunk_id] for c in chunks}
    rag_service.write_artifact(lang, sirali)

    meta_path, vec_path = rag_service.embedding_files(lang)
    boyut = (meta_path.stat().st_size + vec_path.stat().st_size) / 1024 / 1024
    logger.info("[%s] %s + %s yazildi (%d vektor, %.1f MB).",
                lang, meta_path.name, vec_path.name, len(sirali), boyut)
    return True


def main() -> int:
    ayristirici = argparse.ArgumentParser(description=__doc__)
    ayristirici.add_argument(
        "--check", action="store_true",
        help="Vektor uretme; yalnizca kapsama raporla (CI icin).")
    ayristirici.add_argument(
        "--lang", action="append",
        help="Yalnizca bu dil(ler). Varsayilan: hepsi.")
    args = ayristirici.parse_args()

    diller = args.lang or list(i18n.SUPPORTED)
    tamam = all(dil_isle(lang, args.check) for lang in diller)
    if not tamam:
        logger.error("Vektor uretimi eksik tamamlandi.")
        return 1
    logger.info("Tamam.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
