# ============================================================================
# pylow — MCP Server Dockerfile
# ============================================================================
# Multi-stage build:
#   builder  — installs Python dependencies into /install
#   runtime  — minimal image with only what's needed to run the server
# ============================================================================

# ── Stage 1: builder ─────────────────────────────────────────────────────────
FROM python:3.10-slim AS builder

WORKDIR /build

# System build deps (for packages that compile C extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libffi-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only the project definition first (Docker cache layer)
COPY pyproject.toml README.md ./

# Install runtime deps into an isolated prefix so we can copy them cleanly
RUN pip install --no-cache-dir --prefix=/install "mcp>=1.27" ".[dev]" || \
    pip install --no-cache-dir --prefix=/install "mcp>=1.27"

# Copy source after deps are cached
COPY src/ ./src/

# Install the package itself (editable-style into /install)
RUN pip install --no-cache-dir --prefix=/install --no-deps -e .

# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.10-slim AS runtime

LABEL org.opencontainers.image.title="pylow-mcp"
LABEL org.opencontainers.image.description="pylow MCP server — zero-instrumentation observability toolkit"
LABEL org.opencontainers.image.version="0.1.12"

# Observability tools available to service scripts (curl, jq, tcpdump, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        jq \
        tcpdump \
        openssl \
        net-tools \
        iproute2 \
        procps \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY --from=builder /build/src /app/src

# Set PYTHONPATH so pylow_api and pytrace_* packages are importable
ENV PYTHONPATH=/app/src
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8765

WORKDIR /app

# Non-root user for security
RUN useradd -m -u 1000 pylow && chown -R pylow:pylow /app /tmp
USER pylow

EXPOSE 8765

# Default: run MCP server over Streamable-HTTP
# Override CMD to '--stdio' for Claude Desktop local config
CMD ["python", "-m", "pylow_api.mcp.server"]
