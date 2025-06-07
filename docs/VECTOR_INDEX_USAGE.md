# Vector Index Test Usage Guide

## 🚀 **Professional Vector Index Testing**

The vector index test has been completely rewritten to be more professional and cost-effective. It now clones repositories directly and provides flexible cost control.

## 📋 **Usage Options**

### **1. Basic Test (Cost-Limited) - Default**
```bash
python tests/test_vector_index.py
```

**What it does:**
- Clones java-design-patterns repository to temporary directory
- Processes only Java/Python files
- Limits to 20 code chunks maximum
- Runs 2 vector search queries
- **Estimated cost: ~$0.002**

### **2. Full Test (No Cost Limits)**
```bash
python tests/test_vector_index.py --full
```

**What it does:**
- Processes all supported file types
- No chunk limitations
- Runs 3 vector search queries
- **Estimated cost: ~$0.05-0.20** (depending on repository size)

### **3. Custom Repository**
```bash
python tests/test_vector_index.py --repo https://github.com/spring-projects/spring-petclinic.git
```

**What it does:**
- Clones specified repository
- Uses cost-limited mode by default
- Adapts queries based on repository type

### **4. Full Test with Custom Repository**
```bash
python tests/test_vector_index.py --full --repo https://github.com/spring-projects/spring-petclinic.git
```

## 🎯 **Test Features**

### **✅ Professional Implementation**
- Object-oriented design with `VectorIndexTester` class
- Proper argument parsing with `argparse`
- Clean, professional logging (no childish messages)
- Comprehensive error handling
- Automatic cleanup of temporary files

### **💰 Cost Control**
- **Limited Mode**: 20 chunks max, Java/Python only, 2 queries
- **Full Mode**: All files, no limits, 3 queries
- **Cost estimation** before API calls
- **Interactive confirmation** for clearing existing data

### **🔄 Repository Management**
- **Direct cloning** from any Git repository
- **Temporary directories** (auto-cleanup)
- **No dependency** on pre-existing local repositories
- **Flexible repository selection**

### **📊 Comprehensive Testing**
1. **Repository cloning** and validation
2. **Codebase parsing** with configurable limits
3. **Vector index creation** with embeddings
4. **Vector search testing** with multiple queries
5. **Metadata verification** (CodeChunk, File nodes, relationships)

## 🎛️ **Configuration Options**

### **Cost Limiting (Default)**
```python
# Limited mode settings
chunk_size = 1000
chunk_overlap = 100
include_extensions = ['.java', '.py']
max_chunks = 20
max_queries = 2
```

### **Full Mode**
```python
# Full mode settings
chunk_size = 500
chunk_overlap = 50
include_extensions = None  # All supported types
max_chunks = unlimited
max_queries = 3
```

## 📈 **Expected Output**

### **Successful Run Example:**
```
🚀 Vector Index Test Setup
📊 Cost limiting: Enabled
📂 Repository: https://github.com/iluwatar/java-design-patterns.git

📥 Cloning Repository
✅ Repository cloned successfully
📍 Location: /tmp/vector_test_xyz/java-design-patterns

📄 Parsing Codebase
💰 Cost-limited mode: Java/Python files only
📉 Limited from 156 to 20 chunks
✅ Parsed 20 code chunks

🔍 Creating Vector Index
📊 Processing 20 documents
💰 Estimated API cost: ~$0.0020
✅ Vector index created successfully
⏱️ Time taken: 4.23 seconds

🔎 Testing Vector Search
🔍 Query 1: 'adapter pattern implementation'
✅ Found 3 results for query: 'adapter pattern implementation'
   📄 Top result (score: 0.8234)
   📝 Preview: public class FishingBoatAdapter implements RowingBoat...

📊 Verifying Metadata
✅ Found 3 CodeChunk samples
✅ Found 3 File samples
✅ Found 20 CONTAINS_CHUNK relationships

🎉 Vector Index Test PASSED!
💡 Explore results at http://localhost:7474
```

## 🔧 **Integration with Test Suite**

The vector index test is integrated into the main test runner:

```bash
# Run all tests (includes limited vector index test)
python tests/run_tests.py
```

## 💡 **Best Practices**

1. **Start with limited mode** to understand the system
2. **Use full mode** only when you need comprehensive testing
3. **Specify custom repositories** to test different codebases
4. **Monitor API costs** using the cost estimates
5. **Clean up existing data** when prompted for fresh tests

## 🎯 **What Gets Created**

After running the test, you'll have:
- **CodeChunk nodes** with 3072-dimensional embeddings
- **File nodes** with comprehensive metadata
- **CONTAINS_CHUNK relationships** linking files to chunks
- **Vector index** named `code_chunks_vector_index`
- **Searchable semantic index** for code similarity

## 🌐 **Exploring Results**

Visit http://localhost:7474 and use these queries:

```cypher
-- View vector embeddings
MATCH (c:CodeChunk)
RETURN c.file_path, size(c.embedding) as dimensions
LIMIT 5

-- See file metadata
MATCH (f:File)
RETURN f.name, f.total_chunks, f.language
LIMIT 5

-- Check relationships
MATCH (f:File)-[:CONTAINS_CHUNK]->(c:CodeChunk)
RETURN f.name, count(c) as chunks
ORDER BY chunks DESC
```

The new implementation is professional, cost-effective, and highly configurable! 🎉 