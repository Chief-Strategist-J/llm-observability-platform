FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
RUN mkdir -p src/worker && touch src/worker/__init__.py
RUN pip install --no-cache-dir ".[dev]"

COPY src/ src/
COPY tests/ tests/
COPY contracts/ contracts/

RUN pip install --no-cache-dir ".[dev]" --no-deps

# Run unit tests to verify correctness during build
RUN SKIP_CONSOLE_EXPORTER=true SKIP_OTLP_EXPORTER=true \
    pytest tests/ --tb=short -q

FROM python:3.12-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/src /app/src
COPY --from=builder /app/pyproject.toml /app/pyproject.toml
COPY --from=builder /app/contracts /app/contracts


ENV PYTHONPATH=/app/src
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV SKIP_CONSOLE_EXPORTER=false
ENV SKIP_OTLP_EXPORTER=true

EXPOSE 8002

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

CMD ["python", "src/worker/index.py"]
