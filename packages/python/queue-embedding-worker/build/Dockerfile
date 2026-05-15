FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY pyproject.toml .

# Create a dummy src directory to cache dependencies
# The package name in pyproject.toml is queue-embedding-worker
# Usually the folder in src is named after the package (with underscores)
RUN mkdir -p src/worker && touch src/worker/__init__.py
RUN pip install . uvicorn fastapi

# Now copy the real source code and contracts
COPY src/ src/
COPY contracts/ contracts/
RUN pip install . --no-deps

# Expose the API port (for health/remote execution)
EXPOSE 8000

# Command to run the API
CMD ["uvicorn", "src.api.rest.v1.app:app", "--host", "0.0.0.0", "--port", "8000"]
