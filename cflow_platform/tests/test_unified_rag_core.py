from __future__ import annotations

import asyncio


def test_unified_enterprise_rag_build_index_payload_smoke():
    from cflow_platform.core.services.unified_enterprise_rag import UnifiedEnterpriseRAG

    rag = UnifiedEnterpriseRAG()

    async def _run():
        corpus = [
            {"id": "1", "content": "alpha beta"},
            {"id": "2", "content": "gamma delta"},
        ]
        docs, vecs, metas = await rag.build_index_payload(corpus)
        assert isinstance(docs, list) and len(docs) == 2
        assert isinstance(vecs, list) and len(vecs) == 2
        assert isinstance(vecs[0], list) and len(vecs[0]) > 0
        assert isinstance(metas, list) and len(metas) == 2

    asyncio.run(_run())


