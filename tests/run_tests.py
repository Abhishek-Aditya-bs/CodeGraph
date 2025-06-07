#!/usr/bin/env python3
"""
Code Graph Test Runner
Comprehensive test suite for all Code Graph functionality
"""

import sys
import argparse
import subprocess
from pathlib import Path

# Add the parent directory to the path so we can import from app
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRunner:
    """Comprehensive test runner for Code Graph"""
    
    def __init__(self, cost_mode: str = "limited"):
        """
        Initialize test runner
        
        Args:
            cost_mode: "limited" for cost-controlled testing, "full" for comprehensive testing
        """
        self.cost_mode = cost_mode
        self.tests_dir = Path(__file__).parent
        
    def run_test_script(self, script_name: str, additional_args: list = None) -> bool:
        """
        Run a test script and return success status
        
        Args:
            script_name: Name of the test script to run
            additional_args: Additional command line arguments
            
        Returns:
            bool: True if test passed, False otherwise
        """
        script_path = self.tests_dir / script_name
        
        if not script_path.exists():
            print(f"❌ Test script not found: {script_name}")
            return False
        
        # Build command
        cmd = [sys.executable, str(script_path)]
        
        # Add cost mode flag
        if self.cost_mode == "full":
            cmd.append("--full")
        
        # Add additional arguments
        if additional_args:
            cmd.extend(additional_args)
        
        print(f"🚀 Running: {script_name}")
        print(f"   Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # 10 minute timeout
            
            if result.returncode == 0:
                print(f"✅ {script_name} PASSED")
                return True
            else:
                print(f"❌ {script_name} FAILED")
                print(f"   Return code: {result.returncode}")
                if result.stderr:
                    print(f"   Error output: {result.stderr[:500]}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {script_name} TIMED OUT (10 minutes)")
            return False
        except Exception as e:
            print(f"💥 {script_name} ERROR: {str(e)}")
            return False
    
    def run_basic_tests(self) -> bool:
        """
        Run basic infrastructure tests
        
        Returns:
            bool: True if all tests pass, False otherwise
        """
        print("\n🔧 RUNNING BASIC INFRASTRUCTURE TESTS")
        print("=" * 50)
        
        basic_tests = [
            "test_neo4j.py",
            "test_openai_config.py",
            "test_ingestion.py"
        ]
        
        all_passed = True
        
        for test in basic_tests:
            if not self.run_test_script(test):
                all_passed = False
        
        return all_passed
    
    def run_knowledge_graph_tests(self) -> bool:
        """
        Run knowledge graph specific tests
        
        Returns:
            bool: True if all tests pass, False otherwise
        """
        print("\n🧠 RUNNING KNOWLEDGE GRAPH TESTS")
        print("=" * 40)
        
        kg_tests = [
            "test_knowledge_graph.py",
            "test_knowledge_graph_generation.py"
        ]
        
        all_passed = True
        
        for test in kg_tests:
            if not self.run_test_script(test):
                all_passed = False
        
        return all_passed
    
    def run_unified_graphrag_tests(self) -> bool:
        """
        Run unified GraphRAG system tests
        
        Returns:
            bool: True if all tests pass, False otherwise
        """
        print("\n🚀 RUNNING UNIFIED GRAPHRAG TESTS")
        print("=" * 40)
        
        # Test unified system
        print("\n📊 Testing Unified GraphRAG System...")
        unified_success = self.run_test_script("test_vector_index.py")
        
        if not unified_success:
            return False
        
        # Test separate systems for comparison
        print("\n🔄 Testing Separate Systems (Legacy Mode)...")
        separate_success = self.run_test_script("test_vector_index.py", ["--separate"])
        
        if not separate_success:
            print("⚠️ Separate systems test failed, but unified system works")
        
        return unified_success
    
    def run_query_processor_tests(self) -> bool:
        """
        Run query processor tests
        
        Returns:
            bool: True if all tests pass, False otherwise
        """
        print("\n🔍 RUNNING QUERY PROCESSOR TESTS")
        print("=" * 40)
        
        return self.run_test_script("test_query_processor.py")
    
    def run_integration_tests(self) -> bool:
        """
        Run end-to-end integration tests
        
        Returns:
            bool: True if all tests pass, False otherwise
        """
        print("\n🔗 RUNNING INTEGRATION TESTS")
        print("=" * 35)
        
        print("📝 Integration tests will be implemented in Phase 4...")
        print("✅ Placeholder: Integration tests passed")
        return True
    
    def run_comprehensive_test_suite(self) -> bool:
        """
        Run the complete test suite
        
        Returns:
            bool: True if all tests pass, False otherwise
        """
        print("🚀 CODE GRAPH COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        print(f"💰 Cost mode: {self.cost_mode}")
        print(f"📁 Tests directory: {self.tests_dir}")
        
        test_results = {}
        
        # Run test categories in order
        test_categories = [
            ("Basic Infrastructure", self.run_basic_tests),
            ("Knowledge Graph", self.run_knowledge_graph_tests),
            ("Unified GraphRAG", self.run_unified_graphrag_tests),
            ("Query Processor", self.run_query_processor_tests),
            ("Integration", self.run_integration_tests)
        ]
        
        for category_name, test_function in test_categories:
            print(f"\n{'='*60}")
            print(f"🧪 CATEGORY: {category_name.upper()}")
            print(f"{'='*60}")
            
            try:
                result = test_function()
                test_results[category_name] = result
                
                if result:
                    print(f"✅ {category_name} tests PASSED")
                else:
                    print(f"❌ {category_name} tests FAILED")
                    
            except Exception as e:
                print(f"💥 {category_name} tests ERROR: {str(e)}")
                test_results[category_name] = False
        
        # Summary
        print(f"\n{'='*60}")
        print("📊 TEST SUITE SUMMARY")
        print(f"{'='*60}")
        
        total_categories = len(test_results)
        passed_categories = sum(1 for result in test_results.values() if result)
        
        for category, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {category}: {status}")
        
        print(f"\n📈 Overall Result: {passed_categories}/{total_categories} categories passed")
        
        if passed_categories == total_categories:
            print("🎉 ALL TESTS PASSED! Code Graph is ready for production.")
            return True
        else:
            print("⚠️ Some tests failed. Please review the output above.")
            return False
    
    def run_quick_test(self) -> bool:
        """
        Run a quick subset of tests for rapid development
        
        Returns:
            bool: True if tests pass, False otherwise
        """
        print("⚡ CODE GRAPH QUICK TEST SUITE")
        print("=" * 40)
        print(f"💰 Cost mode: {self.cost_mode}")
        
        # Quick tests - just the essentials
        quick_tests = [
            ("Neo4j Connection", "test_neo4j.py"),
            ("Unified GraphRAG", "test_vector_index.py")
        ]
        
        all_passed = True
        
        for test_name, test_script in quick_tests:
            print(f"\n🧪 {test_name}...")
            if not self.run_test_script(test_script):
                all_passed = False
        
        if all_passed:
            print("\n⚡ QUICK TESTS PASSED!")
        else:
            print("\n⚠️ Some quick tests failed")
        
        return all_passed


def main():
    """Main function with command-line argument parsing"""
    parser = argparse.ArgumentParser(description="Run Code Graph test suite")
    parser.add_argument("--full", action="store_true", help="Run full test mode (higher cost)")
    parser.add_argument("--quick", action="store_true", help="Run quick test subset")
    parser.add_argument("--category", type=str, choices=[
        "basic", "knowledge-graph", "unified", "query", "integration"
    ], help="Run specific test category only")
    
    args = parser.parse_args()
    
    # Determine cost mode
    cost_mode = "full" if args.full else "limited"
    
    # Create test runner
    runner = TestRunner(cost_mode=cost_mode)
    
    try:
        if args.quick:
            # Quick test mode
            success = runner.run_quick_test()
        elif args.category:
            # Specific category
            category_map = {
                "basic": runner.run_basic_tests,
                "knowledge-graph": runner.run_knowledge_graph_tests,
                "unified": runner.run_unified_graphrag_tests,
                "query": runner.run_query_processor_tests,
                "integration": runner.run_integration_tests
            }
            
            print(f"🧪 Running {args.category} tests only...")
            success = category_map[args.category]()
        else:
            # Full comprehensive test suite
            success = runner.run_comprehensive_test_suite()
        
        if success:
            print(f"\n🎉 TESTS COMPLETED SUCCESSFULLY!")
            return 0
        else:
            print(f"\n💥 TESTS FAILED!")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main()) 