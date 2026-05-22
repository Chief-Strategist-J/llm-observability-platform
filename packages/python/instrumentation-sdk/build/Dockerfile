FROM python:3.12-slim

ARG WITH_KAFKA="false"
ENV WITH_KAFKA=${WITH_KAFKA}

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN if [ "$WITH_KAFKA" = "true" ] ; then \
        apt-get update && apt-get install -y default-jre-headless postgresql postgresql-contrib postgresql-17-pgvector && rm -rf /var/lib/apt/lists/* && \
        wget https://archive.apache.org/dist/kafka/3.6.0/kafka_2.13-3.6.0.tgz && \
        tar -xzf kafka_2.13-3.6.0.tgz -C /opt && \
        mv /opt/kafka_2.13-3.6.0 /opt/kafka && \
        rm kafka_2.13-3.6.0.tgz ; \
    fi

ENV PATH="/opt/kafka/bin:${PATH}"

RUN wget https://github.com/grafana/tempo/releases/download/v2.3.0/tempo_2.3.0_linux_amd64.tar.gz && \
    tar -xvf tempo_2.3.0_linux_amd64.tar.gz && \
    mv tempo /usr/local/bin/tempo && \
    rm -rf tempo_2.3.0_linux_amd64.tar.gz tempo-cli tempo-query CHANGELOG.md LICENSE README.md

RUN wget https://dl.grafana.com/oss/release/grafana_10.2.2_amd64.deb && \
    apt-get update && \
    apt-get install -y ./grafana_10.2.2_amd64.deb && \
    rm grafana_10.2.2_amd64.deb

RUN wget https://github.com/prometheus/prometheus/releases/download/v2.48.0/prometheus-2.48.0.linux-amd64.tar.gz && \
    tar -xvf prometheus-2.48.0.linux-amd64.tar.gz && \
    mv prometheus-2.48.0.linux-amd64/prometheus /usr/local/bin/ && \
    mkdir -p /etc/prometheus && \
    rm -rf prometheus-2.48.0.linux-amd64*

COPY pyproject.toml .

RUN mkdir -p src/instrumentation_sdk && touch src/instrumentation_sdk/__init__.py
RUN pip install . uvicorn

COPY src/ src/
COPY config/ /app/config/
COPY database/ /app/database/
COPY scripts/ /app/scripts/
RUN pip install . --no-deps

COPY build/tempo-config.yaml /app/build/tempo-config.yaml
COPY build/grafana-datasource.yaml /etc/grafana/provisioning/datasources/ds.yaml
COPY build/grafana-datasource.yaml /usr/share/grafana/conf/provisioning/datasources/ds.yaml
COPY build/grafana-dashboard-provider.yaml /etc/grafana/provisioning/dashboards/provider.yaml
COPY build/grafana-dashboard-provider.yaml /usr/share/grafana/conf/provisioning/dashboards/provider.yaml
COPY build/dashboards/ /etc/grafana/provisioning/dashboards/json/
COPY build/prometheus.yml /etc/prometheus/prometheus.yml
COPY build/entrypoint.sh /app/build/entrypoint.sh

RUN chmod +x /app/build/entrypoint.sh

EXPOSE 8000 3000 3200 4317 9464 9090

ENTRYPOINT ["/app/build/entrypoint.sh"]
