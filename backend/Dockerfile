# RythoAI backend — Cloud Run imajı
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    RYTHO_DEV_MODE=0 \
    KNOWLEDGE_DIR=/app/knowledge

WORKDIR /app

# mediapipe/opencv için sistem kütüphaneleri
# (libgles2 + libegl1: mediapipe >=0.10.30 libmediapipe.so, libGLESv2.so.2 ve libEGL.so.1'e bağlıdır)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libgles2 libegl1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ /app/
COPY knowledge/ /app/knowledge/

# FaceLandmarker modelini imaja göm (runtime'da indirme gerekmesin)
RUN mkdir -p /app/cache && python -c "import urllib.request; urllib.request.urlretrieve('https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task', '/app/cache/face_landmarker.task')"

EXPOSE 8080
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
