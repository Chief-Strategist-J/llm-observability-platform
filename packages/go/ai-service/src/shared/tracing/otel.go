package tracing

import (
	"os"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/exporters/stdout/stdouttrace"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
)

func InitTracer(serviceName, environment string) (*sdktrace.TracerProvider, error) {
	exporter, err := stdouttrace.New(stdouttrace.WithPrettyPrint())
	if err != nil {
		return nil, err
	}

	hostname, _ := os.Hostname()
	if hostname == "" {
		hostname = "unknown"
	}

	tp := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exporter),
		sdktrace.WithResource(resource.NewWithAttributes(
			"",
			attribute.String("service.name", serviceName),
			attribute.String("deployment.env", environment),
			attribute.String("language.package-name", "github.com/llm-observability/platform/packages/go/ai-service"),
			attribute.String("service.version", "1.0.0"),
			attribute.String("semver", "1.0.0"),
			attribute.String("host.name", hostname),
		)),
	)

	otel.SetTracerProvider(tp)
	return tp, nil
}
