"""Top-k semantic retrieval using pgvector cosine similarity.

Queries the node_embeddings table using the HNSW index for fast approximate
nearest neighbor search. Results are filtered by tenant_id and node_type.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from context_os.core.errors import TenantIsolationError, VectorSearchError
from context_os.db.models import NodeEmbedding
from context_os.vector.embeddings import get_embedding_model

logger = logging.getLogger(__name__)


def _assert_tenant_id(tenant_id: str | uuid.UUID | None) -> None:
    """Raise TenantIsolationError if tenant_id is empty or None.

    Args:
        tenant_id: Tenant identifier to validate.

    Raises:
        TenantIsolationError: If tenant_id is falsy or empty.
    """
    if not tenant_id:
        raise TenantIsolationError(
            code="tenant_isolation_error",
            message="tenant_id is required for vector search",
        )


@dataclass
class SearchResult:
    """Single semantic search result.

    Attributes:
        node_id: UUID string matching the AGE graph node id.
        node_type: Node type (Artifact, Memory).
        content: Text that was embedded.
        distance: Cosine distance (0 = identical, 2 = opposite).
    """

    node_id: str
    node_type: str
    content: str
    distance: float


async def search(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    query_text: str,
    k: int = 5,
    node_types: list[str] | None = None,
) -> list[SearchResult]:
    """Perform top-k semantic similarity search over node embeddings.

    Encodes the query text with the same model used during ingest,
    then retrieves the k nearest neighbors using cosine distance.

    Args:
        session: SQLAlchemy async session.
        tenant_id: Internal tenant UUID — MUST be non-empty.
        query_text: Natural language query to embed and search.
        k: Number of results to return (default 5, max 50).
        node_types: Optional list of node types to filter on.
                    Defaults to ["Artifact", "Memory"].

    Returns:
        List of SearchResult ordered by ascending cosine distance.

    Raises:
        TenantIsolationError: If tenant_id is empty.
        VectorSearchError: If the database query fails.
    """
    _assert_tenant_id(tenant_id)

    if not node_types:
        node_types = ["Artifact", "Memory"]

    # Encode query text using the same model as ingest
    try:
        query_embedding = get_embedding_model().encode(query_text)
    except Exception as e:
        raise VectorSearchError(
            code="vector_search_error",
            message=f"Failed to encode query text: {e}",
        ) from e

    # Build SQL query using pgvector cosine distance operator (<=>)
    # SQLAlchemy ORM approach with the Vector column type
    try:
        stmt = (
            select(
                NodeEmbedding.id,
                NodeEmbedding.node_type,
                NodeEmbedding.content,
                NodeEmbedding.embedding.cosine_distance(query_embedding).label(
                    "distance"
                ),  # type: ignore[attr-defined]
            )
            .where(
                NodeEmbedding.tenant_id == tenant_id,
                NodeEmbedding.node_type.in_(node_types),
                NodeEmbedding.embedding.is_not(None),
            )
            .order_by(text("distance"))
            .limit(k)
        )

        result = await session.execute(stmt)
        rows = result.fetchall()

    except Exception as e:
        logger.error(
            "Vector search failed: tenant=%s k=%d error=%s",
            tenant_id,
            k,
            e,
        )
        raise VectorSearchError(
            code="vector_search_error",
            message=f"Vector search query failed: {e}",
        ) from e

    results = []
    for row in rows:
        results.append(
            SearchResult(
                node_id=str(row.id),
                node_type=row.node_type,
                content=row.content,
                distance=float(row.distance) if row.distance is not None else 1.0,
            )
        )

    logger.debug(
        "Vector search complete: tenant=%s k=%d results=%d",
        tenant_id,
        k,
        len(results),
    )

    return results
