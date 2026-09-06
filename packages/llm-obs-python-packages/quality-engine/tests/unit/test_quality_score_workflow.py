import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
from temporalio import activity
from temporalio.worker import Worker
from temporalio.testing import WorkflowEnvironment

from worker.activities import QualityBaselineActivities, AggregateCompositeInput
from worker.workflows import QualityScoreWorkflow
from shared.ports.clickhouse_port import ClickHousePort
from shared.ports.redis_port import RedisPort
from shared.ports.postgres_port import PostgresPort
from shared.ports.metrics_port import MetricsPort
from shared.ports.scorer_client_port import ScorerClientPort
from shared.ports.kafka_producer_port import KafkaProducerPort

@pytest.fixture
def mock_ports():
    return {
        "clickhouse": MagicMock(spec=ClickHousePort),
        "redis": MagicMock(spec=RedisPort),
        "postgres": MagicMock(spec=PostgresPort),
        "metrics": MagicMock(spec=MetricsPort),
        "scorer_client": MagicMock(spec=ScorerClientPort),
        "kafka_producer": MagicMock(spec=KafkaProducerPort),
    }

@pytest.fixture
def activities(mock_ports):
    return QualityBaselineActivities(
        clickhouse=mock_ports["clickhouse"],
        redis=mock_ports["redis"],
        postgres=mock_ports["postgres"],
        metrics=mock_ports["metrics"],
        scorer_client=mock_ports["scorer_client"],
        kafka_producer=mock_ports["kafka_producer"],
    )

@pytest.mark.asyncio
async def test_detect_language(activities) -> None:
    lang = await activities.detect_language("This is a longer English sentence to ensure language detection works correctly.")
    assert lang == "en"
    lang_empty = await activities.detect_language("")
    assert lang_empty == "en"

@pytest.mark.asyncio
async def test_detect_prompt_type(activities) -> None:
    p_rag = await activities.detect_prompt_type("hello", "world", "some context that indicates RAG")
    assert p_rag == "rag"
    
    p_code = await activities.detect_prompt_type("```python\nprint(1)\n```", "output", None)
    assert p_code == "code"

    p_class = await activities.detect_prompt_type("hello", "stop", None)
    assert p_class == "classification"

    p_chat = await activities.detect_prompt_type("hello", "this is a normal chat output containing words", None)
    assert p_chat == "chat"

@pytest.mark.asyncio
async def test_compute_coherence(activities, mock_ports) -> None:
    payload = {"trace_id": "t1", "span_id": "s1", "coherence_score": 0.8}
    coh = await activities.compute_coherence(payload, "chat")
    assert coh == 0.8
    mock_ports["scorer_client"].get_coherence_score.assert_not_called()

    payload_none = {"trace_id": "t1", "span_id": "s2", "coherence_score": None}
    mock_ports["scorer_client"].get_coherence_score.return_value = 0.9
    coh = await activities.compute_coherence(payload_none, "chat")
    assert coh == 0.9
    mock_ports["scorer_client"].get_coherence_score.assert_called_once()

@pytest.mark.asyncio
async def test_compute_toxicity(activities, mock_ports) -> None:
    payload = {"trace_id": "t1", "span_id": "s1", "toxicity_score": 0.1}
    tox = await activities.compute_toxicity(payload)
    assert tox == 0.1

    payload_none = {"trace_id": "t1", "span_id": "s2", "toxicity_score": None, "response_text": "hello"}
    mock_ports["scorer_client"].get_toxicity_score.return_value = 0.2
    tox = await activities.compute_toxicity(payload_none)
    assert tox == 0.2
    mock_ports["scorer_client"].get_toxicity_score.assert_called_once()

@pytest.mark.asyncio
async def test_compute_faithfulness(activities, mock_ports) -> None:
    payload = {"trace_id": "t1", "span_id": "s1", "faithfulness_score": 0.7}
    faith = await activities.compute_faithfulness(payload)
    assert faith == 0.7

    payload_none = {"trace_id": "t1", "span_id": "s2", "faithfulness_score": None}
    mock_ports["scorer_client"].get_faithfulness_score.return_value = 0.5
    faith = await activities.compute_faithfulness(payload_none)
    assert faith == 0.5

@pytest.mark.asyncio
async def test_compute_perplexity(activities, mock_ports) -> None:
    payload = {"trace_id": "t1", "span_id": "s1", "perplexity_score": 1.5}
    perp = await activities.compute_perplexity(payload, "chat")
    assert perp == 1.5

    payload_none = {"trace_id": "t1", "span_id": "s2", "perplexity_score": None}
    mock_ports["scorer_client"].get_perplexity_value.return_value = 3.0
    perp = await activities.compute_perplexity(payload_none, "chat")
    assert perp == 3.0

@pytest.mark.asyncio
async def test_aggregate_composite_and_invariants(activities, mock_ports) -> None:
    payload = {
        "span_id": "s1",
        "trace_id": "t1",
        "model": "m1",
        "endpoint": "e1",
        "quality_flags": [],
        "scored_at": datetime.now(timezone.utc).isoformat(),
    }
    # Test valid aggregation without perplexity
    inp = AggregateCompositeInput(
        payload=payload, coherence=0.8, toxicity=0.2, faithfulness=0.9, perplexity=None,
        prompt_type="chat", response_language="en"
    )
    res = await activities.aggregate_composite(inp)
    assert res["scores"]["coherence"] == 0.8
    # Test invalid composite score: INV-Q-02 coherence out of bounds
    inp_inv = AggregateCompositeInput(
        payload=payload, coherence=1.5, toxicity=0.2, faithfulness=0.9, perplexity=None,
        prompt_type="chat", response_language="en"
    )
    await activities.aggregate_composite(inp_inv)
    mock_ports["metrics"].record_invariant_violation.assert_called_with("INV-Q-02")

@pytest.mark.asyncio
async def test_quality_score_workflow_e2e(mock_ports) -> None:
    # Set up mock activities
    @activity.defn(name="detect_language")
    async def mock_lang(response_text) -> str:
        return "en"

    @activity.defn(name="detect_prompt_type")
    async def mock_pt(prompt_text, response_text, rag_context) -> str:
        return "chat"

    @activity.defn(name="compute_coherence")
    async def mock_coh(payload, prompt_type) -> float:
        return 0.8

    @activity.defn(name="compute_toxicity")
    async def mock_tox(payload) -> float:
        return 0.1

    @activity.defn(name="compute_faithfulness")
    async def mock_faith(payload) -> float:
        return 0.9

    @activity.defn(name="compute_perplexity")
    async def mock_perp(payload, prompt_type) -> float:
        return 2.5

    @activity.defn(name="aggregate_composite")
    async def mock_agg(inp: AggregateCompositeInput) -> dict:
        return {"composite": 0.85}

    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[QualityScoreWorkflow],
            activities=[
                mock_lang, mock_pt, mock_coh, mock_tox, mock_faith, mock_perp, mock_agg
            ]
        ):
            res = await env.client.execute_workflow(
                QualityScoreWorkflow.run,
                args=[{"span_id": "s1", "trace_id": "t1", "model": "m", "endpoint": "e"}],
                id="test-quality-wf",
                task_queue="test-queue",
            )
            assert res == {"composite": 0.85}

@pytest.mark.asyncio
async def test_numerical_mismatch_detection(activities) -> None:
    # 1. No numbers -> no mismatch
    payload1 = {
        "span_id": "s1", "trace_id": "t1", "model": "m", "endpoint": "e",
        "response_text": "Hello world", "rag_context": "Hello world",
    }
    inp1 = AggregateCompositeInput(
        payload=payload1, coherence=0.8, toxicity=0.2, faithfulness=0.9, perplexity=None,
        prompt_type="chat", response_language="en"
    )
    res1 = await activities.aggregate_composite(inp1)
    assert "NUMERICAL_MISMATCH" not in res1["quality_flags"]

    # 2. Number matches context -> no mismatch
    payload2 = {
        "span_id": "s1", "trace_id": "t1", "model": "m", "endpoint": "e",
        "response_text": "The price is $42.", "rag_context": "The value is 42 USD.",
    }
    inp2 = AggregateCompositeInput(
        payload=payload2, coherence=0.8, toxicity=0.2, faithfulness=0.9, perplexity=None,
        prompt_type="chat", response_language="en"
    )
    res2 = await activities.aggregate_composite(inp2)
    assert "NUMERICAL_MISMATCH" not in res2["quality_flags"]

    # 3. Number within 5% -> no mismatch (43 is within 5% of 42)
    payload3 = {
        "span_id": "s1", "trace_id": "t1", "model": "m", "endpoint": "e",
        "response_text": "The price is $43.", "rag_context": "The value is 42 USD.",
    }
    inp3 = AggregateCompositeInput(
        payload=payload3, coherence=0.8, toxicity=0.2, faithfulness=0.9, perplexity=None,
        prompt_type="chat", response_language="en"
    )
    res3 = await activities.aggregate_composite(inp3)
    assert "NUMERICAL_MISMATCH" not in res3["quality_flags"]

    # 4. Number outside 5% -> mismatch (45 is outside 5% of 42)
    payload4 = {
        "span_id": "s1", "trace_id": "t1", "model": "m", "endpoint": "e",
        "response_text": "The price is $45.", "rag_context": "The value is 42 USD.",
    }
    inp4 = AggregateCompositeInput(
        payload=payload4, coherence=0.8, toxicity=0.2, faithfulness=0.9, perplexity=None,
        prompt_type="chat", response_language="en"
    )
    res4 = await activities.aggregate_composite(inp4)
    assert "NUMERICAL_MISMATCH" in res4["quality_flags"]
