# Code Graph - Knowledge Graph Generation Tests
# Test functions for knowledge graph creation and management

import os
from app.graph_builder import GraphBuilder
from app.ingestion import parse_code_chunks


def test_knowledge_graph_generation_small_sample() -> bool:
    """
    Test knowledge graph generation with a small code sample
    
    Returns:
        bool: True if test passed, False otherwise
    """
    print("🧪 Testing knowledge graph generation with small sample...")
    
    try:
        # Use our own app directory as a small test sample
        app_path = "./app"
        
        # Parse code chunks from app directory
        print("📝 Parsing code chunks...")
        chunk_success, chunk_message, chunks = parse_code_chunks(
            app_path, 
            chunk_size=800,  # Larger chunks for better context
            include_extensions=['.py']  # Only Python files for focused testing
        )
        
        if not chunk_success:
            print(f"❌ Failed to parse chunks: {chunk_message}")
            return False
        
        print(f"📄 Parsed {len(chunks)} chunks from app directory")
        
        # Use only first few chunks for testing to avoid high API costs
        test_chunks = chunks[:3]  # Test with first 3 chunks
        print(f"🔬 Testing with {len(test_chunks)} chunks")
        
        # Test knowledge graph generation
        with GraphBuilder() as gb:
            # Connect to Neo4j
            connect_success, connect_message = gb.connect_to_neo4j()
            if not connect_success:
                print(f"❌ Failed to connect to Neo4j: {connect_message}")
                return False
            
            print("✅ Connected to Neo4j")
            
            # Clear any existing data for clean test
            clear_success, clear_message = gb.clear_knowledge_graph(confirm=True)
            if clear_success:
                print("🧹 Cleared existing knowledge graph")
            
            # Generate knowledge graph
            print("🧠 Generating knowledge graph...")
            kg_success, kg_message = gb.generate_knowledge_graph(test_chunks)
            
            print(f"📊 Knowledge Graph Result: {'PASSED' if kg_success else 'FAILED'}")
            print(f"📝 Message: {kg_message}")
            
            return kg_success
            
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        return False


def test_knowledge_graph_with_spring_petclinic() -> bool:
    """
    Test knowledge graph generation with Spring Pet Clinic repository
    
    Returns:
        bool: True if test passed, False otherwise
    """
    print("🧪 Testing knowledge graph generation with Spring Pet Clinic...")
    
    try:
        # Check if Spring Pet Clinic is cloned
        petclinic_path = "./cloned_repos/spring-petclinic"
        if not os.path.exists(petclinic_path):
            print("❌ Spring Pet Clinic not found. Please clone it first.")
            return False
        
        # Parse code chunks from Spring Pet Clinic (Java files only)
        print("📝 Parsing Java code chunks from Spring Pet Clinic...")
        chunk_success, chunk_message, chunks = parse_code_chunks(
            petclinic_path,
            chunk_size=1000,  # Larger chunks for Java code
            include_extensions=['.java'],  # Only Java files
            exclude_patterns=['target', 'test']  # Exclude build and test directories
        )
        
        if not chunk_success:
            print(f"❌ Failed to parse chunks: {chunk_message}")
            return False
        
        print(f"📄 Parsed {len(chunks)} Java chunks")
        
        # Use only a subset for testing to manage API costs and time
        test_chunks = chunks[:5]  # Test with first 5 chunks
        print(f"🔬 Testing with {len(test_chunks)} chunks")
        
        # Show sample chunk info
        if test_chunks:
            sample_chunk = test_chunks[0]
            print(f"📋 Sample chunk from: {sample_chunk.metadata.get('filename', 'Unknown')}")
            print(f"📏 Sample chunk size: {len(sample_chunk.page_content)} characters")
        
        # Test knowledge graph generation
        with GraphBuilder() as gb:
            # Connect to Neo4j
            connect_success, connect_message = gb.connect_to_neo4j()
            if not connect_success:
                print(f"❌ Failed to connect to Neo4j: {connect_message}")
                return False
            
            print("✅ Connected to Neo4j")
            
            # Clear any existing data for clean test
            clear_success, clear_message = gb.clear_knowledge_graph(confirm=True)
            if clear_success:
                print("🧹 Cleared existing knowledge graph")
            
            # Generate knowledge graph
            print("🧠 Generating knowledge graph from Java code...")
            kg_success, kg_message = gb.generate_knowledge_graph(test_chunks)
            
            print(f"📊 Knowledge Graph Result: {'PASSED' if kg_success else 'FAILED'}")
            print(f"📝 Message: {kg_message}")
            
            return kg_success
            
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        return False


def test_knowledge_graph_statistics() -> bool:
    """
    Test knowledge graph statistics after generation
    
    Returns:
        bool: True if test passed, False otherwise
    """
    print("🧪 Testing knowledge graph statistics...")
    
    try:
        with GraphBuilder() as gb:
            # Connect to Neo4j
            connect_success, connect_message = gb.connect_to_neo4j()
            if not connect_success:
                print(f"❌ Failed to connect to Neo4j: {connect_message}")
                return False
            
            # Get database statistics
            stats_success, stats_message, stats_dict = gb.get_database_info()
            
            print(f"📊 Statistics Result: {'PASSED' if stats_success else 'FAILED'}")
            print(f"📝 Message: {stats_message}")
            
            if stats_success and stats_dict:
                print(f"\n📈 Knowledge Graph Statistics:")
                print(f"   🔵 Total Nodes: {stats_dict.get('node_count', 0)}")
                print(f"   🔗 Total Relationships: {stats_dict.get('relationship_count', 0)}")
                
                # Check if we have any nodes/relationships
                has_data = stats_dict.get('node_count', 0) > 0 or stats_dict.get('relationship_count', 0) > 0
                if has_data:
                    print("✅ Knowledge graph contains data")
                else:
                    print("⚠️ Knowledge graph appears to be empty")
                
                return stats_success
            
            return stats_success
            
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        return False


def test_knowledge_graph_clear() -> bool:
    """
    Test knowledge graph clearing functionality
    
    Returns:
        bool: True if test passed, False otherwise
    """
    print("🧪 Testing knowledge graph clearing...")
    
    try:
        with GraphBuilder() as gb:
            # Connect to Neo4j
            connect_success, connect_message = gb.connect_to_neo4j()
            if not connect_success:
                print(f"❌ Failed to connect to Neo4j: {connect_message}")
                return False
            
            # Test clearing without confirmation (should fail)
            clear_success, clear_message = gb.clear_knowledge_graph(confirm=False)
            if clear_success:
                print("❌ Clear should have failed without confirmation")
                return False
            
            print("✅ Clear correctly requires confirmation")
            
            # Test clearing with confirmation
            clear_success, clear_message = gb.clear_knowledge_graph(confirm=True)
            
            print(f"📊 Clear Result: {'PASSED' if clear_success else 'FAILED'}")
            print(f"📝 Message: {clear_message}")
            
            return clear_success
            
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        return False


def run_all_knowledge_graph_tests():
    """
    Run all knowledge graph tests
    """
    print("🧪 RUNNING ALL KNOWLEDGE GRAPH TESTS")
    print("=" * 50)
    
    # Test 1: Small sample generation
    print("\n1️⃣ Testing Small Sample Generation:")
    test1_result = test_knowledge_graph_generation_small_sample()
    
    # Test 2: Spring Pet Clinic generation
    print("\n2️⃣ Testing Spring Pet Clinic Generation:")
    test2_result = test_knowledge_graph_with_spring_petclinic()
    
    # Test 3: Statistics
    print("\n3️⃣ Testing Knowledge Graph Statistics:")
    test3_result = test_knowledge_graph_statistics()
    
    # Test 4: Clear functionality
    print("\n4️⃣ Testing Knowledge Graph Clear:")
    test4_result = test_knowledge_graph_clear()
    
    # Summary
    print("\n📊 KNOWLEDGE GRAPH TEST SUMMARY:")
    print("=" * 50)
    print(f"Small Sample Generation: {'✅ PASSED' if test1_result else '❌ FAILED'}")
    print(f"Spring Pet Clinic Generation: {'✅ PASSED' if test2_result else '❌ FAILED'}")
    print(f"Knowledge Graph Statistics: {'✅ PASSED' if test3_result else '❌ FAILED'}")
    print(f"Knowledge Graph Clear: {'✅ PASSED' if test4_result else '❌ FAILED'}")
    
    all_passed = all([test1_result, test2_result, test3_result, test4_result])
    print(f"\nOverall Result: {'🎉 ALL TESTS PASSED' if all_passed else '⚠️ SOME TESTS FAILED'}")
    
    return all_passed


if __name__ == "__main__":
    run_all_knowledge_graph_tests() 