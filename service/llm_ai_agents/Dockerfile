ARG CUDA_VERSION=12.1.1
FROM nvidia/cuda:${CUDA_VERSION}-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    python3.10-venv \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip \
    && pip3 install --no-cache-dir -r requirements.txt

COPY scripts/ scripts/
RUN chmod +x scripts/dev/entrypoint.sh \
              scripts/dev/start_model.sh \
              scripts/setup/download_model.sh

COPY . .

ENV APP_TYPE=agent

ENTRYPOINT ["/app/scripts/dev/entrypoint.sh"]
CMD ["bash"]