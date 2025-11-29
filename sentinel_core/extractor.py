"""
InfoExtractor - LLM-based Entity and Relationship Extraction

Extracts structured knowledge graph triples from unstructured text using local LLMs.
"""

from __future__ import annotations

import json
import os
from typing import Optional

import structlog
from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from .models import GraphTriple

logger = structlog.get_logger(__name__)


class ExtractionException(Exception):
    """Raised when extraction operations fail"""
    pass


class InfoExtractor:
    """
    Extracts entities and relationships from text using LLMs.
    
    Follows Single Responsibility Principle: handles only LLM-based
    information extraction.
    """

    def __init__(
        self,
        model: str = "llama3.1",
        base_url: Optional[str] = None,
        temperature: float = 0.1,
        timeout: int = 600,
    ) -> None:
        """
        Initialize the InfoExtractor.

        Args:
            model: Ollama model name (e.g., "llama3.1", "mistral")
            base_url: Ollama base URL (defaults to env var OLLAMA_BASE_URL)
            temperature: LLM temperature (0.0 = deterministic, 1.0 = creative)
            timeout: Request timeout in seconds

        Raises:
            ExtractionException: If initialization fails
        """
        self.model = model
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.temperature = temperature
        self.timeout = timeout

        try:
            # Initialize Ollama chat model
            self.llm = ChatOllama(
                model=self.model,
                base_url=self.base_url,
                temperature=self.temperature,
                timeout=self.timeout,
            )

            # Initialize JSON output parser
            self.parser = JsonOutputParser(pydantic_object=GraphTriple)

            # Create extraction prompt
            self.prompt = self._create_extraction_prompt()

            # Create extraction chain
            self.chain = self.prompt | self.llm | self.parser

            logger.info(
                "info_extractor_initialized",
                model=self.model,
                base_url=self.base_url,
                temperature=self.temperature,
            )

        except Exception as e:
            logger.error("failed_to_initialize_extractor", error=str(e))
            raise ExtractionException(f"Failed to initialize InfoExtractor: {e}") from e

    def _create_extraction_prompt(self) -> ChatPromptTemplate:
        """
        Create the prompt template for entity and relationship extraction.

        Returns:
            ChatPromptTemplate configured for triple extraction
        """
        system_message = """You are an expert knowledge graph extraction system.

Your task is to extract structured information from text in the form of triples:
(head entity, relationship, tail entity)

Guidelines:
1. Extract ONLY factual relationships explicitly stated in the text
2. Use clear, specific entity names (proper nouns when possible)
3. Use standardized relationship types (e.g., WORKS_AT, LOCATED_IN, FOUNDED_BY)
4. Each triple should represent ONE atomic fact
5. Normalize entity names (e.g., "Dr. John Smith" → "John Smith")
6. Use present tense for relationships when possible

Relationship Types (examples):
- WORKS_AT: employment relationship
- LOCATED_IN: geographic location
- FOUNDED_BY: founder relationship
- PART_OF: organizational hierarchy
- PRODUCES: production/creation
- ACQUIRED_BY: acquisition
- INVESTED_IN: investment
- PARTNERED_WITH: partnership
- STUDIED_AT: education
- BORN_IN: birthplace

Output Format:
Return a JSON array of objects, each with:
- "head": source entity name
- "relation": relationship type (UPPERCASE_WITH_UNDERSCORES)
- "tail": target entity name
- "confidence": confidence score 0.0-1.0 (optional, default 1.0)

Example:
[
  {{"head": "Tesla", "relation": "FOUNDED_BY", "tail": "Elon Musk", "confidence": 1.0}},
  {{"head": "Tesla", "relation": "PRODUCES", "tail": "Electric Vehicles", "confidence": 1.0}}
]

IMPORTANT: Return ONLY valid JSON. No explanations, no markdown, just the JSON array."""

        human_message = """Extract knowledge graph triples from the following text:

{text}

Return a JSON array of triples:"""

        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", human_message),
        ])

    def extract_triples(
        self,
        markdown_text: str,
        max_triples: int = 50,
    ) -> list[GraphTriple]:
        """
        Extract knowledge graph triples from markdown text.

        Args:
            markdown_text: The text to extract triples from
            max_triples: Maximum number of triples to extract

        Returns:
            List of GraphTriple objects

        Raises:
            ExtractionException: If extraction fails
        """
        if not markdown_text or not markdown_text.strip():
            logger.warning("empty_text_provided")
            return []

        logger.info(
            "extracting_triples",
            text_length=len(markdown_text),
            max_triples=max_triples,
        )

        try:
            # Truncate text if too long (to avoid token limits)
            max_chars = 8000  # Roughly 2000 tokens
            if len(markdown_text) > max_chars:
                logger.warning(
                    "truncating_text",
                    original_length=len(markdown_text),
                    truncated_length=max_chars,
                )
                markdown_text = markdown_text[:max_chars] + "\n\n[Text truncated...]"

            # Invoke the chain
            result = self.chain.invoke({"text": markdown_text})

            # Parse result
            if isinstance(result, list):
                triples_data = result
            elif isinstance(result, dict):
                # Sometimes LLM returns {"triples": [...]}
                triples_data = result.get("triples", [result])
            else:
                logger.error("unexpected_result_format", result_type=type(result))
                raise ExtractionException(f"Unexpected result format: {type(result)}")

            # Convert to GraphTriple objects
            triples = []
            for item in triples_data[:max_triples]:
                try:
                    if isinstance(item, dict):
                        triple = GraphTriple(**item)
                        triples.append(triple)
                    else:
                        logger.warning("skipping_invalid_triple", item=item)
                except Exception as e:
                    logger.warning("failed_to_parse_triple", item=item, error=str(e))
                    continue

            logger.info(
                "extraction_complete",
                num_triples=len(triples),
                text_length=len(markdown_text),
            )

            return triples

        except Exception as e:
            logger.error(
                "extraction_failed",
                error=str(e),
                text_preview=markdown_text[:200],
            )
            raise ExtractionException(f"Failed to extract triples: {e}") from e

    def extract_triples_with_retry(
        self,
        markdown_text: str,
        max_retries: int = 2,
    ) -> list[GraphTriple]:
        """
        Extract triples with automatic retry on failure.

        Args:
            markdown_text: The text to extract triples from
            max_retries: Maximum number of retry attempts

        Returns:
            List of GraphTriple objects

        Raises:
            ExtractionException: If all retries fail
        """
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return self.extract_triples(markdown_text)
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
            f"Failed to extract triples after {max_retries + 1} attempts"
        ) from last_exception

    def extract_and_validate(
        self,
        markdown_text: str,
        min_confidence: float = 0.5,
    ) -> list[GraphTriple]:
        """
        Extract triples and filter by confidence threshold.

        Args:
            markdown_text: The text to extract triples from
            min_confidence: Minimum confidence score to include

        Returns:
            List of high-confidence GraphTriple objects
        """
        triples = self.extract_triples(markdown_text)

        # Filter by confidence
        filtered_triples = [
            triple for triple in triples
            if triple.confidence >= min_confidence
        ]

        logger.info(
            "triples_filtered_by_confidence",
            original_count=len(triples),
            filtered_count=len(filtered_triples),
            min_confidence=min_confidence,
        )

        return filtered_triples
