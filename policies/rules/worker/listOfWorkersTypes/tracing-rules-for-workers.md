
Tracing Rules for Workers
Temporal workers: workflow spans are created by the SDK interceptor. Activity spans are created per activity execution.
Queue workers: a root span is created when a job is dequeued, before the processor is called.
Cron workers: a root span is created when the schedule fires, before the handler is called.
Event workers: W3C traceparent is extracted from message attributes and used as the parent span.
Every worker span carries: service.name, worker.type, worker.task_queue or worker.queue_name, deployment.env.
Workflow ID and run ID are included as span attributes on every Temporal span.
Activity type and attempt number are included as span attributes on every activity span.
No worker ships to production without trace-check.sh confirming spans are flowing to the collector.

Worker Health Check Rules
Every worker exposes a health endpoint or a health-check.sh script that returns 0 if healthy.
Temporal workers: health check verifies the Temporal server connection and namespace availability.
Queue workers: health check verifies the broker connection and queue accessibility.
Cron workers: health check verifies the scheduler connection.
Event workers: health check verifies the broker connection and consumer group registration.
Health check timeout is 5 seconds maximum.