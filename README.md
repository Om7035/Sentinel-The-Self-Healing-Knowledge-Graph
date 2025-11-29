# 🛡️ Sentinel: Self-Healing Temporal Knowledge Graph

**Sentinel** is an autonomous knowledge graph that automatically scrapes, extracts, stores, and maintains structured knowledge from the web. It uses AI to understand content, tracks changes over time, and heals itself when information becomes stale.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🌟 Key Features

- **🤖 Autonomous**: Automatically scrapes, extracts, and updates knowledge
- **⏰ Temporal**: Track how knowledge evolves over time
- **🔧 Self-Healing**: Detects and updates stale information automatically
- **🧠 AI-Powered**: Uses LLMs to extract entities and relationships
- **📊 Graph-Based**: Stores knowledge in a Neo4j temporal graph
- **🌐 Web Scraping**: Intelligent scraping with Firecrawl or local fallback
- **💻 Developer-Friendly**: Simple Python API and CLI tool
- **🎨 Beautiful UI**: 3D graph visualization with Next.js

## 🚀 Quick Start

### Installation

```bash
pip install sentinel-core[all]
```

### Setup

```bash
# Interactive setup wizard
python sentinel_cli.py init

# Or manually create .env file
cat > .env << EOF
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
OLLAMA_MODEL=ollama/phi3
EOF
```

### Start Services

```bash
# Start Neo4j
docker run -d -p 7687:7687 -p 7474:7474 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest

# Start Ollama (for local LLM)
ollama serve
ollama pull phi3
```

### Your First Knowledge Graph

```bash
# Process a URL
python sentinel_cli.py watch https://stripe.com/pricing

# Check status
python sentinel_cli.py status

# View in UI
cd sentinel_platform/ui
npm install && npm run dev
# Visit http://localhost:3000
```

## 📚 Usage

### Python API

```python
import asyncio
from sentinel_core import Sentinel, GraphManager, GraphExtractor
from sentinel_core.scraper import get_scraper

async def main():
    # Initialize
    graph = GraphManager()
    scraper = get_scraper()
    extractor = GraphExtractor(model_name="ollama/phi3")
    sentinel = Sentinel(graph, scraper, extractor)
    
    # Process URL
    result = await sentinel.process_url("https://example.com")
    print(f"Extracted {result['extracted_nodes']} nodes!")
    
    # Query graph
    snapshot = graph.get_graph_snapshot()
    print(f"Total: {snapshot['metadata']['node_count']} nodes")
    
    graph.close()

asyncio.run(main())
```

### CLI Tool

```bash
# Show version
python sentinel_cli.py version

# Check system status
python sentinel_cli.py status

# Process a URL
python sentinel_cli.py watch https://example.com

# Run healing cycle
python sentinel_cli.py heal --days 7

# Interactive setup
python sentinel_cli.py init
```

## 🎯 Use Cases

### 1. **Product Pricing Monitoring**
Track pricing changes across competitors automatically.

```python
urls = [
    "https://stripe.com/pricing",
    "https://paypal.com/pricing",
    "https://square.com/pricing"
]

for url in urls:
    await sentinel.process_url(url)
```

### 2. **Documentation Tracking**
Monitor documentation changes for your favorite libraries.

```python
docs = {
    "React": "https://react.dev/learn",
    "Next.js": "https://nextjs.org/docs",
}

for name, url in docs.items():
    await sentinel.process_url(url)

# Auto-heal to detect changes
await sentinel.run_healing_cycle(days_threshold=7)
```

### 3. **News Aggregation**
Build a knowledge graph from multiple news sources.

```python
news_sources = [
    "https://techcrunch.com/",
    "https://theverge.com/",
]

for url in news_sources:
    await sentinel.process_url(url)
```

### 4. **Research Paper Tracking**
Track research papers and their citations.

```python
papers = [
    "https://arxiv.org/abs/2303.08774",  # GPT-4
    "https://arxiv.org/abs/2005.14165",  # GPT-3
]

for paper in papers:
    await sentinel.process_url(paper)
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Sentinel System                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐    ┌───────────┐    ┌──────────────┐    │
│  │ Scraper  │───▶│ Extractor │───▶│ Graph Store  │    │
│  │(Firecrawl│    │  (LLM +   │    │   (Neo4j)    │    │
│  │or Local) │    │Instructor)│    │   Temporal   │    │
│  └──────────┘    └───────────┘    └──────────────┘    │
│       │                                    │            │
│       │          ┌───────────┐            │            │
│       └─────────▶│ Sentinel  │◀───────────┘            │
│                  │Orchestrator│                         │
│                  └───────────┘                         │
│                       │                                 │
│                       ▼                                 │
│              ┌─────────────────┐                       │
│              │  Healing Loop   │                       │
│              │ (Auto-Updates)  │                       │
│              └─────────────────┘                       │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## 📖 Documentation

- [User Guide](docs/USER_GUIDE.md) - **Start Here!**
- [Quick Start Guide](docs/QUICKSTART.md)
- [CLI Reference](docs/CLI_REFERENCE.md)
- [Usage Examples](docs/EXAMPLES.md)

## 🛠️ Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/Om7035/Sentinel-The-Self-Healing-Knowledge-Graph
cd Sentinel-The-Self-Healing-Knowledge-Graph

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[all]"

# Run tests
pytest tests/
```

### Project Structure

```
sentinel/
├── sentinel_core/          # Core library (pip-installable)
│   ├── scraper/           # Web scraping (Firecrawl + Local)
│   ├── graph_store.py     # Neo4j temporal graph
│   ├── graph_extractor.py # LLM-based extraction
│   └── orchestrator.py    # Main Sentinel class
├── sentinel_platform/     # Demo platform
│   ├── api/              # FastAPI backend
│   └── ui/               # Next.js frontend
├── tests/                # Test suite
├── docs/                 # Documentation
└── sentinel_cli.py       # CLI tool
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangChain](https://langchain.com/), [Neo4j](https://neo4j.com/), and [FastAPI](https://fastapi.tiangolo.com/)
- Inspired by the need for self-maintaining knowledge systems
- Special thanks to the open-source community

## 📧 Contact

- **Author**: Om Kawale
- **Email**: speedtech602@gmail.com
- **GitHub**: [@Om7035](https://github.com/Om7035)
- **Project**: [Sentinel](https://github.com/Om7035/Sentinel-The-Self-Healing-Knowledge-Graph)

## ⭐ Star History

If you find Sentinel useful, please consider giving it a star! ⭐

---

**Made with ❤️ by Om Kawale**
