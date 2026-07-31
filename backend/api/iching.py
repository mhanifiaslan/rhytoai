from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.auth import get_current_user
from core.i18n import get_language
from core.messages import text
from services import prompts
from services.iching_service import cast_iching, get_hexagram

router = APIRouter(dependencies=[Depends(get_current_user)])


class IChingQuery(BaseModel):
    question: Optional[str] = "Geleceğim ve Kozmik Yolculuğum"
    method: Literal["coins", "yarrow"] = "coins"


@router.post("/cast")
def cast(query: Optional[IChingQuery] = None,
         lang: str = Depends(get_language)):
    q = query.question if query and query.question else "Geleceğim"
    method = query.method if query else "coins"
    result = cast_iching(q, method=method)
    return {"status": "success",
            "hexagram": prompts.localize_iching(lang, result)}


@router.get("/hexagram/{number}")
def hexagram_detail(number: int, lang: str = Depends(get_language)):
    try:
        return {"status": "success", "hexagram": get_hexagram(number)}
    except ValueError:
        raise HTTPException(status_code=404,
                            detail=text("hexagram_not_found", lang))
