FROM python:3.11-slim AS base

WORKDIR /app

# Install build dependencies if needed (e.g. for confluent-kafka or psycopg compiles)
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

# Create dummy source layout so setuptools egg_info / editable install check passes
RUN touch README.md && mkdir -p src && touch src/__init__.py

# Install dependencies and cache this layer
RUN pip install --no-cache-dir ".[dev]"

# Copy actual source files
COPY src/ ./src/
COPY database/ ./database/
COPY scripts/ ./scripts/
COPY contracts/ ./contracts/

# Install the actual package code
RUN pip install --no-cache-dir ".[dev]" --no-deps

RUN chmod +x scripts/*.sh

ENV PYTHONPATH=/app/src

EXPOSE 8080

CMD ["python", "-m", "worker.index"]
