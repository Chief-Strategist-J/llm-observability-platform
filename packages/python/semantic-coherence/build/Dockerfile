FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .

RUN mkdir -p src/api && touch src/api/__init__.py
RUN pip install ".[dev]"

COPY src/ src/
COPY contracts/ contracts/

RUN pip install ".[dev]" --no-deps

EXPOSE 8005
EXPOSE 9468

CMD ["uvicorn", "api.rest.v1.app:app", "--host", "0.0.0.0", "--port", "8005"]
