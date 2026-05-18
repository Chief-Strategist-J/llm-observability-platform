FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://github.com/grafana/tempo/releases/download/v2.3.0/tempo_2.3.0_linux_amd64.tar.gz && \
    tar -xvf tempo_2.3.0_linux_amd64.tar.gz && \
    mv tempo /usr/local/bin/tempo && \
    rm -rf tempo_2.3.0_linux_amd64.tar.gz tempo-cli tempo-query CHANGELOG.md LICENSE README.md

RUN wget https://dl.grafana.com/oss/release/grafana_10.2.2_amd64.deb && \
    apt-get update && \
    apt-get install -y ./grafana_10.2.2_amd64.deb && \
    rm grafana_10.2.2_amd64.deb

COPY pyproject.toml .

RUN mkdir -p src/instrumentation_sdk && touch src/instrumentation_sdk/__init__.py
RUN pip install . uvicorn

COPY src/ src/
RUN pip install . --no-deps

COPY build/tempo-config.yaml /app/build/tempo-config.yaml
COPY build/grafana-datasource.yaml /etc/grafana/provisioning/datasources/ds.yaml
COPY build/grafana-datasource.yaml /usr/share/grafana/conf/provisioning/datasources/ds.yaml
COPY build/entrypoint.sh /app/build/entrypoint.sh

RUN chmod +x /app/build/entrypoint.sh

EXPOSE 8000 3000 3200 4317

ENTRYPOINT ["/app/build/entrypoint.sh"]
