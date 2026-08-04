from fastapi import APIRouter, Depends, HTTPException

from core.auth import get_current_user
from core.i18n import get_language
from core.messages import text
from services import prompts
from services.iching_service import get_hexagram

router = APIRouter(dependencies=[Depends(get_current_user)])

# /cast ucu SİLİNDİ (Revize İ0): kotasız ham çekim, mobil istemcinin hiç
# kullanmadığı bir yoldu ve "günde bir çekim" ritüel sınırını deliyordu.
# Çekim tek kapıdan: /api/v1/reports/iching (kota + cüzdan + rapor).


@router.get("/hexagram/{number}")
def hexagram_detail(number: int, lang: str = Depends(get_language)):
    """Heksagram sözlüğü — statik veri, LLM yok, ücretsiz.

    İ6'daki 64'lük kütüphane ekranının ucu. Yanıt localize'dan GEÇER:
    eskiden judgment_tr/judgment_en birlikte sızıyordu ve İngilizce
    istemci "judgment" alanını hiç alamıyordu.
    """
    try:
        return {"status": "success",
                "hexagram": prompts.localize_hexagram(lang,
                                                      get_hexagram(number))}
    except ValueError:
        raise HTTPException(status_code=404,
                            detail=text("hexagram_not_found", lang))
