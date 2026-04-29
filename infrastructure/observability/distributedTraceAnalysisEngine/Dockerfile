# Stage 1: Builder
FROM rust:1.85-slim-bookworm AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

# Copy the source code
COPY . .

# Build the application in release mode
RUN cargo build --release

# Stage 2: Runtime
FROM debian:bookworm-slim

# Install runtime dependencies (ca-certificates for HTTPS/rustls)
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/local/bin

# Copy the binary from the builder stage
COPY --from=builder /usr/src/app/target/release/dtae-server .

# Expose the default port
EXPOSE 8090

# Set environment variables
ENV RUST_LOG=info
ENV DTAE_BIND_ADDR=0.0.0.0:8090

# Run the binary
CMD ["./dtae-server"]
