# Unified GraphRAG Architecture Guide

## Overview

The Code Graph project implements a **Unified GraphRAG Architecture** that combines the power of knowledge graphs with vector search to provide comprehensive code understanding and querying capabilities. This architecture enables both structural and semantic analysis of codebases.

## Architecture Components

### 1. Structural Layer (Knowledge Graph)
- **Purpose**: Captures explicit relationships between code entities
- **Node Types**: `Class`, `Function`, `Interface`, `Package`
- **Relationships**: `INHERITS`, `IMPLEMENTS`, `CALLS`, `IMPORTS`
- **Use Cases**: Dependency analysis, architecture understanding, structural queries

### 2. Semantic Layer (Vector Search)
- **Purpose**: Captures semantic meaning through embeddings
- **Node Types**: `CodeChunk` (with 3072-dimensional embeddings)
- **Relationships**: `CONTAINS_CHUNK`, `REPRESENTS`
- **Use Cases**: Similarity search, natural language queries, content discovery

### 3. Bridge Layer (Integration)
- **Purpose**: Links structural and semantic layers
- **Key Relationships**: 
  - `REPRESENTS`: Links `CodeChunk` nodes to `Class`/`Function` nodes
  - `PART_OF_FILE`: Links chunks to file-level entities
- **Benefits**: Enables hybrid queries combining both approaches

### 4. Unified File Layer
- **Purpose**: Single source of truth for file metadata
- **Node Type**: `File` (used by both systems)
- **Properties**: `path`, `name`, `language`, `total_chunks`, `total_lines`

## Database Schema

```cypher
// Structural Layer
(Class)-[:INHERITS]->(Class)
(Class)-[:IMPLEMENTS]->(Interface)
(Function)-[:CALLS]->(Function)
(File)-[:CONTAINS]->(Class|Function|Interface)

// Semantic Layer
(CodeChunk {embedding: [3072 dimensions]})
(File)-[:CONTAINS_CHUNK]->(CodeChunk)

// Bridge Layer
(CodeChunk)-[:REPRESENTS]->(Class|Function)
(CodeChunk)-[:PART_OF_FILE]->(Class|Function)

// Vector Index
CREATE VECTOR INDEX code_chunks_vector_index
FOR (c:CodeChunk) ON (c.embedding)
OPTIONS {indexConfig: {
    `vector.dimensions`: 3072,
    `vector.similarity_function`: 'cosine'
}}
```

## Key Benefits

### 1. Hybrid Query Capabilities
- **Semantic Search**: "Find authentication code" → Vector similarity
- **Structural Analysis**: "What depends on this class?" → Graph traversal
- **Combined Queries**: "Find auth code AND its dependencies" → Both approaches

### 2. Rich Context Understanding
- Vector search finds semantically similar code
- Graph traversal provides structural context
- Bridge relationships connect semantic findings to architectural elements

### 3. Scalable Architecture
- Each layer can be optimized independently
- Vector search scales with content similarity
- Graph traversal scales with relationship complexity

## Implementation Details

### GraphBuilder Class Methods

#### `create_unified_graphrag_system(documents)`
Creates the complete unified system:
1. Generates structural knowledge graph
2. Creates semantic vector index (coexistent)
3. Builds bridge relationships
4. Maintains unified file metadata

#### `_create_vector_index_coexistent(documents)`
Creates vector index without clearing existing knowledge graph:
- Manually stores embeddings in Neo4j
- Preserves existing structural data
- Creates vector index if not exists

#### `_create_bridge_relationships(documents)`
Links semantic and structural layers:
- Maps chunks to classes based on content analysis
- Creates `REPRESENTS` relationships
- Enables hybrid query processing

### QueryProcessor Class

#### Hybrid Query Flow
1. **Vector Search**: Find semantically relevant chunks
2. **Entity Mapping**: Map chunks to structural entities via `REPRESENTS`
3. **Graph Traversal**: Explore relationships for context
4. **Response Generation**: Combine semantic and structural insights

#### Key Methods
- `vector_search()`: Pure vector similarity search
- `get_graph_context_for_chunks()`: Extract structural context
- `process_query()`: Full hybrid processing

## Usage Examples

### Creating Unified System
```python
from app.graph_builder import GraphBuilder
from app.ingestion import parse_code_chunks

# Parse codebase
success, message, chunks = parse_code_chunks("path/to/repo")

# Create unified system
with GraphBuilder() as gb:
    gb.connect_to_neo4j()
    success, message = gb.create_unified_graphrag_system(chunks)
```

### Querying the System
```python
from app.query_processor import QueryProcessor

with QueryProcessor() as qp:
    qp.connect_to_neo4j()
    qp.setup_retrievers()
    
    # Hybrid query
    success, response, context = qp.process_query(
        "How is the adapter pattern implemented?",
        k=5,
        include_graph_context=True
    )
```

### Manual Cypher Queries

#### Find Code Chunks with Structural Context
```cypher
MATCH (c:CodeChunk)-[:REPRESENTS]->(entity)
WHERE c.text CONTAINS "adapter"
RETURN c.text, entity.id, labels(entity)
```

#### Explore Relationships from Vector Results
```cypher
MATCH (c:CodeChunk)-[:REPRESENTS]->(e1)-[r]->(e2)
WHERE c.chunk_id IN [0, 1, 2]  // From vector search
RETURN e1.id, type(r), e2.id
```

#### Find Files with Both Chunks and Entities
```cypher
MATCH (f:File)-[:CONTAINS_CHUNK]->(c:CodeChunk)
MATCH (f)-[:CONTAINS]->(entity)
RETURN f.name, count(c) as chunks, count(entity) as entities
```

## Testing

### Unified System Test
```bash
# Test unified GraphRAG system
python tests/test_vector_index.py

# Test with full cost mode
python tests/test_vector_index.py --full

# Test separate systems (legacy)
python tests/test_vector_index.py --separate
```

### Query Processor Test
```bash
# Test hybrid query processing
python tests/test_query_processor.py

# Test with full cost mode
python tests/test_query_processor.py --full
```

### Comprehensive Test Suite
```bash
# Run all tests
python tests/run_tests.py

# Quick test subset
python tests/run_tests.py --quick

# Specific category
python tests/run_tests.py --category unified
```

## Performance Considerations

### Vector Search Performance
- **Index Type**: Cosine similarity with 3072 dimensions
- **Optimal k**: 3-10 results for most queries
- **Memory Usage**: ~12KB per embedding

### Graph Traversal Performance
- **Relationship Indexing**: Automatic Neo4j indexing
- **Query Optimization**: Use `LIMIT` for large result sets
- **Memory Usage**: Depends on graph complexity

### Hybrid Query Performance
- **Sequential Processing**: Vector search → Graph context → Response
- **Optimization**: Cache frequent entity mappings
- **Scalability**: Both layers scale independently

## Troubleshooting

### Common Issues

#### "Vector index not found"
```bash
# Verify index exists
SHOW INDEXES YIELD name WHERE name = 'code_chunks_vector_index'

# Recreate if missing
python tests/test_vector_index.py
```

#### "No bridge relationships"
- Check if both knowledge graph and vector index exist
- Verify `REPRESENTS` relationships were created
- Run unified system creation again

#### "Metadata shows 'unknown'"
- Fixed in current implementation
- Metadata keys now properly mapped
- Language detection from file extensions

### Debugging Queries

#### Check System Status
```cypher
MATCH (n) 
RETURN labels(n)[0] as NodeType, count(n) as Count 
ORDER BY Count DESC
```

#### Verify Coexistence
```cypher
MATCH (kg) WHERE kg:Class OR kg:Function OR kg:Interface
WITH count(kg) as kg_count
MATCH (c:CodeChunk)
WITH kg_count, count(c) as vector_count
MATCH ()-[r:REPRESENTS]->()
RETURN kg_count, vector_count, count(r) as bridge_count
```

## Future Enhancements

### Planned Improvements
1. **Advanced Entity Mapping**: Use NLP for better chunk-to-entity mapping
2. **Relationship Inference**: Infer additional relationships from code analysis
3. **Query Optimization**: Cache and optimize frequent query patterns
4. **Visualization**: Interactive graph visualization of hybrid results

### Integration Opportunities
1. **IDE Integration**: Real-time code understanding
2. **CI/CD Integration**: Architecture analysis in pipelines
3. **Documentation Generation**: Auto-generate docs from graph structure
4. **Code Review**: Semantic similarity for review suggestions

## Conclusion

The Unified GraphRAG Architecture provides a powerful foundation for code understanding that combines the best of both structural and semantic analysis. By maintaining coexistence between knowledge graphs and vector search, the system enables sophisticated queries that would be impossible with either approach alone.

The architecture is designed for scalability, maintainability, and extensibility, making it suitable for both research and production use cases in software engineering and code analysis domains. 