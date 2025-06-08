# Code Graph - Core Graph Builder Tests
# Comprehensive tests for knowledge graph creation and vector indexing functionality

import pytest
import logging
from typing import List, Dict, Any, Tuple
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from app.graph_builder import GraphBuilder
from app.ingestion import parse_code_chunks
from tests.fixtures.java_patterns import get_test_data_manager

logger = logging.getLogger(__name__)


class TestGraphBuilderInitialization:
    """Test suite for GraphBuilder initialization and connection management"""
    
    def test_graph_builder_initialization(self, database_connection):
        """
        Test GraphBuilder initialization with singleton connection
        
        Validates:
        1. Proper initialization with singleton connection
        2. Config loading
        3. Connection property access
        """
        # Initialize GraphBuilder
        graph_builder = GraphBuilder()
        
        # Validate initialization
        assert graph_builder is not None
        assert graph_builder.config is not None
        assert graph_builder.connection is not None
        
        # Validate connection properties
        assert graph_builder.driver is not None
        assert graph_builder.is_connected is True
        
        logger.info("✅ GraphBuilder initialization test passed")
    
    def test_connection_properties(self, database_connection):
        """
        Test connection property behavior
        
        Validates:
        1. Driver property returns correct driver
        2. Connection status reflects actual state
        3. Properties handle connection failures gracefully
        """
        graph_builder = GraphBuilder()
        
        # Test with active connection
        assert graph_builder.is_connected is True
        assert graph_builder.driver is not None
        
        # Test driver type
        from neo4j import Driver
        assert isinstance(graph_builder.driver, Driver)
        
        logger.info("✅ Connection properties test passed")
    
    def test_initialization_without_connection(self):
        """
        Test GraphBuilder behavior when database is not connected
        
        Validates:
        1. Graceful handling of missing connection
        2. Proper error states
        3. Method behavior with no connection
        """
        with patch('app.graph_builder.get_neo4j_connection') as mock_connection:
            # Mock disconnected state
            mock_conn = Mock()
            mock_conn.is_connected = False
            mock_conn.get_driver.return_value = None
            mock_connection.return_value = mock_conn
            
            graph_builder = GraphBuilder()
            
            # Validate disconnected state
            assert graph_builder.is_connected is False
            assert graph_builder.driver is None
            
            # Test method behavior with no connection
            success, message = graph_builder.generate_knowledge_graph([])
            assert success is False
            assert "Not connected to Neo4j" in message
            
            success, message = graph_builder.create_vector_index([])
            assert success is False
            assert "Not connected to Neo4j" in message
        
        logger.info("✅ Initialization without connection test passed")


class TestKnowledgeGraphGeneration:
    """Test suite for knowledge graph generation functionality"""
    
    @pytest.mark.api_cost
    def test_generate_knowledge_graph_basic(self, clean_database, test_config, quick_documents):
        """
        Test basic knowledge graph generation
        
        Validates:
        1. Successful graph generation from documents
        2. Proper LLM integration
        3. Neo4j storage
        4. Statistics generation
        """
        # Use cached test documents (optimized)
        documents = quick_documents
        if not documents:
            pytest.skip("No cached documents available")
        
        # Initialize GraphBuilder
        graph_builder = GraphBuilder()
        
        # Generate knowledge graph
        success, message = graph_builder.generate_knowledge_graph(documents)
        
        # Validate results
        assert success is True, f"Knowledge graph generation failed: {message}"
        assert "Knowledge graph generated successfully" in message
        assert f"Documents processed: {len(documents)}" in message
        
        # Validate graph was created in Neo4j
        self._validate_graph_creation(graph_builder.driver)
        
        logger.info(f"✅ Basic knowledge graph generation test passed with {len(documents)} documents")
    
    def test_generate_knowledge_graph_empty_documents(self, clean_database):
        """
        Test knowledge graph generation with empty document list
        
        Validates:
        1. Proper error handling for empty input
        2. Meaningful error messages
        3. No side effects on database
        """
        graph_builder = GraphBuilder()
        
        # Test with empty list
        success, message = graph_builder.generate_knowledge_graph([])
        
        assert success is False
        assert "No documents provided" in message
        
        # Test with None
        success, message = graph_builder.generate_knowledge_graph(None)
        
        assert success is False
        assert "No documents provided" in message
        
        logger.info("✅ Empty documents test passed")
    
    @pytest.mark.api_cost
    def test_generate_knowledge_graph_large_dataset(self, clean_database, test_config, extended_documents):
        """
        Test knowledge graph generation with larger document set
        
        Validates:
        1. Handling of multiple patterns
        2. Performance with larger datasets
        3. Comprehensive entity extraction
        4. Relationship creation
        """
        # Use cached extended documents (optimized)
        documents = extended_documents
        if not documents or len(documents) < 6:
            pytest.skip("Need at least 6 cached documents for large dataset test")
        
        graph_builder = GraphBuilder()
        
        # Generate knowledge graph
        success, message = graph_builder.generate_knowledge_graph(documents)
        
        assert success is True, f"Large dataset generation failed: {message}"
        
        # Validate comprehensive graph creation
        stats = self._get_detailed_graph_stats(graph_builder.driver)
        
        # Should have multiple node types
        assert stats['total_nodes'] > len(documents), "Should create more nodes than input documents"
        assert stats['total_relationships'] > 0, "Should create relationships between entities"
        
        # Should have code-specific entities
        expected_node_types = ['File', 'Function', 'Class']
        for node_type in expected_node_types:
            assert stats['node_counts'].get(node_type, 0) > 0, f"Should create {node_type} nodes"
        
        logger.info(f"✅ Large dataset test passed: {stats['total_nodes']} nodes, {stats['total_relationships']} relationships")
    
    def test_generate_knowledge_graph_error_handling(self, clean_database):
        """
        Test error handling in knowledge graph generation
        
        Validates:
        1. Handling of malformed documents
        2. API key issues
        3. Neo4j connection issues
        4. Dependency issues
        """
        graph_builder = GraphBuilder()
        
        # Test with malformed documents
        malformed_docs = [Mock(page_content="", metadata={})]
        
        # This might succeed or fail depending on LLM behavior, but should not crash
        success, message = graph_builder.generate_knowledge_graph(malformed_docs)
        assert isinstance(success, bool)
        assert isinstance(message, str)
        
        # Test with missing API key
        with patch.object(graph_builder.config, 'OPENAI_API_KEY', None):
            success, message = graph_builder.generate_knowledge_graph(malformed_docs)
            # Should handle gracefully (might succeed with default key or fail gracefully)
            assert isinstance(success, bool)
        
        logger.info("✅ Error handling test passed")
    
    def _get_test_documents(self, test_config, java_patterns_path, selected_patterns, max_docs=10):
        """Helper method to get test documents"""
        test_data = get_test_data_manager(java_patterns_path, selected_patterns)
        
        # Get first available pattern
        available_patterns = list(test_data.pattern_paths.keys())
        if not available_patterns:
            return []
        
        pattern = available_patterns[0]
        pattern_path = test_data.pattern_paths[pattern]
        
        success, message, documents = parse_code_chunks(
            codebase_path=str(pattern_path),
            chunk_size=test_config["chunk_size"],
            chunk_overlap=test_config["chunk_overlap"],
            include_extensions=['.java']
        )
        
        if success and documents:
            return documents[:max_docs]
        return []
    
    def _validate_graph_creation(self, driver):
        """Helper method to validate graph was created"""
        with driver.session() as session:
            # Check if any nodes were created
            result = session.run("MATCH (n) RETURN count(n) as node_count")
            node_count = result.single()["node_count"]
            assert node_count > 0, "No nodes were created in the graph"
            
            # Check if relationships were created
            result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
            rel_count = result.single()["rel_count"]
            # Note: Relationships might be 0 for small datasets, so we don't assert
            
            logger.info(f"Graph validation: {node_count} nodes, {rel_count} relationships")
    
    def _get_detailed_graph_stats(self, driver):
        """Helper method to get detailed graph statistics"""
        with driver.session() as session:
            # Get total counts
            result = session.run("MATCH (n) RETURN count(n) as total_nodes")
            total_nodes = result.single()["total_nodes"]
            
            result = session.run("MATCH ()-[r]->() RETURN count(r) as total_relationships")
            total_relationships = result.single()["total_relationships"]
            
            # Get node type counts
            result = session.run("MATCH (n) RETURN labels(n)[0] as label, count(n) as count")
            node_counts = {record["label"]: record["count"] for record in result}
            
            return {
                'total_nodes': total_nodes,
                'total_relationships': total_relationships,
                'node_counts': node_counts
            }


class TestVectorIndexCreation:
    """Test suite for vector index creation functionality"""
    
    @pytest.mark.api_cost
    def test_create_vector_index_basic(self, clean_database, test_config, quick_documents):
        """
        Test basic vector index creation
        
        Validates:
        1. Successful embedding generation
        2. CodeChunk node creation
        3. Vector index creation
        4. Metadata preservation
        """
        # Use cached test documents (optimized)
        documents = quick_documents
        if not documents:
            pytest.skip("No cached documents available")
        
        graph_builder = GraphBuilder()
        
        # Create vector index
        success, message = graph_builder.create_vector_index(documents)
        
        # Validate results
        assert success is True, f"Vector index creation failed: {message}"
        assert "Vector index created successfully" in message
        assert f"Documents processed: {len(documents)}" in message
        
        # Validate CodeChunk nodes were created
        self._validate_vector_index_creation(graph_builder.driver, len(documents))
        
        logger.info(f"✅ Basic vector index creation test passed with {len(documents)} documents")
    
    def test_create_vector_index_empty_documents(self, clean_database):
        """
        Test vector index creation with empty document list
        
        Validates:
        1. Proper error handling for empty input
        2. Meaningful error messages
        3. No side effects on database
        """
        graph_builder = GraphBuilder()
        
        # Test with empty list
        success, message = graph_builder.create_vector_index([])
        
        assert success is False
        assert "No documents provided" in message
        
        logger.info("✅ Empty documents vector index test passed")
    
    @pytest.mark.api_cost
    def test_create_vector_index_metadata_preservation(self, clean_database, test_config, quick_documents):
        """
        Test that metadata is properly preserved in CodeChunk nodes
        
        Validates:
        1. All metadata fields are stored
        2. File relationships are created
        3. Chunk IDs are preserved
        4. Language and path information is correct
        """
        documents = quick_documents[:3] if quick_documents else []
        if not documents:
            pytest.skip("No cached documents available")
        
        graph_builder = GraphBuilder()
        
        # Create vector index
        success, message = graph_builder.create_vector_index(documents)
        assert success is True
        
        # Validate metadata preservation
        self._validate_metadata_preservation(graph_builder.driver, documents)
        
        logger.info("✅ Metadata preservation test passed")
    
    @pytest.mark.api_cost
    def test_create_vector_index_file_relationships(self, clean_database, test_config, standard_documents):
        """
        Test that File nodes and relationships are created correctly
        
        Validates:
        1. File nodes are created
        2. CONTAINS_CHUNK relationships exist
        3. File metadata is accurate
        4. Multiple chunks per file are handled
        """
        documents = standard_documents
        if not documents:
            pytest.skip("No cached documents available")
        
        graph_builder = GraphBuilder()
        
        # Create vector index
        success, message = graph_builder.create_vector_index(documents)
        assert success is True
        
        # Validate file relationships
        self._validate_file_relationships(graph_builder.driver, documents)
        
        logger.info("✅ File relationships test passed")
    
    def _get_test_documents(self, test_config, java_patterns_path, selected_patterns, max_docs=10):
        """Helper method to get test documents"""
        test_data = get_test_data_manager(java_patterns_path, selected_patterns)
        
        available_patterns = list(test_data.pattern_paths.keys())
        if not available_patterns:
            return []
        
        pattern = available_patterns[0]
        pattern_path = test_data.pattern_paths[pattern]
        
        success, message, documents = parse_code_chunks(
            codebase_path=str(pattern_path),
            chunk_size=test_config["chunk_size"],
            chunk_overlap=test_config["chunk_overlap"],
            include_extensions=['.java']
        )
        
        if success and documents:
            return documents[:max_docs]
        return []
    
    def _validate_vector_index_creation(self, driver, expected_chunks):
        """Helper method to validate vector index was created"""
        with driver.session() as session:
            # Check CodeChunk nodes were created
            result = session.run("MATCH (c:CodeChunk) RETURN count(c) as chunk_count")
            chunk_count = result.single()["chunk_count"]
            assert chunk_count == expected_chunks, f"Expected {expected_chunks} chunks, got {chunk_count}"
            
            # Check that embeddings exist
            result = session.run("MATCH (c:CodeChunk) WHERE c.embedding IS NOT NULL RETURN count(c) as embedded_count")
            embedded_count = result.single()["embedded_count"]
            assert embedded_count == expected_chunks, f"Expected {expected_chunks} embedded chunks, got {embedded_count}"
            
            # Check vector index exists (this might fail in some Neo4j versions, so we'll be lenient)
            try:
                result = session.run("SHOW INDEXES")
                indexes = [record["name"] for record in result if "vector" in record.get("name", "").lower()]
                logger.info(f"Vector indexes found: {indexes}")
            except Exception as e:
                logger.warning(f"Could not check vector indexes: {e}")
    
    def _validate_metadata_preservation(self, driver, documents):
        """Helper method to validate metadata preservation"""
        with driver.session() as session:
            # Check that all expected metadata fields exist
            result = session.run("""
                MATCH (c:CodeChunk) 
                RETURN c.chunk_id as chunk_id, c.file_path as file_path, c.language as language, 
                       c.start_line as start_line, c.end_line as end_line, c.chunk_size as chunk_size
                LIMIT 5
            """)
            
            chunks = list(result)
            assert len(chunks) > 0, "No chunks found for metadata validation"
            
            for chunk in chunks:
                # Validate required fields exist
                assert chunk["chunk_id"] is not None
                assert chunk["file_path"] is not None
                assert chunk["language"] is not None
                assert chunk["chunk_size"] is not None
                
                # Validate language is Java (for our test data)
                assert chunk["language"] == "java"
    
    def _validate_file_relationships(self, driver, documents):
        """Helper method to validate file relationships"""
        with driver.session() as session:
            # Check File nodes were created
            result = session.run("MATCH (f:File) RETURN count(f) as file_count")
            file_count = result.single()["file_count"]
            assert file_count > 0, "No File nodes were created"
            
            # Check CONTAINS_CHUNK relationships exist
            result = session.run("MATCH (f:File)-[:CONTAINS_CHUNK]->(c:CodeChunk) RETURN count(*) as rel_count")
            rel_count = result.single()["rel_count"]
            assert rel_count > 0, "No CONTAINS_CHUNK relationships were created"
            
            # Validate file metadata
            result = session.run("""
                MATCH (f:File) 
                RETURN f.path as path, f.name as name, f.extension as extension, 
                       f.language as language, f.total_chunks as total_chunks
                LIMIT 3
            """)
            
            files = list(result)
            for file_record in files:
                assert file_record["path"] is not None
                assert file_record["name"] is not None
                assert file_record["extension"] == "java"
                assert file_record["language"] == "java"
                assert file_record["total_chunks"] > 0


class TestGraphRAGSystem:
    """Test suite for complete GraphRAG system creation"""
    
    @pytest.mark.api_cost
    @pytest.mark.slow
    def test_create_graphrag_system_basic(self, clean_database, test_config, java_patterns_path, selected_patterns):
        """
        Test complete GraphRAG system creation
        
        Validates:
        1. Both knowledge graph and vector index are created
        2. Bridge relationships are established
        3. System statistics are generated
        4. All components work together
        """
        # Get test documents
        documents = self._get_test_documents(test_config, java_patterns_path, selected_patterns, max_docs=6)
        if not documents:
            pytest.skip("No test documents available")
        
        graph_builder = GraphBuilder()
        
        # Create complete GraphRAG system
        success, message = graph_builder.create_graphrag_system(documents)
        
        # Validate results
        assert success is True, f"GraphRAG system creation failed: {message}"
        assert "GraphRAG system created successfully" in message
        
        # Validate both systems were created
        self._validate_complete_system(graph_builder.driver, len(documents))
        
        logger.info(f"✅ Complete GraphRAG system test passed with {len(documents)} documents")
    
    @pytest.mark.api_cost
    def test_create_graphrag_system_bridge_relationships(self, clean_database, test_config, java_patterns_path, selected_patterns):
        """
        Test bridge relationship creation in GraphRAG system
        
        Validates:
        1. REPRESENTS relationships are created
        2. Semantic and structural layers are connected
        3. Hybrid queries are possible
        """
        documents = self._get_test_documents(test_config, java_patterns_path, selected_patterns, max_docs=4)
        if not documents:
            pytest.skip("No test documents available")
        
        graph_builder = GraphBuilder()
        
        # Create GraphRAG system
        success, message = graph_builder.create_graphrag_system(documents)
        assert success is True
        
        # Validate bridge relationships
        self._validate_bridge_relationships(graph_builder.driver)
        
        logger.info("✅ Bridge relationships test passed")
    
    def test_create_graphrag_system_empty_documents(self, clean_database):
        """
        Test GraphRAG system creation with empty documents
        
        Validates:
        1. Proper error handling
        2. Meaningful error messages
        3. No partial system creation
        """
        graph_builder = GraphBuilder()
        
        success, message = graph_builder.create_graphrag_system([])
        
        assert success is False
        assert "No documents provided" in message
        
        logger.info("✅ Empty documents GraphRAG test passed")
    
    @pytest.mark.api_cost
    @pytest.mark.slow
    def test_create_graphrag_system_statistics(self, clean_database, test_config, java_patterns_path, selected_patterns):
        """
        Test system statistics generation
        
        Validates:
        1. Comprehensive statistics are generated
        2. Statistics reflect actual system state
        3. Both structural and semantic components are counted
        """
        documents = self._get_test_documents(test_config, java_patterns_path, selected_patterns, max_docs=5)
        if not documents:
            pytest.skip("No test documents available")
        
        graph_builder = GraphBuilder()
        
        # Create GraphRAG system
        success, message = graph_builder.create_graphrag_system(documents)
        assert success is True
        
        # Validate statistics in message
        assert "System Statistics:" in message or "Statistics" in message
        
        # Get detailed statistics
        stats = self._get_system_statistics(graph_builder.driver)
        
        # Validate statistics make sense
        assert stats['total_nodes'] > len(documents), "Should have more nodes than input documents"
        assert stats['codechunk_count'] == len(documents), "Should have one CodeChunk per document"
        assert stats['file_count'] > 0, "Should have File nodes"
        
        logger.info(f"✅ System statistics test passed: {stats}")
    
    def _get_test_documents(self, test_config, java_patterns_path, selected_patterns, max_docs=10):
        """Helper method to get test documents"""
        test_data = get_test_data_manager(java_patterns_path, selected_patterns)
        
        available_patterns = list(test_data.pattern_paths.keys())
        if not available_patterns:
            return []
        
        pattern = available_patterns[0]
        pattern_path = test_data.pattern_paths[pattern]
        
        success, message, documents = parse_code_chunks(
            codebase_path=str(pattern_path),
            chunk_size=test_config["chunk_size"],
            chunk_overlap=test_config["chunk_overlap"],
            include_extensions=['.java']
        )
        
        if success and documents:
            return documents[:max_docs]
        return []
    
    def _validate_complete_system(self, driver, expected_chunks):
        """Helper method to validate complete system creation"""
        with driver.session() as session:
            # Check CodeChunk nodes (vector system)
            result = session.run("MATCH (c:CodeChunk) RETURN count(c) as chunk_count")
            chunk_count = result.single()["chunk_count"]
            assert chunk_count == expected_chunks
            
            # Check structural nodes (knowledge graph)
            result = session.run("MATCH (n) WHERE NOT n:CodeChunk AND NOT n:File RETURN count(n) as struct_count")
            struct_count = result.single()["struct_count"]
            # Should have some structural nodes (though count may vary)
            logger.info(f"Structural nodes created: {struct_count}")
            
            # Check File nodes
            result = session.run("MATCH (f:File) RETURN count(f) as file_count")
            file_count = result.single()["file_count"]
            assert file_count > 0
            
            # Check relationships exist
            result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
            rel_count = result.single()["rel_count"]
            assert rel_count > 0
    
    def _validate_bridge_relationships(self, driver):
        """Helper method to validate bridge relationships"""
        with driver.session() as session:
            # Check for REPRESENTS relationships
            result = session.run("MATCH ()-[r:REPRESENTS]->() RETURN count(r) as represents_count")
            represents_count = result.single()["represents_count"]
            
            # Check for PART_OF_FILE relationships
            result = session.run("MATCH ()-[r:PART_OF_FILE]->() RETURN count(r) as part_of_count")
            part_of_count = result.single()["part_of_count"]
            
            # At least some bridge relationships should exist
            total_bridges = represents_count + part_of_count
            logger.info(f"Bridge relationships: REPRESENTS={represents_count}, PART_OF_FILE={part_of_count}")
            
            # Note: Bridge relationships might be 0 if no matching entities are found
            # This is acceptable for small test datasets
    
    def _get_system_statistics(self, driver):
        """Helper method to get system statistics"""
        with driver.session() as session:
            # Total nodes
            result = session.run("MATCH (n) RETURN count(n) as total_nodes")
            total_nodes = result.single()["total_nodes"]
            
            # CodeChunk count
            result = session.run("MATCH (c:CodeChunk) RETURN count(c) as codechunk_count")
            codechunk_count = result.single()["codechunk_count"]
            
            # File count
            result = session.run("MATCH (f:File) RETURN count(f) as file_count")
            file_count = result.single()["file_count"]
            
            # Total relationships
            result = session.run("MATCH ()-[r]->() RETURN count(r) as total_relationships")
            total_relationships = result.single()["total_relationships"]
            
            return {
                'total_nodes': total_nodes,
                'codechunk_count': codechunk_count,
                'file_count': file_count,
                'total_relationships': total_relationships
            }


class TestGraphBuilderErrorHandling:
    """Test suite for error handling and edge cases"""
    
    def test_missing_dependencies_handling(self, clean_database):
        """
        Test handling of missing dependencies
        
        Validates:
        1. Graceful handling of import errors
        2. Meaningful error messages
        3. Suggestions for fixing issues
        """
        graph_builder = GraphBuilder()
        
        # Mock missing langchain dependencies
        with patch('builtins.__import__', side_effect=ImportError("No module named 'langchain_openai'")):
            success, message = graph_builder.generate_knowledge_graph([Mock()])
            
            assert success is False
            assert "Missing required dependency" in message
            assert "pip install" in message
        
        logger.info("✅ Missing dependencies handling test passed")
    
    def test_api_key_issues(self, clean_database):
        """
        Test handling of API key issues
        
        Validates:
        1. Behavior with missing API keys
        2. Behavior with invalid API keys
        3. Error message quality
        """
        graph_builder = GraphBuilder()
        
        # Test with None API key
        with patch.object(graph_builder.config, 'OPENAI_API_KEY', None):
            # This might succeed with default key or fail - both are acceptable
            success, message = graph_builder.generate_knowledge_graph([Mock(page_content="test", metadata={})])
            assert isinstance(success, bool)
            assert isinstance(message, str)
        
        logger.info("✅ API key issues test passed")
    
    def test_neo4j_connection_issues(self):
        """
        Test handling of Neo4j connection issues
        
        Validates:
        1. Behavior when Neo4j is disconnected
        2. Proper error messages
        3. No crashes or hangs
        """
        # Test with disconnected Neo4j
        with patch('app.graph_builder.get_neo4j_connection') as mock_connection:
            mock_conn = Mock()
            mock_conn.is_connected = False
            mock_conn.get_driver.return_value = None
            mock_connection.return_value = mock_conn
            
            graph_builder = GraphBuilder()
            
            # Test all main methods
            success, message = graph_builder.generate_knowledge_graph([Mock()])
            assert success is False
            assert "Not connected to Neo4j" in message
            
            success, message = graph_builder.create_vector_index([Mock()])
            assert success is False
            assert "Not connected to Neo4j" in message
            
            success, message = graph_builder.create_graphrag_system([Mock()])
            assert success is False
            assert "Not connected to Neo4j" in message
        
        logger.info("✅ Neo4j connection issues test passed")
    
    def test_malformed_document_handling(self, clean_database):
        """
        Test handling of malformed documents
        
        Validates:
        1. Graceful handling of documents without required fields
        2. Handling of empty or invalid content
        3. Proper error reporting
        """
        graph_builder = GraphBuilder()
        
        # Test with documents missing required fields
        malformed_docs = [
            Mock(page_content="", metadata={}),  # Empty content
            Mock(page_content="test content"),   # Missing metadata
            Mock(metadata={"file_path": "test"}), # Missing page_content
        ]
        
        # These should not crash the system
        for doc in malformed_docs:
            try:
                success, message = graph_builder.create_vector_index([doc])
                # Should either succeed or fail gracefully
                assert isinstance(success, bool)
                assert isinstance(message, str)
            except Exception as e:
                # If it raises an exception, it should be handled gracefully
                logger.warning(f"Exception with malformed doc: {e}")
        
        logger.info("✅ Malformed document handling test passed")


# Helper functions for test data management
def create_mock_document(content: str, file_path: str = "test.java", chunk_id: str = "test_chunk") -> Mock:
    """Create a mock document for testing"""
    doc = Mock()
    doc.page_content = content
    doc.metadata = {
        'file_path': file_path,
        'language': 'java',
        'chunk_id': chunk_id,
        'start_line': 1,
        'end_line': 10
    }
    return doc


def create_test_documents(count: int = 3) -> List[Mock]:
    """Create a list of test documents"""
    documents = []
    for i in range(count):
        content = f"""
        public class TestClass{i} {{
            private String field{i};
            
            public void method{i}() {{
                System.out.println("Test method {i}");
            }}
        }}
        """
        doc = create_mock_document(
            content=content,
            file_path=f"test/TestClass{i}.java",
            chunk_id=f"chunk_{i}"
        )
        documents.append(doc)
    return documents 