FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml setup.py ./
COPY src/ ./src/

RUN pip install --no-cache-dir .

CMD ["python"]
