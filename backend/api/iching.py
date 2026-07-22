from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from services.iching_service import cast_iching

router = APIRouter()

class IChingQuery(BaseModel):
    question: Optional[str] = "Geleceğim ve Kozmik Yolculuğum"

@router.post("/cast")
def cast_coins(query: Optional[IChingQuery] = None):
    q = query.question if query and query.question else "Geleceğim"
    result = cast_iching(q)
    return {"status": "success", "hexagram": result}

@router.get("/cast")
def cast_coins_get(question: str = "Geleceğim"):
    result = cast_iching(question)
    return {"status": "success", "hexagram": result}
