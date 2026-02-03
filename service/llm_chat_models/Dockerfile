FROM python:3.11-slim

WORKDIR /app

COPY service/llm_chat_models/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the specific service
COPY service/llm_chat_models /app/service/llm_chat_models

# Copy the infrastructure module for observability
COPY infrastructure /app/infrastructure

# Set PYTHONPATH to /app so imports work from root
ENV PYTHONPATH=/app

WORKDIR /app/service/llm_chat_models

CMD ["python", "-m", "application.main"]
