# Code Graph - Graph Statistics Utilities
# Utility functions for getting statistics about knowledge graphs and vector indexes

import logging
from typing import Tuple, Dict, Any
from neo4j import Driver

logger = logging.getLogger(__name__)


def get_graph_creation_stats(driver: Driver) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Get statistics about the created knowledge graph
    
    Args:
        driver: Neo4j driver instance
        
    Returns:
        Tuple[bool, str, Dict]: (success, message, stats)
    """
    try:
        from app.utilities.neo4j_utils import get_database_statistics
        return get_database_statistics(driver)
    except Exception as e:
        return False, f"Error getting graph creation stats: {str(e)}", {}


def get_vector_index_stats(driver: Driver) -> Tuple[bool, str]:
    """
    Get statistics about the vector index
    
    Args:
        driver: Neo4j driver instance
        
    Returns:
        Tuple[bool, str]: (success, message)
    """
    try:
        with driver.session() as session:
            # Count CodeChunk nodes (safely handle case where they don't exist)
            try:
                chunk_result = session.run("MATCH (c:CodeChunk) RETURN count(c) as chunk_count")
                chunk_record = chunk_result.single()
                chunk_count = chunk_record["chunk_count"] if chunk_record else 0
            except Exception:
                chunk_count = 0
            
            # Count File nodes
            try:
                file_result = session.run("MATCH (f:File) RETURN count(f) as file_count")
                file_record = file_result.single()
                file_count = file_record["file_count"] if file_record else 0
            except Exception:
                file_count = 0
            
            # Count CONTAINS_CHUNK relationships (safely handle case where they don't exist)
            try:
                rel_result = session.run("MATCH ()-[r:CONTAINS_CHUNK]->() RETURN count(r) as rel_count")
                rel_record = rel_result.single()
                rel_count = rel_record["rel_count"] if rel_record else 0
            except Exception:
                rel_count = 0
            
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


def get_graphrag_system_stats(driver: Driver) -> Tuple[bool, str]:
    """
    Get comprehensive statistics about the GraphRAG system
    
    Args:
        driver: Neo4j driver instance
        
    Returns:
        Tuple[bool, str]: (success, message)
    """
    try:
        with driver.session() as session:
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