"""Apache AGE asyncpg pool and Cypher query helper.

Key decisions from research.md:
- statement_cache_size=0: AGE requires this to avoid prepared statement errors
- init hook: LOAD 'age' + SET search_path on every connection
- Never use Python f-strings to inject user values into Cypher — use AGE param map
"""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from typing import Any

import asyncpg

from context_os.config import get_settings

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None  # type: ignore[type-arg]


async def _age_setup(conn: asyncpg.Connection) -> None:  # type: ignore[type-arg]
    """Initialize AGE on each new connection in the pool.

    Runs LOAD 'age' and sets search_path so AGE functions are visible.
    This is required because AGE is a PostgreSQL extension that must be
    loaded per-connection — it cannot be loaded at the session level via
    connection string parameters alone.

    Args:
        conn: New asyncpg connection from the pool.
    """
    await conn.execute("LOAD 'age'")
    await conn.execute('SET search_path = ag_catalog, "$user", public')


async def create_age_pool() -> asyncpg.Pool:  # type: ignore[type-arg]
    """Create and return an asyncpg connection pool configured for AGE.

    Uses statement_cache_size=0 (required by AGE) and sets up the init hook
    to load AGE and configure search_path on each new connection.

    Returns:
        Configured asyncpg Pool ready for Cypher queries.
    """
    global _pool
    settings = get_settings()

    # Convert SQLAlchemy URL to asyncpg DSN (strip +asyncpg driver qualifier)
    dsn = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")

    _pool = await asyncpg.create_pool(
        dsn=dsn,
        statement_cache_size=0,  # Required: AGE is incompatible with prepared stmts
        init=_age_setup,
        min_size=2,
        max_size=10,
    )
    logger.info("AGE asyncpg pool created")
    return _pool


async def close_age_pool() -> None:
    """Close the AGE connection pool on application shutdown."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("AGE asyncpg pool closed")


def get_age_pool() -> asyncpg.Pool:  # type: ignore[type-arg]
    """Return the initialized AGE pool.

    Raises:
        RuntimeError: If create_age_pool() has not been called.
    """
    if _pool is None:
        raise RuntimeError("AGE pool not initialized; call create_age_pool() first")
    return _pool


async def init_graph(
    pool: asyncpg.Pool,  # type: ignore[type-arg]
    graph_name: str = "context_os",
) -> None:
    """Create the AGE graph if it does not already exist.

    Args:
        pool: AGE-configured asyncpg pool.
        graph_name: Name of the AGE property graph to create.
    """
    async with pool.acquire() as conn:
        try:
            await conn.execute(f"SELECT create_graph('{graph_name}')")
            logger.info("AGE graph '%s' created", graph_name)
        except asyncpg.UniqueViolationError:
            logger.debug("AGE graph '%s' already exists", graph_name)
        except Exception as e:
            # Graph already exists raises a different error in some AGE versions
            if "already exists" in str(e).lower():
                logger.debug("AGE graph '%s' already exists", graph_name)
            else:
                raise


async def run_cypher(
    pool: asyncpg.Pool,  # type: ignore[type-arg]
    cypher: str,
    params: dict[str, Any] | None = None,
    graph_name: str = "context_os",
    columns: Sequence[tuple[str, str]] | None = None,
) -> list[dict[str, Any]]:
    """Execute a Cypher query against the AGE graph and return results.

    User-supplied values MUST be passed via the params dict (AGE parameter map),
    never interpolated directly into the Cypher string. This prevents injection.

    The Cypher query should use AGE parameter references like $param_name.

    Args:
        pool: AGE-configured asyncpg pool.
        cypher: Cypher query string. Use $param_name for user values.
        params: Dict of parameter values referenced in the Cypher query.
                These are passed as an AGE agtype parameter map.
        graph_name: AGE graph name (default: "context_os").
        columns: Optional list of (name, type) tuples for the AS clause.
                 Defaults to [("result", "agtype")] if not specified.

    Returns:
        List of dicts, one per result row.

    Example:
        results = await run_cypher(
            pool,
            "MATCH (n {id: $node_id, tenant_id: $tenant_id}) RETURN n",
            params={"node_id": "abc", "tenant_id": "org_123"},
        )
    """
    if columns is None:
        columns = [("result", "agtype")]

    col_clause = ", ".join(f"{name} {dtype}" for name, dtype in columns)

    if params:
        params_json = json.dumps(params)
        query = (
            f"SELECT * FROM cypher('{graph_name}', $$ {cypher} $$,"
            f" $1::agtype) AS ({col_clause})"
        )
    else:
        params_json = None
        query = (
            f"SELECT * FROM cypher('{graph_name}', $$ {cypher} $$) AS ({col_clause})"
        )

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *([params_json] if params_json else []))

    results = []
    for row in rows:
        row_dict: dict[str, Any] = {}
        for i, (col_name, _) in enumerate(columns):
            val = row[i]
            if isinstance(val, str):
                # AGE returns agtype as JSON-like strings; parse them
                try:
                    row_dict[col_name] = _parse_agtype(val)
                except (ValueError, json.JSONDecodeError):
                    row_dict[col_name] = val
            else:
                row_dict[col_name] = val
        results.append(row_dict)

    return results


def _parse_agtype(value: str | None) -> Any:
    """Parse an AGE agtype string value to a Python object.

    AGE returns values as agtype strings which are JSON-like but may include
    type annotations like '{"id": 1}::vertex'. Strip type annotations and
    parse as JSON.

    Args:
        value: Raw agtype string from AGE.

    Returns:
        Parsed Python value (dict, list, str, int, float, bool, or None).
    """
    if value is None:
        return None

    # Strip AGE type annotations (e.g. '::vertex', '::edge', '::path')
    if "::" in value:
        value = value[: value.rfind("::")]

    # Handle AGE NULL
    if value.strip().lower() == "null":
        return None

    return json.loads(value)
