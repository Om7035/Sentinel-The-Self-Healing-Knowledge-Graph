"""
GraphManager - Neo4j Temporal Knowledge Graph Manager

Manages Neo4j connections and temporal edge operations for the Sentinel system.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime
from typing import Any, Optional

import structlog
from neo4j import GraphDatabase, Driver, Session, ManagedTransaction
from neo4j.exceptions import ServiceUnavailable, AuthError

logger = structlog.get_logger(__name__)


class GraphException(Exception):
    """Raised when graph operations fail"""
    pass


class GraphManager:
    """
    Manages Neo4j graph database operations with temporal validity tracking.
    
    Follows Single Responsibility Principle: handles only graph database
    operations and temporal edge management.
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: str = "neo4j",
    ) -> None:
        """
        Initialize the GraphManager.

        Args:
            uri: Neo4j connection URI (defaults to env var NEO4J_URI)
            username: Neo4j username (defaults to env var NEO4J_USERNAME)
            password: Neo4j password (defaults to env var NEO4J_PASSWORD)
            database: Neo4j database name (defaults to "neo4j")

        Raises:
            GraphException: If connection parameters are missing or invalid
        """
        # Load from environment variables if not provided
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = username or os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        self.database = database

        if not self.password:
            raise GraphException("Neo4j password is required")

        # Initialize driver
        try:
            self.driver: Driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
            )
            logger.info(
                "graph_manager_initialized",
                uri=self.uri,
                database=self.database,
            )
        except Exception as e:
            logger.error("failed_to_initialize_driver", error=str(e))
            raise GraphException(f"Failed to initialize Neo4j driver: {e}") from e

    def close(self) -> None:
        """
        Close the Neo4j driver connection.

        Should be called when the GraphManager is no longer needed.
        """
        if self.driver:
            self.driver.close()
            logger.info("graph_driver_closed")

    def verify_connectivity(self) -> bool:
        """
        Verify connectivity to the Neo4j database.

        Returns:
            True if connection is successful, False otherwise

        Raises:
            GraphException: If connection verification fails
        """
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1 AS num")
                record = result.single()
                
                if record and record["num"] == 1:
                    logger.info("connectivity_verified", uri=self.uri)
                    return True
                else:
                    raise GraphException("Unexpected response from Neo4j")
                    
        except ServiceUnavailable as e:
            logger.error("neo4j_unavailable", error=str(e))
            raise GraphException(f"Neo4j service unavailable: {e}") from e
        except AuthError as e:
            logger.error("neo4j_auth_failed", error=str(e))
            raise GraphException(f"Neo4j authentication failed: {e}") from e
        except Exception as e:
            logger.error("connectivity_check_failed", error=str(e))
            raise GraphException(f"Connectivity check failed: {e}") from e

    def clear_database(self) -> int:
        """
        Clear all nodes and relationships from the database.

        ⚠️ WARNING: This is a destructive operation! Use only for testing.

        Returns:
            Number of nodes deleted

        Raises:
            GraphException: If clearing fails
        """
        logger.warning("clearing_database", database=self.database)

        try:
            with self.driver.session(database=self.database) as session:
                # Delete all relationships first
                session.run("MATCH ()-[r]->() DELETE r")
                
                # Then delete all nodes and count them
                result = session.run("MATCH (n) DELETE n RETURN count(n) AS deleted")
                record = result.single()
                deleted_count = record["deleted"] if record else 0

                logger.info("database_cleared", nodes_deleted=deleted_count)
                return deleted_count

        except Exception as e:
            logger.error("failed_to_clear_database", error=str(e))
            raise GraphException(f"Failed to clear database: {e}") from e

    def compute_content_hash(self, source_node: str, relation_type: str, target_node: str) -> str:
        """
        Generate SHA-256 hash of edge content for deduplication.
        
        Phase 2: Idempotent Ingestion
        This enables zero-write operations when content hasn't changed.
        
        Args:
            source_node: Source entity name
            relation_type: Relationship type
            target_node: Target entity name
            
        Returns:
            SHA-256 hash string
        """
        content = f"{source_node}|{relation_type}|{target_node}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get_edge_hash(self, source_node: str, relation_type: str, target_node: str) -> Optional[str]:
        """
        Retrieve the stored content hash for an existing edge.
        
        Args:
            source_node: Source entity name
            relation_type: Relationship type
            target_node: Target entity name
            
        Returns:
            Stored hash or None if edge doesn't exist
        """
        try:
            with self.driver.session(database=self.database) as session:
                query = f"""
                MATCH (source:Entity {{name: $source_name}})
                      -[r:{relation_type}]->(target:Entity {{name: $target_name}})
                WHERE r.valid_to IS NULL
                RETURN r.content_hash AS hash
                """
                
                result = session.run(
                    query,
                    source_name=source_node,
                    target_name=target_node
                )
                
                record = result.single()
                return record["hash"] if record else None
                
        except Exception as e:
            logger.error("failed_to_get_edge_hash", error=str(e))
            return None

    def upsert_temporal_edge(
        self,
        source_node: str,
        relation_type: str,
        target_node: str,
        source_url: str,
        confidence: float = 1.0,
        evidence_text: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create or update a temporal edge between two nodes.

        This implements the core temporal validity logic:
        1. Check if an active relationship exists (valid_to is NULL)
        2. If exists: Update last_verified timestamp
        3. If not exists: Create new relationship with valid_from=NOW

        Args:
            source_node: Name of the source entity
            relation_type: Type of relationship (e.g., "WORKS_AT", "LOCATED_IN")
            target_node: Name of the target entity
            source_url: URL where this relationship was found
            confidence: Confidence score (0.0 - 1.0)
            evidence_text: Supporting text snippet

        Returns:
            Dictionary with operation details:
                - action: "created" or "updated"
                - relationship_id: Neo4j relationship ID
                - valid_from: Timestamp when relationship became valid
                - last_verified: Timestamp of last verification

        Raises:
            GraphException: If the operation fails
        """
        logger.info(
            "upserting_temporal_edge",
            source=source_node,
            relation=relation_type,
            target=target_node,
            source_url=source_url,
        )

        # Phase 2: Idempotent Ingestion - Check content hash
        new_hash = self.compute_content_hash(source_node, relation_type, target_node)
        existing_hash = self.get_edge_hash(source_node, relation_type, target_node)
        
        if new_hash == existing_hash:
            logger.info(
                "content_unchanged_skipping_write",
                source=source_node,
                relation=relation_type,
                target=target_node,
                hash=new_hash
            )
            # Zero DB operations - content hasn't changed
            return {
                "action": "skipped",
                "reason": "content_unchanged",
                "hash": new_hash
            }

        try:
            with self.driver.session(database=self.database) as session:
                result = session.execute_write(
                    self._upsert_temporal_edge_tx,
                    source_node,
                    relation_type,
                    target_node,
                    source_url,
                    confidence,
                    evidence_text,
                    new_hash,  # Pass the computed hash
                )
                
                logger.info(
                    "temporal_edge_upserted",
                    action=result["action"],
                    relationship_id=result["relationship_id"],
                )
                
                return result

        except Exception as e:
            logger.error(
                "failed_to_upsert_temporal_edge",
                source=source_node,
                relation=relation_type,
                target=target_node,
                error=str(e),
            )
            raise GraphException(f"Failed to upsert temporal edge: {e}") from e

    @staticmethod
    def _upsert_temporal_edge_tx(
        tx: ManagedTransaction,
        source_node: str,
        relation_type: str,
        target_node: str,
        source_url: str,
        confidence: float,
        evidence_text: Optional[str],
        content_hash: str,
    ) -> dict[str, Any]:
        """
        Transaction function for upserting a temporal edge.

        This runs within a Neo4j transaction to ensure atomicity.
        """
        now = datetime.utcnow()

        # First, ensure both nodes exist (create if they don't)
        create_nodes_query = """
        MERGE (source:Entity {name: $source_name})
        ON CREATE SET source.created_at = datetime($now)
        
        MERGE (target:Entity {name: $target_name})
        ON CREATE SET target.created_at = datetime($now)
        
        RETURN source, target
        """
        
        tx.run(
            create_nodes_query,
            source_name=source_node,
            target_name=target_node,
            now=now.isoformat(),
        )

        # Check if an active relationship exists
        check_query = """
        MATCH (source:Entity {name: $source_name})
              -[r]->(target:Entity {name: $target_name})
        WHERE type(r) = $relation_type
          AND r.valid_to IS NULL
        RETURN r, id(r) AS rel_id
        """

        result = tx.run(
            check_query,
            source_name=source_node,
            target_name=target_node,
            relation_type=relation_type,
        )

        existing_rel = result.single()

        if existing_rel:
            # Active relationship exists - update last_verified
            update_query = f"""
            MATCH (source:Entity {{name: $source_name}})
                  -[r:{relation_type}]->(target:Entity {{name: $target_name}})
            WHERE r.valid_to IS NULL
            SET r.last_verified = datetime($now),
                r.verification_count = coalesce(r.verification_count, 0) + 1
            RETURN id(r) AS rel_id, r.valid_from AS valid_from, r.last_verified AS last_verified
            """

            update_result = tx.run(
                update_query,
                source_name=source_node,
                target_name=target_node,
                now=now.isoformat(),
            )

            record = update_result.single()

            return {
                "action": "updated",
                "relationship_id": record["rel_id"],
                "valid_from": record["valid_from"],
                "last_verified": record["last_verified"],
            }

        else:
            # No active relationship - create new one
            create_query = f"""
            MATCH (source:Entity {{name: $source_name}})
            MATCH (target:Entity {{name: $target_name}})
            CREATE (source)-[r:{relation_type}]->(target)
            SET r.valid_from = datetime($now),
                r.valid_to = NULL,
                r.source_url = $source_url,
                r.confidence = $confidence,
                r.evidence_text = $evidence_text,
                r.last_verified = datetime($now),
                r.verification_count = 1,
                r.content_hash = $content_hash
            RETURN id(r) AS rel_id, r.valid_from AS valid_from, r.last_verified AS last_verified
            """

            create_result = tx.run(
                create_query,
                source_name=source_node,
                target_name=target_node,
                now=now.isoformat(),
                source_url=source_url,
                confidence=confidence,
                evidence_text=evidence_text,
                content_hash=content_hash,
            )

            record = create_result.single()

            return {
                "action": "created",
                "relationship_id": record["rel_id"],
                "valid_from": record["valid_from"],
                "last_verified": record["last_verified"],
            }

    def upsert_data(
        self,
        data: "GraphData",
        source_url: str = "unknown",
    ) -> dict[str, Any]:
        """
        Upsert GraphData (nodes and edges) into Neo4j with temporal logic.

        This is the main method for ingesting extracted knowledge graph data.
        
        Logic for each edge:
        1. Match existing active edge (valid_to IS NULL)
        2. Compute hash of edge content
        3. If found & hash matches: Update last_verified = NOW (zero writes if unchanged)
        4. If found & hash differs: Set old edge valid_to = NOW, Create NEW edge valid_from = NOW
        5. If not found: Create NEW edge valid_from = NOW

        Args:
            data: GraphData object containing nodes and edges
            source_url: Source URL for provenance tracking

        Returns:
            Dictionary with operation statistics:
                - nodes_created: Number of new nodes created
                - edges_created: Number of new edges created
                - edges_updated: Number of edges updated (last_verified)
                - edges_invalidated: Number of edges invalidated
                - edges_skipped: Number of edges skipped (unchanged)

        Raises:
            GraphException: If the operation fails
        """
        from .models import GraphData  # Import here to avoid circular dependency
        
        logger.info(
            "upserting_graph_data",
            num_nodes=len(data.nodes),
            num_edges=len(data.edges),
            source_url=source_url,
        )

        stats = {
            "nodes_created": 0,
            "edges_created": 0,
            "edges_updated": 0,
            "edges_invalidated": 0,
            "edges_skipped": 0,
        }

        try:
            with self.driver.session(database=self.database) as session:
                # First, create/merge all nodes
                for node in data.nodes:
                    result = session.execute_write(
                        self._upsert_node_tx,
                        node.id,
                        node.label,
                        node.properties,
                    )
                    if result["created"]:
                        stats["nodes_created"] += 1

                # Then, process all edges with temporal logic
                for edge in data.edges:
                    # Compute hash for change detection
                    edge_hash = edge.compute_hash()
                    
                    # Check if active edge exists
                    existing_hash = self.get_edge_hash(edge.source, edge.relation, edge.target)
                    
                    if existing_hash == edge_hash:
                        # Content unchanged - just update last_verified
                        logger.debug(
                            "edge_unchanged_updating_verification",
                            source=edge.source,
                            relation=edge.relation,
                            target=edge.target,
                        )
                        result = session.execute_write(
                            self._update_edge_verification_tx,
                            edge.source,
                            edge.relation,
                            edge.target,
                        )
                        if result:
                            stats["edges_updated"] += 1
                        else:
                            stats["edges_skipped"] += 1
                            
                    elif existing_hash is not None:
                        # Hash differs - invalidate old edge and create new one
                        logger.info(
                            "edge_changed_invalidating_and_creating",
                            source=edge.source,
                            relation=edge.relation,
                            target=edge.target,
                            old_hash=existing_hash,
                            new_hash=edge_hash,
                        )
                        
                        # Invalidate old edge
                        session.execute_write(
                            self._invalidate_edge_tx,
                            edge.source,
                            edge.relation,
                            edge.target,
                        )
                        stats["edges_invalidated"] += 1
                        
                        # Create new edge
                        session.execute_write(
                            self._create_edge_tx,
                            edge.source,
                            edge.relation,
                            edge.target,
                            edge.properties,
                            edge.valid_from,
                            source_url,
                            edge_hash,
                        )
                        stats["edges_created"] += 1
                        
                    else:
                        # No existing edge - create new one
                        logger.debug(
                            "creating_new_edge",
                            source=edge.source,
                            relation=edge.relation,
                            target=edge.target,
                        )
                        session.execute_write(
                            self._create_edge_tx,
                            edge.source,
                            edge.relation,
                            edge.target,
                            edge.properties,
                            edge.valid_from,
                            source_url,
                            edge_hash,
                        )
                        stats["edges_created"] += 1

                logger.info(
                    "graph_data_upserted",
                    **stats,
                )

                return stats

        except Exception as e:
            logger.error(
                "failed_to_upsert_graph_data",
                error=str(e),
                exc_info=True,
            )
            raise GraphException(f"Failed to upsert graph data: {e}") from e

    @staticmethod
    def _upsert_node_tx(
        tx: ManagedTransaction,
        node_id: str,
        label: str,
        properties: dict,
    ) -> dict[str, bool]:
        """Transaction function for upserting a node."""
        now = datetime.utcnow()
        
        # Use MERGE to create node if it doesn't exist
        query = f"""
        MERGE (n:{label} {{id: $node_id}})
        ON CREATE SET n.created_at = datetime($now),
                      n += $properties
        ON MATCH SET n.updated_at = datetime($now),
                     n += $properties
        RETURN n, 
               CASE WHEN n.created_at = datetime($now) THEN true ELSE false END AS created
        """
        
        result = tx.run(
            query,
            node_id=node_id,
            properties=properties,
            now=now.isoformat(),
        )
        
        record = result.single()
        return {"created": record["created"] if record else False}

    @staticmethod
    def _update_edge_verification_tx(
        tx: ManagedTransaction,
        source_id: str,
        relation: str,
        target_id: str,
    ) -> bool:
        """Transaction function for updating edge last_verified timestamp."""
        now = datetime.utcnow()
        
        query = f"""
        MATCH (source {{id: $source_id}})-[r:{relation}]->(target {{id: $target_id}})
        WHERE r.valid_to IS NULL
        SET r.last_verified = datetime($now),
            r.verification_count = coalesce(r.verification_count, 0) + 1
        RETURN id(r) AS rel_id
        """
        
        result = tx.run(
            query,
            source_id=source_id,
            target_id=target_id,
            now=now.isoformat(),
        )
        
        return result.single() is not None

    @staticmethod
    def _create_edge_tx(
        tx: ManagedTransaction,
        source_id: str,
        relation: str,
        target_id: str,
        properties: dict,
        valid_from: datetime,
        source_url: str,
        content_hash: str,
    ) -> int:
        """Transaction function for creating a new temporal edge."""
        now = datetime.utcnow()
        
        query = f"""
        MATCH (source {{id: $source_id}})
        MATCH (target {{id: $target_id}})
        CREATE (source)-[r:{relation}]->(target)
        SET r.valid_from = datetime($valid_from),
            r.valid_to = NULL,
            r.last_verified = datetime($now),
            r.verification_count = 1,
            r.source_url = $source_url,
            r.content_hash = $content_hash,
            r += $properties
        RETURN id(r) AS rel_id
        """
        
        result = tx.run(
            query,
            source_id=source_id,
            target_id=target_id,
            valid_from=valid_from.isoformat(),
            now=now.isoformat(),
            source_url=source_url,
            content_hash=content_hash,
            properties=properties,
        )
        
        record = result.single()
        return record["rel_id"] if record else None

    def invalidate_edge(
        self,
        source_node: str,
        relation_type: str,
        target_node: str,
    ) -> bool:
        """
        Invalidate an active temporal edge by setting valid_to to NOW.

        This is used when a relationship is no longer valid (detected by change detection).

        Args:
            source_node: Name of the source entity
            relation_type: Type of relationship
            target_node: Name of the target entity

        Returns:
            True if an edge was invalidated, False if no active edge found

        Raises:
            GraphException: If the operation fails
        """
        logger.info(
            "invalidating_edge",
            source=source_node,
            relation=relation_type,
            target=target_node,
        )

        try:
            with self.driver.session(database=self.database) as session:
                result = session.execute_write(
                    self._invalidate_edge_tx,
                    source_node,
                    relation_type,
                    target_node,
                )

                if result:
                    logger.info("edge_invalidated", relationship_id=result)
                else:
                    logger.warning("no_active_edge_to_invalidate")

                return result

        except Exception as e:
            logger.error("failed_to_invalidate_edge", error=str(e))
            raise GraphException(f"Failed to invalidate edge: {e}") from e

    @staticmethod
    def _invalidate_edge_tx(
        tx: ManagedTransaction,
        source_node: str,
        relation_type: str,
        target_node: str,
    ) -> Optional[int]:
        """
        Transaction function for invalidating an edge.
        """
        now = datetime.utcnow()

        query = f"""
        MATCH (source:Entity {{name: $source_name}})
              -[r:{relation_type}]->(target:Entity {{name: $target_name}})
        WHERE r.valid_to IS NULL
        SET r.valid_to = datetime($now)
        RETURN id(r) AS rel_id
        """

        result = tx.run(
            query,
            source_name=source_node,
            target_name=target_node,
            now=now.isoformat(),
        )

        record = result.single()
        return record["rel_id"] if record else None

    def get_active_relationships(
        self,
        entity_name: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Get all active relationships (valid_to is NULL).

        Args:
            entity_name: Optional entity name to filter by (source or target)

        Returns:
            List of relationship dictionaries with source, relation, target, and metadata

        Raises:
            GraphException: If the query fails
        """
        try:
            with self.driver.session(database=self.database) as session:
                if entity_name:
                    query = """
                    MATCH (source:Entity)-[r]->(target:Entity)
                    WHERE r.valid_to IS NULL
                      AND (source.name = $entity_name OR target.name = $entity_name)
                    RETURN source.name AS source,
                           type(r) AS relation,
                           target.name AS target,
                           r.valid_from AS valid_from,
                           r.last_verified AS last_verified,
                           r.confidence AS confidence,
                           r.source_url AS source_url
                    """
                    result = session.run(query, entity_name=entity_name)
                else:
                    query = """
                    MATCH (source:Entity)-[r]->(target:Entity)
                    WHERE r.valid_to IS NULL
                    RETURN source.name AS source,
                           type(r) AS relation,
                           target.name AS target,
                           r.valid_from AS valid_from,
                           r.last_verified AS last_verified,
                           r.confidence AS confidence,
                           r.source_url AS source_url
                    """
                    result = session.run(query)

                relationships = []
                for record in result:
                    relationships.append({
                        "source": record["source"],
                        "relation": record["relation"],
                        "target": record["target"],
                        "valid_from": record["valid_from"],
                        "last_verified": record["last_verified"],
                        "confidence": record["confidence"],
                        "source_url": record["source_url"],
                    })

                return relationships

        except Exception as e:
            logger.error("failed_to_get_active_relationships", error=str(e))
            raise GraphException(f"Failed to get active relationships: {e}") from e

    def find_stale_nodes(self, days_threshold: int = 7) -> list[str]:
        """
        Find URLs that haven't been verified in > days_threshold days.
        
        Phase 4: Autonomous Healing
        This identifies stale data that needs re-scraping.
        
        Args:
            days_threshold: Number of days after which a relationship is considered stale

        Returns:
            List of unique source URLs that need re-scraping

        Raises:
            GraphException: If the query fails
        """
        logger.info("finding_stale_nodes", days_threshold=days_threshold)

        try:
            with self.driver.session(database=self.database) as session:
                query = """
                MATCH (source:Entity)-[r]->(target:Entity)
                WHERE r.valid_to IS NULL
                  AND r.last_verified < datetime() - duration({days: $days_threshold})
                RETURN DISTINCT r.source_url AS source_url,
                       r.last_verified AS last_verified,
                       count(r) AS stale_count
                ORDER BY r.last_verified ASC
                """

                result = session.run(query, days_threshold=days_threshold)

                stale_urls = []
                for record in result:
                    url = record["source_url"]
                    if url:  # Filter out None values
                        stale_urls.append(url)
                        logger.debug(
                            "found_stale_url",
                            url=url,
                            last_verified=record["last_verified"],
                            stale_count=record["stale_count"],
                        )

                logger.info(
                    "stale_nodes_found",
                    count=len(stale_urls),
                    days_threshold=days_threshold,
                )

                return stale_urls

        except Exception as e:
            logger.error("failed_to_find_stale_nodes", error=str(e))
            raise GraphException(f"Failed to find stale nodes: {e}") from e

    def get_graph_snapshot(
        self,
        timestamp: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """
        Get a snapshot of the knowledge graph at a specific point in time.

        This implements time-travel queries by retrieving all nodes and edges
        that were valid at the given timestamp.

        Args:
            timestamp: Point in time to query (defaults to now)

        Returns:
            Dictionary with:
                - nodes: List of node objects for react-force-graph-3d
                - links: List of link objects for react-force-graph-3d
                - metadata: Additional information about the snapshot

        Raises:
            GraphException: If the query fails
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        logger.info("getting_graph_snapshot", timestamp=timestamp.isoformat())

        try:
            with self.driver.session(database=self.database) as session:
                # Query for edges valid at the timestamp
                query = """
                MATCH (source:Entity)-[r]->(target:Entity)
                WHERE r.valid_from <= datetime($timestamp)
                  AND (r.valid_to >= datetime($timestamp) OR r.valid_to IS NULL)
                RETURN source.name AS source_name,
                       target.name AS target_name,
                       type(r) AS relation_type,
                       r.valid_from AS valid_from,
                       r.valid_to AS valid_to,
                       r.confidence AS confidence,
                       r.source_url AS source_url,
                       r.last_verified AS last_verified
                """

                result = session.run(query, timestamp=timestamp.isoformat())

                # Build nodes and links for react-force-graph-3d
                nodes_dict = {}  # Use dict to avoid duplicates
                links = []

                for record in result:
                    source_name = record["source_name"]
                    target_name = record["target_name"]
                    relation_type = record["relation_type"]

                    # Add source node if not already present
                    if source_name not in nodes_dict:
                        nodes_dict[source_name] = {
                            "id": source_name,
                            "name": source_name,
                            "val": 1,  # Node size
                        }

                    # Add target node if not already present
                    if target_name not in nodes_dict:
                        nodes_dict[target_name] = {
                            "id": target_name,
                            "name": target_name,
                            "val": 1,
                        }

                    # Helper to safely convert dates
                    def to_iso(dt):
                        if dt is None:
                            return None
                        if hasattr(dt, 'iso_format'):
                            return dt.iso_format()
                        if hasattr(dt, 'isoformat'):
                            return dt.isoformat()
                        return str(dt)

                    # Add link
                    links.append({
                        "source": source_name,
                        "target": target_name,
                        "relation": relation_type,
                        "confidence": record["confidence"],
                        "source_url": record["source_url"],
                        "valid_from": to_iso(record["valid_from"]),
                        "valid_to": to_iso(record["valid_to"]),
                        "last_verified": to_iso(record["last_verified"]),
                    })

                # Convert nodes dict to list
                nodes = list(nodes_dict.values())

                logger.info(
                    "graph_snapshot_retrieved",
                    timestamp=timestamp.isoformat(),
                    num_nodes=len(nodes),
                    num_links=len(links),
                )

                return {
                    "nodes": nodes,
                    "links": links,
                    "metadata": {
                        "timestamp": timestamp.isoformat(),
                        "node_count": len(nodes),
                        "link_count": len(links),
                    },
                }

        except Exception as e:
            logger.error("failed_to_get_graph_snapshot", error=str(e))
            raise GraphException(f"Failed to get graph snapshot: {e}") from e

    def get_document_state(self, url: str) -> Optional[str]:
        """
        Get the last known content hash for a document (URL).

        Args:
            url: The URL of the document

        Returns:
            The SHA-256 hash of the content when it was last processed, or None if not found.
        """
        try:
            with self.driver.session(database=self.database) as session:
                query = """
                MATCH (d:Document {url: $url})
                RETURN d.last_content_hash as hash
                """
                result = session.run(query, url=url)
                record = result.single()
                return record["hash"] if record else None
        except Exception as e:
            logger.error("failed_to_get_document_state", url=url, error=str(e))
            return None

    def update_document_state(self, url: str, content_hash: str) -> None:
        """
        Update the content hash for a document (URL).

        Args:
            url: The URL of the document
            content_hash: The new SHA-256 hash of the content
        """
        try:
            with self.driver.session(database=self.database) as session:
                query = """
                MERGE (d:Document {url: $url})
                SET d.last_content_hash = $hash,
                    d.last_updated = datetime()
                """
                session.run(query, url=url, hash=content_hash)
                logger.info("document_state_updated", url=url, hash=content_hash)
        except Exception as e:
            logger.error("failed_to_update_document_state", url=url, error=str(e))
            raise GraphException(f"Failed to update document state: {e}") from e

    def __enter__(self) -> GraphManager:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - close driver."""
        self.close()
