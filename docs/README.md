# Code Graph Documentation

## 📚 **Documentation Overview**

This directory contains comprehensive documentation for the Code Graph project - a **Unified GraphRAG System** that combines knowledge graphs with vector search for advanced codebase analysis using Neo4j, OpenAI, and Streamlit.

## 🏗️ **Architecture Documentation**

### **[Unified GraphRAG Architecture Guide](UNIFIED_GRAPHRAG_ARCHITECTURE.md)** ⭐ **NEW**
**Complete architectural overview of the unified GraphRAG system:**
- **Coexistence architecture** - How knowledge graphs and vector search work together
- **Database schema** and relationship design
- **Hybrid query processing** flow and implementation
- **Performance considerations** and optimization strategies
- **Usage examples** and code samples
- **Troubleshooting guide** and debugging queries

**Use this when**: You want to understand the system architecture, implement custom queries, or extend the functionality.

## 📋 **Testing Documentation**

### **[Tests Guide](TESTS_GUIDE.md)**
Complete guide for running all tests in the Code Graph system:
- **Test structure** and organization
- **Execution commands** for all test suites
- **Individual test descriptions** and what they do
- **Troubleshooting** common issues
- **Expected results** and output examples

**Use this when**: You want to run tests, understand the test structure, or troubleshoot test issues.

### **[Vector Index Usage Guide](VECTOR_INDEX_USAGE.md)**
Professional usage guide for the unified GraphRAG tests with cost control:
- **Command-line options** and flags
- **Cost control modes** (limited vs full)
- **Unified vs separate system testing**
- **Repository cloning** and custom repositories
- **Professional implementation** features

**Use this when**: You want to run unified GraphRAG tests with proper cost control and understand all available options.

## 🔍 **Exploration Documentation**

### **[Neo4j Browser Guide](NEO4J_BROWSER_GUIDE.md)**
Comprehensive guide for exploring knowledge graphs in Neo4j Browser:
- **20+ Cypher queries** for exploring code relationships
- **Design pattern analysis** queries
- **Object-oriented relationship** exploration
- **Neo4j Browser tips** and navigation
- **Visualization techniques** and export options

**Use this when**: You want to explore the generated knowledge graphs visually and understand code relationships.

### **[Vector Index Visualization Guide](VECTOR_INDEX_VISUALIZATION_GUIDE.md)**
Complete guide for understanding and visualizing vector embeddings in Neo4j:
- **Vector index structure** and what gets stored
- **Embedding visualization** queries (3072-dimensional vectors)
- **CodeChunk and File metadata** exploration
- **Vector search testing** and similarity scores
- **Understanding semantic search** vs keyword search

**Use this when**: You want to understand how vector embeddings work and explore the semantic search capabilities.

## 🚀 **Quick Start**

### For New Users
1. **Understand Architecture**: Read the [Unified GraphRAG Architecture Guide](UNIFIED_GRAPHRAG_ARCHITECTURE.md)
2. **Run Tests**: Follow the [Tests Guide](TESTS_GUIDE.md) to execute the test suite
3. **Explore Results**: Use the [Neo4j Browser Guide](NEO4J_BROWSER_GUIDE.md) to explore generated knowledge graphs

### For Developers
1. **Architecture Deep Dive**: Study the [Unified GraphRAG Architecture Guide](UNIFIED_GRAPHRAG_ARCHITECTURE.md)
2. **Test Unified System**: Use the [Vector Index Usage Guide](VECTOR_INDEX_USAGE.md) for comprehensive testing
3. **Custom Queries**: Implement hybrid queries using the architecture documentation

### Quick Commands
```bash
# Test unified GraphRAG system
python tests/test_vector_index.py

# Test query processor
python tests/test_query_processor.py

# Run comprehensive test suite
python tests/run_tests.py

# Access Neo4j Browser
open http://localhost:7474  # (login: neo4j/password)
```

## 🎯 **Project Structure**

```
CodeGraph/
├── docs/                                    # 📚 Documentation (you are here)
│   ├── README.md                           # This file - Documentation index
│   ├── UNIFIED_GRAPHRAG_ARCHITECTURE.md   # 🏗️ System architecture guide
│   ├── TESTS_GUIDE.md                     # 🧪 Complete testing guide
│   ├── VECTOR_INDEX_USAGE.md              # 🔧 Test usage and cost control
│   ├── NEO4J_BROWSER_GUIDE.md             # 🔍 Neo4j exploration guide
│   └── VECTOR_INDEX_VISUALIZATION_GUIDE.md # 📊 Vector embeddings guide
├── tests/                                   # 🧪 Test files
│   ├── test_vector_index.py               # Unified GraphRAG tests
│   ├── test_query_processor.py            # Query processor tests
│   └── run_tests.py                       # Comprehensive test runner
├── app/                                     # 🔧 Application code
│   ├── graph_builder.py                   # Unified GraphRAG implementation
│   ├── query_processor.py                 # Hybrid query processing
│   └── ingestion.py                       # Code parsing and chunking
└── README.md                               # 📖 Main project README
```

## 🔄 **System Capabilities**

### Unified GraphRAG Features
- **🧠 Knowledge Graph**: Structural relationships (Class, Function, Interface)
- **🔍 Vector Search**: Semantic similarity with 3072-dimensional embeddings
- **🌉 Bridge Layer**: Links semantic chunks to structural entities
- **📁 Unified Files**: Single source of truth for file metadata
- **🔄 Coexistence**: Both systems work together without interference

### Query Types Supported
- **Semantic Queries**: "Find authentication code"
- **Structural Queries**: "What classes inherit from this?"
- **Hybrid Queries**: "Find auth code AND show its dependencies"
- **Natural Language**: "How is the adapter pattern implemented?"

## 💡 **Documentation Tips**

- **Start with Architecture Guide** if you're new to GraphRAG concepts
- **Use Tests Guide** for hands-on experience with the system
- **Neo4j Browser Guide** is essential for visual exploration
- **All guides are self-contained** and can be used independently
- **Examples and commands** are provided throughout

## 🔗 **Related Files**

- **Main README**: `../README.md` - Project overview and setup
- **Test Files**: `../tests/` - Actual test implementations
- **Application Code**: `../app/` - Core GraphRAG implementation
- **Configuration**: `../app/config.py` - Environment setup 