"""
Query Engine - Natural Language to Cypher Query Conversion

Phase 5: Explainable Retrieval
Converts natural language questions to Cypher queries and tracks the path.
"""

from __future__ import annotations

import re
from typing import List, Dict, Any, Optional
import structlog

logger = structlog.get_logger(__name__)


class QueryEngine:
    """
    Converts natural language questions to Cypher queries.
    
    Phase 5: Explainable Retrieval
    - Tracks query paths for visualization
    - Enables "show your work" functionality
    """
    
    def __init__(self, graph_manager, llm=None):
        """
        Initialize the Query Engine.
        
        Args:
            graph_manager: GraphManager instance
            llm: Optional LLM for natural language processing
        """
        self.graph = graph_manager
        self.llm = llm
        
    def _extract_entities_from_question(self, question: str) -> list[str]:
        """
        Extract potential entity names from the question.
        Uses simple capitalization heuristics.
        """
        # Remove common question words
        question_words = {'what', 'who', 'when', 'where', 'why', 'how', 'is', 'are', 'was', 'were', 
                         'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'about',
                         'does', 'do', 'did', 'can', 'could', 'would', 'should', 'founded', 'created',
                         'made', 'built', 'developed', 'invented'}
        
        # Split into words and find capitalized sequences
        words = question.split()
        entities = []
        current_entity = []
        
        for word in words:
            # Clean word
            clean_word = re.sub(r'[^\w\s]', '', word)
            if not clean_word:
                continue
                
            # Check if it's a potential entity (capitalized or all caps)
            if clean_word[0].isupper() or clean_word.isupper():
                if clean_word.lower() not in question_words:
                    current_entity.append(clean_word)
            else:
                if current_entity:
                    entities.append(' '.join(current_entity))
                    current_entity = []
        
        # Add last entity if exists
        if current_entity:
            entities.append(' '.join(current_entity))
        
        return entities
    
    def generate_cypher_from_question(self, question: str) -> str:
        """
        Convert a natural language question to a Cypher query.
        
        Extracts entities from the question and searches for them in the graph.
        
        Args:
            question: Natural language question
            
        Returns:
            Cypher query string
        """
        question_lower = question.lower()
        entities = self._extract_entities_from_question(question)
        
        # If we found entities in the question, search for them
        if entities:
            entity_pattern = '|'.join([f'(?i).*{re.escape(e)}.*' for e in entities])
            
            # Check question type
            if "who" in question_lower and ("founded" in question_lower or "created" in question_lower or "started" in question_lower):
                # Founder query - check both directions
                return f"""
                MATCH path = (target:Entity)-[r]->(person:Entity)
                WHERE r.valid_to IS NULL
                  AND (type(r) =~ '.*FOUND.*' OR type(r) =~ '.*CREAT.*' OR type(r) =~ '.*START.*')
                  AND (target.name =~ '{entity_pattern}')
                RETURN person.name AS person,
                       type(r) AS relation,
                       target.name AS company,
                       r.confidence AS confidence,
                       [node in nodes(path) | node.name] AS path_nodes
                LIMIT 1
                """
            elif "what" in question_lower or "tell" in question_lower or "about" in question_lower:
                # General information query about an entity
                return f"""
                MATCH path = (source:Entity)-[r]->(target:Entity)
                WHERE r.valid_to IS NULL
                  AND (source.name =~ '{entity_pattern}' OR target.name =~ '{entity_pattern}')
                RETURN source.name AS source,
                       type(r) AS relation,
                       target.name AS target,
                       r.confidence AS confidence,
                       [node in nodes(path) | node.name] AS path_nodes
                LIMIT 5
                """
        
        # Fallback patterns based on question type
        if "how much" in question_lower or "cost" in question_lower or "price" in question_lower:
            return """
            MATCH path = (product:Entity)-[r]->(price:Entity)
            WHERE r.valid_to IS NULL
              AND (type(r) =~ '.*COST.*' OR type(r) =~ '.*PRICE.*')
            RETURN product.name AS product,
                   price.name AS price,
                   r.confidence AS confidence,
                   r.source_url AS source,
                   [node in nodes(path) | node.name] AS path_nodes
            LIMIT 1
            """
        elif "who" in question_lower and ("ceo" in question_lower or "founder" in question_lower):
            return """
            MATCH path = (person:Entity)-[r]->(company:Entity)
            WHERE r.valid_to IS NULL
              AND (type(r) =~ '.*CEO.*' OR type(r) =~ '.*FOUND.*')
            RETURN person.name AS person,
                   type(r) AS relation,
                   company.name AS company,
                   r.confidence AS confidence,
                   [node in nodes(path) | node.name] AS path_nodes
            LIMIT 1
            """
        elif "what" in question_lower and "changed" in question_lower:
            return """
            MATCH path = (source:Entity)-[r]->(target:Entity)
            WHERE r.valid_to IS NOT NULL
            RETURN source.name AS source,
                   type(r) AS relation,
                   target.name AS target,
                   r.valid_from AS from_date,
                   r.valid_to AS to_date,
                   [node in nodes(path) | node.name] AS path_nodes
            ORDER BY r.valid_to DESC
            LIMIT 5
            """
        else:
            # Default: show random relationships
            return """
            MATCH path = (source:Entity)-[r]->(target:Entity)
            WHERE r.valid_to IS NULL
            RETURN source.name AS source,
                   type(r) AS relation,
                   target.name AS target,
                   r.confidence AS confidence,
                   [node in nodes(path) | node.name] AS path_nodes
            ORDER BY rand()
            LIMIT 5
            """
    
    def execute_query_with_path(
        self,
        question: str,
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a natural language query and return results with path.
        
        Args:
            question: Natural language question
            timestamp: Optional timestamp for time-travel queries
            
        Returns:
            Dictionary with answer and path for visualization
        """
        logger.info("executing_query", question=question)
        
        try:
            # Generate Cypher query
            cypher_query = self.generate_cypher_from_question(question)
            logger.debug("generated_cypher", query=cypher_query)
            
            # Execute query
            with self.graph.driver.session(database=self.graph.database) as session:
                result = session.run(cypher_query)
                records = list(result)
                
                if not records:
                    return {
                        "answer": "No results found.",
                        "path": [],
                        "results": []
                    }
                
                # Extract path from first result
                first_record = records[0]
                path_nodes = first_record.get("path_nodes", [])
                
                # Format answer
                answer = self._format_answer(question, records)
                
                # Extract all results
                results = []
                for record in records:
                    results.append(dict(record))
                
                logger.info(
                    "query_executed",
                    question=question,
                    results_count=len(results),
                    path_length=len(path_nodes)
                )
                
                return {
                    "answer": answer,
                    "path": path_nodes,
                    "results": results,
                    "cypher_query": cypher_query
                }
                
        except Exception as e:
            logger.error("query_execution_failed", question=question, error=str(e))
            return {
                "answer": f"Error: {str(e)}",
                "path": [],
                "results": []
            }
    
    def _format_answer(self, question: str, records: List) -> str:
        """
        Format query results into a natural language answer.
        
        Args:
            question: Original question
            records: Query results
            
        Returns:
            Natural language answer
        """
        if not records:
            return "I don't have enough information to answer that question."
        
        first_record = records[0]
        question_lower = question.lower()
        
        # Price questions
        if "how much" in question_lower or "cost" in question_lower or "price" in question_lower:
            product = first_record.get("product", "Unknown")
            price = first_record.get("price", "Unknown")
            return f"{product} costs {price}."
        
        # Leadership/Founder questions
        elif "who" in question_lower and ("ceo" in question_lower or "founder" in question_lower or "founded" in question_lower):
            person = first_record.get("person", "Unknown")
            relation = first_record.get("relation", "is associated with")
            company = first_record.get("company", "Unknown")
            
            # Handle passive relationships (e.g., FOUNDED_BY -> founded)
            relation_clean = relation.lower().replace('_', ' ')
            if 'by' in relation_clean:
                # Convert passive to active: "founded by" -> "founded"
                relation_clean = relation_clean.replace(' by', '')
            
            return f"{person} {relation_clean} {company}."
        
        # Change detection
        elif "what" in question_lower and "changed" in question_lower:
            changes = []
            for record in records[:3]:  # Top 3 changes
                source = record.get("source", "Unknown")
                relation = record.get("relation", "relates to")
                target = record.get("target", "Unknown")
                to_date = record.get("to_date", "recently")
                changes.append(f"{source} {relation.lower().replace('_', ' ')} {target} (changed {to_date})")
            
            return "Recent changes:\n" + "\n".join(f"- {change}" for change in changes)
        
        # Default
        else:
            source = first_record.get("source", "Unknown")
            relation = first_record.get("relation", "relates to")
            target = first_record.get("target", "Unknown")
            return f"{source} {relation.lower().replace('_', ' ')} {target}."
