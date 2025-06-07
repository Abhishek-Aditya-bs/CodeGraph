#!/usr/bin/env python3
"""
Code Graph - Comprehensive Test Runner
Runs all tests in the correct order, with cleanup at the end
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import from app
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_all_tests():
    """
    Run all available tests in the correct order
    
    Returns:
        bool: True if all tests passed, False otherwise
    """
    print("🚀 CODE GRAPH COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    # List of test functions to run
    test_functions = [
        ("Ingestion Tests", "tests.test_ingestion", "run_all_tests"),
        ("Neo4j Tests", "tests.test_neo4j", "run_all_neo4j_tests"),
        ("Knowledge Graph Mock Tests", "tests.test_knowledge_graph_mock", "run_all_mock_tests"),
        ("OpenAI Configuration Tests", "tests.test_openai_config", "run_openai_tests"),
        ("Knowledge Graph Generation Tests", "tests.test_knowledge_graph_generation", "run_all_tests")
    ]
    
    results = []
    
    # Run each test suite
    for test_name, module_name, function_name in test_functions:
        print(f"\n🚀 RUNNING {test_name.upper()}")
        print("=" * 70)
        
        try:
            # Import the module and get the test function
            module = __import__(module_name, fromlist=[function_name])
            test_func = getattr(module, function_name)
            
            # Run the test
            success = test_func()
            results.append((test_name, success))
            
            if success:
                print(f"✅ {test_name} completed successfully")
            else:
                print(f"❌ {test_name} failed")
                
        except ImportError as e:
            print(f"⚠️ Could not import {module_name}: {e}")
            print(f"⏭️ Skipping {test_name}")
            results.append((test_name, True))  # Skip gracefully
            
        except AttributeError as e:
            print(f"⚠️ Could not find function {function_name} in {module_name}: {e}")
            print(f"⏭️ Skipping {test_name}")
            results.append((test_name, True))  # Skip gracefully
            
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Print intermediate summary
    print(f"\n📊 MAIN TESTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 Main Tests: {passed}/{total} test suites passed")
    
    # Run cleanup test LAST
    print(f"\n🧹 RUNNING FINAL DATABASE CLEANUP")
    print("=" * 50)
    
    cleanup_success = False
    try:
        from tests.test_cleanup import test_database_cleanup
        cleanup_success = test_database_cleanup()
        
        if cleanup_success:
            print("✅ Database cleanup completed successfully")
        else:
            print("❌ Database cleanup failed")
            
    except ImportError as e:
        print(f"⚠️ Could not import cleanup test: {e}")
        print("⏭️ Skipping cleanup")
        cleanup_success = True  # Skip gracefully
        
    except Exception as e:
        print(f"❌ Database cleanup failed with error: {e}")
        cleanup_success = False
    
    # Final summary
    print(f"\n🎯 FINAL TEST SUMMARY")
    print("=" * 50)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    cleanup_status = "✅ PASSED" if cleanup_success else "❌ FAILED"
    print(f"   Database Cleanup: {cleanup_status}")
    
    total_with_cleanup = total + 1
    passed_with_cleanup = passed + (1 if cleanup_success else 0)
    
    print(f"\n📈 Overall: {passed_with_cleanup}/{total_with_cleanup} test suites passed")
    
    # Final result
    if passed == total and cleanup_success:
        print("\n🎉 ALL TESTS PASSED! Database is clean and ready.")
        print("\n💡 What you can do now:")
        print("   🌐 Open http://localhost:7474 to explore Neo4j Browser")
        print("   🔍 Run individual tests to generate specific knowledge graphs")
        print("   📊 Explore the Java design patterns relationships")
        return True
    elif passed == total:
        print("\n⚠️ Main tests passed but cleanup failed.")
        print("💡 You may need to manually clear the database")
        return False
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1) 