# Code Graph - Neo4j Utilities
# Neo4j database utility functions

import logging
from typing import Tuple, Dict, Any
from neo4j import Driver

logger = logging.getLogger(__name__)


def check_neo4j_health(driver: Driver) -> Tuple[bool, str]:
    """
    Check if Neo4j is healthy and responsive
    
    Args:
        driver: Neo4j driver instance
        
    Returns:
        Tuple[bool, str]: (is_healthy, status_message)
    """
    try:
        with driver.session() as session:
            # Simple health check query
            result = session.run("RETURN 'healthy' as status")
            record = result.single()
            
            if record and record["status"] == "healthy":
                return True, "✅ Neo4j is healthy and responsive"
            else:
                return False, "❌ Neo4j health check failed"
                
    except Exception as e:
        return False, f"❌ Neo4j health check error: {str(e)}"


def clear_database(driver: Driver, confirm: bool = False) -> Tuple[bool, str]:
    """
    Clear all nodes and relationships from the database
    WARNING: This will delete all data!
    
    Args:
        driver: Neo4j driver instance
        confirm: Must be True to actually perform the deletion
        
    Returns:
        Tuple[bool, str]: (success, message)
    """
    if not confirm:
        return False, "❌ Database clear not confirmed. Set confirm=True to proceed."
    
    try:
        with driver.session() as session:
            # Get counts before deletion
            node_result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = node_result.single()["count"]
            
            rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = rel_result.single()["count"]
            
            # Delete all relationships first
            session.run("MATCH ()-[r]->() DELETE r")
            
            # Delete all nodes
            session.run("MATCH (n) DELETE n")
            
            success_message = (
                f"✅ Database cleared successfully!\n"
                f"🗑️ Deleted {node_count} nodes and {rel_count} relationships"
            )
            
            logger.info(f"Database cleared: {node_count} nodes, {rel_count} relationships")
            return True, success_message
            
    except Exception as e:
        error_msg = f"❌ Error clearing database: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def get_database_statistics(driver: Driver) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Get comprehensive database statistics
    
    Args:
        driver: Neo4j driver instance
        
    Returns:
        Tuple[bool, str, Dict]: (success, message, stats_dict)
    """
    try:
        stats = {}
        
        with driver.session() as session:
            # Simple node count
            node_result = session.run("MATCH (n) RETURN count(n) as total_nodes")
            total_nodes = node_result.single()["total_nodes"]
            stats["total_nodes"] = total_nodes
            
            # Simple relationship count
            rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as total_relationships")
            total_relationships = rel_result.single()["total_relationships"]
            stats["total_relationships"] = total_relationships
            
            # Try to get labels (fallback if not available)
            try:
                label_result = session.run("CALL db.labels() YIELD label RETURN collect(label) as labels")
                labels = label_result.single()["labels"]
                stats["node_labels"] = {label: 0 for label in labels}  # Placeholder counts
                
                # Get actual counts for each label
                for label in labels:
                    count_result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                    count = count_result.single()["count"]
                    stats["node_labels"][label] = count
                    
            except Exception:
                stats["node_labels"] = {"Unknown": total_nodes}
            
            # Try to get relationship types (fallback if not available)
            try:
                rel_type_result = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) as types")
                rel_types = rel_type_result.single()["types"]
                stats["relationship_types"] = {rel_type: 0 for rel_type in rel_types}  # Placeholder counts
                
                # Get actual counts for each relationship type
                for rel_type in rel_types:
                    count_result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
                    count = count_result.single()["count"]
                    stats["relationship_types"][rel_type] = count
                    
            except Exception:
                stats["relationship_types"] = {"Unknown": total_relationships}
        
        success_message = (
            f"📊 Database Statistics:\n"
            f"🔵 Total Nodes: {stats['total_nodes']}\n"
            f"🔗 Total Relationships: {stats['total_relationships']}\n"
            f"🏷️ Node Labels: {len(stats['node_labels'])}\n"
            f"🔗 Relationship Types: {len(stats['relationship_types'])}"
        )
        
        return True, success_message, stats
        
    except Exception as e:
        error_msg = f"❌ Error getting database statistics: {str(e)}"
        logger.error(error_msg)
        return False, error_msg, {}


def create_constraints_and_indexes(driver: Driver) -> Tuple[bool, str]:
    """
    Create useful constraints and indexes for the knowledge graph
    
    Args:
        driver: Neo4j driver instance
        
    Returns:
        Tuple[bool, str]: (success, message)
    """
    try:
        constraints_created = []
        indexes_created = []
        
        with driver.session() as session:
            # Create constraints for unique identifiers
            constraints = [
                "CREATE CONSTRAINT file_path_unique IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE",
                "CREATE CONSTRAINT function_signature_unique IF NOT EXISTS FOR (fn:Function) REQUIRE (fn.name, fn.file_path) IS UNIQUE",
                "CREATE CONSTRAINT class_signature_unique IF NOT EXISTS FOR (c:Class) REQUIRE (c.name, c.file_path) IS UNIQUE"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                    constraint_name = constraint.split("FOR (")[1].split(")")[0]
                    constraints_created.append(constraint_name)
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        logger.warning(f"Could not create constraint: {e}")
            
            # Create indexes for better query performance
            indexes = [
                "CREATE INDEX file_name_index IF NOT EXISTS FOR (f:File) ON (f.name)",
                "CREATE INDEX function_name_index IF NOT EXISTS FOR (fn:Function) ON (fn.name)",
                "CREATE INDEX class_name_index IF NOT EXISTS FOR (c:Class) ON (c.name)",
                "CREATE INDEX chunk_id_index IF NOT EXISTS FOR (ch:Chunk) ON (ch.chunk_id)"
            ]
            
            for index in indexes:
                try:
                    session.run(index)
                    index_name = index.split("FOR (")[1].split(")")[0]
                    indexes_created.append(index_name)
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        logger.warning(f"Could not create index: {e}")
        
        success_message = (
            f"✅ Database schema setup completed!\n"
            f"🔒 Constraints created: {len(constraints_created)}\n"
            f"📇 Indexes created: {len(indexes_created)}"
        )
        
        return True, success_message
        
    except Exception as e:
        error_msg = f"❌ Error creating constraints and indexes: {str(e)}"
        logger.error(error_msg)
        return False, error_msg 