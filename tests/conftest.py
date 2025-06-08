# Code Graph - Test Configuration and Fixtures
# Optimized fixtures for efficient testing with API cost control

import pytest
import logging
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

from app.database import get_neo4j_connection, initialize_database
from app.ingestion import parse_code_chunks
from tests.fixtures.test_data_manager import get_self_contained_test_manager, get_test_data_manager

logger = logging.getLogger(__name__)

# Test configuration flags
SKIP_INTEGRATION_TESTS = os.getenv("SKIP_INTEGRATION_TESTS", "true").lower() == "true"
SKIP_API_COST_TESTS = os.getenv("SKIP_API_COST_TESTS", "false").lower() == "true"
SKIP_SLOW_TESTS = os.getenv("SKIP_SLOW_TESTS", "false").lower() == "true"

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "api_cost: mark test as making expensive API calls"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as full system integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection based on environment flags"""
    skip_integration = pytest.mark.skip(reason="Integration tests skipped (SKIP_INTEGRATION_TESTS=true)")
    skip_api_cost = pytest.mark.skip(reason="API cost tests skipped (SKIP_API_COST_TESTS=true)")
    skip_slow = pytest.mark.skip(reason="Slow tests skipped (SKIP_SLOW_TESTS=true)")
    
    for item in items:
        # Skip integration tests by default
        if SKIP_INTEGRATION_TESTS and "test_full_system.py" in str(item.fspath):
            item.add_marker(skip_integration)
        
        # Skip API cost tests if flag is set
        if SKIP_API_COST_TESTS and "api_cost" in item.keywords:
            item.add_marker(skip_api_cost)
        
        # Skip slow tests if flag is set
        if SKIP_SLOW_TESTS and "slow" in item.keywords:
            item.add_marker(skip_slow)

# Session-scoped fixtures for shared data
@pytest.fixture(scope="session")
def session_config():
    """Session-wide test configuration"""
    return {
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "max_chunks_per_pattern": 3,  # Reduced for cost control with self-contained data
        "max_chunks_total": 8,        # Smaller set with focused samples
        "test_patterns": ["adapter", "factory", "observer"],  # Available self-contained patterns
        "skip_integration": SKIP_INTEGRATION_TESTS,
        "skip_api_cost": SKIP_API_COST_TESTS,
        "skip_slow": SKIP_SLOW_TESTS
    }

@pytest.fixture(scope="session")
def selected_patterns(session_config):
    """Session-wide selected patterns for testing"""
    return session_config["test_patterns"]

@pytest.fixture(scope="session")
def cached_test_documents(session_config, selected_patterns):
    """
    Session-scoped cached test documents using self-contained sample code.
    
    No longer depends on external repositories - uses built-in Java samples.
    This fixture dramatically reduces test execution time and eliminates
    external dependencies.
    """
    logger.info("🔄 Creating cached test documents from self-contained samples")
    
    test_manager = get_self_contained_test_manager()
    available_patterns = test_manager.get_available_patterns()
    
    if not available_patterns:
        logger.warning("No patterns available for testing")
        return {}
    
    cached_docs = {}
    total_docs = 0
    max_total = session_config["max_chunks_total"]
    
    for pattern in available_patterns:
        if total_docs >= max_total:
            break
        
        try:
            # Get documents for this pattern from self-contained samples
            max_per_pattern = min(
                session_config["max_chunks_per_pattern"],
                max_total - total_docs
            )
            
            pattern_docs = test_manager.get_pattern_documents(pattern, max_per_pattern)
            
            if pattern_docs:
                cached_docs[pattern] = pattern_docs
                total_docs += len(pattern_docs)
                
                logger.info(f"✅ Cached {len(pattern_docs)} documents for pattern '{pattern}'")
            else:
                logger.warning(f"❌ No documents found for pattern '{pattern}'")
                
        except Exception as e:
            logger.error(f"❌ Error getting documents for pattern '{pattern}': {str(e)}")
    
    logger.info(f"🎯 Session cache created: {total_docs} total documents across {len(cached_docs)} patterns")
    return cached_docs

@pytest.fixture(scope="session")
def sample_documents(cached_test_documents):
    """Session-scoped sample documents for basic testing"""
    all_docs = []
    for pattern_docs in cached_test_documents.values():
        all_docs.extend(pattern_docs)
    
    # Return first 6 documents for consistent testing
    return all_docs[:6] if all_docs else []

@pytest.fixture(scope="session")
def small_document_set(cached_test_documents):
    """Session-scoped small document set for quick tests"""
    all_docs = []
    for pattern_docs in cached_test_documents.values():
        all_docs.extend(pattern_docs[:2])  # Max 2 per pattern
    
    return all_docs[:4] if all_docs else []

@pytest.fixture(scope="session")
def medium_document_set(cached_test_documents):
    """Session-scoped medium document set for moderate tests"""
    all_docs = []
    for pattern_docs in cached_test_documents.values():
        all_docs.extend(pattern_docs[:4])  # Max 4 per pattern
    
    return all_docs[:10] if all_docs else []

# Function-scoped fixtures for test isolation
@pytest.fixture(scope="session")
def database_connection():
    """Session-scoped database connection for compatibility"""
    connection = get_neo4j_connection()
    success = initialize_database()
    if not success:
        pytest.skip("Database connection not available")
    return connection

@pytest.fixture
def clean_database():
    """Function-scoped clean database for each test"""
    connection = get_neo4j_connection()
    
    # Clear database before test
    from app.utilities.neo4j_utils import clear_knowledge_graph
    clear_knowledge_graph(connection.get_driver(), confirm=True)
    
    yield connection
    
    # Clear database after test (optional, can be disabled for speed)
    # clear_knowledge_graph(connection.get_driver(), confirm=True)

@pytest.fixture
def test_config(session_config):
    """Function-scoped test configuration (copy of session config)"""
    return session_config.copy()

# Optimized document fixtures
@pytest.fixture
def quick_documents(small_document_set):
    """Quick documents for fast unit tests"""
    return small_document_set

@pytest.fixture
def standard_documents(sample_documents):
    """Standard documents for regular tests"""
    return sample_documents

@pytest.fixture
def extended_documents(medium_document_set):
    """Extended documents for comprehensive tests"""
    return medium_document_set

# Mock fixtures for API cost reduction
@pytest.fixture
def mock_openai_embeddings():
    """Mock OpenAI embeddings to avoid API costs in unit tests"""
    import numpy as np
    
    class MockEmbeddings:
        def embed_query(self, text: str) -> List[float]:
            # Generate deterministic fake embedding based on text hash
            import hashlib
            text_hash = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
            np.random.seed(text_hash)
            return np.random.random(3072).tolist()
        
        def embed_documents(self, texts: List[str]) -> List[List[float]]:
            return [self.embed_query(text) for text in texts]
    
    return MockEmbeddings()

@pytest.fixture
def mock_llm_responses():
    """Mock LLM responses to avoid API costs in unit tests"""
    
    class MockLLM:
        def invoke(self, prompt: str) -> str:
            # Generate deterministic fake response based on prompt
            if "singleton" in prompt.lower():
                return "This is a mock response about the Singleton design pattern."
            elif "factory" in prompt.lower():
                return "This is a mock response about the Factory design pattern."
            else:
                return "This is a mock response about the code."
    
    return MockLLM()

# Database state fixtures
@pytest.fixture
def empty_database(clean_database):
    """Explicitly empty database"""
    return clean_database

@pytest.fixture
def database_with_vector_index(clean_database, quick_documents):
    """Database with vector index pre-created"""
    if not quick_documents:
        pytest.skip("No documents available for vector index")
    
    from app.graph_builder import GraphBuilder
    graph_builder = GraphBuilder()
    
    # Create only vector index (no knowledge graph)
    success, message = graph_builder.create_vector_index(quick_documents)
    if not success:
        pytest.skip(f"Failed to create vector index: {message}")
    
    return clean_database

# Test data factories
class DocumentFactory:
    """Factory for creating test documents"""
    
    @staticmethod
    def create_simple_document(content: str = "public class Test {}", 
                             file_path: str = "Test.java",
                             language: str = "java") -> Any:
        """Create a simple test document"""
        from langchain.schema import Document
        
        return Document(
            page_content=content,
            metadata={
                "file_path": file_path,
                "language": language,
                "start_line": 1,
                "end_line": 1,
                "chunk_id": f"chunk_{hash(content) % 10000}"
            }
        )
    
    @staticmethod
    def create_java_class_document(class_name: str = "TestClass") -> Any:
        """Create a Java class document"""
        content = f"""
public class {class_name} {{
    private static {class_name} instance;
    
    private {class_name}() {{}}
    
    public static {class_name} getInstance() {{
        if (instance == null) {{
            instance = new {class_name}();
        }}
        return instance;
    }}
}}
"""
        return DocumentFactory.create_simple_document(
            content=content.strip(),
            file_path=f"{class_name}.java"
        )

@pytest.fixture
def document_factory():
    """Document factory for creating test documents"""
    return DocumentFactory

# Performance monitoring fixtures
@pytest.fixture
def performance_monitor():
    """Monitor test performance"""
    import time
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.metrics = {}
        
        def start(self, operation: str):
            self.start_time = time.time()
            self.current_operation = operation
        
        def end(self):
            if self.start_time:
                duration = time.time() - self.start_time
                self.metrics[self.current_operation] = duration
                return duration
            return 0
        
        def get_metrics(self):
            return self.metrics.copy()
    
    return PerformanceMonitor()

# Conditional fixtures based on environment
@pytest.fixture
def real_or_mock_embeddings(mock_openai_embeddings):
    """Return real embeddings for integration tests, mock for unit tests"""
    if SKIP_API_COST_TESTS:
        return mock_openai_embeddings
    else:
        from langchain_openai import OpenAIEmbeddings
        from app.config import Config
        config = Config()
        return OpenAIEmbeddings(
            model="text-embedding-3-large",
            openai_api_key=config.OPENAI_API_KEY
        )

# Utility fixtures
@pytest.fixture
def temp_directory():
    """Temporary directory for test files"""
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def test_logger():
    """Test-specific logger"""
    import logging
    
    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)
    
    # Add handler if not already present
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

# Java patterns path fixture
@pytest.fixture(scope="session")
def java_patterns_path():
    """Path to Java design patterns repository for testing"""
    patterns_path = Path("cloned_repos/java-design-patterns")
    
    if not patterns_path.exists():
        pytest.skip(
            "Java design patterns repository not found. "
            "Please clone https://github.com/iluwatar/java-design-patterns "
            "into cloned_repos/java-design-patterns for these tests to run."
        )
    
    return str(patterns_path)

# Environment info fixture
@pytest.fixture(scope="session")
def test_environment_info():
    """Information about test environment"""
    return {
        "skip_integration": SKIP_INTEGRATION_TESTS,
        "skip_api_cost": SKIP_API_COST_TESTS,
        "skip_slow": SKIP_SLOW_TESTS,
        "python_version": os.sys.version,
        "working_directory": os.getcwd()
    } 