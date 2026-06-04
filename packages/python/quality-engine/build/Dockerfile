FROM python:3.11-slim AS base

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

COPY src/ ./src/
COPY database/ ./database/
COPY scripts/ ./scripts/

RUN chmod +x scripts/*.sh

ENV PYTHONPATH=/app/src

EXPOSE 8080

CMD ["python", "-m", "worker.index"]
