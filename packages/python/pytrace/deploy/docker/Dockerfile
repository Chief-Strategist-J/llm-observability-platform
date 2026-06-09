# pylow distribution container
# Since pylow uses bpftrace / USDT / eBPF underneath, it requires access to the host's 
# kernel debug filesystem (/sys/kernel/debug), modules (/lib/modules), and headers.
FROM ubuntu:22.04

# Avoid prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies (bpftrace, python3, pip, and debug symbols helpers)
RUN apt-get update && apt-get install -y \
    bpftrace \
    python3 \
    python3-pip \
    linux-tools-common \
    linux-tools-generic \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy python packages
COPY . /app/

# Install the package locally in the container
RUN pip install .

# Make pylow wrapper available in PATH
ENTRYPOINT ["pylow"]
