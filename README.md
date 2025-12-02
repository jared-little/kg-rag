# Knowledge Graph RAG (kg-rag)
This is just an ongoing project to build and play with LLMs. It may change frequently.
A Retrieval-Augmented Generation (RAG) system that uses Neo4j graph database and OpenAI to build a knowledge graph from PDF documents and answer questions using hierarchical retrieval with step-back prompting.

## Overview

This package implements a sophisticated RAG pipeline that:
- Extracts and processes text from PDF documents
- Creates a hierarchical knowledge graph in Neo4j with parent-child chunk relationships
- Uses vector embeddings for semantic search
- Implements step-back prompting to improve question answering
- Retrieves relevant context through parent-child document hierarchy

## Features

- **PDF Processing**: Automatic extraction and chunking of PDF documents with title-based section splitting
- **Hierarchical Chunking**: Parent chunks (2000 tokens) with child chunks (500 tokens) for optimal retrieval
- **Vector Search**: Sentence transformers for embedding generation and semantic search
- **Graph Database**: Neo4j for storing document relationships and metadata
- **Step-back Prompting**: Generates broader questions to improve retrieval accuracy
- **Parent Retrieval**: Retrieves full parent chunks based on child chunk similarity

## Architecture

```
PDF → Extract Text → Split Sections → Parent Chunks → Child Chunks
                                            ↓              ↓
                                        Neo4j Graph ← Embeddings
                                            ↓
                                    Vector Search ← Question
                                            ↓
                                    Parent Retrieval → Answer
```

## Prerequisites

- Python 3.8+
- Neo4j database (running locally on port 7687)
- OpenAI API key

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/jared-little/kg-rag.git
cd kg-rag
```

### 2. Set Up Python Environment

It's recommended to use a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Neo4j

Install and start Neo4j:

**Option A: Using Neo4j Desktop**
1. Download [Neo4j Desktop](https://neo4j.com/download/)
2. Create a new project and database
3. Set password (read from environment) for example:
    - export NEO4J_URI='neo4j://127.0.0.1:7687'
    - export NEO4J_USERNAME='neo4j'
    - export NEO4J_PASSWORD='password'
4. Start the database

**Option B: Using Docker**
```bash
docker run \
    --name neo4j-kg-rag \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/abcd1234 \
    -v $HOME/neo4j/data:/data \
    neo4j:latest
```

**Option C: Using Homebrew (macOS)**
```bash
brew install neo4j
neo4j start
```

Verify Neo4j is running at: http://localhost:7474

### 5. Configure Environment Variables

Create a `dev.env` file in the project root:

```bash
# Create dev.env file
cat > dev.env << 'EOF'
export OPENAI_API_KEY="your-api-key-here"
EOF

# Source the environment file
source dev.env
```

**Note**: Make sure `dev.env` is in your `.gitignore` to avoid committing secrets.

### 6. Configure Neo4j Connection (Optional)

If you're using different Neo4j credentials, update `src/utilities/utils.py`:

```python
neo4j_user = 'neo4j'
neo4j_password = 'your-password'
neo4j_URI = 'neo4j://127.0.0.1:7687'
```

### 7. Verify Installation

Test your setup:

```bash
cd src
python -c "from utilities.utils import get_neo4j_driver, get_openai_client; print('✓ Setup successful!')"
```

## Usage

### 1. Download PDFs

Download a PDF from a URL:

```bash
cd src
python downloadPDF.py
```

Edit the script to change the URL and destination filename.

### 2. Upload and Process PDFs

Process PDFs and store them in Neo4j:

```bash
python upload_pdf.py
```

This will:
- Extract text from PDFs
- Split into sections based on document structure
- Create parent and child chunks
- Generate embeddings
- Store everything in Neo4j with vector index

### 3. Query the Knowledge Base

Run queries against your knowledge graph:

```bash
python retrieve.py
```

Edit the question in the script or modify it to accept CLI arguments.

## Project Structure

```
kg-rag/
├── data/                   # PDF files storage
├── src/
│   ├── downloadPDF.py      # Download PDFs from URLs
│   ├── upload_pdf.py       # Process and upload PDFs to Neo4j
│   ├── retrieve.py         # Query and retrieve answers
│   └── utilities/
│       ├── __init__.py
│       └── utils.py        # Shared utilities (chunking, embedding, Neo4j)
├── requirements.txt        # Python dependencies
├── dev.env                # Environment variables (not committed)
└── README.md              # This file
```

## Components

### `downloadPDF.py`
Simple utility to download PDFs from remote URLs.

### `upload_pdf.py`
- Extracts text from PDFs using `pdfplumber`
- Splits text into sections using regex patterns for document titles
- Creates hierarchical chunks (parent: 2000 tokens, child: 500 tokens)
- Generates embeddings using sentence-transformers
- Stores in Neo4j with parent-child relationships
- Creates vector index for similarity search

### `retrieve.py`
- Implements step-back prompting to generalize questions
- Performs vector similarity search on child chunks
- Retrieves parent chunks for full context
- Generates answers using OpenAI GPT models

### `utilities/utils.py`
Shared utilities including:
- `chunk_text()`: Text chunking with overlap
- `embed()`: Generate embeddings using sentence-transformers
- `get_neo4j_driver()`: Neo4j database connection
- `get_openai_client()`: OpenAI API client
- `chat()`: OpenAI chat completion wrapper
- `num_tokens_from_string()`: Token counting

## Neo4j Schema

```cypher
(:PDF)-[:HAS_PARENT]->(:Parent)-[:HAS_CHILD]->(:Child)
```

- **PDF Node**: Represents a document
- **Parent Node**: Large context chunks (~2000 tokens)
- **Child Node**: Smaller chunks (~500 tokens) with embeddings

## Configuration

### Chunking Parameters
- Parent chunk size: 2000 tokens
- Parent overlap: 40 tokens
- Child chunk size: 500 tokens
- Child overlap: 20 tokens

### Models
- Embeddings: `sentence-transformers/all-MiniLM-L12-v2`
- Chat: `gpt-4o-mini`

## Example

```python
from src.retrieve import rag_pipeline

# Ask a question
answer = rag_pipeline("What is gfex?")
```

The system will:
1. Generate a step-back question
2. Search for relevant child chunks
3. Retrieve parent chunks for context
4. Generate an answer using GPT

## Dependencies

Key dependencies:
- `neo4j`: Graph database driver
- `openai`: GPT API client
- `sentence-transformers`: Embedding generation
- `pdfplumber`: PDF text extraction
- `tiktoken`: Token counting
- `torch`: Deep learning framework

See `requirements.txt` for complete list.

## Security Note

⚠️ **Important**: Never commit API keys to version control. Store sensitive credentials in `dev.env` and ensure it's added to `.gitignore`.

## License

MIT

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Authors

Jared Little
