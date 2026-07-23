import logging
import os
import shutil
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from core.auth import AuthUser, get_current_user
from services import report_service
from services.face_service import analyze_face

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analyze")
async def process_face_image(
    file: UploadFile = File(...),
    user: AuthUser = Depends(get_current_user),
):
    tmp_path = None
    try:
        suffix = os.path.splitext(file.filename or "photo.jpg")[1] or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        result = analyze_face(tmp_path)
        if "error" in result:
            raise HTTPException(status_code=422, detail=result["error"])

        report = report_service.face_report(user.uid, result)
        result["face_reading_summary"] = report["text"]
        return {"status": "success", "data": result}
    except HTTPException:
        raise
    except Exception:
        # Traceback'i logla; kullanıcıya iç detay sızdırmadan kısa Türkçe mesaj döndür
        logger.exception("Yüz analizi başarısız oldu")
        raise HTTPException(
            status_code=500,
            detail="Yüz analizi sırasında beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar deneyin.",
        )
    finally:
        # Fotoğraf analiz sonrası SİLİNİR — KVKK/GDPR gereği sunucuda tutulmaz
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
