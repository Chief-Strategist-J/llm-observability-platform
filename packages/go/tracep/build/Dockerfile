# Stage 1: Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy dependencies files first to leverage Docker cache
COPY go.mod go.sum ./
RUN go mod download

# Copy the entire source code
COPY . .

# Build the server binary
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /app/traceserver ./src/main.go

# Stage 2: Final runtime stage
FROM alpine:3.18

RUN apk add --no-cache ca-certificates tzdata

WORKDIR /app

# Copy built binary from builder
COPY --from=builder /app/traceserver /app/traceserver
COPY --from=builder /app/database/migrations /app/database/migrations

# Expose ports: 4318 (Ingest), 4319 (Query API)
EXPOSE 4318 4319

# Set default env variables
ENV DB_PATH=/app/data/traces.db
ENV TRACE_TOKEN=""

# Run the binary
ENTRYPOINT ["/app/traceserver"]
