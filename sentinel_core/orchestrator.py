"""
Sentinel Orchestrator - Main Entry Point

This module defines the Sentinel class, which orchestrates the entire knowledge graph lifecycle:
1. Ingestion (Scraping + Diffing)
2. Extraction (LLM)
3. Storage (Temporal Graph)
4. Healing (Autonomous Maintenance)
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, List, Optional

import structlog
from fastapi.concurrency import run_in_threadpool

from .graph_extractor import GraphExtractor
from .graph_store import GraphManager
from .scraper.base import BaseScraper

logger = structlog.get_logger(__name__)


class Sentinel:
    """
    Main orchestrator for the Sentinel system.
    
    Handles the pipeline:
    URL -> Scrape -> Diff -> Extract -> Upsert -> Update State
    """
    
    def __init__(
        self,
        graph_manager: GraphManager,
        scraper: BaseScraper,
        extractor: GraphExtractor,
        config: Optional[dict] = None,
    ) -> None:
        """
        Initialize the Sentinel orchestrator.
        
        Args:
            graph_manager: Initialized GraphManager
            scraper: Initialized scraper (any BaseScraper implementation)
            extractor: Initialized GraphExtractor
            config: Optional configuration dictionary
        """
        self.graph = graph_manager
        self.scraper = scraper
        self.extractor = extractor
        self.config = config or {}
        self.is_running = False
        
        logger.info("sentinel_orchestrator_initialized")

    async def process_url(self, url: str) -> dict[str, Any]:
        """
        Process a single URL through the Sentinel pipeline.
        
        Pipeline:
        1. Check current state (hash) in DB
        2. Scrape URL to get new content and hash
        3. Diff: If hash matches, skip (Optimization)
        4. Extract: If changed, extract knowledge using LLM
        5. Upsert: Store extracted knowledge in Graph
        6. Update State: Save new hash to Document node
        
        Args:
            url: The URL to process
            
        Returns:
            Dictionary with processing results
        """
        logger.info("processing_url", url=url)
        
        try:
            # 1. Check current state
            current_hash = self.graph.get_document_state(url)
            logger.debug("current_document_state", url=url, hash=current_hash)
            
            # 2. Scrape and hash (using new scraper interface)
            scrape_result = await self.scraper.scrape(url)
            markdown = scrape_result.content
            new_hash = scrape_result.content_hash
            
            # 3. Diff Logic
            if current_hash == new_hash:
                logger.info("content_unchanged_updating_verification", url=url)
                
                # Update verification timestamps even if content hasn't changed
                # This prevents the node from remaining "stale"
                edges_updated = self.graph.mark_edges_verified(url)
                self.graph.update_document_state(url, new_hash)
                
                return {
                    "status": "unchanged_verified",
                    "reason": "content_unchanged",
                    "url": url,
                    "hash": new_hash,
                    "edges_updated": edges_updated
                }
            
            logger.info(
                "content_changed_processing",
                url=url,
                old_hash=current_hash,
                new_hash=new_hash
            )
            
            # 4. Extract Knowledge
            # Run in threadpool to avoid blocking event loop
            graph_data = await run_in_threadpool(
                self.extractor.extract,
                markdown
            )
            
            if not graph_data.nodes and not graph_data.edges:
                logger.warning("no_knowledge_extracted", url=url)
                return {
                    "status": "warning",
                    "reason": "no_knowledge_extracted",
                    "url": url
                }
            
            # 5. Upsert to Graph
            stats = self.graph.upsert_data(graph_data, source_url=url)
            
            # 6. Update Document State
            self.graph.update_document_state(url, new_hash)
            
            return {
                "status": "success",
                "url": url,
                "hash": new_hash,
                "stats": stats,
                "extracted_nodes": len(graph_data.nodes),
                "extracted_edges": len(graph_data.edges)
            }
            
        except Exception as e:
            logger.error("failed_to_process_url", url=url, error=str(e), exc_info=True)
            return {
                "status": "error",
                "url": url,
                "error": str(e)
            }


    async def run_healing_cycle(self, days_threshold: int = 7) -> dict:
        """
        Run a single autonomous healing cycle.
        
        Finds stale nodes and re-processes them.
        """
        logger.info("starting_healing_cycle", days_threshold=days_threshold)
        start_time = datetime.utcnow()
        
        # Find stale nodes
        stale_urls = self.graph.find_stale_nodes(days_threshold)
        
        if not stale_urls:
            logger.info("no_stale_nodes_found")
            return {
                "status": "completed",
                "stale_count": 0,
                "processed_count": 0,
                "duration_seconds": 0
            }
        
        # Process each stale URL
        results = []
        for url in stale_urls:
            result = await self.process_url(url)
            results.append(result)
            
            # Small delay to be polite
            await asyncio.sleep(1)
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            "status": "completed",
            "stale_count": len(stale_urls),
            "processed_count": len(results),
            "duration_seconds": duration,
            "results": results
        }

    async def run_healing_loop(self, days_threshold: int = 7, interval_hours: int = 6):
        """Run the autonomous healing loop indefinitely."""
        logger.info("starting_healing_loop")
        self.is_running = True
        
        while self.is_running:
            try:
                await self.run_healing_cycle(days_threshold)
                logger.info("sleeping_until_next_cycle", hours=interval_hours)
                await asyncio.sleep(interval_hours * 3600)
            except Exception as e:
                logger.error("healing_loop_error", error=str(e))
                await asyncio.sleep(3600)

    def stop(self):
        """Stop the healing loop."""
        self.is_running = False
