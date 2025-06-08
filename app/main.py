# Code Graph - Beautiful Streamlit UI for GraphRAG Codebase Analysis
# Complete workflow: Input → Ingestion → Knowledge Graph → Vector Index → Query → Response

import streamlit as st
import logging
import time
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Import CodeGraph components
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import initialize_database, get_neo4j_connection
from app.config import Config
from app.ingestion import clone_repository, read_local_folder, parse_code_chunks
from app.graph_builder import GraphBuilder
from app.query_processor import QueryProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="CodeGraph - GraphRAG Analysis",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .status-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 0.5rem 0;
    }
    
    .error-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 0.5rem 0;
    }
    
    .warning-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin: 0.5rem 0;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .workflow-step {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #2196f3;
    }
    
    .completed-step {
        background: #e8f5e8;
        border-left-color: #4caf50;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #5a6fd8 0%, #6a4190 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'app_initialized' not in st.session_state:
        st.session_state.app_initialized = False
    if 'database_connected' not in st.session_state:
        st.session_state.database_connected = False
    if 'codebase_ingested' not in st.session_state:
        st.session_state.codebase_ingested = False
    if 'knowledge_graph_created' not in st.session_state:
        st.session_state.knowledge_graph_created = False
    if 'vector_index_created' not in st.session_state:
        st.session_state.vector_index_created = False
    if 'system_ready' not in st.session_state:
        st.session_state.system_ready = False
    if 'documents' not in st.session_state:
        st.session_state.documents = []
    if 'codebase_path' not in st.session_state:
        st.session_state.codebase_path = ""
    if 'query_processor' not in st.session_state:
        st.session_state.query_processor = None

def sync_session_state_with_database():
    """Sync session state with actual database state to handle page refreshes"""
    if not st.session_state.get('database_connected', False):
        return
    
    try:
        connection = get_neo4j_connection()
        success, db_info = connection.get_database_info()
        
        if success and isinstance(db_info, dict):
            node_count = db_info.get('node_count', 0)
            has_vector_index = db_info.get('has_vector_index', False)
            
            # If we have data in the database, update session state accordingly
            if node_count > 0:
                # Check if we have CodeChunk nodes (indicates ingestion completed)
                driver = connection.get_driver()
                if driver:
                    with driver.session() as session:
                        # Check for CodeChunk nodes (safely handle case where they don't exist)
                        try:
                            chunk_result = session.run("MATCH (c:CodeChunk) RETURN count(c) as count LIMIT 1")
                            chunk_count = chunk_result.single()["count"]
                        except Exception:
                            chunk_count = 0
                        
                        # Check for knowledge graph entities (safely handle case where CodeChunk label doesn't exist)
                        try:
                            kg_result = session.run("MATCH (n) WHERE NOT n:CodeChunk RETURN count(n) as count LIMIT 1")
                            kg_count = kg_result.single()["count"]
                        except Exception:
                            # If CodeChunk label doesn't exist, count all nodes
                            try:
                                kg_result = session.run("MATCH (n) RETURN count(n) as count LIMIT 1")
                                kg_count = kg_result.single()["count"]
                            except Exception:
                                kg_count = 0
                        
                        # Update session state based on what we find
                        logger.info(f"Sync check: {chunk_count} CodeChunks, {kg_count} KG entities, vector_index={has_vector_index}")
                        
                        if chunk_count > 0:
                            st.session_state.codebase_ingested = True
                            st.session_state.vector_index_created = True  # CodeChunks exist means vector index was created
                            
                        if kg_count > 0:
                            st.session_state.knowledge_graph_created = True
                            
                        if has_vector_index:
                            st.session_state.vector_index_created = True
                            
                        # If we have ingestion, knowledge graph, and vector index, system is ready
                        if (st.session_state.codebase_ingested and 
                            st.session_state.knowledge_graph_created and 
                            st.session_state.vector_index_created):
                            st.session_state.system_ready = True
                            
                            # Initialize query processor if not already done
                            if st.session_state.query_processor is None:
                                from app.query_processor import QueryProcessor
                                query_processor = QueryProcessor()
                                
                                # Setup retrievers for the query processor
                                setup_success, setup_message = query_processor.setup_retrievers()
                                if setup_success:
                                    st.session_state.query_processor = query_processor
                                    logger.info("✅ QueryProcessor initialized and set up successfully during sync")
                                else:
                                    logger.warning(f"Failed to setup QueryProcessor during sync: {setup_message}")
                                    st.session_state.query_processor = None
                                    st.session_state.system_ready = False
                        
                        # Show notification if we detected existing data
                        if chunk_count > 0 or kg_count > 0:
                            st.sidebar.success(f"🔍 Auto-detected: {chunk_count} code chunks, {kg_count} entities")
                            
                            # Show detailed sync status
                            if 'sync_notification_shown' not in st.session_state:
                                st.session_state.sync_notification_shown = True
                                
                                # Create detailed status message
                                status_parts = []
                                status_parts.append(f"Found {chunk_count} code chunks")
                                status_parts.append(f"{kg_count} knowledge graph entities")
                                if has_vector_index:
                                    status_parts.append("vector index ready")
                                
                                if st.session_state.get('system_ready', False):
                                    st.success(f"🔄 Synced with existing database: {', '.join(status_parts)}. System ready for queries!")
                                else:
                                    st.info(f"🔄 Synced with existing database: {', '.join(status_parts)}. Workflow updated.")
                                    if st.session_state.query_processor is None:
                                        st.warning("⚠️ QueryProcessor setup failed. You may need to use the 'Sync with Database' button in the Database tab.")
            
    except Exception as e:
        logger.warning(f"Failed to sync session state with database: {e}")
        # Don't show error to user as this is a background sync operation

def initialize_app():
    """Initialize the application and database connection"""
    if not st.session_state.app_initialized:
        with st.spinner("🔧 Initializing CodeGraph..."):
            success, message = initialize_database()
            
            if success:
                st.session_state.database_connected = True
                st.session_state.app_initialized = True
                logger.info("✅ Application initialized successfully")
                return True, "✅ Application initialized successfully"
            else:
                st.session_state.database_connected = False
                logger.error(f"Database initialization failed: {message}")
                return False, f"❌ Database initialization failed: {message}"
    
    return st.session_state.database_connected, "Already initialized"

def show_system_status():
    """Display comprehensive system status in the sidebar"""
    st.sidebar.markdown("## 🔧 System Status")
    
    config = Config()
    
    # Database Status
    if st.session_state.get('database_connected', False):
        st.sidebar.markdown('<div class="status-card">✅ Neo4j Connected</div>', unsafe_allow_html=True)
        
        # Get database info
        connection = get_neo4j_connection()
        success, db_info = connection.get_database_info()
        
        if success and isinstance(db_info, dict):
            st.sidebar.metric("📊 Nodes", db_info.get('node_count', 0))
            st.sidebar.metric("🔗 Relationships", db_info.get('relationship_count', 0))
            
            if db_info.get('has_vector_index', False):
                st.sidebar.markdown('<div class="status-card">🧠 Vector Index Ready</div>', unsafe_allow_html=True)
            else:
                st.sidebar.markdown('<div class="warning-card">⚠️ No Vector Index</div>', unsafe_allow_html=True)
    else:
        st.sidebar.markdown('<div class="error-card">❌ Neo4j Disconnected</div>', unsafe_allow_html=True)
    
    # API Configuration Status
    if config.OPENAI_API_KEY:
        st.sidebar.markdown('<div class="status-card">✅ OpenAI API Key Set</div>', unsafe_allow_html=True)
    else:
        st.sidebar.markdown('<div class="error-card">❌ OpenAI API Key Missing</div>', unsafe_allow_html=True)
    
    # Database Management Section
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 🗄️ Database Management")
    
    if st.session_state.get('database_connected', False):
        # Clear Database Button
        if st.sidebar.button("🗑️ Clear Database", type="secondary", help="⚠️ This will delete ALL data in the database"):
            if 'confirm_clear' not in st.session_state:
                st.session_state.confirm_clear = False
            
            if not st.session_state.confirm_clear:
                st.session_state.confirm_clear = True
                st.sidebar.warning("⚠️ Click again to confirm deletion")
            else:
                # Import the clear function
                from app.utilities.neo4j_utils import clear_database
                
                with st.spinner("🗑️ Clearing database..."):
                    driver = connection.get_driver()
                    if driver:
                        success, message = clear_database(driver, confirm=True)
                        if success:
                            st.sidebar.success("✅ Database cleared successfully!")
                            # Reset session state
                            st.session_state.codebase_ingested = False
                            st.session_state.knowledge_graph_created = False
                            st.session_state.vector_index_created = False
                            st.session_state.system_ready = False
                            st.session_state.documents = []
                            st.session_state.query_processor = None
                            st.session_state.confirm_clear = False
                            st.rerun()
                        else:
                            st.sidebar.error(f"❌ Failed to clear database: {message}")
                            st.session_state.confirm_clear = False
    else:
        st.sidebar.info("Connect to database to manage data")
    
    # Configuration Details
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Configuration")
    st.sidebar.text(f"Neo4j URI: {config.NEO4J_URI}")
    st.sidebar.text(f"Embedding Model: {config.EMBEDDING_MODEL}")
    st.sidebar.text(f"LLM Model: {config.LLM_MODEL}")
    st.sidebar.text(f"Chunk Size: {config.CHUNK_SIZE}")
    
    # Debug Information
    if st.session_state.get('database_connected', False):
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🐛 Debug Info")
        connection = get_neo4j_connection()
        driver_status = "✅ Available" if connection.get_driver() else "❌ None"
        st.sidebar.text(f"Driver: {driver_status}")
        
        # Quick connection test
        if st.sidebar.button("🧪 Test Connection", type="secondary"):
            test_success, test_message = connection.test_connection()
            if test_success:
                st.sidebar.success("✅ Connection test passed")
            else:
                st.sidebar.error(f"❌ Connection test failed")
                # Try to auto-reconnect
                reconnect_success, reconnect_message = connection.connect()
                if reconnect_success:
                    st.sidebar.success("✅ Auto-reconnected successfully!")
                    st.rerun()
                else:
                    st.sidebar.error(f"❌ Auto-reconnect failed")

def show_workflow_progress():
    """Display workflow progress"""
    st.markdown("### 🔄 Workflow Progress")
    
    steps = [
        ("🔧 System Initialization", st.session_state.get('app_initialized', False)),
        ("📥 Codebase Ingestion", st.session_state.get('codebase_ingested', False)),
        ("🧠 Knowledge Graph Creation", st.session_state.get('knowledge_graph_created', False)),
        ("🔍 Vector Index Creation", st.session_state.get('vector_index_created', False)),
        ("🚀 System Ready", st.session_state.get('system_ready', False))
    ]
    
    cols = st.columns(len(steps))
    for i, (step_name, completed) in enumerate(steps):
        with cols[i]:
            if completed:
                st.markdown(f'<div class="workflow-step completed-step">{step_name}<br/>✅ Complete</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="workflow-step">{step_name}<br/>⏳ Pending</div>', unsafe_allow_html=True)

def handle_codebase_input():
    """Handle codebase input (GitHub URL or local folder)"""
    st.markdown("## 📥 Codebase Input")
    
    input_type = st.radio(
        "Choose input type:",
        ["🌐 GitHub Repository", "📁 Local Folder"],
        horizontal=True
    )
    
    if input_type == "🌐 GitHub Repository":
        repo_url = st.text_input(
            "GitHub Repository URL:",
            placeholder="https://github.com/username/repository",
            help="Enter the full GitHub repository URL (HTTPS or SSH)"
        )
        
        if st.button("🔄 Clone Repository", type="primary"):
            if repo_url:
                with st.spinner("🔄 Cloning repository..."):
                    success, message, cloned_path = clone_repository(repo_url)
                    
                    if success:
                        st.success(message)
                        st.session_state.codebase_path = cloned_path
                        return True
                    else:
                        st.error(message)
                        return False
            else:
                st.warning("Please enter a repository URL")
                return False
    
    else:  # Local Folder
        folder_path = st.text_input(
            "Local Folder Path:",
            placeholder="/path/to/your/codebase",
            help="Enter the absolute path to your local codebase folder"
        )
        
        if st.button("📁 Validate Folder", type="primary"):
            if folder_path:
                with st.spinner("📁 Validating folder..."):
                    success, message, validated_path = read_local_folder(folder_path)
                    
                    if success:
                        st.success(message)
                        st.session_state.codebase_path = validated_path
                        return True
                    else:
                        st.error(message)
                        return False
            else:
                st.warning("Please enter a folder path")
                return False
    
    return False

def handle_ingestion():
    """Handle codebase ingestion and parsing"""
    st.markdown("## 🔄 Codebase Ingestion")
    
    if not st.session_state.codebase_path:
        st.warning("Please provide a codebase path first")
        return False
    
    st.info(f"📁 Codebase Path: {st.session_state.codebase_path}")
    
    # Ingestion parameters
    col1, col2 = st.columns(2)
    with col1:
        chunk_size = st.number_input("Chunk Size", min_value=100, max_value=2000, value=500)
        include_extensions = st.multiselect(
            "Include Extensions",
            ['.py', '.java', '.js', '.ts', '.cpp', '.c', '.go', '.rs', '.rb'],
            default=['.py', '.java', '.js', '.ts']
        )
    
    with col2:
        chunk_overlap = st.number_input("Chunk Overlap", min_value=0, max_value=200, value=50)
        max_file_size = st.number_input("Max File Size (MB)", min_value=1, max_value=50, value=10)
    
    if st.button("🚀 Start Ingestion", type="primary"):
        with st.spinner("🔄 Parsing codebase..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Parse code chunks
            status_text.text("📄 Discovering code files...")
            progress_bar.progress(25)
            
            success, message, documents = parse_code_chunks(
                codebase_path=st.session_state.codebase_path,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                include_extensions=include_extensions or None
            )
            
            progress_bar.progress(100)
            
            if success:
                st.session_state.documents = documents
                st.session_state.codebase_ingested = True
                
                # Show ingestion results
                st.success(f"✅ Ingestion completed! {len(documents)} code chunks created.")
                
                # Display statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📄 Total Chunks", len(documents))
                with col2:
                    languages = set(doc.metadata.get('language', 'unknown') for doc in documents)
                    st.metric("🔤 Languages", len(languages))
                with col3:
                    files = set(doc.metadata.get('file_path', '') for doc in documents)
                    st.metric("📁 Files", len(files))
                
                return True
            else:
                st.error(f"❌ Ingestion failed: {message}")
                return False
    
    return False

def handle_knowledge_graph_creation():
    """Handle knowledge graph creation"""
    st.markdown("## 🧠 Knowledge Graph Creation")
    
    if not st.session_state.codebase_ingested or not st.session_state.documents:
        st.warning("Please complete codebase ingestion first")
        return False
    
    st.info(f"📊 Ready to process {len(st.session_state.documents)} code chunks")
    
    if st.button("🧠 Create Knowledge Graph", type="primary"):
        with st.spinner("🧠 Creating knowledge graph..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            graph_builder = GraphBuilder()
            
            status_text.text("🔄 Initializing LLM and graph transformer...")
            progress_bar.progress(25)
            
            status_text.text("🧠 Extracting entities and relationships...")
            progress_bar.progress(50)
            
            success, message = graph_builder.generate_knowledge_graph(st.session_state.documents)
            
            progress_bar.progress(100)
            
            if success:
                st.session_state.knowledge_graph_created = True
                st.success(message)
                return True
            else:
                st.error(message)
                return False
    
    return False

def handle_vector_index_creation():
    """Handle vector index creation"""
    st.markdown("## 🔍 Vector Index Creation")
    
    if not st.session_state.knowledge_graph_created:
        st.warning("Please create knowledge graph first")
        return False
    
    st.info(f"🔍 Ready to create vector embeddings for {len(st.session_state.documents)} code chunks")
    
    if st.button("🔍 Create Vector Index", type="primary"):
        with st.spinner("🔍 Creating vector index..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Verify database connection before proceeding
            status_text.text("🔄 Verifying database connection...")
            connection = get_neo4j_connection()
            
            # Test the connection to ensure it's still active
            test_success, test_message = connection.test_connection()
            if not test_success:
                # Try to reconnect if connection test fails
                status_text.text("⚠️ Connection lost, attempting to reconnect...")
                reconnect_success, reconnect_message = connection.connect()
                if not reconnect_success:
                    st.error(f"❌ Failed to reconnect to Neo4j: {reconnect_message}")
                    st.info("💡 **Troubleshooting Tips:**\n- Check if Neo4j is running\n- Verify your credentials in .env file\n- Try refreshing the page")
                    return False
                else:
                    st.success("✅ Successfully reconnected to Neo4j!")
            else:
                status_text.text("✅ Database connection verified")
            
            progress_bar.progress(25)
            
            # Initialize GraphBuilder with verified connection
            status_text.text("🔧 Initializing graph builder...")
            graph_builder = GraphBuilder()
            
            # Double-check connection in GraphBuilder
            if not graph_builder.is_connected or not graph_builder.driver:
                st.error("❌ GraphBuilder not properly connected to Neo4j. Please check the Database tab and ensure connection is active.")
                st.info("💡 **Try this:**\n- Go to the Database tab\n- Click 'Sync with Database'\n- Return to this tab and try again")
                return False
            
            status_text.text("🧮 Generating embeddings...")
            progress_bar.progress(50)
            
            success, message = graph_builder.create_vector_index(st.session_state.documents)
            
            progress_bar.progress(100)
            
            if success:
                st.session_state.vector_index_created = True
                st.session_state.system_ready = True
                
                # Initialize query processor
                query_processor = QueryProcessor()
                setup_success, setup_message = query_processor.setup_retrievers()
                
                if setup_success:
                    st.session_state.query_processor = query_processor
                    st.success(f"{message}\n\n✅ System is now ready for queries!")
                    return True
                else:
                    st.error(f"Vector index created but query setup failed: {setup_message}")
                    return False
            else:
                st.error(message)
                return False
    
    return False

def handle_query_interface():
    """Handle query interface and processing"""
    st.markdown("## 🔍 Query Interface")
    
    if not st.session_state.system_ready or not st.session_state.query_processor:
        st.warning("Please complete the full workflow first")
        return
    
    st.success("🚀 System is ready! Ask questions about your codebase.")
    
    # Query input
    query = st.text_area(
        "Enter your question:",
        placeholder="e.g., 'How does the authentication system work?' or 'Show me the main classes and their relationships'",
        height=100
    )
    
    # Query parameters
    col1, col2 = st.columns(2)
    with col1:
        k_value = st.slider("Number of results", min_value=3, max_value=15, value=5)
    with col2:
        include_graph = st.checkbox("Include graph context", value=True)
    
    if st.button("🔍 Search", type="primary") and query:
        with st.spinner("🔍 Processing query..."):
            success, response, context_data = st.session_state.query_processor.process_query(
                query=query,
                k=k_value,
                include_graph_context=include_graph
            )
            
            if success:
                # Display response
                st.markdown("### 💬 Response")
                st.markdown(response)
                
                # Display context information
                with st.expander("📊 Query Context Details"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📄 Chunks Found", context_data.get('num_chunks_found', 0))
                    with col2:
                        st.metric("🏷️ Entities Found", context_data.get('num_entities_found', 0))
                    with col3:
                        st.metric("🔗 Relationships Found", context_data.get('num_relationships_found', 0))
                
                # Show vector results outside the expander to avoid nesting
                if context_data.get('vector_results'):
                    st.markdown("### 🔍 Most Relevant Code Chunks")
                    for i, result in enumerate(context_data['vector_results'][:3]):
                        st.markdown(f"**Chunk {i+1}**: `{result.get('file_path', 'Unknown')}` (Similarity Score: `{result.get('similarity_score', 0):.3f}`)")
                        st.code(result.get('text', ''), language=result.get('language', 'text'))
                        st.markdown("---")
            else:
                st.error(f"❌ Query failed: {response}")

def handle_database_management():
    """Handle database management and statistics"""
    st.markdown("## 🗄️ Database Management")
    
    if not st.session_state.get('database_connected', False):
        st.warning("Please establish database connection first")
        return
    
    connection = get_neo4j_connection()
    driver = connection.get_driver()
    
    if not driver:
        st.error("❌ Database driver not available")
        return
    
    # Import utilities
    from app.utilities.neo4j_utils import clear_database, get_database_statistics
    
    # Database Statistics Section
    st.markdown("### 📊 Database Statistics")
    
    if st.button("🔄 Refresh Statistics", type="secondary"):
        with st.spinner("📊 Gathering database statistics..."):
            success, message, stats = get_database_statistics(driver)
            
            if success:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("📊 Total Nodes", stats.get('total_nodes', 0))
                    st.metric("🔗 Total Relationships", stats.get('total_relationships', 0))
                
                with col2:
                    st.metric("🏷️ Node Types", len(stats.get('node_labels', {})))
                    st.metric("🔗 Relationship Types", len(stats.get('relationship_types', {})))
                
                # Node Labels Breakdown
                if stats.get('node_labels'):
                    st.markdown("#### 🏷️ Node Labels Breakdown")
                    label_data = stats['node_labels']
                    for label, count in label_data.items():
                        st.write(f"• **{label}**: {count} nodes")
                
                # Relationship Types Breakdown
                if stats.get('relationship_types'):
                    st.markdown("#### 🔗 Relationship Types Breakdown")
                    rel_data = stats['relationship_types']
                    for rel_type, count in rel_data.items():
                        st.write(f"• **{rel_type}**: {count} relationships")
            else:
                st.error(f"❌ Failed to get statistics: {message}")
    
    st.markdown("---")
    
    # Database Management Actions
    st.markdown("### 🛠️ Database Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🗑️ Clear Database")
        st.warning("⚠️ **Warning**: This will permanently delete ALL data in the database!")
        
        # Two-step confirmation process
        if 'confirm_clear_tab' not in st.session_state:
            st.session_state.confirm_clear_tab = False
        
        if st.button("🗑️ Clear All Data", type="primary"):
            if not st.session_state.confirm_clear_tab:
                st.session_state.confirm_clear_tab = True
                st.warning("⚠️ Click 'Confirm Deletion' below to proceed")
            
        if st.session_state.confirm_clear_tab:
            if st.button("💥 Confirm Deletion", type="primary"):
                with st.spinner("🗑️ Clearing database..."):
                    success, message = clear_database(driver, confirm=True)
                    
                    if success:
                        st.success("✅ Database cleared successfully!")
                        # Reset session state
                        st.session_state.codebase_ingested = False
                        st.session_state.knowledge_graph_created = False
                        st.session_state.vector_index_created = False
                        st.session_state.system_ready = False
                        st.session_state.documents = []
                        st.session_state.query_processor = None
                        st.session_state.confirm_clear_tab = False
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to clear database: {message}")
                        st.session_state.confirm_clear_tab = False
            
            if st.button("❌ Cancel", type="secondary"):
                st.session_state.confirm_clear_tab = False
                st.rerun()
    
    with col2:
        st.markdown("#### 📈 Quick Actions")
        
        if st.button("🔍 View Current Data", type="secondary"):
            # Show current database state
            success, db_info = connection.get_database_info()
            if success:
                st.json({
                    "nodes": db_info.get('node_count', 0),
                    "relationships": db_info.get('relationship_count', 0),
                    "labels": db_info.get('node_labels', []),
                    "relationship_types": db_info.get('relationship_types', []),
                    "has_vector_index": db_info.get('has_vector_index', False)
                })
        
        if st.button("🚀 Reset Workflow State", type="secondary"):
            # Reset only session state, keep database
            st.session_state.codebase_ingested = False
            st.session_state.knowledge_graph_created = False
            st.session_state.vector_index_created = False
            st.session_state.system_ready = False
            st.session_state.documents = []
            st.session_state.query_processor = None
            st.success("✅ Workflow state reset! You can now start fresh while keeping your data.")
            st.rerun()
            
        if st.button("🔄 Sync with Database", type="secondary"):
            # Sync session state with database content
            with st.spinner("🔄 Syncing with database..."):
                sync_session_state_with_database()
                if st.session_state.get('system_ready', False):
                    st.success("✅ Session state synced with database! System ready for queries.")
                else:
                    st.warning("⚠️ Session state synced, but system not fully ready. Check if all data exists.")
                st.rerun()
    
    st.markdown("---")
    
    # Tips Section
    st.markdown("### 💡 Tips")
    st.info("""
    **🔄 When to clear the database:**
    - Before processing a completely different codebase
    - When you want to start fresh without duplicates
    - After experimenting and want clean results
    
    **🚀 When to reset workflow state:**
    - Keep existing data but restart the UI workflow
    - Useful after page refresh to skip re-ingestion
    - When you want to query existing data immediately
    
    **🔄 When to sync with database:**
    - After page refresh when you see "complete workflow first"
    - When database has data but UI doesn't recognize it
    - Automatically happens on app startup
    """)

def main():
    """Main Streamlit application"""
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🕸️ CodeGraph</h1>
        <h3>GraphRAG-Powered Codebase Analysis</h3>
        <p>Transform your codebase into an intelligent knowledge graph for advanced querying and analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize application
    init_success, init_message = initialize_app()
    
    # Sync session state with existing database data
    if init_success:
        sync_session_state_with_database()
    
    # Show system status in sidebar
    show_system_status()
    
    # Show workflow progress
    show_workflow_progress()
    
    if not init_success:
        st.error(init_message)
        st.markdown("### 🔧 Troubleshooting:")
        st.markdown("1. Ensure Neo4j is running on `localhost:7687`")
        st.markdown("2. Check your `.env` file has correct Neo4j credentials")
        st.markdown("3. Verify Neo4j authentication (default: neo4j/password)")
        st.markdown("4. Set your OpenAI API key in the `.env` file")
        return
    
    # Main workflow tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📥 Input", "🔄 Ingestion", "🧠 Knowledge Graph", "🔍 Vector Index", "💬 Query", "🗄️ Database"
    ])
    
    with tab1:
        handle_codebase_input()
    
    with tab2:
        handle_ingestion()
    
    with tab3:
        handle_knowledge_graph_creation()
    
    with tab4:
        handle_vector_index_creation()
    
    with tab5:
        handle_query_interface()
    
    with tab6:
        handle_database_management()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>🕸️ <strong>CodeGraph</strong> - Powered by Neo4j, OpenAI, and LangChain</p>
        <p>Transform your codebase into intelligent knowledge graphs for advanced analysis</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 