# 🛡️ Sentinel: Self-Healing Temporal Knowledge Graph

**Sentinel** is an autonomous knowledge graph that automatically scrapes, extracts, stores, and maintains structured knowledge from the web. It uses AI to understand content, tracks changes over time, and heals itself when information becomes stale.

[![PyPI version](https://badge.fury.io/py/sentinel-core.svg)](https://badge.fury.io/py/sentinel-core)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> [!IMPORTANT]
> **🚧 Python Package New Release In Progress**
> 
> Please note that a **new release of the Python package is currently in progress**, and it may take some time to complete.
> 
> Sentinel is a **library in progress**. We are working hard to improve stability, add new features, and refine it. 
> While the core functionality is ready for testing, expect breaking changes and rapid updates. 
> 
> **We are building it and making it better every day!** 🚀


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
pip install sentinel-core
```

### Setup

```bash
# Interactive setup wizard
sentinel init

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
sentinel watch https://stripe.com/pricing

# Check status
sentinel status

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
sentinel version

# Check system status
sentinel status

# Process a URL
sentinel watch https://example.com

# Run healing cycle
sentinel heal --days 7

# Interactive setup
sentinel init
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

<img width="1078" height="461" alt="image" src="https://github.com/user-attachments/assets/0b321486-555d-433c-9b37-c9a99930533b" />

## 📖 Documentation

- [User Guide](docs/USER_GUIDE.md) - **Start Here!**
- [Quick Start Guide](docs/QUICKSTART.md)
- [CLI Reference](docs/CLI_REFERENCE.md)
- [Usage Examples](docs/EXAMPLES.md)

## ⚠️ Limitations & Best Practices

### 1. Reliability & Hallucinations
LLMs can occasionally "hallucinate" relationships or misinterpret complex DOM structures. Sentinel mitigates this by:
- **Using Firecrawl**: Converts complex JS/HTML into clean Markdown, reducing noise.
- **Structured Extraction**: Uses `instructor` to enforce strict Pydantic schemas for nodes and edges.
- **Verification**: The `heal` command re-verifies content hashes before any costly LLM extraction.

### 2. Self-Healing Mechanism
Sentinel uses a **Hash-based Change Detection** strategy:
1.  **Monitor**: Checks for nodes that haven't been verified in `days_threshold` (default: 7).
2.  **Scrape & Hash**: Re-scrapes the URL and computes a SHA-256 hash of the *content*.
3.  **Diff**: Compares the new hash with the stored hash in Neo4j.
    - **Match**: Updates the `last_verified` timestamp (Zero LLM cost).
    - **Mismatch**: Triggers a full LLM extraction and graph update.

### 3. Cost & Scale
- **LLM Costs**: Frequent updates on large sites can be expensive. Use the `days_threshold` in `sentinel heal` to control frequency.
- **Storage**: The temporal graph grows over time. Currently, Sentinel does *not* auto-prune old versions. We recommend periodically archiving old `VALID_TO` relationships if storage is a concern.

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
