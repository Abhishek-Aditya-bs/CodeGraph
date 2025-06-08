"""
Neo4j Database Connection Singleton

This module provides a singleton pattern for managing Neo4j database connections
across the entire application. It ensures only one connection is maintained
and provides thread-safe access to the database.
"""

import logging
from typing import Optional, Tuple
from neo4j import GraphDatabase, Driver
from threading import Lock
from .config import Config

logger = logging.getLogger(__name__)

class Neo4jConnection:
    """
    Singleton class for managing Neo4j database connections
    
    This class ensures that only one Neo4j connection is maintained
    throughout the application lifecycle, providing efficient resource
    management and consistent database access.
    """
    
    _instance: Optional['Neo4jConnection'] = None
    _lock: Lock = Lock()
    
    def __new__(cls) -> 'Neo4jConnection':
        """
        Create or return the singleton instance
        
        Returns:
            Neo4jConnection: The singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(Neo4jConnection, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the connection manager (only once)"""
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.config = Config()
        self.driver: Optional[Driver] = None
        self.is_connected: bool = False
        self._initialized = True
        logger.info("🔧 Neo4j Connection Manager initialized")
    
    def connect(self) -> Tuple[bool, str]:
        """
        Establish connection to Neo4j database
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if self.is_connected and self.driver:
                return True, "✅ Already connected to Neo4j"
            
            logger.info(f"🔗 Connecting to Neo4j at {self.config.NEO4J_URI}")
            
            # Create driver with authentication
            self.driver = GraphDatabase.driver(
                self.config.NEO4J_URI,
                auth=(self.config.NEO4J_USERNAME, self.config.NEO4J_PASSWORD)
            )
            
            # Test the connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                if test_value != 1:
                    raise Exception("Connection test failed")
            
            self.is_connected = True
            logger.info("✅ Neo4j connection established successfully")
            return True, "✅ Connected to Neo4j successfully"
            
        except Exception as e:
            error_msg = f"❌ Failed to connect to Neo4j: {str(e)}"
            logger.error(error_msg)
            self.is_connected = False
            self.driver = None
            return False, error_msg
    
    def get_driver(self) -> Optional[Driver]:
        """
        Get the Neo4j driver instance
        
        Returns:
            Optional[Driver]: The Neo4j driver if connected, None otherwise
        """
        if not self.is_connected or not self.driver:
            logger.warning("⚠️ Attempting to get driver when not connected")
            return None
        return self.driver
    
    def get_session(self):
        """
        Get a new Neo4j session
        
        Returns:
            Neo4j session if connected, None otherwise
        """
        if not self.is_connected or not self.driver:
            logger.warning("⚠️ Attempting to get session when not connected")
            return None
        return self.driver.session()
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test the current connection
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if not self.is_connected or not self.driver:
                return False, "❌ Not connected to Neo4j"
            
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                if test_value == 1:
                    return True, "✅ Neo4j connection is healthy"
                else:
                    return False, "❌ Connection test failed"
                    
        except Exception as e:
            error_msg = f"❌ Connection test failed: {str(e)}"
            logger.error(error_msg)
            # Mark connection as failed so it can be renewed
            self.is_connected = False
            return False, error_msg
    
    def get_database_info(self) -> Tuple[bool, dict]:
        """
        Get database information and statistics
        
        Returns:
            Tuple[bool, dict]: (success, database_info)
        """
        try:
            if not self.is_connected or not self.driver:
                return False, {"error": "Not connected to Neo4j"}
            
            with self.driver.session() as session:
                # Get node counts
                node_result = session.run("MATCH (n) RETURN count(n) as node_count")
                node_count = node_result.single()["node_count"]
                
                # Get relationship counts
                rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
                rel_count = rel_result.single()["rel_count"]
                
                # Get node labels
                labels_result = session.run("CALL db.labels()")
                labels = [record["label"] for record in labels_result]
                
                # Get relationship types
                types_result = session.run("CALL db.relationshipTypes()")
                rel_types = [record["relationshipType"] for record in types_result]
                
                # Check for vector index
                indexes_result = session.run("SHOW INDEXES")
                vector_indexes = []
                for record in indexes_result:
                    if record.get("type") == "VECTOR":
                        vector_indexes.append(record.get("name"))
                
                database_info = {
                    "connected": True,
                    "node_count": node_count,
                    "relationship_count": rel_count,
                    "node_labels": labels,
                    "relationship_types": rel_types,
                    "vector_indexes": vector_indexes,
                    "has_vector_index": "code_chunks_vector_index" in vector_indexes
                }
                
                return True, database_info
                
        except Exception as e:
            error_msg = f"Failed to get database info: {str(e)}"
            logger.error(error_msg)
            return False, {"error": error_msg}
    
    def close(self) -> None:
        """Close the Neo4j connection"""
        try:
            if self.driver:
                self.driver.close()
                self.driver = None
                self.is_connected = False
                logger.info("🔌 Neo4j connection closed")
        except Exception as e:
            logger.error(f"Error closing Neo4j connection: {str(e)}")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.close()


# Global singleton instance
neo4j_connection = Neo4jConnection()

def get_neo4j_connection() -> Neo4jConnection:
    """
    Get the global Neo4j connection singleton
    
    Returns:
        Neo4jConnection: The singleton instance
    """
    return neo4j_connection

def initialize_database() -> Tuple[bool, str]:
    """
    Initialize the database connection (to be called at app startup)
    
    Returns:
        Tuple[bool, str]: (success, message)
    """
    connection = get_neo4j_connection()
    return connection.connect()

def get_database_driver() -> Optional[Driver]:
    """
    Get the Neo4j driver instance
    
    Returns:
        Optional[Driver]: The Neo4j driver if connected, None otherwise
    """
    connection = get_neo4j_connection()
    return connection.get_driver()

def get_database_session():
    """
    Get a new Neo4j session
    
    Returns:
        Neo4j session if connected, None otherwise
    """
    connection = get_neo4j_connection()
    return connection.get_session() 