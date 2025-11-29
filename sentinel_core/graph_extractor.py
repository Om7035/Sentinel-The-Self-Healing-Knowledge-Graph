"""
GraphExtractor - Model-Agnostic LLM-based Entity and Relationship Extraction

Uses LiteLLM for model-agnostic LLM calls and Instructor for output-strict schema enforcement.
Extracts structured knowledge graph data from unstructured text.
"""

from __future__ import annotations

import os
from typing import Optional

import httpx
import instructor
import litellm
import structlog
from pydantic import Field

from .models import GraphData, GraphNode, TemporalEdge

logger = structlog.get_logger(__name__)


class ExtractionException(Exception):
    """Raised when extraction operations fail"""
    pass


class GraphExtractor:
    """
    Extracts entities and relationships from text using LLMs.
    
    Model-agnostic: Uses LiteLLM to support any LLM provider (OpenAI, Anthropic, Ollama, etc.)
    Output-strict: Uses Instructor to enforce GraphData schema
    """

    def __init__(
        self,
        model_name: str = "ollama/phi3",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.1,
        timeout: int = 600,
    ) -> None:
        """
        Initialize the GraphExtractor.

        Args:
            model_name: LiteLLM model name (e.g., "ollama/llama3", "gpt-4", "claude-3-opus")
            api_key: API key for the LLM provider (if required)
            base_url: Base URL for the LLM API (e.g., for Ollama: "http://localhost:11434")
            temperature: LLM temperature (0.0 = deterministic, 1.0 = creative)
            timeout: Request timeout in seconds

        Raises:
            ExtractionException: If initialization fails
        """
        self.model_name = model_name
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.temperature = temperature
        self.timeout = timeout

        # Patch litellm with instructor for structured outputs
        self.client = instructor.from_litellm(litellm.completion)

        logger.info(
            "graph_extractor_initialized",
            model=self.model_name,
            base_url=self.base_url,
            temperature=self.temperature,
        )

    def check_connection(self) -> bool:
        """
        Verify connection to the LLM provider.
        
        For Ollama: Attempts to connect to localhost:11434
        For other providers: Checks if API key is set
        
        Returns:
            True if connection is available
            
        Raises:
            ExtractionException: If connection check fails with helpful guidance
        """
        try:
            if "ollama" in self.model_name.lower():
                # Check Ollama connection
                try:
                    response = httpx.get(f"{self.base_url}/api/tags", timeout=5)
                    if response.status_code == 200:
                        logger.info("ollama_connection_verified", base_url=self.base_url)
                        return True
                except Exception as e:
                    logger.error("ollama_connection_failed", error=str(e))
                    raise ExtractionException(
                        f"❌ Cannot connect to Ollama at {self.base_url}\n"
                        f"Please ensure Ollama is running: ollama serve\n"
                        f"Error: {str(e)}"
                    ) from e
            else:
                # For cloud providers, check if API key is set
                if not self.api_key:
                    raise ExtractionException(
                        f"❌ No API key found for {self.model_name}\n"
                        f"Please set the LLM_API_KEY environment variable"
                    )
                logger.info("api_key_configured", model=self.model_name)
                return True
                
        except ExtractionException:
            raise
        except Exception as e:
            logger.error("connection_check_failed", error=str(e))
            raise ExtractionException(f"Connection check failed: {e}") from e

    def extract(self, text: str) -> GraphData:
        """
        Extract knowledge graph triples from text.

        This method uses Instructor to enforce strict schema compliance,
        ensuring the LLM returns valid GraphData objects.

        Args:
            text: The text to extract knowledge from

        Returns:
            GraphData object containing nodes and edges

        Raises:
            ExtractionException: If extraction fails
        """
        if not text or not text.strip():
            logger.warning("empty_text_provided")
            return GraphData(nodes=[], edges=[])

        logger.info("extracting_knowledge", text_length=len(text))

        try:
            # Create extraction prompt
            system_prompt = """You are an expert knowledge graph extraction system.

Your task is to extract structured information from text in the form of nodes and edges.

Guidelines:
1. Extract ONLY factual relationships explicitly stated in the text
2. Create nodes for each distinct entity (people, organizations, places, concepts)
3. Create edges to represent relationships between entities
4. Use clear, specific node IDs (lowercase with underscores, e.g., "elon_musk")
5. Use standardized relationship types (UPPERCASE_WITH_UNDERSCORES, e.g., "FOUNDED_BY")
6. If a fact implies a timeframe, add it to the edge properties
7. Each edge should represent ONE atomic fact

Node labels (examples):
- Person, Company, Organization, Location, Product, Concept, Event

Relationship types (examples):
- FOUNDED_BY, WORKS_AT, LOCATED_IN, PART_OF, PRODUCES, ACQUIRED_BY
- INVESTED_IN, PARTNERED_WITH, STUDIED_AT, BORN_IN, CEO_OF

IMPORTANT: Return strict JSON matching the GraphData schema."""

            user_prompt = f"""Extract knowledge triples from the following text.
If a fact implies a timeframe, add it to the edge properties.
Return strict JSON with nodes and edges.

Text:
{text}"""

            # Use instructor to get structured output
            response: GraphData = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_model=GraphData,
                temperature=self.temperature,
                timeout=self.timeout,
                api_key=self.api_key,
                base_url=self.base_url if "ollama" in self.model_name.lower() else None,
            )

            logger.info(
                "extraction_complete",
                num_nodes=len(response.nodes),
                num_edges=len(response.edges),
            )

            return response

        except Exception as e:
            logger.error(
                "extraction_failed",
                error=str(e),
                text_preview=text[:200],
                exc_info=True,
            )
            raise ExtractionException(f"Failed to extract knowledge: {e}") from e

    def extract_with_retry(
        self,
        text: str,
        max_retries: int = 2,
    ) -> GraphData:
        """
        Extract knowledge with automatic retry on failure.

        Args:
            text: The text to extract knowledge from
            max_retries: Maximum number of retry attempts

        Returns:
            GraphData object

        Raises:
            ExtractionException: If all retries fail
        """
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return self.extract(text)
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    logger.warning(
                        "extraction_attempt_failed",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        error=str(e),
                    )
                else:
                    logger.error(
                        "all_extraction_attempts_failed",
                        attempts=max_retries + 1,
                    )

        raise ExtractionException(
            f"Failed to extract knowledge after {max_retries + 1} attempts"
        ) from last_exception
