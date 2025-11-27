package observability

import (
	"context"
	"log"
	"os"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
	"go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetricgrpc"
	"go.opentelemetry.io/otel/metric"
	"go.opentelemetry.io/otel/sdk/metric"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	"go.opentelemetry.io/otel/sdk/resource"
	semconv "go.opentelemetry.io/otel/semconv/v1.17.0"
	"go.opentelemetry.io/otel/trace"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

// Client provides unified observability for Go services
type Client struct {
	ServiceName    string
	ServiceVersion string
	Environment    string
	OtelEndpoint   string
	
	Tracer trace.Tracer
	Meter  metric.Meter
	Logger *StructuredLogger
	
	tracerProvider *sdktrace.TracerProvider
	meterProvider  *metric.MeterProvider
}

// NewClient creates a new observability client
func NewClient(serviceName, serviceVersion string, opts ...Option) (*Client, error) {
	c := &Client{
		ServiceName:    serviceName,
		ServiceVersion: serviceVersion,
		Environment:    getEnv("ENVIRONMENT", "development"),
		OtelEndpoint:   getEnv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317"),
	}
	
	// Apply options
	for _, opt := range opts {
		opt(c)
	}
	
	// Initialize resource
	res, err := resource.New(
		context.Background(),
		resource.WithAttributes(
			semconv.ServiceName(c.ServiceName),
			semconv.ServiceVersion(c.ServiceVersion),
			semconv.DeploymentEnvironment(c.Environment),
		),
	)
	if err != nil {
		return nil, err
	}
	
	// Initialize tracing
	if err := c.initTracing(res); err != nil {
		return nil, err
	}
	
	// Initialize metrics
	if err := c.initMetrics(res); err != nil {
		return nil, err
	}
	
	// Initialize logging
	c.Logger = NewStructuredLogger(c.ServiceName)
	
	return c, nil
}

func (c *Client) initTracing(res *resource.Resource) error {
	ctx := context.Background()
	
	conn, err := grpc.DialContext(ctx, c.OtelEndpoint,
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithBlock(),
	)
	if err != nil {
		return err
	}
	
	traceExporter, err := otlptracegrpc.New(ctx, otlptracegrpc.WithGRPCConn(conn))
	if err != nil {
		return err
	}
	
	bsp := sdktrace.NewBatchSpanProcessor(traceExporter)
	c.tracerProvider = sdktrace.NewTracerProvider(
		sdktrace.WithSampler(sdktrace.AlwaysSample()),
		sdktrace.WithResource(res),
		sdktrace.WithSpanProcessor(bsp),
	)
	
	otel.SetTracerProvider(c.tracerProvider)
	c.Tracer = c.tracerProvider.Tracer(c.ServiceName)
	
	return nil
}

func (c *Client) initMetrics(res *resource.Resource) error {
	ctx := context.Background()
	
	metricExporter, err := otlpmetricgrpc.New(ctx,
		otlpmetricgrpc.WithEndpoint(c.OtelEndpoint),
		otlpmetricgrpc.WithInsecure(),
	)
	if err != nil {
		return err
	}
	
	c.meterProvider = metric.NewMeterProvider(
		metric.WithResource(res),
		metric.WithReader(metric.NewPeriodicReader(metricExporter)),
	)
	
	otel.SetMeterProvider(c.meterProvider)
	c.Meter = c.meterProvider.Meter(c.ServiceName)
	
	return nil
}

// Shutdown gracefully shuts down and flushes telemetry
func (c *Client) Shutdown(ctx context.Context) error {
	if err := c.tracerProvider.Shutdown(ctx); err != nil {
		return err
	}
	if err := c.meterProvider.Shutdown(ctx); err != nil {
		return err
	}
	return nil
}

// StructuredLogger provides structured logging
type StructuredLogger struct {
	serviceName string
}

// NewStructuredLogger creates a new structured logger
func NewStructuredLogger(serviceName string) *StructuredLogger {
	return &StructuredLogger{serviceName: serviceName}
}

// Info logs an info message with structured fields
func (l *StructuredLogger) Info(msg string, fields map[string]interface{}) {
	log.Printf("[INFO] [%s] %s %v", l.serviceName, msg, fields)
}

// Error logs an error message with structured fields
func (l *StructuredLogger) Error(msg string, fields map[string]interface{}) {
	log.Printf("[ERROR] [%s] %s %v", l.serviceName, msg, fields)
}

// Warning logs a warning message with structured fields
func (l *StructuredLogger) Warning(msg string, fields map[string]interface{}) {
	log.Printf("[WARN] [%s] %s %v", l.serviceName, msg, fields)
}

// Option is a functional option for Client
type Option func(*Client)

// WithEnvironment sets the environment
func WithEnvironment(env string) Option {
	return func(c *Client) {
		c.Environment = env
	}
}

// WithOtelEndpoint sets the OTel endpoint
func WithOtelEndpoint(endpoint string) Option {
	return func(c *Client) {
		c.OtelEndpoint = endpoint
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// Helper to create span with attributes
func (c *Client) StartSpan(ctx context.Context, name string, attrs ...attribute.KeyValue) (context.Context, trace.Span) {
	return c.Tracer.Start(ctx, name, trace.WithAttributes(attrs...))
}
