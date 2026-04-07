FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir \
    psutil \
    pynvml \
    torch \
    transformers \
    accelerate \
    bitsandbytes \
    huggingface_hub \
    pyyaml \
    flask \
    requests

COPY . .

RUN chmod +x scripts/dev/entrypoint.sh scripts/dev/start_model.sh scripts/setup/download_model.sh

ENV PYTHONUNBUFFERED=1
ENV APP_TYPE=bash

ENTRYPOINT ["/app/scripts/dev/entrypoint.sh"]

CMD ["bash"]
