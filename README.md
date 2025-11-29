# Sentinel - The Self-Healing Knowledge Graph

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-grade, self-healing knowledge graph system with temporal validity tracking, built on Neo4j, LangChain, and Firecrawl.

## 🌟 Features

- **Temporal Validity Tracking**: Time-travel queries to see how knowledge evolved
- **Self-Healing**: Autonomous detection and correction of stale information
- **Idempotent Ingestion**: Content-hash based deduplication prevents duplicate writes
- **LLM-Powered Extraction**: Uses local Ollama models for entity/relationship extraction
- **RESTful API**: FastAPI backend with real-time graph visualization
- **Modern UI**: Next.js dashboard with 3D force-directed graph

## 📁 Project Structure

```
Sentinel/
├── sentinel_core/              # [LIBRARY] The pip-installable logic
│   ├── __init__.py             # Package exports
│   ├── models.py               # Pydantic v2 Models (GraphNode, TemporalEdge)
│   ├── graph_store.py          # Neo4j Adapter with Time-Travel Logic
│   ├── extractor.py            # LLM Extraction (Instructor + LiteLLM)
│   ├── scraper.py              # Firecrawl Adapter + Hashing
│   └── orchestrator.py         # Main "Sentinel" class users interact with
├── sentinel_service/           # [API] FastAPI backend for the UI
│   ├── main.py                 # API Endpoints
│   ├── worker.py               # Celery/Redis Tasks (placeholder)
│   ├── schemas.py              # API Request/Response models
│   └── query_engine.py         # Natural language query engine
├── sentinel_ui/                # [FRONTEND] Next.js Dashboard
│   ├── app/                    # Next.js 13+ App Router
│   │   ├── page.tsx            # Dashboard Page
│   │   └── globals.css         # Global styles
│   ├── package.json            # Frontend dependencies
│   └── next.config.js          # Next.js configuration
├── examples/                   # [DOCS] Usage scripts
│   └── basic_bot.py            # Quick start script
├── tests/                      # [TESTS] Pytest suite
│   ├── test_phase1.py          # Infrastructure tests
│   ├── test_phase2.py          # Ingestion tests
│   ├── test_phase3.py          # Query tests
│   └── test_phase4.py          # Healing tests
├── docker-compose.yml          # Infrastructure (Neo4j, Redis, Postgres)
├── pyproject.toml              # Python dependencies (setuptools)
└── README.md                   # This file
```

## 🚀 Quick Start

### Prerequisites

- **Docker** & **Docker Compose** (for Neo4j and Postgres)
- **Python 3.11+**
- **Node.js 18+** (for the UI)
- **Ollama** running locally (for LLM extraction)
- **Firecrawl API Key** (get one at [firecrawl.dev](https://firecrawl.dev))

### 1. Start Infrastructure

```bash
# Start Neo4j and Postgres
docker-compose up -d

# Verify containers are running
docker-compose ps
```

### 2. Install Python Dependencies

```bash
# Install the package in development mode
pip install -e .

# Or use requirements.txt
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your credentials
# Required:
# - FIRECRAWL_API_KEY
# - NEO4J_PASSWORD
# - POSTGRES_PASSWORD
```

### 4. Run the API

```bash
# Start the FastAPI service
cd sentinel_service
python main.py

# API will be available at http://localhost:8000
```

### 5. Run the UI

```bash
# Install frontend dependencies
cd sentinel_ui
npm install

# Start development server
npm run dev

# UI will be available at http://localhost:3000
```

## ✅ How to Test & Verify

### Test Phase 1: The Brain
Run the core test suite to verify the logic:
```bash
pytest tests/test_core.py
```
If it passes, your "Brain" (Core Library) is working correctly.

### Test Phase 2: The Ingestion Engine
Run the basic bot example twice to verify idempotent ingestion:
```bash
python examples/basic_bot.py
```
Run it once to ingest. Run it a second time pointing to the same URL. It should say **"Skipping update (content unchanged)"**. This confirms the hashing and diffing logic.

### Test Phase 3: The Time Machine
1. Spin up the full stack: `docker-compose up -d`
2. Start the API and Worker (see Quick Start)
3. Open the Dashboard: `http://localhost:3000`
4. Ingest a URL via the UI
5. **Drag the time slider** at the bottom.
If nodes appear/disappear as you move through time, you have successfully built a **Time Machine for Data**.

## 💻 Usage Examples

### Using the Library

```python
from sentinel_core import Sentinel, GraphManager, InfoExtractor, SentinelScraper
import asyncio

# Initialize components
graph = GraphManager()
scraper = SentinelScraper(api_key="your_firecrawl_key")
extractor = InfoExtractor(model="llama3.1")

# Create Sentinel orchestrator
sentinel = Sentinel(graph, scraper, extractor)

# Run autonomous healing
async def heal():
    result = await sentinel.run_healing_cycle(days_threshold=7)
    print(f"Healed {result['healed_count']} stale URLs")

asyncio.run(heal())
```

### Using the API

```bash
# Ingest a URL
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"url": "https://en.wikipedia.org/wiki/Tesla,_Inc."}'

# Query the graph
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Who founded Tesla?"}'

# Get graph snapshot
curl http://localhost:8000/api/graph-snapshot

# Get statistics
curl http://localhost:8000/api/stats
```

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/test_phase1.py -v

# Run with coverage
pytest --cov=sentinel_core --cov-report=html
```

## 🏗️ Architecture

### Sentinel Core (Library)

The core library is a standalone Python package that can be pip-installed. It provides:

1. **graph_store.py**: Neo4j adapter with temporal edge management
2. **extractor.py**: LLM-based triple extraction using LangChain + Ollama
3. **scraper.py**: Firecrawl integration with content hashing
4. **orchestrator.py**: Main Sentinel class that coordinates healing
5. **models.py**: Pydantic v2 data models

### Sentinel Service (API)

FastAPI backend that exposes the core functionality via REST API:

- `/api/ingest`: Manually ingest a URL
- `/api/query`: Natural language queries
- `/api/graph-snapshot`: Get graph state (with optional time-travel)
- `/api/stats`: Get graph statistics
- `/api/health`: Health check

### Sentinel UI (Frontend)

Next.js 13+ dashboard with:

- 3D force-directed graph visualization (react-force-graph-3d)
- Real-time graph updates
- Natural language query interface
- Temporal navigation (time-travel slider)

## 📊 Key Concepts

### Temporal Edges

Every relationship in the graph has:
- `valid_from`: When the relationship became valid
- `valid_to`: When it became invalid (NULL = still valid)
- `last_verified`: Last time we confirmed it's still true
- `content_hash`: SHA-256 hash for deduplication

### Self-Healing

The Sentinel agent:
1. Finds stale URLs (not verified in > 7 days)
2. Re-scrapes them using Firecrawl
3. Extracts new triples with LLM
4. Compares hashes and updates graph
5. Runs autonomously every 6 hours (configurable)

### Idempotent Ingestion

When you ingest the same URL twice:
- Content is hashed (SHA-256)
- If hash matches existing edge: only update `last_verified`
- If hash changed: invalidate old edge, create new edge
- Zero wasted writes on unchanged content

## 🐛 Troubleshooting

### Docker Issues

```bash
# View logs
docker-compose logs -f neo4j
docker-compose logs -f postgres

# Restart services
docker-compose restart

# Clean start
docker-compose down -v
docker-compose up -d
```

### Neo4j Connection Issues

1. Ensure Neo4j is running: `docker-compose ps`
2. Access Neo4j Browser: http://localhost:7474
3. Check credentials in `.env`

### Frontend Issues

The CSS warnings about `@tailwind` directives are normal and expected. They don't affect functionality. To suppress them:

1. Install the Tailwind CSS IntelliSense extension for VS Code
2. Or ignore CSS validation in VS Code settings

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📧 Contact

For questions or support, please open an issue on GitHub.

---
Built with ❤️ by [@Om7035](https://github.com/Om7035) using Neo4j, FastAPI, Next.js, and LangChain
