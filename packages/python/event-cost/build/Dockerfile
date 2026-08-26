FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .

RUN mkdir -p src/event_cost/worker && touch src/event_cost/__init__.py src/event_cost/worker/__init__.py
RUN pip install ".[dev]"

COPY src/ src/
COPY contracts/ contracts/
RUN pip install ".[dev]" --no-deps

EXPOSE 8001

CMD ["python", "src/event_cost/worker/index.py"]
