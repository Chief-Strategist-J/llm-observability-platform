FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /service-registry .

FROM alpine:3.19

RUN apk add --no-cache ca-certificates
COPY --from=builder /service-registry /usr/local/bin/service-registry

EXPOSE 31426

ENTRYPOINT ["service-registry"]
