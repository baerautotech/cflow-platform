"""
BMAD Expansion Pack Storage

YOLO MODE: Fast implementation of expansion pack storage for BMAD.
"""

import os
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")


class BMADExpansionPackStorage:
    """YOLO Expansion Pack storage for BMAD."""
    
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
                print("[INFO] YOLO: Supabase client created for expansion packs")
            else:
                print("[INFO][INFO] YOLO: Supabase not available, using local storage")
                
        except Exception as e:
            print(f"[INFO][INFO] YOLO: Supabase setup failed: {e}")
    
    def list_expansion_packs(self) -> List[Dict[str, Any]]:
        """List available expansion packs (YOLO implementation)."""
        try:
            packs = []
            expansion_dir = self.bmad_root / "expansion-packs"
            
            if not expansion_dir.exists():
                print("[INFO][INFO] YOLO: No expansion-packs directory found")
                return packs
            
            for pack_dir in expansion_dir.iterdir():
                if pack_dir.is_dir():
                    pack_info = self._get_pack_info(pack_dir)
                    if pack_info:
                        packs.append(pack_info)
            
            print(f"[INFO] YOLO: Found {len(packs)} expansion packs")
            return packs
            
        except Exception as e:
            print(f"[INFO] YOLO: Failed to list expansion packs: {e}")
            return []
    
    def _get_pack_info(self, pack_dir: Path) -> Optional[Dict[str, Any]]:
        """Get pack information (YOLO style)."""
        try:
            # Look for README.md or package.json
            readme_file = pack_dir / "README.md"
            package_file = pack_dir / "package.json"
            
            pack_info = {
                "id": pack_dir.name,
                "name": pack_dir.name,
                "path": str(pack_dir),
                "installed": True,
                "enabled": False,
                "version": "1.0.0",
                "description": "",
                "created_at": datetime.utcnow().isoformat()
            }
            
            if readme_file.exists():
                with open(readme_file, 'r') as f:
                    content = f.read()
                    # Extract description from first few lines
                    lines = content.split('\n')
                    for line in lines[:5]:
                        if line.strip() and not line.startswith('#'):
                            pack_info["description"] = line.strip()
                            break
            
            if package_file.exists():
                with open(package_file, 'r') as f:
                    package_data = json.load(f)
                    pack_info.update({
                        "name": package_data.get("name", pack_dir.name),
                        "version": package_data.get("version", "1.0.0"),
                        "description": package_data.get("description", "")
                    })
            
            return pack_info
            
        except Exception as e:
            print(f"[INFO][INFO] YOLO: Failed to get pack info for {pack_dir}: {e}")
            return None
    
    def install_expansion_pack(self, pack_id: str, pack_data: Dict[str, Any]) -> bool:
        """Install expansion pack to database (YOLO implementation)."""
        try:
            if not self.supabase_client:
                print(f"[INFO][INFO] YOLO: Mock installing pack {pack_id}")
                return True
            
            # Create pack record
            pack_record = {
                "id": str(uuid.uuid4()),
                "pack_id": pack_id,
                "name": pack_data.get("name", pack_id),
                "version": pack_data.get("version", "1.0.0"),
                "description": pack_data.get("description", ""),
                "status": "installed",
                "enabled": False,
                "metadata": pack_data,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Store in database
            result = self.supabase_client.table("bmad_expansion_packs").insert(pack_record).execute()
            
            if result.data:
                print(f"[INFO] YOLO: Pack {pack_id} installed successfully")
                return True
            else:
                print(f"[INFO] YOLO: Failed to install pack {pack_id}")
                return False
                
        except Exception as e:
            print(f"[INFO] YOLO: Pack installation failed: {e}")
            return False
    
    def enable_expansion_pack(self, pack_id: str) -> bool:
        """Enable expansion pack (YOLO implementation)."""
        try:
            if not self.supabase_client:
                print(f"[INFO][INFO] YOLO: Mock enabling pack {pack_id}")
                return True
            
            # Update pack status
            result = self.supabase_client.table("bmad_expansion_packs").update({
                "enabled": True,
                "status": "enabled",
                "updated_at": datetime.utcnow().isoformat()
            }).eq("pack_id", pack_id).execute()
            
            if result.data:
                print(f"[INFO] YOLO: Pack {pack_id} enabled successfully")
                return True
            else:
                print(f"[INFO] YOLO: Failed to enable pack {pack_id}")
                return False
                
        except Exception as e:
            print(f"[INFO] YOLO: Pack enable failed: {e}")
            return False
    
    def get_enabled_packs(self) -> List[Dict[str, Any]]:
        """Get enabled expansion packs (YOLO implementation)."""
        try:
            if not self.supabase_client:
                print("[INFO][INFO] YOLO: Mock getting enabled packs")
                return []
            
            result = self.supabase_client.table("bmad_expansion_packs").select("*").eq("enabled", True).execute()
            
            if result.data:
                print(f"[INFO] YOLO: Found {len(result.data)} enabled packs")
                return result.data
            else:
                print("[INFO] YOLO: No enabled packs found")
                return []
                
        except Exception as e:
            print(f"[INFO] YOLO: Failed to get enabled packs: {e}")
            return []
    
    def sync_local_packs(self) -> bool:
        """Sync local expansion packs to database (YOLO implementation)."""
        try:
            print("[INFO] YOLO: Syncing local expansion packs...")
            
            local_packs = self.list_expansion_packs()
            synced_count = 0
            
            for pack in local_packs:
                success = self.install_expansion_pack(pack["id"], pack)
                if success:
                    synced_count += 1
            
            print(f"[INFO] YOLO: Synced {synced_count}/{len(local_packs)} packs")
            return synced_count > 0
            
        except Exception as e:
            print(f"[INFO] YOLO: Pack sync failed: {e}")
            return False


# YOLO Global instance
expansion_storage = BMADExpansionPackStorage()

# Alias for compatibility
ExpansionPackStorage = BMADExpansionPackStorage


def get_expansion_storage() -> BMADExpansionPackStorage:
    """Get global expansion pack storage instance."""
    return expansion_storage


# YOLO Test function
def test_expansion_storage():
    """Test expansion pack storage (YOLO style)."""
    print("[INFO] YOLO: Testing Expansion Pack Storage...")
    
    storage = get_expansion_storage()
    
    # Test listing packs
    packs = storage.list_expansion_packs()
    print(f"Local packs found: {len(packs)}")
    
    if packs:
        for pack in packs[:3]:  # Show first 3
            print(f"  - {pack['name']}: {pack['description'][:50]}...")
    
    # Test syncing packs
    sync_success = storage.sync_local_packs()
    print(f"Pack sync: {'[INFO]' if sync_success else '[INFO]'}")
    
    # Test getting enabled packs
    enabled_packs = storage.get_enabled_packs()
    print(f"Enabled packs: {len(enabled_packs)}")
    
    print("[INFO] YOLO: Expansion pack storage test complete!")


if __name__ == "__main__":
    test_expansion_storage()

