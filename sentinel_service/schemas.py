"""
API Request/Response Schemas for Sentinel Service

Pydantic models for API endpoints.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    """Request to ingest a new URL into the knowledge graph."""
    url: str = Field(..., description="URL to scrape and ingest")


class QueryRequest(BaseModel):
    """Request to query the knowledge graph with natural language."""
    question: str = Field(..., description="Natural language question")
    timestamp: Optional[str] = Field(None, description="ISO 8601 timestamp for time-travel queries")


class GraphSnapshotResponse(BaseModel):
    """Response containing a graph snapshot."""
    nodes: List[Dict[str, Any]] = Field(..., description="List of nodes in the graph")
    links: List[Dict[str, Any]] = Field(..., description="List of edges/links in the graph")
    metadata: Dict[str, Any] = Field(..., description="Metadata about the snapshot")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Current timestamp")
    agent_status: Optional[str] = Field(None, description="Sentinel agent status")


class StatsResponse(BaseModel):
    """Statistics about the knowledge graph."""
    total_nodes: int = Field(..., description="Total number of nodes")
    total_edges: int = Field(..., description="Total number of edges")
    stale_urls_count: int = Field(..., description="Number of stale URLs")
    timestamp: str = Field(..., description="Current timestamp")


class QueryResponse(BaseModel):
    """Response to a natural language query."""
    answer: str = Field(..., description="Natural language answer")
    path: List[Dict[str, Any]] = Field(..., description="Query path taken through the graph")
    confidence: Optional[float] = Field(None, description="Confidence in the answer")


class IngestResponse(BaseModel):
    """Response to an ingest request."""
    status: str = Field(..., description="Status of the ingest operation")
    message: str = Field(..., description="Human-readable message")
    triples_count: int = Field(..., description="Number of triples extracted")
    

class StatusResponse(BaseModel):
    """System status response."""
    state: str = Field(..., description="Current system state")
    message: str = Field(..., description="Status message")
    last_update: str = Field(..., description="Last update timestamp")
