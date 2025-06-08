# CodeGraph Architecture

A comprehensive guide to the GraphRAG (Graph-based Retrieval-Augmented Generation) architecture that powers CodeGraph - a hybrid system combining knowledge graphs with vector search for intelligent codebase analysis.

## System Overview

CodeGraph implements a sophisticated multi-layered architecture that processes codebases through structural and semantic analysis, storing both in Neo4j for hybrid querying capabilities.

### Core Philosophy
- **Hybrid Intelligence**: Combines explicit relationships (graph) with semantic understanding (vectors)
- **Unified Storage**: Single Neo4j database houses both graph and vector data
- **Bridge Connections**: Smart links between structural and semantic layers
- **Scalable Design**: Each layer optimized independently for performance

## Architecture Layers

### 1. 📥 Ingestion Layer
**Purpose**: Converts raw codebases into processable documents

**Components**:
- **Repository Cloner**: Handles GitHub/local folder input
- **Code Parser**: Splits code into manageable chunks
- **Metadata Extractor**: Captures file information and language detection

**Flow**:
```
Codebase Input → Validation → Chunking → Document Objects
```

**Key Classes**:
- `parse_code_chunks()` - Main ingestion function
- `clone_repository()` - Git repository handling
- `read_local_folder()` - Local file processing

### 2. 🧠 Structural Layer (Knowledge Graph)
**Purpose**: Captures explicit relationships between code entities

**Node Types**:
- `Class` - Java/Python classes with methods and properties
- `Function` - Standalone functions and class methods  
- `Interface` - Java interfaces and abstract classes
- `File` - Source files with metadata
- `Package` - Code organization units

**Relationship Types**:
- `INHERITS` - Class inheritance (extends)
- `IMPLEMENTS` - Interface implementation
- `CALLS` - Function/method calls
- `CONTAINS` - File/package containment
- `DEPENDS_ON` - Module dependencies

**Implementation**:
- Uses GPT-4o for entity extraction
- LangChain's `LLMGraphTransformer` for relationship mapping
- Cypher queries for graph storage

### 3. 🔍 Semantic Layer (Vector Search)
**Purpose**: Captures semantic meaning through embeddings

**Components**:
- **CodeChunk Nodes**: 3072-dimensional vector embeddings
- **Vector Index**: Cosine similarity search index
- **Embedding Generator**: OpenAI text-embedding-3-large

**Storage Schema**:
```cypher
(CodeChunk {
  text: "actual code content",
  embedding: [3072 dimensions],
  file_path: "src/main/java/...",
  chunk_id: unique_identifier,
  language: "java",
  start_line: 45,
  end_line: 78
})
```

**Vector Index**:
```cypher
CREATE VECTOR INDEX code_chunks_vector_index
FOR (c:CodeChunk) ON (c.embedding)
OPTIONS {indexConfig: {
    `vector.dimensions`: 3072,
    `vector.similarity_function`: 'cosine'
}}
```

### 4. 🌉 Bridge Layer (Integration)
**Purpose**: Links structural and semantic layers for hybrid queries

**Key Relationships**:
- `REPRESENTS`: Links CodeChunk → Class/Function entities
- `CONTAINS_CHUNK`: Links File → CodeChunk
- `PART_OF_FILE`: Links chunks to their source files

**Benefits**:
- Enables queries like "Find auth code AND show its dependencies"
- Provides context for vector search results
- Allows semantic search with structural follow-up

### 5. 🔗 Unified File Layer
**Purpose**: Single source of truth for file metadata

**File Node Properties**:
```cypher
(File {
  path: "/full/path/to/file.java",
  name: "file.java",
  language: "java",
  total_chunks: 5,
  total_lines: 150,
  extension: ".java",
  created_at: timestamp
})
```

## System Flow

### Complete Workflow
```
1. Input Processing
   Codebase → Validation → Chunking → Documents

2. Knowledge Graph Creation  
   Documents → Entity Extraction → Relationship Mapping → Neo4j Storage

3. Vector Index Creation
   Documents → Embedding Generation → Vector Storage → Index Creation

4. Bridge Building
   Code Analysis → Chunk-to-Entity Mapping → Bridge Relationships

5. Query Processing
   Natural Language → Vector Search → Entity Mapping → Graph Context → Response
```

### Data Flow Diagram

The following diagram illustrates the complete data flow from codebase input to query results:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CodeGraph Data Flow                                 │
└─────────────────────────────────────────────────────────────────────────────┘

🌐 Codebase Input                    📥 Ingestion Layer                📄 Document Objects
(GitHub/Local)           ──────▶      (Validation &         ──────▶      (Code Chunks)
                                       Chunking)                           
┌─────────────────┐                 ┌─────────────────┐                ┌─────────────────┐
│ • GitHub Repos  │                 │ • Repository    │                │ • Chunked Code  │
│ • Local Folders │                 │   Cloning       │                │ • File Metadata │
│ • Validation    │                 │ • Code Parsing  │                │ • Language Info │
└─────────────────┘                 │ • Language Det. │                └─────────────────┘
                                    └─────────────────┘                          │
                                                                                 │
                                                                                 ▼
           ┌─────────────────────────────────────────────────────────────────────────────┐
           │                           Processing Layers                                  │
           └─────────────────────────────────────────────────────────────────────────────┘
                                                    │
                    ┌───────────────────────────────┼───────────────────────────────┐
                    ▼                               ▼                               ▼

🧠 Structural Layer              🔍 Semantic Layer               🌉 Bridge Layer
(Knowledge Graph)               (Vector Search)                 (Integration)

┌─────────────────┐              ┌─────────────────┐              ┌─────────────────┐
│ • Classes       │              │ • CodeChunks    │              │ • REPRESENTS    │
│ • Functions     │              │ • 3072-dim      │              │ • CONTAINS_CHUNK│
│ • Interfaces    │              │   Embeddings    │              │ • PART_OF_FILE  │
│ • INHERITS      │              │ • Vector Index  │              │ • Entity Links  │
│ • IMPLEMENTS    │              │ • Similarity    │              │ • Context Maps  │
│ • CALLS         │              │   Search        │              │                 │
└─────────────────┘              └─────────────────┘              └─────────────────┘
         │                                │                                │
         └────────────────────────────────┼────────────────────────────────┘
                                          ▼

                              📊 Neo4j Database
                              (Unified Storage)
                              ┌─────────────────┐
                              │ • Graph Data    │
                              │ • Vector Index  │
                              │ • File Metadata │
                              │ • Relationships │
                              │ • Unified Schema│
                              └─────────────────┘
                                          │
                                          ▼

💬 Natural Language Query  ──────▶  🔎 Query Processor  ──────▶  📋 Hybrid Results
                                   (Hybrid Processing)          (Semantic + Structural)

┌─────────────────┐                ┌─────────────────┐          ┌─────────────────┐
│ • "Find auth    │                │ 1. Vector Search│          │ • Relevant Code │
│   code patterns"│                │ 2. Entity Map   │          │ • Context Info  │
│ • "Show class   │                │ 3. Graph Context│          │ • Relationships │
│   dependencies" │                │ 4. LLM Response │          │ • Explanations  │
│ • "How is X     │                │ 5. Result Merge │          │ • Similarity    │
│   implemented?" │                │                 │          │   Scores        │
└─────────────────┘                └─────────────────┘          └─────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           Key Data Flows                                     │
│                                                                             │
│ Input Processing:    Codebase → Validation → Chunking → Documents          │
│ Graph Creation:      Documents → Entity Extraction → Relationships → Neo4j │
│ Vector Creation:     Documents → Embeddings → Vector Index → Neo4j         │
│ Bridge Building:     Analysis → Chunk-Entity Mapping → Bridge Relations    │
│ Query Processing:    NL Query → Vector Search → Graph Context → Response   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Implementation Architecture

### Core Classes

#### GraphBuilder
**Responsibility**: Creates and manages the unified GraphRAG system

**Key Methods**:
```python
def create_unified_graphrag_system(documents):
    """Creates complete unified system with all layers"""
    # 1. Build knowledge graph (structural layer)
    # 2. Create vector index (semantic layer)  
    # 3. Build bridge relationships (integration layer)
    # 4. Maintain unified file metadata

def create_vector_index(documents):
    """Creates vector index while preserving existing graph"""
    # Coexistent creation without clearing structural data

def _create_bridge_relationships(documents):
    """Links semantic chunks to structural entities"""
    # Maps CodeChunks to Classes/Functions based on content
```

#### QueryProcessor  
**Responsibility**: Handles hybrid query processing

**Query Flow**:
```python
def process_query(query, k=5, include_graph_context=True):
    # 1. Vector Search: Find semantically relevant chunks
    # 2. Entity Mapping: Map chunks to entities via REPRESENTS  
    # 3. Graph Traversal: Explore relationships for context
    # 4. Response Generation: Combine insights from both layers
```

**Key Methods**:
- `vector_search()` - Pure vector similarity search
- `get_graph_context_for_chunks()` - Extract structural context
- `setup_retrievers()` - Initialize embeddings and verify index

### Database Schema

#### Complete Schema
```cypher
// Structural Layer (Knowledge Graph)
(Class)-[:INHERITS]->(Class)
(Class)-[:IMPLEMENTS]->(Interface)  
(Function)-[:CALLS]->(Function)
(File)-[:CONTAINS]->(Class|Function|Interface)
(Package)-[:CONTAINS]->(File)

// Semantic Layer (Vector Search)
(CodeChunk {embedding: [3072 dimensions]})
(File)-[:CONTAINS_CHUNK]->(CodeChunk)

// Bridge Layer (Integration)
(CodeChunk)-[:REPRESENTS]->(Class|Function)
(CodeChunk)-[:PART_OF_FILE]->(Class|Function)

// Unified File Layer
(File {path, name, language, total_chunks, total_lines})
```

#### Index Configuration
```cypher
// Vector index for semantic search
CREATE VECTOR INDEX code_chunks_vector_index
FOR (c:CodeChunk) ON (c.embedding)
OPTIONS {indexConfig: {
    `vector.dimensions`: 3072,
    `vector.similarity_function`: 'cosine'
}}

// Standard indexes for performance
CREATE INDEX class_id_index FOR (c:Class) ON (c.id)
CREATE INDEX function_id_index FOR (f:Function) ON (f.id)
CREATE INDEX file_path_index FOR (f:File) ON (f.path)
```

## Query Capabilities

### Query Types

#### 1. Semantic Queries
```
"Find authentication code" → Vector similarity search
"Show error handling patterns" → Embedding-based discovery
```

#### 2. Structural Queries  
```
"What classes inherit from BaseAdapter?" → Graph traversal
"Show all dependencies of UserService" → Relationship following
```

#### 3. Hybrid Queries
```
"Find auth code AND show its dependencies" → Vector + Graph
"How is the adapter pattern implemented?" → Semantic + Structural
```

### Example Cypher Queries

#### Find Code with Context
```cypher
// Find semantically similar code with structural context
MATCH (c:CodeChunk)-[:REPRESENTS]->(entity)
WHERE c.text CONTAINS "adapter"
RETURN c.text, entity.id, labels(entity)
```

#### Explore Dependencies
```cypher  
// Follow relationships from vector search results
MATCH (c:CodeChunk)-[:REPRESENTS]->(e1)-[r]->(e2)
WHERE c.chunk_id IN [0, 1, 2]  // From vector search
RETURN e1.id, type(r), e2.id
```

#### Unified File Analysis
```cypher
// Files with both semantic and structural data
MATCH (f:File)-[:CONTAINS_CHUNK]->(c:CodeChunk)
MATCH (f)-[:CONTAINS]->(entity)
RETURN f.name, count(c) as chunks, count(entity) as entities
```

## Performance Characteristics

### Scalability
- **Structural Layer**: Scales with code complexity and relationships
- **Semantic Layer**: Scales with content volume and similarity requirements  
- **Bridge Layer**: Scales with mapping accuracy and coverage
- **Independent Optimization**: Each layer can be tuned separately

### Memory Usage
- **Vector Embeddings**: ~12KB per code chunk (3072 dimensions × 4 bytes)
- **Graph Storage**: Depends on relationship density
- **Index Overhead**: Vector index requires additional memory
- **Query Processing**: Temporary memory for result aggregation

### Query Performance
- **Vector Search**: Fast similarity lookups (< 100ms for most codebases)
- **Graph Traversal**: Efficient relationship following (< 50ms for most queries)
- **Hybrid Processing**: Sequential vector → graph → response (< 200ms total)
- **Caching**: Query processor caches frequent entity mappings

## Technical Benefits

### Advantages of Hybrid Architecture
1. **Rich Context**: Combines semantic similarity with structural relationships
2. **Comprehensive Understanding**: Answers both "what" and "how" questions
3. **Flexible Querying**: Natural language queries with precise structural follow-up
4. **Scalable Design**: Each layer optimized for its specific task
5. **Maintainable**: Clear separation of concerns and responsibilities

### Production Readiness
- **Error Handling**: Graceful degradation when layers are incomplete
- **Performance Monitoring**: Real-time metrics for all components
- **Data Consistency**: ACID transactions for graph operations
- **Session Management**: Persistent state across browser refreshes
- **Cost Optimization**: Configurable API usage and caching strategies

---

This architecture enables CodeGraph to provide intelligent, context-aware code analysis that goes far beyond traditional keyword search or simple vector similarity, delivering a truly comprehensive understanding of codebase structure and semantics. 