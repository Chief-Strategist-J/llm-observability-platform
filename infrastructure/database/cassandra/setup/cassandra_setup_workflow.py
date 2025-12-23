from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

from infrastructure.database.shared.database_definitions import (
    get_host_entries,
    get_all_hostnames,
)


@workflow.defn(name="CassandraSetupWorkflow")
class CassandraSetupWorkflow:
    @workflow.run
    async def run(self, params: dict) -> dict:
        trace_id = params.get("trace_id", "cassandra-setup")
        service_name = "cassandra"
        
        hostnames = get_all_hostnames(service_name)
        host_entries = get_host_entries(service_name)
        
        await workflow.execute_activity(
            "generate_certificates_activity",
            {"hostnames": hostnames, "trace_id": trace_id},
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )

        await workflow.execute_activity(
            "add_hosts_entries_activity",
            {"entries": host_entries, "force_replace": True, "trace_id": trace_id},
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )

        result = await workflow.execute_activity(
            "setup_cassandra_activity",
            {"env_vars": params.get("env_vars", {}), "trace_id": trace_id},
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        return result


@workflow.defn(name="CassandraTeardownWorkflow")
class CassandraTeardownWorkflow:
    @workflow.run
    async def run(self, params: dict) -> dict:
        trace_id = params.get("trace_id", "cassandra-teardown")
        
        result = await workflow.execute_activity(
            "teardown_cassandra_activity",
            {"trace_id": trace_id},
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        return result
