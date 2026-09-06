import asyncio
from dataclasses import dataclass
from datetime import timedelta
from temporalio import workflow

@dataclass
class ForecastWorkflowInput:
    lookback_hours: int = 168
    min_history_hours: int = 48

@workflow.defn(name="ForecastWorkflow")
class ForecastWorkflow:
    @workflow.run
    async def run(self, workflow_input: ForecastWorkflowInput | None = None) -> None:
        lookback_hours = workflow_input.lookback_hours if workflow_input else 168
        min_history_hours = workflow_input.min_history_hours if workflow_input else 48

        # 1. Fetch cost series
        cost_data = await workflow.execute_activity(
            "fetch_cost_series",
            args=[lookback_hours, min_history_hours],
            start_to_close_timeout=timedelta(seconds=60),
        )

        # 2. Fetch latency series
        latency_data = await workflow.execute_activity(
            "fetch_latency_series",
            args=[lookback_hours, min_history_hours],
            start_to_close_timeout=timedelta(seconds=60),
        )

        forecast_time_iso = workflow.now().isoformat()

        # 3. Process cost series
        tasks = []
        for key_str, series in cost_data.get("dense", {}).items():
            service, model = key_str.split("||")
            tasks.append(self._process_cost_pair(service, model, series, forecast_time_iso))
        
        if tasks:
            await asyncio.gather(*tasks)

        # 4. Process latency series
        latency_tasks = []
        for key_str, series in latency_data.get("dense", {}).items():
            service, model = key_str.split("||")
            latency_tasks.append(self._process_latency_pair(service, model, series))
            
        if latency_tasks:
            await asyncio.gather(*latency_tasks)

    async def _process_cost_pair(self, service: str, model: str, series: list[float], forecast_time_iso: str) -> None:
        forecast_res = await workflow.execute_activity(
            "run_timesfm_forecast",
            args=[series, 24],
            start_to_close_timeout=timedelta(seconds=120),
        )
        
        # We can use the last forecasted point (representing the end of the 24h horizon)
        mean_val = forecast_res["mean"][-1]
        p10_val = forecast_res["p10"][-1]
        p90_val = forecast_res["p90"][-1]
        
        await workflow.execute_activity(
            "write_forecast_outputs",
            args=[service, model, forecast_time_iso, mean_val, p10_val, p90_val],
            start_to_close_timeout=timedelta(seconds=30),
        )
        
        await workflow.execute_activity(
            "check_predicted_breach",
            args=[service, model, p90_val],
            start_to_close_timeout=timedelta(seconds=30),
        )

    async def _process_latency_pair(self, service: str, model: str, series: list[float]) -> None:
        # Just run the forecast for latency
        await workflow.execute_activity(
            "run_timesfm_forecast",
            args=[series, 24],
            start_to_close_timeout=timedelta(seconds=120),
        )
