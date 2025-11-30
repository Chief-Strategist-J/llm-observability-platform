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
            "params_keys": list(params.keys())
        })

        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "cleanup"},
            "msg": "cleanup_existing_containers_start"
        })

        cleanup_activities = [
            "stop_loki_activity",
            "delete_loki_activity",
            "stop_opentelemetry_collector",
            "delete_opentelemetry_collector",
        ]

        for act in cleanup_activities:
            try:
                await workflow.execute_activity(
                    act, {}, start_to_close_timeout=timedelta(seconds=30)
                )
            except Exception:
                workflow.logger.info({
                    "labels": {"pipeline": "logs", "event": "cleanup"},
                    "msg": "activity_cleanup_skipped",
                    "activity": act
                })

        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "cleanup"},
            "msg": "cleanup_complete"
        })

        traefik_result = await workflow.execute_activity(
            "start_traefik_activity",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )

        if not traefik_result:
            workflow.logger.error({
                "labels": {"pipeline": "logs", "event": "traefik"},
                "msg": "traefik_start_failed",
                "error": "port_8888_maybe_taken"
            })
            raise RuntimeError("Traefik failed to start - check if port 8888 is available")

        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "traefik"},
            "msg": "traefik_started"
        })

        await workflow.sleep(5)

        await workflow.execute_activity(
            "start_grafana_activity",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({"labels": {"pipeline": "logs", "event": "grafana"}, "msg": "grafana_started"})

        await workflow.execute_activity(
            "start_loki_activity",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({"labels": {"pipeline": "logs", "event": "loki"}, "msg": "loki_started"})

        await workflow.execute_activity(
            "start_opentelemetry_collector",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({"labels": {"pipeline": "logs", "event": "otel"}, "msg": "otel_started"})

        await workflow.sleep(10)

        dynamic_dir = params.get("dynamic_dir", "infrastructure/orchestrator/dynamicconfig")

        loki_push_url = params.get("loki_push_url", "http://loki-instance-0:3100/loki/api/v1/push")
        loki_query_url = params.get("loki_query_url", "http://loki-instance-0:3100/loki/api/v1/query")
        grafana_url = params.get("grafana_url", "http://localhost:31001")
        otel_container_name = params.get("otel_container_name", "opentelemetry-collector")

        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "endpoints"},
            "msg": "resolved_endpoints",
            "loki_push_url": loki_push_url,
            "loki_query_url": loki_query_url,
            "grafana_url": grafana_url
        })

        gen_res = await workflow.execute_activity(
            "generate_config_logs",
            {"dynamic_dir": dynamic_dir, "loki_push_url": loki_push_url},
            start_to_close_timeout=timedelta(seconds=120),
        )

        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "generate_config"},
            "msg": "generate_config_completed",
            "result": gen_res
        })

        config_path = None
        if isinstance(gen_res, dict):
            data = gen_res.get("data") or {}
            config_path = data.get("config_path")

        cfg_paths_res = await workflow.execute_activity(
            "configure_source_paths_logs",
            {"config_path": config_path} if config_path else {},
            start_to_close_timeout=timedelta(seconds=60),
        )

        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "configure_paths"},
            "msg": "configure_paths_completed",
            "result": cfg_paths_res
        })

        cfg_apply_res = await workflow.execute_activity(
            "configure_source_logs",
            {"config_path": config_path, "dynamic_dir": dynamic_dir} if config_path else {},
            start_to_close_timeout=timedelta(seconds=60),
        )

        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "configure_source"},
            "msg": "configure_source_completed",
            "result": cfg_apply_res
        })

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
            "msg": "deploy_processor_completed",
            "result": deploy_res
        })

        restart_res = await workflow.execute_activity(
            "restart_source_logs",
            {"container_name": otel_container_name, "timeout_seconds": 60},
            start_to_close_timeout=timedelta(seconds=120),
        )

        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "restart_source"},
            "msg": "restart_source_completed",
            "result": restart_res
        })

        await workflow.execute_activity(
            "create_grafana_datasource_activity",
            {
                "grafana_url": grafana_url,
                "grafana_user": params.get("grafana_user", "admin"),
                "grafana_password": params.get("grafana_password", "SuperSecret123!"),
                "datasource_name": params.get("datasource_name", "loki"),
                "loki_url": "http://loki-instance-0:3100",
                "upsert_mode": params.get("upsert_mode", "upsert"),
                "org_id": params.get("org_id", 1)
            },
            start_to_close_timeout=timedelta(seconds=120),
        )

        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "grafana_datasource"},
            "msg": "grafana_datasource_created"
        })

        emit_res = await workflow.execute_activity(
            "emit_test_event_logs",
            {"config_path": config_path},
            start_to_close_timeout=timedelta(seconds=60),
        )

        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "emit_test"},
            "msg": "emit_test_completed",
            "result": emit_res
        })

        token = None
        if isinstance(emit_res, dict):
            data = emit_res.get("data") or {}
            token = data.get("token")

        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "token_extracted"},
            "msg": "token_acquired",
            "token": token
        })

        logql = f'{{filename=~".+"}} |= "{token}"' if token else '{filename=~".+"}'

        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "verify_start"},
            "msg": "verification_query_prepared",
            "logql": logql
        })

        verify_res = await workflow.execute_activity(
            "verify_event_ingestion_logs",
            {
                "loki_query_url": loki_query_url,
                "logql": logql,
                "timeout_seconds": 60,
                "poll_interval": 2.0
            },
            start_to_close_timeout=timedelta(seconds=120),
        )

        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "verify_complete"},
            "msg": "verification_completed",
            "result": verify_res
        })

        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "done"},
            "msg": "workflow_complete"
        })

        return "logs_pipeline_completed"
