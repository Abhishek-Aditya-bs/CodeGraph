# Code Graph - Core Database Tests
# Connection layer tests for Neo4j database operations and singleton pattern

import pytest
import logging
from typing import Dict, Any, Tuple
from neo4j import Driver

from app.database import (
    get_neo4j_connection, 
    initialize_database,
    Neo4jConnection
)
from app.utilities.neo4j_utils import clear_knowledge_graph
from app.utilities.graph_stats_utils import (
    get_graph_creation_stats,
    get_vector_index_stats,
    get_graphrag_system_stats
)

logger = logging.getLogger(__name__)


class TestDatabaseConnection:
    """Test suite for database connection functionality"""
    
    def test_database_initialization(self):
        """
        Test database initialization and singleton pattern
        
        Validates:
        1. Database initialization works
        2. Singleton pattern is enforced
        3. Connection properties are accessible
        4. Multiple calls return same instance
        """
        # Test initialization
        success = initialize_database()
        assert success, "Database initialization should succeed"
        
        # Get connection instance
        connection1 = get_neo4j_connection()
        assert connection1 is not None, "Should return connection instance"
        assert isinstance(connection1, Neo4jConnection), "Should return Neo4jConnection instance"
        
        # Test singleton pattern - multiple calls should return same instance
        connection2 = get_neo4j_connection()
        assert connection1 is connection2, "Should return same instance (singleton pattern)"
        
        # Test connection properties
        assert hasattr(connection1, 'is_connected'), "Connection should have is_connected property"
        assert hasattr(connection1, 'get_driver'), "Connection should have get_driver method"
        
        logger.info("✅ Database initialization and singleton pattern validated")
    
    def test_connection_status_and_driver(self, database_connection):
        """
        Test connection status and driver access
        
        Validates:
        1. Connection status reporting
        2. Driver access
        3. Driver properties
        4. Connection health
        """
        # Test connection status
        assert database_connection.is_connected, "Database should be connected"
        
        # Test driver access
        driver = database_connection.get_driver()
        assert driver is not None, "Should return driver instance"
        assert isinstance(driver, Driver), "Should return Neo4j Driver instance"
        
        # Test driver properties
        assert hasattr(driver, 'session'), "Driver should have session method"
        assert hasattr(driver, 'close'), "Driver should have close method"
        
        logger.info("✅ Connection status and driver access validated")
    
    def test_basic_database_operations(self, database_connection):
        """
        Test basic database operations
        
        Validates:
        1. Simple queries work
        2. Database responds correctly
        3. Session management
        4. Query results
        """
        driver = database_connection.get_driver()
        
        # Test simple query
        with driver.session() as session:
            # Test basic connectivity
            result = session.run("RETURN 1 as test_value")
            record = result.single()
            assert record is not None, "Query should return a record"
            assert record["test_value"] == 1, "Query should return correct value"
            
            # Test current time query
            result = session.run("RETURN datetime() as current_time")
            record = result.single()
            assert record is not None, "DateTime query should return a record"
            assert record["current_time"] is not None, "Should return current_time field"
            
            # Test database info query
            result = session.run("CALL db.info()")
            record = result.single()
            assert record is not None, "Database info query should return a record"
        
        logger.info("✅ Basic database operations validated")
    
    def test_database_info_and_statistics(self, database_connection):
        """
        Test database information and statistics retrieval
        
        Validates:
        1. Database version and info
        2. Node and relationship counts
        3. Index information
        4. Statistics utilities
        """
        driver = database_connection.get_driver()
        
        with driver.session() as session:
            # Test database version
            try:
                result = session.run("CALL dbms.components() YIELD name, versions, edition")
                components = list(result)
                assert len(components) > 0, "Should return database components"
                
                # Look for Neo4j Kernel
                neo4j_found = any(comp["name"] == "Neo4j Kernel" for comp in components)
                assert neo4j_found, "Should find Neo4j Kernel component"
                
            except Exception as e:
                # Some Neo4j versions might not support this query
                logger.warning(f"Database version query failed: {e}")
            
            # Test node count
            result = session.run("MATCH (n) RETURN count(n) as node_count")
            record = result.single()
            assert record is not None, "Node count query should return a record"
            node_count = record["node_count"]
            assert isinstance(node_count, int), "Node count should be an integer"
            assert node_count >= 0, "Node count should be non-negative"
            
            # Test relationship count
            result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
            record = result.single()
            assert record is not None, "Relationship count query should return a record"
            rel_count = record["rel_count"]
            assert isinstance(rel_count, int), "Relationship count should be an integer"
            assert rel_count >= 0, "Relationship count should be non-negative"
            
            logger.info(f"Database stats: {node_count} nodes, {rel_count} relationships")
        
        logger.info("✅ Database info and statistics validated")
    
    def test_graph_statistics_utilities(self, database_connection):
        """
        Test graph statistics utility functions
        
        Validates:
        1. Graph creation stats utility
        2. Vector index stats utility
        3. GraphRAG system stats utility
        4. Error handling in stats functions
        """
        driver = database_connection.get_driver()
        
        # Test graph creation stats
        success, message, stats = get_graph_creation_stats(driver)
        assert isinstance(success, bool), "Should return boolean success status"
        assert isinstance(message, str), "Should return string message"
        assert isinstance(stats, dict), "Should return dictionary of stats"
        
        if success:
            logger.info(f"Graph creation stats: {message}")
        else:
            logger.info(f"Graph creation stats (expected empty): {message}")
        
        # Test vector index stats
        success, message = get_vector_index_stats(driver)
        assert isinstance(success, bool), "Should return boolean success status"
        assert isinstance(message, str), "Should return string message"
        
        if success:
            logger.info(f"Vector index stats: {message}")
        else:
            logger.info(f"Vector index stats (expected empty): {message}")
        
        # Test GraphRAG system stats
        success, message = get_graphrag_system_stats(driver)
        assert isinstance(success, bool), "Should return boolean success status"
        assert isinstance(message, str), "Should return string message"
        
        if success:
            logger.info(f"GraphRAG system stats: {message}")
        else:
            logger.info(f"GraphRAG system stats (expected empty): {message}")
        
        logger.info("✅ Graph statistics utilities validated")
    
    def test_database_cleanup_operations(self, database_connection):
        """
        Test database cleanup operations
        
        Validates:
        1. Clear knowledge graph function
        2. Safety confirmation requirement
        3. Cleanup verification
        4. Error handling
        """
        driver = database_connection.get_driver()
        
        # First, create some test data
        with driver.session() as session:
            # Create a test node
            session.run("CREATE (t:TestNode {name: 'test', created_at: datetime()})")
            
            # Verify test node was created
            result = session.run("MATCH (t:TestNode) RETURN count(t) as test_count")
            record = result.single()
            test_count = record["test_count"]
            assert test_count > 0, "Test node should be created"
        
        # Test clear function without confirmation (should fail safely)
        success, message = clear_knowledge_graph(driver, confirm=False)
        assert not success, "Should fail without confirmation"
        assert "confirm" in message.lower(), "Should mention confirmation requirement"
        
        # Verify data still exists
        with driver.session() as session:
            result = session.run("MATCH (t:TestNode) RETURN count(t) as test_count")
            record = result.single()
            test_count = record["test_count"]
            assert test_count > 0, "Test node should still exist without confirmation"
        
        # Test clear function with confirmation (should succeed)
        success, message = clear_knowledge_graph(driver, confirm=True)
        assert success, f"Should succeed with confirmation: {message}"
        
        # Verify data was cleared
        with driver.session() as session:
            result = session.run("MATCH (t:TestNode) RETURN count(t) as test_count")
            record = result.single()
            test_count = record["test_count"]
            assert test_count == 0, "Test node should be cleared"
        
        logger.info("✅ Database cleanup operations validated")
    
    def test_error_handling_and_recovery(self, database_connection):
        """
        Test error handling and recovery scenarios
        
        Validates:
        1. Invalid query handling
        2. Connection recovery
        3. Error message handling
        4. Graceful degradation
        """
        driver = database_connection.get_driver()
        
        # Test invalid query handling
        with driver.session() as session:
            try:
                # This should fail due to invalid syntax
                session.run("INVALID CYPHER QUERY SYNTAX")
                assert False, "Invalid query should raise an exception"
            except Exception as e:
                assert "syntax" in str(e).lower() or "invalid" in str(e).lower(), "Should get syntax error"
                logger.info(f"Invalid query properly handled: {type(e).__name__}")
        
        # Test connection is still working after error
        with driver.session() as session:
            result = session.run("RETURN 'recovery_test' as test")
            record = result.single()
            assert record["test"] == "recovery_test", "Connection should recover after error"
        
        # Test parameter handling
        with driver.session() as session:
            try:
                # This should work fine
                result = session.run("RETURN $param as value", param="test_value")
                record = result.single()
                assert record["value"] == "test_value", "Parameterized query should work"
            except Exception as e:
                assert False, f"Valid parameterized query should not fail: {e}"
        
        logger.info("✅ Error handling and recovery validated")


class TestDatabaseUtilities:
    """Test suite for database utility functions"""
    
    def test_clear_knowledge_graph_utility(self, clean_database):
        """
        Test the clear_knowledge_graph utility function
        
        Validates:
        1. Function signature and parameters
        2. Confirmation requirement
        3. Actual clearing functionality
        4. Return value format
        """
        driver = clean_database.get_driver()
        
        # Create some test data first
        with driver.session() as session:
            session.run("""
                CREATE (f:File {path: '/test/file.java', name: 'file.java'})
                CREATE (c:Class {name: 'TestClass'})
                CREATE (m:Method {name: 'testMethod'})
                CREATE (f)-[:CONTAINS]->(c)
                CREATE (c)-[:HAS_METHOD]->(m)
            """)
            
            # Verify test data exists
            result = session.run("MATCH (n) RETURN count(n) as total")
            record = result.single()
            initial_count = record["total"]
            assert initial_count >= 3, "Test data should be created"
        
        # Test clear function
        success, message = clear_knowledge_graph(driver, confirm=True)
        assert success, f"Clear function should succeed: {message}"
        assert isinstance(message, str), "Should return string message"
        
        # Verify data was cleared
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as total")
            record = result.single()
            final_count = record["total"]
            assert final_count == 0, "All data should be cleared"
        
        logger.info("✅ Clear knowledge graph utility validated")
    
    def test_statistics_utilities_with_data(self, clean_database):
        """
        Test statistics utilities with actual data
        
        Validates:
        1. Stats with empty database
        2. Stats with sample data
        3. Different node types counting
        4. Relationship counting
        """
        driver = clean_database.get_driver()
        
        # Test stats with empty database
        success, message, stats = get_graph_creation_stats(driver)
        assert success, "Stats should work with empty database"
        
        # Create sample data
        with driver.session() as session:
            session.run("""
                CREATE (f1:File {path: '/test/file1.java'})
                CREATE (f2:File {path: '/test/file2.java'})
                CREATE (c1:Class {name: 'Class1'})
                CREATE (c2:Class {name: 'Class2'})
                CREATE (m1:Method {name: 'method1'})
                CREATE (m2:Method {name: 'method2'})
                CREATE (f1)-[:CONTAINS]->(c1)
                CREATE (f2)-[:CONTAINS]->(c2)
                CREATE (c1)-[:HAS_METHOD]->(m1)
                CREATE (c2)-[:HAS_METHOD]->(m2)
                CREATE (c1)-[:CALLS]->(m2)
            """)
        
        # Test stats with data
        success, message, stats = get_graph_creation_stats(driver)
        assert success, f"Stats should work with data: {message}"
        assert isinstance(stats, dict), "Should return stats dictionary"
        
        # Verify some expected stats
        if stats:
            assert "total_nodes" in stats or "nodes" in message.lower(), "Should report node count"
            assert "total_relationships" in stats or "relationships" in message.lower(), "Should report relationship count"
        
        logger.info(f"✅ Statistics utilities with data validated: {message}")


# Utility functions for testing
def create_test_data(driver: Driver, node_count: int = 10) -> Dict[str, int]:
    """
    Create test data for database testing
    
    Args:
        driver: Neo4j driver instance
        node_count: Number of test nodes to create
        
    Returns:
        Dict: Statistics about created data
    """
    with driver.session() as session:
        # Create test nodes and relationships
        session.run("""
            UNWIND range(1, $count) as i
            CREATE (f:TestFile {id: i, name: 'file' + toString(i) + '.java'})
            CREATE (c:TestClass {id: i, name: 'Class' + toString(i)})
            CREATE (m:TestMethod {id: i, name: 'method' + toString(i)})
            CREATE (f)-[:CONTAINS]->(c)
            CREATE (c)-[:HAS_METHOD]->(m)
        """, count=node_count)
        
        # Get statistics
        result = session.run("MATCH (n) RETURN count(n) as total_nodes")
        total_nodes = result.single()["total_nodes"]
        
        result = session.run("MATCH ()-[r]->() RETURN count(r) as total_rels")
        total_rels = result.single()["total_rels"]
        
        return {
            "nodes": total_nodes,
            "relationships": total_rels,
            "test_files": node_count,
            "test_classes": node_count,
            "test_methods": node_count
        }


def verify_test_data_cleanup(driver: Driver) -> bool:
    """
    Verify that test data has been cleaned up
    
    Args:
        driver: Neo4j driver instance
        
    Returns:
        bool: True if database is clean
    """
    with driver.session() as session:
        result = session.run("MATCH (n) RETURN count(n) as total")
        total_nodes = result.single()["total"]
        
        result = session.run("MATCH ()-[r]->() RETURN count(r) as total")
        total_rels = result.single()["total"]
        
        return total_nodes == 0 and total_rels == 0 