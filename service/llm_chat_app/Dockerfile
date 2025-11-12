FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV TEMPORAL_HOST=temporal:7233
ENV TEMPORAL_TASK_QUEUE=chat-service-queue

EXPOSE 8501

CMD ["python", "workers/chat_worker.py"]
