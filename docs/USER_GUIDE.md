# 📘 Sentinel User Guide

## Where can Sentinel be used?

Sentinel is designed to be a versatile component in your AI stack. You can use it in three main ways:

### 1. As a Python Library (`pip install sentinel-core`)
Integrate Sentinel directly into your Python applications (FastAPI, Django, Flask, or scripts).
- **Use case**: Building a custom RAG pipeline, a research assistant, or a data monitoring bot.
- **How**: Import `Sentinel`, `GraphManager`, and `GraphExtractor` to build custom workflows.

### 2. As a CLI Tool
Run Sentinel from your terminal to manage knowledge graphs without writing code.
- **Use case**: Quick scraping, monitoring a specific URL, or checking system status.
- **How**: Run `sentinel init`, `sentinel watch <url>`, `sentinel status`.

### 3. As a RAG Knowledge Source
Use the Neo4j graph created by Sentinel as a rich context source for your LLMs.
- **Use case**: Chatbots that need historical context or structured data (not just vector similarity).
- **How**: Connect your RAG chain (LangChain, LlamaIndex) to the Neo4j database populated by Sentinel.

---

## 🚀 How to Use Sentinel

### Prerequisite: Infrastructure
Sentinel requires:
1.  **Neo4j Database**: To store the knowledge graph.
2.  **LLM**: Ollama (local) or OpenAI/Anthropic (cloud) to extract knowledge.

### Method 1: The "No-Code" CLI Approach

Best for getting started quickly.

1.  **Install**:
    ```bash
    pip install sentinel-core
    ```

2.  **Initialize**:
    ```bash
    # Sets up your .env file and checks connections
    python -m sentinel_core.cli init
    ```

3.  **Watch a URL**:
    ```bash
    # Scrapes, extracts, and saves to Neo4j
    python -m sentinel_core.cli watch https://example.com
    ```

4.  **Auto-Heal**:
    ```bash
    # Checks for stale data and updates it
    python -m sentinel_core.cli heal
    ```

### Method 2: The Python API Approach

Best for building custom applications.

```python
import asyncio
from sentinel_core import Sentinel, GraphManager, GraphExtractor
from sentinel_core.scraper import get_scraper

async def main():
    # 1. Setup components
    graph = GraphManager()  # Connects to Neo4j
    scraper = get_scraper() # Uses Firecrawl or Local
    extractor = GraphExtractor(model_name="ollama/phi3") # Uses your LLM
    
    sentinel = Sentinel(graph, scraper, extractor)
    
    # 2. Process a website
    print("Processing...")
    result = await sentinel.process_url("https://docs.python.org/3/")
    
    print(f"Done! Extracted {result['extracted_nodes']} nodes.")
    
    # 3. Query the graph (Time Travel)
    # Get the state of the graph as it was yesterday
    # snapshot = graph.get_graph_snapshot(timestamp=yesterday)

if __name__ == "__main__":
    asyncio.run(main())
```

### Method 3: Integrating with LangChain (RAG)

Once Sentinel has populated your Neo4j database, you can query it using LangChain.

```python
from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_openai import ChatOpenAI

# 1. Connect to the same Neo4j instance Sentinel is using
graph = Neo4jGraph(
    url="bolt://localhost:7687", 
    username="neo4j", 
    password="password"
)

# 2. Create a QA chain
chain = GraphCypherQAChain.from_llm(
    ChatOpenAI(temperature=0), 
    graph=graph, 
    verbose=True
)

# 3. Ask questions based on Sentinel's data
response = chain.run("What entities are related to 'Python'?")
print(response)
```

## 📚 Further Reading

- [CLI Reference](CLI_REFERENCE.md) - All command line options.
- [Examples](EXAMPLES.md) - Real-world scenarios (Pricing monitor, News aggregator).
- [Quick Start](QUICKSTART.md) - Detailed installation steps.
