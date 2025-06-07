#!/usr/bin/env python3
# Code Graph - Test Runner
# Comprehensive script to run all tests

import sys
from pathlib import Path

# Add the parent directory to the path so we can import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_all_tests():
    """
    Run all available tests
    
    Returns:
        bool: True if all tests passed, False otherwise
    """
    print("🚀 CODE GRAPH COMPREHENSIVE TEST RUNNER")
    print("=" * 60)
    
    # Run ingestion tests
    print("\n📝 RUNNING INGESTION TESTS")
    print("=" * 60)
    from tests.test_ingestion import run_all_tests as run_ingestion_tests
    ingestion_result = run_ingestion_tests()
    
    # Run Neo4j tests
    print("\n🔗 RUNNING NEO4J TESTS")
    print("=" * 60)
    from tests.test_neo4j import run_all_neo4j_tests
    neo4j_result = run_all_neo4j_tests()
    
    # Run Knowledge Graph mock tests (always safe to run)
    print("\n🧠 RUNNING KNOWLEDGE GRAPH MOCK TESTS")
    print("=" * 60)
    from tests.test_knowledge_graph_mock import run_all_mock_tests
    mock_result = run_all_mock_tests()
    
    # Summary
    print("\n📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 60)
    print(f"📝 Ingestion Tests: {'✅ PASSED' if ingestion_result else '❌ FAILED'}")
    print(f"🔗 Neo4j Tests: {'✅ PASSED' if neo4j_result else '❌ FAILED'}")
    print(f"🧠 Knowledge Graph Mock Tests: {'✅ PASSED' if mock_result else '❌ FAILED'}")
    
    all_passed = ingestion_result and neo4j_result and mock_result
    print(f"\nFinal Result: {'🎉 ALL TESTS PASSED' if all_passed else '⚠️ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n💡 Next Steps:")
        print("   1. Set up OpenAI API key in .env file")
        print("   2. Run full knowledge graph generation tests:")
        print("      python -m tests.test_knowledge_graph")
        print("   3. Test with actual repositories")
        print("\n🔧 Task 3.2 Implementation Status:")
        print("   ✅ Knowledge graph generation structure implemented")
        print("   ✅ LangChain LLMGraphTransformer integration")
        print("   ✅ GPT-4o-mini model configuration")
        print("   ✅ Neo4j graph storage setup")
        print("   ✅ Comprehensive error handling")
        print("   ⏳ Waiting for OpenAI API key for full testing")
    
    return all_passed

if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1) 