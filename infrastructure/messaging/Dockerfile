FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY infrastructure/ ./infrastructure/
COPY application/ ./application/
COPY domain/ ./domain/

RUN pip install --upgrade pip setuptools wheel

RUN pip install -e .

RUN pip install -e .[dev,schema-registry,app]

EXPOSE 8000 8200 8201

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from infrastructure.messaging import MessagingSDK; print('OK')" || exit 1

CMD ["python", "-m", "pytest", "tests/", "-v"]
