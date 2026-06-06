FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ALLOW_REAL_SOURCE_ADAPTERS=false \
    ENABLE_HF_RUNTIME_MODELS=false \
    MEMORY_MAX_RECORD_COUNT=500

WORKDIR /app

# FAISS requires the OpenMP runtime on slim Debian images.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.lock.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY main.py .env.example ./
COPY agent_runs.py ./
COPY agent_graph_storage.py ./
COPY core ./core
COPY schemas ./schemas
COPY video_generation ./video_generation
COPY source_adapters ./source_adapters
COPY scripts ./scripts
COPY tests ./tests
COPY data/reviews ./data/reviews
COPY docs ./docs
COPY static ./static
COPY runs/baselines ./runs/baselines

RUN mkdir -p /app/storage

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; port=os.getenv('PORT', '8001'); urllib.request.urlopen(f'http://127.0.0.1:{port}/healthz', timeout=3).read()"

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8001}"]
