# Code Graph - Neo4j Connection Tests
# Test functions for Neo4j connection and database operations

import time
from app.graph_builder import GraphBuilder
from app.utilities.neo4j_utils import check_neo4j_health, get_database_statistics


def test_neo4j_connection() -> bool:
    """
    Test Neo4j connection functionality
    
    Returns:
        bool: True if test passed, False otherwise
    """
    print("🧪 Testing Neo4j connection...")
    
    try:
        # Test connection using context manager
        with GraphBuilder() as graph_builder:
            # Test connection
            success, message = graph_builder.connect_to_neo4j()
            
            print(f"📊 Connection Result: {'PASSED' if success else 'FAILED'}")
            print(f"📝 Message: {message}")
            
            if not success:
                return False
            
            # Test database info
            info_success, info_message, info_dict = graph_builder.get_database_info()
            if info_success:
                print(f"\n📊 Database Info:")
                print(info_message)
            
            return success
            
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        return False


def test_neo4j_health_check() -> bool:
    """
    Test Neo4j health check functionality
    
    Returns:
        bool: True if test passed, False otherwise
    """
    print("🧪 Testing Neo4j health check...")
    
    try:
        with GraphBuilder() as graph_builder:
            # Connect first
            success, _ = graph_builder.connect_to_neo4j()
            if not success:
                print("❌ Could not connect to Neo4j for health check test")
                return False
            
            # Test health check
            health_success, health_message = check_neo4j_health(graph_builder.driver)
            
            print(f"📊 Health Check Result: {'PASSED' if health_success else 'FAILED'}")
            print(f"📝 Message: {health_message}")
            
            return health_success
            
    except Exception as e:
        print(f"❌ Health check test failed with exception: {str(e)}")
        return False


def test_database_statistics() -> bool:
    """
    Test database statistics functionality
    
    Returns:
        bool: True if test passed, False otherwise
    """
    print("🧪 Testing database statistics...")
    
    try:
        with GraphBuilder() as graph_builder:
            # Connect first
            success, _ = graph_builder.connect_to_neo4j()
            if not success:
                print("❌ Could not connect to Neo4j for statistics test")
                return False
            
            # Test statistics
            stats_success, stats_message, stats_dict = get_database_statistics(graph_builder.driver)
            
            print(f"📊 Statistics Result: {'PASSED' if stats_success else 'FAILED'}")
            print(f"📝 Message: {stats_message}")
            
            if stats_success and stats_dict:
                print(f"\n📈 Statistics Details:")
                print(f"   🔵 Total Nodes: {stats_dict.get('total_nodes', 0)}")
                print(f"   🔗 Total Relationships: {stats_dict.get('total_relationships', 0)}")
                print(f"   🏷️ Node Labels: {list(stats_dict.get('node_labels', {}).keys())}")
                print(f"   🔗 Relationship Types: {list(stats_dict.get('relationship_types', {}).keys())}")
            
            return stats_success
            
    except Exception as e:
        print(f"❌ Statistics test failed with exception: {str(e)}")
        return False


def test_connection_error_handling() -> bool:
    """
    Test connection error handling with invalid URI
    
    Returns:
        bool: True if test passed (error handled correctly), False otherwise
    """
    print("🧪 Testing connection error handling...")
    
    try:
        # Create a GraphBuilder instance
        graph_builder = GraphBuilder()
        
        # Temporarily modify config to test error handling
        original_uri = graph_builder.config.NEO4J_URI
        graph_builder.config.NEO4J_URI = "neo4j://invalid-host:7687"
        
        # Test connection with invalid URI
        success, message = graph_builder.connect_to_neo4j()
        
        # Restore original URI
        graph_builder.config.NEO4J_URI = original_uri
        
        # Should fail with service unavailable error
        if not success and ("service unavailable" in message.lower() or "connection" in message.lower()):
            print("📊 Error Handling Result: PASSED")
            print("📝 Message: Successfully caught connection error")
            return True
        else:
            print("📊 Error Handling Result: FAILED")
            print(f"📝 Message: Expected connection error, got: {message}")
            return False
            
    except Exception as e:
        print(f"❌ Error handling test failed with exception: {str(e)}")
        return False


def test_connection_lifecycle() -> bool:
    """
    Test connection lifecycle (connect, use, disconnect)
    
    Returns:
        bool: True if test passed, False otherwise
    """
    print("🧪 Testing connection lifecycle...")
    
    try:
        graph_builder = GraphBuilder()
        
        # Test initial state
        if graph_builder.is_connected:
            print("❌ Should not be connected initially")
            return False
        
        # Test connection
        success, message = graph_builder.connect_to_neo4j()
        if not success:
            print(f"❌ Connection failed: {message}")
            return False
        
        # Test connected state
        if not graph_builder.is_connected:
            print("❌ Should be connected after successful connection")
            return False
        
        # Test using connection
        test_success, test_message = graph_builder.test_connection()
        if not test_success:
            print(f"❌ Test query failed: {test_message}")
            return False
        
        # Test disconnection
        graph_builder.close_connection()
        if graph_builder.is_connected:
            print("❌ Should not be connected after close")
            return False
        
        print("📊 Lifecycle Result: PASSED")
        print("📝 Message: Connection lifecycle works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Lifecycle test failed with exception: {str(e)}")
        return False


def run_all_neo4j_tests():
    """
    Run all Neo4j tests
    """
    print("🧪 RUNNING ALL NEO4J TESTS")
    print("=" * 50)
    
    # Test 1: Basic connection
    print("\n1️⃣ Testing Neo4j Connection:")
    test1_result = test_neo4j_connection()
    
    # Test 2: Health check
    print("\n2️⃣ Testing Health Check:")
    test2_result = test_neo4j_health_check()
    
    # Test 3: Database statistics
    print("\n3️⃣ Testing Database Statistics:")
    test3_result = test_database_statistics()
    
    # Test 4: Error handling
    print("\n4️⃣ Testing Error Handling:")
    test4_result = test_connection_error_handling()
    
    # Test 5: Connection lifecycle
    print("\n5️⃣ Testing Connection Lifecycle:")
    test5_result = test_connection_lifecycle()
    
    # Summary
    print("\n📊 NEO4J TEST SUMMARY:")
    print("=" * 50)
    print(f"Neo4j Connection: {'✅ PASSED' if test1_result else '❌ FAILED'}")
    print(f"Health Check: {'✅ PASSED' if test2_result else '❌ FAILED'}")
    print(f"Database Statistics: {'✅ PASSED' if test3_result else '❌ FAILED'}")
    print(f"Error Handling: {'✅ PASSED' if test4_result else '❌ FAILED'}")
    print(f"Connection Lifecycle: {'✅ PASSED' if test5_result else '❌ FAILED'}")
    
    all_passed = all([test1_result, test2_result, test3_result, test4_result, test5_result])
    print(f"\nOverall Result: {'🎉 ALL TESTS PASSED' if all_passed else '⚠️ SOME TESTS FAILED'}")
    
    return all_passed


if __name__ == "__main__":
    run_all_neo4j_tests() 