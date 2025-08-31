#/Users/bbaer/Development/Cerebral/.venv/bin/python
"""
Cerebral Project Memory Service
Enterprise-grade memory management for human-AI collaborative development

UNIFIED IMPLEMENTATION: Uses ChromaDBSupabaseSyncService (100% Python, no Mem0)
"""

import os
import json
import time
import logging
import asyncio
import sys
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field
from pathlib import Path
from opentelemetry import trace

# Add services path
services_path = Path(__file__).parent.parent / "services"
if str(services_path) not in sys.path:
    sys.path.append(str(services_path))

# Import unified storage system
from chromadb_supabase_sync_service import ChromaDBSupabaseSyncService

# Configure logging
logger = logging.getLogger(__name__)
tracer = trace.get_tracer("cerebral.memory")


class MemoryType(str, Enum):
    """Types of memories in our system."""

    ARCHITECTURAL = "architectural"
    SECURITY = "security"
    PATTERN = "pattern"
    DECISION = "decision"
    PREFERENCE = "preference"
    CONTEXT = "context"
    RULE = "rule"
    PERFORMANCE = "performance"
    HIL_FEEDBACK = "hil_feedback"  # Human-in-the-Loop feedback patterns


class MemoryScope(str, Enum):
    """Scope levels for memory storage."""

    USER = "user"  # Individual developer preferences
    PROJECT = "project"  # Project-wide decisions
    TEAM = "team"  # Team-level patterns
    ORGANIZATION = "organization"  # Enterprise standards


class MemoryClassification(str, Enum):
    """Security classification for memories."""

    PUBLIC = "public"  # General patterns, publicly known
    INTERNAL = "internal"  # Project-specific, internal only
    CONFIDENTIAL = "confidential"  # Sensitive architectural decisions
    RESTRICTED = "restricted"  # Critical security patterns
class ProcedureStep(BaseModel):
    """Schema for a single procedure step."""
    order: int = Field(ge=1)
    instruction: str
    notes: Optional[str] = None


class ProcedureUpdate(BaseModel):
    """Schema for a procedure update payload."""
    title: str
    steps: List[ProcedureStep]
    justification: str
    source: Optional[str] = None



@dataclass
class ProjectMemory:
    """Structured project memory with metadata."""

    id: Optional[str] = None
    type: MemoryType = MemoryType.CONTEXT
    scope: MemoryScope = MemoryScope.PROJECT
    classification: MemoryClassification = MemoryClassification.INTERNAL
    title: str = ""
    content: str = ""
    metadata: Dict[str, Any] = None
    tags: List[str] = None
    # Cross-linking to Knowledge Graph
    kg_entity_ids: List[str] = None  # Neo4j/Supabase KG entity IDs
    kg_rel_ids: List[str] = None     # Relationship IDs if relevant
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user_id: Optional[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.tags is None:
            self.tags = []
        if self.kg_entity_ids is None:
            self.kg_entity_ids = []
        if self.kg_rel_ids is None:
            self.kg_rel_ids = []
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


class CerebralProjectMemory:
    """
    Enterprise memory management for collaborative development.
    
    UNIFIED IMPLEMENTATION: 100% Python using ChromaDBSupabaseSyncService
    NO Mem0 dependencies - fully self-contained with enterprise features.

    Provides persistent, searchable memory storage for:
    - Architectural decisions
    - Security patterns
    - Development preferences
    - Code patterns and rules
    - Project context and history
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the unified cerebralMemory system."""
        self.config = config or {}
        
        # Initialize unified storage system (replaces Mem0)
        self._setup_unified_storage()

        # Memory statistics
        self.stats = {
            "memories_stored": 0, 
            "memories_retrieved": 0, 
            "last_updated": datetime.now(timezone.utc)
        }

        logger.info("✅ CerebralProjectMemory initialized with unified storage (no Mem0)")

    # ------------ Metrics helpers ------------
    def _log_metric(self, name: str, value: Any, **attrs: Any) -> None:
        try:
            metrics_dir = Path(".cerebraflow/core/storage/metrics")
            metrics_dir.mkdir(parents=True, exist_ok=True)
            rec = {"ts": time.time(), "name": name, "value": value, **attrs}
            with open(metrics_dir / "memory_metrics.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
        except Exception as e:
            logger.debug(f"metrics emit failed: {e}")

    def _setup_unified_storage(self):
        """Setup unified ChromaDBSupabaseSyncService (replaces Mem0)."""
        try:
            # Use unified storage service
            self.storage = ChromaDBSupabaseSyncService()
            logger.info("✅ Unified cerebralMemory storage initialized")
            
        except Exception as e:
            logger.error(f"❌ Unified storage setup failed: {e}")
            raise

    async def add_memory(
        self, 
        content: str, 
        user_id: str = "system", 
        metadata: Dict[str, Any] = None,
        *,
        implicit: bool = False,
    ) -> str:
        """Add memory using unified storage system."""
        try:
            t0 = time.perf_counter()
            with tracer.start_as_current_span("memory.add") as span:
                # Use unified storage add_document method
                # Enrich metadata with tenant_id if available
                meta: Dict[str, Any] = {
                    "user_id": user_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    **(metadata or {}),
                }
                tenant_env = os.getenv("CEREBRAL_TENANT_ID")
                if tenant_env and "tenant_id" not in meta:
                    meta["tenant_id"] = tenant_env

                span.set_attribute("collection", "cerebral_mem")
                span.set_attribute("user_id", user_id)
                if "tenant_id" in meta:
                    span.set_attribute("tenant_id", meta["tenant_id"])
                span.set_attribute("content.length", len(content))

                # Optional write-queue for non-critical writes
                if implicit or os.getenv("MEMORY_WRITE_QUEUE_ENABLED", "false").lower() in {"1","true","yes"}:
                    queued_id = await self._enqueue_memory_write(content=content, user_id=user_id, metadata=meta)
                    span.set_attribute("queued", True)
                    self.stats["memories_stored"] += 1
                    return queued_id

                memory_id = await self.storage.add_document(
                    collection_type="cerebral_mem",
                    content=content,
                    metadata=meta,
                )
                span.set_attribute("result.id", str(memory_id))
            
            self.stats["memories_stored"] += 1
            self._log_metric(
                "memory_add",
                1,
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                content_length=len(content),
            )
            return memory_id
            
        except Exception as e:
            logger.error(f"❌ Memory add failed: {e}")
            return f"mem_{datetime.now().timestamp()}"

    async def _enqueue_memory_write(self, *, content: str, user_id: str, metadata: Dict[str, Any]) -> str:
        """Append a write request to a local JSONL queue for background consumption.

        Queue path: .cerebraflow/core/storage/queues/memory_write_queue.jsonl
        """
        try:
            queue_dir = Path(".cerebraflow/core/storage/queues")
            queue_dir.mkdir(parents=True, exist_ok=True)
            queued_id = f"queued_{int(datetime.now(timezone.utc).timestamp()*1000)}"
            record = {
                "id": queued_id,
                "content": content,
                "user_id": user_id,
                "metadata": metadata,
                "enqueued_at": datetime.now(timezone.utc).isoformat(),
            }
            with open(queue_dir / "memory_write_queue.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
            return queued_id
        except Exception as e:
            logger.error(f"❌ Queue write failed, falling back to direct add: {e}")
            # Fallback to direct add on queue failure
            return await self.add_memory(content=content, user_id=user_id, metadata=metadata, implicit=False)

    async def search_memories(
        self,
        query: str,
        user_id: str = "system",
        limit: int = 20,
        *,
        min_similarity_score: float = 0.72,
        max_results: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        recency_alpha: float = 0.85,
        recency_lambda: float = 0.05,
        include_expired: bool = False,
    ) -> List[Dict[str, Any]]:
        """Search memories using unified storage system with threshold and cap.

        Args:
            query: Free-text query string
            user_id: Caller id (reserved for future auditing)
            limit: Upstream fetch count from storage
            min_similarity_score: Minimum similarity to include in results (default: 0.72)
            max_results: Maximum number of results to return after filtering (default: 20)

        Returns:
            List of result dicts filtered by similarity and truncated to max_results.
        """
        try:
            t0 = time.perf_counter()
            with tracer.start_as_current_span("memory.search") as span:
                span.set_attribute("query.length", len(query))
                span.set_attribute("limit", limit)
                span.set_attribute("min_similarity_score", float(min_similarity_score))
                span.set_attribute("max_results", max_results)
                # Fetch from unified storage with back-compat collection aliases
                raw_batches = []
                for coll in ("cerebral_mem", "cerebral_memory", "cerebral_mem0"):
                    try:
                        batch = await self.storage.search_documents(
                            collection_type=coll,
                            query=query,
                            limit=limit,
                        )
                        # Accept first non-empty batch for efficiency; or append to aggregate
                        if batch:
                            raw_batches.append(batch)
                            span.set_attribute("collection", coll)
                            break
                    except Exception:
                        continue
                raw_results = raw_batches[0] if raw_batches else []

                # Enrich with KG pivots if available (optional lightweight step)
                try:
                    neo4j_enabled = os.getenv("KNOWLEDGE_MAP_NEO4J_ENABLED", "false").lower() in {"1","true","yes"}
                    if neo4j_enabled and raw_results:
                        # add a light indicator for downstream handlers
                        for r in raw_results:
                            meta = r.get("metadata") or {}
                            if meta.get("kg_entity_ids"):
                                r["kg_linked"] = True
                except Exception:
                    pass

                processed = self._apply_min_score_and_cap(
                    raw_results, min_similarity_score=min_similarity_score, max_results=10_000
                )

                # Apply metadata prefilters (tenant_id, scope, type, task_id, run_id, etc.)
                if filters:
                    processed = self._apply_metadata_filters(processed, filters)

                # Apply TTL policy filter unless explicitly including expired
                processed = self._apply_ttl_filter(processed, include_expired=include_expired)

                # Decay scoring and recency-weighted reranking before final cap
                processed = self._apply_decay(processed, age_lambda=recency_lambda)
                processed = self._rerank_with_recency(processed, alpha=recency_alpha, decay_lambda=recency_lambda)

                # Final cap
                processed = processed[: max(0, max_results)]

                self.stats["memories_retrieved"] += len(processed)
                span.set_attribute("result.count", len(processed))
                self._log_metric(
                    "memory_search",
                    len(processed),
                    latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                    min_similarity=min_similarity_score,
                    requested_limit=limit,
                    final_k=len(processed),
                )
                return processed

        except Exception as e:
            logger.error(f"❌ Memory search failed: {e}")
            return []

    @staticmethod
    def _apply_min_score_and_cap(
        raw_results: Any, *, min_similarity_score: float, max_results: int
    ) -> List[Dict[str, Any]]:
        """Normalize result shape, compute similarity if needed, filter by score, cap length.

        Accepts either:
        - List[Dict]: each dict may contain 'similarity' or 'distance' and 'metadata'
        - Chroma-style payload dict with keys: 'ids', 'documents', 'metadatas', 'distances'
        """
        # Case 1: Already a list of items
        if isinstance(raw_results, list):
            normalized: List[Dict[str, Any]] = []
            for item in raw_results:
                if not isinstance(item, dict):
                    continue
                sim = item.get("similarity")
                if sim is None:
                    dist = item.get("distance")
                    if isinstance(dist, (int, float)):
                        sim = max(0.0, min(1.0, 1.0 - float(dist)))
                # If neither present, treat as unknown similarity and include by default
                if sim is None:
                    sim = 1.0
                enriched = dict(item)
                enriched["similarity"] = sim
                normalized.append(enriched)
            filtered = [i for i in normalized if i.get("similarity", 0.0) >= min_similarity_score]
            return filtered[: max(0, max_results)]

        # Case 2: Chroma-style response dict
        if isinstance(raw_results, dict):
            ids = (raw_results.get("ids") or [[]])[0]
            docs = (raw_results.get("documents") or [[]])[0]
            metas = (raw_results.get("metadatas") or [[]])[0]
            dists = (raw_results.get("distances") or [[]])[0]

            items: List[Dict[str, Any]] = []
            for rid, doc, meta, dist in zip(ids, docs, metas, dists):
                sim = None
                if isinstance(dist, (int, float)):
                    sim = max(0.0, min(1.0, 1.0 - float(dist)))
                items.append({
                    "id": rid,
                    "document": doc,
                    "metadata": meta,
                    "distance": dist,
                    "similarity": sim if sim is not None else 1.0,
                })
            filtered = [i for i in items if i.get("similarity", 0.0) >= min_similarity_score]
            return filtered[: max(0, max_results)]

        # Fallback: unknown shape
        return []

    @staticmethod
    def _rerank_with_recency(
        items: List[Dict[str, Any]], *, alpha: float = 0.85, decay_lambda: float = 0.05
    ) -> List[Dict[str, Any]]:
        """Rerank by combining similarity with recency decay on metadata timestamp/last_accessed.

        score = alpha * similarity + (1 - alpha) * exp(-lambda * age_days)
        """
        from datetime import datetime

        now = datetime.utcnow()

        def parse_iso(ts: str) -> Optional[datetime]:
            try:
                # Support both aware/naive ISO strings
                return datetime.fromisoformat(ts.replace("Z", "+00:00").replace(" ", "T"))
            except Exception:
                return None

        def age_days(meta: Dict[str, Any]) -> float:
            ts = meta.get("last_accessed") or meta.get("timestamp")
            if not ts:
                return 365.0
            dt = parse_iso(ts)
            if not dt:
                return 365.0
            delta = now - (dt if not dt.tzinfo else dt.replace(tzinfo=None))
            return max(0.0, delta.total_seconds() / 86400.0)

        def composite_score(it: Dict[str, Any]) -> float:
            sim = float(it.get("similarity", 0.0))
            meta = it.get("metadata") or {}
            rec = math.exp(-decay_lambda * age_days(meta))
            return alpha * sim + (1 - alpha) * rec

        import math

        return sorted(items, key=composite_score, reverse=True)

    @staticmethod
    def _apply_ttl_filter(
        items: List[Dict[str, Any]], *, include_expired: bool = False
    ) -> List[Dict[str, Any]]:
        """Filter out expired items based on type-specific TTL and pinning.

        TTL policy (days):
          - context: 90
          - preference: 365
          - procedure: None (no TTL)
        Pinned items (metadata.pinned == True) are never expired.
        """
        if include_expired:
            return items

        from datetime import datetime

        ttl_days_by_type: Dict[str, Optional[int]] = {
            "context": 90,
            "preference": 365,
            "procedure": None,
        }

        def parse_iso(ts: str) -> Optional[datetime]:
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00").replace(" ", "T"))
            except Exception:
                return None

        now = datetime.utcnow()
        kept: List[Dict[str, Any]] = []
        for it in items:
            meta = it.get("metadata") or {}
            if meta.get("pinned") is True:
                kept.append(it)
                continue
            t = str(meta.get("type", "")).lower()
            ttl_days = ttl_days_by_type.get(t)
            if not ttl_days:  # None or 0 -> no TTL for this type
                kept.append(it)
                continue
            ts = meta.get("timestamp") or meta.get("last_accessed")
            if not ts:
                # No timestamp -> treat as expired for TTL-managed types
                continue
            dt = parse_iso(ts)
            if not dt:
                continue
            age_days = (now - (dt if not dt.tzinfo else dt.replace(tzinfo=None))).total_seconds() / 86400.0
            if age_days <= float(ttl_days):
                kept.append(it)
        return kept

    @staticmethod
    def _apply_decay(
        items: List[Dict[str, Any]], *, age_lambda: float = 0.05
    ) -> List[Dict[str, Any]]:
        """Apply decay multiplier to similarity based on age_days and optional access_count.

        similarity' = similarity * exp(-age_lambda * age_days) * (1 + log1p(access_count)/10)
        """
        from datetime import datetime
        import math

        now = datetime.utcnow()

        def parse_iso(ts: str) -> Optional[datetime]:
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00").replace(" ", "T"))
            except Exception:
                return None

        def age_days(meta: Dict[str, Any]) -> float:
            ts = meta.get("last_accessed") or meta.get("timestamp")
            if not ts:
                return 365.0
            dt = parse_iso(ts)
            if not dt:
                return 365.0
            delta = now - (dt if not dt.tzinfo else dt.replace(tzinfo=None))
            return max(0.0, delta.total_seconds() / 86400.0)

        adjusted: List[Dict[str, Any]] = []
        for it in items:
            sim = float(it.get("similarity", 0.0))
            meta = it.get("metadata") or {}
            decay = math.exp(-age_lambda * age_days(meta))
            access_cnt = 0
            try:
                access_cnt = int(meta.get("access_count", 0))
            except Exception:
                access_cnt = 0
            frequency_boost = 1.0 + (math.log1p(access_cnt) / 10.0)
            new_sim = max(0.0, min(1.0, sim * decay * frequency_boost))
            new_item = dict(it)
            new_item["similarity"] = new_sim
            adjusted.append(new_item)
        return adjusted

    @staticmethod
    def _apply_metadata_filters(items: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply simple metadata filters with support for equality and $in.

        Example filters:
        {"tenant_id": "...", "scope": {"$in": ["project","team"]}, "type": "episodic"}
        """
        def match(meta: Dict[str, Any], key: str, cond: Any) -> bool:
            if isinstance(cond, dict):
                if "$in" in cond and isinstance(cond["$in"], list):
                    return meta.get(key) in cond["$in"]
                # Extend here for other operators as needed
                return False
            return meta.get(key) == cond

        filtered: List[Dict[str, Any]] = []
        for it in items:
            meta = it.get("metadata") or it.get("meta") or {}
            if all(match(meta, k, v) for k, v in filters.items()):
                filtered.append(it)
        return filtered

    async def store_architectural_decision(
        self,
        title: str,
        decision: str,
        context: str,
        rationale: str,
        alternatives: Optional[List[str]] = None,
        user_id: str = "system"
    ) -> str:
        """Store architectural decision using unified storage."""
        content = f"""
ARCHITECTURAL DECISION: {title}

DECISION: {decision}

CONTEXT: {context}

RATIONALE: {rationale}

ALTERNATIVES: {', '.join(alternatives or [])}
        """.strip()
        
        metadata = {
            "type": MemoryType.ARCHITECTURAL,
            "scope": MemoryScope.PROJECT,
            "classification": MemoryClassification.INTERNAL,
            "title": title,
            "alternatives": alternatives or []
        }
        
        return await self.add_memory(content, user_id, metadata)

    async def store_security_pattern(
        self,
        pattern_name: str,
        description: str,
        implementation: str,
        classification: MemoryClassification = MemoryClassification.CONFIDENTIAL,
        user_id: str = "system"
    ) -> str:
        """Store security pattern using unified storage."""
        content = f"""
SECURITY PATTERN: {pattern_name}

DESCRIPTION: {description}

IMPLEMENTATION: {implementation}
        """.strip()
        
        metadata = {
            "type": MemoryType.SECURITY,
            "scope": MemoryScope.ORGANIZATION,
            "classification": classification,
            "pattern_name": pattern_name
        }
        
        return await self.add_memory(content, user_id, metadata)

    async def store_development_preference(
        self,
        preference_name: str,
        value: str,
        justification: str,
        scope: MemoryScope = MemoryScope.USER,
        user_id: str = "system"
    ) -> str:
        """Store development preference using unified storage."""
        content = f"""
DEVELOPMENT PREFERENCE: {preference_name}

VALUE: {value}

JUSTIFICATION: {justification}
        """.strip()
        
        metadata = {
            "type": MemoryType.PREFERENCE,
            "scope": scope,
            "classification": MemoryClassification.INTERNAL,
            "preference_name": preference_name,
            "value": value
        }
        
        return await self.add_memory(content, user_id, metadata)

    async def store_procedure_update(
        self,
        title: str,
        steps: List[Dict[str, Any]],
        justification: str,
        source: Optional[str] = None,
        user_id: str = "system",
        hil_required: Optional[bool] = None,
    ) -> str:
        """Store a procedure update with structured, validated steps.

        Validates payload using `ProcedureUpdate` and persists with metadata type=procedure.
        """
        # Validate using Pydantic models
        validated = ProcedureUpdate(
            title=title,
            steps=[ProcedureStep(**s) if not isinstance(s, ProcedureStep) else s for s in steps],
            justification=justification,
            source=source,
        )

        # Create a readable content block for quick inspection
        steps_block = "\n".join(
            f"{s.order}. {s.instruction}" + (f"\n   - {s.notes}" if s.notes else "") for s in validated.steps
        )
        content = (
            f"PROCEDURE UPDATE: {validated.title}\n\n"
            f"JUSTIFICATION: {validated.justification}\n"
            f"SOURCE: {validated.source or 'unspecified'}\n\n"
            f"STEPS:\n{steps_block}"
        )

        metadata = {
            "type": "procedure",
            "title": validated.title,
            "step_count": len(validated.steps),
            "source": validated.source,
        }

        # HIL gating: feature flag via env or argument
        if hil_required is None:
            hil_required = os.getenv("PROCEDURE_HIL_REQUIRED", "false").lower() in {"1", "true", "yes"}

        if hil_required:
            # Queue to CAEF review queue; do not persist immediately
            with tracer.start_as_current_span("memory.procedure.queue_for_review") as span:
                span.set_attribute("title", validated.title)
                span.set_attribute("step_count", len(validated.steps))
                span.set_attribute("hil_required", True)
                # Minimal queue record using add_memory under review namespace
                review_meta = {
                    **metadata,
                    "status": "pending_review",
                    "review_queue": "procedure_updates",
                    "submitted_at": datetime.now(timezone.utc).isoformat(),
                }
                return await self.add_memory(
                    content=content,
                    user_id=user_id,
                    metadata=review_meta,
                )
        else:
            return await self.add_memory(content=content, user_id=user_id, metadata=metadata)

    async def store_episode(
        self,
        run_id: str,
        task_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: str = "system",
    ) -> str:
        """Store an episodic memory item for a run/task.

        Adds metadata keys: type=episodic, run_id, task_id.
        """
        meta = {
            "type": "episodic",
            "run_id": run_id,
            "task_id": task_id,
            **(metadata or {}),
        }
        return await self.add_memory(content=content, user_id=user_id, metadata=meta)

    async def get_memories_by_type(
        self, 
        memory_type: MemoryType, 
        user_id: str = "system"
    ) -> List[Dict[str, Any]]:
        """Get memories filtered by type."""
        return await self.search_memories(
            query=f"type:{memory_type.value}",
            user_id=user_id
        )

    async def get_episodes(
        self,
        task_id: Optional[str] = None,
        run_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Retrieve episodic memories filtered by task_id and/or run_id.

        Uses metadata filters to constrain results to type=episodic.
        """
        try:
            with tracer.start_as_current_span("memory.get_episodes") as span:
                span.set_attribute("limit", limit)
                if task_id:
                    span.set_attribute("task_id", task_id)
                if run_id:
                    span.set_attribute("run_id", run_id)

                filters: Dict[str, Any] = {"type": {"$in": ["episodic"]}}
                if task_id:
                    filters["task_id"] = task_id
                if run_id:
                    filters["run_id"] = run_id

                # Prefer storage-level filtering if supported
                try:
                    results = await self.storage.search_documents(
                        collection_type="cerebral_mem",
                        query="",
                        limit=limit,
                        filters=filters,
                    )
                    # Normalize/cap if needed using existing helpers
                    processed = self._apply_min_score_and_cap(results, min_similarity_score=0.0, max_results=limit)
                except TypeError:
                    # Fallback: no filters arg in storage -> reuse search_memories with local filters
                    processed = await self.search_memories(
                        query="",
                        limit=limit,
                        min_similarity_score=0.0,
                        max_results=limit,
                        filters=filters,
                    )

                span.set_attribute("result.count", len(processed or []))
                return processed or []
        except Exception as e:
            logger.error(f"❌ get_episodes failed: {e}")
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        return {
            **self.stats,
            "storage_type": "unified_chromadb_supabase",
            "cerebral_memory_dependency": True
        }

    # HIL (Human-in-the-Loop) Memory Methods
    
    async def store_hil_feedback_pattern(
        self, 
        pattern_title: str,
        feedback_content: str,
        satisfaction_score: float,
        pattern_type: str,
        reviewer_id: str,
        implementation_context: str,
        user_id: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store HIL feedback pattern for ML learning.
        
        Args:
            pattern_title: Descriptive title for the feedback pattern
            feedback_content: The actual human feedback content
            satisfaction_score: Satisfaction score (0.0-1.0) from reviewer
            pattern_type: Type of HIL pattern (review_feedback, architecture_preference, etc.)
            reviewer_id: ID of the human reviewer
            implementation_context: Context about what was being reviewed
            user_id: User storing the memory
            metadata: Additional metadata
            
        Returns:
            str: Memory ID for the stored HIL pattern
        """
        try:
            hil_metadata = {
                "satisfaction_score": satisfaction_score,
                "pattern_type": pattern_type,
                "reviewer_id": reviewer_id,
                "implementation_context": implementation_context,
                "memory_type": MemoryType.HIL_FEEDBACK.value,
                "scope": MemoryScope.PROJECT.value,
                "classification": MemoryClassification.INTERNAL.value,
                **(metadata or {})
            }
            
            # Create structured content for HIL feedback
            structured_content = f"""
Title: {pattern_title}
Satisfaction Score: {satisfaction_score}
Pattern Type: {pattern_type}
Reviewer: {reviewer_id}

Feedback Content:
{feedback_content}

Implementation Context:
{implementation_context}
"""
            
            # Store using unified storage system
            memory_id = await self.add_memory(
                content=structured_content,
                user_id=user_id,
                metadata=hil_metadata
            )
            
            logger.info(f"✅ HIL feedback pattern stored: {pattern_title} (ID: {memory_id})")
            return memory_id
            
        except Exception as e:
            logger.error(f"❌ Failed to store HIL feedback pattern: {e}")
            raise

    async def get_hil_feedback_patterns(
        self,
        pattern_type: Optional[str] = None,
        satisfaction_threshold: Optional[float] = None,
        reviewer_id: Optional[str] = None,
        limit: int = 50,
        user_id: str = "system"
    ) -> List[Dict[str, Any]]:
        """Retrieve HIL feedback patterns for ML training.
        
        Args:
            pattern_type: Filter by specific HIL pattern type
            satisfaction_threshold: Minimum satisfaction score to include
            reviewer_id: Filter by specific reviewer
            limit: Maximum number of patterns to return
            user_id: User requesting the patterns
            
        Returns:
            List[Dict]: List of HIL feedback patterns with metadata
        """
        try:
            # Search for HIL feedback memories
            memories = await self.search_memories(
                query=f"HIL feedback {pattern_type or ''}", 
                user_id=user_id,
                limit=limit
            )
            
            # Filter by HIL feedback type and apply filters
            hil_patterns = []
            for memory in memories:
                if memory.get("metadata", {}).get("memory_type") == MemoryType.HIL_FEEDBACK.value:
                    metadata = memory.get("metadata", {})
                    
                    # Apply satisfaction threshold filter
                    if satisfaction_threshold is not None:
                        score = metadata.get("satisfaction_score", 0.0)
                        if score < satisfaction_threshold:
                            continue
                    
                    # Apply pattern type filter
                    if pattern_type is not None:
                        if metadata.get("pattern_type") != pattern_type:
                            continue
                            
                    # Apply reviewer filter
                    if reviewer_id is not None:
                        if metadata.get("reviewer_id") != reviewer_id:
                            continue
                    
                    hil_patterns.append(memory)
            
            logger.info(f"✅ Retrieved {len(hil_patterns)} HIL feedback patterns")
            return hil_patterns
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve HIL feedback patterns: {e}")
            return []

    async def analyze_hil_feedback_trends(
        self,
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """Analyze HIL feedback trends for ML insights.
        
        Args:
            user_id: User requesting the analysis
            
        Returns:
            Dict: Analysis of HIL feedback trends and patterns
        """
        try:
            # Get all HIL feedback patterns
            hil_patterns = await self.get_hil_feedback_patterns(user_id=user_id, limit=1000)
            
            if not hil_patterns:
                return {"error": "No HIL feedback patterns found"}
            
            # Analyze trends
            total_patterns = len(hil_patterns)
            satisfaction_scores = []
            pattern_types = {}
            reviewers = {}
            
            for pattern in hil_patterns:
                metadata = pattern.get("metadata", {})
                
                # Satisfaction score analysis
                score = metadata.get("satisfaction_score", 0.0)
                satisfaction_scores.append(score)
                
                # Pattern type distribution
                pattern_type = metadata.get("pattern_type", "unknown")
                pattern_types[pattern_type] = pattern_types.get(pattern_type, 0) + 1
                
                # Reviewer activity
                reviewer = metadata.get("reviewer_id", "unknown")
                reviewers[reviewer] = reviewers.get(reviewer, 0) + 1
            
            # Calculate statistics
            avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0.0
            high_satisfaction = len([s for s in satisfaction_scores if s >= 0.7])
            low_satisfaction = len([s for s in satisfaction_scores if s < 0.4])
            
            analysis = {
                "total_patterns": total_patterns,
                "average_satisfaction": round(avg_satisfaction, 3),
                "high_satisfaction_count": high_satisfaction,
                "low_satisfaction_count": low_satisfaction,
                "pattern_type_distribution": pattern_types,
                "reviewer_activity": reviewers,
                "satisfaction_scores": satisfaction_scores,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"✅ HIL feedback trend analysis completed: {total_patterns} patterns analyzed")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze HIL feedback trends: {e}")
            return {"error": str(e)}

    async def store_feedback_batch_enhanced(
        self,
        feedback_data: List[Any],  # List of HIL feedback data
        training_session_id: Optional[str] = None,
        source: str = "training_pipeline"
    ) -> Dict[str, Any]:
        """
        Store HIL feedback batch using enhanced persistence capabilities
        
        Integration point for enhanced HIL feedback persistence system.
        Falls back to regular storage if enhanced system unavailable.
        """
        try:
            # Try to use enhanced persistence system
            try:
                from shared.enhanced_hil_feedback_persistence import (
                    get_enhanced_hil_persistence,
                    FeedbackBatchType
                )
                
                enhanced_persistence = get_enhanced_hil_persistence()
                batch_result = await enhanced_persistence.store_feedback_batch(
                    feedback_data=feedback_data,
                    batch_type=FeedbackBatchType.TRAINING_SESSION,
                    training_session_id=training_session_id,
                    source=source
                )
                
                return {
                    "success": batch_result.success,
                    "batch_id": batch_result.batch_id,
                    "feedback_count": batch_result.feedback_count,
                    "processing_method": "enhanced_persistence",
                    "metadata": batch_result.metadata
                }
                
            except ImportError:
                # Fallback to standard storage
                logger.info("Enhanced persistence not available, using standard storage")
                stored_count = 0
                
                for feedback in feedback_data:
                    try:
                        # Basic storage using existing method
                        memory_id = await self.store_hil_feedback_pattern(
                            pattern_title=f"HIL Feedback - {getattr(feedback, 'review_type', 'unknown')}",
                            feedback_content=getattr(feedback, 'feedback_content', str(feedback)),
                            satisfaction_score=getattr(feedback, 'satisfaction_score', 0.5),
                            pattern_type=getattr(feedback, 'review_type', 'general'),
                            reviewer_id=getattr(feedback, 'reviewer_id', 'unknown'),
                            implementation_context=str(getattr(feedback, 'implementation_context', {})),
                            metadata={
                                "training_session_id": training_session_id,
                                "source": source,
                                "fallback_storage": True
                            }
                        )
                        stored_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to store feedback item: {e}")
                        continue
                
                return {
                    "success": stored_count > 0,
                    "batch_id": f"fallback_{int(datetime.now(timezone.utc).timestamp())}",
                    "feedback_count": len(feedback_data),
                    "stored_count": stored_count,
                    "processing_method": "fallback_storage"
                }
                
        except Exception as e:
            logger.error(f"❌ Enhanced feedback batch storage failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_enhanced_feedback_metrics(self) -> Dict[str, Any]:
        """
        Get enhanced feedback persistence metrics if available
        """
        try:
            from shared.enhanced_hil_feedback_persistence import get_enhanced_hil_persistence
            
            enhanced_persistence = get_enhanced_hil_persistence()
            return await enhanced_persistence.get_persistence_metrics()
            
        except ImportError:
            # Return basic metrics from standard system
            return {
                "system_type": "standard_memory",
                "enhanced_features": False,
                "message": "Enhanced persistence system not available"
            }
        except Exception as e:
            logger.error(f"❌ Failed to get enhanced metrics: {e}")
            return {"error": str(e)}

    async def optimize_hil_storage(self) -> Dict[str, Any]:
        """
        Perform HIL feedback storage optimization if enhanced system available
        """
        try:
            from shared.enhanced_hil_feedback_persistence import get_enhanced_hil_persistence
            
            enhanced_persistence = get_enhanced_hil_persistence()
            return await enhanced_persistence.optimize_storage()
            
        except ImportError:
            return {
                "optimization_type": "basic",
                "message": "Enhanced optimization not available - using basic memory system"
            }
        except Exception as e:
            logger.error(f"❌ Storage optimization failed: {e}")
            return {"error": str(e)}


# Global instance for easy access
_project_memory_instance = None

def get_project_memory(config: Optional[Dict[str, Any]] = None) -> CerebralProjectMemory:
    """Get or create global project memory instance."""
    global _project_memory_instance
    if _project_memory_instance is None:
        _project_memory_instance = CerebralProjectMemory(config)
    return _project_memory_instance
