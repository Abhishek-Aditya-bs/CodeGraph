# Code Graph

A GraphRAG (Graph-based Retrieval-Augmented Generation) system for analyzing and querying codebases using knowledge graphs and vector embeddings.

## Overview

Code Graph uses a graph-based approach to understand codebases by:
- Building knowledge graphs to capture relationships between code elements
- Creating vector embeddings for semantic search
- Combining graph traversal with vector search for enhanced query responses
- Providing a simple Streamlit interface for codebase analysis

## Features

- **Repository Analysis**: Supports GitHub/Bitbucket URLs and local folders
- **Knowledge Graph**: Captures relationships between files, functions, and classes
- **Vector Search**: Semantic search using OpenAI embeddings
- **GraphRAG Queries**: Multi-hop reasoning for complex code analysis
- **Interactive UI**: Simple Streamlit interface for querying

## Architecture

- **Backend**: Python 3.10+, Neo4j, LangChain, OpenAI API
- **Frontend**: Streamlit
- **Database**: Neo4j (graph database + vector index)
- **Deployment**: Docker-ready, AWS-compatible

## Quick Start

### Prerequisites

- Python 3.10+
- Docker (for Neo4j)
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Code-Graph
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Start Neo4j with Docker:
```bash
docker run -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_apoc_export_file_enabled=true \
  neo4j:latest
```

6. Run the application:
```bash
streamlit run app/main.py
```

## Configuration

Create a `.env` file with the following variables:

```env
# Neo4j Configuration
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Optional Configuration
CHUNK_SIZE=500
CHUNK_OVERLAP=50
EMBEDDING_MODEL=text-embedding-3-large
LLM_MODEL=gpt-4o
```

## Usage

1. Open the Streamlit interface at `http://localhost:8501`
2. Enter a GitHub/Bitbucket URL or local folder path
3. Wait for the system to process and build the knowledge graph
4. Query your codebase using natural language

For exploring generated knowledge graphs, see the [Neo4j Browser Guide](docs/NEO4J_BROWSER_GUIDE.md).

## Development

### Project Structure

```
Code-Graph/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # Streamlit UI and entry point
│   ├── ingestion.py         # Codebase ingestion and parsing
│   ├── graph_builder.py     # Knowledge graph and embeddings
│   ├── query_processor.py   # GraphRAG query handling
│   └── config.py            # Configuration management
├── docs/                    # Documentation guides
│   ├── README.md            # Documentation index
│   ├── TESTS_GUIDE.md       # Testing guide
│   └── NEO4J_BROWSER_GUIDE.md # Neo4j exploration guide
├── scripts/
│   └── deploy_aws.sh        # AWS deployment script
├── Dockerfile               # Docker configuration
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (not committed)
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

### Running Tests

See the comprehensive [Tests Guide](docs/TESTS_GUIDE.md) for detailed testing instructions.

```bash
# Run all tests
python tests/run_tests.py

# Run specific test
python tests/test_knowledge_graph_generation.py
```

### Code Formatting

```bash
black app/
flake8 app/
```

## Docker Deployment

Build and run with Docker:

```bash
docker build -t code-graph .
docker run -p 8501:8501 code-graph
```

## AWS Deployment

See `scripts/deploy_aws.sh` for AWS deployment instructions.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Acknowledgments

- Built for the Global Innovation Hackathon
- Uses Neo4j for graph database capabilities
- Powered by OpenAI's language models
- Built with LangChain for RAG pipeline integration 