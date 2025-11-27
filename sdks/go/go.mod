module github.com/yourcompany/observability-sdk-go

go 1.21

require (
	go.opentelemetry.io/otel v1.21.0
	go.opentelemetry.io/otel/sdk v1.21.0
	go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc v1.21.0
	go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetricgrpc v0.44.0
	google.golang.org/grpc v1.60.0
)
