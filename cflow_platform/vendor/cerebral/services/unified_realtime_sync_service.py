#!/usr/bin/env python3
import os
import sys
import json
import logging
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from chromadb import PersistentClient  # type: ignore
from chromadb.config import Settings  # type: ignore

logger = logging.getLogger("unified_sync")
logger.setLevel(getattr(logging, os.environ.get("CFLOW_SYNC_LOG_LEVEL", "INFO")))
_handler_path = os.environ.get("CFLOW_SYNC_LOG_FILE")
if _handler_path:
    _h = logging.FileHandler(_handler_path)
else:
    _h = logging.StreamHandler()
_h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(_h)


class UnifiedSync:
    def __init__(self, project_root: str) -> None:
        self.project_root = project_root
        self.supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
        self.supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY") or ""
        chroma_path = os.environ.get("CFLOW_CHROMADB_PATH") or str(Path(project_root) / ".cerebraflow" / "core" / "storage" / "chromadb")
        self.client = PersistentClient(path=chroma_path, settings=Settings(anonymized_telemetry=False, allow_reset=False))
        # Prefer platform embedder if available (used only for generation, not bound to Chroma)
        self.embedder = self._embedding_fn_or_none()
        if self.embedder is not None:
            try:
                name = getattr(self.embedder, "name", type(self.embedder).__name__)
            except Exception:
                name = type(self.embedder).__name__
            logger.info(f"embedding initialized: {name}")
        self.tasks = self.client.get_or_create_collection("cerebral_tasks")
        self.docs = self.client.get_or_create_collection("cerebral_docs")
        self.mem = self.client.get_or_create_collection("cerebral_mem")
        # Config
        self.tasks_table = os.environ.get("CFLOW_SUPABASE_TASKS_TABLE", "tasks")
        self.docs_table = os.environ.get("CFLOW_SUPABASE_DOCS_TABLE", "documentation_files")
        self.mem_table = os.environ.get("CFLOW_SUPABASE_MEM_TABLE", "project_memory")
        self.tenant_id = os.environ.get("CEREBRAL_TENANT_ID") or os.environ.get("CEREBRAFLOW_TENANT_ID")
        self.project_id = os.environ.get("CEREBRAL_PROJECT_ID") or os.environ.get("CEREBRAFLOW_PROJECT_ID")
        self.user_id = os.environ.get("CEREBRAL_USER_ID") or os.environ.get("CEREBRAFLOW_USER_ID")
        # State
        self._last_tasks_sync: Optional[str] = None
        self._last_docs_sync: Optional[str] = None
        # Flags
        self.skip_chroma_counts = os.environ.get("CFLOW_SYNC_SKIP_CHROMA_COUNTS", "0").lower() in {"1", "true", "yes"}
        # Pagination / batching
        try:
            self.page_size = int(os.environ.get("CFLOW_SYNC_PAGE_SIZE", "1000"))
        except Exception:
            self.page_size = 1000
        try:
            self.batch_size = int(os.environ.get("CFLOW_SYNC_BATCH_SIZE", "200"))
        except Exception:
            self.batch_size = 200
        # Vector sync (pgvector)
        self.vector_enabled = (os.environ.get("CFLOW_VECTOR_SYNC_ENABLED", "0").lower() in {"1", "true", "yes"})
        self._vector_tasks_env = os.environ.get("CFLOW_SUPABASE_TASKS_VECTOR_TABLE")
        self._vector_docs_env = os.environ.get("CFLOW_SUPABASE_DOCS_VECTOR_TABLE")
        self.vector_tasks_table = self._vector_tasks_env or self.tasks_table
        self.vector_docs_table = self._vector_docs_env or self.docs_table
        self.vector_column = os.environ.get("CFLOW_VECTOR_COLUMN", "embeddings")
        logger.info(f"vector_sync_enabled={self.vector_enabled} vector_column={self.vector_column}")

    def _embedding_fn_or_none(self):
        # Optional Apple Silicon-accelerated embeddings via local module or sentence-transformers
        try:
            # Allow skipping Apple MPS embedder via env for stability
            if os.environ.get("CFLOW_SKIP_APPLE_MPS", "0").lower() not in {"1", "true", "yes"}:
                try:
                    from cflow_platform.core.embeddings.apple_mps import get_embedder  # type: ignore
                    return get_embedder()
                except Exception:
                    pass
            if os.environ.get("CFLOW_APPLE_MPS", "1").lower() in {"1", "true", "yes"}:
                # Prefer MPS where available
                device = "mps"
            else:
                device = os.environ.get("CFLOW_EMBED_DEVICE", "cpu")
            from sentence_transformers import SentenceTransformer  # type: ignore
            model_name = os.environ.get("CFLOW_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
            model = SentenceTransformer(model_name, device=device)

            class _Embedder:
                def __call__(self, inputs):
                    if isinstance(inputs, str):
                        inputs_ = [inputs]
                    else:
                        inputs_ = inputs
                    vecs = model.encode(inputs_, show_progress_bar=False, normalize_embeddings=True)
                    return vecs.tolist()

            logger.info(f"embedding model initialized: {model_name} on {device}")
            return _Embedder()
        except Exception as e:
            logger.debug(f"no embedding function available: {e}")
            return None

    def _embedding_call(self, texts: List[str]) -> List[List[float]]:
        # Resolve embedder on-demand and support multiple APIs
        if self.embedder is None:
            try:
                from cflow_platform.core.embeddings.apple_mps import get_embedder  # type: ignore
                if os.environ.get("CFLOW_SKIP_APPLE_MPS", "0").lower() in {"1", "true", "yes"}:
                    raise RuntimeError("skipping apple mps embedder by env")
                self.embedder = get_embedder()
            except Exception:
                self.embedder = None
        if self.embedder is None:
            raise RuntimeError("embedding function not available")
        try:
            # sentence-transformers style callable
            if callable(self.embedder):  # type: ignore[call-arg]
                return self.embedder(texts)  # type: ignore[misc]
            # Enhanced accelerator with generate_embeddings
            if hasattr(self.embedder, "generate_embeddings"):
                return getattr(self.embedder, "generate_embeddings")(texts)  # type: ignore[no-any-return]
            raise RuntimeError("unsupported embedder interface")
        except Exception as e:
            raise RuntimeError(f"embedder call failed: {e}")

    def _headers(self) -> Dict[str, str]:
        return {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates",
        }

    async def _sb_get(self, path: str, params: Dict[str, Any]) -> httpx.Response:
        url = self.supabase_url + path
        logger.debug(f"HTTP GET {url} params={params}")
        async with httpx.AsyncClient(timeout=12) as s:
            r = await s.get(url, headers=self._headers(), params=params)
        logger.debug(f"HTTP GET {url} -> {r.status_code}")
        return r

    async def _sb_upsert(self, table: str, rows: List[Dict[str, Any]]) -> httpx.Response:
        # Use on_conflict=id when available to ensure UPSERT semantics on PK
        base = self.supabase_url + f"/rest/v1/{table}"
        use_on_conflict = bool(rows and isinstance(rows[0], dict) and ("id" in rows[0]))
        url = base + ("?on_conflict=id" if use_on_conflict else "")
        logger.debug(f"HTTP POST {url} rows={len(rows)} keys={sorted(list(rows[0].keys())) if rows else []}")
        async with httpx.AsyncClient(timeout=12) as s:
            r = await s.post(url, headers=self._headers(), content=json.dumps(rows))
        logger.debug(f"HTTP POST {url} -> {r.status_code} body={r.text[:200] if r.text else ''}")
        return r

    async def _sb_patch_embedding(self, table: str, row_id: str, vector_column: str, embedding: List[float]) -> httpx.Response:
        url = self.supabase_url + f"/rest/v1/{table}?id=eq.{row_id}"
        payload = {vector_column: embedding}
        async with httpx.AsyncClient(timeout=12) as s:
            r = await s.patch(url, headers=self._headers(), content=json.dumps(payload))
        return r

    def _with_meta(self, base: Dict[str, Any]) -> Dict[str, Any]:
        meta = self._scalarize_metadata(dict(base))
        if self.tenant_id:
            meta.setdefault("tenant_id", self.tenant_id)
        if self.project_id:
            meta.setdefault("project_id", self.project_id)
        if self.user_id:
            meta.setdefault("user_id", self.user_id)
        return meta

    def _sanitize_chroma_metadata(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        # Ensure all values are strictly scalar and non-None
        sanitized: Dict[str, Any] = {}
        for k, v in meta.items():
            if v is None:
                continue
            if isinstance(v, (str, int, float, bool)):
                sanitized[k] = v
            else:
                try:
                    sanitized[k] = str(v)
                except Exception:
                    continue
        return sanitized

    def _scalarize_metadata(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        clean: Dict[str, Any] = {}
        for k, v in meta.items():
            if v is None:
                # Drop None values entirely to satisfy Chroma metadata constraints
                continue
            if isinstance(v, (str, int, float, bool)):
                clean[k] = v
            elif isinstance(v, (list, dict)):
                try:
                    if not v:
                        # drop empty lists/dicts
                        continue
                    clean[k] = json.dumps(v)
                except Exception:
                    clean[k] = str(v)
            else:
                clean[k] = str(v)
        return clean

    def _whitelist_task_meta(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        keys = {
            "id", "task_id", "status", "priority", "title", "category",
            "tenant_id", "project_id", "user_id", "created_at", "updated_at",
        }
        return {k: meta.get(k) for k in keys if meta.get(k) is not None}

    def _whitelist_doc_meta(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        keys = {
            "id", "doc_id", "source", "path", "content_type",
            "knowledge_base", "tenant_id", "project_id", "user_id",
            "created_at", "updated_at",
        }
        return {k: meta.get(k) for k in keys if meta.get(k) is not None}

    async def discover_tables(self) -> None:
        if not (self.supabase_url and self.supabase_key):
            return
        candidates_tasks = [
            self.tasks_table,
            "cerebraflow_tasks", "cerebral_tasks", "cflow_tasks",
            "tasks_items", "tasks", "task_items",
        ]
        candidates_docs = [
            self.docs_table,
            "documentation_files", "cerebral_docs", "cerebraflow_docs", "cflow_docs",
            "knowledge_rag", "rag_documents",
        ]
        candidates_mem = [
            self.mem_table,
            "project_memory", "cerebral_memory", "cerebraflow_memory", "cflow_memory", "memory"
        ]
        async with httpx.AsyncClient(timeout=10) as s:
            # tasks
            for t in [x for x in candidates_tasks if x]:
                try:
                    r = await s.get(self.supabase_url + f"/rest/v1/{t}", headers=self._headers(), params={"select": "id", "limit": 1})
                    if r.status_code == 200:
                        self.tasks_table = t
                        logger.info(f"discovered tasks table: {t}")
                        break
                except Exception:
                    pass
            # docs
            for d in [x for x in candidates_docs if x]:
                try:
                    r = await s.get(self.supabase_url + f"/rest/v1/{d}", headers=self._headers(), params={"select": "id", "limit": 1})
                    if r.status_code == 200:
                        self.docs_table = d
                        logger.info(f"discovered docs table: {d}")
                        break
                except Exception:
                    pass
            # memory
            for m in [x for x in candidates_mem if x]:
                try:
                    r = await s.get(self.supabase_url + f"/rest/v1/{m}", headers=self._headers(), params={"select": "id", "limit": 1})
                    if r.status_code == 200:
                        self.mem_table = m
                        logger.info(f"discovered memory table: {m}")
                        break
                except Exception:
                    pass
        # If nothing discovered, fall back to plausible defaults instead of "tasks"
        if not self.tasks_table or self.tasks_table == "tasks":
            self.tasks_table = "cerebral_tasks"
        if not self.docs_table or self.docs_table == "documentation_files":
            # Keep documentation_files if it exists; otherwise prefer cerebral_docs
            try:
                async with httpx.AsyncClient(timeout=5) as s:
                    r = await s.get(self.supabase_url + f"/rest/v1/{self.docs_table}", headers=self._headers(), params={"select": "id", "limit": 1})
                if r.status_code != 200:
                    self.docs_table = "cerebral_docs"
            except Exception:
                self.docs_table = "cerebral_docs"
        # Align vector tables with discovered names unless explicitly overridden by env
        if not self._vector_tasks_env:
            self.vector_tasks_table = self.tasks_table
        if not self._vector_docs_env:
            self.vector_docs_table = self.docs_table
        logger.info(f"vector targets tasks={self.vector_tasks_table} docs={self.vector_docs_table} column={self.vector_column}")

    async def _get_table_columns(self, table: str) -> List[str]:
        # Probe one row to infer column names
        try:
            r = await self._sb_get(f"/rest/v1/{table}", {"select": "*", "limit": 1})
            if r.status_code == 200:
                data = r.json() or []
                if isinstance(data, list) and data:
                    first = data[0]
                    if isinstance(first, dict):
                        return list(first.keys())
        except Exception:
            pass
        return []

    async def sync_tasks_pull(self) -> int:
        logger.debug("sync_tasks_pull enter")
        if not (self.supabase_url and self.supabase_key):
            return 0
        total_fetched = 0
        upserted = 0
        latest_updated: Optional[str] = None
        offset = 0
        while True:
            params: Dict[str, Any] = {"select": "*", "limit": self.page_size}
            if self._last_tasks_sync:
                params["updated_at"] = f"gte.{self._last_tasks_sync}"
                params["order"] = "updated_at.asc"
            else:
                params["order"] = "updated_at.desc"
                params["offset"] = offset
            r = await self._sb_get(f"/rest/v1/{self.tasks_table}", params)
            if r.status_code != 200:
                logger.warning(f"tasks pull failed: {r.status_code} {r.text}")
                break
            try:
                rows = r.json() or []
            except Exception as e:
                logger.warning(f"tasks pull json decode failed: {e}")
                break
            fetched = len(rows)
            total_fetched += fetched
            logger.debug(f"tasks pull page fetched={fetched} total={total_fetched} offset={offset}")
            if not rows:
                break
            for row in rows:
                try:
                    tid = str(row.get("id") or row.get("task_id") or row.get("uuid") or row.get("_id") or "")
                    if not tid:
                        continue
                    title = str(row.get("title") or "")
                    desc = str(row.get("description") or "")
                    doc = f"{title}\n{desc}"
                    try:
                        self.tasks.delete(ids=[tid])  # type: ignore
                    except Exception:
                        pass
                    try:
                        self.tasks.add(ids=[tid], documents=[doc])  # type: ignore
                        upserted += 1
                    except Exception as e:
                        logger.debug(f"tasks chroma add failed; tid={tid} err={e}")
                    upd = row.get("updated_at")
                    if isinstance(upd, str):
                        latest_updated = max(latest_updated or upd, upd)
                except Exception as e:
                    logger.debug(f"tasks pull upsert error: {e}")
            if self._last_tasks_sync:
                break
            if fetched < self.page_size:
                break
            offset += self.page_size
            await asyncio.sleep(0)
        if latest_updated:
            self._last_tasks_sync = latest_updated
        logger.info(f"tasks pull upserted={upserted}")
        return upserted

    async def sync_docs_pull(self) -> int:
        logger.debug("sync_docs_pull enter")
        if not (self.supabase_url and self.supabase_key):
            return 0
        total_fetched = 0
        upserted = 0
        latest_updated: Optional[str] = None
        offset = 0
        while True:
            params: Dict[str, Any] = {"select": "*", "limit": self.page_size}
            if self._last_docs_sync:
                params["updated_at"] = f"gte.{self._last_docs_sync}"
                params["order"] = "updated_at.asc"
            else:
                params["order"] = "updated_at.desc"
                params["offset"] = offset
            r = await self._sb_get(f"/rest/v1/{self.docs_table}", params)
            if r.status_code != 200:
                logger.warning(f"docs pull failed: {r.status_code} {r.text}")
                break
            try:
                rows = r.json() or []
            except Exception as e:
                logger.warning(f"docs pull json decode failed: {e}")
                break
            fetched = len(rows)
            total_fetched += fetched
            logger.debug(f"docs pull page fetched={fetched} total={total_fetched} offset={offset}")
            if not rows:
                break
            batch_ids: List[str] = []
            batch_docs: List[str] = []
            for row in rows:
                try:
                    did = str(row.get("id") or row.get("doc_id") or row.get("uuid") or row.get("_id") or "")
                    if not did:
                        continue
                    content = str(row.get("content") or row.get("document") or "")
                    batch_ids.append(did)
                    batch_docs.append(content)
                    if len(batch_ids) >= self.batch_size:
                        try:
                            self.docs.delete(ids=batch_ids)  # type: ignore
                        except Exception:
                            pass
                        try:
                            self.docs.add(ids=batch_ids, documents=batch_docs)  # type: ignore
                            upserted += len(batch_ids)
                        except Exception as e:
                            logger.debug(f"docs batch add failed size={len(batch_ids)} err={e}")
                        batch_ids, batch_docs = [], []
                        await asyncio.sleep(0)
                    upd = row.get("updated_at")
                    if isinstance(upd, str):
                        latest_updated = max(latest_updated or upd, upd)
                except Exception as e:
                    logger.debug(f"docs pull upsert error: {e}")
            if batch_ids:
                try:
                    self.docs.delete(ids=batch_ids)  # type: ignore
                except Exception:
                    pass
                try:
                    self.docs.add(ids=batch_ids, documents=batch_docs)  # type: ignore
                    upserted += len(batch_ids)
                except Exception as e:
                    logger.debug(f"docs final batch add failed size={len(batch_ids)} err={e}")
            if self._last_docs_sync:
                break
            if fetched < self.page_size:
                break
            offset += self.page_size
            await asyncio.sleep(0)
        if latest_updated:
            self._last_docs_sync = latest_updated
        logger.info(f"docs pull upserted={upserted}")
        return upserted

    async def sync_mem_pull(self) -> int:
        logger.debug("sync_mem_pull enter")
        if not (self.supabase_url and self.supabase_key):
            return 0
        total_fetched = 0
        upserted = 0
        latest_updated: Optional[str] = None
        offset = 0
        while True:
            params: Dict[str, Any] = {"select": "*", "limit": self.page_size}
            if self._last_docs_sync:
                params["updated_at"] = f"gte.{self._last_docs_sync}"
                params["order"] = "updated_at.asc"
            else:
                params["order"] = "updated_at.desc"
                params["offset"] = offset
            r = await self._sb_get(f"/rest/v1/{self.mem_table}", params)
            if r.status_code != 200:
                logger.warning(f"mem pull failed: {r.status_code} {r.text}")
                break
            try:
                rows = r.json() or []
            except Exception as e:
                logger.warning(f"mem pull json decode failed: {e}")
                break
            fetched = len(rows)
            total_fetched += fetched
            logger.debug(f"mem pull page fetched={fetched} total={total_fetched} offset={offset}")
            if not rows:
                break
            batch_ids: List[str] = []
            batch_docs: List[str] = []
            for row in rows:
                try:
                    mid = str(row.get("id") or row.get("mem_id") or row.get("uuid") or row.get("_id") or "")
                    if not mid:
                        continue
                    content = str(row.get("content") or row.get("text") or row.get("value") or "")
                    batch_ids.append(mid)
                    batch_docs.append(content)
                    if len(batch_ids) >= self.batch_size:
                        try:
                            self.mem.delete(ids=batch_ids)  # type: ignore
                        except Exception:
                            pass
                        try:
                            self.mem.add(ids=batch_ids, documents=batch_docs)  # type: ignore
                            upserted += len(batch_ids)
                        except Exception as e:
                            logger.debug(f"mem batch add failed size={len(batch_ids)} err={e}")
                        batch_ids, batch_docs = [], []
                        await asyncio.sleep(0)
                    upd = row.get("updated_at")
                    if isinstance(upd, str):
                        latest_updated = max(latest_updated or upd, upd)
                except Exception as e:
                    logger.debug(f"mem pull upsert error: {e}")
            if batch_ids:
                try:
                    self.mem.delete(ids=batch_ids)  # type: ignore
                except Exception:
                    pass
                try:
                    self.mem.add(ids=batch_ids, documents=batch_docs)  # type: ignore
                    upserted += len(batch_ids)
                except Exception as e:
                    logger.debug(f"mem final batch add failed size={len(batch_ids)} err={e}")
            if self._last_docs_sync:
                break
            if fetched < self.page_size:
                break
            offset += self.page_size
            await asyncio.sleep(0)
        if latest_updated:
            self._last_docs_sync = latest_updated
        logger.info(f"mem pull upserted={upserted}")
        return upserted

    async def sync_tasks_push(self) -> int:
        # Push a small batch of local tasks to Supabase
        if not (self.supabase_url and self.supabase_key):
            return 0
        pushed = 0
        try:
            res = self.tasks.get(limit=200)  # type: ignore
            ids = res.get("ids") or []
            docs = res.get("documents") or []
            metas = res.get("metadatas") or []
            rows: List[Dict[str, Any]] = []
            for i, tid in enumerate(ids):
                meta = metas[i] if i < len(metas) else {}
                doc = docs[i] if i < len(docs) else ""
                # Map to Supabase row
                row = self._scalarize_metadata(self._whitelist_task_meta(dict(meta)))
                if "id" not in row and "task_id" not in row:
                    row["id"] = tid
                if "title" not in row and isinstance(doc, str):
                    first = doc.splitlines()[0] if doc else ""
                    row.setdefault("title", first[:200])
                row.setdefault("description", "\n".join(doc.splitlines()[1:]) if isinstance(doc, str) else "")
                rows.append(self._with_meta(row))
            if rows:
                # Enforce uniform keys across all rows for PostgREST
                key_sets = [set(r0.keys()) for r0 in rows if isinstance(r0, dict)]
                common_keys = set.intersection(*key_sets) if key_sets else set()
                # Ensure identifiers exist in common keys
                for must in ("id", "task_id"):
                    if any(must in r0 for r0 in rows):
                        common_keys.add(must)
                payload = [{k: r0.get(k) for k in common_keys} for r0 in rows]
                # Reduce further to table-real columns if we can infer them
                cols = await self._get_table_columns(self.tasks_table)
                if cols:
                    colset = set(cols)
                    payload = [{k: r0.get(k) for k in common_keys if k in colset} for r0 in rows]
                r = await self._sb_upsert(self.tasks_table, payload)
                if r.status_code in (200, 201, 204):
                    pushed = len(payload)
                else:
                    logger.warning(f"tasks push failed: {r.status_code} {r.text}")
        except Exception as e:
            logger.debug(f"tasks push error: {e}")
        logger.info(f"tasks push pushed={pushed}")
        return pushed

    async def sync_docs_push(self) -> int:
        if not (self.supabase_url and self.supabase_key):
            return 0
        pushed = 0
        try:
            res = self.docs.get(limit=200)  # type: ignore
            ids = res.get("ids") or []
            docs = res.get("documents") or []
            metas = res.get("metadatas") or []
            rows: List[Dict[str, Any]] = []
            for i, did in enumerate(ids):
                meta = metas[i] if i < len(metas) else {}
                doc = docs[i] if i < len(docs) else ""
                row = self._scalarize_metadata(self._whitelist_doc_meta(dict(meta)))
                if "id" not in row and "doc_id" not in row:
                    row["id"] = did
                row.setdefault("content", doc)
                rows.append(self._with_meta(row))
            if rows:
                key_sets = [set(r0.keys()) for r0 in rows if isinstance(r0, dict)]
                common_keys = set.intersection(*key_sets) if key_sets else set()
                for must in ("id", "doc_id"):
                    if any(must in r0 for r0 in rows):
                        common_keys.add(must)
                payload = [{k: r0.get(k) for k in common_keys} for r0 in rows]
                cols = await self._get_table_columns(self.docs_table)
                if cols:
                    colset = set(cols)
                    payload = [{k: r0.get(k) for k in common_keys if k in colset} for r0 in rows]
                r = await self._sb_upsert(self.docs_table, payload)
                if r.status_code in (200, 201, 204):
                    pushed = len(payload)
                else:
                    logger.warning(f"docs push failed: {r.status_code} {r.text}")
        except Exception as e:
            logger.debug(f"docs push error: {e}")
        logger.info(f"docs push pushed={pushed}")
        return pushed

    async def sync_vectors_push(self) -> Dict[str, int]:
        pushed: Dict[str, int] = {"tasks": 0, "docs": 0}
        logger.info("sync_vectors_push enter")
        if not (self.vector_enabled and self.supabase_url and self.supabase_key):
            logger.info("vector sync disabled or missing supabase config")
            return pushed
        # Verify target tables/columns support vector column
        try:
            t_cols = await self._get_table_columns(self.vector_tasks_table)
            d_cols = await self._get_table_columns(self.vector_docs_table)
        except Exception:
            t_cols, d_cols = [], []
        if self.vector_column not in (t_cols or []):
            logger.warning(f"skip tasks vector push; column '{self.vector_column}' missing on table '{self.vector_tasks_table}' (cols={t_cols})")
        if self.vector_column not in (d_cols or []):
            logger.warning(f"skip docs vector push; column '{self.vector_column}' missing on table '{self.vector_docs_table}' (cols={d_cols})")
        # Tasks vectors (compute from Supabase rows)
        try:
            limit = int(os.environ.get("CFLOW_VECTOR_LIMIT", str(self.batch_size)))
            params: Dict[str, Any] = {"select": "id,title,description", "limit": limit}
            if os.environ.get("CFLOW_VECTOR_REFRESH", "0").lower() not in {"1", "true", "yes"}:
                params["embeddings"] = "is.null"
            r = await self._sb_get(f"/rest/v1/{self.vector_tasks_table}", params)
            if r.status_code != 200:
                logger.warning(f"tasks vector source fetch failed: {r.status_code} {r.text}")
            else:
                src = r.json() or []
                rows: List[Dict[str, Any]] = []
                for row in src:
                    try:
                        tid = row.get("id")
                        title = row.get("title") or ""
                        desc = row.get("description") or ""
                        doc = f"{title}\n{desc}".strip()
                        if not doc:
                            continue
                        emb = self._embedding_call([doc])[0]
                        if isinstance(emb, list):
                            rows.append({"id": tid, self.vector_column: emb})
                    except Exception:
                        continue
                # Inject required IDs (e.g., project_id/tenant_id) if columns exist
                if rows:
                    try:
                        if "project_id" in (t_cols or []) and self.project_id:
                            for r0 in rows:
                                r0.setdefault("project_id", self.project_id)
                        if "tenant_id" in (t_cols or []) and self.tenant_id:
                            for r0 in rows:
                                r0.setdefault("tenant_id", self.tenant_id)
                        if "user_id" in (t_cols or []) and self.user_id:
                            for r0 in rows:
                                r0.setdefault("user_id", self.user_id)
                    except Exception:
                        pass
                pushed_count = 0
                if rows:
                    # Prefer per-row PATCH to avoid NOT NULL on other columns
                    for r0 in rows:
                        rid = r0.get("id")
                        emb = r0.get(self.vector_column)
                        if not rid or not isinstance(emb, list):
                            continue
                        r2 = await self._sb_patch_embedding(self.vector_tasks_table, rid, self.vector_column, emb)
                        if r2.status_code in (200, 204):
                            pushed_count += 1
                        else:
                            logger.warning(f"tasks vector patch failed: {r2.status_code} {r2.text}")
                pushed["tasks"] = pushed_count
                logger.info(f"tasks vectors: prepared={len(rows)} pushed={pushed['tasks']}")
        except Exception as e:
            logger.info(f"tasks vectors push error: {e}")
        # Docs vectors (compute from Supabase rows)
        try:
            limit = int(os.environ.get("CFLOW_VECTOR_LIMIT", str(self.batch_size)))
            params: Dict[str, Any] = {"select": "id,content", "limit": limit}
            if os.environ.get("CFLOW_VECTOR_REFRESH", "0").lower() not in {"1", "true", "yes"}:
                params["embeddings"] = "is.null"
            r = await self._sb_get(f"/rest/v1/{self.vector_docs_table}", params)
            if r.status_code != 200:
                logger.warning(f"docs vector source fetch failed: {r.status_code} {r.text}")
            else:
                src = r.json() or []
                rows: List[Dict[str, Any]] = []
                for row in src:
                    try:
                        did = row.get("id")
                        content = row.get("content") or ""
                        if not isinstance(content, str) or not content.strip():
                            continue
                        emb = self._embedding_call([content])[0]
                        if isinstance(emb, list):
                            rows.append({"id": did, self.vector_column: emb})
                    except Exception:
                        continue
                # Inject required IDs (e.g., tenant_id/project_id) if columns exist
                if rows:
                    try:
                        if "tenant_id" in (d_cols or []) and self.tenant_id:
                            for r0 in rows:
                                r0.setdefault("tenant_id", self.tenant_id)
                        if "project_id" in (d_cols or []) and self.project_id:
                            for r0 in rows:
                                r0.setdefault("project_id", self.project_id)
                        if "user_id" in (d_cols or []) and self.user_id:
                            for r0 in rows:
                                r0.setdefault("user_id", self.user_id)
                    except Exception:
                        pass
                pushed_count = 0
                if rows:
                    for r0 in rows:
                        rid = r0.get("id")
                        emb = r0.get(self.vector_column)
                        if not rid or not isinstance(emb, list):
                            continue
                        r2 = await self._sb_patch_embedding(self.vector_docs_table, rid, self.vector_column, emb)
                        if r2.status_code in (200, 204):
                            pushed_count += 1
                        else:
                            logger.warning(f"docs vector patch failed: {r2.status_code} {r2.text}")
                pushed["docs"] = pushed_count
                logger.info(f"docs vectors: prepared={len(rows)} pushed={pushed['docs']}")
        except Exception as e:
            logger.info(f"docs vectors push error: {e}")
        logger.info(f"vectors push pushed={json.dumps(pushed)}")
        return pushed

    async def sync_mem_push(self) -> int:
        if not (self.supabase_url and self.supabase_key):
            return 0
        pushed = 0
        try:
            res = self.mem.get(limit=200)  # type: ignore
            ids = res.get("ids") or []
            docs = res.get("documents") or []
            metas = res.get("metadatas") or []
            rows: List[Dict[str, Any]] = []
            for i, mid in enumerate(ids):
                meta = metas[i] if i < len(metas) else {}
                doc = docs[i] if i < len(docs) else ""
                row = self._scalarize_metadata(dict(meta))
                if "id" not in row and "mem_id" not in row:
                    row["id"] = mid
                row.setdefault("content", doc)
                rows.append(self._with_meta(row))
            if rows:
                key_sets = [set(r0.keys()) for r0 in rows if isinstance(r0, dict)]
                common_keys = set.intersection(*key_sets) if key_sets else set()
                for must in ("id", "mem_id"):
                    if any(must in r0 for r0 in rows):
                        common_keys.add(must)
                payload = [{k: r0.get(k) for k in common_keys} for r0 in rows]
                cols = await self._get_table_columns(self.mem_table)
                if cols:
                    colset = set(cols)
                    payload = [{k: r0.get(k) for k in common_keys if k in colset} for r0 in rows]
                r = await self._sb_upsert(self.mem_table, payload)
                if r.status_code in (200, 201, 204):
                    pushed = len(payload)
                else:
                    logger.warning(f"mem push failed: {r.status_code} {r.text}")
        except Exception as e:
            logger.debug(f"mem push error: {e}")
        logger.info(f"mem push pushed={pushed}")
        return pushed

    async def sync_once(self) -> Dict[str, Any]:
        report: Dict[str, Any] = {"supabase": {}, "chroma": {}}
        logger.debug("sync_once start")
        skip_pulls = os.environ.get("CFLOW_SKIP_PULLS", "0").lower() in {"1", "true", "yes"}
        # Discover tables on first run
        try:
            await self.discover_tables()
            report["tables"] = {"tasks": self.tasks_table, "docs": self.docs_table}
        except Exception as e:
            report["table_discovery_error"] = str(e)
        # Report local counts (optional to avoid native crashes)
        if not self.skip_chroma_counts:
            try:
                report["chroma"]["tasks_count"] = self.tasks.count()  # type: ignore
            except Exception as e:
                logger.warning(f"tasks count error: {e}")
            try:
                report["chroma"]["docs_count"] = self.docs.count()  # type: ignore
            except Exception as e:
                logger.warning(f"docs count error: {e}")
        # Supabase reachability check via tasks table
        try:
            if self.supabase_url and self.supabase_key:
                r = await self._sb_get(f"/rest/v1/{self.tasks_table}", {"select": "id", "limit": 1})
                report["supabase"]["status_code"] = r.status_code
            else:
                report["supabase"]["error"] = "missing url or key"
        except Exception as e:
            report["supabase"]["error"] = str(e)
        # Pull then push
        if not skip_pulls:
            try:
                t_up = await self.sync_tasks_pull()
                d_up = await self.sync_docs_pull()
                m_up = await self.sync_mem_pull()
                report["pull"] = {"tasks": t_up, "docs": d_up, "mem": m_up}
            except Exception as e:
                report["pull_error"] = str(e)
        try:
            t_push = await self.sync_tasks_push()
            d_push = await self.sync_docs_push()
            m_push = await self.sync_mem_push()
            report["push"] = {"tasks": t_push, "docs": d_push, "mem": m_push}
        except Exception as e:
            report["push_error"] = str(e)
        if self.vector_enabled:
            try:
                logger.info("starting vector push")
                v_push = await self.sync_vectors_push()
                report.setdefault("push", {})["vectors"] = v_push
            except Exception as e:
                report["vector_push_error"] = str(e)
        logger.info(f"sync_once report: {json.dumps(report)}")
        return report

    async def run(self) -> None:
        # Robust loop until interrupted; never exit on transient errors
        try:
            while True:
                logger.debug("run loop tick start")
                try:
                    await self.sync_once()
                except Exception as e:
                    logger.error(f"sync_once crashed: {e}")
                try:
                    await asyncio.sleep(10)
                except asyncio.CancelledError:
                    logger.debug("sleep cancelled; continuing")
                    continue
        except Exception as e:
            logger.error(f"run loop fatal: {e}")
            # Keep process alive even on unexpected fatal; short backoff
            try:
                await asyncio.sleep(5)
            except Exception:
                pass
            await self.run()


def start() -> int:
    project_root = os.environ.get("CEREBRAL_PROJECT_ROOT") or os.getcwd()
    sync = UnifiedSync(project_root)
    logger.info("UnifiedSync starting")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    task = loop.create_task(sync.run())
    try:
        loop.run_until_complete(task)
    except KeyboardInterrupt:
        task.cancel()
        try:
            loop.run_until_complete(task)
        except Exception:
            pass
    finally:
        loop.close()
    return 0


def run_once() -> int:
    project_root = os.environ.get("CEREBRAL_PROJECT_ROOT") or os.getcwd()
    sync = UnifiedSync(project_root)
    logger.info("UnifiedSync once")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        report = loop.run_until_complete(sync.sync_once())
        try:
            # Emit a concise JSON for callers
            print(json.dumps({"success": True, "report": report}))
        except Exception:
            pass
    finally:
        loop.close()
    return 0


def cli() -> int:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["start", "once"], help="Start loop or run a single sync cycle")
    p.add_argument("--project-root", dest="project_root")
    args = p.parse_args()
    if args.project_root:
        os.environ["CEREBRAL_PROJECT_ROOT"] = args.project_root
    if args.command == "once":
        return run_once()
    return start()


if __name__ == "__main__":
    raise SystemExit(cli())
