# Code Graph - Tests Package
# This package contains test functions for the application

from .test_ingestion import (
    test_repository_cloning,
    test_local_folder_reading,
    test_code_chunking
)

from .test_neo4j import (
    test_neo4j_connection,
    test_neo4j_health_check,
    test_database_statistics,
    test_connection_error_handling,
    test_connection_lifecycle,
    run_all_neo4j_tests
)

from .test_knowledge_graph import (
    test_knowledge_graph_generation_small_sample,
    test_knowledge_graph_with_spring_petclinic,
    test_knowledge_graph_statistics,
    test_knowledge_graph_clear,
    run_all_knowledge_graph_tests
)

from .test_knowledge_graph_mock import (
    test_knowledge_graph_structure,
    test_knowledge_graph_imports,
    test_knowledge_graph_configuration,
    run_all_mock_tests
)

from .test_openai_config import (
    test_openai_api_key_config,
    test_openai_api_key_environment,
    test_openai_api_curl,
    test_langchain_openai_integration,
    run_all_openai_tests
)

__all__ = [
    # Ingestion tests
    'test_repository_cloning',
    'test_local_folder_reading', 
    'test_code_chunking',
    
    # Neo4j tests
    'test_neo4j_connection',
    'test_neo4j_health_check',
    'test_database_statistics',
    'test_connection_error_handling',
    'test_connection_lifecycle',
    'run_all_neo4j_tests',
    
    # Knowledge Graph tests
    'test_knowledge_graph_generation_small_sample',
    'test_knowledge_graph_with_spring_petclinic',
    'test_knowledge_graph_statistics',
    'test_knowledge_graph_clear',
    'run_all_knowledge_graph_tests',
    
    # Knowledge Graph mock tests
    'test_knowledge_graph_structure',
    'test_knowledge_graph_imports',
    'test_knowledge_graph_configuration',
    'run_all_mock_tests',
    
    # OpenAI configuration tests
    'test_openai_api_key_config',
    'test_openai_api_key_environment',
    'test_openai_api_curl',
    'test_langchain_openai_integration',
    'run_all_openai_tests'
] 