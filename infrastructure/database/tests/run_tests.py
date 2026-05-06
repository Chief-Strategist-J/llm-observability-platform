#!/usr/bin/env python3
"""
Comprehensive test runner for database query monitoring system.

This script runs all tests for the database monitoring components including:
- Shared utilities and interfaces
- MongoDB monitoring components
- Neo4j monitoring components  
- PostgreSQL monitoring components
- Cross-database integration tests
- API endpoint tests

Usage:
    python run_tests.py [--verbose] [--database <database>] [--pattern <pattern>]

Options:
    --verbose: Enable verbose output
    --database: Test specific database only (mongodb, neo4j, postgres, shared)
    --pattern: Run tests matching specific pattern
"""

import sys
import os
import unittest
import argparse
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))


def discover_tests(test_dir: Path, pattern: str = "test_*.py") -> unittest.TestSuite:
    """Discover all test files in the given directory."""
    loader = unittest.TestLoader()
    start_dir = str(test_dir)
    suite = loader.discover(start_dir, pattern=pattern)
    return suite


def run_specific_database_tests(database: str, verbose: bool = False) -> bool:
    """Run tests for a specific database."""
    test_dirs = {
        "shared": project_root / "infrastructure/database/shared/tests",
        "mongodb": project_root / "infrastructure/database/mongodb/tests",
        "neo4j": project_root / "infrastructure/database/neo4j/tests",
        "postgres": project_root / "infrastructure/database/postgres/tests"
    }
    
    if database not in test_dirs:
        print(f"Unknown database: {database}")
        print(f"Available databases: {', '.join(test_dirs.keys())}")
        return False
    
    test_dir = test_dirs[database]
    if not test_dir.exists():
        print(f"Test directory not found: {test_dir}")
        return False
    
    print(f"\n{'='*60}")
    print(f"Running {database.upper()} Database Monitoring Tests")
    print(f"{'='*60}")
    
    suite = discover_tests(test_dir)
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_all_tests(verbose: bool = False, pattern: str = "test_*.py") -> bool:
    """Run all tests across all database monitoring components."""
    print(f"\n{'='*60}")
    print("Running Complete Database Monitoring Test Suite")
    print(f"{'='*60}")
    
    test_dirs = [
        project_root / "infrastructure/database/shared/tests",
        project_root / "infrastructure/database/mongodb/tests",
        project_root / "infrastructure/database/neo4j/tests",
        project_root / "infrastructure/database/postgres/tests",
        project_root / "infrastructure/database/tests"
    ]
    
    all_suites = unittest.TestSuite()
    
    for test_dir in test_dirs:
        if test_dir.exists():
            suite = discover_tests(test_dir, pattern)
            all_suites.addTest(suite)
        else:
            print(f"Warning: Test directory not found: {test_dir}")
    
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(all_suites)
    
    return result.wasSuccessful()


def run_integration_tests(verbose: bool = False) -> bool:
    """Run integration tests specifically."""
    print(f"\n{'='*60}")
    print("Running Cross-Database Integration Tests")
    print(f"{'='*60}")
    
    test_dir = project_root / "infrastructure/database/tests"
    if not test_dir.exists():
        print(f"Integration test directory not found: {test_dir}")
        return False
    
    suite = discover_tests(test_dir, "test_integration.py")
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_performance_tests(verbose: bool = False) -> bool:
    """Run performance-related tests."""
    print(f"\n{'='*60}")
    print("Running Performance Analysis Tests")
    print(f"{'='*60}")
    
    test_dirs = [
        project_root / "infrastructure/database/shared/tests",
        project_root / "infrastructure/database/tests"
    ]
    
    performance_suite = unittest.TestSuite()
    
    for test_dir in test_dirs:
        if test_dir.exists():
            loader = unittest.TestLoader()
            suite = loader.discover(str(test_dir), pattern="test_*performance*.py")
            performance_suite.addTest(suite)
    
    if performance_suite.countTestCases() == 0:
        print("No performance tests found")
        return True
    
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(performance_suite)
    
    return result.wasSuccessful()


def main():
    parser = argparse.ArgumentParser(description="Run database monitoring tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--database", "-d", choices=["shared", "mongodb", "neo4j", "postgres", "all"],
                       default="all", help="Test specific database (default: all)")
    parser.add_argument("--pattern", "-p", default="test_*.py", help="Test file pattern")
    parser.add_argument("--integration-only", action="store_true", help="Run only integration tests")
    parser.add_argument("--performance-only", action="store_true", help="Run only performance tests")
    
    args = parser.parse_args()
    
    # Check if we're in the right directory
    if not (project_root / "infrastructure/database").exists():
        print("Error: Not in the correct project directory")
        print("Please run this script from the project root or infrastructure/database directory")
        sys.exit(1)
    
    success = True
    
    try:
        if args.integration_only:
            success = run_integration_tests(args.verbose)
        elif args.performance_only:
            success = run_performance_tests(args.verbose)
        elif args.database == "all":
            success = run_all_tests(args.verbose, args.pattern)
        else:
            success = run_specific_database_tests(args.database, args.verbose)
        
        if success:
            print(f"\n{'='*60}")
            print("✅ All tests passed successfully!")
            print(f"{'='*60}")
            sys.exit(0)
        else:
            print(f"\n{'='*60}")
            print("❌ Some tests failed!")
            print(f"{'='*60}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError running tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
