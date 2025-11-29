# 🧠 Sentinel - The Self-Healing Knowledge Graph

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Next.js](https://img.shields.io/badge/Next.js-13+-black.svg)](https://nextjs.org/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.0+-blue.svg)](https://neo4j.com/)

**Sentinel** is a production-grade, self-healing knowledge graph system that automatically extracts, stores, and visualizes knowledge from the web. It combines temporal validity tracking, intelligent fact extraction, and autonomous healing to keep your knowledge base fresh and accurate.

### 🎯 In Simple Terms
Sentinel is like a **smart librarian that reads websites, extracts facts, visualizes connections, and keeps everything up-to-date automatically**. Built on Neo4j, Firecrawl, and LLMs.

## 🌟 Key Features

| Feature | What It Does |
|---------|-------------|
| **⏰ Temporal Validity** | See how knowledge evolved over time - time-travel queries |
| **🔄 Self-Healing** | Automatically detects and corrects stale information |
| **🚫 Idempotent Ingestion** | SHA-256 hashing prevents duplicate data storage |
| **🧠 LLM-Powered** | Local Ollama models extract entities and relationships |
| **🔌 REST API** | FastAPI backend for easy integration |
| **📊 3D Visualization** | Interactive neural network-style graph with draggable nodes |
| **💾 Graph Database** | Neo4j for powerful relationship queries |
| **🔐 Privacy-First** | All AI runs locally - no data sent to external services |

### 🎬 What Happens Behind the Scenes

```
Website URL
    ↓
Firecrawl (Web Scraper) → Extracts clean text
    ↓
Ollama (Local AI) → Extracts facts & relationships
    ↓
Neo4j (Graph DB) → Stores with timestamps
    ↓
3D UI → Visualizes as interactive graph
    ↓
Self-Healing Agent → Keeps facts fresh automatically
```

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

## 🏗️ Architecture Overview

### Three-Tier Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  TIER 1: USER INTERFACE (Next.js + React + Three.js)       │
│  - 3D Graph Visualization                                   │
│  - Draggable Nodes (Neurons)                               │
│  - Time-Travel Slider                                       │
│  - Natural Language Query Box                               │
└─────────────────────────────────────────────────────────────┘
                           ↕ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│  TIER 2: API LAYER (FastAPI)                               │
│  - /api/ingest - Add URLs                                   │
│  - /api/query - Ask questions                               │
│  - /api/graph-snapshot - Get graph at time T               │
│  - /api/stats - Statistics                                  │
│  - /api/health - System status                              │
└─────────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────────┐
│  TIER 3: CORE LOGIC (Python Library)                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ SentinelScraper (Firecrawl)                         │   │
│  │ - Visits websites                                   │   │
│  │ - Extracts clean text                              │   │
│  │ - Hashes content (SHA-256)                         │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ InfoExtractor (Ollama + LangChain)                  │   │
│  │ - Extracts entities & relationships                │   │
│  │ - Assigns confidence scores                        │   │
│  │ - Runs locally (no external AI calls)              │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ GraphManager (Neo4j Adapter)                        │   │
│  │ - Stores facts with timestamps                     │   │
│  │ - Manages temporal validity                        │   │
│  │ - Supports time-travel queries                     │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Sentinel Orchestrator                              │   │
│  │ - Coordinates all components                       │   │
│  │ - Runs healing cycles                              │   │
│  │ - Manages workflow                                 │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────────┐
│  EXTERNAL SERVICES                                          │
│  • Firecrawl API (Web Scraping)                            │
│  • Ollama (Local AI Model)                                 │
│  • Neo4j Database (Graph Storage)                          │
│  • PostgreSQL (Optional: Metadata)                         │
└─────────────────────────────────────────────────────────────┘
```

### Component Details

#### 1. **Sentinel Core** (Python Library)
The brain of the system. Handles all logic:
- **graph_store.py**: Neo4j adapter with temporal edge management
- **extractor.py**: LLM-based fact extraction using Ollama
- **scraper.py**: Firecrawl integration with content hashing
- **orchestrator.py**: Coordinates all components and healing cycles
- **models.py**: Pydantic v2 data models

#### 2. **Sentinel Service** (FastAPI Backend)
Exposes core functionality via REST API:
- `POST /api/ingest` - Add new URL for analysis
- `POST /api/query` - Ask natural language questions
- `GET /api/graph-snapshot` - Get graph at specific time
- `GET /api/stats` - Get statistics
- `GET /api/health` - Health check

#### 3. **Sentinel UI** (Next.js Frontend)
Interactive 3D visualization:
- 3D force-directed graph (nodes repel/attract like magnets)
- Draggable nodes (drag to rearrange)
- Time-travel slider (see graph at any point in history)
- Natural language query interface
- Real-time updates

## 📊 Key Concepts Explained

### 1. **Temporal Edges** ⏰
Every fact in Sentinel has a timeline:
```
Fact: "Elon Musk is CEO of Tesla"

Timeline:
2008-06-03: valid_from (became true)
2022-08-09: valid_to (became false)
2024-11-29: last_verified (last checked)

Result: You can ask "Show me the graph in 2015" 
        and it will show Elon as CEO (because 2008 < 2015 < 2022)
```

### 2. **Self-Healing** 🔄
Sentinel automatically keeps facts fresh:
```
Every 6 hours:
1. Find facts not verified in > 7 days
2. Re-scrape original websites using Firecrawl
3. Extract new facts using Ollama
4. Compare content hashes
5. Update graph if facts changed
6. Report results
```

### 3. **Idempotent Ingestion** 🚫
No duplicate data, ever:
```
First ingest: "Tesla founded in 2003"
  → Hash: abc123
  → Store in graph

Second ingest: "Tesla founded in 2003"
  → Hash: abc123 (SAME!)
  → Skip (no duplicate)
  → Just update last_verified

Third ingest: "Tesla founded in 2004"
  → Hash: xyz789 (DIFFERENT!)
  → Mark old fact as invalid
  → Store new fact
```

### 4. **Confidence Scoring** 📊
AI isn't always 100% sure:
```
Extracted Fact: "Elon Musk founded SpaceX"
Confidence: 0.95 (95% sure)

Extracted Fact: "SpaceX is a company"
Confidence: 0.99 (99% sure)

Extracted Fact: "SpaceX has 9000 employees"
Confidence: 0.70 (70% sure - might be outdated)
```

## 🛠️ Technologies Used

### Backend Stack
- **Python 3.11+**: Core language
- **FastAPI**: REST API framework
- **Neo4j**: Graph database for storing relationships
- **Ollama**: Local LLM inference (Llama 3.1)
- **LangChain**: LLM orchestration
- **Firecrawl**: Web scraping API
- **Pydantic v2**: Data validation
- **SQLAlchemy**: ORM for metadata

### Frontend Stack
- **Next.js 13+**: React framework
- **React**: UI library
- **Three.js**: 3D graphics
- **react-force-graph-3d**: 3D force-directed graph
- **TailwindCSS**: Styling
- **TypeScript**: Type safety

### Infrastructure
- **Docker & Docker Compose**: Containerization
- **Neo4j**: Graph database
- **PostgreSQL**: Metadata storage (optional)
- **Redis**: Caching & task queue (optional)

### Why These Technologies?

| Tech | Why |
|------|-----|
| **Neo4j** | Perfect for storing relationships; queries are 10-100x faster than SQL |
| **Firecrawl** | Handles JavaScript-rendered content; extracts clean text |
| **Ollama** | Runs AI locally; no data leaves your machine |
| **Three.js** | Beautiful 3D visualizations; GPU-accelerated |
| **FastAPI** | Fast, modern, auto-generates API docs |
| **Next.js** | Server-side rendering; great for SEO and performance |

---

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
