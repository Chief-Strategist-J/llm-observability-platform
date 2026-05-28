FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .

RUN mkdir -p src/worker && touch src/worker/__init__.py
RUN pip install ".[dev]"

COPY src/ src/
COPY contracts/ contracts/
COPY service_owners.yaml service_owners.yaml
RUN pip install ".[dev]" --no-deps

EXPOSE 8001
EXPOSE 9464

CMD ["python", "src/worker/index.py"]
