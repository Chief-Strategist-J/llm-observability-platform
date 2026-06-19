package tracep

import "github.com/llm-observability/platform/packages/go/tracep/src/features/tracer"

// Tracer is a type alias for the TracerService.
type Tracer = tracer.TracerService

// TraceOption is a type alias for the TraceOption function.
type TraceOption = tracer.TraceOption

// WithParent sets the parent function name for context propagation.
var WithParent = tracer.WithParent

// WithLevel sets the log/event level.
var WithLevel = tracer.WithLevel

// New initializes the Tracer.
func New(endpoint, apiKey, service string) (*Tracer, error) {
	return tracer.NewTracerService(endpoint, apiKey, service)
}
