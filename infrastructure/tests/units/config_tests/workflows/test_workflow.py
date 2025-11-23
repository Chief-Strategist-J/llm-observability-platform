from datetime import timedelta
from temporalio import workflow

@workflow.defn
class TestWorkflow:
    @workflow.run
    async def run(self, params: dict) -> dict:
        result_start = await workflow.execute_activity(
            "start_traefik_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        result_stop = await workflow.execute_activity(
            "stop_traefik_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        result_restart = await workflow.execute_activity(
            "restart_traefik_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        result_delete = await workflow.execute_activity(
            "delete_traefik_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        result_start = await workflow.execute_activity(
            "start_traefik_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        result_stop = await workflow.execute_activity(
            "stop_traefik_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        result_restart = await workflow.execute_activity(
            "restart_traefik_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        result_delete = await workflow.execute_activity(
            "delete_traefik_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        result_start = await workflow.execute_activity(
            "start_traefik_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        result_stop = await workflow.execute_activity(
            "stop_traefik_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        result_restart = await workflow.execute_activity(
            "restart_traefik_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        result_delete = await workflow.execute_activity(
            "delete_traefik_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        result_start = await workflow.execute_activity(
            "start_traefik_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        result_stop = await workflow.execute_activity(
            "stop_traefik_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        result_restart = await workflow.execute_activity(
            "restart_traefik_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        result_delete = await workflow.execute_activity(
            "delete_traefik_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        result_start = await workflow.execute_activity(
            "start_traefik_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        result_stop = await workflow.execute_activity(
            "stop_traefik_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        result_restart = await workflow.execute_activity(
            "restart_traefik_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=60),
        )
        result_delete = await workflow.execute_activity(
            "delete_traefik_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=60),
        )

        return {
            "start": result_start,
            "stop": result_stop,
            "restart": result_restart,
            "delete": result_delete,
        }
