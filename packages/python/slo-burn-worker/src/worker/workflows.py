import asyncio
from datetime import timedelta
from temporalio import workflow

@workflow.defn(name="SloBurnWorkflow")
class SloBurnWorkflow:
    @workflow.run
    async def run(self) -> None:
        # Fetch current time from the deterministic workflow context
        current_time = workflow.now()
        unix_ts = int(current_time.timestamp())

        # 1. Fetch active (model, endpoint) pairs from Redis keys
        active_pairs = await workflow.execute_activity(
            "fetch_active_pairs",
            start_to_close_timeout=timedelta(seconds=60),
        )

        # 2. For each pair, run computations and handle alerting
        tasks = [
            self._process_pair(model, endpoint, unix_ts)
            for model, endpoint in active_pairs
        ]
        if tasks:
            await asyncio.gather(*tasks)

    async def _process_pair(self, model: str, endpoint: str, unix_ts: int) -> None:
        # 2a. Compute burn rates
        burn_rates = await workflow.execute_activity(
            "compute_burn_rates",
            args=[model, endpoint, unix_ts],
            start_to_close_timeout=timedelta(seconds=60),
        )

        # 2b. Write burn rates to Redis
        await workflow.execute_activity(
            "write_burn_rates",
            args=[model, endpoint, burn_rates],
            start_to_close_timeout=timedelta(seconds=30),
        )

        # 2c. Evaluate alert criteria, enrich, rate limit, and publish alerts
        await workflow.execute_activity(
            "handle_alerts",
            args=[model, endpoint, burn_rates, unix_ts],
            start_to_close_timeout=timedelta(seconds=60),
        )
