from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import shutil
import os
from services.deepface_service import analyze_face
from services.gemini_service import generate_face_reading_summary, chat_with_cosmic_confidant

router = APIRouter()

class ChatMessageItem(BaseModel):
    sender: str
    text: str

class ChatRequest(BaseModel):
    history: List[ChatMessageItem] = []
    message: str

@router.post("/analyze")
async def process_face_image(file: UploadFile = File(...)):
    try:
        # Save uploaded file temporarily
        temp_file = f"temp_{file.filename}"
        with open(temp_file, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Analyze using DeepFace
        result = analyze_face(temp_file)
        
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
            
        # Enrich with Gemini LLM Summary
        summary = generate_face_reading_summary(
            age=result.get("age", 25),
            gender=result.get("gender", "Unknown"),
            emotion=result.get("emotion", "neutral"),
            wu_xing=result.get("wu_xing_element", "Toprak"),
            san_ting=result.get("san_ting_balance", "Dengeli")
        )
        result["face_reading_summary"] = summary
            
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat_with_confidant(request: ChatRequest):
    try:
        history_dicts = [{"sender": item.sender, "text": item.text} for item in request.history]
        reply = chat_with_cosmic_confidant(history_dicts, request.message)
        return {"status": "success", "reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
