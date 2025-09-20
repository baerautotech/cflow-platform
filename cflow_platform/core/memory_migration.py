"""
BMAD Memory Migration

⚠️  DEPRECATED: This module is deprecated. Use cflow_platform.core.unified_database_schema instead.

YOLO MODE: Fast migration from local JSONL to Supabase memory_items table.
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


class BMADMemoryMigration:
    """YOLO Memory migration from JSONL to Supabase."""
    
    def __init__(self):
        self.supabase_client = None
        self.memory_file = Path(__file__).parent.parent.parent / ".cerebraflow" / "memory_items.jsonl"
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
                print("[INFO] YOLO: Supabase client created for memory migration")
            else:
                print("[INFO][INFO] YOLO: Supabase not available for memory migration")
                
        except Exception as e:
            print(f"[INFO][INFO] YOLO: Supabase setup failed: {e}")
    
    def read_jsonl_memory(self) -> Iterator[Dict[str, Any]]:
        """Read memory items from JSONL file (YOLO implementation)."""
        try:
            if not self.memory_file.exists():
                print(f"[INFO][INFO] YOLO: Memory file not found: {self.memory_file}")
                return
            
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        item = json.loads(line)
                        item['_line_number'] = line_num
                        yield item
                    except json.JSONDecodeError as e:
                        print(f"[INFO][INFO] YOLO: JSON decode error on line {line_num}: {e}")
                        continue
            
        except Exception as e:
            print(f"[INFO] YOLO: Failed to read JSONL memory: {e}")
    
    def migrate_memory_to_supabase(self, batch_size: int = 100) -> Dict[str, Any]:
        """Migrate memory items to Supabase (YOLO implementation)."""
        try:
            if not self.supabase_client:
                print("[INFO][INFO] YOLO: Supabase not available, skipping migration")
                return {"success": False, "reason": "Supabase not available"}
            
            print("[INFO] YOLO: Starting memory migration to Supabase...")
            
            migrated_count = 0
            error_count = 0
            batch = []
            
            for item in self.read_jsonl_memory():
                # Transform item for Supabase
                supabase_item = self._transform_memory_item(item)
                if supabase_item:
                    batch.append(supabase_item)
                    
                    if len(batch) >= batch_size:
                        success = self._insert_batch(batch)
                        if success:
                            migrated_count += len(batch)
                        else:
                            error_count += len(batch)
                        batch = []
            
            # Insert remaining items
            if batch:
                success = self._insert_batch(batch)
                if success:
                    migrated_count += len(batch)
                else:
                    error_count += len(batch)
            
            result = {
                "success": error_count == 0,
                "migrated_count": migrated_count,
                "error_count": error_count,
                "total_processed": migrated_count + error_count
            }
            
            print(f"[INFO] YOLO: Memory migration complete: {migrated_count} migrated, {error_count} errors")
            return result
            
        except Exception as e:
            print(f"[INFO] YOLO: Memory migration failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _transform_memory_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform memory item for Supabase (YOLO implementation)."""
        try:
            # Extract key fields
            original_id = item.get('id', '')
            memory_id = str(uuid.uuid4())  # Always generate new UUID
            content = item.get('content', '')
            metadata = item.get('metadata', {})
            
            # Add original ID to metadata for reference
            if original_id:
                metadata['original_id'] = original_id
            
            # Create Supabase record
            supabase_item = {
                "id": memory_id,
                "collection": item.get('collection', 'default'),
                "content": content,
                "metadata": metadata,
                "created_at": item.get('created_at', datetime.utcnow().isoformat()),
                "source": "jsonl_migration",
                "line_number": item.get('_line_number', 0)
            }
            
            return supabase_item
            
        except Exception as e:
            print(f"[INFO][INFO] YOLO: Failed to transform memory item: {e}")
            return None
    
    def _insert_batch(self, batch: List[Dict[str, Any]]) -> bool:
        """Insert batch of memory items (YOLO implementation)."""
        try:
            result = self.supabase_client.table("memory_items").insert(batch).execute()
            
            if result.data:
                print(f"[INFO] YOLO: Inserted batch of {len(batch)} memory items")
                return True
            else:
                print(f"[INFO] YOLO: Failed to insert batch of {len(batch)} items")
                return False
                
        except Exception as e:
            print(f"[INFO] YOLO: Batch insert failed: {e}")
            return False
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics (YOLO implementation)."""
        try:
            stats = {
                "jsonl_file_exists": self.memory_file.exists(),
                "jsonl_file_size": 0,
                "jsonl_item_count": 0,
                "supabase_item_count": 0
            }
            
            # Count JSONL items
            if self.memory_file.exists():
                stats["jsonl_file_size"] = self.memory_file.stat().st_size
                stats["jsonl_item_count"] = sum(1 for _ in self.read_jsonl_memory())
            
            # Count Supabase items
            if self.supabase_client:
                try:
                    result = self.supabase_client.table("memory_items").select("id", count="exact").execute()
                    stats["supabase_item_count"] = result.count or 0
                except Exception as e:
                    print(f"[INFO][INFO] YOLO: Failed to count Supabase items: {e}")
            
            return stats
            
        except Exception as e:
            print(f"[INFO] YOLO: Failed to get memory stats: {e}")
            return {}
    
    def verify_migration(self) -> bool:
        """Verify migration success (YOLO implementation)."""
        try:
            stats = self.get_memory_stats()
            
            print("Memory Migration Stats:")
            print(f"  JSONL file exists: {stats.get('jsonl_file_exists', False)}")
            print(f"  JSONL file size: {stats.get('jsonl_file_size', 0)} bytes")
            print(f"  JSONL items: {stats.get('jsonl_item_count', 0)}")
            print(f"  Supabase items: {stats.get('supabase_item_count', 0)}")
            
            # Check if migration was successful
            jsonl_count = stats.get('jsonl_item_count', 0)
            supabase_count = stats.get('supabase_item_count', 0)
            
            if jsonl_count > 0 and supabase_count >= jsonl_count:
                print("[INFO] YOLO: Migration verification successful")
                return True
            elif jsonl_count == 0:
                print("[INFO][INFO] YOLO: No JSONL items to migrate")
                return True
            else:
                print("[INFO] YOLO: Migration verification failed")
                return False
                
        except Exception as e:
            print(f"[INFO] YOLO: Migration verification failed: {e}")
            return False


# YOLO Global instance
memory_migration = BMADMemoryMigration()

# Alias for compatibility
MemoryMigration = BMADMemoryMigration


def get_memory_migration() -> BMADMemoryMigration:
    """Get global memory migration instance."""
    return memory_migration


# YOLO Test function
def test_memory_migration():
    """Test memory migration (YOLO style)."""
    print("[INFO] YOLO: Testing Memory Migration...")
    
    migration = get_memory_migration()
    
    # Get stats
    stats = migration.get_memory_stats()
    print(f"Memory stats: {stats}")
    
    # Run migration
    result = migration.migrate_memory_to_supabase()
    print(f"Migration result: {result}")
    
    # Verify migration
    verification = migration.verify_migration()
    print(f"Migration verification: {'[INFO]' if verification else '[INFO]'}")
    
    print("[INFO] YOLO: Memory migration test complete!")


if __name__ == "__main__":
    test_memory_migration()
