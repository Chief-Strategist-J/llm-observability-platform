#!/usr/bin/env python3
"""
Standalone test script for the Logs Pipeline.

This script tests the logs pipeline functionality without requiring Temporal workers.
It checks Loki service health, emits test events, verifies ingestion, and cleans up.
"""

import sys
import os
import time
import urllib.request
import urllib.error
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infrastructure.orchestrator.base.base_container_activity import YAMLContainerManager


def check_loki_health(loki_url: str = "http://localhost:3100") -> bool:
    """Check if Loki is healthy and ready."""
    print(f"🔍 Checking Loki health at {loki_url}/ready...")
    try:
        req = urllib.request.Request(f"{loki_url}/ready", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.getcode() == 200:
                print("✅ Loki is healthy and ready")
                return True
    except Exception as e:
        print(f"❌ Loki health check failed: {e}")
    return False


def emit_test_log(loki_url: str = "http://localhost:3100") -> bool:
    """Emit a test log entry to Loki."""
    print(f"📝 Emitting test log to Loki...")
    
    # Create a test log entry
    timestamp_ns = int(time.time() * 1e9)
    log_data = {
        "streams": [
            {
                "stream": {
                    "job": "test_logs_pipeline",
                    "level": "info",
                    "source": "test_script",
                    "test_id": f"test_{int(time.time())}"
                },
                "values": [
                    [str(timestamp_ns), f"Test log entry from standalone test at {time.ctime()}"]
                ]
            }
        ]
    }
    
    try:
        data = json.dumps(log_data).encode('utf-8')
        req = urllib.request.Request(
            f"{loki_url}/loki/api/v1/push",
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.getcode() in [200, 204]:
                print("✅ Test log emitted successfully")
                return True
    except Exception as e:
        print(f"❌ Failed to emit test log: {e}")
    return False


def verify_log_ingestion(loki_url: str = "http://localhost:3100", max_wait: int = 30) -> bool:
    """Verify that test logs were ingested into Loki."""
    print(f"🔎 Verifying log ingestion (max wait: {max_wait}s)...")
    
    query = '{job="test_logs_pipeline"}'
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            now = int(time.time() * 1e9)
            start_ns = now - (5 * 60 * 1e9)  # Last 5 minutes
            
            url = (
                f"{loki_url}/loki/api/v1/query_range?"
                f"query={urllib.parse.quote(query)}&"
                f"start={start_ns}&end={now}&limit=100"
            )
            
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.getcode() == 200:
                    body = resp.read().decode('utf-8')
                    data = json.loads(body)
                    results = data.get('data', {}).get('result', [])
                    
                    if results:
                        print(f"✅ Log ingestion verified! Found {len(results)} stream(s)")
                        return True
        except Exception as e:
            print(f"⏳ Waiting for logs... ({int(time.time() - start_time)}s)")
        
        time.sleep(2)
    
    print(f"❌ Log verification timeout after {max_wait}s")
    return False


def cleanup_loki(instance_id: int = 0) -> bool:
    """Clean up Loki container and images."""
    print("\n🧹 Cleaning up Loki container and images...")
    try:
        yaml_path = str(Path(__file__).parent.parent.parent / 
                       "infrastructure/orchestrator/config/docker/loki-dynamic-docker.yaml")
        
        manager = YAMLContainerManager(yaml_path, instance_id=instance_id)
        success = manager.delete(remove_volumes=True, remove_images=True, remove_networks=False)
        
        if success:
            print("✅ Loki cleanup completed")
        else:
            print("⚠️  Loki cleanup had issues")
        return success
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False


def setup_loki(instance_id: int = 0) -> bool:
    """Start Loki container."""
    print("\n🚀 Starting Loki container...")
    try:
        # Set config path env var
        config_path = str(Path(__file__).parent.parent.parent / 
                         "infrastructure/orchestrator/dynamicconfig/loki-config.yaml")
        os.environ["CONFIG_FILE_PATH"] = config_path
        
        yaml_path = str(Path(__file__).parent.parent.parent / 
                       "infrastructure/orchestrator/config/docker/loki-dynamic-docker.yaml")
        
        manager = YAMLContainerManager(yaml_path, instance_id=instance_id)
        # Ensure cleanup first
        manager.delete(remove_volumes=True, remove_images=False, remove_networks=False)
        
        success = manager.start()
        if success:
            print("✅ Loki container started")
            # Wait a bit for startup
            time.sleep(5)
        else:
            print("❌ Failed to start Loki container")
        return success
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False


def main():
    """Main test execution."""
    print("=" * 60)
    print("🚀 LOGS PIPELINE STANDALONE TEST")
    print("=" * 60)
    print()
    
    # Setup
    if not setup_loki():
        return 1
    
    results = {
        "health_check": False,
        "emit_log": False,
        "verify_ingestion": False,
        "cleanup": False
    }
    
    try:
        # Step 1: Health check
        # Wait up to 30s for health
        for _ in range(6):
            if check_loki_health():
                results["health_check"] = True
                break
            time.sleep(5)
            
        if not results["health_check"]:
            print("\n⚠️  Loki is not healthy after waiting.")
            print("   docker ps | grep loki")
            print("\nSkipping test...")
            return 1
        
        print()
        
        # Step 2: Emit test log
        results["emit_log"] = emit_test_log()
        if not results["emit_log"]:
            print("\n❌ Failed to emit test log")
            # Don't return here, try to cleanup
        
        print()
        
        # Step 3: Verify ingestion
        if results["emit_log"]:
            results["verify_ingestion"] = verify_log_ingestion()
        
    finally:
        # Cleanup
        results["cleanup"] = cleanup_loki()
    
    print()
    print("=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    print(f"Health Check:      {'✅ PASS' if results['health_check'] else '❌ FAIL'}")
    print(f"Emit Test Log:     {'✅ PASS' if results['emit_log'] else '❌ FAIL'}")
    print(f"Verify Ingestion:  {'✅ PASS' if results['verify_ingestion'] else '❌ FAIL'}")
    print(f"Cleanup:           {'✅ PASS' if results['cleanup'] else '❌ FAIL'}")
    print("=" * 60)
    
    # Determine overall status
    all_passed = all([results["health_check"], results["emit_log"], results["verify_ingestion"], results["cleanup"]])
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    # Check for cleanup flag
    if "--cleanup" in sys.argv:
        print("=" * 60)
        print("🧹 CLEANUP MODE")
        print("=" * 60)
        cleanup_loki()
        sys.exit(0)
    
    sys.exit(main())
