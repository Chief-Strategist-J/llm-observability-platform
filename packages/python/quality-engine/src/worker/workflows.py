from datetime import timedelta
import asyncio
from temporalio import workflow
from features.quality_baseline.types import BaselineRecomputeResult
from worker.activities import AggregateCompositeInput

@workflow.defn(name="RecomputeQualityBaseline")
class RecomputeQualityBaseline:
    @workflow.run
    async def run(self) -> int:
        baselines = await workflow.execute_activity(
            "recompute_baseline_scores",
            start_to_close_timeout=timedelta(seconds=60),
        )
        count = await workflow.execute_activity(
            "write_redis_baselines",
            args=[baselines],
            start_to_close_timeout=timedelta(seconds=30),
        )
        return count

@workflow.defn(name="RollupQualityTrend")
class RollupQualityTrend:
    @workflow.run
    async def run(self) -> int:
        count = await workflow.execute_activity(
            "rollup_quality_trend",
            start_to_close_timeout=timedelta(seconds=120),
        )
        return count

@workflow.defn(name="quality_score_workflow")
class QualityScoreWorkflow:
    @workflow.run
    async def run(self, payload: dict) -> dict:
        # Step 1: Detect response language
        response_language = await workflow.execute_activity(
            "detect_language",
            args=[payload.get("response_text")],
            start_to_close_timeout=timedelta(seconds=5),
        )

        # Step 2: Detect prompt type
        prompt_type = await workflow.execute_activity(
            "detect_prompt_type",
            args=[payload.get("prompt_text"), payload.get("response_text"), payload.get("rag_context")],
            start_to_close_timeout=timedelta(seconds=5),
        )

        # Step 3, 4, 5, 6: Compute coherence, toxicity, faithfulness, perplexity in parallel
        coherence, toxicity, faithfulness, perplexity = await asyncio.gather(
            workflow.execute_activity(
                "compute_coherence",
                args=[payload, prompt_type],
                start_to_close_timeout=timedelta(seconds=10),
            ),
            workflow.execute_activity(
                "compute_toxicity",
                args=[payload],
                start_to_close_timeout=timedelta(seconds=10),
            ),
            workflow.execute_activity(
                "compute_faithfulness",
                args=[payload],
                start_to_close_timeout=timedelta(seconds=10),
            ),
            workflow.execute_activity(
                "compute_perplexity",
                args=[payload, prompt_type],
                start_to_close_timeout=timedelta(seconds=10),
            ),
        )

        # Step 7: Aggregate composite, check invariants, publish to Kafka
        inp = AggregateCompositeInput(
            payload=payload,
            coherence=coherence,
            toxicity=toxicity,
            faithfulness=faithfulness,
            perplexity=perplexity,
            prompt_type=prompt_type,
            response_language=response_language,
        )
        result = await workflow.execute_activity(
            "aggregate_composite",
            args=[inp],
            start_to_close_timeout=timedelta(seconds=10),
        )
        return result
