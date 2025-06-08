# Code Graph - GraphRAG Query Processing
# This module handles query processing using vector search and graph traversal

import logging
from typing import Optional, List, Dict, Tuple, Any
from neo4j import Driver
from .config import Config
from .database import get_neo4j_connection

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryProcessor:
    """Handles GraphRAG query processing and response generation using hybrid approach"""
    
    def __init__(self):
        """Initialize QueryProcessor with singleton database connection"""
        self.config = Config()
        # Use singleton connection instead of creating our own
        self.connection = get_neo4j_connection()
        self.embeddings = None
        
    @property
    def driver(self) -> Optional[Driver]:
        """Get the driver from singleton connection"""
        return self.connection.get_driver()
    
    @property
    def is_connected(self) -> bool:
        """Check if singleton connection is active"""
        return self.connection.is_connected
    
    def ensure_connection(self) -> Tuple[bool, str]:
        """
        Ensure database connection is active and healthy
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # First check if connection object thinks it's connected
            if not self.connection.is_connected:
                # Try to reconnect
                return self.connection.connect()
            
            # Test the actual connection
            test_success, test_message = self.connection.test_connection()
            if not test_success:
                # Connection is stale, try to reconnect
                logger.warning("🔄 Connection appears stale, attempting to reconnect...")
                return self.connection.connect()
            
            return True, "✅ Connection is healthy"
            
        except Exception as e:
            return False, f"❌ Connection validation failed: {str(e)}"
        

    
    def setup_retrievers(self) -> Tuple[bool, str]:
        """
        Set up vector retriever and embeddings for query processing
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Ensure we have a healthy connection before proceeding
            connection_success, connection_message = self.ensure_connection()
            if not connection_success:
                return False, f"❌ Database connection failed: {connection_message}"
            
            # Initialize OpenAI embeddings
            from langchain_openai import OpenAIEmbeddings
            
            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-3-large",
                openai_api_key=self.config.OPENAI_API_KEY
            )
            
            # Verify vector index exists
            with self.driver.session() as session:
                index_result = session.run("SHOW INDEXES YIELD name WHERE name = 'code_chunks_vector_index'")
                index_exists = len(list(index_result)) > 0
                
                if not index_exists:
                    return False, "❌ Vector index 'code_chunks_vector_index' not found. Please create GraphRAG system first."
            
            logger.info("✅ QueryProcessor retrievers set up successfully")
            return True, "✅ QueryProcessor retrievers set up successfully"
            
        except ImportError as e:
            return False, f"❌ Missing dependency: {str(e)}. Please install langchain-openai."
        except Exception as e:
            return False, f"❌ Error setting up retrievers: {str(e)}"
    
    def process_query(self, query: str, k: int = 5, include_graph_context: bool = True) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Process a user query using hybrid GraphRAG approach
        
        Args:
            query: User's natural language query about the codebase
            k: Number of vector search results to retrieve
            include_graph_context: Whether to include graph traversal context
            
        Returns:
            Tuple[bool, str, Dict]: (success, response, context_data)
        """
        try:
            if not self.is_connected or not self.embeddings:
                return False, "❌ QueryProcessor not properly initialized. Please connect and setup retrievers first.", {}
            
            logger.info(f"🔍 Processing query: '{query}'")
            
            # Step 1: Vector similarity search
            vector_success, vector_results = self.vector_search(query, k)
            if not vector_success:
                return False, f"❌ Vector search failed: {vector_results}", {}
            
            # Step 2: Extract entities from vector results (if graph context requested)
            graph_context = {}
            if include_graph_context and vector_results:
                graph_success, graph_data = self.get_graph_context_for_chunks(vector_results)
                if graph_success:
                    graph_context = graph_data
            
            # Step 3: Generate comprehensive response
            response_success, response_text = self._generate_response(query, vector_results, graph_context)
            if not response_success:
                return False, f"❌ Response generation failed: {response_text}", {}
            
            # Prepare context data for debugging/analysis
            context_data = {
                'query': query,
                'vector_results': vector_results,
                'graph_context': graph_context,
                'num_chunks_found': len(vector_results),
                'num_entities_found': len(graph_context.get('entities', [])),
                'num_relationships_found': len(graph_context.get('relationships', []))
            }
            
            logger.info(f"✅ Query processed successfully: {len(vector_results)} chunks, {len(graph_context.get('entities', []))} entities")
            return True, response_text, context_data
            
        except Exception as e:
            error_msg = f"❌ Error processing query: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, {}
    
    def vector_search(self, query: str, k: int = 5) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Perform vector similarity search using Neo4j vector index
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            Tuple[bool, List[Dict]]: (success, results)
        """
        try:
            # Ensure connection is healthy
            connection_success, connection_message = self.ensure_connection()
            if not connection_success:
                logger.error(f"Connection failed during vector search: {connection_message}")
                return False, []
                
            if not self.embeddings:
                return False, []
            
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Perform vector search in Neo4j
            with self.driver.session() as session:
                vector_query = """
                CALL db.index.vector.queryNodes('code_chunks_vector_index', $k, $query_embedding)
                YIELD node, score
                RETURN node.chunk_id as chunk_id,
                       node.text as text,
                       node.file_path as file_path,
                       node.language as language,
                       node.start_line as start_line,
                       node.end_line as end_line,
                       score
                ORDER BY score DESC
                """
                
                result = session.run(vector_query, {
                    'k': k,
                    'query_embedding': query_embedding
                })
                
                results = []
                for record in result:
                    results.append({
                        'chunk_id': record['chunk_id'],
                        'text': record['text'],
                        'file_path': record['file_path'],
                        'language': record['language'],
                        'start_line': record['start_line'],
                        'end_line': record['end_line'],
                        'similarity_score': record['score']
                    })
                
                return True, results
                
        except Exception as e:
            logger.error(f"Vector search error: {str(e)}")
            return False, []
    
    def get_graph_context_for_chunks(self, vector_results: List[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
        """
        Get graph context (entities and relationships) for vector search results
        
        Args:
            vector_results: Results from vector search
            
        Returns:
            Tuple[bool, Dict]: (success, graph_context)
        """
        try:
            if not vector_results:
                return True, {'entities': [], 'relationships': [], 'files': []}
            
            chunk_ids = [result['chunk_id'] for result in vector_results]
            file_paths = list(set([result['file_path'] for result in vector_results]))
            
            with self.driver.session() as session:
                # Find entities (Classes, Functions) related to these chunks
                entity_query = """
                MATCH (c:CodeChunk)-[:REPRESENTS]->(entity)
                WHERE c.chunk_id IN $chunk_ids
                RETURN entity, labels(entity) as entity_type, c.chunk_id as chunk_id
                """
                
                entity_result = session.run(entity_query, {'chunk_ids': chunk_ids})
                entities = []
                for record in entity_result:
                    entity_node = record['entity']
                    entities.append({
                        'id': entity_node.get('id', 'unknown'),
                        'type': record['entity_type'][0] if record['entity_type'] else 'unknown',
                        'properties': dict(entity_node),
                        'related_chunk': record['chunk_id']
                    })
                
                # Find relationships between entities
                relationship_query = """
                MATCH (c:CodeChunk)-[:REPRESENTS]->(e1)-[r]->(e2)
                WHERE c.chunk_id IN $chunk_ids
                RETURN e1.id as source, type(r) as relationship, e2.id as target, e1, e2
                LIMIT 20
                """
                
                rel_result = session.run(relationship_query, {'chunk_ids': chunk_ids})
                relationships = []
                for record in rel_result:
                    relationships.append({
                        'source': record['source'],
                        'relationship': record['relationship'],
                        'target': record['target'],
                        'source_properties': dict(record['e1']),
                        'target_properties': dict(record['e2'])
                    })
                
                # Get file-level information
                file_query = """
                MATCH (f:File)
                WHERE f.path IN $file_paths
                OPTIONAL MATCH (f)-[:CONTAINS]->(entity)
                RETURN f, collect(DISTINCT labels(entity)[0]) as entity_types, count(entity) as entity_count
                """
                
                file_result = session.run(file_query, {'file_paths': file_paths})
                files = []
                for record in file_result:
                    file_node = record['f']
                    files.append({
                        'path': file_node.get('path', 'unknown'),
                        'name': file_node.get('name', 'unknown'),
                        'language': file_node.get('language', 'unknown'),
                        'entity_types': [t for t in record['entity_types'] if t],
                        'entity_count': record['entity_count']
                    })
                
                graph_context = {
                    'entities': entities,
                    'relationships': relationships,
                    'files': files
                }
                
                return True, graph_context
                
        except Exception as e:
            logger.error(f"Graph context error: {str(e)}")
            return False, {'entities': [], 'relationships': [], 'files': []}
    
    def _generate_response(self, query: str, vector_results: List[Dict], graph_context: Dict) -> Tuple[bool, str]:
        """
        Generate a natural, conversational response using LLM
        
        Args:
            query: Original user query
            vector_results: Results from vector search
            graph_context: Graph traversal context
            
        Returns:
            Tuple[bool, str]: (success, conversational_response)
        """
        try:
            if not vector_results:
                return True, "I couldn't find any relevant code for your query. Could you try rephrasing your question or being more specific about what you're looking for?"
            
            # Use utility functions for LLM processing
            from app.utilities.llm_utils import (
                prepare_context_for_llm, 
                generate_conversational_response, 
                generate_fallback_response
            )
            
            # Prepare context for LLM
            context_data = prepare_context_for_llm(query, vector_results, graph_context)
            
            # Generate conversational response using LLM
            response_success, conversational_response = generate_conversational_response(context_data, self.config.OPENAI_API_KEY)
            
            if not response_success:
                # Fallback to basic response if LLM fails
                return True, generate_fallback_response(vector_results, graph_context)
            
            return True, conversational_response
            
        except Exception as e:
            logger.error(f"Error generating conversational response: {str(e)}")
            # Fallback response
            return True, f"I found {len(vector_results)} relevant code chunks, but had trouble generating a detailed explanation. The most relevant file is {vector_results[0]['file_path'].split('/')[-1]} if you'd like to explore it."
