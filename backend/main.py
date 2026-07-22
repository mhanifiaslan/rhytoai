from fastapi import FastAPI
from api.astrology import router as astrology_router
from api.face_reading import router as face_reading_router
from api.iching import router as iching_router

app = FastAPI(title="Cosmic Social AI - Backend", version="1.0.0")

app.include_router(astrology_router, prefix="/api/v1/astrology", tags=["Astrology"])
app.include_router(face_reading_router, prefix="/api/v1/face-reading", tags=["Face Reading"])
app.include_router(iching_router, prefix="/api/v1/iching", tags=["I Ching"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Cosmic Social AI Engine"}
