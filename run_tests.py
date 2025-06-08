#!/usr/bin/env python3
"""
CodeGraph Test Runner
Provides easy commands for running different types of tests with proper configuration.
"""

import os
import sys
import subprocess
import argparse


def set_env_vars(skip_integration=True, skip_api_cost=False, skip_slow=False):
    """Set environment variables for test configuration"""
    os.environ["SKIP_INTEGRATION_TESTS"] = str(skip_integration).lower()
    os.environ["SKIP_API_COST_TESTS"] = str(skip_api_cost).lower()
    os.environ["SKIP_SLOW_TESTS"] = str(skip_slow).lower()


def run_pytest(args):
    """Run pytest with given arguments"""
    cmd = ["python", "-m", "pytest"] + args
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd).returncode


def main():
    parser = argparse.ArgumentParser(description="CodeGraph Test Runner")
    
    # Test type selection
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--unit", action="store_true", 
                      help="Run only unit tests (fast, no API calls)")
    group.add_argument("--integration", action="store_true",
                      help="Run integration tests (expensive, with API calls)")
    group.add_argument("--all", action="store_true",
                      help="Run all tests including expensive ones")
    group.add_argument("--core", action="store_true", default=True,
                      help="Run core tests (default: unit + some API tests)")
    
    # Additional options
    parser.add_argument("--no-api", action="store_true",
                       help="Skip all API cost tests")
    parser.add_argument("--no-slow", action="store_true", 
                       help="Skip slow tests")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    parser.add_argument("--module", "-m", type=str,
                       help="Run specific test module (e.g., test_database)")
    parser.add_argument("--test", "-t", type=str,
                       help="Run specific test function")
    parser.add_argument("--collect-only", action="store_true",
                       help="Only collect tests, don't run them")
    
    args = parser.parse_args()
    
    # Build pytest arguments
    pytest_args = []
    
    if args.verbose:
        pytest_args.extend(["-v", "-s"])
    
    if args.collect_only:
        pytest_args.append("--collect-only")
        
    # Configure environment based on test type
    if args.unit:
        print("🧪 Running unit tests only (fast, no API calls)")
        set_env_vars(skip_integration=True, skip_api_cost=True, skip_slow=True)
        pytest_args.extend(["-m", "unit or (not integration and not api_cost and not slow)"])
        
    elif args.integration:
        print("🔗 Running integration tests (expensive, with API calls)")
        set_env_vars(skip_integration=False, skip_api_cost=False, skip_slow=False)
        pytest_args.extend(["-m", "integration"])
        
    elif args.all:
        print("🚀 Running ALL tests (very expensive, all API calls)")
        set_env_vars(skip_integration=False, skip_api_cost=False, skip_slow=False)
        # No marker filter - run everything
        
    else:  # core (default)
        print("⚡ Running core tests (unit + some API tests, no integration)")
        set_env_vars(skip_integration=True, skip_api_cost=args.no_api, skip_slow=args.no_slow)
        pytest_args.extend(["-m", "not integration"])
    
    # Additional filters
    if args.no_api:
        pytest_args.extend(["-m", "not api_cost"])
    if args.no_slow:
        pytest_args.extend(["-m", "not slow"])
    
    # Specific module or test
    if args.module:
        pytest_args.append(f"tests/**/test_{args.module}.py")
    elif args.test:
        pytest_args.extend(["-k", args.test])
    
    # Show environment configuration
    print(f"Environment configuration:")
    print(f"  SKIP_INTEGRATION_TESTS: {os.environ.get('SKIP_INTEGRATION_TESTS')}")
    print(f"  SKIP_API_COST_TESTS: {os.environ.get('SKIP_API_COST_TESTS')}")
    print(f"  SKIP_SLOW_TESTS: {os.environ.get('SKIP_SLOW_TESTS')}")
    print()
    
    # Run tests
    return run_pytest(pytest_args)


if __name__ == "__main__":
    sys.exit(main()) 