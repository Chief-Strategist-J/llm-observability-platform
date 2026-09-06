FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
COPY scripts ./scripts
COPY contracts ./contracts

RUN pip install --no-cache-dir opentelemetry-sdk pytest

ENV PYTHONPATH=/app/src

CMD ["bash", "scripts/run.sh"]
