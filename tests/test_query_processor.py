#!/usr/bin/env python3
"""
Query Processor Tests for Code Graph
Tests the hybrid GraphRAG query processing functionality
"""

import sys
import argparse
import tempfile
import shutil
from pathlib import Path

# Add the parent directory to the path so we can import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.graph_builder import GraphBuilder
from app.query_processor import QueryProcessor
from app.ingestion import clone_repository, parse_code_chunks


class QueryProcessorTester:
    """Professional tester for GraphRAG query processing"""
    
    def __init__(self, cost_mode: str = "limited"):
        """
        Initialize the tester with cost control settings
        
        Args:
            cost_mode: "limited" for cost-controlled testing, "full" for comprehensive testing
        """
        self.cost_mode = cost_mode
        self.temp_dirs = []
        
        # Cost control settings
        if cost_mode == "limited":
            self.max_chunks = 15
            self.allowed_languages = ['.java']
            self.estimated_cost = "$0.003-0.008"
        else:  # full mode
            self.max_chunks = 50
            self.allowed_languages = ['.java', '.py']
            self.estimated_cost = "$0.01-0.05"
    
    def cleanup(self):
        """Clean up temporary directories"""
        for temp_dir in self.temp_dirs:
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)
                print(f"🧹 Cleaned up temporary directory: {temp_dir}")
    
    def setup_test_data(self) -> tuple:
        """
        Set up test data by creating a unified GraphRAG system
        
        Returns:
            tuple: (success, message, chunks_count)
        """
        try:
            print("📥 Setting up test data...")
            
            # Clone a small, well-structured repository
            repo_url = "https://github.com/iluwatar/java-design-patterns.git"
            temp_dir = tempfile.mkdtemp(prefix="query_test_")
            self.temp_dirs.append(temp_dir)
            
            clone_success, clone_message, repo_path = clone_repository(
                repo_url,
                target_dir=temp_dir,
                use_project_dir=False
            )
            
            if not clone_success:
                return False, f"Repository cloning failed: {clone_message}", 0
            
            # Focus on specific design patterns for rich examples
            pattern_path = Path(repo_path) / "adapter"
            if not pattern_path.exists():
                # Fallback to parsing the entire repo with limits
                parse_path = repo_path
            else:
                parse_path = str(pattern_path)
            
            # Parse code chunks
            chunk_success, chunk_message, chunks = parse_code_chunks(
                parse_path,
                chunk_size=1000,  # Larger chunks for better context
                include_extensions=self.allowed_languages,
                exclude_patterns=['target', 'test', '.git', 'README']
            )
            
            if not chunk_success or not chunks:
                return False, f"Code parsing failed: {chunk_message}", 0
            
            # Apply cost controls
            if self.max_chunks and len(chunks) > self.max_chunks:
                chunks = chunks[:self.max_chunks]
            
            print(f"📄 Using {len(chunks)} chunks for testing")
            
            # Create unified GraphRAG system
            with GraphBuilder() as gb:
                connect_success, connect_message = gb.connect_to_neo4j()
                if not connect_success:
                    return False, f"Neo4j connection failed: {connect_message}", 0
                
                # Clear database for clean test
                gb.clear_knowledge_graph(confirm=True)
                
                # Create unified system
                unified_success, unified_message = gb.create_unified_graphrag_system(chunks)
                if not unified_success:
                    return False, f"Unified GraphRAG creation failed: {unified_message}", 0
            
            return True, f"Test data setup successful with {len(chunks)} chunks", len(chunks)
            
        except Exception as e:
            return False, f"Setup failed with error: {str(e)}", 0
    
    def test_query_processor_initialization(self) -> bool:
        """
        Test query processor initialization and setup
        
        Returns:
            bool: True if test passes, False otherwise
        """
        print("\n🔧 TESTING QUERY PROCESSOR INITIALIZATION")
        print("=" * 50)
        
        try:
            with QueryProcessor() as qp:
                # Test connection
                connect_success, connect_message = qp.connect_to_neo4j()
                if not connect_success:
                    print(f"❌ Connection failed: {connect_message}")
                    return False
                
                print("✅ Neo4j connection successful")
                
                # Test retriever setup
                setup_success, setup_message = qp.setup_retrievers()
                if not setup_success:
                    print(f"❌ Retriever setup failed: {setup_message}")
                    return False
                
                print("✅ Retrievers setup successful")
                print(setup_message)
                
                return True
                
        except Exception as e:
            print(f"❌ Initialization test failed: {str(e)}")
            return False
    
    def test_vector_search_only(self) -> bool:
        """
        Test vector search functionality in isolation
        
        Returns:
            bool: True if test passes, False otherwise
        """
        print("\n🔍 TESTING VECTOR SEARCH FUNCTIONALITY")
        print("=" * 45)
        
        try:
            with QueryProcessor() as qp:
                # Initialize
                qp.connect_to_neo4j()
                qp.setup_retrievers()
                
                # Test queries
                test_queries = [
                    "adapter pattern implementation",
                    "class definition",
                    "method implementation"
                ]
                
                for i, query in enumerate(test_queries, 1):
                    print(f"\n🔎 Vector Search {i}: '{query}'")
                    
                    search_success, results = qp.vector_search(query, k=3)
                    
                    if not search_success:
                        print(f"❌ Vector search failed")
                        return False
                    
                    if results:
                        print(f"✅ Found {len(results)} results")
                        top_result = results[0]
                        print(f"   📄 Top result: {top_result['file_path']}")
                        print(f"   📊 Similarity: {top_result['similarity_score']:.3f}")
                        print(f"   🔤 Language: {top_result['language']}")
                    else:
                        print("⚠️ No results found")
                
                return True
                
        except Exception as e:
            print(f"❌ Vector search test failed: {str(e)}")
            return False
    
    def test_graph_context_extraction(self) -> bool:
        """
        Test graph context extraction for vector results
        
        Returns:
            bool: True if test passes, False otherwise
        """
        print("\n🌉 TESTING GRAPH CONTEXT EXTRACTION")
        print("=" * 40)
        
        try:
            with QueryProcessor() as qp:
                # Initialize
                qp.connect_to_neo4j()
                qp.setup_retrievers()
                
                # Get some vector results first
                search_success, vector_results = qp.vector_search("adapter pattern", k=3)
                
                if not search_success or not vector_results:
                    print("❌ No vector results to test graph context")
                    return False
                
                print(f"📄 Using {len(vector_results)} vector results for context extraction")
                
                # Extract graph context
                context_success, graph_context = qp.get_graph_context_for_chunks(vector_results)
                
                if not context_success:
                    print("❌ Graph context extraction failed")
                    return False
                
                print("✅ Graph context extraction successful")
                
                # Analyze context
                entities = graph_context.get('entities', [])
                relationships = graph_context.get('relationships', [])
                files = graph_context.get('files', [])
                
                print(f"   🏷️ Entities found: {len(entities)}")
                if entities:
                    entity_types = {}
                    for entity in entities:
                        entity_type = entity['type']
                        entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
                    
                    for entity_type, count in entity_types.items():
                        print(f"      {entity_type}: {count}")
                
                print(f"   🔗 Relationships found: {len(relationships)}")
                if relationships:
                    rel_types = {}
                    for rel in relationships:
                        rel_type = rel['relationship']
                        rel_types[rel_type] = rel_types.get(rel_type, 0) + 1
                    
                    for rel_type, count in rel_types.items():
                        print(f"      {rel_type}: {count}")
                
                print(f"   📁 Files involved: {len(files)}")
                for file_info in files[:3]:  # Show top 3
                    print(f"      {file_info['name']} ({file_info['language']}) - {file_info['entity_count']} entities")
                
                return True
                
        except Exception as e:
            print(f"❌ Graph context test failed: {str(e)}")
            return False
    
    def test_hybrid_query_processing(self) -> bool:
        """
        Test full hybrid query processing (vector + graph)
        
        Returns:
            bool: True if test passes, False otherwise
        """
        print("\n🚀 TESTING HYBRID QUERY PROCESSING")
        print("=" * 40)
        
        try:
            with QueryProcessor() as qp:
                # Initialize
                qp.connect_to_neo4j()
                qp.setup_retrievers()
                
                # Test different types of queries
                test_queries = [
                    {
                        "query": "How is the adapter pattern implemented?",
                        "description": "Pattern implementation query"
                    },
                    {
                        "query": "Show me class inheritance relationships",
                        "description": "Structural relationship query"
                    },
                    {
                        "query": "Find factory method examples",
                        "description": "Specific pattern query"
                    }
                ]
                
                all_passed = True
                
                for i, test_case in enumerate(test_queries, 1):
                    query = test_case["query"]
                    description = test_case["description"]
                    
                    print(f"\n🔍 Hybrid Query {i}: {description}")
                    print(f"   Query: '{query}'")
                    
                    # Process query with graph context
                    process_success, response, context_data = qp.process_query(
                        query, 
                        k=5, 
                        include_graph_context=True
                    )
                    
                    if not process_success:
                        print(f"❌ Query processing failed: {response}")
                        all_passed = False
                        continue
                    
                    print("✅ Query processed successfully")
                    
                    # Analyze results
                    num_chunks = context_data.get('num_chunks_found', 0)
                    num_entities = context_data.get('num_entities_found', 0)
                    num_relationships = context_data.get('num_relationships_found', 0)
                    
                    print(f"   📄 Code chunks found: {num_chunks}")
                    print(f"   🏷️ Entities found: {num_entities}")
                    print(f"   🔗 Relationships found: {num_relationships}")
                    
                    # Show full response
                    print(f"   📝 Full Response:")
                    print("   " + "="*50)
                    # Indent each line of the response
                    for line in response.split('\n'):
                        print(f"   {line}")
                    print("   " + "="*50)
                    
                    # Test without graph context for comparison
                    process_success_no_graph, response_no_graph, context_data_no_graph = qp.process_query(
                        query,
                        k=5,
                        include_graph_context=False
                    )
                    
                    if process_success_no_graph:
                        print(f"   🔍 Vector-only mode also successful")
                    
                return all_passed
                
        except Exception as e:
            print(f"❌ Hybrid query test failed: {str(e)}")
            return False
    
    def test_edge_cases(self) -> bool:
        """
        Test edge cases and error handling
        
        Returns:
            bool: True if test passes, False otherwise
        """
        print("\n⚠️ TESTING EDGE CASES")
        print("=" * 25)
        
        try:
            with QueryProcessor() as qp:
                qp.connect_to_neo4j()
                qp.setup_retrievers()
                
                # Test empty query
                print("\n🔍 Testing empty query...")
                process_success, response, context_data = qp.process_query("", k=3)
                print(f"   Empty query result: {'✅' if process_success else '❌'}")
                
                # Test very specific query that might not match
                print("\n🔍 Testing very specific query...")
                process_success, response, context_data = qp.process_query(
                    "quantum entanglement implementation in blockchain", k=3
                )
                print(f"   Specific query result: {'✅' if process_success else '❌'}")
                if process_success:
                    chunks_found = context_data.get('num_chunks_found', 0)
                    print(f"   Chunks found: {chunks_found}")
                
                # Test large k value
                print("\n🔍 Testing large k value...")
                process_success, response, context_data = qp.process_query(
                    "class definition", k=100
                )
                print(f"   Large k result: {'✅' if process_success else '❌'}")
                
                return True
                
        except Exception as e:
            print(f"❌ Edge cases test failed: {str(e)}")
            return False
    
    def run_comprehensive_test(self) -> bool:
        """
        Run comprehensive query processor test suite
        
        Returns:
            bool: True if all tests pass, False otherwise
        """
        print("🚀 QUERY PROCESSOR COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        print(f"💰 Cost mode: {self.cost_mode} (estimated: {self.estimated_cost})")
        
        try:
            # Step 1: Setup test data
            setup_success, setup_message, chunks_count = self.setup_test_data()
            if not setup_success:
                print(f"❌ Test data setup failed: {setup_message}")
                return False
            
            print(f"✅ Test data setup successful: {setup_message}")
            
            # Step 2: Test initialization
            if not self.test_query_processor_initialization():
                print("❌ Initialization test failed")
                return False
            
            # Step 3: Test vector search
            if not self.test_vector_search_only():
                print("❌ Vector search test failed")
                return False
            
            # Step 4: Test graph context extraction
            if not self.test_graph_context_extraction():
                print("❌ Graph context test failed")
                return False
            
            # Step 5: Test hybrid query processing
            if not self.test_hybrid_query_processing():
                print("❌ Hybrid query test failed")
                return False
            
            # Step 6: Test edge cases
            if not self.test_edge_cases():
                print("❌ Edge cases test failed")
                return False
            
            print(f"\n🎉 ALL QUERY PROCESSOR TESTS PASSED!")
            print(f"📊 Processed {chunks_count} code chunks successfully")
            print(f"💡 The hybrid GraphRAG system is working correctly!")
            
            return True
            
        except Exception as e:
            print(f"❌ Comprehensive test failed: {str(e)}")
            return False
        
        finally:
            self.cleanup()


def main():
    """Main function with command-line argument parsing"""
    parser = argparse.ArgumentParser(description="Test GraphRAG query processor")
    parser.add_argument("--full", action="store_true", help="Run full test mode (higher cost)")
    
    args = parser.parse_args()
    
    # Determine cost mode
    cost_mode = "full" if args.full else "limited"
    
    # Create tester
    tester = QueryProcessorTester(cost_mode=cost_mode)
    
    try:
        success = tester.run_comprehensive_test()
        
        if success:
            print(f"\n🎉 ALL TESTS PASSED!")
            return 0
        else:
            print(f"\n💥 TESTS FAILED!")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        return 1
    finally:
        tester.cleanup()


if __name__ == "__main__":
    exit(main()) 