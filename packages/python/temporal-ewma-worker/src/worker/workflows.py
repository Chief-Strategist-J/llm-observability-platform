import asyncio
from dataclasses import dataclass
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from shared.types.ewma_types import EwmaRecord, AnomalyPayload
from features.ewma_compute.service import EwmaService


@dataclass
class EwmaWorkflowInput:
    force_hour: int | None = None


@workflow.defn(name="EwmaBaselineUpdate")
class EwmaBaselineUpdate:
    @workflow.run
    async def run(self, workflow_input: EwmaWorkflowInput | None = None) -> None:
        if workflow_input and workflow_input.force_hour is not None:
            hour_of_week = workflow_input.force_hour
        else:
            current_time = workflow.now()
            hour_of_week = current_time.weekday() * 24 + current_time.hour

        active_pairs = await workflow.execute_activity(
            "fetch_active_pairs", start_to_close_timeout=timedelta(seconds=60)
        )

        tasks = [
            self._process_pair(service, model, hour_of_week)
            for service, model in active_pairs
        ]
        await asyncio.gather(*tasks)

    async def _process_pair(self, service: str, model: str, hour_of_week: int) -> None:
        existing_record = await workflow.execute_activity(
            "get_baseline",
            args=[service, model, hour_of_week],
            result_type=EwmaRecord,
            start_to_close_timeout=timedelta(seconds=10),
        )

        if existing_record is None:
            global_avg = await workflow.execute_activity(
                "fetch_global_model_avg",
                args=[model, hour_of_week],
                start_to_close_timeout=timedelta(seconds=30),
            )

            new_record = EwmaService.process_update(0.0, None, global_avg)
            new_record.service = service
            new_record.model = model
            new_record.hour_of_week = hour_of_week

            await workflow.execute_activity(
                "upsert_baseline",
                args=[new_record],
                start_to_close_timeout=timedelta(seconds=15),
            )
        else:
            current_cost = await workflow.execute_activity(
                "fetch_current_cost_1h",
                args=[service, model],
                start_to_close_timeout=timedelta(seconds=30),
            )

            is_anomaly = (
                not existing_record.is_cold_start
                and current_cost > 3.0 * existing_record.ewma_value
            )

            if is_anomaly:
                cluster_drilldown = await workflow.execute_activity(
                    "fetch_cost_by_cluster_1h",
                    args=[service, model],
                    start_to_close_timeout=timedelta(seconds=30),
                )

                alert_payload = AnomalyPayload(
                    service=service,
                    model=model,
                    hour_of_week=hour_of_week,
                    current_cost=current_cost,
                    ewma_value=existing_record.ewma_value,
                    threshold_value=3.0 * existing_record.ewma_value,
                    sample_count=existing_record.sample_count,
                    timestamp=workflow.now().isoformat(),
                    cluster_drilldown=cluster_drilldown,
                )

                await workflow.execute_activity(
                    "publish_anomaly_alert",
                    args=[alert_payload],
                    start_to_close_timeout=timedelta(seconds=20),
                )

            new_record = EwmaService.process_update(current_cost, existing_record, 0.0)

            await workflow.execute_activity(
                "upsert_baseline",
                args=[new_record],
                start_to_close_timeout=timedelta(seconds=15),
            )


DEFAULT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=10),
    maximum_attempts=3,
)


@dataclass
class IntegrityCheckInput:
    pass


@workflow.defn(name="WeeklyIntegrityCheck")
class WeeklyIntegrityCheck:
    @workflow.run
    async def run(self, workflow_input: IntegrityCheckInput | None = None) -> dict:
        dimensions = ["service", "model", "user"]
        all_results = {}

        for dim in dimensions:
            keys = await workflow.execute_activity(
                "fetch_active_keys",
                args=[dim],
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=DEFAULT_RETRY_POLICY,
            )

            tasks = [
                workflow.execute_activity(
                    "verify_key_integrity",
                    args=[dim, key],
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=DEFAULT_RETRY_POLICY,
                )
                for key in keys
            ]

            results = await asyncio.gather(*tasks)
            all_results[dim] = results

        return all_results


@dataclass
class RetroactiveCorrectionInput:
    hours: int = 24


@workflow.defn(name="RetroactivePriceCorrection")
class RetroactivePriceCorrection:
    @workflow.run
    async def run(
        self, workflow_input: RetroactiveCorrectionInput | None = None
    ) -> int:
        hours = workflow_input.hours if workflow_input else 24

        spans = await workflow.execute_activity(
            "fetch_spans_for_correction",
            args=[hours],
            start_to_close_timeout=timedelta(seconds=120),
            retry_policy=DEFAULT_RETRY_POLICY,
        )

        if not spans:
            return 0

        correction_count = await workflow.execute_activity(
            "apply_price_corrections",
            args=[spans],
            start_to_close_timeout=timedelta(seconds=180),
            retry_policy=DEFAULT_RETRY_POLICY,
        )

        return correction_count


