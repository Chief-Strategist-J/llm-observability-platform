from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

@workflow.defn(name="MongodbSetupWorkflow")
class MongodbSetupWorkflow:
    @workflow.run
    async def run(self, params: dict) -> dict:
        trace_id = params.get("trace_id", "mongodb-setup")
        
        # 1. VIP [SKIPPED]

        # 2. Certs
        await workflow.execute_activity(
            "generate_certificates_activity",
            {
                "hostnames": ["scaibu.mongoexpress"], 
                "trace_id": trace_id
            },
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )

        # 3. Hosts
        await workflow.execute_activity(
            "add_hosts_entries_activity",
            {
                "entries": [
                    {"hostname": "scaibu.mongoexpress", "ip": "127.0.0.1"},
                    {"hostname": "scaibu.mongodb", "ip": "127.0.0.1"}
                ],
                "force_replace": True,
                "trace_id": trace_id
            },
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )

        # 4. Docker
        result = await workflow.execute_activity(
            "setup_mongodb_activity",
            {
                "env_vars": params.get("env_vars", {}),
                "trace_id": trace_id
            },
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        return result
