FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src/ src/
COPY tests/ tests/

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir ".[dev,gpt2]"

COPY contracts/ contracts/

RUN SKIP_CONSOLE_EXPORTER=true SKIP_OTLP_EXPORTER=true \
    pytest tests/ --tb=short -q


FROM python:3.12-slim AS runtime

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/src /app/src
COPY --from=builder /app/contracts /app/contracts

ENV PYTHONPATH=/app/src
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV GPT2_MODEL_PATH=gpt2
ENV SKIP_CONSOLE_EXPORTER=false
ENV SKIP_OTLP_EXPORTER=true

EXPOSE 8007

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8007/health')"

CMD ["uvicorn", "api.rest.v1.app:app", "--host", "0.0.0.0", "--port", "8007"]
