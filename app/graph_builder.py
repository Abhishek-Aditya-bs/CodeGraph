# Code Graph - Knowledge Graph and Embeddings Builder
# This module handles knowledge graph creation and vector indexing using singleton Neo4j connection

import logging
from typing import Optional, Tuple
from neo4j import Driver
from .config import Config
from .database import get_neo4j_connection


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GraphBuilder:
    """Handles knowledge graph creation and vector indexing in Neo4j"""
    
    def __init__(self):
        """Initialize GraphBuilder with singleton database connection"""
        self.config = Config()
        # Use singleton connection instead of creating our own
        self.connection = get_neo4j_connection()
        
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

    
    def generate_knowledge_graph(self, documents: list) -> Tuple[bool, str]:
        """
        Generate knowledge graph from code documents using LLMGraphTransformer
        
        Args:
            documents: List of chunked Document objects from parse_code_chunks
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Ensure we have a healthy connection before proceeding
            connection_success, connection_message = self.ensure_connection()
            if not connection_success:
                return False, f"❌ Database connection failed: {connection_message}"
            
            if not documents:
                return False, "❌ No documents provided for knowledge graph generation."
            
            logger.info(f"🧠 Starting knowledge graph generation for {len(documents)} documents")
            
            # Import required libraries
            from langchain_openai import ChatOpenAI
            from langchain_experimental.graph_transformers import LLMGraphTransformer
            from langchain_neo4j import Neo4jGraph
            
            # Initialize OpenAI LLM with configured model
            llm = ChatOpenAI(
                model=self.config.LLM_MODEL,
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
            stats_success, stats_message, stats = self._get_stats()
            
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
    
    def _get_stats(self) -> Tuple[bool, str, dict]:
        """
        Get statistics about the created knowledge graph
        
        Returns:
            Tuple[bool, str, dict]: (success, message, stats)
        """
        try:
            from .utilities.graph_stats_utils import get_graph_creation_stats
            return get_graph_creation_stats(self.driver)
        except Exception as e:
            return False, f"Error getting stats: {str(e)}", {}
    

    
    def create_vector_index(self, documents: list) -> Tuple[bool, str]:
        """
        Create vector index for embeddings
        
        Args:
            documents: List of chunked Document objects from parse_code_chunks
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Ensure we have a healthy connection before proceeding
            connection_success, connection_message = self.ensure_connection()
            if not connection_success:
                return False, f"❌ Database connection failed: {connection_message}"
            
            if not documents:
                return False, "❌ No documents provided for vector index creation."
            
            logger.info(f"🔍 Creating vector index for {len(documents)} documents")
            
            # Import required libraries
            from langchain_openai import OpenAIEmbeddings
            import time
            
            # Initialize OpenAI embeddings
            embeddings = OpenAIEmbeddings(
                model="text-embedding-3-large",
                openai_api_key=self.config.OPENAI_API_KEY
            )
            
            logger.info("🧮 Generating embeddings for documents...")
            start_time = time.time()
            
            # Create embeddings for all documents
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            
            # Generate embeddings
            doc_embeddings = embeddings.embed_documents(texts)
            
            # Store in Neo4j manually to avoid clearing existing data
            with self.driver.session() as session:
                chunks_created = 0
                
                for i, (text, metadata, embedding) in enumerate(zip(texts, metadatas, doc_embeddings)):
                    # Create CodeChunk node with embedding
                    chunk_query = """
                    CREATE (c:CodeChunk {
                        chunk_id: $chunk_id,
                        text: $text,
                        embedding: $embedding,
                        file_path: $file_path,
                        language: $language,
                        start_line: $start_line,
                        end_line: $end_line,
                        chunk_size: $chunk_size,
                        created_at: datetime()
                    })
                    """
                    
                    chunk_id = metadata.get('chunk_id', i)
                    
                    session.run(chunk_query, {
                        'chunk_id': chunk_id,
                        'text': text,
                        'embedding': embedding,
                        'file_path': metadata.get('file_path', 'unknown'),
                        'language': metadata.get('language', 'unknown'),
                        'start_line': metadata.get('start_line', 0),
                        'end_line': metadata.get('end_line', 0),
                        'chunk_size': len(text)
                    })
                    
                    chunks_created += 1
                
                # Create vector index if it doesn't exist
                try:
                    session.run("""
                    CREATE VECTOR INDEX code_chunks_vector_index IF NOT EXISTS
                    FOR (c:CodeChunk) ON (c.embedding)
                    OPTIONS {indexConfig: {
                        `vector.dimensions`: 3072,
                        `vector.similarity_function`: 'cosine'
                    }}
                    """)
                except Exception as e:
                    logger.warning(f"Vector index creation warning: {str(e)}")
            
            embedding_time = time.time() - start_time
            
            # Create metadata nodes and relationships
            metadata_success, metadata_message = self._create_metadata_nodes(documents)
            
            success_message = (
                f"✅ Vector index created successfully!\n"
                f"📄 Documents processed: {len(documents)}\n"
                f"🔍 Chunks created: {chunks_created}\n"
                f"⏱️ Embedding time: {embedding_time:.2f} seconds\n"
                f"📊 Metadata: {metadata_message if metadata_success else 'Metadata creation failed'}"
            )
            
            return True, success_message
            
        except Exception as e:
            return False, f"❌ Error creating vector index: {str(e)}"
    
    def _create_metadata_nodes(self, documents: list) -> Tuple[bool, str]:
        """
        Create File nodes and link to CodeChunk nodes
        
        Args:
            documents: List of Document objects with metadata
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            with self.driver.session() as session:
                files_processed = 0
                chunks_linked = 0
                
                # Group documents by file
                file_chunks = {}
                for doc in documents:
                    file_path = doc.metadata.get('file_path', 'unknown')
                    if file_path not in file_chunks:
                        file_chunks[file_path] = []
                    file_chunks[file_path].append(doc)
                
                # Create or update File nodes and link to CodeChunk nodes
                for file_path, chunks in file_chunks.items():
                    # Create/update File node
                    file_query = """
                    MERGE (f:File {path: $file_path})
                    SET f.name = $file_name,
                        f.extension = $extension,
                        f.language = $language,
                        f.total_chunks = $chunk_count,
                        f.total_lines = $total_lines,
                        f.updated_at = datetime()
                    """
                    
                    # Extract file metadata
                    file_name = file_path.split('/')[-1] if '/' in file_path else file_path
                    extension = file_name.split('.')[-1] if '.' in file_name else 'unknown'
                    language = chunks[0].metadata.get('language', 'unknown')
                    total_lines = max([chunk.metadata.get('end_line', 0) for chunk in chunks])
                    
                    session.run(file_query, {
                        'file_path': file_path,
                        'file_name': file_name,
                        'extension': extension,
                        'language': language,
                        'chunk_count': len(chunks),
                        'total_lines': total_lines
                    })
                    files_processed += 1
                    
                    # Link CodeChunk nodes to File nodes
                    for chunk in chunks:
                        chunk_id = chunk.metadata.get('chunk_id', f"chunk_{hash(chunk.page_content)}")
                        
                        link_query = """
                        MATCH (f:File {path: $file_path})
                        MATCH (c:CodeChunk {chunk_id: $chunk_id})
                        MERGE (f)-[:CONTAINS_CHUNK]->(c)
                        """
                        
                        session.run(link_query, {
                            'file_path': file_path,
                            'chunk_id': chunk_id
                        })
                        chunks_linked += 1
                
                message = f"Files: {files_processed}, Chunks linked: {chunks_linked}"
                return True, message
                
        except Exception as e:
            return False, f"Error creating metadata: {str(e)}"
    
    def create_graphrag_system(self, documents: list) -> Tuple[bool, str]:
        """
        Create a complete GraphRAG system with both knowledge graph and vector index
        
        This method:
        1. Creates structural knowledge graph (Class, Function, Interface nodes)
        2. Creates semantic vector index (CodeChunk nodes with embeddings)
        3. Creates bridge relationships (REPRESENTS) linking chunks to entities
        4. Maintains File nodes used by both systems
        
        Args:
            documents: List of chunked Document objects from parse_code_chunks
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if not self.is_connected or not self.driver:
                return False, "❌ Not connected to Neo4j. Please connect first."
            
            if not documents:
                return False, "❌ No documents provided for GraphRAG system creation."
            
            logger.info(f"🚀 Creating GraphRAG system for {len(documents)} documents")
            
            # Step 1: Create structural knowledge graph
            logger.info("🧠 Step 1: Creating structural knowledge graph...")
            kg_success, kg_message = self.generate_knowledge_graph(documents)
            
            if not kg_success:
                return False, f"❌ Knowledge graph creation failed: {kg_message}"
            
            # Step 2: Create semantic vector index
            logger.info("🔍 Step 2: Creating semantic vector index...")
            vector_success, vector_message = self.create_vector_index(documents)
            
            if not vector_success:
                return False, f"❌ Vector index creation failed: {vector_message}"
            
            # Step 3: Create bridge relationships between structural and semantic layers
            logger.info("🌉 Step 3: Creating bridge relationships...")
            bridge_success, bridge_message = self._create_bridge_relationships(documents)
            
            if not bridge_success:
                logger.warning(f"⚠️ Bridge relationships creation had issues: {bridge_message}")
            
            # Step 4: Get comprehensive statistics
            stats_success, stats_message = self._get_system_stats()
            
            success_message = (
                f"✅ GraphRAG system created successfully!\n"
                f"🧠 Knowledge Graph: {kg_message.split('!')[0]}!\n"
                f"🔍 Vector Index: {vector_message.split('!')[0]}!\n"
                f"🌉 Bridge Relationships: {bridge_message}\n"
                f"📊 System Statistics: {stats_message if stats_success else 'Stats unavailable'}"
            )
            
            logger.info("✅ GraphRAG system creation completed successfully")
            return True, success_message
            
        except Exception as e:
            error_msg = f"❌ Error creating GraphRAG system: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _create_bridge_relationships(self, documents: list) -> Tuple[bool, str]:
        """
        Create bridge relationships between CodeChunk nodes and structural entities (Class, Function)
        
        This enables hybrid queries that combine semantic search with structural understanding.
        
        Args:
            documents: List of Document objects
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            with self.driver.session() as session:
                bridges_created = 0
                
                # Create REPRESENTS relationships based on content similarity
                # This is a simplified approach - in production, you'd use more sophisticated NLP
                
                # Link chunks to classes based on class name mentions
                class_bridge_query = """
                MATCH (c:CodeChunk)
                MATCH (cls:Class)
                WHERE c.text CONTAINS cls.id OR c.text CONTAINS REPLACE(cls.id, 'Class', '')
                MERGE (c)-[:REPRESENTS]->(cls)
                """
                
                result = session.run(class_bridge_query)
                bridges_created += result.consume().counters.relationships_created
                
                # Link chunks to functions based on function name mentions
                function_bridge_query = """
                MATCH (c:CodeChunk)
                MATCH (f:Function)
                WHERE c.text CONTAINS f.id OR c.text CONTAINS REPLACE(f.id, '()', '')
                MERGE (c)-[:REPRESENTS]->(f)
                """
                
                result = session.run(function_bridge_query)
                bridges_created += result.consume().counters.relationships_created
                
                # Create file-level bridges
                file_bridge_query = """
                MATCH (c:CodeChunk)
                MATCH (cls:Class)
                MATCH (f:File)-[:CONTAINS_CHUNK]->(c)
                WHERE EXISTS((f)-[:CONTAINS]->(cls))
                MERGE (c)-[:PART_OF_FILE]->(cls)
                """
                
                result = session.run(file_bridge_query)
                bridges_created += result.consume().counters.relationships_created
                
                message = f"Bridge relationships created: {bridges_created}"
                return True, message
                
        except Exception as e:
            return False, f"Error creating bridge relationships: {str(e)}"
    
    def _get_system_stats(self) -> Tuple[bool, str]:
        """
        Get comprehensive statistics about the GraphRAG system
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            from app.utilities.graph_stats_utils import get_graphrag_system_stats
            return get_graphrag_system_stats(self.driver)
        except Exception as e:
            return False, f"Error getting system stats: {str(e)}"
    
 