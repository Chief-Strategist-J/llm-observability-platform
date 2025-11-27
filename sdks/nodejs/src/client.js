// Node.js/JavaScript Observability Client
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-grpc');
const { OTLPMetricExporter } = require('@opentelemetry/exporter-metrics-otlp-grpc');
const { OTLPLogExporter } = require('@opentelemetry/exporter-logs-otlp-grpc');
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');
const { trace, metrics } = require('@opentelemetry/api');
const { logs } = require('@opentelemetry/api-logs');

class ObservabilityClient {
    constructor({
        serviceName,
        serviceVersion = '1.0.0',
        environment = process.env.ENVIRONMENT || 'development',
        otelEndpoint = process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4317',
        resourceAttributes = {}
    }) {
        this.serviceName = serviceName;
        this.serviceVersion = serviceVersion;
        this.environment = environment;
        this.otelEndpoint = otelEndpoint;
        
        // Build resource
        const resource = new Resource({
            [SemanticResourceAttributes.SERVICE_NAME]: serviceName,
            [SemanticResourceAttributes.SERVICE_VERSION]: serviceVersion,
            [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: environment,
            ...resourceAttributes
        });
        
        // Initialize SDK
        this.sdk = new NodeSDK({
            resource,
            traceExporter: new OTLPTraceExporter({ url: otelEndpoint }),
            metricReader: new OTLPMetricExporter({ url: otelEndpoint }),
            logRecordProcessor: new OTLPLogExporter({ url: otelEndpoint }),
            instrumentations: [getNodeAutoInstrumentations()],
        });
        
        this.sdk.start();
        
        // Get providers
        this.tracer = trace.getTracer(serviceName, serviceVersion);
        this.meter = metrics.getMeter(serviceName, serviceVersion);
        this.logger = new StructuredLogger(serviceName);
        this.metrics = new MetricsClient(this.meter);
    }
    
    async shutdown() {
        await this.sdk.shutdown();
    }
}

class StructuredLogger {
    constructor(serviceName) {
        this.serviceName = serviceName;
    }
    
    info(message, attributes = {}) {
        console.log(JSON.stringify({
            level: 'info',
            service: this.serviceName,
            message,
            ...attributes,
            timestamp: new Date().toISOString()
        }));
    }
    
    error(message, attributes = {}) {
        console.error(JSON.stringify({
            level: 'error',
            service: this.serviceName,
            message,
            ...attributes,
            timestamp: new Date().toISOString()
        }));
    }
    
    warning(message, attributes = {}) {
        console.warn(JSON.stringify({
            level: 'warning',
            service: this.serviceName,
            message,
            ...attributes,
            timestamp: new Date().toISOString()
        }));
    }
}

class MetricsClient {
    constructor(meter) {
        this.meter = meter;
        this.counters = {};
        this.histograms = {};
    }
    
    counter(name, value = 1, attributes = {}) {
        if (!this.counters[name]) {
            this.counters[name] = this.meter.createCounter(name);
        }
        this.counters[name].add(value, attributes);
    }
    
    histogram(name, value, attributes = {}) {
        if (!this.histograms[name]) {
            this.histograms[name] = this.meter.createHistogram(name);
        }
        this.histograms[name].record(value, attributes);
    }
}

// Singleton instance
let clientInstance = null;

function initObservability(config) {
    clientInstance = new ObservabilityClient(config);
    return clientInstance;
}

function getClient() {
    if (!clientInstance) {
        throw new Error('Observability client not initialized. Call initObservability() first.');
    }
    return clientInstance;
}

module.exports = {
    ObservabilityClient,
    initObservability,
    getClient
};
