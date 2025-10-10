FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy from build context (service directory)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY __init__.py .
COPY adapters/ ./adapters/
COPY api/ ./api/
COPY core/ ./core/
COPY config/ ./config/

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
