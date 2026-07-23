# RythoAI backend — Cloud Run imajı
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    RYTHO_DEV_MODE=0 \
    KNOWLEDGE_DIR=/app/knowledge

WORKDIR /app

# mediapipe/opencv için sistem kütüphaneleri
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ /app/
COPY knowledge/ /app/knowledge/

EXPOSE 8080
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
