from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.auth import get_current_user
from services.iching_service import cast_iching, get_hexagram

router = APIRouter(dependencies=[Depends(get_current_user)])


class IChingQuery(BaseModel):
    question: Optional[str] = "Geleceğim ve Kozmik Yolculuğum"
    method: Literal["coins", "yarrow"] = "coins"


@router.post("/cast")
def cast(query: Optional[IChingQuery] = None):
    q = query.question if query and query.question else "Geleceğim"
    method = query.method if query else "coins"
    result = cast_iching(q, method=method)
    return {"status": "success", "hexagram": result}


@router.get("/hexagram/{number}")
def hexagram_detail(number: int):
    try:
        return {"status": "success", "hexagram": get_hexagram(number)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
