# Stage 1: Chef — computes dependency recipe
FROM rust:1.85-slim-bookworm AS chef
RUN apt-get update && apt-get install -y pkg-config libssl-dev && rm -rf /var/lib/apt/lists/*
RUN cargo install cargo-chef --locked
WORKDIR /usr/src/app

# Stage 2: Planner — generates recipe.json from Cargo files only
FROM chef AS planner
COPY . .
RUN cargo chef prepare --recipe-path recipe.json

# Stage 3: Builder — deps layer cached unless Cargo.toml/Cargo.lock change
FROM chef AS builder
COPY --from=planner /usr/src/app/recipe.json recipe.json
RUN cargo chef cook --release --recipe-path recipe.json
COPY . .
RUN cargo build --release

# Stage 4: Runtime — unchanged
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y ca-certificates curl && rm -rf /var/lib/apt/lists/*
WORKDIR /usr/local/bin
COPY --from=builder /usr/src/app/target/release/dtae-server .
EXPOSE 8090
ENV RUST_LOG=info
ENV DTAE_BIND_ADDR=0.0.0.0:8090
CMD ["./dtae-server"]
