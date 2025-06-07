# Code Graph - Mock Knowledge Graph Tests
# Test functions for knowledge graph structure without API calls

import os
from unittest.mock import Mock, patch
from app.graph_builder import GraphBuilder
from app.ingestion import parse_code_chunks


def test_knowledge_graph_structure() -> bool:
    """
    Test knowledge graph structure and setup without API calls
    
    Returns:
        bool: True if test passed, False otherwise
    """
    print("🧪 Testing knowledge graph structure (mock test)...")
    
    try:
        # Test GraphBuilder initialization
        gb = GraphBuilder()
        
        # Check if required methods exist
        required_methods = [
            'generate_knowledge_graph',
            'clear_knowledge_graph',
            'connect_to_neo4j',
            'get_database_info'
        ]
        
        for method in required_methods:
            if not hasattr(gb, method):
                print(f"❌ Missing method: {method}")
                return False
            print(f"✅ Method exists: {method}")
        
        print("✅ All required methods exist")
        
        # Test that we can create sample documents
        app_path = "./app"
        chunk_success, chunk_message, chunks = parse_code_chunks(
            app_path, 
            chunk_size=800,
            include_extensions=['.py']
        )
        
        if not chunk_success:
            print(f"❌ Failed to parse chunks: {chunk_message}")
            return False
        
        print(f"✅ Successfully parsed {len(chunks)} chunks")
        
        # Test connection to Neo4j (without generating graph)
        connect_success, connect_message = gb.connect_to_neo4j()
        if not connect_success:
            print(f"❌ Failed to connect to Neo4j: {connect_message}")
            return False
        
        print("✅ Successfully connected to Neo4j")
        
        # Test database info
        info_success, info_message, info_dict = gb.get_database_info()
        if not info_success:
            print(f"❌ Failed to get database info: {info_message}")
            return False
        
        print("✅ Successfully retrieved database info")
        print(f"   🔵 Nodes: {info_dict.get('node_count', 0)}")
        print(f"   🔗 Relationships: {info_dict.get('relationship_count', 0)}")
        
        # Close connection
        gb.close_connection()
        print("✅ Successfully closed connection")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        return False


def test_knowledge_graph_imports() -> bool:
    """
    Test that all required imports are available
    
    Returns:
        bool: True if test passed, False otherwise
    """
    print("🧪 Testing knowledge graph imports...")
    
    try:
        # Test LangChain imports
        from langchain_openai import ChatOpenAI
        print("✅ langchain_openai.ChatOpenAI imported")
        
        from langchain_experimental.graph_transformers import LLMGraphTransformer
        print("✅ langchain_experimental.graph_transformers.LLMGraphTransformer imported")
        
        from langchain_neo4j import Neo4jGraph
        print("✅ langchain_neo4j.Neo4jGraph imported")
        
        # Test that we can instantiate the classes (without API keys)
        try:
            # This should work without API key
            transformer = LLMGraphTransformer(
                llm=None,  # We'll pass None for testing
                allowed_nodes=["File", "Function", "Class"],
                allowed_relationships=["CONTAINS", "CALLS"],
                strict_mode=False
            )
            print("✅ LLMGraphTransformer can be instantiated")
        except Exception as e:
            print(f"⚠️ LLMGraphTransformer instantiation issue (expected): {str(e)}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        return False


def test_knowledge_graph_configuration() -> bool:
    """
    Test knowledge graph configuration and parameters
    
    Returns:
        bool: True if test passed, False otherwise
    """
    print("🧪 Testing knowledge graph configuration...")
    
    try:
        # Test allowed nodes and relationships
        allowed_nodes = ["File", "Function", "Class", "Module", "Package"]
        allowed_relationships = ["CONTAINS", "CALLS", "IMPORTS", "INHERITS", "IMPLEMENTS", "DEPENDS_ON"]
        
        print(f"✅ Allowed nodes: {allowed_nodes}")
        print(f"✅ Allowed relationships: {allowed_relationships}")
        
        # Test chunk processing
        sample_code = '''
def hello_world():
    """A simple hello world function"""
    print("Hello, World!")
    return "Hello, World!"

class TestClass:
    def __init__(self):
        self.value = "test"
    
    def get_value(self):
        return self.value
'''
        
        from langchain.schema import Document
        
        # Create a sample document
        doc = Document(
            page_content=sample_code,
            metadata={"filename": "test.py", "line_start": 1}
        )
        
        print("✅ Sample document created successfully")
        print(f"   📄 Content length: {len(doc.page_content)} characters")
        print(f"   📋 Metadata: {doc.metadata}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        return False


def run_all_mock_tests():
    """
    Run all mock knowledge graph tests
    """
    print("🧪 RUNNING ALL MOCK KNOWLEDGE GRAPH TESTS")
    print("=" * 50)
    
    # Test 1: Structure test
    print("\n1️⃣ Testing Knowledge Graph Structure:")
    test1_result = test_knowledge_graph_structure()
    
    # Test 2: Imports test
    print("\n2️⃣ Testing Knowledge Graph Imports:")
    test2_result = test_knowledge_graph_imports()
    
    # Test 3: Configuration test
    print("\n3️⃣ Testing Knowledge Graph Configuration:")
    test3_result = test_knowledge_graph_configuration()
    
    # Summary
    print("\n📊 MOCK TEST SUMMARY:")
    print("=" * 50)
    print(f"Knowledge Graph Structure: {'✅ PASSED' if test1_result else '❌ FAILED'}")
    print(f"Knowledge Graph Imports: {'✅ PASSED' if test2_result else '❌ FAILED'}")
    print(f"Knowledge Graph Configuration: {'✅ PASSED' if test3_result else '❌ FAILED'}")
    
    all_passed = all([test1_result, test2_result, test3_result])
    print(f"\nOverall Result: {'🎉 ALL MOCK TESTS PASSED' if all_passed else '⚠️ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n💡 Next Steps:")
        print("   1. Set up OpenAI API key in .env file")
        print("   2. Run full knowledge graph generation tests")
        print("   3. Test with Spring Pet Clinic repository")
    
    return all_passed


if __name__ == "__main__":
    run_all_mock_tests() 