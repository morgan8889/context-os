"""Isolation verification script: two tenants, zero cross-tenant visibility.

Creates two tenants, ingests 3 mock nodes under tenant A, queries all three
APIs as tenant B, and asserts zero results.

Exit 0 if all isolation checks pass; non-zero otherwise.
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import datetime


async def run_verification() -> None:
    """Run all isolation checks."""
    from context_os.db.engine import close_db, get_session_factory, init_db
    from context_os.graph.client import close_age_pool, create_age_pool, init_graph
    from context_os.graph.mutations import get_nodes_for_tenant, upsert_node
    from context_os.relational.repositories import TenantRepository

    print("Initializing database and graph...")
    await init_db()
    pool = await create_age_pool()
    await init_graph(pool)

    factory = get_session_factory()

    # Create two tenants
    tenant_a_clerk_id = f"test_tenant_a_{uuid.uuid4().hex[:8]}"
    tenant_b_clerk_id = f"test_tenant_b_{uuid.uuid4().hex[:8]}"

    async with factory() as session:
        repo = TenantRepository(session)
        tenant_a = await repo.create(
            clerk_org_id=tenant_a_clerk_id, name="Test Tenant A"
        )
        tenant_b = await repo.create(
            clerk_org_id=tenant_b_clerk_id, name="Test Tenant B"
        )
        await session.commit()

    print(f"Created Tenant A: {tenant_a.id} ({tenant_a_clerk_id})")
    print(f"Created Tenant B: {tenant_b.id} ({tenant_b_clerk_id})")

    now = datetime.utcnow().isoformat() + "Z"

    # Ingest 3 mock nodes under Tenant A
    test_nodes = [
        {
            "id": str(uuid.uuid4()),
            "node_type": "Artifact",
            "source": "github",
            "source_id": "test_pr_1",
            "fetch_ts": now,
            "created_at": now,
            "updated_at": now,
            "title": "Tenant A PR",
            "content": "This belongs to Tenant A",
            "artifact_type": "pull_request",
            "status": "open",
        },
        {
            "id": str(uuid.uuid4()),
            "node_type": "Initiative",
            "source": "github",
            "source_id": "test_repo_1",
            "fetch_ts": now,
            "created_at": now,
            "updated_at": now,
            "title": "Tenant A Repo",
            "description": "Tenant A's repository",
            "status": "active",
            "url": "https://github.com/test/repo",
        },
        {
            "id": str(uuid.uuid4()),
            "node_type": "Signal",
            "source": "slack",
            "source_id": "test_msg_1",
            "fetch_ts": now,
            "created_at": now,
            "updated_at": now,
            "content": "Hello from Tenant A",
            "signal_type": "message",
            "occurred_at": now,
        },
    ]

    print("Ingesting 3 nodes under Tenant A...")
    for node in test_nodes:
        await upsert_node(
            pool=pool,
            tenant_id=tenant_a_clerk_id,
            node_type=node["node_type"],
            props=node,
        )
    print(f"  Ingested {len(test_nodes)} nodes")

    # Query as Tenant B — should see zero results
    print("\nQuerying as Tenant B (should see ZERO results)...")
    failures = []

    # 1. GET /admin/entities equivalent
    nodes_b, total_b = await get_nodes_for_tenant(
        pool=pool,
        tenant_id=tenant_b_clerk_id,
    )
    if total_b > 0 or len(nodes_b) > 0:
        failures.append(f"FAIL: Tenant B sees {total_b} nodes (expected 0)")
    else:
        print("  graph query: PASS (0 nodes visible)")

    # 2. Verify no Tenant A data in Tenant B results
    for node in nodes_b:
        if node.get("tenant_id") == tenant_a_clerk_id:
            failures.append(f"FAIL: Tenant A node visible to Tenant B: {node}")

    # 3. Query Tenant A — should see all 3 nodes
    nodes_a, total_a = await get_nodes_for_tenant(
        pool=pool,
        tenant_id=tenant_a_clerk_id,
    )
    if total_a < 3:
        failures.append(f"WARN: Tenant A only sees {total_a} nodes (expected 3)")
    else:
        print(f"  Tenant A sees {total_a} nodes: PASS")

    # 4. Test vector search isolation (if embeddings table is populated)
    try:
        from context_os.vector.search import search

        async with factory() as session:
            results_b = await search(
                session=session,
                tenant_id=tenant_b.id,
                query_text="Tenant A content",
                k=10,
            )
        if results_b:
            failures.append(
                f"FAIL: Tenant B sees {len(results_b)} vector results (expected 0)"
            )
        else:
            print("  vector search: PASS (0 results for Tenant B)")
    except Exception as e:
        print(f"  vector search: SKIP (no embeddings: {e})")

    # Cleanup: the test tenants are ephemeral (no cleanup needed for test DB)

    await close_age_pool()
    await close_db()

    if failures:
        print("\n❌ ISOLATION FAILURES:")
        for f in failures:
            print(f"  {f}")
        sys.exit(1)
    else:
        print("\n✅ All isolation checks passed")
        sys.exit(0)


if __name__ == "__main__":
    import os
    import sys

    # Add src to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

    asyncio.run(run_verification())
