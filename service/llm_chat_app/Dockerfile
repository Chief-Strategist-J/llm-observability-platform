# syntax=docker/dockerfile:1.4
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Step 1: Install system dependencies with apt cache mount
# This layer is cached unless you change the package list
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Step 2: Copy ONLY requirements.txt first
# This layer is cached unless requirements.txt changes
COPY requirements.txt .

# Step 3: Install Python dependencies with pip cache mount
# This layer is cached unless requirements.txt changes
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip && \
    pip install --prefer-binary -r requirements.txt

# Step 4: Create directories needed by application
# This layer is cached unless you change these commands
RUN mkdir -p /app/chat_backups

# Step 5: Copy application code LAST
# Only this layer rebuilds when you change Python files
COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]