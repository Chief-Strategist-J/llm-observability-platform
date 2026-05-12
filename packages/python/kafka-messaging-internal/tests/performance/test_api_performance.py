"""Performance tests for API endpoints."""

import pytest
import httpx
import time
import statistics
from typing import List, Dict, Any

from kafka_messaging_internal.api.rest.v1.router import create_app


@pytest.mark.performance
class TestAPIPerformance:
    """Performance tests for API endpoints."""
    
    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        app = create_app()
        return httpx.Client(app=app, base_url="http://test")
    
    @pytest.fixture
    def auth_headers(self):
        """Authentication headers."""
        return {"Authorization": "Bearer test-token"}
    
    @pytest.fixture
    def sample_events(self):
        """Generate sample events for testing."""
        return [
            {
                "event_id": f"perf-event-{i}",
                "topic": "performance-test-topic",
                "partition": 0,
                "offset": i,
                "key": f"perf-key-{i}",
                "value": {
                    "message": f"Performance test message {i}",
                    "data": "x" * 100,  # 100 bytes of data
                    "timestamp": int(time.time() * 1000)
                },
                "timestamp": "2025-01-11T12:00:00Z"
            }
            for i in range(100)
        ]
    
    def test_single_event_insert_performance(self, client, auth_headers, sample_events):
        """Test performance of single event inserts."""
        times = []
        
        for event in sample_events[:10]:  # Test with 10 events
            start_time = time.time()
            response = client.post(
                "/api/v1/database/events",
                json=event,
                headers=auth_headers
            )
            end_time = time.time()
            
            assert response.status_code == 200
            times.append(end_time - start_time)
        
        # Performance assertions
        avg_time = statistics.mean(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]
        
        print(f"Single insert avg: {avg_time:.3f}s, p95: {p95_time:.3f}s")
        
        # Should complete within reasonable time
        assert avg_time < 0.1, f"Average single insert too slow: {avg_time:.3f}s"
        assert p95_time < 0.2, f"P95 single insert too slow: {p95_time:.3f}s"
    
    def test_batch_insert_performance(self, client, auth_headers, sample_events):
        """Test performance of batch event inserts."""
        batch_sizes = [10, 50, 100]
        results = {}
        
        for batch_size in batch_sizes:
            times = []
            batch_events = sample_events[:batch_size]
            
            for _ in range(5):  # Run each batch size 5 times
                start_time = time.time()
                response = client.post(
                    "/api/v1/database/events/batch",
                    json={"records": batch_events},
                    headers=auth_headers
                )
                end_time = time.time()
                
                assert response.status_code == 200
                times.append(end_time - start_time)
            
            avg_time = statistics.mean(times)
            throughput = batch_size / avg_time  # events per second
            
            results[batch_size] = {
                "avg_time": avg_time,
                "throughput": throughput
            }
            
            print(f"Batch size {batch_size}: avg {avg_time:.3f}s, throughput {throughput:.1f} events/s")
            
            # Performance assertions
            assert avg_time < 1.0, f"Batch insert too slow for size {batch_size}: {avg_time:.3f}s"
            assert throughput > 50, f"Throughput too low for size {batch_size}: {throughput:.1f} events/s"
        
        # Larger batches should have better throughput
        assert results[50]["throughput"] > results[10]["throughput"]
        assert results[100]["throughput"] > results[50]["throughput"]
    
    def test_query_performance(self, client, auth_headers):
        """Test performance of event queries."""
        # First, insert some test data
        events = [
            {
                "event_id": f"query-test-{i}",
                "topic": "query-performance-topic",
                "partition": 0,
                "offset": i,
                "key": f"query-key-{i}",
                "value": {"message": f"Query test message {i}"},
                "timestamp": "2025-01-11T12:00:00Z"
            }
            for i in range(1000)
        ]
        
        # Insert in batches
        for i in range(0, len(events), 100):
            batch = events[i:i+100]
            response = client.post(
                "/api/v1/database/events/batch",
                json={"records": batch},
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Test query performance with different limits
        limits = [10, 50, 100, 500]
        
        for limit in limits:
            times = []
            
            for _ in range(10):  # Run each query 10 times
                start_time = time.time()
                response = client.get(
                    f"/api/v1/database/events?topic=query-performance-topic&limit={limit}",
                    headers=auth_headers
                )
                end_time = time.time()
                
                assert response.status_code == 200
                result = response.json()
                assert result["count"] <= limit
                
                times.append(end_time - start_time)
            
            avg_time = statistics.mean(times)
            p95_time = sorted(times)[int(len(times) * 0.95)]
            
            print(f"Query limit {limit}: avg {avg_time:.3f}s, p95 {p95_time:.3f}s")
            
            # Performance assertions
            assert avg_time < 0.5, f"Query too slow for limit {limit}: {avg_time:.3f}s"
            assert p95_time < 1.0, f"Query P95 too slow for limit {limit}: {p95_time:.3f}s"
    
    def test_concurrent_requests_performance(self, client, auth_headers):
        """Test performance under concurrent load."""
        import threading
        import queue
        
        def worker(event_queue: queue.Queue, results: queue.Queue):
            """Worker function for concurrent requests."""
            while True:
                try:
                    event = event_queue.get_nowait()
                except queue.Empty:
                    break
                
                start_time = time.time()
                response = client.post(
                    "/api/v1/database/events",
                    json=event,
                    headers=auth_headers
                )
                end_time = time.time()
                
                results.append({
                    "status_code": response.status_code,
                    "duration": end_time - start_time
                })
                
                event_queue.task_done()
        
        # Prepare test events
        num_requests = 50
        event_queue = queue.Queue()
        results = []
        
        for i in range(num_requests):
            event_queue.put({
                "event_id": f"concurrent-test-{i}",
                "topic": "concurrent-test-topic",
                "partition": 0,
                "offset": i,
                "key": f"concurrent-key-{i}",
                "value": {"message": f"Concurrent test message {i}"},
                "timestamp": "2025-01-11T12:00:00Z"
            })
        
        # Start worker threads
        num_workers = 5
        threads = []
        
        for _ in range(num_workers):
            thread = threading.Thread(target=worker, args=(event_queue, results))
            thread.start()
            threads.append(thread)
        
        # Wait for all work to complete
        event_queue.join()
        for thread in threads:
            thread.join()
        
        # Analyze results
        assert len(results) == num_requests
        
        success_count = sum(1 for r in results if r["status_code"] == 200)
        assert success_count == num_requests, f"Only {success_count}/{num_requests} requests succeeded"
        
        durations = [r["duration"] for r in results]
        avg_duration = statistics.mean(durations)
        p95_duration = sorted(durations)[int(len(durations) * 0.95)]
        
        print(f"Concurrent requests: avg {avg_duration:.3f}s, p95 {p95_duration:.3f}s")
        
        # Performance assertions
        assert avg_duration < 0.5, f"Concurrent avg too slow: {avg_duration:.3f}s"
        assert p95_duration < 1.0, f"Concurrent P95 too slow: {p95_duration:.3f}s"
    
    def test_memory_usage_stability(self, client, auth_headers):
        """Test memory usage stability over time."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform many operations
        for batch_num in range(10):
            # Insert batch
            events = [
                {
                    "event_id": f"memory-test-{batch_num}-{i}",
                    "topic": "memory-test-topic",
                    "partition": 0,
                    "offset": batch_num * 100 + i,
                    "key": f"memory-key-{batch_num}-{i}",
                    "value": {"message": f"Memory test message {batch_num}-{i}", "data": "x" * 1000},
                    "timestamp": "2025-01-11T12:00:00Z"
                }
                for i in range(100)
            ]
            
            response = client.post(
                "/api/v1/database/events/batch",
                json={"records": events},
                headers=auth_headers
            )
            assert response.status_code == 200
            
            # Query events
            response = client.get(
                "/api/v1/database/events?topic=memory-test-topic&limit=50",
                headers=auth_headers
            )
            assert response.status_code == 200
            
            # Check memory
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory
            
            print(f"Batch {batch_num}: memory {current_memory:.1f}MB (+{memory_increase:.1f}MB)")
            
            # Memory should not grow excessively
            assert memory_increase < 100, f"Memory growth too high: {memory_increase:.1f}MB"
    
    def test_schema_registry_performance(self, client, auth_headers):
        """Test schema registry performance."""
        schema_data = {
            "subject": "performance-schema",
            "schema": '{"type": "record", "name": "PerfRecord", "fields": [{"name": "message", "type": "string"}, {"name": "data", "type": "bytes"}]}',
            "schema_type": "AVRO"
        }
        
        # Test schema registration
        times = []
        for i in range(10):
            subject = f"performance-schema-{i}"
            test_schema = schema_data.copy()
            test_schema["subject"] = subject
            
            start_time = time.time()
            response = client.post(
                "/api/v1/schema-registry/schemas",
                json=test_schema,
                headers=auth_headers
            )
            end_time = time.time()
            
            assert response.status_code == 200
            times.append(end_time - start_time)
        
        avg_time = statistics.mean(times)
        print(f"Schema registration avg: {avg_time:.3f}s")
        assert avg_time < 0.5, f"Schema registration too slow: {avg_time:.3f}s"
        
        # Test schema retrieval
        times = []
        for i in range(10):
            subject = f"performance-schema-{i}"
            
            start_time = time.time()
            response = client.get(
                f"/api/v1/schema-registry/schemas/{subject}",
                headers=auth_headers
            )
            end_time = time.time()
            
            assert response.status_code == 200
            times.append(end_time - start_time)
        
        avg_time = statistics.mean(times)
        print(f"Schema retrieval avg: {avg_time:.3f}s")
        assert avg_time < 0.1, f"Schema retrieval too slow: {avg_time:.3f}s"
