import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from infrastructure.observability.logIntelligent.client.api_client import LogIntelligenceApiClient
from infrastructure.observability.logIntelligent.intelligence.drift import ADWINLikeDriftDetector
from infrastructure.observability.logIntelligent.intelligence.frequency import CountMinSketch
from infrastructure.observability.logIntelligent.models import RawLogRecord
from infrastructure.observability.logIntelligent.pipeline import LogIntelligencePipeline
from infrastructure.observability.logIntelligent.storage.router import StorageRouter


class TestCriticalPipelineBehavior(unittest.TestCase):
    def test_count_min_sketch_error_bounds_and_monotonicity(self):
        sketch = CountMinSketch(width=2000, depth=7)
        for _ in range(9):
            sketch.add("template-A")
        first = sketch.estimate("template-A")
        sketch.add("template-A", count=5)
        second = sketch.estimate("template-A")

        self.assertGreaterEqual(first, 9)
        self.assertGreaterEqual(second, first)
        self.assertLess(sketch.epsilon, 0.002)
        self.assertLess(sketch.delta, 0.001)

    def test_drift_detector_flags_large_distribution_shift(self):
        detector = ADWINLikeDriftDetector(max_window=20, sensitivity=0.3)
        has_drift = False
        for value in [1] * 10 + [8] * 10:
            has_drift = detector.update("tpl", value)
        self.assertTrue(has_drift)

    def test_pipeline_storage_router_and_trace_lookup(self):
        pipeline = LogIntelligencePipeline()
        recent = RawLogRecord(
            line_id="line-hot",
            message="2026-04-27T10:00:00Z INFO service=checkout trace_id=t-1 payment failed",
            received_at=datetime.now(timezone.utc),
        )
        older = RawLogRecord(
            line_id="line-cold",
            message="2026-03-01T10:00:00Z ERROR service=checkout trace_id=t-1 retry exhausted",
            received_at=datetime.now(timezone.utc) - timedelta(days=60),
        )

        parsed_recent = pipeline.ingest(recent)
        parsed_older = pipeline.ingest(older)

        self.assertEqual(parsed_recent.storage_tier, "hot")
        self.assertEqual(parsed_older.storage_tier, "cold")
        self.assertEqual(pipeline.trace_index.lookup("t-1"), ["line-hot", "line-cold"])


class TestApiAndClient(unittest.TestCase):
    def test_api_ingest_and_trace_flow(self):
        from infrastructure.observability.logIntelligent.api.schemas import IngestLogRequest
        from infrastructure.observability.logIntelligent.api.service import LogIntelligenceService

        service = LogIntelligenceService(LogIntelligencePipeline())
        payload = service.ingest(
            IngestLogRequest(
                line_id="line-api-1",
                message="2026-04-27T10:00:00Z WARN service=billing trace_id=trace-api-1 card timeout",
            )
        )
        self.assertTrue(payload.template_id)
        self.assertEqual(payload.normalized_fields["level"], "WARNING")

        trace_payload = service.trace_lookup("trace-api-1")
        self.assertEqual(trace_payload.line_ids, ["line-api-1"])

    @patch("infrastructure.observability.logIntelligent.client.api_client.requests.post")
    @patch("infrastructure.observability.logIntelligent.client.api_client.requests.get")
    def test_client_contract(self, mock_get: MagicMock, mock_post: MagicMock):
        post_response = MagicMock()
        post_response.json.return_value = {"template_id": "abc"}
        post_response.raise_for_status.return_value = None
        mock_post.return_value = post_response

        get_response = MagicMock()
        get_response.json.return_value = {"line_ids": ["l1", "l2"]}
        get_response.raise_for_status.return_value = None
        mock_get.return_value = get_response

        api_client = LogIntelligenceApiClient("http://localhost:8113")
        ingest_payload = api_client.ingest("l1", "hello")
        line_ids = api_client.trace_lookup("trace-1")

        self.assertEqual(ingest_payload["template_id"], "abc")
        self.assertEqual(line_ids, ["l1", "l2"])


class TestRouterBoundaries(unittest.TestCase):
    def test_storage_boundaries(self):
        now = datetime(2026, 4, 27, tzinfo=timezone.utc)
        router = StorageRouter(now_fn=lambda: now)

        self.assertEqual(router.route(now - timedelta(hours=23)).tier, "hot")
        self.assertEqual(router.route(now - timedelta(days=7)).tier, "warm")
        self.assertEqual(router.route(now - timedelta(days=31)).tier, "cold")


if __name__ == "__main__":
    unittest.main()

class TestProductionFailureScenarios(unittest.TestCase):
    def test_structural_enricher_handles_missing_service_and_invalid_timestamp(self):
        pipeline = LogIntelligencePipeline()
        parsed = pipeline.ingest(
            RawLogRecord(
                line_id="line-invalid-ts",
                message="2026-99-99T10:00:00Z ERROR trace_id=t-prod failure happened",
            )
        )
        self.assertEqual(parsed.normalized_fields["service"], "unknown")
        self.assertEqual(parsed.normalized_fields["level"], "ERROR")

    def test_template_similarity_for_unknown_template_returns_empty(self):
        pipeline = LogIntelligencePipeline()
        self.assertEqual(pipeline.similar_templates("missing-template", k=3), [])

    def test_anomaly_score_is_bounded_under_repeated_unseen_fields(self):
        pipeline = LogIntelligencePipeline()
        score = 0.0
        for i in range(30):
            parsed = pipeline.ingest(
                RawLogRecord(
                    line_id=f"line-{i}",
                    message=f"2026-04-27T10:00:00Z WARN service=s{i} trace_id=t-{i} err code {1000+i}",
                )
            )
            score = parsed.anomaly_score
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_dependency_injection_allows_swapping_parser(self):
        class FixedParser:
            def parse(self, message: str):
                return "fixed-template", "fixed-template"

        from infrastructure.observability.logIntelligent.dependencies import build_default_dependencies, PipelineDependencies

        base = build_default_dependencies()
        deps = PipelineDependencies(
            template_store=base.template_store,
            parser=FixedParser(),
            structural_enricher=base.structural_enricher,
            embedding_cache=base.embedding_cache,
            frequency=base.frequency,
            drift=base.drift,
            anomaly=base.anomaly,
            semantic_index=base.semantic_index,
            trace_index=base.trace_index,
            storage_router=base.storage_router,
        )
        pipeline = LogIntelligencePipeline(dependencies=deps)
        parsed = pipeline.ingest(RawLogRecord(line_id="line-fixed", message="any payload"))
        self.assertEqual(parsed.template_id, "fixed-template")

class TestAdditionalCriticalScenarios(unittest.TestCase):
    def test_log_level_alias_normalization_err_maps_to_error(self):
        pipeline = LogIntelligencePipeline()
        parsed = pipeline.ingest(
            RawLogRecord(
                line_id="line-err",
                message="2026-04-27T10:00:00Z ERR service=payments trace_id=t-err downstream timeout",
            )
        )
        self.assertEqual(parsed.normalized_fields["level"], "ERROR")

    def test_storage_boundary_exact_thresholds(self):
        now = datetime(2026, 4, 27, tzinfo=timezone.utc)
        router = StorageRouter(now_fn=lambda: now)
        self.assertEqual(router.route(now - timedelta(hours=24)).tier, "hot")
        self.assertEqual(router.route(now - timedelta(days=30)).tier, "warm")

    def test_similar_templates_returns_self_and_neighbors_when_available(self):
        pipeline = LogIntelligencePipeline()
        first = pipeline.ingest(
            RawLogRecord(
                line_id="line-sim-1",
                message="2026-04-27T10:00:00Z INFO service=auth trace_id=t-sim user 100 login failed",
            )
        )
        pipeline.ingest(
            RawLogRecord(
                line_id="line-sim-2",
                message="2026-04-27T10:00:02Z INFO service=auth trace_id=t-sim user 200 login failed",
            )
        )
        neighbors = pipeline.similar_templates(first.template_id, k=2)
        self.assertTrue(neighbors)
        self.assertEqual(neighbors[0], first.template_id)

    def test_count_min_sketch_never_undercounts_known_key(self):
        sketch = CountMinSketch(width=2000, depth=7)
        for _ in range(50):
            sketch.add("key-A")
        for _ in range(10):
            sketch.add("key-B")
        self.assertGreaterEqual(sketch.estimate("key-A"), 50)

class TestImplementedPlannedComponents(unittest.TestCase):
    def test_template_store_trie_lookup(self):
        from infrastructure.observability.logIntelligent.ingestion.template_store import TemplateStore

        store = TemplateStore()
        template_id = store.register("INFO service=auth user <NUM> failed")
        found = store.find_template_id("INFO service=auth user <NUM> failed")
        self.assertEqual(found, template_id)

    def test_semantic_embedding_fallback_is_stable(self):
        from unittest.mock import patch
        from infrastructure.observability.logIntelligent.enrichment.semantic import TemplateEmbeddingCache

        cache = TemplateEmbeddingCache(dim=384)
        with patch.object(cache, "_get_model", side_effect=RuntimeError("model unavailable")):
            one = cache.get_or_compute("id-1", "hello world")
            two = cache.get_or_compute("id-1", "hello world")
        self.assertEqual(len(one), 384)
        self.assertEqual(one, two)

    def test_isolation_forest_scorer_trains_and_stays_bounded(self):
        from infrastructure.observability.logIntelligent.enrichment.anomaly import IsolationForestLikeScorer

        scorer = IsolationForestLikeScorer(window_size=64, retrain_interval=8)
        last_score = 0.0
        for i in range(80):
            last_score = scorer.score(template_count=(i % 5) + 1, unseen_fields=i % 7, drift_detected=(i % 9 == 0))
        self.assertGreaterEqual(last_score, 0.0)
        self.assertLessEqual(last_score, 1.0)

    def test_semantic_index_returns_nearest_for_inserted_vector(self):
        from infrastructure.observability.logIntelligent.intelligence.semantic_index import HNSWLikeIndex

        index = HNSWLikeIndex()
        index.upsert("a", (1.0, 0.0, 0.0))
        index.upsert("b", (0.0, 1.0, 0.0))
        result = index.query((1.0, 0.0, 0.0), k=1)
        self.assertEqual(result, ["a"])

class TestApiSurfaceCriticality(unittest.TestCase):
    def test_service_capability_metrics_shape_and_bounds(self):
        from infrastructure.observability.logIntelligent.api.service import LogIntelligenceService

        service = LogIntelligenceService(LogIntelligencePipeline())
        metrics = service.capability_metrics()
        self.assertTrue(metrics.implemented)
        self.assertTrue(metrics.partial)
        self.assertTrue(metrics.pending)
        self.assertGreaterEqual(metrics.readiness_score, 0.0)
        self.assertLessEqual(metrics.readiness_score, 1.0)

    def test_service_batch_ingest_and_log_lookup(self):
        from infrastructure.observability.logIntelligent.api.schemas import IngestLogRequest
        from infrastructure.observability.logIntelligent.api.service import LogIntelligenceService

        service = LogIntelligenceService(LogIntelligencePipeline())
        response = service.ingest_batch(
            [
                IngestLogRequest(line_id="b1", message="2026-04-27T10:00:00Z INFO service=auth trace_id=tb login"),
                IngestLogRequest(line_id="b2", message="2026-04-27T10:00:01Z ERROR service=auth trace_id=tb fail"),
            ]
        )
        self.assertEqual(len(response), 2)
        lookup = service.log_lookup("b2")
        self.assertTrue(lookup.found)
        self.assertIsNotNone(lookup.item)
        self.assertEqual(lookup.item.line_id, "b2")

    @patch("infrastructure.observability.logIntelligent.client.api_client.requests.get")
    @patch("infrastructure.observability.logIntelligent.client.api_client.requests.post")
    def test_client_exposes_health_metrics_batch_and_lookup(self, mock_post: MagicMock, mock_get: MagicMock):
        get_response = MagicMock()
        get_response.raise_for_status.return_value = None
        get_response.json.side_effect = [
            {"status": "ok"},
            {"implemented": ["a"], "partial": ["b"], "pending": ["c"], "readiness_score": 0.5},
            {"found": True, "item": {"line_id": "l1"}},
        ]
        mock_get.return_value = get_response

        post_response = MagicMock()
        post_response.raise_for_status.return_value = None
        post_response.json.return_value = {"items": [{"line_id": "l1"}]}
        mock_post.return_value = post_response

        client = LogIntelligenceApiClient("http://localhost:8113")
        self.assertEqual(client.health()["status"], "ok")
        self.assertIn("implemented", client.capability_metrics())
        self.assertEqual(client.ingest_batch([{"line_id": "l1", "message": "m"}])["items"][0]["line_id"], "l1")
        self.assertTrue(client.log_lookup("l1")["found"])
