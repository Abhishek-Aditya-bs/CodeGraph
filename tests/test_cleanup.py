#!/usr/bin/env python3
"""
Database Cleanup Test
This test should run LAST to clean up the Neo4j database after all other tests
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.graph_builder import GraphBuilder
from app.utilities.neo4j_utils import get_database_statistics


def test_database_cleanup():
    """
    Final cleanup test - clears the Neo4j database completely
    This should be run LAST after all other tests are complete
    """
    print("🧹 FINAL DATABASE CLEANUP TEST")
    print("=" * 50)
    
    with GraphBuilder() as gb:
        # Connect to Neo4j
        connect_success, connect_message = gb.connect_to_neo4j()
        if not connect_success:
            print(f"❌ Failed to connect to Neo4j: {connect_message}")
            return False
        
        print("✅ Connected to Neo4j")
        
        # Get current database statistics before cleanup
        print("\n📊 DATABASE STATUS BEFORE CLEANUP:")
        stats_success, stats_message, stats_dict = get_database_statistics(gb.driver)
        
        if stats_success:
            total_nodes = sum(stats_dict.get('node_labels', {}).values())
            total_rels = sum(stats_dict.get('relationship_types', {}).values())
            
            print(f"   🔵 Total Nodes: {total_nodes}")
            print(f"   🔗 Total Relationships: {total_rels}")
            
            if total_nodes > 0 or total_rels > 0:
                print(f"\n🏷️ Node Types:")
                for label, count in stats_dict.get('node_labels', {}).items():
                    print(f"   {label}: {count}")
                
                print(f"\n🔗 Relationship Types:")
                for rel_type, count in stats_dict.get('relationship_types', {}).items():
                    print(f"   {rel_type}: {count}")
            else:
                print("   Database is already empty")
        else:
            print(f"   ⚠️ Could not get database statistics: {stats_message}")
        
        # Perform cleanup
        print(f"\n🧹 PERFORMING FINAL CLEANUP...")
        clear_success, clear_message = gb.clear_knowledge_graph(confirm=True)
        
        if clear_success:
            print("✅ Database cleared successfully!")
            print(clear_message)
        else:
            print(f"❌ Failed to clear database: {clear_message}")
            return False
        
        # Verify cleanup
        print(f"\n🔍 VERIFYING CLEANUP...")
        final_stats_success, final_stats_message, final_stats_dict = get_database_statistics(gb.driver)
        
        if final_stats_success:
            final_nodes = sum(final_stats_dict.get('node_labels', {}).values())
            final_rels = sum(final_stats_dict.get('relationship_types', {}).values())
            
            print(f"   🔵 Final Nodes: {final_nodes}")
            print(f"   🔗 Final Relationships: {final_rels}")
            
            if final_nodes == 0 and final_rels == 0:
                print("✅ Database is completely clean!")
            else:
                print("⚠️ Some data may still remain in the database")
                return False
        else:
            print(f"   ⚠️ Could not verify cleanup: {final_stats_message}")
            return False
    
    print("\n🎉 CLEANUP TEST COMPLETED SUCCESSFULLY!")
    print("💡 Database is now ready for fresh tests")
    return True


def main():
    """
    Main function to run the cleanup test
    """
    print("🧹 DATABASE CLEANUP TEST")
    print("=" * 40)
    print("⚠️  WARNING: This will delete ALL data in the Neo4j database!")
    print("📝 This test should be run LAST after all other tests")
    print("=" * 40)
    
    success = test_database_cleanup()
    
    if success:
        print("\n✅ CLEANUP COMPLETED SUCCESSFULLY!")
    else:
        print("\n❌ CLEANUP FAILED!")
    
    return success


if __name__ == "__main__":
    main() 