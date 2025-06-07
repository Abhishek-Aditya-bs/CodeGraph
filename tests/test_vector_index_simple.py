#!/usr/bin/env python3
"""
Simple Vector Index Test - Minimal API Usage
Tests vector index creation with very limited files to minimize costs
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.graph_builder import GraphBuilder
import time


def test_simple_vector_index():
    """Test vector index with minimal data to minimize API costs"""
    print("🧪 Simple Vector Index Test (Minimal API Usage)")
    print("=" * 50)
    
    graph_builder = GraphBuilder()
    
    try:
        # Connect to Neo4j
        print("🔗 Connecting to Neo4j...")
        success, message = graph_builder.connect_to_neo4j()
        if not success:
            print(f"❌ Neo4j connection failed: {message}")
            return False
        print("✅ Connected to Neo4j")
        
        # Create minimal test documents (no API calls for parsing)
        print("📄 Creating minimal test documents...")
        from langchain.schema import Document
        
        # Create 2 simple test documents to minimize API costs
        test_documents = [
            Document(
                page_content="""
public class FishingBoatAdapter implements RowingBoat {
    private FishingBoat boat;
    
    public FishingBoatAdapter() {
        boat = new FishingBoat();
    }
    
    @Override
    public void row() {
        boat.sail();
    }
}
                """.strip(),
                metadata={
                    'file_path': 'test/FishingBoatAdapter.java',
                    'chunk_id': 'chunk_1',
                    'language': 'java',
                    'start_line': 1,
                    'end_line': 15
                }
            ),
            Document(
                page_content="""
public interface RowingBoat {
    void row();
}

public class FishingBoat {
    public void sail() {
        System.out.println("The fishing boat is sailing");
    }
}
                """.strip(),
                metadata={
                    'file_path': 'test/RowingBoat.java',
                    'chunk_id': 'chunk_2', 
                    'language': 'java',
                    'start_line': 1,
                    'end_line': 10
                }
            )
        ]
        
        print(f"✅ Created {len(test_documents)} test documents")
        
        # Create vector index (this will use API calls for embeddings)
        print("🔍 Creating vector index with embeddings...")
        print("⚠️ This will make API calls to OpenAI for embeddings...")
        
        start_time = time.time()
        vector_success, vector_message = graph_builder.create_vector_index(test_documents)
        embedding_time = time.time() - start_time
        
        if not vector_success:
            print(f"❌ Vector index creation failed: {vector_message}")
            return False
        
        print(f"✅ Vector index created successfully!")
        print(f"⏱️ Total time: {embedding_time:.2f} seconds")
        print(f"📊 Details: {vector_message}")
        
        # Test vector search
        print("\n🔍 Testing Vector Search...")
        test_queries = [
            "adapter pattern",
            "interface implementation"
        ]
        
        for query in test_queries:
            print(f"\n🔎 Searching for: '{query}'")
            
            search_success, search_message, results = graph_builder.test_vector_search(
                query=query,
                k=2
            )
            
            if search_success:
                print(f"✅ {search_message}")
                for i, result in enumerate(results, 1):
                    print(f"  📄 Result {i}: Score {result['score']:.4f}")
                    print(f"    📝 Content: {result['content'][:80]}...")
            else:
                print(f"❌ Search failed: {search_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in simple vector index test: {str(e)}")
        return False
    
    finally:
        graph_builder.close_connection()


def check_database_contents():
    """Check what's currently in the database"""
    print("\n📊 Checking Database Contents...")
    print("=" * 40)
    
    graph_builder = GraphBuilder()
    
    try:
        success, message = graph_builder.connect_to_neo4j()
        if not success:
            print(f"❌ Connection failed: {message}")
            return
        
        with graph_builder.driver.session() as session:
            # Check existing knowledge graph nodes
            kg_result = session.run("""
                MATCH (n)
                WHERE NOT n:CodeChunk AND NOT n:File
                RETURN labels(n) as node_labels, count(n) as count
                ORDER BY count DESC
            """)
            
            print("🔵 Knowledge Graph Nodes:")
            kg_nodes = list(kg_result)
            if kg_nodes:
                for record in kg_nodes:
                    print(f"  {record['node_labels']}: {record['count']}")
            else:
                print("  No knowledge graph nodes found")
            
            # Check vector index nodes
            vector_result = session.run("""
                MATCH (c:CodeChunk)
                RETURN count(c) as chunk_count
            """)
            vector_record = vector_result.single()
            chunk_count = vector_record['chunk_count'] if vector_record else 0
            
            file_result = session.run("""
                MATCH (f:File)
                RETURN count(f) as file_count
            """)
            file_record = file_result.single()
            file_count = file_record['file_count'] if file_record else 0
            
            print(f"\n🔍 Vector Index Nodes:")
            print(f"  CodeChunk nodes: {chunk_count}")
            print(f"  File nodes: {file_count}")
            
            # Check relationships
            rel_result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as rel_type, count(r) as count
                ORDER BY count DESC
                LIMIT 10
            """)
            
            print(f"\n🔗 Relationships:")
            for record in rel_result:
                print(f"  {record['rel_type']}: {record['count']}")
    
    except Exception as e:
        print(f"❌ Error checking database: {str(e)}")
    
    finally:
        graph_builder.close_connection()


if __name__ == "__main__":
    print("🚀 Simple Vector Index Test")
    print("This test uses minimal data to reduce API costs")
    print("=" * 60)
    
    # First check what's already in the database
    check_database_contents()
    
    # Run the simple vector index test
    success = test_simple_vector_index()
    
    if success:
        print("\n🎉 Simple Vector Index Test PASSED!")
        print("\n💡 What to explore in Neo4j Browser:")
        print("   🌐 Open http://localhost:7474")
        print("   🔍 Try the queries from docs/VECTOR_INDEX_VISUALIZATION_GUIDE.md")
        print("   📊 Compare knowledge graph nodes vs vector index nodes")
    else:
        print("\n❌ Test failed!") 