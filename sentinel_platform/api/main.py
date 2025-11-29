"""
FastAPI application for Sentinel Knowledge Graph API.
"""

from __future__ import annotations

import asyncio
import os
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

from sentinel_core import (
    GraphManager, 
    GraphException, 
    Sentinel, 
    GraphExtractor
)
from sentinel_core.scraper import get_scraper
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
    agent_status: str = "unknown"


# Global instances
graph_manager: Optional[GraphManager] = None
sentinel_agent: Optional[Sentinel] = None

# Global system status
system_status = {
    "state": "Idle",
    "message": "Waiting for tasks...",
    "last_update": datetime.utcnow().isoformat()
}


def get_graph_manager() -> GraphManager:
    """Get or create GraphManager instance."""
    global graph_manager
    if graph_manager is None:
        graph_manager = GraphManager()
    return graph_manager


def update_status(state: str, message: str):
    """Update the global system status."""
    global system_status
    system_status["state"] = state
    system_status["message"] = message
    system_status["last_update"] = datetime.utcnow().isoformat()
    logger.info("status_updated", state=state, message=message)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("api_starting_up")
    
    global graph_manager, sentinel_agent
    
    try:
        # Initialize graph manager
        graph_manager = get_graph_manager()
        
        # Initialize Sentinel Agent components
        # 1. Scraper (Auto-detects best available)
        scraper = get_scraper()
        logger.info(f"scraper_initialized", type=scraper.get_name())
        
        # 2. Extractor
        model_name = os.getenv("OLLAMA_MODEL", "ollama/llama3")
        extractor = GraphExtractor(model_name=model_name)
        
        # 3. Sentinel Orchestrator
        sentinel_agent = Sentinel(graph_manager, scraper, extractor)
        
        # Start healing loop in background
        asyncio.create_task(sentinel_agent.run_healing_loop(
            days_threshold=7,
            interval_hours=6
        ))
        
        logger.info("sentinel_agent_started")
        
    except Exception as e:
        logger.error("failed_to_start_sentinel_agent", error=str(e))

    logger.info("api_started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("api_shutting_down")
    
    global graph_manager, sentinel_agent
    
    if sentinel_agent:
        # sentinel_agent.stop() # If stop method exists
        pass
        
    if graph_manager:
        graph_manager.close()
        
    logger.info("api_shutdown_complete")


@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "agent_status": "running" if sentinel_agent else "stopped"
    }


@app.get("/api/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    try:
        manager = get_graph_manager()
        manager.verify_connectivity()
        
        # Check agent status
        agent_status = "running" if sentinel_agent else "stopped"
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "agent_status": agent_status
        }
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.get("/api/status")
async def get_status():
    """Get current system status."""
    return system_status


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
    """
    logger.info("graph_snapshot_requested", timestamp=timestamp)

    try:
        manager = get_graph_manager()

        # Parse timestamp if provided
        dt = None
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid timestamp format: {e}. Use ISO 8601 format.",
                )

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
    """Get statistics about the knowledge graph."""
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


@app.post("/api/ingest")
async def ingest_url(request: IngestRequest):
    """
    Ingest a URL into the knowledge graph using the Sentinel pipeline.
    """
    logger.info("ingest_requested", url=request.url)
    
    if not sentinel_agent:
        raise HTTPException(status_code=503, detail="Sentinel agent not initialized")
    
    try:
        update_status("Processing", f"Processing {request.url}...")
        
        # Use the Sentinel agent to process the URL
        result = await sentinel_agent.process_url(request.url)
        
        status = result.get("status")
        if status == "success":
            msg = f"Successfully processed {request.url}. Extracted {result.get('extracted_nodes', 0)} nodes."
            update_status("Idle", msg)
        elif status == "unchanged_verified":
            msg = f"Content unchanged for {request.url}. Verified existing data."
            update_status("Idle", msg)
        else:
            msg = f"Processed {request.url} with status: {status}"
            update_status("Idle", msg)
            
        return result

    except Exception as e:
        logger.error("ingest_failed", error=str(e))
        update_status("Error", f"Failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class QueryRequest(BaseModel):
    """Request model for natural language queries."""
    question: str
    timestamp: Optional[str] = None


@app.post("/api/query")
async def query_graph(request: QueryRequest):
    """
    Answer a natural language question about the knowledge graph.
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
