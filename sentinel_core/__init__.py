"""
Sentinel Core - Self-Healing Knowledge Graph Library

This is the pip-installable library that provides core Sentinel functionality:
- Graph storage with temporal validity tracking (Neo4j)
- LLM-based entity and relationship extraction (LiteLLM + Instructor)
- Web scraping with Firecrawl or local fallback
- Autonomous healing orchestration

Usage:
    from sentinel_core import Sentinel, GraphManager, GraphExtractor
    from sentinel_core.scraper import get_scraper
    
    # Initialize components
    graph = GraphManager()
    scraper = get_scraper()  # Auto-selects best available scraper
    extractor = GraphExtractor(model_name="ollama/llama3")
    
    # Create Sentinel orchestrator
    sentinel = Sentinel(graph, scraper, extractor)
    
    # Run autonomous healing
    await sentinel.run_healing_cycle()
"""

from .extractor import InfoExtractor, ExtractionException
from .graph_extractor import GraphExtractor
from .graph_store import Neo4jStore, GraphManager, GraphException
from .models import (
    GraphNode,
    TemporalEdge,
    GraphTriple,
    GraphData,
    ScrapedContent,
    HealingResult,
    ScrapeResult,
)
from .orchestrator import Sentinel

# Note: Scraper module is imported separately to avoid circular imports
# Use: from sentinel_core.scraper import get_scraper, LocalScraper, FirecrawlScraper

__version__ = "0.1.6"

__all__ = [
    # Main orchestrator
    "Sentinel",
    
    # Core components
    "Neo4jStore",
    "GraphManager",  # Backward compatibility alias
    "InfoExtractor",
    "GraphExtractor",  # LiteLLM + Instructor extractor
    
    # Models
    "GraphNode",
    "TemporalEdge",
    "GraphTriple",
    "GraphData",  # Container for nodes and edges
    "ScrapedContent",
    "HealingResult",
    "ScrapeResult",  # New: Standardized scraper output
    
    # Exceptions
    "GraphException",
    "ExtractionException",
    
    # Version
    "__version__",
]
