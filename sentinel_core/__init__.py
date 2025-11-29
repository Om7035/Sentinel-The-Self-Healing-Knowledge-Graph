"""
Sentinel Core - Self-Healing Knowledge Graph Library

This is the pip-installable library that provides core Sentinel functionality:
- Graph storage with temporal validity tracking (Neo4j)
- LLM-based entity and relationship extraction (LiteLLM + Instructor)
- Web scraping with Firecrawl
- Autonomous healing orchestration

Usage:
    from sentinel_core import Sentinel, GraphManager, GraphExtractor, SentinelScraper
    
    # Initialize components
    graph = GraphManager()
    scraper = SentinelScraper(api_key="your_key")
    extractor = GraphExtractor(model_name="ollama/llama3")
    
    # Create Sentinel orchestrator
    sentinel = Sentinel(graph, scraper, extractor)
    
    # Run autonomous healing
    await sentinel.run_healing_cycle()
"""

from .extractor import InfoExtractor, ExtractionException
from .graph_extractor import GraphExtractor
from .graph_store import GraphManager, GraphException
from .models import (
    GraphNode,
    TemporalEdge,
    GraphTriple,
    GraphData,
    ScrapedContent,
    HealingResult,
)
from .orchestrator import Sentinel
from .scraper import SentinelScraper, ScraperException

__version__ = "0.1.0"

__all__ = [
    # Main orchestrator
    "Sentinel",
    
    # Core components
    "GraphManager",
    "InfoExtractor",
    "GraphExtractor",  # New: LiteLLM + Instructor extractor
    "SentinelScraper",
    
    # Models
    "GraphNode",
    "TemporalEdge",
    "GraphTriple",
    "GraphData",  # New: Container for nodes and edges
    "ScrapedContent",
    "HealingResult",
    
    # Exceptions
    "GraphException",
    "ExtractionException",
    "ScraperException",
    
    # Version
    "__version__",
]
