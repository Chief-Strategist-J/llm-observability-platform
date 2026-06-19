package tracer

import (
	"context"
	"fmt"
	"os"
	"sync"
	"time"

	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/codes"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.21.0"
	"go.opentelemetry.io/otel/trace"
)

type activeTrace struct {
	mu       sync.Mutex
	rootSpan trace.Span
	spans    map[string]trace.Span
	ctx      context.Context
}

// TracerService manages the telemetry lifecycle and trace active state.
type TracerService struct {
	tp         *sdktrace.TracerProvider
	exporter   sdktrace.SpanExporter
	otelTracer trace.Tracer
	mu         sync.RWMutex
	traces     map[string]*activeTrace
}

// NewTracerService initializes the service with standard OTel settings.
func NewTracerService(endpoint, apiKey, service string) (*TracerService, error) {
	if os.Getenv("OTEL_EXPORTER_OTLP_PROTOCOL") == "" {
		os.Setenv("OTEL_EXPORTER_OTLP_PROTOCOL", "http/json")
	}
	if os.Getenv("OTEL_EXPORTER_OTLP_TRACES_PROTOCOL") == "" {
		os.Setenv("OTEL_EXPORTER_OTLP_TRACES_PROTOCOL", "http/json")
	}

	ctx := context.Background()

	opts := []otlptracehttp.Option{
		otlptracehttp.WithHeaders(map[string]string{
			"Authorization": "Bearer " + apiKey,
		}),
	}

	cleanEndpoint := endpoint
	if len(endpoint) > 7 && endpoint[:7] == "http://" {
		cleanEndpoint = endpoint[7:]
		opts = append(opts, otlptracehttp.WithInsecure())
	} else if len(endpoint) > 8 && endpoint[:8] == "https://" {
		cleanEndpoint = endpoint[8:]
	}

	opts = append(opts, otlptracehttp.WithEndpoint(cleanEndpoint))

	exporter, err := otlptracehttp.New(ctx, opts...)
	if err != nil {
		return nil, fmt.Errorf("failed to create OTLP trace exporter: %w", err)
	}

	hostname, _ := os.Hostname()
	if hostname == "" {
		hostname = "unknown"
	}

	res, err := resource.New(ctx,
		resource.WithAttributes(
			semconv.ServiceNameKey.String(service),
			attribute.String("host.name", hostname),
		),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to create resource: %w", err)
	}

	tp := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(
			exporter,
			sdktrace.WithMaxExportBatchSize(50),
			sdktrace.WithBatchTimeout(1*time.Second),
		),
		sdktrace.WithResource(res),
	)

	otelTracer := tp.Tracer("tracep-sdk")

	return &TracerService{
		tp:         tp,
		exporter:   exporter,
		otelTracer: otelTracer,
		traces:     make(map[string]*activeTrace),
	}, nil
}

// Close flushes and shuts down the tracer provider.
func (s *TracerService) Close() error {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	return s.tp.Shutdown(ctx)
}

// Start starts a root trace span and returns its Trace ID (tid).
func (s *TracerService) Start(name string) string {
	ctx := context.Background()
	ctx, span := s.otelTracer.Start(ctx, name)
	tid := span.SpanContext().TraceID().String()

	s.mu.Lock()
	s.traces[tid] = &activeTrace{
		rootSpan: span,
		spans:    make(map[string]trace.Span),
		ctx:      ctx,
	}
	s.mu.Unlock()

	return tid
}

// Trace adds or appends a step/event to a trace span under the given tid.
func (s *TracerService) Trace(tid, class, function, step, message string, opts ...TraceOption) {
	options := TraceOptions{
		Level: "info",
	}
	for _, opt := range opts {
		opt(&options)
	}

	s.mu.RLock()
	at, exists := s.traces[tid]
	s.mu.RUnlock()

	if !exists {
		return
	}

	at.mu.Lock()
	defer at.mu.Unlock()

	key := class + "." + function
	span, spanExists := at.spans[key]

	if !spanExists {
		parentCtx := at.ctx
		if options.Parent != "" {
			var parentSpan trace.Span
			for k, sp := range at.spans {
				if k == options.Parent || (len(k) > len(options.Parent) && k[len(k)-len(options.Parent)-1:] == "."+options.Parent) {
					parentSpan = sp
					break
				}
			}
			if parentSpan != nil {
				parentCtx = trace.ContextWithSpan(at.ctx, parentSpan)
			}
		}

		_, span = s.otelTracer.Start(parentCtx, class+"."+function, trace.WithAttributes(
			attribute.String("code.namespace", class),
			attribute.String("code.function", function),
		))
		at.spans[key] = span
	}

	attrs := []attribute.KeyValue{
		attribute.String("message", message),
		attribute.String("level", options.Level),
	}
	span.AddEvent(step, trace.WithAttributes(attrs...))
}

// End ends all open spans for the trace and flushes.
func (s *TracerService) End(tid string, status string) {
	s.mu.Lock()
	at, exists := s.traces[tid]
	if exists {
		delete(s.traces, tid)
	}
	s.mu.Unlock()

	if !exists {
		return
	}

	at.mu.Lock()
	defer at.mu.Unlock()

	var otelStatus codes.Code
	statusMsg := "trace ended with status " + status
	if status == "error" {
		otelStatus = codes.Error
	} else {
		otelStatus = codes.Ok
	}

	for _, span := range at.spans {
		span.SetStatus(otelStatus, statusMsg)
		span.End()
	}

	at.rootSpan.SetStatus(otelStatus, statusMsg)
	at.rootSpan.End()

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	_ = s.tp.ForceFlush(ctx)
}
