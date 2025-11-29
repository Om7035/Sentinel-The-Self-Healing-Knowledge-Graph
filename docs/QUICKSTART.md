# 🚀 Sentinel Quick Start Guide

Get up and running with Sentinel in less than 5 minutes!

## What is Sentinel?

Sentinel is a **Self-Healing Temporal Knowledge Graph** that automatically:
- 📥 Scrapes and monitors web content
- 🧠 Extracts knowledge using AI
- 📊 Stores it in a temporal graph database
- 🔧 Automatically updates when content changes
- ⏰ Tracks how knowledge evolves over time

## Prerequisites

Before you begin, make sure you have:

- **Python 3.11+** installed
- **Docker** installed and running (for Neo4j)
- **Ollama** installed (for local LLM) OR an OpenAI API key

## Installation

### Step 1: Install Sentinel

```bash
pip install sentinel-core[all]
```

Or for development:

```bash
git clone https://github.com/Om7035/Sentinel-The-Self-Healing-Knowledge-Graph
cd Sentinel-The-Self-Healing-Knowledge-Graph
pip install -e ".[all]"
```

### Step 2: Start Neo4j

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

Wait ~30 seconds for Neo4j to start, then verify at http://localhost:7474

### Step 3: Start Ollama (Optional - for local LLM)

If you want to use a local LLM instead of OpenAI:

```bash
# Install Ollama from https://ollama.ai
ollama pull llama3
ollama serve
```

### Step 4: Run Setup Wizard

```bash
sentinel init
```

This interactive wizard will:
- ✅ Check your Docker installation
- ✅ Collect your API keys
- ✅ Generate a `.env` file
- ✅ Verify all connections

Follow the prompts and you're done!

## Your First Knowledge Graph

### 1. Process a URL

```bash
sentinel watch https://stripe.com/pricing
```

This will:
1. Scrape the Stripe pricing page
2. Extract entities and relationships using AI
3. Store them in your Neo4j graph

### 2. Ask Questions

```bash
sentinel ask "How much does Stripe cost?"
```

Sentinel will query the knowledge graph and give you an answer based on what it learned.

### 3. Check Status

```bash
sentinel status
```

See your graph statistics, database connection, and scraper status.

## Using Sentinel in Your Code

```python
import asyncio
from sentinel_core import Sentinel, GraphManager, GraphExtractor
from sentinel_core.scraper import get_scraper

async def main():
    # Initialize components
    graph = GraphManager()
    scraper = get_scraper()  # Auto-detects best available scraper
    extractor = GraphExtractor(model_name="ollama/llama3")
    
    # Create Sentinel instance
    sentinel = Sentinel(graph, scraper, extractor)
    
    # Process a URL
    result = await sentinel.process_url("https://example.com")
    print(f"Extracted {result['extracted_nodes']} nodes!")
    
    # Query the graph
    snapshot = graph.get_graph_snapshot()
    print(f"Total nodes: {snapshot['metadata']['node_count']}")
    
    # Clean up
    graph.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Next Steps

### Explore the CLI

```bash
# Get help
sentinel --help

# Run a healing cycle (update stale knowledge)
sentinel heal --days 7

# See what would be healed without doing it
sentinel heal --dry-run
```

### Explore the Web UI

Start the API server:

```bash
cd sentinel_platform/api
uvicorn main:app --reload
```

Start the frontend:

```bash
cd sentinel_platform/ui
npm install
npm run dev
```

Visit http://localhost:3000 to see your knowledge graph in 3D!

### Advanced Configuration

Edit your `.env` file to customize:

```bash
# Use OpenAI instead of Ollama
OLLAMA_MODEL=gpt-4
OPENAI_API_KEY=sk-...

# Use Firecrawl for premium scraping
FIRECRAWL_API_KEY=fc-...

# Customize Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
```

## Troubleshooting

### "Could not connect to Neo4j"

Make sure Docker is running and Neo4j is started:

```bash
docker ps  # Should show neo4j container
docker logs neo4j  # Check for errors
```

### "Ollama connection failed"

Make sure Ollama is running:

```bash
ollama serve
# In another terminal:
ollama list  # Should show your models
```

### "No scraper available"

The local scraper should always work. If you see this error:

```bash
pip install beautifulsoup4 markdownify requests
```

## Getting Help

- 📖 [Full Documentation](https://github.com/Om7035/Sentinel-The-Self-Healing-Knowledge-Graph/docs)
- 💬 [GitHub Issues](https://github.com/Om7035/Sentinel-The-Self-Healing-Knowledge-Graph/issues)
- 📧 Email: speedtech602@gmail.com

## What's Next?

- ⏰ **Time Travel**: Query your graph at any point in the past
- 🔧 **Self-Healing**: Automatic updates when content changes
- 🌐 **Multi-Source**: Combine knowledge from multiple websites
- 🤖 **RAG Pipelines**: Use Sentinel as a knowledge base for your AI apps

Happy graphing! 🎉
