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
    
    def create_vector_index(self, documents: list) -> Tuple[bool, str]:
        """
        Create vector index for embeddings with rich metadata
        
        Args:
            documents: List of chunked Document objects from parse_code_chunks
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if not self.is_connected or not self.driver:
                return False, "❌ Not connected to Neo4j. Please connect first."
            
            if not documents:
                return False, "❌ No documents provided for vector index creation."
            
            logger.info(f"🔍 Creating vector index for {len(documents)} documents")
            
            # Import required libraries
            from langchain_openai import OpenAIEmbeddings
            from langchain_neo4j import Neo4jVector
            import time
            
            # Initialize OpenAI embeddings
            embeddings = OpenAIEmbeddings(
                model="text-embedding-3-large",
                openai_api_key=self.config.OPENAI_API_KEY
            )
            
            logger.info("🧮 Generating embeddings for documents...")
            start_time = time.time()
            
            # Create Neo4j vector store with rich metadata
            vector_store = Neo4jVector.from_documents(
                documents=documents,
                embedding=embeddings,
                url=self.config.NEO4J_URI,
                username=self.config.NEO4J_USERNAME,
                password=self.config.NEO4J_PASSWORD,
                index_name="code_chunks_vector_index",  # Custom index name
                node_label="CodeChunk",  # Custom node label for code chunks
                text_node_property="text",  # Fixed parameter name
                embedding_node_property="embedding"
            )
            
            embedding_time = time.time() - start_time
            
            # Create additional metadata nodes and relationships
            logger.info("📊 Creating metadata nodes and relationships...")
            metadata_success, metadata_message = self._create_metadata_nodes(documents)
            
            # Get vector index statistics
            stats_success, stats_message = self._get_vector_index_stats()
            
            success_message = (
                f"✅ Vector index created successfully!\n"
                f"📄 Documents processed: {len(documents)}\n"
                f"🔍 Embedding model: text-embedding-3-large\n"
                f"⏱️ Embedding time: {embedding_time:.2f} seconds\n"
                f"🏷️ Index name: code_chunks_vector_index\n"
                f"🔵 Node label: CodeChunk\n"
                f"📊 Metadata: {metadata_message if metadata_success else 'Metadata creation failed'}\n"
                f"📈 Statistics: {stats_message if stats_success else 'Stats unavailable'}"
            )
            
            logger.info("✅ Vector index creation completed successfully")
            return True, success_message
            
        except ImportError as e:
            error_msg = f"❌ Missing required dependency: {str(e)}\n💡 Tip: Install with 'pip install langchain-openai'"
            logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"❌ Error creating vector index: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _create_metadata_nodes(self, documents: list) -> Tuple[bool, str]:
        """
        Create additional metadata nodes for files, functions, and relationships
        
        Args:
            documents: List of Document objects with metadata
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            with self.driver.session() as session:
                files_created = 0
                chunks_linked = 0
                
                # Group documents by file
                file_chunks = {}
                for doc in documents:
                    file_path = doc.metadata.get('file_path', 'unknown')
                    if file_path not in file_chunks:
                        file_chunks[file_path] = []
                    file_chunks[file_path].append(doc)
                
                # Create File nodes and link to CodeChunk nodes
                for file_path, chunks in file_chunks.items():
                    # Create File node with metadata
                    file_query = """
                    MERGE (f:File {path: $file_path})
                    SET f.name = $file_name,
                        f.extension = $extension,
                        f.language = $language,
                        f.total_chunks = $chunk_count,
                        f.total_lines = $total_lines,
                        f.created_at = datetime()
                    RETURN f
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
                    files_created += 1
                    
                    # Link CodeChunk nodes to File nodes
                    for chunk in chunks:
                        chunk_id = chunk.metadata.get('chunk_id', f"chunk_{hash(chunk.page_content)}")
                        
                        link_query = """
                        MATCH (f:File {path: $file_path})
                        MATCH (c:CodeChunk {chunk_id: $chunk_id})
                        MERGE (f)-[:CONTAINS_CHUNK]->(c)
                        SET c.file_path = $file_path,
                            c.language = $language,
                            c.start_line = $start_line,
                            c.end_line = $end_line
                        """
                        
                        session.run(link_query, {
                            'file_path': file_path,
                            'chunk_id': chunk_id,
                            'language': language,
                            'start_line': chunk.metadata.get('start_line', 0),
                            'end_line': chunk.metadata.get('end_line', 0)
                        })
                        chunks_linked += 1
                
                message = f"Files: {files_created}, Chunks linked: {chunks_linked}"
                return True, message
                
        except Exception as e:
            return False, f"Error creating metadata: {str(e)}"
    
    def _get_vector_index_stats(self) -> Tuple[bool, str]:
        """
        Get statistics about the vector index
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            with self.driver.session() as session:
                # Count CodeChunk nodes
                chunk_result = session.run("MATCH (c:CodeChunk) RETURN count(c) as chunk_count")
                chunk_record = chunk_result.single()
                chunk_count = chunk_record["chunk_count"] if chunk_record else 0
                
                # Count File nodes
                file_result = session.run("MATCH (f:File) RETURN count(f) as file_count")
                file_record = file_result.single()
                file_count = file_record["file_count"] if file_record else 0
                
                # Count CONTAINS_CHUNK relationships
                rel_result = session.run("MATCH ()-[r:CONTAINS_CHUNK]->() RETURN count(r) as rel_count")
                rel_record = rel_result.single()
                rel_count = rel_record["rel_count"] if rel_record else 0
                
                # Check if vector index exists
                try:
                    index_result = session.run("SHOW INDEXES YIELD name WHERE name = 'code_chunks_vector_index'")
                    index_exists = len(list(index_result)) > 0
                except:
                    index_exists = False
                
                message = f"CodeChunks: {chunk_count}, Files: {file_count}, Links: {rel_count}, Index: {'✅' if index_exists else '❌'}"
                return True, message
                
        except Exception as e:
            return False, f"Error getting vector stats: {str(e)}"
    
    def test_vector_search(self, query: str, k: int = 3) -> Tuple[bool, str, list]:
        """
        Test vector search functionality
        
        Args:
            query: Search query string
            k: Number of results to return
            
        Returns:
            Tuple[bool, str, list]: (success, message, results)
        """
        try:
            if not self.is_connected or not self.driver:
                return False, "❌ Not connected to Neo4j. Please connect first.", []
            
            from langchain_openai import OpenAIEmbeddings
            from langchain_neo4j import Neo4jVector
            
            # Initialize embeddings and vector store
            embeddings = OpenAIEmbeddings(
                model="text-embedding-3-large",
                openai_api_key=self.config.OPENAI_API_KEY
            )
            
            vector_store = Neo4jVector.from_existing_index(
                embedding=embeddings,
                url=self.config.NEO4J_URI,
                username=self.config.NEO4J_USERNAME,
                password=self.config.NEO4J_PASSWORD,
                index_name="code_chunks_vector_index"
            )
            
            # Perform similarity search
            results = vector_store.similarity_search_with_score(query, k=k)
            
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    'content': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    'score': score,
                    'metadata': doc.metadata
                })
            
            message = f"Found {len(results)} results for query: '{query}'"
            return True, message, formatted_results
            
        except Exception as e:
            error_msg = f"❌ Error testing vector search: {str(e)}"
            return False, error_msg, []
    
    def create_unified_graphrag_system(self, documents: list) -> Tuple[bool, str]:
        """
        Create a unified GraphRAG system with both knowledge graph and vector index coexisting
        
        This method:
        1. Creates structural knowledge graph (Class, Function, Interface nodes)
        2. Creates semantic vector index (CodeChunk nodes with embeddings)
        3. Creates bridge relationships (REPRESENTS) linking chunks to entities
        4. Maintains unified File nodes used by both systems
        
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
            
            logger.info(f"🚀 Creating unified GraphRAG system for {len(documents)} documents")
            
            # Step 1: Create structural knowledge graph
            logger.info("🧠 Step 1: Creating structural knowledge graph...")
            kg_success, kg_message = self.generate_knowledge_graph(documents)
            
            if not kg_success:
                return False, f"❌ Knowledge graph creation failed: {kg_message}"
            
            # Step 2: Create semantic vector index (without clearing existing data)
            logger.info("🔍 Step 2: Creating semantic vector index...")
            vector_success, vector_message = self._create_vector_index_coexistent(documents)
            
            if not vector_success:
                return False, f"❌ Vector index creation failed: {vector_message}"
            
            # Step 3: Create bridge relationships between structural and semantic layers
            logger.info("🌉 Step 3: Creating bridge relationships...")
            bridge_success, bridge_message = self._create_bridge_relationships(documents)
            
            if not bridge_success:
                logger.warning(f"⚠️ Bridge relationships creation had issues: {bridge_message}")
            
            # Step 4: Get comprehensive statistics
            stats_success, stats_message = self._get_unified_system_stats()
            
            success_message = (
                f"✅ Unified GraphRAG system created successfully!\n"
                f"🧠 Knowledge Graph: {kg_message.split('!')[0]}!\n"
                f"🔍 Vector Index: {vector_message.split('!')[0]}!\n"
                f"🌉 Bridge Relationships: {bridge_message}\n"
                f"📊 System Statistics: {stats_message if stats_success else 'Stats unavailable'}"
            )
            
            logger.info("✅ Unified GraphRAG system creation completed successfully")
            return True, success_message
            
        except Exception as e:
            error_msg = f"❌ Error creating unified GraphRAG system: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _create_vector_index_coexistent(self, documents: list) -> Tuple[bool, str]:
        """
        Create vector index that coexists with knowledge graph (doesn't clear existing data)
        
        Args:
            documents: List of chunked Document objects
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
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
            
            # Create unified metadata nodes and relationships
            metadata_success, metadata_message = self._create_unified_metadata_nodes(documents)
            
            success_message = (
                f"Vector index created with {chunks_created} chunks "
                f"(embedding time: {embedding_time:.2f}s, metadata: {metadata_message})"
            )
            
            return True, success_message
            
        except Exception as e:
            return False, f"Error creating coexistent vector index: {str(e)}"
    
    def _create_unified_metadata_nodes(self, documents: list) -> Tuple[bool, str]:
        """
        Create unified File nodes that work with both knowledge graph and vector index
        
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
                    # Create/update unified File node
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
            return False, f"Error creating unified metadata: {str(e)}"
    
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
    
    def _get_unified_system_stats(self) -> Tuple[bool, str]:
        """
        Get comprehensive statistics about the unified GraphRAG system
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            with self.driver.session() as session:
                stats = {}
                
                # Count all node types
                node_query = """
                MATCH (n)
                RETURN labels(n)[0] as NodeType, count(n) as Count
                ORDER BY Count DESC
                """
                
                node_result = session.run(node_query)
                node_counts = {record["NodeType"]: record["Count"] for record in node_result}
                
                # Count all relationship types
                rel_query = """
                MATCH ()-[r]->()
                RETURN type(r) as RelType, count(r) as Count
                ORDER BY Count DESC
                """
                
                rel_result = session.run(rel_query)
                rel_counts = {record["RelType"]: record["Count"] for record in rel_result}
                
                # Check vector index
                try:
                    index_result = session.run("SHOW INDEXES YIELD name WHERE name = 'code_chunks_vector_index'")
                    vector_index_exists = len(list(index_result)) > 0
                except:
                    vector_index_exists = False
                
                # Format statistics
                node_summary = ", ".join([f"{k}: {v}" for k, v in list(node_counts.items())[:5]])
                rel_summary = ", ".join([f"{k}: {v}" for k, v in list(rel_counts.items())[:5]])
                
                message = (
                    f"Nodes ({node_summary}), "
                    f"Relationships ({rel_summary}), "
                    f"Vector Index: {'✅' if vector_index_exists else '❌'}"
                )
                
                return True, message
                
        except Exception as e:
            return False, f"Error getting system stats: {str(e)}" 