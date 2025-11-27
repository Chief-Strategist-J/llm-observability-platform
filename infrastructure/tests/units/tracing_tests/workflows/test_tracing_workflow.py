from datetime import timedelta
from temporalio import workflow

@workflow.defn
class TestTracingWorkflow:
    @workflow.run
    async def run(self, params: dict) -> dict:
        # Test Tempo container lifecycle
        result_start = await workflow.execute_activity(
            "start_tempo_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        result_stop = await workflow.execute_activity(
            "stop_tempo_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        result_restart = await workflow.execute_activity(
            "restart_tempo_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        result_delete = await workflow.execute_activity(
            "delete_tempo_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=60),
        )

        # Test tracing configuration activities
        result_generate = await workflow.execute_activity(
            "generate_config_tracings",
            {"dynamic_dir": "/tmp/test", "internal_tempo_url": "tempo:4317"},
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        
        result_configure_paths = await workflow.execute_activity(
            "configure_source_paths_tracings",
            {"config_path": "/tmp/test-config.yaml"},
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        
        result_configure_source = await workflow.execute_activity(
            "configure_source_tracings",
            {"config_path": "/tmp/test-config.yaml", "dynamic_dir": "/tmp/test"},
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        
        result_deploy = await workflow.execute_activity(
            "deploy_processor_tracings",
            {"dynamic_dir": "/tmp/test", "config_name": "test.yaml"},
            schedule_to_close_timeout=timedelta(seconds=60),
        )

        # Test trace emission and verification
        result_emit = await workflow.execute_activity(
            "emit_test_event_tracings",
            {
                "otlp_endpoint": "http://localhost:4317",
                "service_name": "test-service",
                "span_name": "test-span"
            },
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        
        result_verify = await workflow.execute_activity(
            "verify_event_ingestion_tracings",
            {
                "tempo_query_url": "http://localhost:3200",
                "trace_id": "test-trace-123",
                "timeout_seconds": 30,
                "poll_interval": 1.0
            },
            schedule_to_close_timeout=timedelta(seconds=60),
        )

        # Test Grafana datasource creation
        result_grafana_ds = await workflow.execute_activity(
            "create_grafana_datasource_tracings_activity",
            {
                "grafana_url": "http://localhost:3000",
                "grafana_user": "admin",
                "grafana_password": "admin",
                "datasource_name": "tempo",
                "tempo_url": "http://tempo:3200"
            },
            schedule_to_close_timeout=timedelta(seconds=60),
        )

        return {
            "tempo_start": result_start,
            "tempo_stop": result_stop,
            "tempo_restart": result_restart,
            "tempo_delete": result_delete,
            "config_generate": result_generate,
            "config_paths": result_configure_paths,
            "config_source": result_configure_source,
            "deploy": result_deploy,
            "emit": result_emit,
            "verify": result_verify,
            "grafana_datasource": result_grafana_ds,
        }
