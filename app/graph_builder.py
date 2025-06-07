# Code Graph - Knowledge Graph and Embeddings Builder
# This module handles Neo4j connection, knowledge graph creation, and vector indexing

import logging
from typing import Optional, Tuple
from neo4j import GraphDatabase, Driver
from neo4j.exceptions import ServiceUnavailable, AuthError, ConfigurationError
from .config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GraphBuilder:
    """Handles knowledge graph creation and vector indexing in Neo4j"""
    
    def __init__(self):
        """Initialize GraphBuilder with configuration"""
        self.config = Config()
        self.driver: Optional[Driver] = None
        self.is_connected = False
    
    def connect_to_neo4j(self) -> Tuple[bool, str]:
        """
        Establish connection to Neo4j database
        
        Returns:
            Tuple[bool, str]: (success, message)
                - success: True if connection successful, False otherwise
                - message: Success/error message
        """
        try:
            # Validate configuration
            if not self.config.validate_config():
                return False, "❌ Invalid Neo4j configuration. Please check your .env file."
            
            logger.info(f"🔗 Connecting to Neo4j at {self.config.NEO4J_URI}")
            
            # Create Neo4j driver
            self.driver = GraphDatabase.driver(
                self.config.NEO4J_URI,
                auth=(self.config.NEO4J_USERNAME, self.config.NEO4J_PASSWORD),
                max_connection_lifetime=3600,  # 1 hour
                max_connection_pool_size=50,
                connection_acquisition_timeout=60  # 60 seconds
            )
            
            # Test the connection with a simple query
            success, test_message = self.test_connection()
            if not success:
                self.close_connection()
                return False, f"❌ Connection test failed: {test_message}"
            
            self.is_connected = True
            
            success_message = (
                f"✅ Successfully connected to Neo4j!\n"
                f"📍 URI: {self.config.NEO4J_URI}\n"
                f"👤 Username: {self.config.NEO4J_USERNAME}\n"
                f"🔍 Test query: {test_message}"
            )
            
            logger.info("✅ Neo4j connection established successfully")
            return True, success_message
            
        except AuthError as e:
            error_msg = f"❌ Authentication failed: {str(e)}\n💡 Tip: Check your Neo4j username and password in .env file."
            logger.error(error_msg)
            return False, error_msg
            
        except ServiceUnavailable as e:
            error_msg = f"❌ Neo4j service unavailable: {str(e)}\n💡 Tip: Make sure Neo4j is running (try: docker ps)"
            logger.error(error_msg)
            return False, error_msg
            
        except ConfigurationError as e:
            error_msg = f"❌ Configuration error: {str(e)}\n💡 Tip: Check your Neo4j URI format in .env file."
            logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"❌ Unexpected error connecting to Neo4j: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test the Neo4j connection with a simple query
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if not self.driver:
                return False, "No driver available"
            
            # Test with a simple query
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test_value")
                record = result.single()
                
                if record and record["test_value"] == 1:
                    return True, "RETURN 1 query successful"
                else:
                    return False, "Test query returned unexpected result"
                    
        except Exception as e:
            return False, f"Test query failed: {str(e)}"
    
    def get_database_info(self) -> Tuple[bool, str, dict]:
        """
        Get information about the Neo4j database
        
        Returns:
            Tuple[bool, str, dict]: (success, message, info_dict)
        """
        try:
            if not self.is_connected or not self.driver:
                return False, "Not connected to Neo4j", {}
            
            info = {}
            
            with self.driver.session() as session:
                # Get Neo4j version
                version_result = session.run("CALL dbms.components() YIELD name, versions, edition")
                for record in version_result:
                    if record["name"] == "Neo4j Kernel":
                        info["version"] = record["versions"][0]
                        info["edition"] = record["edition"]
                        break
                
                # Get database name
                db_result = session.run("CALL db.info()")
                db_record = db_result.single()
                if db_record:
                    info["database_name"] = db_record.get("name", "neo4j")
                
                # Get node and relationship counts
                node_result = session.run("MATCH (n) RETURN count(n) as node_count")
                node_record = node_result.single()
                info["total_nodes"] = node_record["node_count"] if node_record else 0
                
                rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
                rel_record = rel_result.single()
                info["total_relationships"] = rel_record["rel_count"] if rel_record else 0
                
                # Check for APOC procedures (with fallback)
                try:
                    apoc_result = session.run("CALL dbms.procedures() YIELD name WHERE name STARTS WITH 'apoc' RETURN count(name) as apoc_count")
                    apoc_record = apoc_result.single()
                    info["apoc_procedures"] = apoc_record["apoc_count"] if apoc_record else 0
                except:
                    info["apoc_procedures"] = 0
            
            success_message = (
                f"📊 Neo4j Database Information:\n"
                f"🏷️ Version: {info.get('version', 'Unknown')}\n"
                f"📦 Edition: {info.get('edition', 'Unknown')}\n"
                f"🗄️ Database: {info.get('database_name', 'Unknown')}\n"
                f"🔵 Nodes: {info.get('total_nodes', 0)}\n"
                f"🔗 Relationships: {info.get('total_relationships', 0)}\n"
                f"🔧 APOC Procedures: {info.get('apoc_procedures', 0)}"
            )
            
            return True, success_message, info
            
        except Exception as e:
            error_msg = f"❌ Error getting database info: {str(e)}"
            return False, error_msg, {}
    
    def close_connection(self) -> None:
        """Close the Neo4j connection"""
        try:
            if self.driver:
                self.driver.close()
                self.driver = None
                self.is_connected = False
                logger.info("🔌 Neo4j connection closed")
        except Exception as e:
            logger.error(f"Error closing Neo4j connection: {str(e)}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically close connection"""
        self.close_connection()
    
    def generate_knowledge_graph(self, documents: list) -> Tuple[bool, str]:
        """
        Generate knowledge graph from code documents using LLMGraphTransformer
        
        Args:
            documents: List of chunked Document objects from parse_code_chunks
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if not self.is_connected or not self.driver:
                return False, "❌ Not connected to Neo4j. Please connect first."
            
            if not documents:
                return False, "❌ No documents provided for knowledge graph generation."
            
            logger.info(f"🧠 Starting knowledge graph generation for {len(documents)} documents")
            
            # Import required libraries
            from langchain_openai import ChatOpenAI
            from langchain_experimental.graph_transformers import LLMGraphTransformer
            from langchain_neo4j import Neo4jGraph
            
            # Initialize OpenAI LLM with GPT-4o-mini
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,  # Deterministic output for consistent entity extraction
                openai_api_key=self.config.OPENAI_API_KEY
            )
            
            # Initialize Neo4j graph connection
            neo4j_graph = Neo4jGraph(
                url=self.config.NEO4J_URI,
                username=self.config.NEO4J_USERNAME,
                password=self.config.NEO4J_PASSWORD
            )
            
            # Configure LLMGraphTransformer with code-specific schema
            graph_transformer = LLMGraphTransformer(
                llm=llm,
                allowed_nodes=["File", "Function", "Class", "Module", "Package"],
                allowed_relationships=["CONTAINS", "CALLS", "IMPORTS", "INHERITS", "IMPLEMENTS", "DEPENDS_ON"],
                strict_mode=False  # Allow flexible entity extraction
            )
            
            logger.info("🔄 Transforming documents to graph documents...")
            
            # Transform documents to graph documents
            graph_documents = graph_transformer.convert_to_graph_documents(documents)
            
            if not graph_documents:
                return False, "❌ No graph documents generated from the provided documents."
            
            logger.info(f"📊 Generated {len(graph_documents)} graph documents")
            
            # Store graph documents in Neo4j
            logger.info("💾 Storing knowledge graph in Neo4j...")
            neo4j_graph.add_graph_documents(graph_documents)
            
            # Get statistics about what was created
            stats_success, stats_message, stats = self._get_graph_creation_stats()
            
            success_message = (
                f"✅ Knowledge graph generated successfully!\n"
                f"📄 Documents processed: {len(documents)}\n"
                f"🔄 Graph documents created: {len(graph_documents)}\n"
                f"💾 Stored in Neo4j database\n"
                f"{stats_message if stats_success else 'Statistics unavailable'}"
            )
            
            logger.info("✅ Knowledge graph generation completed successfully")
            return True, success_message
            
        except ImportError as e:
            error_msg = f"❌ Missing required dependency: {str(e)}\n💡 Tip: Install with 'pip install langchain-openai langchain-experimental langchain-community'"
            logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"❌ Error generating knowledge graph: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    

    
    def _get_graph_creation_stats(self) -> Tuple[bool, str, dict]:
        """
        Get statistics about the created knowledge graph
        
        Returns:
            Tuple[bool, str, dict]: (success, message, stats)
        """
        try:
            from app.utilities.neo4j_utils import get_database_statistics
            return get_database_statistics(self.driver)
        except Exception as e:
            return False, f"Error getting stats: {str(e)}", {}
    
    def clear_knowledge_graph(self, confirm: bool = False) -> Tuple[bool, str]:
        """
        Clear the knowledge graph from Neo4j
        WARNING: This will delete all nodes and relationships!
        
        Args:
            confirm: Must be True to actually perform the deletion
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if not self.is_connected or not self.driver:
                return False, "❌ Not connected to Neo4j. Please connect first."
            
            from app.utilities.neo4j_utils import clear_database
            return clear_database(self.driver, confirm=confirm)
            
        except Exception as e:
            error_msg = f"❌ Error clearing knowledge graph: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def create_vector_index(self, documents: list) -> bool:
        """
        Create vector index for embeddings
        
        Args:
            documents: List of chunked Document objects
            
        Returns:
            bool: True if successful, False otherwise
        """
        # TODO: Implement vector index creation using OpenAI embeddings
        pass 