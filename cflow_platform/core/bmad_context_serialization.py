"""
BMAD Context Serialization System

This module implements context serialization and deserialization for Phase 2:
Unified Persona Activation. It provides efficient storage and retrieval
of persona contexts, session states, and task checkpoints.
"""

import asyncio
import json
import logging
import pickle
import uuid
import zlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, BinaryIO, TextIO
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import hashlib
import base64

from .bmad_persona_context import PersonaContext, SessionState, PersonaType, ContextState
from .bmad_task_checkpoint import TaskState, Checkpoint, CheckpointType, CheckpointScope

logger = logging.getLogger(__name__)


class SerializationFormat(Enum):
    """Enumeration of serialization formats."""
    JSON = "json"
    PICKLE = "pickle"
    COMPRESSED_PICKLE = "compressed_pickle"
    BINARY = "binary"


class SerializationVersion(Enum):
    """Enumeration of serialization versions."""
    V1_0 = "1.0"
    V1_1 = "1.1"  # Added compression support
    V1_2 = "1.2"  # Added binary format support


@dataclass
class SerializationMetadata:
    """Metadata for serialized context data."""
    version: str
    format: str
    timestamp: str
    checksum: str
    size: int
    compression_ratio: Optional[float] = None
    schema_version: Optional[str] = None


class BMADContextSerializer:
    """
    Handles serialization and deserialization of BMAD contexts.
    
    This class provides efficient serialization of persona contexts,
    session states, and task checkpoints with support for multiple
    formats and compression.
    """
    
    def __init__(self, 
                 default_format: SerializationFormat = SerializationFormat.JSON,
                 enable_compression: bool = True,
                 compression_level: int = 6):
        """
        Initialize the context serializer.
        
        Args:
            default_format: Default serialization format
            enable_compression: Whether to enable compression for supported formats
            compression_level: Compression level (1-9)
        """
        self.default_format = default_format
        self.enable_compression = enable_compression
        self.compression_level = compression_level
        self.serialization_version = SerializationVersion.V1_2
    
    async def serialize_persona_context(self, 
                                      persona_context: PersonaContext,
                                      format: Optional[SerializationFormat] = None) -> bytes:
        """
        Serialize a persona context.
        
        Args:
            persona_context: Persona context to serialize
            format: Serialization format (uses default if None)
            
        Returns:
            Serialized data as bytes
        """
        format = format or self.default_format
        
        # Convert to dictionary
        data = asdict(persona_context)
        
        # Add serialization metadata
        data["_serialization_metadata"] = {
            "version": self.serialization_version.value,
            "format": format.value,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "persona_context"
        }
        
        return await self._serialize_data(data, format)
    
    async def deserialize_persona_context(self, 
                                        data: bytes,
                                        format: Optional[SerializationFormat] = None) -> PersonaContext:
        """
        Deserialize a persona context.
        
        Args:
            data: Serialized data
            format: Serialization format (auto-detected if None)
            
        Returns:
            Deserialized persona context
        """
        # Deserialize data
        deserialized_data = await self._deserialize_data(data, format)
        
        # Extract metadata
        metadata = deserialized_data.pop("_serialization_metadata", {})
        
        # Validate type
        if metadata.get("type") != "persona_context":
            raise ValueError("Invalid data type for persona context deserialization")
        
        # Convert datetime strings back to datetime objects
        deserialized_data["created_at"] = datetime.fromisoformat(deserialized_data["created_at"])
        deserialized_data["last_accessed"] = datetime.fromisoformat(deserialized_data["last_accessed"])
        
        # Convert enums back
        deserialized_data["persona_type"] = PersonaType(deserialized_data["persona_type"])
        deserialized_data["state"] = ContextState(deserialized_data["state"])
        
        return PersonaContext(**deserialized_data)
    
    async def serialize_session_state(self, 
                                    session_state: SessionState,
                                    format: Optional[SerializationFormat] = None) -> bytes:
        """
        Serialize a session state.
        
        Args:
            session_state: Session state to serialize
            format: Serialization format (uses default if None)
            
        Returns:
            Serialized data as bytes
        """
        format = format or self.default_format
        
        # Convert to dictionary
        data = asdict(session_state)
        
        # Serialize persona contexts within the session
        serialized_personas = {}
        for persona_id, persona_context in data["personas"].items():
            persona_bytes = await self.serialize_persona_context(persona_context, format)
            serialized_personas[persona_id] = base64.b64encode(persona_bytes).decode('utf-8')
        
        data["personas"] = serialized_personas
        
        # Add serialization metadata
        data["_serialization_metadata"] = {
            "version": self.serialization_version.value,
            "format": format.value,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "session_state"
        }
        
        return await self._serialize_data(data, format)
    
    async def deserialize_session_state(self, 
                                      data: bytes,
                                      format: Optional[SerializationFormat] = None) -> SessionState:
        """
        Deserialize a session state.
        
        Args:
            data: Serialized data
            format: Serialization format (auto-detected if None)
            
        Returns:
            Deserialized session state
        """
        # Deserialize data
        deserialized_data = await self._deserialize_data(data, format)
        
        # Extract metadata
        metadata = deserialized_data.pop("_serialization_metadata", {})
        
        # Validate type
        if metadata.get("type") != "session_state":
            raise ValueError("Invalid data type for session state deserialization")
        
        # Deserialize persona contexts
        personas = {}
        for persona_id, persona_data_b64 in deserialized_data["personas"].items():
            persona_data = base64.b64decode(persona_data_b64.encode('utf-8'))
            personas[persona_id] = await self.deserialize_persona_context(persona_data, format)
        
        deserialized_data["personas"] = personas
        
        # Convert datetime strings back to datetime objects
        deserialized_data["created_at"] = datetime.fromisoformat(deserialized_data["created_at"])
        deserialized_data["last_activity"] = datetime.fromisoformat(deserialized_data["last_activity"])
        
        return SessionState(**deserialized_data)
    
    async def serialize_task_state(self, 
                                 task_state: TaskState,
                                 format: Optional[SerializationFormat] = None) -> bytes:
        """
        Serialize a task state.
        
        Args:
            task_state: Task state to serialize
            format: Serialization format (uses default if None)
            
        Returns:
            Serialized data as bytes
        """
        format = format or self.default_format
        
        # Convert to dictionary
        data = asdict(task_state)
        
        # Add serialization metadata
        data["_serialization_metadata"] = {
            "version": self.serialization_version.value,
            "format": format.value,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "task_state"
        }
        
        return await self._serialize_data(data, format)
    
    async def deserialize_task_state(self, 
                                   data: bytes,
                                   format: Optional[SerializationFormat] = None) -> TaskState:
        """
        Deserialize a task state.
        
        Args:
            data: Serialized data
            format: Serialization format (auto-detected if None)
            
        Returns:
            Deserialized task state
        """
        # Deserialize data
        deserialized_data = await self._deserialize_data(data, format)
        
        # Extract metadata
        metadata = deserialized_data.pop("_serialization_metadata", {})
        
        # Validate type
        if metadata.get("type") != "task_state":
            raise ValueError("Invalid data type for task state deserialization")
        
        return TaskState(**deserialized_data)
    
    async def serialize_checkpoint(self, 
                                 checkpoint: Checkpoint,
                                 format: Optional[SerializationFormat] = None) -> bytes:
        """
        Serialize a checkpoint.
        
        Args:
            checkpoint: Checkpoint to serialize
            format: Serialization format (uses default if None)
            
        Returns:
            Serialized data as bytes
        """
        format = format or self.default_format
        
        # Convert to dictionary
        data = asdict(checkpoint)
        
        # Serialize task states within the checkpoint
        serialized_task_states = {}
        for task_id, task_state in data["task_states"].items():
            task_bytes = await self.serialize_task_state(task_state, format)
            serialized_task_states[task_id] = base64.b64encode(task_bytes).decode('utf-8')
        
        data["task_states"] = serialized_task_states
        
        # Convert datetime to string
        data["timestamp"] = data["timestamp"].isoformat()
        
        # Convert enums to strings
        data["checkpoint_type"] = data["checkpoint_type"].value
        data["scope"] = data["scope"].value
        
        # Add serialization metadata
        data["_serialization_metadata"] = {
            "version": self.serialization_version.value,
            "format": format.value,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "checkpoint"
        }
        
        return await self._serialize_data(data, format)
    
    async def deserialize_checkpoint(self, 
                                   data: bytes,
                                   format: Optional[SerializationFormat] = None) -> Checkpoint:
        """
        Deserialize a checkpoint.
        
        Args:
            data: Serialized data
            format: Serialization format (auto-detected if None)
            
        Returns:
            Deserialized checkpoint
        """
        # Deserialize data
        deserialized_data = await self._deserialize_data(data, format)
        
        # Extract metadata
        metadata = deserialized_data.pop("_serialization_metadata", {})
        
        # Validate type
        if metadata.get("type") != "checkpoint":
            raise ValueError("Invalid data type for checkpoint deserialization")
        
        # Deserialize task states
        task_states = {}
        for task_id, task_data_b64 in deserialized_data["task_states"].items():
            task_data = base64.b64decode(task_data_b64.encode('utf-8'))
            task_states[task_id] = await self.deserialize_task_state(task_data, format)
        
        deserialized_data["task_states"] = task_states
        
        # Convert string back to datetime
        deserialized_data["timestamp"] = datetime.fromisoformat(deserialized_data["timestamp"])
        
        # Convert strings back to enums
        deserialized_data["checkpoint_type"] = CheckpointType(deserialized_data["checkpoint_type"])
        deserialized_data["scope"] = CheckpointScope(deserialized_data["scope"])
        
        return Checkpoint(**deserialized_data)
    
    async def serialize_to_file(self, 
                              data: Any,
                              file_path: Union[str, Path],
                              format: Optional[SerializationFormat] = None) -> SerializationMetadata:
        """
        Serialize data to a file.
        
        Args:
            data: Data to serialize (PersonaContext, SessionState, TaskState, or Checkpoint)
            file_path: Path to output file
            format: Serialization format (uses default if None)
            
        Returns:
            Serialization metadata
        """
        file_path = Path(file_path)
        
        # Serialize data based on type
        if isinstance(data, PersonaContext):
            serialized_data = await self.serialize_persona_context(data, format)
        elif isinstance(data, SessionState):
            serialized_data = await self.serialize_session_state(data, format)
        elif isinstance(data, TaskState):
            serialized_data = await self.serialize_task_state(data, format)
        elif isinstance(data, Checkpoint):
            serialized_data = await self.serialize_checkpoint(data, format)
        else:
            raise ValueError(f"Unsupported data type for serialization: {type(data)}")
        
        # Write to file
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'wb') as f:
            f.write(serialized_data)
        
        # Calculate metadata
        metadata = SerializationMetadata(
            version=self.serialization_version.value,
            format=format.value if format else self.default_format.value,
            timestamp=datetime.utcnow().isoformat(),
            checksum=self._calculate_checksum(serialized_data),
            size=len(serialized_data),
            compression_ratio=self._calculate_compression_ratio(data, serialized_data)
        )
        
        # Write metadata file
        metadata_file = file_path.with_suffix(file_path.suffix + '.meta')
        with open(metadata_file, 'w') as f:
            json.dump(asdict(metadata), f, indent=2)
        
        return metadata
    
    async def deserialize_from_file(self, 
                                  file_path: Union[str, Path],
                                  expected_type: str,
                                  format: Optional[SerializationFormat] = None) -> Any:
        """
        Deserialize data from a file.
        
        Args:
            file_path: Path to input file
            expected_type: Expected data type ("persona_context", "session_state", "task_state", "checkpoint")
            format: Serialization format (auto-detected if None)
            
        Returns:
            Deserialized data
        """
        file_path = Path(file_path)
        
        # Read file
        with open(file_path, 'rb') as f:
            data = f.read()
        
        # Deserialize based on type
        if expected_type == "persona_context":
            return await self.deserialize_persona_context(data, format)
        elif expected_type == "session_state":
            return await self.deserialize_session_state(data, format)
        elif expected_type == "task_state":
            return await self.deserialize_task_state(data, format)
        elif expected_type == "checkpoint":
            return await self.deserialize_checkpoint(data, format)
        else:
            raise ValueError(f"Unsupported expected type: {expected_type}")
    
    async def get_serialization_metadata(self, file_path: Union[str, Path]) -> Optional[SerializationMetadata]:
        """
        Get serialization metadata from a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Serialization metadata or None if not found
        """
        metadata_file = Path(file_path).with_suffix(Path(file_path).suffix + '.meta')
        
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r') as f:
                metadata_data = json.load(f)
            
            return SerializationMetadata(**metadata_data)
        except Exception as e:
            logger.error(f"Failed to read metadata file {metadata_file}: {e}")
            return None
    
    async def _serialize_data(self, data: Dict[str, Any], format: SerializationFormat) -> bytes:
        """Internal method to serialize data in the specified format."""
        if format == SerializationFormat.JSON:
            json_data = json.dumps(data, default=str, indent=2)
            serialized = json_data.encode('utf-8')
            
            if self.enable_compression:
                serialized = zlib.compress(serialized, self.compression_level)
                # Add compression header
                serialized = b'COMPRESSED:' + serialized
            
            return serialized
        
        elif format == SerializationFormat.PICKLE:
            serialized = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
            
            if self.enable_compression:
                serialized = zlib.compress(serialized, self.compression_level)
                # Add compression header
                serialized = b'COMPRESSED:' + serialized
            
            return serialized
        
        elif format == SerializationFormat.COMPRESSED_PICKLE:
            serialized = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
            serialized = zlib.compress(serialized, self.compression_level)
            return serialized
        
        elif format == SerializationFormat.BINARY:
            # Custom binary format for maximum efficiency
            return await self._serialize_binary(data)
        
        else:
            raise ValueError(f"Unsupported serialization format: {format}")
    
    async def _deserialize_data(self, data: bytes, format: Optional[SerializationFormat]) -> Dict[str, Any]:
        """Internal method to deserialize data from the specified format."""
        # Auto-detect format if not specified
        if format is None:
            format = self._detect_format(data)
        
        # Handle compression
        if data.startswith(b'COMPRESSED:'):
            data = data[11:]  # Remove compression header
            data = zlib.decompress(data)
        
        if format == SerializationFormat.JSON:
            return json.loads(data.decode('utf-8'))
        
        elif format == SerializationFormat.PICKLE:
            return pickle.loads(data)
        
        elif format == SerializationFormat.COMPRESSED_PICKLE:
            decompressed = zlib.decompress(data)
            return pickle.loads(decompressed)
        
        elif format == SerializationFormat.BINARY:
            return await self._deserialize_binary(data)
        
        else:
            raise ValueError(f"Unsupported deserialization format: {format}")
    
    async def _serialize_binary(self, data: Dict[str, Any]) -> bytes:
        """Serialize data in custom binary format."""
        # This is a simplified binary format
        # In a real implementation, this would be more sophisticated
        binary_data = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
        compressed = zlib.compress(binary_data, self.compression_level)
        
        # Add version header
        version_bytes = self.serialization_version.value.encode('utf-8')
        return len(version_bytes).to_bytes(4, 'big') + version_bytes + compressed
    
    async def _deserialize_binary(self, data: bytes) -> Dict[str, Any]:
        """Deserialize data from custom binary format."""
        # Read version header
        version_length = int.from_bytes(data[:4], 'big')
        version = data[4:4+version_length].decode('utf-8')
        
        # Decompress and deserialize
        compressed_data = data[4+version_length:]
        decompressed = zlib.decompress(compressed_data)
        return pickle.loads(decompressed)
    
    def _detect_format(self, data: bytes) -> SerializationFormat:
        """Auto-detect serialization format from data."""
        # Check for compression header
        if data.startswith(b'COMPRESSED:'):
            data = data[11:]
        
        # Try to parse as JSON
        try:
            json.loads(data.decode('utf-8'))
            return SerializationFormat.JSON
        except:
            pass
        
        # Check for binary format header
        if len(data) > 4:
            version_length = int.from_bytes(data[:4], 'big')
            if version_length > 0 and version_length < 10:  # Reasonable version string length
                return SerializationFormat.BINARY
        
        # Default to pickle
        return SerializationFormat.PICKLE
    
    def _calculate_checksum(self, data: bytes) -> str:
        """Calculate SHA256 checksum of data."""
        return hashlib.sha256(data).hexdigest()
    
    def _calculate_compression_ratio(self, original_data: Any, compressed_data: bytes) -> Optional[float]:
        """Calculate compression ratio."""
        try:
            original_size = len(pickle.dumps(original_data, protocol=pickle.HIGHEST_PROTOCOL))
            compressed_size = len(compressed_data)
            return compressed_size / original_size if original_size > 0 else None
        except:
            return None


class BMADContextStorage:
    """
    Storage backend for BMAD contexts using the serialization system.
    
    This class provides persistent storage for persona contexts,
    session states, and task checkpoints using the serialization system.
    """
    
    def __init__(self, 
                 storage_path: Union[str, Path],
                 serializer: Optional[BMADContextSerializer] = None):
        """
        Initialize the context storage.
        
        Args:
            storage_path: Base path for storage
            serializer: Context serializer instance
        """
        self.storage_path = Path(storage_path)
        self.serializer = serializer or BMADContextSerializer()
        
        # Create storage directories
        self.persona_path = self.storage_path / "personas"
        self.session_path = self.storage_path / "sessions"
        self.task_path = self.storage_path / "tasks"
        self.checkpoint_path = self.storage_path / "checkpoints"
        
        for path in [self.persona_path, self.session_path, self.task_path, self.checkpoint_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    async def store_persona_context(self, persona_context: PersonaContext) -> str:
        """Store a persona context."""
        file_path = self.persona_path / f"{persona_context.persona_id}.pctx"
        metadata = await self.serializer.serialize_to_file(persona_context, file_path)
        return str(file_path)
    
    async def load_persona_context(self, persona_id: str) -> Optional[PersonaContext]:
        """Load a persona context."""
        file_path = self.persona_path / f"{persona_id}.pctx"
        
        if not file_path.exists():
            return None
        
        try:
            return await self.serializer.deserialize_from_file(file_path, "persona_context")
        except Exception as e:
            logger.error(f"Failed to load persona context {persona_id}: {e}")
            return None
    
    async def store_session_state(self, session_state: SessionState) -> str:
        """Store a session state."""
        file_path = self.session_path / f"{session_state.session_id}.sess"
        metadata = await self.serializer.serialize_to_file(session_state, file_path)
        return str(file_path)
    
    async def load_session_state(self, session_id: str) -> Optional[SessionState]:
        """Load a session state."""
        file_path = self.session_path / f"{session_id}.sess"
        
        if not file_path.exists():
            return None
        
        try:
            return await self.serializer.deserialize_from_file(file_path, "session_state")
        except Exception as e:
            logger.error(f"Failed to load session state {session_id}: {e}")
            return None
    
    async def store_task_state(self, task_state: TaskState) -> str:
        """Store a task state."""
        file_path = self.task_path / f"{task_state.task_id}.task"
        metadata = await self.serializer.serialize_to_file(task_state, file_path)
        return str(file_path)
    
    async def load_task_state(self, task_id: str) -> Optional[TaskState]:
        """Load a task state."""
        file_path = self.task_path / f"{task_id}.task"
        
        if not file_path.exists():
            return None
        
        try:
            return await self.serializer.deserialize_from_file(file_path, "task_state")
        except Exception as e:
            logger.error(f"Failed to load task state {task_id}: {e}")
            return None
    
    async def store_checkpoint(self, checkpoint: Checkpoint) -> str:
        """Store a checkpoint."""
        file_path = self.checkpoint_path / f"{checkpoint.checkpoint_id}.chk"
        metadata = await self.serializer.serialize_to_file(checkpoint, file_path)
        return str(file_path)
    
    async def load_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Load a checkpoint."""
        file_path = self.checkpoint_path / f"{checkpoint_id}.chk"
        
        if not file_path.exists():
            return None
        
        try:
            return await self.serializer.deserialize_from_file(file_path, "checkpoint")
        except Exception as e:
            logger.error(f"Failed to load checkpoint {checkpoint_id}: {e}")
            return None
    
    async def list_stored_items(self, item_type: str) -> List[str]:
        """List stored items of a specific type."""
        if item_type == "persona_context":
            path = self.persona_path
            suffix = ".pctx"
        elif item_type == "session_state":
            path = self.session_path
            suffix = ".sess"
        elif item_type == "task_state":
            path = self.task_path
            suffix = ".task"
        elif item_type == "checkpoint":
            path = self.checkpoint_path
            suffix = ".chk"
        else:
            raise ValueError(f"Unsupported item type: {item_type}")
        
        items = []
        for file_path in path.glob(f"*{suffix}"):
            items.append(file_path.stem)
        
        return items
    
    async def cleanup_old_items(self, item_type: str, max_age_hours: int = 24):
        """Clean up old stored items."""
        items = await self.list_stored_items(item_type)
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        cleaned_count = 0
        for item_id in items:
            if item_type == "persona_context":
                file_path = self.persona_path / f"{item_id}.pctx"
            elif item_type == "session_state":
                file_path = self.session_path / f"{item_id}.sess"
            elif item_type == "task_state":
                file_path = self.task_path / f"{item_id}.task"
            elif item_type == "checkpoint":
                file_path = self.checkpoint_path / f"{item_id}.chk"
            
            try:
                metadata = await self.serializer.get_serialization_metadata(file_path)
                if metadata and datetime.fromisoformat(metadata.timestamp) < cutoff_time:
                    file_path.unlink()
                    metadata_file = file_path.with_suffix(file_path.suffix + '.meta')
                    if metadata_file.exists():
                        metadata_file.unlink()
                    cleaned_count += 1
            except Exception as e:
                logger.error(f"Failed to clean up {item_type} {item_id}: {e}")
        
        logger.info(f"Cleaned up {cleaned_count} old {item_type} items")
        return cleaned_count
