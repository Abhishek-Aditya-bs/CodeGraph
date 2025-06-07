#!/usr/bin/env python3
"""
Knowledge Graph Generation Tests
Tests knowledge graph generation with various Java codebases including design patterns and Spring Pet Clinic
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.graph_builder import GraphBuilder
from app.ingestion import parse_code_chunks


def test_java_design_patterns_knowledge_graph():
    """
    Test 1: Generate knowledge graph from Java design patterns repository
    """
    print("🎨 TEST 1: JAVA DESIGN PATTERNS KNOWLEDGE GRAPH")
    print("=" * 60)
    
    # Check if Java design patterns repository exists
    patterns_path = "./cloned_repos/java-design-patterns"
    if not Path(patterns_path).exists():
        print("❌ Java design patterns repository not found.")
        print("💡 Clone it with:")
        print("   python -c \"from app.ingestion import clone_repository; clone_repository('https://github.com/iluwatar/java-design-patterns.git')\"")
        return False
    
    print(f"📁 Processing Java Design Patterns from: {patterns_path}")
    
    # Focus on specific design patterns for rich examples
    selected_patterns = [
        "adapter",
        "factory-method", 
        "observer",
        "strategy",
        "decorator",
        "singleton"
    ]
    
    print(f"🎯 Focusing on these design patterns: {', '.join(selected_patterns)}")
    
    # Parse Java code chunks from selected patterns
    print(f"\n📝 Parsing Java code chunks from design patterns...")
    
    all_chunks = []
    processed_patterns = []
    
    for pattern in selected_patterns:
        pattern_path = Path(patterns_path) / pattern
        if pattern_path.exists():
            print(f"   📂 Processing {pattern} pattern...")
            
            chunk_success, chunk_message, chunks = parse_code_chunks(
                str(pattern_path),
                chunk_size=1500,  # Larger chunks for better context
                include_extensions=['.java'],
                exclude_patterns=['target', 'test', '.git', 'README']
            )
            
            if chunk_success and chunks:
                all_chunks.extend(chunks)
                processed_patterns.append(pattern)
                print(f"      ✅ Added {len(chunks)} chunks from {pattern}")
            else:
                print(f"      ⚠️ No chunks from {pattern}: {chunk_message}")
    
    if not all_chunks:
        print("❌ No Java chunks found in design patterns")
        return False
    
    print(f"\n📄 Total chunks collected: {len(all_chunks)}")
    print(f"🎨 Patterns processed: {', '.join(processed_patterns)}")
    
    # Use a reasonable subset for testing (to manage API costs)
    num_chunks = min(15, len(all_chunks))  # Process up to 15 chunks
    selected_chunks = all_chunks[:num_chunks]
    
    print(f"🔬 Processing {len(selected_chunks)} chunks for knowledge graph generation")
    
    # Generate knowledge graph
    print(f"\n🧠 Generating knowledge graph from Java design patterns...")
    
    with GraphBuilder() as gb:
        # Connect to Neo4j
        connect_success, connect_message = gb.connect_to_neo4j()
        if not connect_success:
            print(f"❌ Failed to connect to Neo4j: {connect_message}")
            return False
        
        print("✅ Connected to Neo4j")
        
        # Clear database for clean test
        clear_success, clear_message = gb.clear_knowledge_graph(confirm=True)
        if clear_success:
            print("🧹 Cleared existing knowledge graph for clean test")
        
        # Generate knowledge graph
        print("🔄 Generating knowledge graph from design patterns...")
        kg_success, kg_message = gb.generate_knowledge_graph(selected_chunks)
        
        if not kg_success:
            print(f"❌ Knowledge graph generation failed: {kg_message}")
            return False
        
        print("✅ Knowledge graph generation successful!")
        print(kg_message)
        
        # Get comprehensive database statistics
        final_info_success, final_info_message, final_info_dict = gb.get_database_info()
        if final_info_success:
            print(f"\n📊 KNOWLEDGE GRAPH STATISTICS:")
            print(f"   🔵 Total Nodes: {final_info_dict.get('total_nodes', 0)}")
            print(f"   🔗 Total Relationships: {final_info_dict.get('total_relationships', 0)}")
            
            # Get detailed statistics
            from app.utilities.neo4j_utils import get_database_statistics
            stats_success, stats_message, stats_dict = get_database_statistics(gb.driver)
            
            if stats_success:
                node_labels = stats_dict.get('node_labels', {})
                rel_types = stats_dict.get('relationship_types', {})
                
                print(f"\n🏷️ NODE TYPES:")
                for label, count in node_labels.items():
                    print(f"   {label}: {count} nodes")
                
                print(f"\n🔗 RELATIONSHIP TYPES:")
                for rel_type, count in rel_types.items():
                    print(f"   {rel_type}: {count} relationships")
    
    print("✅ TEST 1 COMPLETED SUCCESSFULLY")
    return True


def test_knowledge_graph_exploration():
    """
    Test 2: Explore the generated knowledge graph with comprehensive queries
    """
    print(f"\n🔍 TEST 2: KNOWLEDGE GRAPH EXPLORATION")
    print("=" * 60)
    
    with GraphBuilder() as gb:
        connect_success, connect_message = gb.connect_to_neo4j()
        if not connect_success:
            print(f"❌ Failed to connect to Neo4j: {connect_message}")
            return False
        
        print("✅ Connected to Neo4j for exploration")
        
        # Define comprehensive exploration queries
        queries = [
            {
                "name": "Node Overview",
                "query": "MATCH (n) RETURN labels(n) as NodeType, count(n) as Count ORDER BY Count DESC",
                "description": "Overview of all node types and their counts"
            },
            {
                "name": "Relationship Overview", 
                "query": "MATCH ()-[r]->() RETURN type(r) as RelationshipType, count(r) as Count ORDER BY Count DESC",
                "description": "Overview of all relationship types and their counts"
            },
            {
                "name": "Sample Classes",
                "query": "MATCH (n:Class) RETURN n.id as ClassName LIMIT 10",
                "description": "Sample Java classes from the codebase"
            },
            {
                "name": "Class Inheritance Hierarchy",
                "query": "MATCH (child:Class)-[:INHERITS]->(parent:Class) RETURN child.id as ChildClass, parent.id as ParentClass",
                "description": "Class inheritance relationships (extends)"
            },
            {
                "name": "Interface Implementations",
                "query": "MATCH (impl:Class)-[:IMPLEMENTS]->(interface) RETURN impl.id as ImplementingClass, interface.id as Interface, labels(interface) as InterfaceType",
                "description": "Classes implementing interfaces"
            },
            {
                "name": "Adapter Pattern Analysis",
                "query": """
                MATCH (adapter:Class)-[r]->(target:Class)
                WHERE adapter.id CONTAINS 'Adapter' OR adapter.id CONTAINS 'adapter'
                RETURN adapter.id as AdapterClass, type(r) as Relationship, target.id as TargetClass
                """,
                "description": "Adapter pattern relationships (if present)"
            },
            {
                "name": "Factory Pattern Analysis",
                "query": """
                MATCH (n:Class) 
                WHERE n.id CONTAINS 'Blacksmith' OR n.id CONTAINS 'Factory'
                RETURN n.id as ClassName, labels(n) as Type
                """,
                "description": "Factory pattern classes (if present)"
            }
        ]
        
        # Execute each query
        for i, query_info in enumerate(queries, 1):
            print(f"\n{i}️⃣ {query_info['name']}")
            print(f"📝 {query_info['description']}")
            print("-" * 50)
            
            try:
                with gb.driver.session() as session:
                    result = session.run(query_info['query'])
                    records = list(result)
                    
                    if not records:
                        print("   No results found.")
                        continue
                    
                    for j, record in enumerate(records[:5], 1):  # Show first 5 results
                        print(f"   {j}. {dict(record)}")
                    
                    if len(records) > 5:
                        print(f"   ... and {len(records) - 5} more results")
                        
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    print("✅ TEST 2 COMPLETED SUCCESSFULLY")
    return True


def test_spring_petclinic_knowledge_graph():
    """
    Test 3: Generate knowledge graph from Spring Pet Clinic (if available)
    """
    print(f"\n🐕 TEST 3: SPRING PET CLINIC KNOWLEDGE GRAPH")
    print("=" * 60)
    
    # Check if Spring Pet Clinic repository exists
    petclinic_path = "./cloned_repos/spring-petclinic"
    if not Path(petclinic_path).exists():
        print("⚠️ Spring Pet Clinic repository not found, skipping this test")
        return True
    
    print(f"📁 Processing Spring Pet Clinic from: {petclinic_path}")
    
    # Parse Java code chunks
    chunk_success, chunk_message, chunks = parse_code_chunks(
        petclinic_path,
        chunk_size=1200,
        include_extensions=['.java'],
        exclude_patterns=['target', 'test', '.git', 'README']
    )
    
    if not chunk_success or not chunks:
        print(f"❌ Failed to parse Spring Pet Clinic chunks: {chunk_message}")
        return False
    
    # Use first 10 chunks for testing
    selected_chunks = chunks[:10]
    print(f"🔬 Processing {len(selected_chunks)} chunks from Spring Pet Clinic")
    
    with GraphBuilder() as gb:
        connect_success, connect_message = gb.connect_to_neo4j()
        if not connect_success:
            print(f"❌ Failed to connect to Neo4j: {connect_message}")
            return False
        
        # Clear and generate new graph
        clear_success, clear_message = gb.clear_knowledge_graph(confirm=True)
        if clear_success:
            print("🧹 Cleared existing knowledge graph")
        
        kg_success, kg_message = gb.generate_knowledge_graph(selected_chunks)
        
        if kg_success:
            print("✅ Spring Pet Clinic knowledge graph generated successfully!")
            print(kg_message)
        else:
            print(f"❌ Failed to generate Spring Pet Clinic graph: {kg_message}")
            return False
    
    print("✅ TEST 3 COMPLETED SUCCESSFULLY")
    return True


def run_all_tests():
    """
    Run all knowledge graph generation tests in sequence
    """
    print("🧠 KNOWLEDGE GRAPH GENERATION TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Java Design Patterns Knowledge Graph", test_java_design_patterns_knowledge_graph),
        ("Knowledge Graph Exploration", test_knowledge_graph_exploration),
        ("Spring Pet Clinic Knowledge Graph", test_spring_petclinic_knowledge_graph)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🚀 RUNNING: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name} - PASSED")
            else:
                print(f"❌ {test_name} - FAILED")
        except Exception as e:
            print(f"❌ {test_name} - ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n📊 TEST RESULTS SUMMARY:")
    print("=" * 50)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 OVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print(f"🌐 Open http://localhost:7474 to explore your knowledge graph!")
        print(f"💡 Use the queries from docs/NEO4J_BROWSER_GUIDE.md for exploration")
    else:
        print(f"⚠️ Some tests failed. Check the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    run_all_tests() 