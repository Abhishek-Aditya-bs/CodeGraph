#!/usr/bin/env python3
"""
Professional Vector Index Tests for Code Graph
Tests vector index functionality with cost controls and repository cloning
"""

import sys
import argparse
import tempfile
import shutil
from pathlib import Path

# Add the parent directory to the path so we can import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.graph_builder import GraphBuilder
from app.ingestion import clone_repository, parse_code_chunks


class UnifiedGraphRAGTester:
    """Professional tester for unified GraphRAG system with cost controls"""
    
    def __init__(self, cost_mode: str = "limited", custom_repo: str = None):
        """
        Initialize the tester with cost control settings
        
        Args:
            cost_mode: "limited" for cost-controlled testing, "full" for comprehensive testing
            custom_repo: Custom repository URL to test (optional)
        """
        self.cost_mode = cost_mode
        self.custom_repo = custom_repo
        self.temp_dirs = []
        
        # Cost control settings
        if cost_mode == "limited":
            self.max_chunks = 20
            self.allowed_languages = ['.java', '.py']
            self.estimated_cost = "$0.002-0.005"
        else:  # full mode
            self.max_chunks = None
            self.allowed_languages = None
            self.estimated_cost = "$0.05-0.20"
    
    def cleanup(self):
        """Clean up temporary directories"""
        for temp_dir in self.temp_dirs:
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)
                print(f"🧹 Cleaned up temporary directory: {temp_dir}")
    
    def test_unified_graphrag_system(self) -> bool:
        """
        Test the unified GraphRAG system that combines knowledge graph and vector index
        
        Returns:
            bool: True if test passes, False otherwise
        """
        print("🚀 UNIFIED GRAPHRAG SYSTEM TEST")
        print("=" * 60)
        print(f"💰 Cost mode: {self.cost_mode} (estimated: {self.estimated_cost})")
        
        try:
            # Step 1: Clone or use existing repository
            repo_url = self.custom_repo or "https://github.com/iluwatar/java-design-patterns.git"
            print(f"\n📥 Cloning repository: {repo_url}")
            
            temp_dir = tempfile.mkdtemp(prefix="graphrag_test_")
            self.temp_dirs.append(temp_dir)
            
            clone_success, clone_message, repo_path = clone_repository(
                repo_url, 
                target_dir=temp_dir,
                use_project_dir=False
            )
            
            if not clone_success:
                print(f"❌ Repository cloning failed: {clone_message}")
                return False
            
            print(f"✅ Repository cloned successfully to: {repo_path}")
            
            # Step 2: Parse code chunks with cost controls
            print(f"\n📝 Parsing code chunks (mode: {self.cost_mode})...")
            
            chunk_success, chunk_message, chunks = parse_code_chunks(
                repo_path,
                chunk_size=800,  # Larger chunks for better context
                include_extensions=self.allowed_languages,
                exclude_patterns=['target', 'test', '.git', 'README', 'docs']
            )
            
            if not chunk_success:
                print(f"❌ Code parsing failed: {chunk_message}")
                return False
            
            print(f"📄 Parsed {len(chunks)} total chunks")
            
            # Apply cost controls
            if self.max_chunks and len(chunks) > self.max_chunks:
                chunks = chunks[:self.max_chunks]
                print(f"💰 Limited to {len(chunks)} chunks for cost control")
            
            # Step 3: Create unified GraphRAG system
            print(f"\n🧠 Creating unified GraphRAG system with {len(chunks)} chunks...")
            
            with GraphBuilder() as gb:
                # Connect to Neo4j
                connect_success, connect_message = gb.connect_to_neo4j()
                if not connect_success:
                    print(f"❌ Neo4j connection failed: {connect_message}")
                    return False
                
                print("✅ Connected to Neo4j")
                
                # Clear database for clean test
                clear_success, clear_message = gb.clear_knowledge_graph(confirm=True)
                if clear_success:
                    print("🧹 Cleared existing data for clean test")
                
                # Create unified GraphRAG system
                print("🚀 Creating unified GraphRAG system...")
                unified_success, unified_message = gb.create_unified_graphrag_system(chunks)
                
                if not unified_success:
                    print(f"❌ Unified GraphRAG creation failed: {unified_message}")
                    return False
                
                print("✅ Unified GraphRAG system created successfully!")
                print(unified_message)
                
                # Step 4: Test vector search functionality
                print(f"\n🔍 Testing vector search functionality...")
                test_queries = [
                    "adapter pattern implementation",
                    "factory method design pattern",
                    "class inheritance hierarchy"
                ]
                
                for query in test_queries:
                    print(f"\n🔎 Testing query: '{query}'")
                    search_success, search_message, search_results = gb.test_vector_search(query, k=3)
                    
                    if search_success and search_results:
                        print(f"✅ Found {len(search_results)} results")
                        for i, result in enumerate(search_results[:2], 1):
                            print(f"   {i}. {result['metadata'].get('file_path', 'unknown')} (score: {result['score']:.3f})")
                    else:
                        print(f"⚠️ Search issue: {search_message}")
                
                # Step 5: Verify coexistence - check both systems exist
                print(f"\n🔍 Verifying coexistence of both systems...")
                
                with gb.driver.session() as session:
                    # Check knowledge graph entities
                    kg_result = session.run("MATCH (n) WHERE n:Class OR n:Function OR n:Interface RETURN count(n) as kg_count")
                    kg_count = kg_result.single()["kg_count"]
                    
                    # Check vector index chunks
                    vector_result = session.run("MATCH (c:CodeChunk) RETURN count(c) as vector_count")
                    vector_count = vector_result.single()["vector_count"]
                    
                    # Check bridge relationships
                    bridge_result = session.run("MATCH ()-[r:REPRESENTS]->() RETURN count(r) as bridge_count")
                    bridge_count = bridge_result.single()["bridge_count"]
                    
                    # Check unified File nodes
                    file_result = session.run("MATCH (f:File) RETURN count(f) as file_count")
                    file_count = file_result.single()["file_count"]
                    
                    print(f"📊 COEXISTENCE VERIFICATION:")
                    print(f"   🧠 Knowledge Graph Entities: {kg_count}")
                    print(f"   🔍 Vector Index Chunks: {vector_count}")
                    print(f"   🌉 Bridge Relationships: {bridge_count}")
                    print(f"   📁 Unified File Nodes: {file_count}")
                    
                    if kg_count > 0 and vector_count > 0:
                        print("✅ COEXISTENCE VERIFIED: Both systems working together!")
                    else:
                        print("❌ COEXISTENCE FAILED: One or both systems missing")
                        return False
                
                # Step 6: Get final system statistics
                stats_success, stats_message = gb._get_unified_system_stats()
                if stats_success:
                    print(f"\n📈 FINAL SYSTEM STATISTICS:")
                    print(f"   {stats_message}")
            
            print(f"\n✅ UNIFIED GRAPHRAG SYSTEM TEST COMPLETED SUCCESSFULLY!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")
            return False
        
        finally:
            self.cleanup()
    
    def test_separate_systems(self) -> bool:
        """
        Test knowledge graph and vector index as separate systems (legacy mode)
        
        Returns:
            bool: True if test passes, False otherwise
        """
        print("\n🔄 SEPARATE SYSTEMS TEST (Legacy Mode)")
        print("=" * 60)
        
        try:
            # Use a smaller dataset for separate testing
            repo_url = "https://github.com/spring-projects/spring-petclinic.git"
            print(f"📥 Cloning repository: {repo_url}")
            
            temp_dir = tempfile.mkdtemp(prefix="separate_test_")
            self.temp_dirs.append(temp_dir)
            
            clone_success, clone_message, repo_path = clone_repository(
                repo_url,
                target_dir=temp_dir,
                use_project_dir=False
            )
            
            if not clone_success:
                print(f"❌ Repository cloning failed: {clone_message}")
                return False
            
            # Parse chunks with strict limits for cost control
            chunk_success, chunk_message, chunks = parse_code_chunks(
                repo_path,
                chunk_size=600,
                include_extensions=['.java'],
                exclude_patterns=['target', 'test', '.git', 'static', 'resources']
            )
            
            if not chunk_success or not chunks:
                print(f"❌ Code parsing failed: {chunk_message}")
                return False
            
            # Limit chunks for cost control
            chunks = chunks[:10]  # Very limited for separate testing
            print(f"📄 Using {len(chunks)} chunks for separate systems test")
            
            with GraphBuilder() as gb:
                connect_success, connect_message = gb.connect_to_neo4j()
                if not connect_success:
                    print(f"❌ Neo4j connection failed: {connect_message}")
                    return False
                
                # Clear database
                gb.clear_knowledge_graph(confirm=True)
                
                # Test 1: Knowledge graph only
                print("\n🧠 Testing knowledge graph creation...")
                kg_success, kg_message = gb.generate_knowledge_graph(chunks)
                
                if kg_success:
                    print("✅ Knowledge graph created successfully")
                else:
                    print(f"❌ Knowledge graph failed: {kg_message}")
                    return False
                
                # Test 2: Vector index only (this will clear the knowledge graph)
                print("\n🔍 Testing vector index creation...")
                vector_success, vector_message = gb.create_vector_index(chunks)
                
                if vector_success:
                    print("✅ Vector index created successfully")
                    print("⚠️ Note: This cleared the knowledge graph (expected in separate mode)")
                else:
                    print(f"❌ Vector index failed: {vector_message}")
                    return False
            
            print("✅ SEPARATE SYSTEMS TEST COMPLETED")
            return True
            
        except Exception as e:
            print(f"❌ Separate systems test failed: {str(e)}")
            return False
        
        finally:
            self.cleanup()


def main():
    """Main function with command-line argument parsing"""
    parser = argparse.ArgumentParser(description="Test unified GraphRAG system with cost controls")
    parser.add_argument("--full", action="store_true", help="Run full test mode (higher cost)")
    parser.add_argument("--repo", type=str, help="Custom repository URL to test")
    parser.add_argument("--separate", action="store_true", help="Test separate systems (legacy mode)")
    
    args = parser.parse_args()
    
    # Determine cost mode
    cost_mode = "full" if args.full else "limited"
    
    # Create tester
    tester = UnifiedGraphRAGTester(cost_mode=cost_mode, custom_repo=args.repo)
    
    try:
        if args.separate:
            # Test separate systems
            success = tester.test_separate_systems()
        else:
            # Test unified system
            success = tester.test_unified_graphrag_system()
        
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