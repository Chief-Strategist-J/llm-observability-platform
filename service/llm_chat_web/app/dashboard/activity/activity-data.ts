import { Settings, FileText, Activity as ActivityIcon, Cloud, Database, BarChart, PlayCircle, CheckCircle, RefreshCw, LucideIcon } from "lucide-react"

export interface ActivitySchema {
    inputs: Record<string, {
        type: string
        description: string
        required?: boolean
    }>
    outputs: Record<string, {
        type: string
        description: string
    }>
}

export interface ActivityComponent {
    id: string
    name: string
    icon: LucideIcon
    category: string
    description: string
}

export interface CustomActivity {
    id: string
    name: string
    description: string
    category: string
    inputs: { name: string; type: string; description: string; required: boolean }[]
    outputs: { name: string; type: string; description: string }[]
    code: string
    createdAt: string
}

export const activitySchemas: Record<string, ActivitySchema> = {
    "http-request": {
        inputs: {
            method: { type: "select", description: "HTTP method", required: true },
            url: { type: "string", description: "Request URL", required: true },
            headers: { type: "json", description: "HTTP headers" },
            queryParams: { type: "json", description: "Query parameters" },
            pathParams: { type: "json", description: "Path parameters" },
            body: { type: "json", description: "Request body" }
        },
        outputs: {
            status: { type: "number", description: "HTTP status code" },
            data: { type: "json", description: "Response data" },
            headers: { type: "json", description: "Response headers" }
        }
    },
    "configure-service": {
        inputs: {
            serviceName: { type: "string", description: "Service name (e.g., prometheus, grafana)", required: true },
            configPath: { type: "string", description: "Configuration file path", required: true },
            configuration: { type: "json", description: "Service configuration", required: true }
        },
        outputs: {
            success: { type: "boolean", description: "Configuration status" },
            configFile: { type: "string", description: "Generated config file path" },
            message: { type: "string", description: "Status message" }
        }
    },
    "generate-config": {
        inputs: {
            templateType: { type: "string", description: "Config template type", required: true },
            parameters: { type: "json", description: "Template parameters", required: true },
            outputPath: { type: "string", description: "Output file path", required: true }
        },
        outputs: {
            configPath: { type: "string", description: "Generated config path" },
            content: { type: "string", description: "Config content" }
        }
    },
    "deploy-processor": {
        inputs: {
            processorType: { type: "string", description: "Processor type (logs/metrics/traces)", required: true },
            configuration: { type: "json", description: "Processor configuration", required: true },
            replicas: { type: "number", description: "Number of replicas" }
        },
        outputs: {
            deploymentId: { type: "string", description: "Deployment ID" },
            status: { type: "string", description: "Deployment status" },
            endpoints: { type: "array", description: "Service endpoints" }
        }
    },
    "configure-logs": {
        inputs: {
            sourcePaths: { type: "array", description: "Log file paths", required: true },
            logFormat: { type: "string", description: "Log format (json/text)", required: true },
            filters: { type: "json", description: "Log filters" }
        },
        outputs: {
            configured: { type: "boolean", description: "Configuration status" },
            sources: { type: "array", description: "Configured sources" }
        }
    },
    "configure-metrics": {
        inputs: {
            scrapeInterval: { type: "string", description: "Scrape interval (e.g., 15s)", required: true },
            targets: { type: "array", description: "Scrape targets", required: true },
            labels: { type: "json", description: "Additional labels" }
        },
        outputs: {
            configId: { type: "string", description: "Configuration ID" },
            activeTargets: { type: "number", description: "Active target count" }
        }
    },
    "configure-tracing": {
        inputs: {
            samplingRate: { type: "number", description: "Sampling rate (0-1)", required: true },
            exportEndpoint: { type: "string", description: "Trace export endpoint", required: true },
            serviceName: { type: "string", description: "Service name", required: true }
        },
        outputs: {
            tracerId: { type: "string", description: "Tracer ID" },
            configured: { type: "boolean", description: "Configuration status" }
        }
    },
    "create-datasource": {
        inputs: {
            datasourceType: { type: "string", description: "Datasource type (prometheus/loki/jaeger)", required: true },
            url: { type: "string", description: "Datasource URL", required: true },
            name: { type: "string", description: "Datasource name", required: true }
        },
        outputs: {
            datasourceId: { type: "string", description: "Created datasource ID" },
            uid: { type: "string", description: "Datasource UID" }
        }
    },
    "emit-test-event": {
        inputs: {
            eventType: { type: "string", description: "Event type (log/metric/trace)", required: true },
            payload: { type: "json", description: "Event payload", required: true }
        },
        outputs: {
            eventId: { type: "string", description: "Emitted event ID" },
            timestamp: { type: "string", description: "Event timestamp" }
        }
    },
    "verify-ingestion": {
        inputs: {
            eventId: { type: "string", description: "Event ID to verify", required: true },
            timeout: { type: "number", description: "Verification timeout (seconds)" }
        },
        outputs: {
            verified: { type: "boolean", description: "Verification status" },
            latency: { type: "number", description: "Ingestion latency (ms)" }
        }
    },
    "restart-service": {
        inputs: {
            serviceName: { type: "string", description: "Service to restart", required: true },
            gracefulShutdown: { type: "boolean", description: "Graceful shutdown" }
        },
        outputs: {
            restarted: { type: "boolean", description: "Restart status" },
            downtime: { type: "number", description: "Downtime (seconds)" }
        }
    }
}

export const activityComponents: ActivityComponent[] = [
    { id: "http-request", name: "HTTP Request", icon: Cloud, category: "general", description: "Make HTTP/HTTPS requests" },
    { id: "configure-service", name: "Configure Service", icon: Settings, category: "configuration", description: "Configure infrastructure services" },
    { id: "generate-config", name: "Generate Config", icon: FileText, category: "configuration", description: "Generate configuration files" },
    { id: "deploy-processor", name: "Deploy Processor", icon: PlayCircle, category: "deployment", description: "Deploy processing components" },
    { id: "configure-logs", name: "Configure Logs", icon: FileText, category: "logs", description: "Configure log sources and paths" },
    { id: "configure-metrics", name: "Configure Metrics", icon: BarChart, category: "metrics", description: "Configure metrics collection" },
    { id: "configure-tracing", name: "Configure Tracing", icon: ActivityIcon, category: "tracing", description: "Configure distributed tracing" },
    { id: "create-datasource", name: "Create Datasource", icon: Database, category: "configuration", description: "Create Grafana datasource" },
    { id: "emit-test-event", name: "Emit Test Event", icon: PlayCircle, category: "testing", description: "Emit test events for validation" },
    { id: "verify-ingestion", name: "Verify Ingestion", icon: CheckCircle, category: "testing", description: "Verify event ingestion" },
    { id: "restart-service", name: "Restart Service", icon: RefreshCw, category: "deployment", description: "Restart infrastructure service" },
]

export const categoryColors: Record<string, string> = {
    general: "bg-cyan-500",
    configuration: "bg-purple-500",
    deployment: "bg-blue-500",
    logs: "bg-orange-500",
    metrics: "bg-green-500",
    tracing: "bg-yellow-500",
    testing: "bg-pink-500",
    custom: "bg-emerald-500",
}
