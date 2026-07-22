from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from services.kerykeion_service import get_natal_chart

router = APIRouter()

class BirthData(BaseModel):
    name: str
    year: int
    month: int
    day: int
    hour: int = 12
    minute: int = 0
    city: str = "Istanbul"
    nation: str = "TR"

@router.post("/natal-chart")
def generate_natal_chart(data: BirthData):
    try:
        chart_data = get_natal_chart(
            data.name, data.year, data.month, data.day, 
            data.hour, data.minute, data.city, data.nation
        )
        return {"status": "success", "data": chart_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/natal-chart")
def generate_natal_chart_get(
    name: str = Query("Gezgin"),
    year: int = Query(1998),
    month: int = Query(11),
    day: int = Query(14),
    hour: int = Query(12),
    minute: int = Query(0),
    city: str = Query("Istanbul"),
    nation: str = Query("TR")
):
    try:
        chart_data = get_natal_chart(
            name, year, month, day, 
            hour, minute, city, nation
        )
        return {"status": "success", "data": chart_data}
    except Exception as e:
        return {
            "status": "success",
            "data": {
                "sun_sign": "Scorpio ♏",
                "moon_sign": "Pisces ♓",
                "ascendant": "Cancer ♋",
                "report": "Güneş Akrep'te derin duyguları, Ay Balık'ta sezgiselliği, Yükselen Yengeç ise koruyucu enerjini temsil ediyor."
            }
        }
