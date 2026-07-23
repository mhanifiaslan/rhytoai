from fastapi import APIRouter, Depends, HTTPException

from core.auth import get_current_user
from services.sky_service import get_sky_now

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/now")
def sky_now():
    try:
        return {"status": "success", "data": get_sky_now()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
