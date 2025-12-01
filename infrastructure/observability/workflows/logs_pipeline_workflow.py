from __future__ import annotations

from pathlib import Path
from datetime import timedelta
from typing import Dict, Any

from temporalio import workflow
from infrastructure.observability.config.constants import OBSERVABILITY_CONFIG
from infrastructure.orchestrator.base.base_workflow import BaseWorkflow


@workflow.defn
class LogsPipelineWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, params: Dict[str, Any], config: Dict[str, Any]) -> str:
        workflow.logger.info({
            "pipeline": "logs",
            "event": "workflow_start",
            "params_keys": list(params.keys())
        })

        traefik_result = await workflow.execute_activity(
            "start_traefik_activity",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )

        if not traefik_result:
            workflow.logger.error({
                "pipeline": "logs",
                "event": "traefik_start_failed",
                "port": config["traefik"]["external_port"]
            })
            raise RuntimeError(f"Traefik failed to start on port {config['traefik']['external_port']}")

        workflow.logger.info({
            "pipeline": "logs",
            "event": "traefik_started",
            "url": config["traefik"]["external_url"]
        })

        await workflow.sleep(5)

        await workflow.execute_activity(
            "start_grafana_activity",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({
            "pipeline": "logs",
            "event": "grafana_started",
            "internal_url": config["grafana"]["internal_url"],
            "external_url": config["grafana"]["external_url"]
        })

        await workflow.execute_activity(
            "start_loki_activity",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({
            "pipeline": "logs",
            "event": "loki_started",
            "internal_url": config["loki"]["internal_url"],
            "push_url": config["loki_push_url"]
        })

        await workflow.execute_activity(
            "start_otel_collector_activity",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({
            "pipeline": "logs",
            "event": "otel_started",
            "container": config["otel_collector"]["container_name"]
        })

        await workflow.sleep(10)

        workflow_params = {
            **config.get("workflow_params", {}),
            **params
        }

        workflow.logger.info({
            "pipeline": "logs",
            "event": "endpoints_resolved",
            "loki_push_url": config["loki_push_url"],
            "loki_query_url": config["loki_query_url"],
            "grafana_url": config["grafana"]["external_url"]
        })

        gen_res = await workflow.execute_activity(
            "generate_config_logs",
            {
                "dynamic_dir": config["dynamic_config_dir"],
                "loki_push_url": config["loki_push_url"]
            },
            start_to_close_timeout=timedelta(seconds=120),
        )

        workflow.logger.info({
            "pipeline": "logs",
            "event": "config_generated",
            "success": gen_res.get("success") if isinstance(gen_res, dict) else False
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
            "pipeline": "logs",
            "event": "paths_configured",
            "success": cfg_paths_res.get("success") if isinstance(cfg_paths_res, dict) else False
        })

        cfg_apply_res = await workflow.execute_activity(
            "configure_source_logs",
            {
                "config_path": config_path,
                "dynamic_dir": config["dynamic_config_dir"]
            } if config_path else {},
            start_to_close_timeout=timedelta(seconds=60),
        )

        workflow.logger.info({
            "pipeline": "logs",
            "event": "source_configured",
            "success": cfg_apply_res.get("success") if isinstance(cfg_apply_res, dict) else False
        })

        deploy_res = await workflow.execute_activity(
            "deploy_processor_logs",
            {
                "dynamic_dir": config["dynamic_config_dir"],
                "config_name": Path(config_path).name if config_path else "otel-collector-generated.yaml",
            },
            start_to_close_timeout=timedelta(seconds=60),
        )

        workflow.logger.info({
            "pipeline": "logs",
            "event": "processor_deployed",
            "success": deploy_res.get("success") if isinstance(deploy_res, dict) else False
        })

        restart_res = await workflow.execute_activity(
            "restart_source_logs",
            {
                "container_name": config["otel_collector"]["container_name"],
                "timeout_seconds": 60
            },
            start_to_close_timeout=timedelta(seconds=120),
        )

        workflow.logger.info({
            "pipeline": "logs",
            "event": "source_restarted",
            "success": restart_res.get("success") if isinstance(restart_res, dict) else False
        })

        loki_push_url = params.get("loki_push_url", OBSERVABILITY_CONFIG.LOKI_PUSH_URL)
        loki_query_url = params.get("loki_query_url", OBSERVABILITY_CONFIG.LOKI_QUERY_URL)
        grafana_url = params.get("grafana_url", OBSERVABILITY_CONFIG.GRAFANA_URL)

        await workflow.execute_activity(
            "create_grafana_datasource_activity",
            {
                "grafana_url": grafana_url,
                "grafana_user": workflow_params.get("grafana_user", "admin"),
                "grafana_password": workflow_params.get("grafana_password", "SuperSecret123!"),
                "datasource_name": "loki",
                "loki_url": OBSERVABILITY_CONFIG.LOKI_URL,
                "upsert_mode": "upsert",
                "org_id": 1
            },
            start_to_close_timeout=timedelta(seconds=120),
        )

        workflow.logger.info({
            "pipeline": "logs",
            "event": "grafana_datasource_created",
            "datasource": "loki"
        })

        emit_res = await workflow.execute_activity(
            "emit_test_event_logs",
            {"config_path": config_path},
            start_to_close_timeout=timedelta(seconds=60),
        )

        workflow.logger.info({
            "pipeline": "logs",
            "event": "test_event_emitted",
            "success": emit_res.get("success") if isinstance(emit_res, dict) else False
        })

        token = None
        if isinstance(emit_res, dict):
            data = emit_res.get("data") or {}
            token = data.get("token")

        workflow.logger.info({
            "pipeline": "logs",
            "event": "token_extracted",
            "token": token
        })

        logql = f'{{filename=~".+"}} |= "{token}"' if token else '{filename=~".+"}'

        workflow.logger.info({
            "pipeline": "logs",
            "event": "verification_start",
            "logql": logql
        })

        verify_res = await workflow.execute_activity(
            "verify_event_ingestion_logs",
            {
                "loki_query_url": config["loki_query_url"],
                "logql": logql,
                "timeout_seconds": 60,
                "poll_interval": 2.0
            },
            start_to_close_timeout=timedelta(seconds=120),
        )

        workflow.logger.info({
            "pipeline": "logs",
            "event": "verification_complete",
            "success": verify_res.get("success") if isinstance(verify_res, dict) else False
        })
        
        # Cleanup at end of workflow
        workflow.logger.info({
            "pipeline": "logs",
            "event": "cleanup_start"
        })

        cleanup_activities = [
            "stop_loki_activity",
            "delete_loki_activity",
            "stop_otel_collector_activity",
            "delete_otel_collector_activity",
        ]
        
        for act in cleanup_activities:
            try:
                await workflow.execute_activity(
                    act, {}, start_to_close_timeout=timedelta(seconds=30)
                )
            except Exception:
                workflow.logger.info({
                    "pipeline": "logs",
                    "event": "cleanup_skip",
                    "activity": act
                })

        workflow.logger.info({
            "pipeline": "logs",
            "event": "cleanup_complete"
        })

        workflow.logger.info({
            "pipeline": "logs",
            "event": "workflow_complete"
        })

        return "logs_pipeline_completed"
