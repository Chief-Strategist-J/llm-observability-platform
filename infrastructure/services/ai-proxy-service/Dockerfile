FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl && \
    rm -rf /var/lib/apt/lists/* && \
    useradd --create-home --shell /bin/bash appuser

# Copy requirements and install Python dependencies
COPY infrastructure/services/ai-proxy-service/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY service/ai-proxy-service/ ./service/ai-proxy-service/

# Set Python path to include the service directory
ENV PYTHONPATH=/app

EXPOSE 8001

USER appuser

CMD ["uvicorn", "service.ai-proxy-service.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
