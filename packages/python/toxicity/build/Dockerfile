FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir ".[dev]"

RUN python -c "from optimum.onnxruntime import ORTModelForSequenceClassification; from transformers import AutoTokenizer; ORTModelForSequenceClassification.from_pretrained('unitary/toxic-bert', export=True); AutoTokenizer.from_pretrained('unitary/toxic-bert')"

COPY contracts/ contracts/

FROM python:3.12-slim AS runtime

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/src /app/src
COPY --from=builder /app/contracts /app/contracts
COPY --from=builder /root/.cache /root/.cache

ENV PYTHONPATH=/app/src
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV TOXICITY_MODEL_ID=unitary/toxic-bert

EXPOSE 8007

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8007/health')"

CMD ["uvicorn", "api.rest.v1.app:app", "--host", "0.0.0.0", "--port", "8007"]
