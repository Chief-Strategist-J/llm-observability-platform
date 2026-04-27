FROM python:3.12-slim

WORKDIR /app

COPY infrastructure/observability/dependencies/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt requests

COPY . /app

EXPOSE 8113
CMD ["python", "-m", "infrastructure.observability.logIntelligent.api.run"]
