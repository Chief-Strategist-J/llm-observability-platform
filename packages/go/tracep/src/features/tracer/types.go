package tracer

// TraceOptions holds optional values for Trace.
type TraceOptions struct {
	Parent string
	Level  string
}

// TraceOption is a function that configures TraceOptions.
type TraceOption func(*TraceOptions)

// WithParent sets the parent function name.
func WithParent(parent string) TraceOption {
	return func(o *TraceOptions) {
		o.Parent = parent
	}
}

// WithLevel sets the log/event level.
func WithLevel(level string) TraceOption {
	return func(o *TraceOptions) {
		o.Level = level
	}
}
