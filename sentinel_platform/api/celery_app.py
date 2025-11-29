"""
Celery Application for Sentinel Service.

Handles asynchronous background tasks for knowledge graph processing.
"""

import os
import sys
from pathlib import Path

from celery import Celery
import structlog

# Add parent directory to path to import sentinel_core
sys.path.insert(0, str(Path(__file__).parent.parent))

from sentinel_core import Sentinel, GraphManager, SentinelScraper, GraphExtractor

logger = structlog.get_logger(__name__)

# Configure Celery
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("sentinel_worker", broker=redis_url, backend=redis_url)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Global Sentinel instance for worker
sentinel_instance = None

def get_sentinel():
    """Get or create global Sentinel instance for worker."""
    global sentinel_instance
    if sentinel_instance is None:
        firecrawl_key = os.getenv("FIRECRAWL_API_KEY", "fc_test_key")
        
        graph = GraphManager()
        scraper = SentinelScraper(api_key=firecrawl_key)
        extractor = GraphExtractor(model_name="ollama/llama3")
        
        sentinel_instance = Sentinel(graph, scraper, extractor)
    return sentinel_instance

@celery_app.task(bind=True)
def process_url_task(self, url: str):
    """
    Background task to process a URL.
    
    Args:
        url: URL to process
    """
    import asyncio
    
    logger.info("received_process_url_task", url=url, task_id=self.request.id)
    
    try:
        sentinel = get_sentinel()
        
        # Run async method in sync Celery task
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        result = loop.run_until_complete(sentinel.process_url(url))
        
        logger.info("process_url_task_completed", url=url, status=result.get("status"))
        return result
        
    except Exception as e:
        logger.error("process_url_task_failed", url=url, error=str(e))
        raise
