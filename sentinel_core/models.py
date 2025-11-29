"""
Pydantic v2 Models for Sentinel Knowledge Graph.

This module defines the core data models used throughout the Sentinel system.
Model-agnostic design for use with LiteLLM + Instructor.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class GraphNode(BaseModel):
    """Represents an entity node in the knowledge graph."""
    
    id: str = Field(..., description="Unique identifier for the node")
    label: str = Field(..., description="Node label/type (e.g., 'Person', 'Company')")
    properties: dict = Field(default_factory=dict, description="Node properties as key-value pairs")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "id": "tesla_inc",
                "label": "Company",
                "properties": {"name": "Tesla", "industry": "Automotive", "founded": "2003"}
            }
        }


class TemporalEdge(BaseModel):
    """Represents a temporal relationship edge in the knowledge graph."""
    
    source: str = Field(..., description="Source entity ID")
    target: str = Field(..., description="Target entity ID")
    relation: str = Field(..., description="Relationship type (e.g., 'FOUNDED_BY')")
    properties: dict = Field(default_factory=dict, description="Edge properties including temporal info")
    
    # Temporal validity fields
    valid_from: datetime = Field(..., description="When this relationship became valid")
    valid_to: Optional[datetime] = Field(None, description="When this relationship became invalid (NULL = still valid)")
    
    def compute_hash(self) -> str:
        """
        Compute SHA-256 hash of edge content for change detection.
        
        Hash is based on: source + target + relation + properties
        This allows detecting when an edge's content has changed.
        
        Returns:
            SHA-256 hash as hexadecimal string
        """
        # Create a stable string representation
        hash_content = {
            "source": self.source,
            "target": self.target,
            "relation": self.relation,
            "properties": self.properties,
        }
        # Sort keys for consistent hashing
        content_str = json.dumps(hash_content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "source": "tesla_inc",
                "target": "elon_musk",
                "relation": "FOUNDED_BY",
                "properties": {"year": "2003", "role": "Co-founder"},
                "valid_from": "2024-01-15T10:00:00Z",
                "valid_to": None
            }
        }


class GraphData(BaseModel):
    """Container for lists of nodes and edges extracted from text."""
    
    nodes: list[GraphNode] = Field(default_factory=list, description="List of graph nodes")
    edges: list[TemporalEdge] = Field(default_factory=list, description="List of graph edges")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "nodes": [
                    {"id": "tesla_inc", "label": "Company", "properties": {"name": "Tesla"}},
                    {"id": "elon_musk", "label": "Person", "properties": {"name": "Elon Musk"}}
                ],
                "edges": [
                    {
                        "source": "tesla_inc",
                        "target": "elon_musk",
                        "relation": "FOUNDED_BY",
                        "properties": {"year": "2003"},
                        "valid_from": "2024-01-15T10:00:00Z",
                        "valid_to": None
                    }
                ]
            }
        }


class GraphTriple(BaseModel):
    """Represents a single knowledge graph triple (entity-relationship-entity).
    
    This is the fundamental unit of knowledge extracted from text.
    Used for simple extraction before converting to GraphData format.
    """
    
    head: str = Field(
        ...,
        description="Source entity (subject of the relationship)",
        min_length=1,
    )
    relation: str = Field(
        ...,
        description="Relationship type (predicate)",
        min_length=1,
    )
    tail: str = Field(
        ...,
        description="Target entity (object of the relationship)",
        min_length=1,
    )
    confidence: float = Field(
        default=0.8,
        description="Confidence score for this extraction (0-1)",
        ge=0.0,
        le=1.0,
    )
    properties: dict = Field(
        default_factory=dict,
        description="Additional properties (e.g., temporal info, evidence)"
    )

    @field_validator("head", "relation", "tail")
    @classmethod
    def not_empty(cls, v: str) -> str:
        """Ensure fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @field_validator("relation")
    @classmethod
    def normalize_relation(cls, v: str) -> str:
        """Normalize relation to uppercase with underscores."""
        return v.upper().replace(" ", "_")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "head": "John Doe",
                "relation": "WORKS_AT",
                "tail": "Acme Corp",
                "confidence": 0.95,
                "properties": {"since": "2020", "role": "CEO"}
            }
        }


class ScrapedContent(BaseModel):
    """Represents scraped web content."""
    
    url: str = Field(..., description="Source URL")
    markdown: str = Field(..., description="Scraped content in markdown format")
    title: str = Field(..., description="Page title")
    file_path: Optional[str] = Field(None, description="Path where raw content was saved")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the content was scraped")
    content_hash: str = Field(..., description="SHA-256 hash of the content")


class HealingResult(BaseModel):
    """Result of a healing operation on a stale URL."""
    
    url: str = Field(..., description="URL that was healed")
    status: str = Field(..., description="Status: 'success', 'failed', 'unchanged'")
    triples_extracted: int = Field(default=0, description="Number of triples extracted")
    triples_updated: int = Field(default=0, description="Number of triples updated in graph")
    error: Optional[str] = Field(None, description="Error message if healing failed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When healing occurred")


class ScrapeResult(BaseModel):
    """Standardized result from any scraper implementation.
    
    This model ensures consistency between different scraper backends
    (Firecrawl, Local, etc.) and provides all necessary data for processing.
    """
    
    url: str = Field(..., description="Source URL that was scraped")
    content: str = Field(..., description="Scraped content in markdown format")
    content_hash: str = Field(..., description="SHA-256 hash of the content for change detection")
    title: Optional[str] = Field(None, description="Page title if available")
    metadata: dict = Field(default_factory=dict, description="Additional metadata (scraper type, timestamp, etc.)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the scraping occurred")
    
    @classmethod
    def compute_content_hash(cls, content: str) -> str:
        """Compute SHA-256 hash of content.
        
        Args:
            content: The content to hash
            
        Returns:
            SHA-256 hash as hexadecimal string
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "url": "https://example.com",
                "content": "# Example Page\n\nThis is the content...",
                "content_hash": "a7f3c2d1...",
                "title": "Example Page",
                "metadata": {"scraper": "local", "user_agent": "Mozilla/5.0..."},
                "timestamp": "2024-01-15T10:00:00Z"
            }
        }

