from datetime import timedelta
from pathlib import Path
from temporalio import workflow
from temporalio.common import RetryPolicy

from infrastructure.database.shared.database_definitions import (
    get_host_entries,
    get_all_hostnames,
)


@workflow.defn(name="MongodbSetupWorkflow")
class MongodbSetupWorkflow:
    @workflow.run
    async def run(self, params: dict) -> dict:
        trace_id = params.get("trace_id", "mongodb-setup")
        service_name = "mongodb"
        
        hostnames = get_all_hostnames(service_name)
        host_entries = get_host_entries(service_name)
        
        project_root = Path("/home/j/live/dinesh/llm-chatbot-python")
        traefik_dir = project_root / "infrastructure/orchestrator/config/docker/traefik"
        certs_dir = traefik_dir / "certs"
        tls_config_dir = traefik_dir / "config/tls"
        
        await workflow.execute_activity(
            "generate_certificates_activity",
            {
                "hostnames": hostnames, 
                "trace_id": trace_id,
                "certs_dir": str(certs_dir)
            },
            start_to_close_timeout=timedelta(minutes=3),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=2),
                maximum_interval=timedelta(seconds=20),
                maximum_attempts=3,
                backoff_coefficient=2.0
            )
        )

        await workflow.execute_activity(
            "generate_traefik_tls_config_activity",
            {
                "hostnames": hostnames,
                "certs_dir": "/certs",
                "output_file": str(tls_config_dir / "mongodb_tls.yaml"),
                "trace_id": trace_id
            },
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=2),
                maximum_interval=timedelta(seconds=20),
                maximum_attempts=3,
                backoff_coefficient=2.0
            )
        )

        await workflow.execute_activity(
            "add_hosts_entries_activity",
            {"entries": host_entries, "force_replace": True, "trace_id": trace_id},
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=2),
                maximum_interval=timedelta(seconds=20),
                maximum_attempts=3,
                backoff_coefficient=2.0
            )
        )

        result = await workflow.execute_activity(
            "setup_mongodb_activity",
            {"env_vars": params.get("env_vars", {}), "trace_id": trace_id},
            start_to_close_timeout=timedelta(minutes=15),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=5),
                maximum_interval=timedelta(seconds=60),
                maximum_attempts=3,
                backoff_coefficient=2.0
            )
        )
        
        return result


@workflow.defn(name="MongodbTeardownWorkflow")
class MongodbTeardownWorkflow:
    @workflow.run
    async def run(self, params: dict) -> dict:
        trace_id = params.get("trace_id", "mongodb-teardown")
        
        result = await workflow.execute_activity(
            "teardown_mongodb_activity",
            {"trace_id": trace_id},
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=5),
                maximum_interval=timedelta(seconds=60),
                maximum_attempts=3,
                backoff_coefficient=2.0
            )
        )
        
        return result