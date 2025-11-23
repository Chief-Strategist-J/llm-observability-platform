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
class LogsPipelineWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, params: Dict[str, Any]) -> str:
        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "start"},
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
            workflow.logger.error({"labels": {"pipeline": "logs", "event": "traefik"}, "msg": "traefik_failed_to_start"})
            raise RuntimeError("Traefik failed to start - check if port 8888 is available")
        
        workflow.logger.info({"labels": {"pipeline": "logs", "event": "traefik"}, "msg": "traefik_started"})

        # Wait for Traefik to be fully ready
        await workflow.sleep(5)

        # STEP 2: Start Grafana (behind Traefik)
        await workflow.execute_activity(
            "start_grafana_activity",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({"labels": {"pipeline": "logs", "event": "grafana"}, "msg": "grafana_started"})

        # STEP 3: Start Loki (behind Traefik)
        await workflow.execute_activity(
            "start_loki_activity",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({"labels": {"pipeline": "logs", "event": "loki"}, "msg": "loki_started"})

        # STEP 4: Start OTel Collector (behind Traefik)
        await workflow.execute_activity(
            "start_opentelemetry_collector",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({"labels": {"pipeline": "logs", "event": "otel"}, "msg": "otel_started"})

        # Wait for all services to be fully ready
        await workflow.sleep(10)

        dynamic_dir = params.get("dynamic_dir", "infrastructure/orchestrator/dynamicconfig")

        # Use localhost URLs (Traefik proxies these)
        # These URLs work BOTH locally and in cloud (just change localhost to your domain)
        loki_push_url = params.get("loki_push_url", "http://localhost:31002/loki/api/v1/push")
        loki_query_url = params.get("loki_query_url", "http://localhost:31002/loki/api/v1/query")
        grafana_url = params.get("grafana_url", "http://localhost:31001")
        otel_container_name = params.get("otel_container_name", "opentelemetry-collector-development")

        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "endpoints"},
            "msg": "using_traefik_endpoints",
            "loki_push_url": loki_push_url,
            "loki_query_url": loki_query_url,
            "grafana_url": grafana_url
        })

        # STEP 5: Generate OTel config with Loki endpoint
        gen_res = await workflow.execute_activity(
            "generate_config_logs",
            {"dynamic_dir": dynamic_dir, "loki_push_url": loki_push_url},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "generate_config"},
            "msg": "generate_config_result",
            "result": gen_res
        })

        config_path = None
        if isinstance(gen_res, dict):
            data = gen_res.get("data") or {}
            config_path = data.get("config_path")

        # STEP 6: Configure source paths
        cfg_paths_res = await workflow.execute_activity(
            "configure_source_paths_logs",
            {"config_path": config_path} if config_path else {},
            start_to_close_timeout=timedelta(seconds=60),
        )
        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "configure_paths"},
            "msg": "configure_paths_result",
            "result": cfg_paths_res
        })

        # STEP 7: Apply configuration
        cfg_apply_res = await workflow.execute_activity(
            "configure_source_logs",
            {"config_path": config_path, "dynamic_dir": dynamic_dir} if config_path else {},
            start_to_close_timeout=timedelta(seconds=60),
        )
        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "configure_source"},
            "msg": "configure_source_result",
            "result": cfg_apply_res
        })

        # STEP 8: Deploy processors
        deploy_res = await workflow.execute_activity(
            "deploy_processor_logs",
            {
                "dynamic_dir": dynamic_dir,
                "config_name": Path(config_path).name if config_path else "otel-collector-generated.yaml",
            },
            start_to_close_timeout=timedelta(seconds=60),
        )
        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "deploy_processor"},
            "msg": "deploy_processor_result",
            "result": deploy_res
        })

        # STEP 9: Restart OTel to pick up new config
        restart_res = await workflow.execute_activity(
            "restart_source_logs",
            {"container_name": otel_container_name, "timeout_seconds": 60},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "restart_source"},
            "msg": "restart_source_result",
            "result": restart_res
        })

        # STEP 10: Create Grafana datasource pointing to Loki
        # Grafana uses container-to-container communication, so we use the Loki container name
        await workflow.execute_activity(
            "create_grafana_datasource_activity",
            {
                "grafana_url": grafana_url,  # Access Grafana through Traefik
                "grafana_user": params.get("grafana_user", "admin"),
                "grafana_password": params.get("grafana_password", "SuperSecret123!"),
                "datasource_name": params.get("datasource_name", "loki"),
                "loki_url": "http://loki-development:3100",  # Container-to-container URL
                "upsert_mode": params.get("upsert_mode", "upsert"),
                "org_id": params.get("org_id", 1),
            },
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({"labels": {"pipeline": "logs", "event": "grafana_datasource"}, "msg": "grafana_datasource_created"})

        # STEP 11: Emit test log event
        emit_res = await workflow.execute_activity(
            "emit_test_event_logs",
            {"config_path": config_path},
            start_to_close_timeout=timedelta(seconds=60),
        )
        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "emit_test"},
            "msg": "emit_test_result",
            "result": emit_res
        })

        token = None
        if isinstance(emit_res, dict):
            data = emit_res.get("data") or {}
            token = data.get("token")

        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "token_extracted"},
            "msg": "synthetic_token",
            "token": token
        })

        logql = f'{{filename=~".+"}} |= "{token}"' if token else '{filename=~".+"}'

        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "verify_start"},
            "msg": "starting_verification",
            "logql": logql
        })

        # STEP 12: Verify log ingestion in Loki
        verify_res = await workflow.execute_activity(
            "verify_event_ingestion_logs",
            {"loki_query_url": loki_query_url, "logql": logql, "timeout_seconds": 60, "poll_interval": 2.0},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "verify_complete"},
            "msg": "verification_result",
            "result": verify_res
        })

        workflow.logger.info({"labels": {"pipeline": "logs", "event": "done"}, "msg": "workflow_complete"})

        return "logs_pipeline_completed"