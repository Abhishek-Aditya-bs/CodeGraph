# CodeGraph Integration Tests

This directory contains comprehensive integration tests for the complete CodeGraph system, validating end-to-end functionality of the GraphRAG (Graph Retrieval-Augmented Generation) system.

## Test Structure

### 🔄 TestFullSystemWorkflow
**Complete end-to-end system workflow testing**

- **`test_complete_workflow_basic`** - Core integration test validating the complete pipeline:
  1. Code ingestion and chunking
  2. Knowledge graph generation with LLM
  3. Vector index creation with embeddings
  4. Query processing and response generation
  5. System statistics and validation

- **`test_complete_workflow_multiple_patterns`** - Multi-pattern workflow testing:
  - Multi-pattern code ingestion
  - Complex knowledge graph creation
  - Cross-pattern query processing
  - Pattern-specific and general queries

- **`test_incremental_system_building`** - Incremental system updates:
  - Building system with small dataset
  - Adding more data incrementally
  - System consistency after updates
  - Query performance with growing dataset

### ⚡ TestSystemPerformance
**System performance and scalability validation**

- **`test_system_performance_metrics`** - Performance measurement:
  - Ingestion performance timing
  - Graph building performance
  - Query processing performance
  - Memory and time efficiency metrics

- **`test_system_scalability`** - Scalability testing:
  - Performance with different document counts
  - Query response time consistency
  - System stability under load

### 🛡️ TestSystemRobustness
**System robustness and error recovery**

- **`test_system_error_recovery`** - Error recovery and resilience:
  - Recovery from partial failures
  - Graceful degradation
  - Error handling across components
  - Vector-only system operation

- **`test_system_data_consistency`** - Data consistency and integrity:
  - Data consistency across components
  - Referential integrity validation
  - No data corruption checks
  - Metadata consistency validation

### 👨‍💻 TestSystemUseCases
**Real-world use cases and scenarios**

- **`test_developer_workflow_simulation`** - Realistic developer workflow:
  - Initial codebase exploration
  - Pattern-specific investigation
  - Implementation guidance queries
  - Multi-scenario validation

- **`test_code_search_and_discovery`** - Code search capabilities:
  - Semantic code search
  - Pattern discovery
  - Method and class finding
  - Cross-reference capabilities

## Test Results Summary

### ✅ All Tests Passing (9/9)
- **Total Execution Time**: ~12 minutes (includes API calls)
- **Test Coverage**: Complete end-to-end system validation
- **API Integration**: Real OpenAI API calls with cost management
- **Database Integration**: Real Neo4j operations with proper cleanup

### 🔧 Technical Validation

**Database Layer**:
- ✅ Singleton Neo4j connection management
- ✅ Proper cleanup and transaction handling
- ✅ Index creation and management

**Graph Builder**:
- ✅ LLM-based entity extraction (GPT-4o)
- ✅ Vector embeddings (text-embedding-3-large)
- ✅ Hybrid GraphRAG system creation
- ✅ Bridge relationships between layers

**Query Processor**:
- ✅ Vector similarity search
- ✅ Graph context retrieval
- ✅ Response generation with LLM
- ✅ Fallback mechanisms

**Integration**:
- ✅ Real Java Design Patterns data processing
- ✅ Multi-pattern system creation
- ✅ Cross-component data consistency
- ✅ Error handling and recovery

### 📊 Performance Metrics

**System Creation**:
- Graph building: < 5 minutes for typical datasets
- Query setup: < 30 seconds
- Vector index creation: Efficient with batching

**Query Performance**:
- Average query time: < 60 seconds
- Scalable with document count
- Consistent response quality

**Data Integrity**:
- 100% CodeChunk-Document consistency
- Complete embedding coverage
- Proper file-chunk relationships
- Metadata preservation

## Test Infrastructure

### 🏗️ Fixtures and Configuration
- **`clean_database`**: Ensures clean test environment
- **`test_config`**: Standardized test parameters
- **`java_patterns_path`**: Real codebase for testing
- **`selected_patterns`**: Curated design patterns

### 🏷️ Test Markers
- **`@pytest.mark.api_cost`**: Tests that make expensive API calls
- **`@pytest.mark.slow`**: Long-running integration tests
- Proper cost management and execution control

### 📈 Helper Functions
- **`validate_system_state()`**: Comprehensive system validation
- **`measure_query_performance()`**: Performance metrics collection
- **`_get_test_documents()`**: Standardized test data preparation

## Usage

### Run All Integration Tests
```bash
python -m pytest tests/integration/test_full_system.py -v
```

### Run Specific Test Categories
```bash
# Workflow tests only
python -m pytest tests/integration/test_full_system.py::TestFullSystemWorkflow -v

# Performance tests only
python -m pytest tests/integration/test_full_system.py::TestSystemPerformance -v

# Robustness tests only
python -m pytest tests/integration/test_full_system.py::TestSystemRobustness -v

# Use case tests only
python -m pytest tests/integration/test_full_system.py::TestSystemUseCases -v
```

### Run Without API Costs
```bash
# Skip expensive API tests
python -m pytest tests/integration/test_full_system.py -v -m "not api_cost"
```

## Key Features Validated

### 🧠 AI Integration
- **LLM Knowledge Graph Generation**: GPT-4o for entity extraction
- **Vector Embeddings**: OpenAI text-embedding-3-large
- **Conversational Responses**: Natural language query responses
- **Error Handling**: Graceful API failure recovery

### 🗄️ Database Operations
- **Neo4j Graph Storage**: Complex graph relationships
- **Vector Index**: Efficient similarity search
- **Transaction Management**: ACID compliance
- **Data Consistency**: Referential integrity

### 🔍 Query Processing
- **Hybrid Search**: Vector + graph traversal
- **Context Enrichment**: Multi-source information
- **Response Generation**: LLM-powered explanations
- **Performance Optimization**: Efficient retrieval

### 🏗️ System Architecture
- **Modular Design**: Independent component testing
- **Scalability**: Growing dataset handling
- **Robustness**: Error recovery and graceful degradation
- **Extensibility**: Easy addition of new patterns

## Implementation Quality

### ✅ Comprehensive Coverage
- **9 integration tests** covering all major workflows
- **4 test classes** organized by functionality
- **Real data integration** with Java Design Patterns
- **Performance validation** with timing metrics

### ✅ Production Readiness
- **Error handling** for all failure modes
- **Resource management** with proper cleanup
- **API cost control** with test markers
- **Scalability validation** with growing datasets

### ✅ Developer Experience
- **Clear test organization** with descriptive names
- **Comprehensive logging** for debugging
- **Flexible configuration** for different environments
- **Helper functions** for common operations

This integration test suite provides confidence that the CodeGraph system works correctly as a complete GraphRAG solution, handling real-world codebases with proper AI integration, database management, and query processing capabilities. 