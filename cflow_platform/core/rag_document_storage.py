"""
BMAD RAG Document Storage

YOLO MODE: Fast implementation of RAG document storage for BMAD.
"""

import os
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Iterator
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")


class BMADRAGDocumentStorage:
    """YOLO RAG document storage for BMAD."""
    
    def __init__(self):
        self.supabase_client = None
        self.bmad_root = Path(__file__).parent.parent.parent / "vendor" / "bmad"
        self._ensure_supabase()
    
    def _ensure_supabase(self) -> None:
        """Create Supabase client (YOLO style)."""
        try:
            from supabase import create_client
            from .config.supabase_config import get_api_key, get_rest_url
            
            url = get_rest_url()
            key = get_api_key(secure=True)
            
            if url and key:
                self.supabase_client = create_client(url, key)
                print("[INFO] YOLO: Supabase client created for RAG storage")
            else:
                print("[INFO][INFO] YOLO: Supabase not available for RAG storage")
                
        except Exception as e:
            print(f"[INFO][INFO] YOLO: Supabase setup failed: {e}")
    
    def store_document_chunks(self, doc_id: str, chunks: List[Dict[str, Any]]) -> bool:
        """Store document chunks for RAG (YOLO implementation)."""
        try:
            if not self.supabase_client:
                print(f"[INFO][INFO] YOLO: Mock storing {len(chunks)} chunks for doc {doc_id}")
                return True
            
            # Transform chunks for storage
            rag_items = []
            for i, chunk in enumerate(chunks):
                rag_item = {
                    "id": str(uuid.uuid4()),
                    "knowledge_item_id": doc_id,  # Use doc_id as knowledge_item_id
                    "chunk_index": i,
                    "content_chunk": chunk.get("content", ""),
                    "metadata": chunk.get("metadata", {}),
                    "embedding": chunk.get("embedding", None),
                    "content_type": chunk.get("metadata", {}).get("type", "unknown"),
                    "created_at": datetime.utcnow().isoformat(),
                    "tenant_id": "00000000-0000-0000-0000-000000000100"  # Default tenant
                }
                rag_items.append(rag_item)
            
            # Store in batches
            batch_size = 50
            for i in range(0, len(rag_items), batch_size):
                batch = rag_items[i:i + batch_size]
                result = self.supabase_client.table("knowledge_embeddings").insert(batch).execute()
                
                if not result.data:
                    print(f"[INFO] YOLO: Failed to store batch {i//batch_size + 1}")
                    return False
            
            print(f"[INFO] YOLO: Stored {len(chunks)} chunks for doc {doc_id}")
            return True
            
        except Exception as e:
            print(f"[INFO] YOLO: Failed to store document chunks: {e}")
            return False
    
    def chunk_document(self, doc_content: str, doc_type: str) -> List[Dict[str, Any]]:
        """Chunk document content for RAG (YOLO implementation)."""
        try:
            chunks = []
            
            if doc_type == "PRD":
                chunks = self._chunk_prd(doc_content)
            elif doc_type == "ARCH":
                chunks = self._chunk_architecture(doc_content)
            elif doc_type == "STORY":
                chunks = self._chunk_story(doc_content)
            else:
                chunks = self._chunk_generic(doc_content)
            
            print(f"[INFO] YOLO: Created {len(chunks)} chunks for {doc_type} document")
            return chunks
            
        except Exception as e:
            print(f"[INFO] YOLO: Failed to chunk document: {e}")
            return []
    
    def _chunk_prd(self, content: str) -> List[Dict[str, Any]]:
        """Chunk PRD document (YOLO implementation)."""
        chunks = []
        lines = content.split('\n')
        current_chunk = ""
        chunk_metadata = {"type": "PRD", "section": "unknown"}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect section headers
            if line.startswith('#') or line.startswith('##'):
                # Save previous chunk
                if current_chunk:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "metadata": chunk_metadata.copy()
                    })
                
                # Start new chunk
                current_chunk = line + "\n"
                chunk_metadata["section"] = line.replace('#', '').strip().lower()
            else:
                current_chunk += line + "\n"
                
                # Split large chunks
                if len(current_chunk) > 1000:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "metadata": chunk_metadata.copy()
                    })
                    current_chunk = ""
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                "content": current_chunk.strip(),
                "metadata": chunk_metadata.copy()
            })
        
        return chunks
    
    def _chunk_architecture(self, content: str) -> List[Dict[str, Any]]:
        """Chunk Architecture document (YOLO implementation)."""
        chunks = []
        lines = content.split('\n')
        current_chunk = ""
        chunk_metadata = {"type": "ARCH", "section": "unknown"}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect section headers
            if line.startswith('#') or line.startswith('##'):
                # Save previous chunk
                if current_chunk:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "metadata": chunk_metadata.copy()
                    })
                
                # Start new chunk
                current_chunk = line + "\n"
                chunk_metadata["section"] = line.replace('#', '').strip().lower()
            else:
                current_chunk += line + "\n"
                
                # Split large chunks
                if len(current_chunk) > 1000:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "metadata": chunk_metadata.copy()
                    })
                    current_chunk = ""
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                "content": current_chunk.strip(),
                "metadata": chunk_metadata.copy()
            })
        
        return chunks
    
    def _chunk_story(self, content: str) -> List[Dict[str, Any]]:
        """Chunk Story document (YOLO implementation)."""
        chunks = []
        lines = content.split('\n')
        current_chunk = ""
        chunk_metadata = {"type": "STORY", "section": "unknown"}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect section headers
            if line.startswith('#') or line.startswith('##'):
                # Save previous chunk
                if current_chunk:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "metadata": chunk_metadata.copy()
                    })
                
                # Start new chunk
                current_chunk = line + "\n"
                chunk_metadata["section"] = line.replace('#', '').strip().lower()
            else:
                current_chunk += line + "\n"
                
                # Split large chunks
                if len(current_chunk) > 1000:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "metadata": chunk_metadata.copy()
                    })
                    current_chunk = ""
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                "content": current_chunk.strip(),
                "metadata": chunk_metadata.copy()
            })
        
        return chunks
    
    def _chunk_generic(self, content: str) -> List[Dict[str, Any]]:
        """Chunk generic document (YOLO implementation)."""
        chunks = []
        words = content.split()
        chunk_size = 200  # words per chunk
        
        for i in range(0, len(words), chunk_size):
            chunk_words = words[i:i + chunk_size]
            chunk_content = ' '.join(chunk_words)
            
            chunks.append({
                "content": chunk_content,
                "metadata": {
                    "type": "generic",
                    "chunk_index": i // chunk_size,
                    "word_count": len(chunk_words)
                }
            })
        
        return chunks
    
    def index_document(self, doc_id: str, doc_content: str, doc_type: str) -> bool:
        """Index document for RAG (YOLO implementation)."""
        try:
            print(f"[INFO] YOLO: Indexing {doc_type} document {doc_id}...")
            
            # Chunk the document
            chunks = self.chunk_document(doc_content, doc_type)
            
            if not chunks:
                print(f"[INFO] YOLO: No chunks created for document {doc_id}")
                return False
            
            # Store chunks
            success = self.store_document_chunks(doc_id, chunks)
            
            if success:
                print(f"[INFO] YOLO: Document {doc_id} indexed with {len(chunks)} chunks")
                return True
            else:
                print(f"[INFO] YOLO: Failed to store chunks for document {doc_id}")
                return False
                
        except Exception as e:
            print(f"[INFO] YOLO: Document indexing failed: {e}")
            return False
    
    def search_documents(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search documents using RAG (YOLO implementation)."""
        try:
            if not self.supabase_client:
                print(f"[INFO][INFO] YOLO: Mock search for '{query}'")
                return []
            
            # Simple text search (YOLO implementation)
            result = self.supabase_client.table("knowledge_embeddings").select(
                "*"
            ).ilike("content_chunk", f"%{query}%").limit(limit).execute()
            
            if result.data:
                print(f"[INFO] YOLO: Found {len(result.data)} results for '{query}'")
                return result.data
            else:
                print(f"[INFO] YOLO: No results found for '{query}'")
                return []
                
        except Exception as e:
            print(f"[INFO] YOLO: Document search failed: {e}")
            return []
    
    def get_rag_stats(self) -> Dict[str, Any]:
        """Get RAG storage statistics (YOLO implementation)."""
        try:
            stats = {
                "total_chunks": 0,
                "documents_indexed": 0,
                "storage_size": 0
            }
            
            if self.supabase_client:
                # Count chunks
                result = self.supabase_client.table("knowledge_embeddings").select("id", count="exact").execute()
                stats["total_chunks"] = result.count or 0
                
                # Count unique documents
                result = self.supabase_client.table("knowledge_embeddings").select("knowledge_item_id").execute()
                unique_docs = set(item["knowledge_item_id"] for item in result.data)
                stats["documents_indexed"] = len(unique_docs)
            
            return stats
            
        except Exception as e:
            print(f"[INFO] YOLO: Failed to get RAG stats: {e}")
            return {}


# YOLO Global instance
rag_storage = BMADRAGDocumentStorage()

# Alias for compatibility
RAGDocumentStorage = BMADRAGDocumentStorage


def get_rag_storage() -> BMADRAGDocumentStorage:
    """Get global RAG document storage instance."""
    return rag_storage


# YOLO Test function
def test_rag_storage():
    """Test RAG document storage (YOLO style)."""
    print("[INFO] YOLO: Testing RAG Document Storage...")
    
    storage = get_rag_storage()
    
    # Test document chunking
    test_content = """
    # Test PRD Document
    
    ## Overview
    This is a test PRD document for YOLO testing.
    
    ## Requirements
    - Requirement 1: Test requirement
    - Requirement 2: Another test requirement
    
    ## Success Criteria
    The system should work correctly.
    """
    
    chunks = storage.chunk_document(test_content, "PRD")
    print(f"Document chunking: {len(chunks)} chunks created")
    
    # Test document indexing
    test_doc_id = str(uuid.uuid4())
    indexing_success = storage.index_document(test_doc_id, test_content, "PRD")
    print(f"Document indexing: {'[INFO]' if indexing_success else '[INFO]'}")
    
    # Test document search
    search_results = storage.search_documents("test requirement", limit=5)
    print(f"Document search: {len(search_results)} results")
    
    # Get stats
    stats = storage.get_rag_stats()
    print(f"RAG stats: {stats}")
    
    print("[INFO] YOLO: RAG document storage test complete!")


if __name__ == "__main__":
    test_rag_storage()
