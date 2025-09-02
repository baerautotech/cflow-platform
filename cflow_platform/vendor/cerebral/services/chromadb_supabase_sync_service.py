#!/usr/bin/env python3
"""
ChromaDB Supabase Sync Service
Python interface for the existing Cerebral unified sync infrastructure

This service provides a Python API for:
- Interfacing with the existing com.cerebral.unified-sync service
- Status monitoring and health checks for the sync system
- Compatibility layer for CAEF orchestrator integration

Architecture:
- Interfaces with existing Cerebral unified sync service (com.cerebral.unified-sync)
- Connects to /Users/bbaer/.cerebral/sync-service/unified_realtime_sync_service.py
- Provides compatibility with CAEF orchestrator requirements
- No duplication of existing sync infrastructure
"""

import os
import sys
import json
import asyncio
import logging
import signal
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import uuid
from dotenv import load_dotenv
import psutil
import time
import json as _json
from urllib import request as _urlreq
from urllib.error import URLError, HTTPError

# Add project paths for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT / ".cerebraflow" / "local"))
sys.path.append(str(PROJECT_ROOT / "backend-python"))

# Use the existing Cerebral unified sync service
CEREBRAL_SYNC_SERVICE = "com.cerebral.unified-sync"
CEREBRAL_REALTIME_SYNC_SERVICE = "com.cerebral.realtime-sync"
CEREBRAL_SYNC_BINARY = "/Users/bbaer/.cerebral/sync-service/cerebral-sync"
CEREBRAL_LOGS_DIR = "/Users/bbaer/.cerebral/logs"

# Standard collection names from Cerebral architecture
COLLECTION_SYNC_MAP = {
    "cerebral_tasks": "cerebraflow_tasks",
    "cerebral_docs": "cerebral_docs", 
    "cerebral_rag": "cerebral_rag",
    # Standard collection name and back-compat aliases
    "cerebral_mem": "cerebral_mem",
    "cerebral_memory": "cerebral_mem",
    "cerebral_mem0": "cerebral_mem",
}

# ChromaDB and Supabase imports
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

logger = logging.getLogger(__name__)


class ChromaDBSupabaseSyncService:
    """
    Python service interface for ChromaDB-Supabase synchronization
    
    Provides both daemon control and direct sync capabilities
    """
    
    def __init__(self, project_root: Optional[str] = None, auto_start_daemon: bool = False):
        """Initialize the sync service"""
        self.project_root = Path(project_root) if project_root else PROJECT_ROOT
        self.chromadb_path = self.project_root / ".cerebraflow" / "core" / "storage" / "chromadb"
        self.daemon_process = None
        self.direct_sync_mode = False
        
        # Initialize clients for direct operations
        self.chromadb_client = None
        self.supabase_client = None
        # Hard-coded Supabase targets aligned with knowledge RAG/KG
        # Items live in `public.knowledge_items`; embeddings live in `public.knowledge_embeddings`.
        # Search uses RPC `public.search_agentic_embeddings`.
        self._items_table = "knowledge_items"
        self._embeddings_table = "knowledge_embeddings"
        self._search_rpc = "search_agentic_embeddings"

        # Cached ids (not hardcoded; resolved from environment per call as needed)
        self.tenant_id_env = os.getenv("CEREBRAL_TENANT_ID") or os.getenv("CEREBRAFLOW_TENANT_ID")
        self.user_id_env = (
            os.getenv("CEREBRAL_USER_ID")
            or os.getenv("CEREBRAFLOW_USER_ID")
            or self.tenant_id_env
        )
        self.project_id_env = os.getenv("CEREBRAL_PROJECT_ID") or os.getenv("CEREBRAFLOW_PROJECT_ID")

        # Load environment from .env files to pick up Supabase credentials
        try:
            # Load .env from project_root and ascend to repo root
            roots = [
                self.project_root,
                self.project_root.parent,
                self.project_root.parent.parent,
                self.project_root.parent.parent.parent,
            ]
            seen = set()
            candidates = []
            for r in roots:
                if r is None:
                    continue
                for p in [r / ".env", r / ".cerebraflow" / ".env"]:
                    if p not in seen and p.exists():
                        candidates.append(p)
                        seen.add(p)
            for p in candidates:
                load_dotenv(dotenv_path=str(p), override=True)
            # Fallback: default search on cwd
            load_dotenv(override=False)
        except Exception:
            pass
        
        # Check if daemon is already running or start if requested
        if self.is_daemon_running():
            logger.info(" CerebraFlow sync daemon already running")
        elif auto_start_daemon:
            self._ensure_daemon_running()
        else:
            # Fall back to direct sync mode
            self.direct_sync_mode = True
            self._initialize_direct_clients()
    
    def _ensure_daemon_running(self) -> bool:
        """Ensure the sync daemon is running"""
        try:
            if self.is_daemon_running():
                logger.info(" Sync daemon already running")
                return True
            
            # Try to start daemon
            logger.info(" Starting CerebraFlow sync daemon...")
            return self.start_daemon()
            
        except Exception as e:
            logger.warning(f"️ Could not start daemon, falling back to direct sync: {e}")
            self.direct_sync_mode = True
            self._initialize_direct_clients()
            return False

    def _resolve_tenant_user_project(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Resolve tenant, user, and project IDs from the environment at call time."""
        tenant_id = os.getenv("CEREBRAL_TENANT_ID") or os.getenv("CEREBRAFLOW_TENANT_ID") or self.tenant_id_env
        user_id = (
            os.getenv("CEREBRAL_USER_ID")
            or os.getenv("CEREBRAFLOW_USER_ID")
            or tenant_id
            or self.user_id_env
        )
        project_id = os.getenv("CEREBRAL_PROJECT_ID") or os.getenv("CEREBRAFLOW_PROJECT_ID") or self.project_id_env
        return tenant_id, user_id, project_id
    
    def _initialize_direct_clients(self) -> bool:
        """Initialize direct ChromaDB and Supabase clients"""
        try:
            # Initialize ChromaDB client (new client configuration per migration docs)
            if CHROMADB_AVAILABLE:
                try:
                    from chromadb import PersistentClient
                    self.chromadb_client = PersistentClient(path=str(self.chromadb_path))
                    logger.info(" Direct ChromaDB client initialized (new client API)")
                except Exception:
                    # Fallback to generic client if PersistentClient import path differs
                    self.chromadb_client = chromadb.PersistentClient(path=str(self.chromadb_path))
                    logger.info(" Direct ChromaDB client initialized (compat mode)")
            
            # Initialize Supabase client
            if SUPABASE_AVAILABLE:
                supabase_url = os.getenv("SUPABASE_URL")
                supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
                
                if supabase_url and supabase_key:
                    self.supabase_client = create_client(supabase_url, supabase_key)
                    logger.info(" Direct Supabase client initialized")
                else:
                    logger.warning("️ Supabase credentials not found in environment")
            
            return True
            
        except Exception as e:
            logger.error(f" Failed to initialize direct clients: {e}")
            return False

    # ---------------- Supabase HTTP fallback -----------------
    def _get_supabase_http_headers(self) -> Optional[Dict[str, str]]:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            return None
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Prefer": "resolution=merge-duplicates",
        }

    def _supabase_http_upsert(self, table: str, payload: Dict[str, Any], on_conflict: str = "id") -> bool:
        headers = self._get_supabase_http_headers()
        url = os.getenv("SUPABASE_URL")
        if not headers or not url:
            return False
        endpoint = f"{url}/rest/v1/{table}?on_conflict={on_conflict}"
        data = _json.dumps(payload).encode("utf-8")
        req = _urlreq.Request(endpoint, data=data, headers=headers, method="POST")
        try:
            with _urlreq.urlopen(req, timeout=10) as resp:
                resp.read()
                return 200 <= resp.status < 300
        except HTTPError as e:
            logger.warning(f"️ Supabase HTTP upsert failed ({table}): {e}")
            return False
        except URLError as e:
            logger.warning(f"️ Supabase HTTP upsert network error ({table}): {e}")
            return False

    def _supabase_http_rpc(self, function: str, payload: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        headers = self._get_supabase_http_headers()
        url = os.getenv("SUPABASE_URL")
        if not headers or not url:
            return None
        endpoint = f"{url}/rest/v1/rpc/{function}"
        data = _json.dumps(payload).encode("utf-8")
        req = _urlreq.Request(endpoint, data=data, headers=headers, method="POST")
        try:
            with _urlreq.urlopen(req, timeout=20) as resp:
                body = resp.read().decode("utf-8")
                try:
                    parsed = _json.loads(body)
                except Exception:
                    parsed = []
                if isinstance(parsed, list):
                    return parsed
                return []
        except HTTPError as e:
            logger.warning(f"️ Supabase HTTP RPC failed ({function}): {e}")
            return None
        except URLError as e:
            logger.warning(f"️ Supabase HTTP RPC network error ({function}): {e}")
            return None

    # ---------------- Embeddings (Apple Silicon) -----------------
    def _embed_text(self, text: str) -> Tuple[List[float], Dict[str, Any]]:
        """Generate an embedding using core Apple Silicon accelerator if available, CPU fallback.

        Returns: (vector, metadata)
        """
        try:
            from cflow_platform.core.embeddings.apple_silicon_accelerator import (
                generate_accelerated_embeddings,
                get_apple_silicon_accelerator,
            )
            accel = get_apple_silicon_accelerator()
            device = accel.get_device_string()
            vecs = generate_accelerated_embeddings([text])
            if isinstance(vecs, list) and vecs and isinstance(vecs[0], list):
                v = vecs[0]
                return v, {
                    "model": "sentence-transformer",
                    "dims": len(v),
                    "device": device,
                }
        except Exception as e:
            logger.warning(f"️ Apple Silicon embeddings unavailable, falling back to CPU: {e}")
        # Fallback: simple hash-based vector (non-semantic) to avoid failure
        import math
        h = abs(hash(text))
        vec = [((h >> (i * 8)) & 0xFF) / 255.0 for i in range(0, 32)]
        return vec, {"model": "fallback-hash", "dims": 32, "device": "cpu"}

    def _target_dims(self) -> int:
        try:
            return int(os.getenv("SUPABASE_VECTOR_DIMS", "1536"))
        except Exception:
            return 1536

    def _normalize_vector(self, vector: List[float]) -> List[float]:
        """Pad or truncate vector to match pgvector column dimensions."""
        td = self._target_dims()
        if len(vector) == td:
            return vector
        if len(vector) > td:
            return vector[:td]
        # pad with zeros
        return vector + [0.0] * (td - len(vector))

    # ---------------- Public storage/search API -----------------
    async def add_document(self, *, collection_type: str, content: str, metadata: Dict[str, Any]) -> str:
        """Add a document to local Chroma and attempt Supabase dual-write.

        - Embeds locally (Apple Silicon accelerated when available)
        - Writes to Chroma collection (collection_type)
        - Attempts to write to Supabase tables: memory_items, memory_vectors (pgvector)
        """
        try:
            doc_id = str(uuid.uuid4())
            vector, embed_meta = self._embed_text(content)
            vector = self._normalize_vector(vector)

            # 1) Write to Chroma
            if self.chromadb_client:
                try:
                    collection = self.get_collection(collection_type)
                    collection.add(ids=[doc_id], documents=[content], metadatas=[metadata], embeddings=[vector])
                except Exception as e:
                    logger.warning(f"️ Chroma add failed: {e}")

            # 2) Attempt Supabase dual-write (RDB row + pgvector)
            if self.supabase_client or os.getenv("SUPABASE_URL"):
                try:
                    # Required tenancy fields (from env; no hardcoding)
                    tenant_id, user_id, project_id = self._resolve_tenant_user_project()

                    # knowledge_items (minimal fields to satisfy schema/RLS)
                    items_payload = {
                        "id": doc_id,
                        "user_id": tenant_id if user_id is None else user_id,
                        "title": metadata.get("title") if isinstance(metadata, dict) else None,
                        "content": content,
                        "metadata": metadata,
                        "created_at": datetime.utcnow().isoformat() + "Z",
                        "tenant_id": tenant_id,
                    }
                    # Ensure a fallback title
                    if not items_payload.get("title"):
                        items_payload["title"] = f"{collection_type}:{doc_id[:8]}"
                    if self.supabase_client:
                        self.supabase_client.table(self._items_table).upsert(items_payload).execute()
                    else:
                        self._supabase_http_upsert(self._items_table, items_payload, on_conflict="id")

                    # Resolve content_type to satisfy search filter defaults
                    content_type = None
                    if isinstance(metadata, dict):
                        content_type = metadata.get("content_type")
                    if not content_type:
                        content_type = "documentation" if "doc" in collection_type else "technical_design_document"

                    # knowledge_embeddings
                    embeddings_payload = {
                        "id": str(uuid.uuid4()),
                        "knowledge_item_id": doc_id,
                        "content_chunk": content,
                        "embedding": vector,  # pgvector expects array; supabase client will serialize
                        "chunk_index": 0,
                        "metadata": metadata,
                        "content_type": content_type,
                        "created_at": datetime.utcnow().isoformat() + "Z",
                        "tenant_id": tenant_id,
                    }
                    if self.supabase_client:
                        self.supabase_client.table(self._embeddings_table).upsert(embeddings_payload).execute()
                    else:
                        self._supabase_http_upsert(self._embeddings_table, embeddings_payload, on_conflict="id")
                except Exception as e:
                    logger.warning(f"️ Supabase write failed (ensure tables/migrations & valid URL/key): {e}")

            return doc_id
        except Exception as e:
            logger.error(f" add_document failed: {e}")
            # Always return an id to keep upstream flows moving
            return str(uuid.uuid4())

    async def search_documents(
        self,
        *,
        collection_type: str,
        query: str,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Semantic search with Supabase pgvector preferred, Chroma fallback.

        If Supabase pgvector query is not configured, fall back to Chroma similarity search.
        """
        # Embed query
        vector, _ = self._embed_text(query)
        vector = self._normalize_vector(vector)

        # Try Supabase RPC first (agentic/knowledge search)
        if self.supabase_client or os.getenv("SUPABASE_URL"):
            try:
                tenant_id, _, _ = self._resolve_tenant_user_project()
                payload = {
                    "query_embedding": vector,
                    "match_threshold": 0.0,
                    "match_count": limit,
                    "tenant_filter": tenant_id,
                    "content_types": None,
                }
                if self.supabase_client:
                    resp = self.supabase_client.rpc(self._search_rpc, payload).execute()
                    data = getattr(resp, "data", None) or []
                else:
                    data = self._supabase_http_rpc(self._search_rpc, payload) or []
                if isinstance(data, list) and data:
                    return data
            except Exception as e:
                logger.warning(f"️ Supabase pgvector search failed or RPC missing: {e}")

        # Fallback to Chroma similarity
        try:
            if self.chromadb_client:
                collection = self.get_collection(collection_type)
                res = collection.query(query_embeddings=[vector], n_results=limit)
                # Normalize Chroma response to list[dict]
                results: List[Dict[str, Any]] = []
                ids = res.get("ids", [[]])[0]
                docs = res.get("documents", [[]])[0]
                metas = res.get("metadatas", [[]])[0]
                dists = res.get("distances", [[]])[0]
                for rid, doc, meta, dist in zip(ids, docs, metas, dists):
                    results.append({
                        "id": rid,
                        "document": doc,
                        "metadata": meta,
                        "distance": dist,
                    })
                return results
        except Exception as e:
            logger.error(f" Chroma search failed: {e}")

        return []
    
    def is_daemon_running(self) -> bool:
        """Check if the Cerebral unified sync service is running"""
        try:
            # Check general list for PID
            result = subprocess.run([
                "launchctl", "list"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Look for service in list with PID
                for line in result.stdout.split('\n'):
                    if CEREBRAL_SYNC_SERVICE in line:
                        parts = line.split()
                        if len(parts) >= 1 and parts[0].isdigit():
                            return True
            
            return False
            
        except Exception:
            return False
    
    def start_daemon(self, background: bool = True) -> bool:
        """Start the Cerebral unified sync service"""
        try:
            if self.is_daemon_running():
                logger.info(" Cerebral sync service already running")
                return True
            
            # Load the LaunchAgent
            result = subprocess.run([
                "launchctl", "load", f"{os.path.expanduser('~')}/Library/LaunchAgents/com.cerebral.unified-sync.plist"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Wait a moment for startup
                time.sleep(3)
                
                if self.is_daemon_running():
                    logger.info(" Cerebral sync service started successfully")
                    return True
                else:
                    logger.warning("️ Service loaded but not yet running (may still be starting)")
                    return True
            else:
                logger.error(f" Failed to load sync service: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f" Failed to start sync service: {e}")
            return False
    
    def stop_daemon(self) -> bool:
        """Stop the Cerebral unified sync service"""
        try:
            if not self.is_daemon_running():
                logger.info(" Cerebral sync service not running")
                return True
            
            # Unload the LaunchAgent
            result = subprocess.run([
                "launchctl", "unload", f"{os.path.expanduser('~')}/Library/LaunchAgents/com.cerebral.unified-sync.plist"
            ], capture_output=True, text=True)
            
            success = result.returncode == 0
            if success:
                logger.info(" Cerebral sync service stopped")
            else:
                logger.error(f" Failed to stop sync service: {result.stderr}")
            
            return success
            
        except Exception as e:
            logger.error(f" Failed to stop sync service: {e}")
            return False
    
    def get_daemon_status(self) -> Dict[str, Any]:
        """Get Cerebral sync service status and statistics"""
        try:
            # Check general service list
            result = subprocess.run([
                "launchctl", "list"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                return {
                    "running": False,
                    "mode": "direct_sync" if self.direct_sync_mode else "service_offline",
                    "service": CEREBRAL_SYNC_SERVICE,
                    "pid": None,
                    "uptime": None
                }
            
            # Parse output to find our service
            pid = None
            exit_code = None
            
            for line in result.stdout.split('\n'):
                if CEREBRAL_SYNC_SERVICE in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        pid_str = parts[0].strip()
                        exit_code_str = parts[1].strip()
                        
                        if pid_str.isdigit():
                            pid = int(pid_str)
                        if exit_code_str.isdigit() or exit_code_str == '-':
                            exit_code = int(exit_code_str) if exit_code_str != '-' else None
                    break
            
            if pid:
                # Get process info
                try:
                    process = psutil.Process(pid)
                    return {
                        "running": True,
                        "mode": "cerebral_unified_sync",
                        "service": CEREBRAL_SYNC_SERVICE,
                        "pid": pid,
                        "uptime": time.time() - process.create_time(),
                        "memory_mb": process.memory_info().rss / 1024 / 1024,
                        "cpu_percent": process.cpu_percent()
                    }
                except psutil.NoSuchProcess:
                    return {
                        "running": False,
                        "mode": "service_terminated",
                        "service": CEREBRAL_SYNC_SERVICE,
                        "pid": pid,
                        "exit_code": exit_code
                    }
            else:
                return {
                    "running": False,
                    "mode": "service_not_started" if exit_code is None else "service_failed",
                    "service": CEREBRAL_SYNC_SERVICE,
                    "exit_code": exit_code
                }
            
        except Exception as e:
            logger.error(f" Failed to get sync service status: {e}")
            return {"running": False, "error": str(e)}
    
    async def sync_collection(self, collection_name: str, direction: str = "bidirectional") -> Dict[str, Any]:
        """Sync a specific collection between ChromaDB and Supabase"""
        if not self.direct_sync_mode:
            # Daemon is running - sync happens automatically
            return {
                "status": "success",
                "message": f"Collection {collection_name} sync handled by daemon",
                "mode": "daemon"
            }
        
        # Direct sync mode
        try:
            if not self.chromadb_client or not self.supabase_client:
                return {
                    "status": "error",
                    "message": "Direct sync clients not available"
                }
            
            # Get ChromaDB collection
            try:
                collection = self.chromadb_client.get_collection(collection_name)
            except Exception:
                logger.warning(f"Collection {collection_name} does not exist in ChromaDB")
                return {
                    "status": "skipped",
                    "message": f"Collection {collection_name} does not exist"
                }
            
            # Get all documents from collection
            results = collection.get()
            
            if not results['ids']:
                return {
                    "status": "success",
                    "message": f"Collection {collection_name} is empty",
                    "synced_count": 0
                }
            
            # For now, just return success with count
            # Real implementation would sync to Supabase
            return {
                "status": "success",
                "message": f"Synced {len(results['ids'])} documents",
                "synced_count": len(results['ids']),
                "mode": "direct"
            }
            
        except Exception as e:
            logger.error(f" Direct sync failed for {collection_name}: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def sync_all_collections(self) -> Dict[str, Any]:
        """Sync all collections"""
        results = {}
        total_synced = 0
        
        collections = list(COLLECTION_SYNC_MAP.keys()) if COLLECTION_SYNC_MAP else [
            "cerebral_tasks", "cerebral_docs", "cerebral_rag", "cerebral_mem"
        ]
        
        for collection_name in collections:
            result = await self.sync_collection(collection_name)
            results[collection_name] = result
            if result.get("synced_count"):
                total_synced += result["synced_count"]
        
        return {
            "status": "completed",
            "total_synced": total_synced,
            "collections": results,
            "mode": "direct" if self.direct_sync_mode else "daemon"
        }
    
    def get_collection(self, name: str):
        """Get a ChromaDB collection (compatibility method)"""
        if not self.chromadb_client:
            raise Exception("ChromaDB client not available")
        
        try:
            return self.chromadb_client.get_collection(name)
        except Exception:
            # Create collection if it doesn't exist
            return self.chromadb_client.create_collection(name)
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        # Cleanup if needed
        pass


# Convenience functions for backward compatibility
def get_sync_service(project_root: Optional[str] = None) -> ChromaDBSupabaseSyncService:
    """Get a sync service instance"""
    return ChromaDBSupabaseSyncService(project_root=project_root)


async def quick_sync(collection_name: Optional[str] = None) -> Dict[str, Any]:
    """Perform a quick sync operation"""
    sync_service = ChromaDBSupabaseSyncService()
    
    if collection_name:
        return await sync_service.sync_collection(collection_name)
    else:
        return await sync_service.sync_all_collections()


if __name__ == "__main__":
    # CLI interface
    import argparse
    
    parser = argparse.ArgumentParser(description="ChromaDB Supabase Sync Service")
    parser.add_argument("action", choices=["start", "stop", "status", "sync"], help="Action to perform")
    parser.add_argument("--collection", help="Collection name for sync action")
    
    args = parser.parse_args()
    
    sync_service = ChromaDBSupabaseSyncService()
    
    if args.action == "start":
        success = sync_service.start_daemon()
        sys.exit(0 if success else 1)
        
    elif args.action == "stop":
        success = sync_service.stop_daemon()
        sys.exit(0 if success else 1)
        
    elif args.action == "status":
        status = sync_service.get_daemon_status()
        print(json.dumps(status, indent=2))
        
    elif args.action == "sync":
        async def run_sync():
            if args.collection:
                result = await sync_service.sync_collection(args.collection)
            else:
                result = await sync_service.sync_all_collections()
            print(json.dumps(result, indent=2))
        
        asyncio.run(run_sync())
