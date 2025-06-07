# Code Graph - GraphRAG Query Processing
# This module handles query processing using vector search and graph traversal

import logging
from typing import Optional, List, Dict, Tuple, Any
from neo4j import GraphDatabase, Driver
from .config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryProcessor:
    """Handles GraphRAG query processing and response generation using hybrid approach"""
    
    def __init__(self):
        """Initialize QueryProcessor with Neo4j connection"""
        self.config = Config()
        self.driver: Optional[Driver] = None
        self.is_connected = False
        self.embeddings = None
        
    def connect_to_neo4j(self) -> Tuple[bool, str]:
        """
        Establish connection to Neo4j database
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if not self.config.validate_config():
                return False, "❌ Invalid Neo4j configuration. Please check your .env file."
            
            logger.info(f"🔗 Connecting QueryProcessor to Neo4j at {self.config.NEO4J_URI}")
            
            self.driver = GraphDatabase.driver(
                self.config.NEO4J_URI,
                auth=(self.config.NEO4J_USERNAME, self.config.NEO4J_PASSWORD),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60
            )
            
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                if result.single()["test"] == 1:
                    self.is_connected = True
                    logger.info("✅ QueryProcessor connected to Neo4j successfully")
                    return True, "✅ QueryProcessor connected to Neo4j successfully"
                else:
                    return False, "❌ Connection test failed"
                    
        except Exception as e:
            return False, f"❌ Error connecting to Neo4j: {str(e)}"
    
    def setup_retrievers(self) -> Tuple[bool, str]:
        """
        Set up vector retriever and embeddings for query processing
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if not self.is_connected:
                return False, "❌ Not connected to Neo4j. Please connect first."
            
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
                    return False, "❌ Vector index 'code_chunks_vector_index' not found. Please create unified GraphRAG system first."
            
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
        Generate a comprehensive response using vector results and graph context
        
        Args:
            query: Original user query
            vector_results: Results from vector search
            graph_context: Graph traversal context
            
        Returns:
            Tuple[bool, str]: (success, response)
        """
        try:
            if not vector_results:
                return True, "No relevant code found for your query."
            
            # Build response sections
            response_parts = []
            
            # Summary (without repeating the query)
            response_parts.append(f"Found {len(vector_results)} relevant code chunks across {len(set(r['file_path'] for r in vector_results))} files.")
            
            # Most relevant code chunks
            response_parts.append("\n### Most Relevant Code:")
            for i, result in enumerate(vector_results[:3], 1):  # Top 3 results
                file_name = result['file_path'].split('/')[-1] if '/' in result['file_path'] else result['file_path']
                response_parts.append(f"\n**{i}. {file_name} (Lines {result['start_line']}-{result['end_line']}, Similarity: {result['similarity_score']:.3f})**")
                response_parts.append(f"```{result['language']}")
                # Show more of the code content
                code_text = result['text']
                if len(code_text) > 800:
                    # Find a good breaking point (end of line)
                    break_point = code_text.rfind('\n', 0, 800)
                    if break_point > 600:  # If we found a reasonable break point
                        code_text = code_text[:break_point] + "\n... (truncated)"
                    else:
                        code_text = code_text[:800] + "..."
                response_parts.append(code_text)
                response_parts.append("```")
            
            # Graph context (if available)
            if graph_context.get('entities'):
                response_parts.append("\n### Related Code Entities:")
                entity_types = {}
                for entity in graph_context['entities']:
                    entity_type = entity['type']
                    if entity_type not in entity_types:
                        entity_types[entity_type] = []
                    entity_types[entity_type].append(entity['id'])
                
                for entity_type, entity_ids in entity_types.items():
                    response_parts.append(f"- **{entity_type}s**: {', '.join(entity_ids[:5])}")
            
            if graph_context.get('relationships'):
                response_parts.append("\n### Code Relationships:")
                rel_types = {}
                for rel in graph_context['relationships']:
                    rel_type = rel['relationship']
                    if rel_type not in rel_types:
                        rel_types[rel_type] = []
                    rel_types[rel_type].append(f"{rel['source']} → {rel['target']}")
                
                for rel_type, examples in rel_types.items():
                    response_parts.append(f"- **{rel_type}**: {', '.join(examples[:3])}")
            
            # File summary
            if graph_context.get('files'):
                response_parts.append("\n### Files Involved:")
                for file_info in graph_context['files'][:5]:  # Top 5 files
                    response_parts.append(f"- **{file_info['name']}** ({file_info['language']}) - {file_info['entity_count']} entities")
            
            response_text = "\n".join(response_parts)
            return True, response_text
            
        except Exception as e:
            return False, f"Error generating response: {str(e)}"
    
    def close_connection(self) -> None:
        """Close the Neo4j connection"""
        try:
            if self.driver:
                self.driver.close()
                self.driver = None
                self.is_connected = False
                logger.info("🔌 QueryProcessor Neo4j connection closed")
        except Exception as e:
            logger.error(f"Error closing QueryProcessor connection: {str(e)}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically close connection"""
        self.close_connection() 