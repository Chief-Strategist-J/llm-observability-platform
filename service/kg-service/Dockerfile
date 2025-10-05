FROM python:3.11-slim
WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gcc g++ \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install -U pip && pip install --no-cache-dir -r requirements.txt


# Dockerfile
RUN pip install "en_core_web_sm@https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1.tar.gz"


COPY . .
RUN mkdir -p logs

EXPOSE 8002

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8002"]
