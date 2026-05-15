FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY pyproject.toml .

# Create a dummy src directory to cache dependencies
RUN mkdir -p src/instrumentation_sdk && touch src/instrumentation_sdk/__init__.py
RUN pip install . uvicorn

# Now copy the real source code
COPY src/ src/
RUN pip install . --no-deps


# Expose the API port
EXPOSE 8000

# Command to run the API
CMD ["uvicorn", "src.api.rest.v1.app:app", "--host", "0.0.0.0", "--port", "8000"]
