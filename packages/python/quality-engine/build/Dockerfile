FROM python:3.11-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

# Dummy source layout so egg_info / editable install passes
RUN touch README.md && mkdir -p src && touch src/__init__.py

# Install all dependencies
RUN pip install --no-cache-dir ".[dev]"

# Copy actual source
COPY src/ ./src/
COPY database/ ./database/
COPY scripts/ ./scripts/
COPY contracts/ ./contracts/

RUN pip install --no-cache-dir ".[dev]" --no-deps
RUN chmod +x scripts/*.sh

ENV PYTHONPATH=/app/src

EXPOSE 8080

CMD ["python", "-m", "worker.index"]
