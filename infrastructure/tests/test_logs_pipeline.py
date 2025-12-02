#!/usr/bin/env python3

import sys
import os
import time
import urllib.request
import urllib.error
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infrastructure.orchestrator.base.base_container_activity import YAMLContainerManager

logging.basicConfig(
    level=logging.INFO,
    format='{"ts": "%(asctime)s", "level": "%(levelname)s", "msg": "%(message)s"}'
)
log = logging.getLogger("logs_pipeline_test")

def check_loki_health(loki_url: str = "http://localhost:3100") -> bool:
    log.info(f"🔍 Checking Loki health at {loki_url}/ready...")
    try:
        req = urllib.request.Request(f"{loki_url}/ready", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.getcode() == 200:
                log.info("✅ Loki is healthy and ready")
                return True
    except Exception as e:
        log.error(f"❌ Loki health check failed: {e}")
    return False

def emit_test_log(loki_url: str = "http://localhost:3100") -> bool:
    log.info("📝 Emitting test log to Loki...")
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
                log.info("✅ Test log emitted successfully")
                return True
    except Exception as e:
        log.error(f"❌ Failed to emit test log: {e}")
    return False

def verify_log_ingestion(loki_url: str = "http://localhost:3100", max_wait: int = 30) -> bool:
    log.info(f"🔎 Verifying log ingestion (max wait: {max_wait}s)...")

    query = '{job="test_logs_pipeline"}'
    start_time = time.time()

    while time.time() - start_time < max_wait:
        try:
            now = int(time.time() * 1e9)
            start_ns = now - (5 * 60 * 1e9)

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
                        log.info(f"✅ Log ingestion verified! Found {len(results)} stream(s)")
                        return True
        except Exception:
            log.info(f"⏳ Waiting for logs... ({int(time.time() - start_time)}s)")

        time.sleep(2)

    log.error(f"❌ Log verification timeout after {max_wait}s")
    return False

def cleanup_loki(instance_id: int = 0) -> bool:
    log.info("🧹 Cleaning up Loki container and images...")
    try:
        yaml_path = str(Path(__file__).parent.parent.parent /
                        "infrastructure/orchestrator/config/docker/loki-dynamic-docker.yaml")

        manager = YAMLContainerManager(yaml_path, instance_id=instance_id)
        success = manager.delete(remove_volumes=True, remove_images=True, remove_networks=False)

        if success:
            log.info("✅ Loki cleanup completed")
        else:
            log.warning("⚠️  Loki cleanup had issues")
        return success
    except Exception as e:
        log.error(f"❌ Cleanup failed: {e}")
        return False

def setup_loki(instance_id: int = 0) -> bool:
    log.info("🚀 Starting Loki container...")
    try:
        config_path = str(Path(__file__).parent.parent.parent /
                          "infrastructure/orchestrator/dynamicconfig/loki-config.yaml")
        os.environ["CONFIG_FILE_PATH"] = config_path

        yaml_path = str(Path(__file__).parent.parent.parent /
                        "infrastructure/orchestrator/config/docker/loki-dynamic-docker.yaml")

        manager = YAMLContainerManager(yaml_path, instance_id=instance_id)
        manager.delete(remove_volumes=True, remove_images=False, remove_networks=False)

        success = manager.start()
        if success:
            log.info("✅ Loki container started")
            time.sleep(5)
        else:
            log.error("❌ Failed to start Loki container")
        return success
    except Exception as e:
        log.error(f"❌ Setup failed: {e}")
        return False

def main():
    log.info("=" * 60)
    log.info("🚀 LOGS PIPELINE STANDALONE TEST")
    log.info("=" * 60)

    if not setup_loki():
        return 1

    results = {
        "health_check": False,
        "emit_log": False,
        "verify_ingestion": False,
        "cleanup": False
    }

    try:
        for _ in range(6):
            if check_loki_health():
                results["health_check"] = True
                break
            time.sleep(5)

        if not results["health_check"]:
            log.warning("⚠️  Loki is not healthy after waiting.")
            log.warning("   docker ps | grep loki")
            log.warning("Skipping test...")
            return 1

        results["emit_log"] = emit_test_log()
        if results["emit_log"]:
            results["verify_ingestion"] = verify_log_ingestion()

    finally:
        results["cleanup"] = cleanup_loki()

    log.info("=" * 60)
    log.info("📊 TEST RESULTS")
    log.info("=" * 60)
    log.info(f"Health Check:      {'✅ PASS' if results['health_check'] else '❌ FAIL'}")
    log.info(f"Emit Test Log:     {'✅ PASS' if results['emit_log'] else '❌ FAIL'}")
    log.info(f"Verify Ingestion:  {'✅ PASS' if results['verify_ingestion'] else '❌ FAIL'}")
    log.info(f"Cleanup:           {'✅ PASS' if results['cleanup'] else '❌ FAIL'}")
    log.info("=" * 60)

    all_passed = all(results.values())

    if all_passed:
        log.info("🎉 ALL TESTS PASSED!")
        return 0
    else:
        log.error("❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    if "--cleanup" in sys.argv:
        log.info("=" * 60)
        log.info("🧹 CLEANUP MODE")
        log.info("=" * 60)
        cleanup_loki()
        sys.exit(0)

    sys.exit(main())
