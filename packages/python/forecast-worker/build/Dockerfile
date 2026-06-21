FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .

# Install PyTorch CPU-only first for efficiency
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

# Build and install the forecast-worker package
RUN mkdir -p src/worker && touch src/worker/__init__.py
RUN pip install .

COPY src/ src/
COPY contracts/ contracts/
RUN pip install . --no-deps

EXPOSE 8000

CMD ["python", "src/worker/index.py"]
