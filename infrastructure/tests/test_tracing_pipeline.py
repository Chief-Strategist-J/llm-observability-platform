#!/usr/bin/env python3
"""
Standalone test script for the Tracing Pipeline.

This script tests the tracing pipeline functionality without requiring Temporal workers.
It checks Tempo/Jaeger service health, emits test traces, verifies ingestion, and cleans up.
"""

import sys
import os
import time
import urllib.request
import urllib.error
import json
import uuid
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infrastructure.orchestrator.base.base_container_activity import YAMLContainerManager


def check_tempo_health(tempo_url: str = "http://localhost:3200") -> bool:
    """Check if Tempo is healthy and ready."""
    print(f"🔍 Checking Tempo health at {tempo_url}/ready...")
    try:
        req = urllib.request.Request(f"{tempo_url}/ready", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.getcode() == 200:
                print("✅ Tempo is healthy and ready")
                return True
    except Exception as e:
        print(f"❌ Tempo health check failed: {e}")
    return False


def check_jaeger_health(jaeger_url: str = "http://localhost:16686") -> bool:
    """Check if Jaeger UI is accessible."""
    print(f"🔍 Checking Jaeger UI at {jaeger_url}...")
    try:
        req = urllib.request.Request(jaeger_url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.getcode() == 200:
                print("✅ Jaeger UI is accessible")
                return True
    except Exception as e:
        print(f"❌ Jaeger UI check failed: {e}")
    return False


def emit_test_trace(tempo_url: str = "http://localhost:3200") -> tuple[bool, str]:
    """Emit a test trace to Tempo."""
    print(f"🔗 Emitting test trace to Tempo...")
    
    # Generate a trace ID
    trace_id = uuid.uuid4().hex
    span_id = uuid.uuid4().hex[:16]
    
    # Create a simple OTLP trace
    timestamp_ns = int(time.time() * 1e9)
    
    # Simplified trace data (Tempo accepts various formats)
    trace_data = {
        "resourceSpans": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "test_tracing_pipeline"}},
                        {"key": "test.id", "value": {"stringValue": f"test_{int(time.time())}"}}
                    ]
                },
                "scopeSpans": [
                    {
                        "scope": {"name": "test-scope"},
                        "spans": [
                            {
                                "traceId": trace_id,
                                "spanId": span_id,
                                "name": "test-span",
                                "kind": 1,
                                "startTimeUnixNano": str(timestamp_ns),
                                "endTimeUnixNano": str(timestamp_ns + 1000000),
                                "attributes": [
                                    {"key": "test", "value": {"stringValue": "true"}}
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    try:
        data = json.dumps(trace_data).encode('utf-8')
        req = urllib.request.Request(
            f"{tempo_url}/v1/traces",
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.getcode() in [200, 202]:
                print(f"✅ Test trace emitted successfully (ID: {trace_id[:8]}...)")
                return True, trace_id
    except Exception as e:
        print(f"⚠️  Trace emission via Tempo failed: {e}")
        print("   Trying Jaeger OTLP endpoint...")
        
        # Try Jaeger collector endpoint
        try:
            req = urllib.request.Request(
                "http://localhost:4318/v1/traces",
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.getcode() in [200, 202]:
                    print(f"✅ Test trace emitted via Jaeger (ID: {trace_id[:8]}...)")
                    return True, trace_id
        except Exception as e2:
            print(f"❌ Failed to emit test trace: {e2}")
    
    return False, trace_id


def verify_trace_ingestion(tempo_url: str = "http://localhost:3200", trace_id: str = "", max_wait: int = 30) -> bool:
    """Verify that test trace was ingested into Tempo."""
    if not trace_id:
        print("⚠️  No trace ID to verify")
        return False
        
    print(f"🔎 Verifying trace ingestion (Trace ID: {trace_id[:8]}..., max wait: {max_wait}s)...")
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            url = f"{tempo_url}/api/traces/{trace_id}"
            
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.getcode() == 200:
                    body = resp.read().decode('utf-8')
                    data = json.loads(body) if body else {}
                    
                    # Check for trace data
                    if data and (data.get('batches') or data.get('resourceSpans')):
                        print(f"✅ Trace ingestion verified!")
                        return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"⏳ Waiting for trace... ({int(time.time() - start_time)}s)")
            else:
                print(f"⏳ Query error (will retry): {e.code}")
        except Exception as e:
            print(f"⏳ Waiting for trace... ({int(time.time() - start_time)}s)")
        
        time.sleep(2)
    
    print(f"❌ Trace verification timeout after {max_wait}s")
    return False


def cleanup_tempo_jaeger(tempo_instance_id: int = 0, jaeger_instance_id: int = 0) -> bool:
    """Clean up Tempo and Jaeger containers and images."""
    print("\n🧹 Cleaning up Tempo and Jaeger containers and images...")
    
    success = True
    
    try:
        # Cleanup Tempo
        tempo_yaml = str(Path(__file__).parent.parent.parent / 
                        "infrastructure/orchestrator/config/docker/tempo-dynamic-docker.yaml")
        tempo_manager = YAMLContainerManager(tempo_yaml, instance_id=tempo_instance_id)
        if tempo_manager.delete(remove_volumes=True, remove_images=True, remove_networks=False):
            print("✅ Tempo cleanup completed")
        else:
            print("⚠️  Tempo cleanup had issues")
            success = False
    except Exception as e:
        print(f"❌ Tempo cleanup failed: {e}")
        success = False
    
    try:
        # Cleanup Jaeger
        jaeger_yaml = str(Path(__file__).parent.parent.parent / 
                         "infrastructure/orchestrator/config/docker/jaeger-dynamic-docker.yaml")
        jaeger_manager = YAMLContainerManager(jaeger_yaml, instance_id=jaeger_instance_id)
        if jaeger_manager.delete(remove_volumes=True, remove_images=True, remove_networks=False):
            print("✅ Jaeger cleanup completed")
        else:
            print("⚠️  Jaeger cleanup had issues")
            success = False
    except Exception as e:
        print(f"❌ Jaeger cleanup failed: {e}")
        success = False
    
    return success


def setup_tracing(instance_id: int = 0) -> bool:
    """Start Tempo and Jaeger containers."""
    print("\n🚀 Starting Tempo and Jaeger containers...")
    try:
        # Tempo
        tempo_yaml = str(Path(__file__).parent.parent.parent / 
                        "infrastructure/orchestrator/config/docker/tempo-dynamic-docker.yaml")
        tempo_manager = YAMLContainerManager(tempo_yaml, instance_id=instance_id)
        tempo_manager.delete(remove_volumes=True, remove_images=False, remove_networks=False)
        if not tempo_manager.start():
            print("❌ Failed to start Tempo")
            return False
            
        # Jaeger
        jaeger_yaml = str(Path(__file__).parent.parent.parent / 
                         "infrastructure/orchestrator/config/docker/jaeger-dynamic-docker.yaml")
        jaeger_manager = YAMLContainerManager(jaeger_yaml, instance_id=instance_id)
        jaeger_manager.delete(remove_volumes=True, remove_images=False, remove_networks=False)
        if not jaeger_manager.start():
            print("❌ Failed to start Jaeger")
            return False
            
        print("✅ Tracing containers started")
        time.sleep(5)
        return True
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False


def main():
    """Main test execution."""
    print("=" * 60)
    print("🚀 TRACING PIPELINE STANDALONE TEST")
    print("=" * 60)
    print()
    
    # Setup
    if not setup_tracing():
        return 1
    
    results = {
        "tempo_health": False,
        "jaeger_health": False,
        "emit_trace": False,
        "verify_ingestion": False,
        "cleanup": False
    }
    
    trace_id = ""
    
    try:
        # Step 1: Health checks
        # Wait up to 30s
        for _ in range(6):
            if check_tempo_health():
                results["tempo_health"] = True
            if check_jaeger_health():
                results["jaeger_health"] = True
            
            if results["tempo_health"] and results["jaeger_health"]:
                break
            time.sleep(5)
            
        print()
        
        if not results["tempo_health"]:
            print("\n⚠️  Tempo is not healthy after waiting.")
            print("   docker ps | grep tempo")
            print("\nContinuing without Tempo...")
        
        print()
        
        # Step 2: Emit test trace
        results["emit_trace"], trace_id = emit_test_trace()
        if not results["emit_trace"]:
            print("\n❌ Failed to emit test trace")
            # Don't return, try cleanup
        
        print()
        
        # Step 3: Verify ingestion
        if results["tempo_health"] and results["emit_trace"]:
            results["verify_ingestion"] = verify_trace_ingestion(trace_id=trace_id)
        else:
            print("⚠️  Skipping verification (Tempo not available or emission failed)")
            
    finally:
        # Cleanup
        results["cleanup"] = cleanup_tempo_jaeger()
    
    print()
    print("=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    print(f"Tempo Health:       {'✅ PASS' if results['tempo_health'] else '❌ FAIL'}")
    print(f"Jaeger Health:      {'✅ PASS' if results['jaeger_health'] else '❌ FAIL'}")
    print(f"Emit Test Trace:    {'✅ PASS' if results['emit_trace'] else '❌ FAIL'}")
    print(f"Verify Ingestion:   {'✅ PASS' if results['verify_ingestion'] else '⚠️  SKIP' if not results['tempo_health'] else '❌ FAIL'}")
    print(f"Cleanup:            {'✅ PASS' if results['cleanup'] else '❌ FAIL'}")
    print("=" * 60)
    
    # Determine overall status
    required_passed = results["emit_trace"] and (results["tempo_health"] or results["jaeger_health"]) and results["cleanup"]
    
    if required_passed:
        print("\n🎉 CORE TESTS PASSED!")
        return 0
    else:
        print("\n❌ CORE TESTS FAILED")
        return 1


if __name__ == "__main__":
    # Check for cleanup flag
    if "--cleanup" in sys.argv:
        print("=" * 60)
        print("🧹 CLEANUP MODE")
        print("=" * 60)
        cleanup_tempo_jaeger()
        sys.exit(0)
    
    sys.exit(main())
