FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir ".[dev]"

COPY contracts/ contracts/


FROM python:3.12-slim AS runtime

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/src /app/src
COPY --from=builder /app/contracts /app/contracts

ENV PYTHONPATH=/app/src
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV EMBEDDING_WORKER_URL=http://localhost:8080
ENV PRIMARY_SCORER=minilm
ENV SCORERS=minilm

EXPOSE 8005

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8005/health')"

CMD ["uvicorn", "api.rest.v1.app:app", "--host", "0.0.0.0", "--port", "8005"]
