# Code Graph - Utilities Package
# This package contains utility functions used across the application

from .file_utils import (
    format_file_size,
    get_directory_size,
    is_likely_binary,
    read_file_content,
    should_exclude_file,
    has_valid_extension
)

from .folder_utils import (
    get_folder_statistics,
    list_cloned_repositories,
    cleanup_cloned_repositories
)

from .git_utils import (
    is_valid_repo_url,
    extract_repo_name,
    get_repository_info
)

from .neo4j_utils import (
    check_neo4j_health,
    clear_database,
    get_database_statistics,
    create_constraints_and_indexes,
    clear_knowledge_graph
)

from .graph_stats_utils import (
    get_graph_creation_stats,
    get_vector_index_stats,
    get_graphrag_system_stats
)

from .llm_utils import (
    prepare_context_for_llm,
    create_conversational_prompt,
    generate_fallback_response,
    generate_conversational_response
)

__all__ = [
    # File utilities
    'format_file_size',
    'get_directory_size', 
    'is_likely_binary',
    'read_file_content',
    'should_exclude_file',
    'has_valid_extension',
    
    # Folder utilities
    'get_folder_statistics',
    'list_cloned_repositories',
    'cleanup_cloned_repositories',
    
    # Git utilities
    'is_valid_repo_url',
    'extract_repo_name',
    'get_repository_info',
    
    # Neo4j utilities
    'check_neo4j_health',
    'clear_database',
    'get_database_statistics',
    'create_constraints_and_indexes',
    'clear_knowledge_graph',
    
    # Graph statistics utilities
    'get_graph_creation_stats',
    'get_vector_index_stats',
    'get_graphrag_system_stats',
    
    # LLM utilities
    'prepare_context_for_llm',
    'create_conversational_prompt',
    'generate_fallback_response',
    'generate_conversational_response'
] 