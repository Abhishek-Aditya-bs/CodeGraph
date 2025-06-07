#!/usr/bin/env python3
# Code Graph - Test Runner
# Simple script to run all tests

import sys
from pathlib import Path

# Add the parent directory to the path so we can import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_ingestion import run_all_tests

if __name__ == "__main__":
    print("🚀 Code Graph Test Runner")
    print("=" * 50)
    
    success = run_all_tests()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1) 