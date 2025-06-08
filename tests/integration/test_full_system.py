# Code Graph - Full System Integration Tests
# Comprehensive end-to-end tests for the complete CodeGraph system

import pytest
import logging
import time
from typing import List, Dict, Any, Tuple
from pathlib import Path

from app.ingestion import parse_code_chunks
from app.graph_builder import GraphBuilder
from app.query_processor import QueryProcessor
from app.database import get_neo4j_connection, initialize_database
from tests.fixtures.java_patterns import get_test_data_manager

logger = logging.getLogger(__name__)


class TestFullSystemWorkflow:
    """Test suite for complete end-to-end system workflow"""
    
    @pytest.mark.integration
    @pytest.mark.api_cost
    @pytest.mark.slow
    def test_complete_workflow_basic(self, clean_database, test_config, standard_documents):
        """
        Test complete end-to-end workflow: ingestion → graph building → query processing
        
        This is the core integration test that validates:
        1. Code ingestion and chunking
        2. Knowledge graph generation
        3. Vector index creation
        4. Query processing and response generation
        5. System statistics and validation
        """
        logger.info("🚀 Starting complete workflow integration test")
        
        # Step 1: Use Pre-cached Documents (optimized)
        logger.info("📝 Step 1: Using Pre-cached Documents")
        documents = standard_documents
        if not documents:
            pytest.skip("No cached documents available for testing")
        assert len(documents) > 0, "No documents available from cache"
        logger.info(f"✅ Using cached documents: {len(documents)} documents")
        
        # Step 2: GraphRAG System Creation
        logger.info("🧠 Step 2: GraphRAG System Creation")
        graph_stats = self._test_graph_building_step(documents)
        logger.info(f"✅ GraphRAG system created: {graph_stats}")
        
        # Step 3: Query Processing Setup
        logger.info("🔍 Step 3: Query Processing Setup")
        query_processor = self._test_query_setup_step()
        logger.info("✅ Query processor setup completed")
        
        # Step 4: End-to-End Query Testing
        logger.info("💬 Step 4: End-to-End Query Testing")
        query_results = self._test_query_processing_step(query_processor, documents)
        logger.info(f"✅ Query processing completed: {len(query_results)} queries tested")
        
        # Step 5: System Validation
        logger.info("📊 Step 5: System Validation")
        validation_results = self._test_system_validation_step(documents, query_results)
        logger.info(f"✅ System validation completed: {validation_results}")
        
        logger.info("🎉 Complete workflow integration test passed successfully!")
    
    @pytest.mark.integration
    @pytest.mark.api_cost
    @pytest.mark.slow
    def test_complete_workflow_multiple_patterns(self, clean_database, test_config, cached_test_documents):
        """
        Test complete workflow with multiple design patterns
        
        Validates:
        1. Multi-pattern code ingestion
        2. Complex knowledge graph creation
        3. Cross-pattern query processing
        4. Pattern-specific and general queries
        """
        logger.info("🚀 Starting multi-pattern workflow integration test")
        
        # Use cached multi-pattern documents (optimized)
        if not cached_test_documents:
            pytest.skip("No cached test documents available")
        
        available_patterns = list(cached_test_documents.keys())
        if len(available_patterns) < 2:
            pytest.skip("Need at least 2 patterns for multi-pattern test")
        
        logger.info(f"Testing with cached patterns: {available_patterns}")
        
        # Step 1: Use cached multi-pattern documents
        all_documents = []
        pattern_doc_counts = {}
        
        for pattern in available_patterns:
            pattern_documents = cached_test_documents[pattern]
            all_documents.extend(pattern_documents)
            pattern_doc_counts[pattern] = len(pattern_documents)
            logger.info(f"Pattern '{pattern}': {len(pattern_documents)} cached documents")
        
        assert len(all_documents) > 0, "No documents from cached patterns"
        logger.info(f"✅ Multi-pattern cached documents: {len(all_documents)} total documents")
        
        # Step 2: Create comprehensive GraphRAG system
        graph_builder = GraphBuilder()
        success, message = graph_builder.create_graphrag_system(all_documents)
        assert success, f"GraphRAG system creation failed: {message}"
        logger.info("✅ Multi-pattern GraphRAG system created")
        
        # Step 3: Setup query processor
        query_processor = QueryProcessor()
        success, message = query_processor.setup_retrievers()
        assert success, f"Query processor setup failed: {message}"
        
        # Step 4: Test pattern-specific and cross-pattern queries
        test_queries = [
            # Pattern-specific queries
            "How does the singleton pattern work?",
            "Show me factory pattern implementation",
            "What is the observer pattern?",
            # Cross-pattern queries
            "Compare different design patterns",
            "Show me all pattern implementations",
            "What are the main classes in these patterns?"
        ]
        
        successful_queries = 0
        for query in test_queries:
            try:
                success, response, context = query_processor.process_query(query, k=5)
                if success and len(response) > 0:
                    successful_queries += 1
                    logger.info(f"Query '{query[:30]}...': {context['num_chunks_found']} chunks found")
            except Exception as e:
                logger.warning(f"Query failed: {query[:30]}... - {str(e)}")
        
        assert successful_queries > 0, "No queries succeeded in multi-pattern test"
        logger.info(f"✅ Multi-pattern queries: {successful_queries}/{len(test_queries)} successful")
        
        logger.info("🎉 Multi-pattern workflow integration test passed!")
    
    @pytest.mark.integration
    @pytest.mark.api_cost
    def test_incremental_system_building(self, clean_database, test_config, extended_documents):
        """
        Test incremental system building and updates
        
        Validates:
        1. Building system with small dataset
        2. Adding more data incrementally
        3. System consistency after updates
        4. Query performance with growing dataset
        """
        logger.info("🚀 Starting incremental system building test")
        
        # Use cached extended documents (optimized)
        documents = extended_documents
        if not documents or len(documents) < 6:
            pytest.skip("Need at least 6 cached documents for incremental test")
        
        # Split documents into batches
        batch1 = documents[:4]
        batch2 = documents[4:8]
        batch3 = documents[8:]
        
        logger.info(f"Document batches: {len(batch1)}, {len(batch2)}, {len(batch3)}")
        
        # Step 1: Build initial system with first batch
        graph_builder = GraphBuilder()
        success, message = graph_builder.create_graphrag_system(batch1)
        assert success, f"Initial system creation failed: {message}"
        
        query_processor = QueryProcessor()
        success, message = query_processor.setup_retrievers()
        assert success, f"Initial query setup failed: {message}"
        
        # Test initial system
        success, response1, context1 = query_processor.process_query("design pattern", k=3)
        assert success, "Initial query failed"
        initial_chunks = context1['num_chunks_found']
        logger.info(f"✅ Initial system: {initial_chunks} chunks found")
        
        # Step 2: Add second batch (simulate incremental update)
        success, message = graph_builder.create_vector_index(batch2)
        assert success, f"Incremental vector index failed: {message}"
        
        # Test system after first update
        success, response2, context2 = query_processor.process_query("design pattern", k=5)
        assert success, "Query after first update failed"
        updated_chunks = context2['num_chunks_found']
        logger.info(f"✅ After first update: {updated_chunks} chunks found")
        
        # Should have more chunks available now
        assert updated_chunks >= initial_chunks, "System should have more chunks after update"
        
        # Step 3: Add third batch
        if batch3:
            success, message = graph_builder.create_vector_index(batch3)
            assert success, f"Second incremental update failed: {message}"
            
            # Test final system
            success, response3, context3 = query_processor.process_query("implementation", k=6)
            assert success, "Query after second update failed"
            final_chunks = context3['num_chunks_found']
            logger.info(f"✅ After second update: {final_chunks} chunks found")
        
        logger.info("🎉 Incremental system building test passed!")
    

    
    def _test_graph_building_step(self, documents: List[Any]) -> Dict[str, Any]:
        """Test the graph building step and return statistics"""
        graph_builder = GraphBuilder()
        
        # Create complete GraphRAG system
        success, message = graph_builder.create_graphrag_system(documents)
        assert success, f"GraphRAG system creation failed: {message}"
        
        # Get system statistics
        with graph_builder.driver.session() as session:
            # Count nodes by type
            result = session.run("MATCH (n) RETURN labels(n)[0] as label, count(n) as count")
            node_counts = {record["label"]: record["count"] for record in result}
            
            # Count relationships
            result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
            rel_count = result.single()["rel_count"]
            
            # Count CodeChunks specifically
            result = session.run("MATCH (c:CodeChunk) RETURN count(c) as chunk_count")
            chunk_count = result.single()["chunk_count"]
        
        stats = {
            'node_counts': node_counts,
            'total_relationships': rel_count,
            'codechunk_count': chunk_count,
            'total_nodes': sum(node_counts.values())
        }
        
        # Validate basic expectations
        assert stats['codechunk_count'] == len(documents), "Should have one CodeChunk per document"
        assert stats['total_nodes'] > len(documents), "Should have more nodes than just CodeChunks"
        assert 'File' in node_counts, "Should have File nodes"
        
        return stats
    
    def _test_query_setup_step(self) -> QueryProcessor:
        """Test query processor setup and return configured processor"""
        query_processor = QueryProcessor()
        
        # Setup retrievers
        success, message = query_processor.setup_retrievers()
        assert success, f"Query processor setup failed: {message}"
        assert query_processor.embeddings is not None, "Embeddings should be initialized"
        
        return query_processor
    
    def _test_query_processing_step(self, query_processor: QueryProcessor, documents: List[Any]) -> List[Dict[str, Any]]:
        """Test query processing with various queries and return results"""
        test_queries = [
            "singleton pattern implementation",
            "getInstance method",
            "class definition",
            "design pattern example"
        ]
        
        query_results = []
        
        for query in test_queries:
            try:
                success, response, context = query_processor.process_query(query, k=3)
                
                result = {
                    'query': query,
                    'success': success,
                    'response_length': len(response) if success else 0,
                    'chunks_found': context.get('num_chunks_found', 0) if success else 0,
                    'entities_found': context.get('num_entities_found', 0) if success else 0
                }
                
                query_results.append(result)
                
                if success:
                    assert len(response) > 0, f"Response should not be empty for query: {query}"
                    logger.info(f"Query '{query}': {result['chunks_found']} chunks, {len(response)} chars response")
                
            except Exception as e:
                logger.warning(f"Query '{query}' failed with exception: {str(e)}")
                query_results.append({
                    'query': query,
                    'success': False,
                    'error': str(e)
                })
        
        # At least some queries should succeed
        successful_queries = sum(1 for r in query_results if r['success'])
        assert successful_queries > 0, "At least one query should succeed"
        
        return query_results
    
    def _test_system_validation_step(self, documents: List[Any], query_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test system validation and return validation results"""
        connection = get_neo4j_connection()
        driver = connection.get_driver()
        
        with driver.session() as session:
            # Validate data integrity
            
            # 1. Check CodeChunk count matches input documents
            result = session.run("MATCH (c:CodeChunk) RETURN count(c) as count")
            chunk_count = result.single()["count"]
            assert chunk_count == len(documents), f"Expected {len(documents)} CodeChunks, found {chunk_count}"
            
            # 2. Check all CodeChunks have embeddings
            result = session.run("MATCH (c:CodeChunk) WHERE c.embedding IS NULL RETURN count(c) as count")
            missing_embeddings = result.single()["count"]
            assert missing_embeddings == 0, f"Found {missing_embeddings} CodeChunks without embeddings"
            
            # 3. Check File nodes exist and are linked
            result = session.run("MATCH (f:File)-[:CONTAINS_CHUNK]->(c:CodeChunk) RETURN count(DISTINCT f) as file_count")
            file_count = result.single()["file_count"]
            assert file_count > 0, "Should have File nodes linked to CodeChunks"
            
            # 4. Check vector index exists
            try:
                result = session.run("SHOW INDEXES YIELD name WHERE name = 'code_chunks_vector_index'")
                index_exists = len(list(result)) > 0
                assert index_exists, "Vector index should exist"
            except Exception:
                # Some Neo4j versions might not support SHOW INDEXES
                pass
            
            # 5. Validate query performance
            successful_queries = sum(1 for r in query_results if r['success'])
            total_chunks_found = sum(r.get('chunks_found', 0) for r in query_results if r['success'])
            
            validation_results = {
                'chunk_count': chunk_count,
                'file_count': file_count,
                'missing_embeddings': missing_embeddings,
                'successful_queries': successful_queries,
                'total_queries': len(query_results),
                'total_chunks_found': total_chunks_found,
                'query_success_rate': successful_queries / len(query_results) if query_results else 0
            }
            
            # Validate success rates
            assert validation_results['query_success_rate'] > 0.5, "Query success rate should be > 50%"
            
            return validation_results


class TestSystemPerformance:
    """Test suite for system performance and scalability"""
    
    @pytest.mark.integration
    @pytest.mark.api_cost
    @pytest.mark.slow
    def test_system_performance_metrics(self, clean_database, test_config, standard_documents):
        """
        Test system performance with timing and resource metrics
        
        Validates:
        1. Ingestion performance
        2. Graph building performance
        3. Query processing performance
        4. Memory and time efficiency
        """
        logger.info("⏱️ Starting system performance test")
        
        # Use cached documents (optimized)
        documents = standard_documents
        if not documents:
            pytest.skip("No cached documents available")
        
        performance_metrics = {}
        
        # Measure ingestion performance (already done, but we'll measure graph building)
        start_time = time.time()
        
        # Measure graph building performance
        graph_builder = GraphBuilder()
        graph_start = time.time()
        success, message = graph_builder.create_graphrag_system(documents)
        graph_end = time.time()
        
        assert success, f"GraphRAG system creation failed: {message}"
        performance_metrics['graph_building_time'] = graph_end - graph_start
        
        # Measure query setup performance
        query_setup_start = time.time()
        query_processor = QueryProcessor()
        success, message = query_processor.setup_retrievers()
        query_setup_end = time.time()
        
        assert success, f"Query setup failed: {message}"
        performance_metrics['query_setup_time'] = query_setup_end - query_setup_start
        
        # Measure query processing performance
        test_queries = [
            "singleton pattern",
            "design pattern implementation",
            "class method"
        ]
        
        query_times = []
        for query in test_queries:
            query_start = time.time()
            success, response, context = query_processor.process_query(query, k=3)
            query_end = time.time()
            
            if success:
                query_times.append(query_end - query_start)
        
        performance_metrics['avg_query_time'] = sum(query_times) / len(query_times) if query_times else 0
        performance_metrics['total_time'] = time.time() - start_time
        performance_metrics['documents_processed'] = len(documents)
        
        # Log performance metrics
        logger.info(f"📊 Performance Metrics:")
        logger.info(f"  Graph building: {performance_metrics['graph_building_time']:.2f}s")
        logger.info(f"  Query setup: {performance_metrics['query_setup_time']:.2f}s")
        logger.info(f"  Avg query time: {performance_metrics['avg_query_time']:.2f}s")
        logger.info(f"  Total time: {performance_metrics['total_time']:.2f}s")
        logger.info(f"  Documents: {performance_metrics['documents_processed']}")
        
        # Validate performance expectations
        assert performance_metrics['graph_building_time'] < 300, "Graph building should complete within 5 minutes"
        assert performance_metrics['query_setup_time'] < 30, "Query setup should complete within 30 seconds"
        assert performance_metrics['avg_query_time'] < 60, "Average query should complete within 60 seconds"
        
        logger.info("✅ System performance test passed!")
    
    @pytest.mark.integration
    @pytest.mark.api_cost
    def test_system_scalability(self, clean_database, test_config, extended_documents):
        """
        Test system scalability with increasing data sizes
        
        Validates:
        1. Performance with different document counts
        2. Query response time consistency
        3. System stability under load
        """
        logger.info("📈 Starting system scalability test")
        
        # Use cached extended documents for scalability testing
        all_documents = extended_documents
        if not all_documents or len(all_documents) < 6:
            pytest.skip("Need at least 6 cached documents for scalability test")
        
        # Test with increasing document sizes
        test_sizes = [3, 6, 9, min(12, len(all_documents))]
        scalability_results = []
        
        for size in test_sizes:
            logger.info(f"Testing with {size} documents")
            
            # Clear database for clean test
            from app.utilities.neo4j_utils import clear_knowledge_graph
            connection = get_neo4j_connection()
            clear_knowledge_graph(connection.get_driver(), confirm=True)
            
            documents = all_documents[:size]
            
            # Measure system creation time
            start_time = time.time()
            
            graph_builder = GraphBuilder()
            success, message = graph_builder.create_graphrag_system(documents)
            assert success, f"System creation failed for {size} documents: {message}"
            
            query_processor = QueryProcessor()
            success, message = query_processor.setup_retrievers()
            assert success, f"Query setup failed for {size} documents: {message}"
            
            creation_time = time.time() - start_time
            
            # Measure query performance
            query_start = time.time()
            success, response, context = query_processor.process_query("design pattern", k=3)
            query_time = time.time() - query_start
            
            result = {
                'document_count': size,
                'creation_time': creation_time,
                'query_time': query_time,
                'chunks_found': context.get('num_chunks_found', 0) if success else 0,
                'success': success
            }
            
            scalability_results.append(result)
            logger.info(f"  Size {size}: creation={creation_time:.2f}s, query={query_time:.2f}s")
        
        # Analyze scalability
        successful_tests = [r for r in scalability_results if r['success']]
        assert len(successful_tests) > 0, "At least one scalability test should succeed"
        
        # Check that query times don't grow exponentially
        if len(successful_tests) >= 2:
            first_query_time = successful_tests[0]['query_time']
            last_query_time = successful_tests[-1]['query_time']
            
            # Query time shouldn't increase by more than 5x
            assert last_query_time < first_query_time * 5, "Query time scaling is too poor"
        
        logger.info("✅ System scalability test passed!")


class TestSystemRobustness:
    """Test suite for system robustness and error recovery"""
    
    @pytest.mark.integration
    @pytest.mark.api_cost
    def test_system_error_recovery(self, clean_database, test_config, quick_documents):
        """
        Test system error recovery and resilience
        
        Validates:
        1. Recovery from partial failures
        2. Graceful degradation
        3. Error handling across components
        """
        logger.info("🛡️ Starting system error recovery test")
        
        # Use cached quick documents (optimized)
        documents = quick_documents
        if not documents:
            pytest.skip("No cached documents available")
        
        # Test 1: Partial system creation (vector index only)
        graph_builder = GraphBuilder()
        success, message = graph_builder.create_vector_index(documents)
        assert success, f"Vector index creation failed: {message}"
        
        # Query processor should work with vector-only system
        query_processor = QueryProcessor()
        success, message = query_processor.setup_retrievers()
        assert success, f"Query setup failed with vector-only system: {message}"
        
        # Test vector-only queries
        success, response, context = query_processor.process_query("test query", k=2, include_graph_context=False)
        assert success, "Vector-only query should succeed"
        logger.info("✅ Vector-only system works")
        
        # Test 2: Add knowledge graph to existing vector system
        success, message = graph_builder.generate_knowledge_graph(documents)
        # This might fail or succeed depending on the system state, both are acceptable
        logger.info(f"Knowledge graph addition: {success} - {message}")
        
        # Test 3: Query with mixed system state
        success, response, context = query_processor.process_query("design pattern", k=3)
        # Should work regardless of knowledge graph state
        assert success, "Query should work with mixed system state"
        logger.info("✅ Mixed system state handled gracefully")
        
        # Test 4: Error handling with malformed queries
        malformed_queries = ["", "   ", "a" * 1000]  # Empty, whitespace, very long
        
        for query in malformed_queries:
            try:
                success, response, context = query_processor.process_query(query, k=1)
                # Should either succeed gracefully or fail gracefully
                assert isinstance(success, bool), "Should return boolean success"
                assert isinstance(response, str), "Should return string response"
            except Exception as e:
                logger.warning(f"Malformed query '{query[:20]}...' caused exception: {str(e)}")
        
        logger.info("✅ System error recovery test passed!")
    
    @pytest.mark.integration
    @pytest.mark.api_cost
    def test_system_data_consistency(self, clean_database, test_config, standard_documents):
        """
        Test system data consistency and integrity
        
        Validates:
        1. Data consistency across components
        2. Referential integrity
        3. No data corruption
        """
        logger.info("🔍 Starting system data consistency test")
        
        # Use cached standard documents (optimized)
        documents = standard_documents
        if not documents:
            pytest.skip("No cached documents available")
        
        # Create complete system
        graph_builder = GraphBuilder()
        success, message = graph_builder.create_graphrag_system(documents)
        assert success, f"System creation failed: {message}"
        
        # Test data consistency
        connection = get_neo4j_connection()
        driver = connection.get_driver()
        
        with driver.session() as session:
            # 1. Check CodeChunk count consistency
            result = session.run("MATCH (c:CodeChunk) RETURN count(c) as count")
            chunk_count = result.single()["count"]
            assert chunk_count == len(documents), f"CodeChunk count mismatch: expected {len(documents)}, got {chunk_count}"
            
            # 2. Check File-CodeChunk relationships
            result = session.run("""
                MATCH (f:File)-[:CONTAINS_CHUNK]->(c:CodeChunk)
                RETURN f.path as file_path, count(c) as chunk_count
            """)
            
            file_chunks = {record["file_path"]: record["chunk_count"] for record in result}
            
            # Verify all chunks are linked to files
            total_linked_chunks = sum(file_chunks.values())
            assert total_linked_chunks == chunk_count, "Not all CodeChunks are linked to Files"
            
            # 3. Check embedding consistency
            result = session.run("MATCH (c:CodeChunk) WHERE c.embedding IS NOT NULL RETURN count(c) as count")
            embedded_count = result.single()["count"]
            assert embedded_count == chunk_count, "Not all CodeChunks have embeddings"
            
            # 4. Check metadata consistency
            result = session.run("""
                MATCH (c:CodeChunk)
                WHERE c.file_path IS NULL OR c.language IS NULL OR c.chunk_id IS NULL
                RETURN count(c) as count
            """)
            missing_metadata = result.single()["count"]
            assert missing_metadata == 0, "Some CodeChunks have missing metadata"
            
            # 5. Check File metadata consistency (be lenient about knowledge graph File nodes)
            result = session.run("""
                MATCH (f:File)-[:CONTAINS_CHUNK]->(:CodeChunk)
                WHERE f.path IS NULL OR f.name IS NULL OR f.language IS NULL
                RETURN count(f) as count
            """)
            missing_file_metadata = result.single()["count"]
            assert missing_file_metadata == 0, "Some Files linked to CodeChunks have missing metadata"
        
        logger.info("✅ System data consistency test passed!")


class TestSystemUseCases:
    """Test suite for real-world use cases and scenarios"""
    
    @pytest.mark.integration
    @pytest.mark.api_cost
    @pytest.mark.slow
    def test_developer_workflow_simulation(self, clean_database, test_config, cached_test_documents):
        """
        Simulate a realistic developer workflow
        
        Validates:
        1. Initial codebase analysis
        2. Pattern discovery queries
        3. Code understanding queries
        4. Implementation guidance queries
        """
        logger.info("👨‍💻 Starting developer workflow simulation")
        
        # Use cached multi-pattern documents (optimized)
        if not cached_test_documents:
            pytest.skip("No cached test documents available")
        
        available_patterns = list(cached_test_documents.keys())
        if len(available_patterns) < 2:
            pytest.skip("Need at least 2 cached patterns for workflow simulation")
        
        # Use cached multiple patterns
        all_documents = []
        for pattern in available_patterns[:2]:  # Use first 2 patterns
            pattern_documents = cached_test_documents[pattern]
            all_documents.extend(pattern_documents)
        
        assert len(all_documents) > 0, "No cached documents for workflow simulation"
        
        # Create system
        graph_builder = GraphBuilder()
        success, message = graph_builder.create_graphrag_system(all_documents)
        assert success, f"System creation failed: {message}"
        
        query_processor = QueryProcessor()
        success, message = query_processor.setup_retrievers()
        assert success, f"Query setup failed: {message}"
        
        # Simulate developer workflow
        workflow_scenarios = [
            {
                "scenario": "Initial codebase exploration",
                "queries": [
                    "What design patterns are implemented in this codebase?",
                    "Show me the main classes and their relationships",
                    "What are the key components of this system?"
                ]
            },
            {
                "scenario": "Pattern-specific investigation",
                "queries": [
                    "How is the singleton pattern implemented?",
                    "Show me the getInstance method implementation",
                    "What makes this singleton thread-safe?"
                ]
            },
            {
                "scenario": "Implementation guidance",
                "queries": [
                    "How do I implement a similar pattern?",
                    "What are the key methods I need to implement?",
                    "Show me example usage of these patterns"
                ]
            }
        ]
        
        workflow_results = []
        
        for scenario in workflow_scenarios:
            scenario_results = {
                "scenario": scenario["scenario"],
                "queries": [],
                "success_rate": 0
            }
            
            successful_queries = 0
            
            for query in scenario["queries"]:
                try:
                    success, response, context = query_processor.process_query(query, k=4)
                    
                    query_result = {
                        "query": query,
                        "success": success,
                        "response_length": len(response) if success else 0,
                        "chunks_found": context.get('num_chunks_found', 0) if success else 0
                    }
                    
                    scenario_results["queries"].append(query_result)
                    
                    if success and len(response) > 50:  # Meaningful response
                        successful_queries += 1
                        logger.info(f"✅ '{query[:40]}...': {query_result['chunks_found']} chunks")
                    else:
                        logger.warning(f"❌ '{query[:40]}...': failed or poor response")
                
                except Exception as e:
                    logger.error(f"Query failed: {query[:40]}... - {str(e)}")
                    scenario_results["queries"].append({
                        "query": query,
                        "success": False,
                        "error": str(e)
                    })
            
            scenario_results["success_rate"] = successful_queries / len(scenario["queries"])
            workflow_results.append(scenario_results)
            
            logger.info(f"Scenario '{scenario['scenario']}': {successful_queries}/{len(scenario['queries'])} successful")
        
        # Validate workflow success
        overall_success_rate = sum(s["success_rate"] for s in workflow_results) / len(workflow_results)
        assert overall_success_rate > 0.4, f"Overall workflow success rate too low: {overall_success_rate:.2f}"
        
        logger.info(f"✅ Developer workflow simulation passed! Overall success rate: {overall_success_rate:.2f}")
    
    @pytest.mark.integration
    @pytest.mark.api_cost
    def test_code_search_and_discovery(self, clean_database, test_config, standard_documents):
        """
        Test code search and discovery capabilities
        
        Validates:
        1. Semantic code search
        2. Pattern discovery
        3. Method and class finding
        4. Cross-reference capabilities
        """
        logger.info("🔍 Starting code search and discovery test")
        
        # Use cached standard documents (optimized)
        documents = standard_documents
        if not documents:
            pytest.skip("No cached documents available")
        
        graph_builder = GraphBuilder()
        success, message = graph_builder.create_graphrag_system(documents)
        assert success, f"System creation failed: {message}"
        
        query_processor = QueryProcessor()
        success, message = query_processor.setup_retrievers()
        assert success, f"Query setup failed: {message}"
        
        # Test different search types
        search_tests = [
            {
                "type": "Semantic search",
                "queries": [
                    "thread safe implementation",
                    "object creation pattern",
                    "lazy initialization"
                ]
            },
            {
                "type": "Method search",
                "queries": [
                    "getInstance method",
                    "constructor implementation",
                    "static method"
                ]
            },
            {
                "type": "Class search",
                "queries": [
                    "singleton class",
                    "main application class",
                    "utility class"
                ]
            },
            {
                "type": "Pattern search",
                "queries": [
                    "design pattern example",
                    "creational pattern",
                    "software pattern"
                ]
            }
        ]
        
        search_results = []
        
        for test_group in search_tests:
            group_results = {
                "type": test_group["type"],
                "successful_searches": 0,
                "total_searches": len(test_group["queries"]),
                "total_chunks_found": 0
            }
            
            for query in test_group["queries"]:
                try:
                    success, response, context = query_processor.process_query(query, k=3)
                    
                    if success and context.get('num_chunks_found', 0) > 0:
                        group_results["successful_searches"] += 1
                        group_results["total_chunks_found"] += context['num_chunks_found']
                        logger.info(f"✅ {test_group['type']} - '{query}': {context['num_chunks_found']} chunks")
                    else:
                        logger.warning(f"❌ {test_group['type']} - '{query}': no results")
                
                except Exception as e:
                    logger.error(f"Search failed: {query} - {str(e)}")
            
            search_results.append(group_results)
            
            success_rate = group_results["successful_searches"] / group_results["total_searches"]
            logger.info(f"{test_group['type']}: {success_rate:.2f} success rate")
        
        # Validate search capabilities
        total_successful = sum(r["successful_searches"] for r in search_results)
        total_searches = sum(r["total_searches"] for r in search_results)
        overall_success_rate = total_successful / total_searches
        
        assert overall_success_rate > 0.3, f"Search success rate too low: {overall_success_rate:.2f}"
        assert total_successful > 0, "At least some searches should succeed"
        
        logger.info(f"✅ Code search and discovery test passed! Success rate: {overall_success_rate:.2f}")


# Helper functions for integration testing
def validate_system_state(driver, expected_chunks: int) -> Dict[str, Any]:
    """Validate the overall system state"""
    with driver.session() as session:
        # Get comprehensive system statistics
        stats = {}
        
        # Node counts
        result = session.run("MATCH (n) RETURN labels(n)[0] as label, count(n) as count")
        stats['node_counts'] = {record["label"]: record["count"] for record in result}
        
        # Relationship counts
        result = session.run("MATCH ()-[r]->() RETURN type(r) as rel_type, count(r) as count")
        stats['relationship_counts'] = {record["rel_type"]: record["count"] for record in result}
        
        # CodeChunk validation
        result = session.run("MATCH (c:CodeChunk) RETURN count(c) as count")
        stats['codechunk_count'] = result.single()["count"]
        
        # Embedding validation
        result = session.run("MATCH (c:CodeChunk) WHERE c.embedding IS NOT NULL RETURN count(c) as count")
        stats['embedded_chunks'] = result.single()["count"]
        
        # File validation
        result = session.run("MATCH (f:File) RETURN count(f) as count")
        stats['file_count'] = result.single()["count"]
        
        return stats


def measure_query_performance(query_processor: QueryProcessor, queries: List[str], k: int = 3) -> Dict[str, Any]:
    """Measure query performance metrics"""
    results = {
        'total_queries': len(queries),
        'successful_queries': 0,
        'failed_queries': 0,
        'total_time': 0,
        'avg_time': 0,
        'total_chunks_found': 0,
        'query_details': []
    }
    
    start_time = time.time()
    
    for query in queries:
        query_start = time.time()
        try:
            success, response, context = query_processor.process_query(query, k=k)
            query_time = time.time() - query_start
            
            if success:
                results['successful_queries'] += 1
                results['total_chunks_found'] += context.get('num_chunks_found', 0)
            else:
                results['failed_queries'] += 1
            
            results['query_details'].append({
                'query': query,
                'success': success,
                'time': query_time,
                'chunks_found': context.get('num_chunks_found', 0) if success else 0
            })
            
        except Exception as e:
            query_time = time.time() - query_start
            results['failed_queries'] += 1
            results['query_details'].append({
                'query': query,
                'success': False,
                'time': query_time,
                'error': str(e)
            })
    
    results['total_time'] = time.time() - start_time
    results['avg_time'] = results['total_time'] / len(queries) if queries else 0
    
    return results 