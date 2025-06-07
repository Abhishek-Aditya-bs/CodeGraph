# Code Graph - Complete Execution Guide

## 🎯 **Reorganized Test Structure**

All test scripts have been properly organized under the `tests/` directory with a clean execution flow:

### **Test Files Structure:**
```
tests/
├── test_ingestion.py              # Codebase ingestion tests
├── test_neo4j.py                  # Neo4j connection tests
├── test_knowledge_graph_mock.py   # Mock knowledge graph tests (no API)
├── test_openai_config.py          # OpenAI API configuration tests
├── test_knowledge_graph_generation.py # Knowledge graph generation tests (Java codebases)
├── test_cleanup.py                # Database cleanup (runs LAST)
└── run_tests.py                   # Main test runner
```

## 🚀 **How to Execute Everything**

### **Option 1: Run All Tests (Recommended)**
```bash
# Run the complete test suite with cleanup at the end
python tests/run_tests.py
```

This will:
1. ✅ Run ingestion tests
2. ✅ Run Neo4j connection tests  
3. ✅ Run knowledge graph mock tests
4. ✅ Run OpenAI configuration tests
5. ✅ Run comprehensive knowledge graph generation tests
6. 🧹 **Clean the database at the end**

### **Option 2: Run Individual Test Suites**

#### Knowledge Graph Generation Tests (Main Feature)
```bash
# Run comprehensive knowledge graph generation tests with Java codebases
python tests/test_knowledge_graph_generation.py
```

#### Database Cleanup Only
```bash
# Clean the database (run this LAST)
python tests/test_cleanup.py
```

#### Other Individual Tests
```bash
# Basic functionality tests
python tests/test_ingestion.py
python tests/test_neo4j.py
python tests/test_knowledge_graph_mock.py
python tests/test_openai_config.py
```

## 📊 **What Each Test Does**

### **1. Knowledge Graph Generation Tests** (`test_knowledge_graph_generation.py`)
- **Test 1**: Generate knowledge graph from Java design patterns repository
- **Test 2**: Explore the generated knowledge graph with comprehensive queries  
- **Test 3**: Generate knowledge graph from Spring Pet Clinic repository (if available)

**Output**: Rich knowledge graph with 30+ nodes and relationships

### **2. Database Cleanup Test** (`test_cleanup.py`)
- Shows current database statistics
- Clears ALL data from Neo4j database
- Verifies cleanup was successful
- **⚠️ WARNING**: This deletes everything!

### **3. Other Tests**
- **Ingestion**: Tests code parsing and chunking
- **Neo4j**: Tests database connection
- **Mock**: Tests knowledge graph structure without API calls
- **OpenAI**: Tests API configuration and connectivity

## 🌐 **Neo4j Browser Access**

After running the knowledge graph generation tests:
- **URL**: http://localhost:7474
- **Login**: neo4j / password

### **Essential Queries to Try:**
```cypher
-- View all nodes
MATCH (n) RETURN n LIMIT 30

-- View inheritance relationships
MATCH (child:Class)-[:INHERITS]->(parent:Class) 
RETURN child.id as ChildClass, parent.id as ParentClass

-- View interface implementations
MATCH (impl:Class)-[:IMPLEMENTS]->(interface) 
RETURN impl.id as ImplementingClass, interface.id as Interface

-- Adapter pattern analysis
MATCH (adapter:Class)-[r]->(target:Class)
WHERE adapter.id CONTAINS 'Adapter'
RETURN adapter.id, type(r), target.id

-- Factory pattern analysis
MATCH (n:Class) 
WHERE n.id CONTAINS 'Blacksmith'
RETURN n.id as ClassName
```

## 🎯 **Expected Results**

### **Successful Run Output:**
```
🚀 CODE GRAPH COMPREHENSIVE TEST SUITE
======================================================================

🚀 RUNNING INGESTION TESTS
✅ Ingestion Tests completed successfully

🚀 RUNNING NEO4J TESTS  
✅ Neo4j Tests completed successfully

🚀 RUNNING KNOWLEDGE GRAPH MOCK TESTS
✅ Knowledge Graph Mock Tests completed successfully

🚀 RUNNING OPENAI CONFIGURATION TESTS
✅ OpenAI Configuration Tests completed successfully

🚀 RUNNING KNOWLEDGE GRAPH GENERATION TESTS
✅ Knowledge Graph Generation Tests completed successfully

🧹 RUNNING FINAL DATABASE CLEANUP
✅ Database cleanup completed successfully

🎯 FINAL TEST SUMMARY
   Ingestion Tests: ✅ PASSED
   Neo4j Tests: ✅ PASSED
   Knowledge Graph Mock Tests: ✅ PASSED
   OpenAI Configuration Tests: ✅ PASSED
   Knowledge Graph Generation Tests: ✅ PASSED
   Database Cleanup: ✅ PASSED

📈 Overall: 6/6 test suites passed

🎉 ALL TESTS PASSED! Database is clean and ready.
```

## 🔧 **Troubleshooting**

### **If Tests Fail:**
1. **Neo4j not running**: Start with `docker start code-graph-neo4j`
2. **OpenAI API issues**: Check your `.env` file has correct `OPENAI_API_KEY`
3. **Repository missing**: Tests will skip gracefully if repositories aren't cloned

### **Manual Cleanup:**
If you need to clean the database manually:
```bash
python tests/test_cleanup.py
```

### **Check What's in Database:**
```bash
# Quick check of database contents
python -c "
from app.graph_builder import GraphBuilder
from app.utilities.neo4j_utils import get_database_statistics
with GraphBuilder() as gb:
    gb.connect_to_neo4j()
    success, msg, stats = get_database_statistics(gb.driver)
    if success:
        print(f'Nodes: {sum(stats[\"node_labels\"].values())}')
        print(f'Relationships: {sum(stats[\"relationship_types\"].values())}')
"
```

## 🎉 **What You Get**

After running the tests, you'll have:
- ✅ **Verified system functionality** across all components
- 📊 **Rich knowledge graph** from Java codebases (design patterns, Spring Pet Clinic)
- 🔍 **Comprehensive exploration queries** 
- 🧹 **Clean database** ready for new experiments
- 📋 **Complete documentation** of all relationships and nodes

The system is now properly organized, tested, and ready for production use! 