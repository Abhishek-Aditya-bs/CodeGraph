# Code Graph: Project Plan for Global Innovation Hackathon

## Project Overview

### What is the Project About?
*Code Graph* is a Retrieval-Augmented Generation (RAG) system that uses a graph-based approach (GraphRAG) to analyze and query codebases. Unlike traditional RAG, which relies on vector search, GraphRAG builds a knowledge graph to capture relationships between code elements (e.g., files, functions, classes, dependencies). The system ingests a codebase from a GitHub/Bitbucket URL or local folder, constructs a knowledge graph, generates embeddings, and stores both in a Neo4j database. Users can query the codebase via a simple Streamlit UI to gain insights, such as understanding code structure, finding dependencies, or summarizing functionality.

The project will be developed locally on a MacBook using Cursor IDE, with Neo4j running in Docker for simplicity. The codebase will be pushed to a personal GitHub repository with a README for portfolio showcasing. For the hackathon, the system will be deployed to an AWS sandbox, ensuring compatibility with both local and cloud environments.

### Benefits of GraphRAG Over Traditional RAG
- **Rich Contextual Understanding**: Captures relationships (e.g., function calls, imports), enabling multi-hop reasoning (e.g., “What functions call this method?”), which traditional RAG’s vector search cannot handle.
- **Improved Accuracy**: Combines graph traversal with vector search for more relevant, contextually grounded results.
- **Enhanced Explainability**: The knowledge graph provides a structured view, making it easier to trace answer derivation (e.g., dependency chains).
- **Better Complex Queries**: Excels at queries requiring relationships (e.g., “Find classes depending on this module”).
- **Scalability for Codebases**: Graphs naturally represent code hierarchies, ideal for large codebases.

### Project Goals
- Build a simple GraphRAG system to process and query a codebase.
- Store knowledge graph and vector index in Neo4j.
- Provide a Streamlit UI for querying.
- Ensure compatibility for local (Docker) and AWS sandbox deployment.
- Push to GitHub with a README for portfolio and hackathon showcasing.

## Dependencies and Frameworks

### Core Dependencies
- **Python**: 3.10+ (stable, widely supported).
- **Neo4j**: Graph database for knowledge graphs and vector indices (Docker locally, AWS-compatible).
- **Streamlit**: Lightweight UI framework.
- **LangChain**: Simplifies LLM and Neo4j integration for GraphRAG.
- **OpenAI API**: For embeddings and query responses (requires API key).
- **neo4j-graphrag-python**: Official Neo4j GraphRAG package.
- **GitPython**: For cloning GitHub/Bitbucket repositories.
- **python-dotenv**: For environment variables (Neo4j, OpenAI credentials).

### Frameworks and Libraries
- **LangChain**: Document parsing, embedding generation, GraphRAG pipelines.
- **Neo4j Python Driver**: Connects to Neo4j for graph/vector operations.
- **APOC Library**: Neo4j plugin for advanced graph operations.
- **OpenAI Embeddings**: Generates vector embeddings (`text-embedding-3-large`).
- **FastAPI** (optional, AWS): Minimal API wrapper if AWS requires it.

### Development Tools
- **Cursor IDE**: Agentic programming and rapid development.
- **Docker**: Runs Neo4j locally.
- **Git**: Version control and GitHub integration.
- **AWS CLI**: For AWS sandbox deployment (configured later).

### Environment Setup
- **Local**: Python virtual environment, Docker for Neo4j, `.env` for credentials.
- **AWS**: Docker-compatible Neo4j or AWS-managed Neo4j (e.g., AuraDB free tier if supported).

## Project Architecture

### High-Level Architecture
1. **Input Layer**:
   - Accepts codebase via GitHub/Bitbucket URL or local folder.
   - Uses GitPython to clone repositories or read local files.
2. **Processing Layer**:
   - **Document Parser**: Splits code into chunks (e.g., functions, classes) using LangChain.
   - **Knowledge Graph Builder**: Extracts entities (files, functions) and relationships (imports, calls) using LangChain’s LLMGraphTransformer.
   - **Embedding Generator**: Creates vector embeddings using OpenAI’s `text-embedding-3-large`.
   - **Storage**: Stores graph and vector index in Neo4j.
3. **Retrieval Layer**:
   - Combines vector search and graph traversal using Neo4j’s VectorRetriever and GraphRAG pipeline.
   - Processes queries via LangChain and OpenAI’s GPT-4o.
4. **Presentation Layer**:
   - Streamlit UI for queries and results (text, optional graph visualization).
5. **Deployment Layer**:
   - Local: Docker with Neo4j and Streamlit.
   - AWS: Docker containers or AWS services (e.g., EC2, ECS).

### Project Structure
```
Code-Graph/
├── app/
│   ├── __init__.py
│   ├── main.py              # Streamlit UI and entry point
│   ├── ingestion.py         # Codebase ingestion and parsing
│   ├── graph_builder.py     # Knowledge graph and embeddings
│   ├── query_processor.py   # GraphRAG query handling
│   └── config.py            # Configuration and environment variables
├── Dockerfile               # Docker setup for Neo4j and app
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (not committed)
├── README.md                # GitHub documentation
├── .gitignore               # Git ignore file
└── scripts/
    └── deploy_aws.sh        # AWS deployment script (placeholder)
```

## Phase-Wise Implementation Plan

### Phase 1: Environment Setup and Project Initialization
**Goal**: Set up development environment and initialize GitHub repository.

#### Task 1.1: Set Up Python Environment
- **Description**: Create and activate a Python virtual environment, install dependencies.
- **Steps**:
  - Run `python -m venv venv` and `source venv/bin/activate`.
  - Create `requirements.txt`: `neo4j`, `streamlit`, `langchain`, `langchain-openai`, `neo4j-graphrag-python`, `python-dotenv`, `GitPython`.
  - Install: `pip install -r requirements.txt`.
- **Tools**: Python 3.10+, pip.
- **Output**: Virtual environment with dependencies.

#### Task 1.2: Set Up Neo4j in Docker
- **Description**: Run Neo4j locally with APOC enabled.
- **Steps**:
  - Pull image: `docker pull neo4j:latest`.
  - Run container: `docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password -e NEO4J_apoc_export_file_enabled=true neo4j:latest`.
  - Verify at `http://localhost:7474`.
  - Create `.env`: `NEO4J_URI=neo4j://localhost:7687`, `NEO4J_USERNAME=neo4j`, `NEO4J_PASSWORD=password`.
- **Tools**: Docker, Neo4j.
- **Output**: Neo4j running locally.

#### Task 1.3: Initialize Project Structure
- **Description**: Create folder structure and initialize Git.
- **Steps**:
  - Create folders/files per project structure.
  - Run `git init`.
  - Create `.gitignore` (exclude `venv/`, `.env`).
  - Create basic `README.md` with project title/description.
  - Commit: `git add . && git commit -m "Initial project structure"`.
- **Tools**: Git, Cursor IDE.
- **Output**: Project structure and Git repository.

#### Task 1.4: Configure Environment Variables
- **Description**: Set up environment variable loading.
- **Steps**:
  - Create `app/config.py` to load `.env` with `python-dotenv`.
  - Add to `.env`: `OPENAI_API_KEY=<your_key>`.
  - Test loading with a script in `config.py`.
- **Tools**: python-dotenv, Cursor IDE.
- **Output**: Accessible environment variables.

### Phase 2: Codebase Ingestion and Parsing
**Goal**: Build ingestion pipeline for codebases.

#### Task 2.1: Implement Repository Cloning
- **Description**: Clone GitHub/Bitbucket repositories.
- **Steps**:
  - Create `app/ingestion.py`.
  - Use `GitPython` to clone from a URL.
  - Handle errors (invalid URLs, authentication).
  - Test with a public repository.
- **Tools**: GitPython.
- **Output**: Repository cloning function.

#### Task 2.2: Support Local Folder Input
- **Description**: Read code files from a local folder.
- **Steps**:
  - Add local path support in `ingestion.py`.
  - Use `pathlib` to read code files (e.g., `.py`, `.js`).
  - Filter non-code files.
  - Test with a sample folder.
- **Tools**: Python (`pathlib`).
- **Output**: Local file reading function.

#### Task 2.3: Parse Code into Chunks
- **Description**: Split code into chunks for processing.
- **Steps**:
  - Use LangChain’s `RecursiveCharacterTextSplitter` (500 characters, overlap).
  - Preserve code structure (functions/classes).
  - Store as LangChain `Document` objects with metadata (file path, line).
  - Test on a sample file.
- **Tools**: LangChain (`langchain.text_splitter`).
- **Output**: Chunked `Document` objects.

### Phase 3: Knowledge Graph and Vector Index Creation
**Goal**: Build and store graph and vector index in Neo4j.

#### Task 3.1: Connect to Neo4j
- **Description**: Establish Neo4j connection.
- **Steps**:
  - In `app/graph_builder.py`, use `neo4j.GraphDatabase.driver` with `.env` credentials.
  - Test with a Cypher query (`RETURN 1`).
  - Handle connection errors.
- **Tools**: Neo4j Python Driver, python-dotenv.
- **Output**: Neo4j connection.

#### Task 3.2: Generate Knowledge Graph
- **Description**: Extract entities/relationships for knowledge graph.
- **Steps**:
  - Use LangChain’s `LLMGraphTransformer` with GPT-4o to extract entities (files, functions, classes) and relationships (imports, calls).
  - Schema: nodes (`File`, `Function`, `Class`), relationships (`CONTAINS`, `CALLS`, `IMPORTS`).
  - Store in Neo4j using `neo4j-graphrag-python`’s `SimpleKGPipeline`.
  - Test on sample chunks.
- **Tools**: LangChain, neo4j-graphrag-python, OpenAI API.
- **Output**: Knowledge graph in Neo4j.

#### Task 3.3: Create Vector Index
- **Description**: Generate and store vector embeddings.
- **Steps**:
  - Use OpenAI’s `text-embedding-3-large` for chunk embeddings.
  - Create vector index in Neo4j with `neo4j_graphrag.indexes.create_vector_index`.
  - Store embeddings with chunk text/metadata.
  - Test vector search.
- **Tools**: OpenAI Embeddings, neo4j-graphrag-python.
- **Output**: Vector index in Neo4j.

### Phase 4: Query Processing and UI Development
**Goal**: Implement GraphRAG query pipeline and Streamlit UI.

#### Task 4.1: Implement GraphRAG Query Pipeline
- **Description**: Build query processor with vector search and graph traversal.
- **Steps**:
  - Create `app/query_processor.py`.
  - Use `neo4j_graphrag.retrievers.VectorRetriever` and `GraphRAG` pipeline.
  - Process queries with GPT-4o.
  - Test with sample queries (e.g., “What functions call X?”).
- **Tools**: neo4j-graphrag-python, LangChain, OpenAI API.
- **Output**: Query pipeline.

#### Task 4.2: Develop Streamlit UI
- **Description**: Create UI for querying codebase.
- **Steps**:
  - Create `app/main.py` with Streamlit.
  - Add inputs for codebase URL/path and query.
  - Display results as text (optional: `st.graphviz` for graph visualization).
  - Test with `streamlit run app/main.py`.
- **Tools**: Streamlit.
- **Output**: Streamlit UI.

### Phase 5: GitHub Integration and AWS Preparation
**Goal**: Finalize for GitHub and prepare AWS deployment.

#### Task 5.1: Finalize README and Push to GitHub
- **Description**: Complete README and push code.
- **Steps**:
  - Update `README.md`: overview, setup, usage.
  - Create GitHub repository, push: `git push origin main`.
  - Verify repository accessibility.
- **Tools**: Git, GitHub.
- **Output**: Code on GitHub with README.

#### Task 5.2: Prepare for AWS Deployment
- **Description**: Create Docker-based AWS setup.
- **Steps**:
  - Create `Dockerfile` for app (Streamlit + Python) and Neo4j.
  - Write `scripts/deploy_aws.sh` (placeholder for AWS CLI).
  - Test `Dockerfile`: `docker build -t code-graph .`.
  - Document AWS steps in `README.md`.
- **Tools**: Docker, AWS CLI.
- **Output**: Docker setup for AWS.

## Future Enhancements
- **Graph Visualization**: Interactive visualization with `yfiles-jupyter-graphs`.
- **Hybrid Retrieval**: Add keyword search.
- **Code Summarization**: LLM-based summaries.
- **Authentication**: GitHub/Bitbucket OAuth for private repos.
- **AWS Optimization**: Use AWS-managed Neo4j or ECS.

## Next Steps
1. Save this file as `project_plan.md`.
2. Feed into Cursor’s context or reference in prompts.
3. Start with Task 1.1: “Implement Task 1.1 from project_plan.md.”
4. Work task-by-task, testing each.
5. Push to GitHub (Phase 5).
6. Deploy to AWS sandbox during hackathon (Task 5.2).