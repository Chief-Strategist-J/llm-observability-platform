#!/usr/bin/env python3
"""
Orchestrator test script for all observability pipelines.

This script runs all three pipeline tests (logs, metrics, tracing) sequentially
and provides a comprehensive summary of results.
"""

import sys
import subprocess
from pathlib import Path


def run_test(test_name: str, script_path: Path) -> dict:
    """Run a single test script and return results."""
    print(f"\n{'=' * 60}")
    print(f"Running {test_name}...")
    print(f"{'=' * 60}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=False,
            text=True,
            check=False
        )
        
        return {
            "name": test_name,
            "passed": result.returncode == 0,
            "return_code": result.returncode
        }
    except Exception as e:
        print(f"❌ Error running {test_name}: {e}")
        return {
            "name": test_name,
            "passed": False,
            "return_code": -1,
            "error": str(e)
        }


def cleanup_all():
    """Run cleanup for all pipelines."""
    print("\n" + "=" * 60)
    print("🧹 CLEANING UP ALL PIPELINES")
    print("=" * 60 + "\n")
    
    tests_dir = Path(__file__).parent
    
    scripts = [
        ("Logs Pipeline", tests_dir / "test_logs_pipeline.py"),
        ("Metrics Pipeline", tests_dir / "test_metrics_pipeline.py"),
        ("Tracing Pipeline", tests_dir / "test_tracing_pipeline.py"),
    ]
    
    for name, script in scripts:
        if script.exists():
            print(f"\nCleaning up {name}...")
            try:
                subprocess.run(
                    [sys.executable, str(script), "--cleanup"],
                    capture_output=False,
                    text=True,
                    check=False
                )
            except Exception as e:
                print(f"❌ Cleanup error for {name}: {e}")


def main():
    """Main execution."""
    print("=" * 60)
    print("🚀 ALL OBSERVABILITY PIPELINES TEST")
    print("=" * 60)
    print("\nThis will test:")
    print("  1. Logs Pipeline (Loki)")
    print("  2. Metrics Pipeline (Prometheus)")
    print("  3. Tracing Pipeline (Tempo/Jaeger)")
    print()
    
    tests_dir = Path(__file__).parent
    
    # Define tests to run
    tests = [
        ("Logs Pipeline", tests_dir / "test_logs_pipeline.py"),
        ("Metrics Pipeline", tests_dir / "test_metrics_pipeline.py"),
        ("Tracing Pipeline", tests_dir / "test_tracing_pipeline.py"),
    ]
    
    results = []
    
    # Run each test
    for test_name, script_path in tests:
        if not script_path.exists():
            print(f"\n❌ Test script not found: {script_path}")
            results.append({
                "name": test_name,
                "passed": False,
                "return_code": -1,
                "error": "Script not found"
            })
            continue
        
        result = run_test(test_name, script_path)
        results.append(result)
    
    # Print summary
    print("\n\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 60)
    
    for result in results:
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"{result['name']:.<40} {status}")
        if not result["passed"] and "error" in result:
            print(f"   Error: {result['error']}")
    
    print("=" * 60)
    
    # Overall result
    all_passed = all(r["passed"] for r in results)
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    
    print(f"\nResults: {passed}/{total} pipelines passed")
    
    if all_passed:
        print("\n🎉 ALL PIPELINES PASSED!")
        print("\nTo cleanup all test containers:")
        print("   python infrastructure/tests/test_all_pipelines.py --cleanup")
        return 0
    else:
        print("\n❌ SOME PIPELINES FAILED")
        failed = [r["name"] for r in results if not r["passed"]]
        print(f"Failed: {', '.join(failed)}")
        return 1


if __name__ == "__main__":
    # Check for cleanup flag
    if "--cleanup" in sys.argv:
        cleanup_all()
        sys.exit(0)
    
    sys.exit(main())
