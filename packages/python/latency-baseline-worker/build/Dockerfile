FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .

RUN mkdir -p src/worker && touch src/worker/__init__.py
RUN pip install .

COPY src/ src/
COPY contracts/ contracts/
RUN pip install . --no-deps

ENV PYTHONPATH=/app/src
EXPOSE 8003

CMD ["python", "src/worker/index.py"]
