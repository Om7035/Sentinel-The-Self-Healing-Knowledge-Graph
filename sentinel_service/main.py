"""
FastAPI application for Sentinel Knowledge Graph API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import structlog
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import from sentinel_core package
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sentinel_core import GraphManager, GraphException
from .query_engine import QueryEngine

logger = structlog.get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Sentinel Knowledge Graph API",
    description="API for temporal knowledge graph queries and visualization",
    version="1.0.0",
)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Response models
class GraphSnapshotResponse(BaseModel):
    """Response model for graph snapshot endpoint."""
    nodes: list[dict]
    links: list[dict]
    metadata: dict


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: str


# Initialize GraphManager (in production, use dependency injection)
graph_manager = None
sentinel_agent = None


def get_graph_manager() -> GraphManager:
    """Get or create GraphManager instance."""
    global graph_manager
    if graph_manager is None:
        graph_manager = GraphManager()
    return graph_manager


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("api_starting_up")
    
    # Initialize graph manager
    manager = get_graph_manager()
    
    # Initialize Sentinel Agent (Phase 4)
    try:
        from sentinel_core import SentinelScraper, GraphExtractor, Sentinel
        import asyncio
        import os
        
        global sentinel_agent
        
        # Get API keys from environment
        firecrawl_key = os.getenv("FIRECRAWL_API_KEY", "fc_test_key")
        
        scraper = SentinelScraper(api_key=firecrawl_key)
        extractor = GraphExtractor(model_name="ollama/llama3")
        
        sentinel_agent = Sentinel(manager, scraper, extractor)
        
        # Start healing loop in background
        asyncio.create_task(sentinel_agent.run_healing_loop(
            days_threshold=7,
            interval_hours=6
        ))
        
        logger.info("sentinel_agent_started")
        
    except Exception as e:
        logger.error("failed_to_start_sentinel_agent", error=str(e))

    logger.info("api_started")


# ---------------------------------------------------------
# Phase 3: New Endpoints
# ---------------------------------------------------------

class JobRequest(BaseModel):
    url: str

class JobResponse(BaseModel):
    task_id: str
    status: str

@app.post("/job", response_model=JobResponse, status_code=202)
async def submit_job(job: JobRequest):
    """
    Submit a URL for processing (Async).
    
    Enqueues a Celery task to scrape, diff, and extract knowledge.
    """
    from .celery_app import process_url_task
    
    task = process_url_task.delay(job.url)
    logger.info("job_submitted", url=job.url, task_id=task.id)
    
    return {
        "task_id": task.id,
        "status": "submitted"
    }

@app.get("/graph/history", response_model=GraphSnapshotResponse)
async def get_graph_history(timestamp: datetime = Query(..., description="ISO timestamp for time-travel query")):
    """
    Get the graph state at a specific point in time.
    
    Returns edges that were valid at the given timestamp.
    """
    manager = get_graph_manager()
    
    try:
        snapshot = manager.get_graph_snapshot(timestamp)
        return snapshot
    except Exception as e:
        logger.error("history_query_failed", timestamp=timestamp, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("api_shutting_down")
    
    global graph_manager, sentinel_agent
    
    if sentinel_agent:
        sentinel_agent.stop()
        
    if graph_manager:
        graph_manager.close()
        
    logger.info("api_shutdown_complete")


@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    try:
        manager = get_graph_manager()
        manager.verify_connectivity()
        
        # Check agent status
        agent_status = "running" if sentinel_agent and sentinel_agent.is_running else "stopped"
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "agent_status": agent_status
        }
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.get("/api/graph-snapshot", response_model=GraphSnapshotResponse)
async def get_graph_snapshot(
    timestamp: Optional[str] = Query(
        None,
        description="ISO 8601 timestamp for time-travel query (defaults to now)",
        example="2024-01-15T12:00:00Z",
    )
):
    """
    Get a snapshot of the knowledge graph at a specific point in time.

    This endpoint implements time-travel queries, allowing you to see
    what the knowledge graph looked like at any point in the past.

    Args:
        timestamp: ISO 8601 timestamp (optional, defaults to now)

    Returns:
        Graph snapshot with nodes and links in react-force-graph-3d format

    Example:
        GET /api/graph-snapshot
        GET /api/graph-snapshot?timestamp=2024-01-15T12:00:00Z
    """
    logger.info("graph_snapshot_requested", timestamp=timestamp)

    try:
        manager = get_graph_manager()

        # Parse timestamp if provided
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid timestamp format: {e}. Use ISO 8601 format.",
                )
        else:
            dt = None  # Will default to now

        # Get snapshot
        snapshot = manager.get_graph_snapshot(timestamp=dt)

        logger.info(
            "graph_snapshot_returned",
            num_nodes=len(snapshot["nodes"]),
            num_links=len(snapshot["links"]),
        )

        return snapshot

    except HTTPException:
        raise
    except GraphException as e:
        logger.error("graph_snapshot_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error("unexpected_error", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/stats")
async def get_stats():
    """
    Get statistics about the knowledge graph.

    Returns:
        Statistics including node count, edge count, etc.
    """
    try:
        manager = get_graph_manager()

        # Get current snapshot for stats
        snapshot = manager.get_graph_snapshot()

        # Get stale URLs count
        stale_urls = manager.find_stale_nodes(days_threshold=7)

        return {
            "total_nodes": snapshot["metadata"]["node_count"],
            "total_edges": snapshot["metadata"]["link_count"],
            "stale_urls_count": len(stale_urls),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error("stats_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


class IngestRequest(BaseModel):
    url: str


class QueryRequest(BaseModel):
    """Request model for natural language queries."""
    question: str
    timestamp: Optional[str] = None


# Global system status
system_status = {
    "state": "Idle",
    "message": "Waiting for tasks...",
    "last_update": datetime.utcnow().isoformat()
}

def update_status(state: str, message: str):
    """Update the global system status."""
    global system_status
    system_status["state"] = state
    system_status["message"] = message
    system_status["last_update"] = datetime.utcnow().isoformat()
    logger.info("status_updated", state=state, message=message)

@app.get("/api/status")
async def get_status():
    """Get current system status."""
    return system_status

@app.post("/api/query")
async def query_graph(request: QueryRequest):
    """
    Answer a natural language question about the knowledge graph.
    
    Phase 5: Explainable Retrieval
    Returns the answer and the path the AI traversed.
    
    Example questions:
    - "How much does Stripe cost?"
    - "Who is the CEO of SpaceX?"
    - "What changed recently?"
    """
    logger.info("query_received", question=request.question)
    
    try:
        manager = get_graph_manager()
        query_engine = QueryEngine(manager)
        
        result = query_engine.execute_query_with_path(
            question=request.question,
            timestamp=request.timestamp
        )
        
        logger.info(
            "query_completed",
            question=request.question,
            path_length=len(result.get("path", []))
        )
        
        return result
        
    except Exception as e:
        logger.error("query_failed", question=request.question, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ingest")
async def ingest_url(request: IngestRequest):
    """
    Manually ingest a URL into the knowledge graph.
    """
    logger.info("ingest_requested", url=request.url)
    
    try:
        update_status("Scraping", f"Reading content from {request.url}...")
        
        # Import here to avoid circular imports
        from sentinel_core import SentinelScraper, InfoExtractor
        import os
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="FIRECRAWL_API_KEY not found in environment variables")
        
        # 1. Scrape
        scraper = SentinelScraper(api_key=api_key)
        scraped_data = await scraper.scrape_url(request.url)
        
        if not scraped_data or not scraped_data.get("markdown"):
            raise HTTPException(status_code=400, detail="Failed to scrape content")
            
        # 2. Extract
        update_status("Extracting", "Using AI to find facts and relationships...")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1")
        extractor = InfoExtractor(model=ollama_model)
        
        from fastapi.concurrency import run_in_threadpool
        triples = await run_in_threadpool(extractor.extract_triples, scraped_data["markdown"])
        
        # 3. Update Graph
        update_status("Updating Graph", f"Saving {len(triples)} new facts to Neo4j...")
        manager = get_graph_manager()
        count = 0
        for triple in triples:
            manager.upsert_temporal_edge(
                source_node=triple.head,
                relation_type=triple.relation,
                target_node=triple.tail,
                source_url=request.url,
                confidence=triple.confidence
            )
            count += 1
            
        update_status("Idle", f"Successfully processed {request.url}")
        
        return {
            "status": "success", 
            "message": f"Extracted {count} facts from {request.url}",
            "triples_count": count
        }

    except Exception as e:
        logger.error("ingest_failed", error=str(e))
        update_status("Error", f"Failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
