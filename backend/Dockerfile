# RythoAI backend — Cloud Run imajı
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    RYTHO_DEV_MODE=0 \
    KNOWLEDGE_DIR=/app/knowledge

WORKDIR /app

# Yüz analizi v1 kapsamı dışında olduğu için mediapipe/opencv sistem
# kütüphaneleri (libgl1, libgles2, libegl1 ...) ve FaceLandmarker model
# indirmesi imajdan çıkarıldı — imaj boyutu ve soğuk başlatma süresi düşer.

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ /app/
COPY knowledge/ /app/knowledge/

RUN mkdir -p /app/cache

EXPOSE 8080
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
