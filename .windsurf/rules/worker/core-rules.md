Core Rules
Every worker is a separate package with its own contracts, database, scripts, and deploy config.
No worker imports source from another worker or service package.
No worker shares a database or schema with another package.
Every worker has its own task queue or queue name — never shared.
All cross-package calls go through generated clients from shared/contracts/.
Every worker emits OTEL trace spans. No worker ships without tracing.
Every worker has its own scripts/ — minimum run.sh, test.sh, and health-check.sh.
Workers are registered in shared/worker-registry.yaml. A missing entry fails CI.
===
Worker-registry.yaml Format

Every worker is registered here. A missing entry fails CI. The registry is the single source of truth for what workers exist, what queues they own, and who owns them.

workers:
  - name:        temporal-payment-worker
    type:        temporal
    language:    python
    task_queue:  payment-tasks
    owner:       @payments-team
    stage:       1
    workflows:
      - ProcessPayment
      - RefundPayment
    activities:
      - ChargeCard
      - SendReceipt
 
  - name:        queue-email-worker
    type:        queue
    language:    node
    queue_name:  email-jobs
    owner:       @notifications-team
    stage:       1
    jobs:
      - SendWelcomeEmail
      - SendPasswordReset
 
  - name:        cron-report-worker
    type:        cron
    language:    go
    owner:       @data-team
    stage:       1
    schedules:
      - DailyRevenueReport
 
  - name:        event-inventory-worker
    type:        event
    language:    java
    topics:
      - orders.created
      - orders.cancelled
    owner:       @inventory-team
    stage:       2

