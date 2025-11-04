from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

@workflow.defn
class LogsPipelineWorkflow:
    @workflow.run
    async def run(self, service_name: str) -> str:
        rp = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
        )
        t = timedelta(minutes=5)

        await workflow.execute_activity(
            "start_loki_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "stop_loki_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "restart_loki_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "stop_loki_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "delete_loki_activity",
            args=[service_name, False],
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "start_promtail_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "restart_promtail_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "stop_promtail_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "delete_promtail_activity",
            args=[service_name, False],
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "start_prometheus_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "restart_prometheus_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "stop_prometheus_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "delete_prometheus_activity",
            args=[service_name, False],
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "start_grafana_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "restart_grafana_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "stop_grafana_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "delete_grafana_activity",
            args=[service_name, False],
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "start_jaeger_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "restart_jaeger_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "stop_jaeger_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "delete_jaeger_activity",
            args=[service_name, False],
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "start_opentelemetry_collector",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "restart_opentelemetry_collector",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "stop_opentelemetry_collector",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "delete_opentelemetry_collector",
            args=[service_name, False],
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "start_neo4j_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "restart_neo4j_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "stop_neo4j_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "delete_neo4j_activity",
            args=[service_name, False],
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "start_qdrant_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "restart_qdrant_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "stop_qdrant_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "delete_qdrant_activity",
            args=[service_name, False],
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "start_redis_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "restart_redis_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "stop_redis_activity",
            arg=service_name,
            start_to_close_timeout=t,
            retry_policy=rp,
        )
        await workflow.execute_activity(
            "delete_redis_activity",
            args=[service_name, False],
            start_to_close_timeout=t,
            retry_policy=rp,
        )


        return "Logs pipeline fully configured"
