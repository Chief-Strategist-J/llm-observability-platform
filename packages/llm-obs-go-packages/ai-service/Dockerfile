FROM golang:1.21-alpine AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY src/ ./src/

RUN CGO_ENABLED=0 go test ./...
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o ai-service src/main.go

FROM alpine:3.19

WORKDIR /app

COPY --from=builder /app/ai-service .

EXPOSE 8080

CMD ["./ai-service"]
