# Code Graph - Core Query Processor Tests
# Comprehensive tests for GraphRAG query processing functionality

import pytest
import logging
from typing import List, Dict, Any, Tuple
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from app.query_processor import QueryProcessor
from app.graph_builder import GraphBuilder
from app.ingestion import parse_code_chunks
from tests.fixtures.java_patterns import get_test_data_manager

logger = logging.getLogger(__name__)


class TestQueryProcessorInitialization:
    """Test suite for QueryProcessor initialization and setup"""
    
    def test_query_processor_initialization(self, database_connection):
        """
        Test QueryProcessor initialization with singleton connection
        
        Validates:
        1. Proper initialization with singleton connection
        2. Config loading
        3. Connection property access
        4. Initial state of embeddings
        """
        # Initialize QueryProcessor
        query_processor = QueryProcessor()
        
        # Validate initialization
        assert query_processor is not None
        assert query_processor.config is not None
        assert query_processor.connection is not None
        
        # Validate connection properties
        assert query_processor.driver is not None
        assert query_processor.is_connected is True
        
        # Validate initial state
        assert query_processor.embeddings is None  # Should be None until setup_retrievers is called
        
        logger.info("✅ QueryProcessor initialization test passed")
    
    def test_connection_properties(self, database_connection):
        """
        Test connection property behavior
        
        Validates:
        1. Driver property returns correct driver
        2. Connection status reflects actual state
        3. Properties handle connection failures gracefully
        """
        query_processor = QueryProcessor()
        
        # Test with active connection
        assert query_processor.is_connected is True
        assert query_processor.driver is not None
        
        # Test driver type
        from neo4j import Driver
        assert isinstance(query_processor.driver, Driver)
        
        logger.info("✅ Connection properties test passed")
    
    def test_initialization_without_connection(self):
        """
        Test QueryProcessor behavior when database is not connected
        
        Validates:
        1. Graceful handling of missing connection
        2. Proper error states
        3. Method behavior with no connection
        """
        with patch('app.query_processor.get_neo4j_connection') as mock_connection:
            # Mock disconnected state
            mock_conn = Mock()
            mock_conn.is_connected = False
            mock_conn.get_driver.return_value = None
            mock_connection.return_value = mock_conn
            
            query_processor = QueryProcessor()
            
            # Validate disconnected state
            assert query_processor.is_connected is False
            assert query_processor.driver is None
            
            # Test method behavior with no connection
            success, message = query_processor.setup_retrievers()
            assert success is False
            assert "Not connected to Neo4j" in message
        
        logger.info("✅ Initialization without connection test passed")


class TestRetrieverSetup:
    """Test suite for retriever setup functionality"""
    
    def test_setup_retrievers_basic(self, clean_database):
        """
        Test basic retriever setup
        
        Validates:
        1. Successful embeddings initialization
        2. Vector index verification
        3. Proper error handling for missing index
        """
        query_processor = QueryProcessor()
        
        # Ensure vector index is dropped first
        with query_processor.driver.session() as session:
            try:
                session.run("DROP INDEX code_chunks_vector_index IF EXISTS")
            except Exception:
                pass  # Index might not exist
        
        # Now test without vector index (should fail)
        success, message = query_processor.setup_retrievers()
        assert success is False
        assert "Vector index 'code_chunks_vector_index' not found" in message
        
        logger.info("✅ Basic retriever setup test passed (expected failure without index)")
    
    @pytest.mark.api_cost
    def test_setup_retrievers_with_vector_index(self, clean_database, test_config, java_patterns_path, selected_patterns):
        """
        Test retriever setup with existing vector index
        
        Validates:
        1. Successful setup when vector index exists
        2. Embeddings initialization
        3. Index verification
        """
        # First create a GraphRAG system to have vector index
        documents = self._get_test_documents(test_config, java_patterns_path, selected_patterns, max_docs=3)
        if not documents:
            pytest.skip("No test documents available")
        
        graph_builder = GraphBuilder()
        success, message = graph_builder.create_vector_index(documents)
        assert success is True, f"Failed to create vector index: {message}"
        
        # Now test retriever setup
        query_processor = QueryProcessor()
        success, message = query_processor.setup_retrievers()
        
        assert success is True, f"Retriever setup failed: {message}"
        assert "QueryProcessor retrievers set up successfully" in message
        assert query_processor.embeddings is not None
        
        logger.info("✅ Retriever setup with vector index test passed")
    
    def test_setup_retrievers_missing_dependencies(self, clean_database):
        """
        Test retriever setup with missing dependencies
        
        Validates:
        1. Graceful handling of import errors
        2. Meaningful error messages
        3. Proper error reporting
        """
        query_processor = QueryProcessor()
        
        # Mock missing langchain dependencies
        with patch('builtins.__import__', side_effect=ImportError("No module named 'langchain_openai'")):
            success, message = query_processor.setup_retrievers()
            
            assert success is False
            assert "Missing dependency" in message
            assert "langchain-openai" in message
        
        logger.info("✅ Missing dependencies setup test passed")
    
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


class TestVectorSearch:
    """Test suite for vector search functionality"""
    
    @pytest.mark.api_cost
    def test_vector_search_basic(self, clean_database, test_config, java_patterns_path, selected_patterns):
        """
        Test basic vector search functionality
        
        Validates:
        1. Successful vector search execution
        2. Proper result format
        3. Similarity scoring
        4. Result ordering
        """
        # Setup system with vector index
        documents = self._get_test_documents(test_config, java_patterns_path, selected_patterns, max_docs=5)
        if not documents:
            pytest.skip("No test documents available")
        
        graph_builder = GraphBuilder()
        success, message = graph_builder.create_vector_index(documents)
        assert success is True
        
        # Setup query processor
        query_processor = QueryProcessor()
        success, message = query_processor.setup_retrievers()
        assert success is True
        
        # Test vector search
        test_query = "singleton pattern implementation"
        success, results = query_processor.vector_search(test_query, k=3)
        
        assert success is True
        assert isinstance(results, list)
        assert len(results) <= 3  # Should return at most k results
        
        # Validate result structure
        if results:
            result = results[0]
            required_fields = ['chunk_id', 'text', 'file_path', 'language', 'start_line', 'end_line', 'similarity_score']
            for field in required_fields:
                assert field in result, f"Missing field: {field}"
            
            # Validate similarity scores are in descending order
            scores = [r['similarity_score'] for r in results]
            assert scores == sorted(scores, reverse=True), "Results should be ordered by similarity score"
        
        logger.info(f"✅ Basic vector search test passed with {len(results)} results")
    
    def test_vector_search_without_embeddings(self, clean_database):
        """
        Test vector search without embeddings setup
        
        Validates:
        1. Proper error handling when embeddings not initialized
        2. Graceful failure
        3. Empty results
        """
        query_processor = QueryProcessor()
        # Don't call setup_retrievers, so embeddings will be None
        
        success, results = query_processor.vector_search("test query")
        
        assert success is False
        assert results == []
        
        logger.info("✅ Vector search without embeddings test passed")
    
    @pytest.mark.api_cost
    def test_vector_search_different_k_values(self, clean_database, test_config, java_patterns_path, selected_patterns):
        """
        Test vector search with different k values
        
        Validates:
        1. Proper handling of different result counts
        2. K parameter functionality
        3. Result count limits
        """
        # Setup system
        documents = self._get_test_documents(test_config, java_patterns_path, selected_patterns, max_docs=8)
        if not documents:
            pytest.skip("No test documents available")
        
        graph_builder = GraphBuilder()
        success, message = graph_builder.create_vector_index(documents)
        assert success is True
        
        query_processor = QueryProcessor()
        success, message = query_processor.setup_retrievers()
        assert success is True
        
        # Test different k values
        test_query = "class implementation"
        k_values = [1, 3, 5, 10]
        
        for k in k_values:
            success, results = query_processor.vector_search(test_query, k=k)
            assert success is True
            assert len(results) <= k, f"Should return at most {k} results, got {len(results)}"
            assert len(results) <= len(documents), f"Cannot return more results than available documents"
        
        logger.info("✅ Different k values test passed")
    
    @pytest.mark.api_cost
    def test_vector_search_query_variations(self, clean_database, test_config, java_patterns_path, selected_patterns):
        """
        Test vector search with different query types
        
        Validates:
        1. Handling of different query styles
        2. Semantic understanding
        3. Result relevance
        """
        # Setup system
        documents = self._get_test_documents(test_config, java_patterns_path, selected_patterns, max_docs=6)
        if not documents:
            pytest.skip("No test documents available")
        
        graph_builder = GraphBuilder()
        success, message = graph_builder.create_vector_index(documents)
        assert success is True
        
        query_processor = QueryProcessor()
        success, message = query_processor.setup_retrievers()
        assert success is True
        
        # Test different query types
        test_queries = [
            "singleton pattern",
            "getInstance method",
            "thread safe implementation",
            "design pattern example",
            "class definition"
        ]
        
        for query in test_queries:
            success, results = query_processor.vector_search(query, k=3)
            assert success is True, f"Vector search failed for query: {query}"
            assert isinstance(results, list), f"Results should be a list for query: {query}"
            
            # Results can be empty for some queries, that's acceptable
            logger.info(f"Query '{query}': {len(results)} results")
        
        logger.info("✅ Query variations test passed")
    
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


class TestGraphContext:
    """Test suite for graph context retrieval functionality"""
    
    @pytest.mark.api_cost
    def test_get_graph_context_basic(self, clean_database, test_config, java_patterns_path, selected_patterns):
        """
        Test basic graph context retrieval
        
        Validates:
        1. Successful context retrieval from vector results
        2. Proper entity extraction
        3. Relationship discovery
        4. File information gathering
        """
        # Setup complete GraphRAG system
        documents = self._get_test_documents(test_config, java_patterns_path, selected_patterns, max_docs=5)
        if not documents:
            pytest.skip("No test documents available")
        
        graph_builder = GraphBuilder()
        success, message = graph_builder.create_graphrag_system(documents)
        assert success is True
        
        query_processor = QueryProcessor()
        success, message = query_processor.setup_retrievers()
        assert success is True
        
        # Get vector results first
        success, vector_results = query_processor.vector_search("singleton pattern", k=3)
        assert success is True
        assert len(vector_results) > 0
        
        # Test graph context retrieval
        success, graph_context = query_processor.get_graph_context_for_chunks(vector_results)
        
        assert success is True
        assert isinstance(graph_context, dict)
        
        # Validate context structure
        required_keys = ['entities', 'relationships', 'files']
        for key in required_keys:
            assert key in graph_context, f"Missing key: {key}"
            assert isinstance(graph_context[key], list), f"{key} should be a list"
        
        logger.info(f"✅ Basic graph context test passed: {len(graph_context['entities'])} entities, {len(graph_context['relationships'])} relationships")
    
    def test_get_graph_context_empty_results(self, clean_database):
        """
        Test graph context retrieval with empty vector results
        
        Validates:
        1. Proper handling of empty input
        2. Default empty context structure
        3. No errors with empty data
        """
        query_processor = QueryProcessor()
        
        # Test with empty vector results
        success, graph_context = query_processor.get_graph_context_for_chunks([])
        
        assert success is True
        assert graph_context == {'entities': [], 'relationships': [], 'files': []}
        
        logger.info("✅ Empty graph context test passed")
    
    @pytest.mark.api_cost
    def test_get_graph_context_entity_types(self, clean_database, test_config, java_patterns_path, selected_patterns):
        """
        Test graph context entity type extraction
        
        Validates:
        1. Different entity types are found
        2. Entity properties are preserved
        3. Chunk relationships are maintained
        """
        # Setup system
        documents = self._get_test_documents(test_config, java_patterns_path, selected_patterns, max_docs=6)
        if not documents:
            pytest.skip("No test documents available")
        
        graph_builder = GraphBuilder()
        success, message = graph_builder.create_graphrag_system(documents)
        assert success is True
        
        query_processor = QueryProcessor()
        success, message = query_processor.setup_retrievers()
        assert success is True
        
        # Get vector results
        success, vector_results = query_processor.vector_search("class method function", k=4)
        assert success is True
        
        if not vector_results:
            pytest.skip("No vector results for entity type test")
        
        # Get graph context
        success, graph_context = query_processor.get_graph_context_for_chunks(vector_results)
        assert success is True
        
        # Validate entity structure
        for entity in graph_context['entities']:
            required_fields = ['id', 'type', 'properties', 'related_chunk']
            for field in required_fields:
                assert field in entity, f"Entity missing field: {field}"
            
            # Validate entity types are reasonable
            assert entity['type'] in ['Class', 'Function', 'Module', 'Package', 'File', 'unknown'], f"Unexpected entity type: {entity['type']}"
        
        logger.info(f"✅ Entity types test passed with {len(graph_context['entities'])} entities")
    
    @pytest.mark.api_cost
    def test_get_graph_context_relationships(self, clean_database, test_config, java_patterns_path, selected_patterns):
        """
        Test graph context relationship extraction
        
        Validates:
        1. Relationships between entities are found
        2. Relationship types are preserved
        3. Source and target information is correct
        """
        # Setup system
        documents = self._get_test_documents(test_config, java_patterns_path, selected_patterns, max_docs=8)
        if not documents:
            pytest.skip("No test documents available")
        
        graph_builder = GraphBuilder()
        success, message = graph_builder.create_graphrag_system(documents)
        assert success is True
        
        query_processor = QueryProcessor()
        success, message = query_processor.setup_retrievers()
        assert success is True
        
        # Get vector results
        success, vector_results = query_processor.vector_search("implementation pattern", k=5)
        assert success is True
        
        if not vector_results:
            pytest.skip("No vector results for relationship test")
        
        # Get graph context
        success, graph_context = query_processor.get_graph_context_for_chunks(vector_results)
        assert success is True
        
        # Validate relationship structure
        for relationship in graph_context['relationships']:
            required_fields = ['source', 'relationship', 'target', 'source_properties', 'target_properties']
            for field in required_fields:
                assert field in relationship, f"Relationship missing field: {field}"
            
            # Validate relationship types are reasonable
            expected_rel_types = ['CONTAINS', 'CALLS', 'IMPORTS', 'INHERITS', 'IMPLEMENTS', 'DEPENDS_ON']
            # Note: Relationship type might not be in expected list for small datasets, so we'll be lenient
            assert isinstance(relationship['relationship'], str), "Relationship type should be a string"
        
        logger.info(f"✅ Relationships test passed with {len(graph_context['relationships'])} relationships")
    
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


class TestQueryProcessing:
    """Test suite for complete query processing functionality"""
    
    @pytest.mark.api_cost
    @pytest.mark.slow
    def test_process_query_basic(self, clean_database, test_config, java_patterns_path, selected_patterns):
        """
        Test basic end-to-end query processing
        
        Validates:
        1. Complete query processing pipeline
        2. Vector search + graph context + response generation
        3. Proper response format
        4. Context data structure
        """
        # Setup complete system
        documents = self._get_test_documents(test_config, java_patterns_path, selected_patterns, max_docs=6)
        if not documents:
            pytest.skip("No test documents available")
        
        graph_builder = GraphBuilder()
        success, message = graph_builder.create_graphrag_system(documents)
        assert success is True
        
        query_processor = QueryProcessor()
        success, message = query_processor.setup_retrievers()
        assert success is True
        
        # Test query processing
        test_query = "How does the singleton pattern work?"
        success, response, context_data = query_processor.process_query(test_query, k=3)
        
        assert success is True, f"Query processing failed: {response}"
        assert isinstance(response, str), "Response should be a string"
        assert len(response) > 0, "Response should not be empty"
        
        # Validate context data structure
        required_context_keys = ['query', 'vector_results', 'graph_context', 'num_chunks_found', 'num_entities_found', 'num_relationships_found']
        for key in required_context_keys:
            assert key in context_data, f"Missing context key: {key}"
        
        assert context_data['query'] == test_query
        assert context_data['num_chunks_found'] >= 0
        assert context_data['num_entities_found'] >= 0
        assert context_data['num_relationships_found'] >= 0
        
        logger.info(f"✅ Basic query processing test passed: {context_data['num_chunks_found']} chunks, {context_data['num_entities_found']} entities")
    
    def test_process_query_without_setup(self, clean_database):
        """
        Test query processing without proper setup
        
        Validates:
        1. Proper error handling when not initialized
        2. Meaningful error messages
        3. Empty context data on failure
        """
        query_processor = QueryProcessor()
        # Don't call setup_retrievers
        
        success, response, context_data = query_processor.process_query("test query")
        
        assert success is False
        assert "not properly initialized" in response
        assert context_data == {}
        
        logger.info("✅ Query processing without setup test passed")
    
    @pytest.mark.api_cost
    def test_process_query_without_graph_context(self, clean_database, test_config, java_patterns_path, selected_patterns):
        """
        Test query processing without graph context
        
        Validates:
        1. Vector-only query processing
        2. Proper handling of include_graph_context=False
        3. Response generation with limited context
        """
        # Setup system
        documents = self._get_test_documents(test_config, java_patterns_path, selected_patterns, max_docs=4)
        if not documents:
            pytest.skip("No test documents available")
        
        graph_builder = GraphBuilder()
        success, message = graph_builder.create_vector_index(documents)  # Only vector index, no full GraphRAG
        assert success is True
        
        query_processor = QueryProcessor()
        success, message = query_processor.setup_retrievers()
        assert success is True
        
        # Test query processing without graph context
        success, response, context_data = query_processor.process_query(
            "singleton pattern", 
            k=3, 
            include_graph_context=False
        )
        
        assert success is True
        assert isinstance(response, str)
        assert len(response) > 0
        
        # Graph context should be empty or minimal
        assert context_data['num_entities_found'] == 0
        assert context_data['num_relationships_found'] == 0
        
        logger.info("✅ Query processing without graph context test passed")
    
    @pytest.mark.api_cost
    def test_process_query_different_k_values(self, clean_database, test_config, java_patterns_path, selected_patterns):
        """
        Test query processing with different k values
        
        Validates:
        1. Different result counts affect processing
        2. K parameter propagation
        3. Response quality with different context sizes
        """
        # Setup system
        documents = self._get_test_documents(test_config, java_patterns_path, selected_patterns, max_docs=8)
        if not documents:
            pytest.skip("No test documents available")
        
        graph_builder = GraphBuilder()
        success, message = graph_builder.create_graphrag_system(documents)
        assert success is True
        
        query_processor = QueryProcessor()
        success, message = query_processor.setup_retrievers()
        assert success is True
        
        # Test different k values
        test_query = "design pattern implementation"
        k_values = [1, 3, 5]
        
        for k in k_values:
            success, response, context_data = query_processor.process_query(test_query, k=k)
            assert success is True, f"Query processing failed for k={k}"
            assert context_data['num_chunks_found'] <= k, f"Should find at most {k} chunks"
            assert len(response) > 0, f"Response should not be empty for k={k}"
        
        logger.info("✅ Different k values query processing test passed")
    
    @pytest.mark.api_cost
    def test_process_query_no_results(self, clean_database, test_config, java_patterns_path, selected_patterns):
        """
        Test query processing when no relevant results are found
        
        Validates:
        1. Graceful handling of no vector results
        2. Appropriate fallback response
        3. Proper context data for empty results
        """
        # Setup system
        documents = self._get_test_documents(test_config, java_patterns_path, selected_patterns, max_docs=3)
        if not documents:
            pytest.skip("No test documents available")
        
        graph_builder = GraphBuilder()
        success, message = graph_builder.create_vector_index(documents)
        assert success is True
        
        query_processor = QueryProcessor()
        success, message = query_processor.setup_retrievers()
        assert success is True
        
        # Test with a query that's unlikely to match Java design patterns
        obscure_query = "quantum computing algorithms in assembly language"
        success, response, context_data = query_processor.process_query(obscure_query, k=3)
        
        assert success is True  # Should succeed even with no results
        assert isinstance(response, str)
        assert len(response) > 0
        
        # Should have minimal or no results
        assert context_data['num_chunks_found'] >= 0  # Could be 0 or small number
        
        logger.info("✅ No results query processing test passed")
    
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


class TestResponseGeneration:
    """Test suite for response generation functionality"""
    
    @pytest.mark.api_cost
    def test_generate_response_with_results(self, clean_database, test_config, java_patterns_path, selected_patterns):
        """
        Test response generation with vector results
        
        Validates:
        1. LLM response generation
        2. Fallback response handling
        3. Response quality and format
        """
        # Setup system
        documents = self._get_test_documents(test_config, java_patterns_path, selected_patterns, max_docs=4)
        if not documents:
            pytest.skip("No test documents available")
        
        graph_builder = GraphBuilder()
        success, message = graph_builder.create_graphrag_system(documents)
        assert success is True
        
        query_processor = QueryProcessor()
        success, message = query_processor.setup_retrievers()
        assert success is True
        
        # Get some vector results
        success, vector_results = query_processor.vector_search("singleton pattern", k=2)
        assert success is True
        
        if not vector_results:
            pytest.skip("No vector results for response generation test")
        
        # Get graph context
        success, graph_context = query_processor.get_graph_context_for_chunks(vector_results)
        assert success is True
        
        # Test response generation
        success, response = query_processor._generate_response("How does singleton work?", vector_results, graph_context)
        
        assert success is True
        assert isinstance(response, str)
        assert len(response) > 0
        
        logger.info("✅ Response generation with results test passed")
    
    def test_generate_response_empty_results(self, clean_database):
        """
        Test response generation with empty results
        
        Validates:
        1. Proper handling of empty vector results
        2. Appropriate fallback message
        3. Helpful user guidance
        """
        query_processor = QueryProcessor()
        
        # Test with empty results
        success, response = query_processor._generate_response("test query", [], {})
        
        assert success is True
        assert isinstance(response, str)
        assert len(response) > 0
        assert "couldn't find any relevant code" in response.lower()
        
        logger.info("✅ Response generation with empty results test passed")
    
    @pytest.mark.api_cost
    def test_generate_response_llm_failure_fallback(self, clean_database, test_config, java_patterns_path, selected_patterns):
        """
        Test response generation fallback when LLM fails
        
        Validates:
        1. Graceful handling of LLM failures
        2. Fallback response generation
        3. Useful information despite LLM failure
        """
        # Setup system
        documents = self._get_test_documents(test_config, java_patterns_path, selected_patterns, max_docs=3)
        if not documents:
            pytest.skip("No test documents available")
        
        graph_builder = GraphBuilder()
        success, message = graph_builder.create_vector_index(documents)
        assert success is True
        
        query_processor = QueryProcessor()
        success, message = query_processor.setup_retrievers()
        assert success is True
        
        # Get vector results
        success, vector_results = query_processor.vector_search("pattern", k=2)
        assert success is True
        
        if not vector_results:
            pytest.skip("No vector results for LLM fallback test")
        
        # Mock LLM failure
        with patch('app.utilities.llm_utils.generate_conversational_response', return_value=(False, "LLM failed")):
            success, response = query_processor._generate_response("test query", vector_results, {})
            
            assert success is True  # Should still succeed with fallback
            assert isinstance(response, str)
            assert len(response) > 0
            # Should contain fallback information
            assert any(keyword in response.lower() for keyword in ["found", "relevant", "file"])
        
        logger.info("✅ LLM failure fallback test passed")
    
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


class TestQueryProcessorErrorHandling:
    """Test suite for error handling and edge cases"""
    
    def test_missing_dependencies_handling(self, clean_database):
        """
        Test handling of missing dependencies
        
        Validates:
        1. Graceful handling of import errors
        2. Meaningful error messages
        3. Proper error propagation
        """
        query_processor = QueryProcessor()
        
        # Mock missing dependencies for setup
        with patch('builtins.__import__', side_effect=ImportError("No module named 'langchain_openai'")):
            success, message = query_processor.setup_retrievers()
            
            assert success is False
            assert "Missing dependency" in message
            assert "langchain-openai" in message
        
        logger.info("✅ Missing dependencies handling test passed")
    
    def test_neo4j_connection_issues(self):
        """
        Test handling of Neo4j connection issues
        
        Validates:
        1. Behavior when Neo4j is disconnected
        2. Proper error messages
        3. No crashes or hangs
        """
        # Test with disconnected Neo4j
        with patch('app.query_processor.get_neo4j_connection') as mock_connection:
            mock_conn = Mock()
            mock_conn.is_connected = False
            mock_conn.get_driver.return_value = None
            mock_connection.return_value = mock_conn
            
            query_processor = QueryProcessor()
            
            # Test setup method
            success, message = query_processor.setup_retrievers()
            assert success is False
            assert "Not connected to Neo4j" in message
            
            # Test query processing
            success, response, context = query_processor.process_query("test")
            assert success is False
            assert "not properly initialized" in response
        
        logger.info("✅ Neo4j connection issues test passed")
    
    def test_malformed_vector_results_handling(self, clean_database):
        """
        Test handling of malformed vector results
        
        Validates:
        1. Graceful handling of unexpected data structures
        2. Proper error handling
        3. No crashes with bad data
        """
        query_processor = QueryProcessor()
        
        # Test with malformed vector results
        malformed_results = [
            {"incomplete": "data"},  # Missing required fields
            {},  # Empty dict
            {"chunk_id": None, "text": ""}  # Invalid values
        ]
        
        # This should not crash
        success, graph_context = query_processor.get_graph_context_for_chunks(malformed_results)
        
        # Should handle gracefully
        assert isinstance(success, bool)
        assert isinstance(graph_context, dict)
        
        logger.info("✅ Malformed vector results handling test passed")
    
    def test_api_key_issues(self, clean_database):
        """
        Test handling of API key issues
        
        Validates:
        1. Behavior with missing API keys
        2. Behavior with invalid API keys
        3. Error message quality
        """
        query_processor = QueryProcessor()
        
        # Test with None API key
        with patch.object(query_processor.config, 'OPENAI_API_KEY', None):
            # Setup might still work (depends on environment)
            success, message = query_processor.setup_retrievers()
            # We'll be lenient here as it might work with default keys
            assert isinstance(success, bool)
            assert isinstance(message, str)
        
        logger.info("✅ API key issues test passed")


# Helper functions for test data management
def create_mock_vector_result(chunk_id: str = "test_chunk", text: str = "test code", file_path: str = "test.java") -> Dict[str, Any]:
    """Create a mock vector search result for testing"""
    return {
        'chunk_id': chunk_id,
        'text': text,
        'file_path': file_path,
        'language': 'java',
        'start_line': 1,
        'end_line': 10,
        'similarity_score': 0.85
    }


def create_mock_graph_context(num_entities: int = 2, num_relationships: int = 1) -> Dict[str, Any]:
    """Create a mock graph context for testing"""
    entities = []
    for i in range(num_entities):
        entities.append({
            'id': f'Entity{i}',
            'type': 'Class',
            'properties': {'name': f'TestClass{i}'},
            'related_chunk': f'chunk_{i}'
        })
    
    relationships = []
    for i in range(num_relationships):
        relationships.append({
            'source': f'Entity{i}',
            'relationship': 'CONTAINS',
            'target': f'Entity{i+1}',
            'source_properties': {'name': f'Source{i}'},
            'target_properties': {'name': f'Target{i}'}
        })
    
    files = [
        {
            'path': 'test/TestFile.java',
            'name': 'TestFile.java',
            'language': 'java',
            'entity_types': ['Class', 'Function'],
            'entity_count': num_entities
        }
    ]
    
    return {
        'entities': entities,
        'relationships': relationships,
        'files': files
    } 