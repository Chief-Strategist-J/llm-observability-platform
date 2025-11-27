import sys
from pathlib import Path
from datetime import timedelta
from typing import Dict, Any

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from temporalio import workflow
from infrastructure.orchestrator.base.base_workflow import BaseWorkflow

@workflow.defn
class TracingPipelineWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, params: Dict[str, Any]) -> str:
        workflow.logger.info({
            "labels": {"pipeline": "tracing", "event": "start"},
            "msg": "workflow_start",
            "params": params
        })

        # STEP 1: Start Traefik FIRST (reverse proxy front-door)
        traefik_result = await workflow.execute_activity(
            "start_traefik_activity",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )
        
        if not traefik_result:
            workflow.logger.error({"labels": {"pipeline": "tracing", "event": "traefik"}, "msg": "traefik_failed_to_start"})
            raise RuntimeError("Traefik failed to start - check if port 8888 is available")
        
        workflow.logger.info({"labels": {"pipeline": "tracing", "event": "traefik"}, "msg": "traefik_started"})

        # Wait for Traefik to be fully ready
        await workflow.sleep(5)

        # STEP 2: Start Grafana (behind Traefik)
        await workflow.execute_activity(
            "start_grafana_activity",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({"labels": {"pipeline": "tracing", "event": "grafana"}, "msg": "grafana_started"})

        # STEP 3: Start Tempo (behind Traefik)
        await workflow.execute_activity(
            "start_tempo_activity",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({"labels": {"pipeline": "tracing", "event": "tempo"}, "msg": "tempo_started"})

        # STEP 4: Start OTel Collector (behind Traefik)
        await workflow.execute_activity(
            "start_opentelemetry_collector",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({"labels": {"pipeline": "tracing", "event": "otel"}, "msg": "otel_started"})

        # Wait for all services to be fully ready
        await workflow.sleep(10)

        dynamic_dir = params.get("dynamic_dir", "infrastructure/orchestrator/dynamicconfig")

        # Use localhost URLs (Traefik proxies these)
        tempo_query_url = params.get("tempo_query_url", "http://localhost:31003")
        grafana_url = params.get("grafana_url", "http://localhost:31001")
        otel_container_name = params.get("otel_container_name", "opentelemetry-collector")

        workflow.logger.info({
            "labels": {"pipeline": "tracing", "event": "endpoints"},
            "msg": "using_traefik_endpoints",
            "tempo_query_url": tempo_query_url,
            "grafana_url": grafana_url
        })

        # STEP 5: Generate OTel config with Tempo endpoint
        gen_res = await workflow.execute_activity(
            "generate_config_tracings",
            {
                "dynamic_dir": dynamic_dir, 
                "internal_tempo_url": "tempo-development:4317"
            },
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({
            "labels": {"pipeline": "tracing", "event": "generate_config"},
            "msg": "generate_config_result",
            "result": gen_res
        })

        config_path = None
        if isinstance(gen_res, dict):
            data = gen_res.get("data") or {}
            config_path = data.get("config_path")

        # STEP 6: Configure source paths
        cfg_paths_res = await workflow.execute_activity(
            "configure_source_paths_tracings",
            {"config_path": config_path} if config_path else {},
            start_to_close_timeout=timedelta(seconds=60),
        )
        workflow.logger.info({
            "labels": {"pipeline": "tracing", "event": "configure_paths"},
            "msg": "configure_paths_result",
            "result": cfg_paths_res
        })

        # STEP 7: Apply configuration
        cfg_apply_res = await workflow.execute_activity(
            "configure_source_tracings",
            {"config_path": config_path, "dynamic_dir": dynamic_dir} if config_path else {},
            start_to_close_timeout=timedelta(seconds=60),
        )
        workflow.logger.info({
            "labels": {"pipeline": "tracing", "event": "configure_source"},
            "msg": "configure_source_result",
            "result": cfg_apply_res
        })

        # STEP 8: Deploy processors
        deploy_res = await workflow.execute_activity(
            "deploy_processor_tracings",
            {
                "dynamic_dir": dynamic_dir,
                "config_name": Path(config_path).name if config_path else "otel-collector-tracings-generated.yaml",
            },
            start_to_close_timeout=timedelta(seconds=60),
        )
        workflow.logger.info({
            "labels": {"pipeline": "tracing", "event": "deploy_processor"},
            "msg": "deploy_processor_result",
            "result": deploy_res
        })

        # STEP 9: Restart OTel to pick up new config
        restart_res = await workflow.execute_activity(
            "restart_source_tracings",
            {"container_name": otel_container_name, "timeout_seconds": 60},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({
            "labels": {"pipeline": "tracing", "event": "restart_source"},
            "msg": "restart_source_result",
            "result": restart_res
        })

        # STEP 10: Create Grafana datasource pointing to Tempo
        # Grafana uses container-to-container communication, so we use the Tempo container name
        await workflow.execute_activity(
            "create_grafana_datasource_tracings_activity",
            {
                "grafana_url": grafana_url,  # Access Grafana through Traefik
                "grafana_user": params.get("grafana_user", "admin"),
                "grafana_password": params.get("grafana_password", "SuperSecret123!"),
                "datasource_name": params.get("datasource_name", "tempo"),
                "tempo_url": "http://tempo-development:3200",  # Container-to-container URL
                "upsert_mode": params.get("upsert_mode", "upsert"),
                "org_id": params.get("org_id", 1),
            },
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({"labels": {"pipeline": "tracing", "event": "grafana_datasource"}, "msg": "grafana_datasource_created"})

        # STEP 11: Emit test trace event
        emit_res = await workflow.execute_activity(
            "emit_test_event_tracings",
            {
                "otlp_endpoint": "http://localhost:4317",
                "service_name": "test-tracing-service",
                "span_name": "test-span"
            },
            start_to_close_timeout=timedelta(seconds=60),
        )
        workflow.logger.info({
            "labels": {"pipeline": "tracing", "event": "emit_test"},
            "msg": "emit_test_result",
            "result": emit_res
        })

        trace_id = None
        if isinstance(emit_res, dict):
            data = emit_res.get("data") or {}
            trace_id = data.get("token")

        workflow.logger.info({
            "labels": {"pipeline": "tracing", "event": "trace_id_extracted"},
            "msg": "synthetic_trace_id",
            "trace_id": trace_id
        })

        # STEP 12: Verify trace ingestion in Tempo
        verify_res = await workflow.execute_activity(
            "verify_event_ingestion_tracings",
            {
                "tempo_query_url": tempo_query_url, 
                "trace_id": trace_id if trace_id else "dummy-trace-id", 
                "timeout_seconds": 60, 
                "poll_interval": 2.0
            },
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({
            "labels": {"pipeline": "tracing", "event": "verify_complete"},
            "msg": "verification_result",
            "result": verify_res
        })

        workflow.logger.info({"labels": {"pipeline": "tracing", "event": "done"}, "msg": "workflow_complete"})

        return "tracing_pipeline_completed"
