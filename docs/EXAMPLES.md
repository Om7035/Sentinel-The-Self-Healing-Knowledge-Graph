# 📚 Sentinel Usage Examples

Real-world examples showing how to use Sentinel in your projects.

## Table of Contents
1. [Basic Usage](#basic-usage)
2. [Monitoring Product Pricing](#monitoring-product-pricing)
3. [Documentation Tracking](#documentation-tracking)
4. [News Aggregation](#news-aggregation)
5. [Research Paper Monitoring](#research-paper-monitoring)
6. [Multi-Source Knowledge Synthesis](#multi-source-knowledge-synthesis)

---

## Basic Usage

### Example 1: Simple URL Processing

```python
import asyncio
from sentinel_core import Sentinel, GraphManager, GraphExtractor
from sentinel_core.scraper import get_scraper

async def main():
    # Initialize components
    graph = GraphManager()
    scraper = get_scraper()  # Auto-selects best available
    extractor = GraphExtractor(model_name="ollama/llama3")
    
    # Create Sentinel
    sentinel = Sentinel(graph, scraper, extractor)
    
    # Process a URL
    result = await sentinel.process_url("https://stripe.com/pricing")
    
    print(f"Status: {result['status']}")
    print(f"Extracted {result['extracted_nodes']} nodes")
    print(f"Extracted {result['extracted_edges']} relationships")
    
    # Clean up
    graph.close()

asyncio.run(main())
```

### Example 2: Querying the Knowledge Graph

```python
from sentinel_core import GraphManager

# Connect to graph
graph = GraphManager()

# Get current snapshot
snapshot = graph.get_graph_snapshot()

print(f"Total nodes: {snapshot['metadata']['node_count']}")
print(f"Total edges: {snapshot['metadata']['link_count']}")

# View nodes
for node in snapshot['nodes'][:5]:
    print(f"- {node['label']}: {node['properties'].get('name', 'N/A')}")

graph.close()
```

---

## Monitoring Product Pricing

Track pricing changes across competitors.

```python
import asyncio
from datetime import datetime, timedelta
from sentinel_core import Sentinel, GraphManager, GraphExtractor
from sentinel_core.scraper import get_scraper

async def monitor_pricing():
    """Monitor pricing pages and detect changes."""
    
    # Setup
    graph = GraphManager()
    scraper = get_scraper()
    extractor = GraphExtractor(model_name="ollama/llama3")
    sentinel = Sentinel(graph, scraper, extractor)
    
    # URLs to monitor
    pricing_urls = [
        "https://stripe.com/pricing",
        "https://www.paypal.com/pricing",
        "https://square.com/pricing",
    ]
    
    # Process each URL
    for url in pricing_urls:
        print(f"\nProcessing: {url}")
        result = await sentinel.process_url(url)
        
        if result["status"] == "success":
            print(f"✓ New data: {result['extracted_nodes']} entities")
        elif result["status"] == "unchanged_verified":
            print(f"✓ No changes detected")
        else:
            print(f"✗ Error: {result.get('error')}")
    
    # Query for pricing information
    snapshot = graph.get_graph_snapshot()
    
    # Find pricing-related nodes
    pricing_nodes = [
        node for node in snapshot['nodes']
        if 'price' in node['properties'].get('name', '').lower()
        or 'pricing' in node['properties'].get('name', '').lower()
    ]
    
    print(f"\n📊 Found {len(pricing_nodes)} pricing-related entities")
    for node in pricing_nodes[:10]:
        print(f"  - {node['properties'].get('name')}")
    
    graph.close()

asyncio.run(monitor_pricing())
```

---

## Documentation Tracking

Monitor documentation changes for your favorite libraries.

```python
import asyncio
from sentinel_core import Sentinel, GraphManager, GraphExtractor
from sentinel_core.scraper import get_scraper

async def track_documentation():
    """Track documentation changes over time."""
    
    graph = GraphManager()
    scraper = get_scraper()
    extractor = GraphExtractor(model_name="ollama/llama3")
    sentinel = Sentinel(graph, scraper, extractor)
    
    # Documentation pages to track
    docs = {
        "React": "https://react.dev/learn",
        "Next.js": "https://nextjs.org/docs",
        "FastAPI": "https://fastapi.tiangolo.com/",
    }
    
    for name, url in docs.items():
        print(f"\n📚 Processing {name} documentation...")
        result = await sentinel.process_url(url)
        
        if result["status"] == "success":
            print(f"✓ Extracted {result['extracted_nodes']} concepts")
    
    # Run healing to detect changes
    print("\n🔧 Running healing cycle...")
    healing_result = await sentinel.run_healing_cycle(days_threshold=7)
    
    print(f"✓ Checked {healing_result['stale_count']} pages")
    print(f"✓ Updated {healing_result['processed_count']} pages")
    
    graph.close()

asyncio.run(track_documentation())
```

---

## News Aggregation

Build a knowledge graph from news articles.

```python
import asyncio
from sentinel_core import Sentinel, GraphManager, GraphExtractor
from sentinel_core.scraper import get_scraper

async def aggregate_news():
    """Aggregate news from multiple sources."""
    
    graph = GraphManager()
    scraper = get_scraper()
    extractor = GraphExtractor(model_name="ollama/llama3")
    sentinel = Sentinel(graph, scraper, extractor)
    
    # News sources
    news_urls = [
        "https://techcrunch.com/",
        "https://www.theverge.com/",
        "https://arstechnica.com/",
    ]
    
    all_entities = []
    
    for url in news_urls:
        print(f"\n📰 Processing: {url}")
        result = await sentinel.process_url(url)
        
        if result["status"] == "success":
            all_entities.append({
                "url": url,
                "nodes": result['extracted_nodes'],
                "edges": result['extracted_edges']
            })
    
    # Analyze the knowledge graph
    snapshot = graph.get_graph_snapshot()
    
    print(f"\n📊 Knowledge Graph Summary:")
    print(f"  Total entities: {snapshot['metadata']['node_count']}")
    print(f"  Total relationships: {snapshot['metadata']['link_count']}")
    
    # Find most connected entities
    node_connections = {}
    for link in snapshot['links']:
        source = link['source']
        target = link['target']
        node_connections[source] = node_connections.get(source, 0) + 1
        node_connections[target] = node_connections.get(target, 0) + 1
    
    top_entities = sorted(node_connections.items(), key=lambda x: x[1], reverse=True)[:5]
    
    print(f"\n🔥 Most Connected Entities:")
    for node_id, connections in top_entities:
        # Find node details
        node = next((n for n in snapshot['nodes'] if n['id'] == node_id), None)
        if node:
            name = node['properties'].get('name', 'Unknown')
            print(f"  - {name}: {connections} connections")
    
    graph.close()

asyncio.run(aggregate_news())
```

---

## Research Paper Monitoring

Track research papers and their citations.

```python
import asyncio
from datetime import datetime
from sentinel_core import Sentinel, GraphManager, GraphExtractor
from sentinel_core.scraper import get_scraper

async def monitor_research():
    """Monitor research papers and build citation graph."""
    
    graph = GraphManager()
    scraper = get_scraper()
    extractor = GraphExtractor(model_name="ollama/llama3")
    sentinel = Sentinel(graph, scraper, extractor)
    
    # Research paper URLs (e.g., arXiv)
    papers = [
        "https://arxiv.org/abs/2303.08774",  # GPT-4 paper
        "https://arxiv.org/abs/2005.14165",  # GPT-3 paper
    ]
    
    for paper_url in papers:
        print(f"\n📄 Processing paper: {paper_url}")
        result = await sentinel.process_url(paper_url)
        
        if result["status"] == "success":
            print(f"✓ Extracted {result['extracted_nodes']} entities")
            print(f"✓ Found {result['extracted_edges']} relationships")
    
    # Query for authors and citations
    snapshot = graph.get_graph_snapshot()
    
    # Find author nodes
    authors = [
        node for node in snapshot['nodes']
        if node['label'].lower() in ['person', 'author', 'researcher']
    ]
    
    print(f"\n👥 Found {len(authors)} researchers")
    
    # Find citation relationships
    citations = [
        link for link in snapshot['links']
        if 'cite' in link['type'].lower()
    ]
    
    print(f"📚 Found {len(citations)} citations")
    
    graph.close()

asyncio.run(monitor_research())
```

---

## Multi-Source Knowledge Synthesis

Combine knowledge from multiple sources into a unified graph.

```python
import asyncio
from sentinel_core import Sentinel, GraphManager, GraphExtractor
from sentinel_core.scraper import get_scraper

async def synthesize_knowledge():
    """Synthesize knowledge from multiple sources about a topic."""
    
    graph = GraphManager()
    scraper = get_scraper()
    extractor = GraphExtractor(model_name="ollama/llama3")
    sentinel = Sentinel(graph, scraper, extractor)
    
    # Topic: "Artificial Intelligence"
    sources = {
        "Wikipedia": "https://en.wikipedia.org/wiki/Artificial_intelligence",
        "Stanford": "https://ai.stanford.edu/",
        "OpenAI": "https://openai.com/research",
    }
    
    print("🧠 Building knowledge graph about AI from multiple sources...\n")
    
    for source_name, url in sources.items():
        print(f"📥 Ingesting from {source_name}...")
        result = await sentinel.process_url(url)
        
        if result["status"] == "success":
            print(f"   ✓ Added {result['extracted_nodes']} entities")
        else:
            print(f"   ✗ Failed: {result.get('error')}")
    
    # Analyze the synthesized knowledge
    snapshot = graph.get_graph_snapshot()
    
    print(f"\n📊 Synthesized Knowledge Graph:")
    print(f"   Entities: {snapshot['metadata']['node_count']}")
    print(f"   Relationships: {snapshot['metadata']['link_count']}")
    print(f"   Sources: {len(sources)}")
    
    # Find entities mentioned across multiple sources
    entity_sources = {}
    for node in snapshot['nodes']:
        name = node['properties'].get('name', '')
        if name:
            entity_sources[name] = entity_sources.get(name, 0) + 1
    
    # Entities mentioned multiple times (likely important)
    important_entities = [
        (name, count) for name, count in entity_sources.items()
        if count > 1
    ]
    
    print(f"\n🔥 Key Entities (mentioned multiple times):")
    for name, count in sorted(important_entities, key=lambda x: x[1], reverse=True)[:10]:
        print(f"   - {name}: {count} sources")
    
    graph.close()

asyncio.run(synthesize_knowledge())
```

---

## Advanced: Custom Scraper

Create a custom scraper for specialized content.

```python
from sentinel_core.scraper.base import BaseScraper
from sentinel_core.models import ScrapeResult
import requests
from bs4 import BeautifulSoup

class CustomAPIScraper(BaseScraper):
    """Custom scraper for a specific API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def scrape(self, url: str) -> ScrapeResult:
        """Scrape content from custom API."""
        # Your custom scraping logic here
        response = requests.get(url, headers={"Authorization": f"Bearer {self.api_key}"})
        data = response.json()
        
        # Convert to markdown or text
        content = f"# {data['title']}\n\n{data['content']}"
        
        return ScrapeResult(
            url=url,
            content=content,
            title=data['title'],
            metadata={"api_version": data.get('version')}
        )
    
    def get_name(self) -> str:
        return "Custom API Scraper"

# Use custom scraper
async def use_custom_scraper():
    from sentinel_core import Sentinel, GraphManager, GraphExtractor
    
    graph = GraphManager()
    scraper = CustomAPIScraper(api_key="your-api-key")
    extractor = GraphExtractor(model_name="ollama/llama3")
    
    sentinel = Sentinel(graph, scraper, extractor)
    
    result = await sentinel.process_url("https://api.example.com/data")
    print(f"Processed: {result['extracted_nodes']} nodes")
    
    graph.close()

import asyncio
asyncio.run(use_custom_scraper())
```

---

## Tips & Best Practices

### 1. **Use Environment Variables**
```python
import os
from dotenv import load_dotenv

load_dotenv()

model = os.getenv("OLLAMA_MODEL", "ollama/llama3")
```

### 2. **Handle Errors Gracefully**
```python
try:
    result = await sentinel.process_url(url)
    if result["status"] == "error":
        print(f"Error: {result['error']}")
except Exception as e:
    print(f"Fatal error: {e}")
```

### 3. **Close Connections**
```python
try:
    # Your code here
    pass
finally:
    graph.close()
```

### 4. **Use Context Managers** (Future Feature)
```python
# Coming soon
async with Sentinel.create() as sentinel:
    result = await sentinel.process_url(url)
```

### 5. **Batch Processing**
```python
urls = ["url1", "url2", "url3"]

for url in urls:
    result = await sentinel.process_url(url)
    await asyncio.sleep(1)  # Be polite to servers
```

---

## Need Help?

- 📖 [Full Documentation](https://github.com/Om7035/Sentinel-The-Self-Healing-Knowledge-Graph/docs)
- 💬 [GitHub Issues](https://github.com/Om7035/Sentinel-The-Self-Healing-Knowledge-Graph/issues)
- 📧 Email: speedtech602@gmail.com

## Contributing

Have a cool use case? Share it with the community!
1. Fork the repository
2. Add your example to `examples/`
3. Submit a pull request

---

**Happy Knowledge Graphing! 🎉**
