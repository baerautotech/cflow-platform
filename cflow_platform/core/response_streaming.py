"""
Response Streaming System for WebMCP Performance Enhancement

This module provides streaming responses for long-running tool operations,
enabling real-time feedback and better user experience.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional, AsyncGenerator, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class StreamEventType(Enum):
    """Types of streaming events"""
    START = "start"
    PROGRESS = "progress"
    DATA = "data"
    ERROR = "error"
    COMPLETE = "complete"
    HEARTBEAT = "heartbeat"


@dataclass
class StreamEvent:
    """Represents a streaming event"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: StreamEventType = StreamEventType.DATA
    timestamp: float = field(default_factory=time.time)
    data: Dict[str, Any] = field(default_factory=dict)
    progress: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class StreamResponse:
    """
    Handles streaming responses for long-running operations.
    
    Features:
    - Real-time progress updates
    - Error handling and recovery
    - Heartbeat mechanism
    - Event buffering and replay
    - Client subscription management
    """
    
    def __init__(
        self,
        stream_id: str,
        timeout_seconds: float = 300.0,
        heartbeat_interval: float = 10.0,
        buffer_size: int = 100
    ):
        self.stream_id = stream_id
        self.timeout_seconds = timeout_seconds
        self.heartbeat_interval = heartbeat_interval
        self.buffer_size = buffer_size
        
        # Event management
        self._events: list[StreamEvent] = []
        self._subscribers: set[asyncio.Queue] = set()
        self._is_complete = False
        self._is_error = False
        self._start_time = time.time()
        
        # Background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._timeout_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the stream and background tasks"""
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._timeout_task = asyncio.create_task(self._timeout_monitor())
        
        # Send start event
        await self.emit_event(StreamEventType.START, {
            "stream_id": self.stream_id,
            "started_at": self._start_time
        })
        
        logger.info(f"Stream {self.stream_id} started")
    
    async def stop(self):
        """Stop the stream and cleanup resources"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._timeout_task:
            self._timeout_task.cancel()
        
        # Send complete event if not already complete
        if not self._is_complete and not self._is_error:
            await self.emit_event(StreamEventType.COMPLETE, {
                "stream_id": self.stream_id,
                "completed_at": time.time(),
                "duration": time.time() - self._start_time
            })
        
        self._is_complete = True
        logger.info(f"Stream {self.stream_id} stopped")
    
    async def emit_event(
        self,
        event_type: StreamEventType,
        data: Dict[str, Any],
        progress: Optional[float] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Emit an event to all subscribers"""
        event = StreamEvent(
            event_type=event_type,
            data=data,
            progress=progress,
            error=error,
            metadata=metadata or {}
        )
        
        # Add to buffer
        self._events.append(event)
        if len(self._events) > self.buffer_size:
            self._events.pop(0)
        
        # Broadcast to subscribers
        if self._subscribers:
            event_json = {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "timestamp": event.timestamp,
                "data": event.data,
                "progress": event.progress,
                "error": event.error,
                "metadata": event.metadata
            }
            
            # Send to all subscribers (non-blocking)
            dead_subscribers = set()
            for queue in self._subscribers:
                try:
                    queue.put_nowait(event_json)
                except asyncio.QueueFull:
                    # Remove full queues (client disconnected)
                    dead_subscribers.add(queue)
                except Exception as e:
                    logger.error(f"Error sending event to subscriber: {e}")
                    dead_subscribers.add(queue)
            
            # Clean up dead subscribers
            self._subscribers -= dead_subscribers
        
        # Handle completion/error states
        if event_type == StreamEventType.COMPLETE:
            self._is_complete = True
        elif event_type == StreamEventType.ERROR:
            self._is_error = True
    
    async def emit_progress(self, progress: float, message: str = ""):
        """Emit a progress update"""
        await self.emit_event(
            StreamEventType.PROGRESS,
            {"message": message, "progress": progress},
            progress=progress
        )
    
    async def emit_data(self, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """Emit data event"""
        await self.emit_event(StreamEventType.DATA, data, metadata=metadata)
    
    async def emit_error(self, error: str, details: Optional[Dict[str, Any]] = None):
        """Emit an error event"""
        await self.emit_event(
            StreamEventType.ERROR,
            {"error": error, "details": details or {}},
            error=error
        )
        self._is_error = True
    
    def subscribe(self) -> asyncio.Queue:
        """Subscribe to stream events"""
        queue = asyncio.Queue(maxsize=50)  # Buffer for disconnected clients
        self._subscribers.add(queue)
        
        # Send buffered events to new subscriber
        for event in self._events:
            try:
                queue.put_nowait({
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "timestamp": event.timestamp,
                    "data": event.data,
                    "progress": event.progress,
                    "error": event.error,
                    "metadata": event.metadata
                })
            except asyncio.QueueFull:
                break
        
        logger.debug(f"New subscriber added to stream {self.stream_id}")
        return queue
    
    def unsubscribe(self, queue: asyncio.Queue):
        """Unsubscribe from stream events"""
        self._subscribers.discard(queue)
        logger.debug(f"Subscriber removed from stream {self.stream_id}")
    
    async def _heartbeat_loop(self):
        """Background task to send heartbeat events"""
        while not self._is_complete and not self._is_error:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                if not self._is_complete and not self._is_error:
                    await self.emit_event(StreamEventType.HEARTBEAT, {
                        "stream_id": self.stream_id,
                        "uptime": time.time() - self._start_time,
                        "subscribers": len(self._subscribers)
                    })
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error for stream {self.stream_id}: {e}")
    
    async def _timeout_monitor(self):
        """Background task to monitor for timeouts"""
        try:
            await asyncio.sleep(self.timeout_seconds)
            
            if not self._is_complete and not self._is_error:
                await self.emit_error(
                    f"Stream timeout after {self.timeout_seconds} seconds",
                    {"timeout_seconds": self.timeout_seconds}
                )
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Timeout monitor error for stream {self.stream_id}: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current stream status"""
        return {
            "stream_id": self.stream_id,
            "is_complete": self._is_complete,
            "is_error": self._is_error,
            "subscribers": len(self._subscribers),
            "events_count": len(self._events),
            "uptime": time.time() - self._start_time,
            "last_event": self._events[-1].timestamp if self._events else None
        }


class StreamManager:
    """
    Manages multiple streaming responses.
    
    Features:
    - Stream lifecycle management
    - Automatic cleanup of completed streams
    - Stream discovery and monitoring
    """
    
    def __init__(self, max_streams: int = 100, cleanup_interval: float = 300.0):
        self.max_streams = max_streams
        self.cleanup_interval = cleanup_interval
        self._streams: Dict[str, StreamResponse] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the stream manager"""
        self._cleanup_task = asyncio.create_task(self._cleanup_completed_streams())
        logger.info("StreamManager started")
    
    async def stop(self):
        """Stop the stream manager and cleanup all streams"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        # Stop all active streams
        for stream in self._streams.values():
            await stream.stop()
        
        self._streams.clear()
        logger.info("StreamManager stopped")
    
    async def create_stream(
        self,
        stream_id: Optional[str] = None,
        timeout_seconds: float = 300.0,
        heartbeat_interval: float = 10.0
    ) -> StreamResponse:
        """Create a new streaming response"""
        if stream_id is None:
            stream_id = str(uuid.uuid4())
        
        # Check stream limit
        if len(self._streams) >= self.max_streams:
            # Remove oldest completed stream
            await self._cleanup_oldest_stream()
        
        stream = StreamResponse(
            stream_id=stream_id,
            timeout_seconds=timeout_seconds,
            heartbeat_interval=heartbeat_interval
        )
        
        self._streams[stream_id] = stream
        await stream.start()
        
        logger.info(f"Created stream {stream_id}")
        return stream
    
    def get_stream(self, stream_id: str) -> Optional[StreamResponse]:
        """Get an existing stream by ID"""
        return self._streams.get(stream_id)
    
    def list_streams(self) -> List[Dict[str, Any]]:
        """List all active streams with their status"""
        return [
            {
                "stream_id": stream_id,
                **stream.get_status()
            }
            for stream_id, stream in self._streams.items()
        ]
    
    async def _cleanup_completed_streams(self):
        """Background task to cleanup completed streams"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                completed_streams = [
                    stream_id for stream_id, stream in self._streams.items()
                    if stream._is_complete or stream._is_error
                ]
                
                for stream_id in completed_streams:
                    stream = self._streams.pop(stream_id, None)
                    if stream:
                        await stream.stop()
                        logger.debug(f"Cleaned up completed stream {stream_id}")
                
                if completed_streams:
                    logger.info(f"Cleaned up {len(completed_streams)} completed streams")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Stream cleanup error: {e}")
    
    async def _cleanup_oldest_stream(self):
        """Remove the oldest completed stream to make room"""
        oldest_stream_id = None
        oldest_time = float('inf')
        
        for stream_id, stream in self._streams.items():
            if stream._is_complete or stream._is_error:
                if stream._start_time < oldest_time:
                    oldest_time = stream._start_time
                    oldest_stream_id = stream_id
        
        if oldest_stream_id:
            stream = self._streams.pop(oldest_stream_id)
            await stream.stop()
            logger.info(f"Removed oldest stream {oldest_stream_id} to make room")


# Global stream manager
_stream_manager: Optional[StreamManager] = None


async def get_stream_manager() -> StreamManager:
    """Get the global stream manager"""
    global _stream_manager
    if _stream_manager is None:
        _stream_manager = StreamManager()
        await _stream_manager.start()
    return _stream_manager


async def create_stream(
    stream_id: Optional[str] = None,
    timeout_seconds: float = 300.0,
    heartbeat_interval: float = 10.0
) -> StreamResponse:
    """Create a new streaming response"""
    manager = await get_stream_manager()
    return await manager.create_stream(stream_id, timeout_seconds, heartbeat_interval)


async def get_stream(stream_id: str) -> Optional[StreamResponse]:
    """Get an existing stream by ID"""
    manager = await get_stream_manager()
    return manager.get_stream(stream_id)


async def list_streams() -> List[Dict[str, Any]]:
    """List all active streams"""
    manager = await get_stream_manager()
    return manager.list_streams()


async def stream_tool_execution(
    tool_name: str,
    kwargs: Dict[str, Any],
    stream_id: Optional[str] = None,
    timeout_seconds: float = 300.0
) -> StreamResponse:
    """
    Execute a tool with streaming response.
    
    This is a higher-level function that combines tool execution with streaming.
    """
    from .async_tool_executor import execute_tool_async, ToolPriority
    
    # Create stream
    stream = await create_stream(stream_id, timeout_seconds)
    
    # Execute tool in background
    async def _execute():
        try:
            # Emit progress updates
            await stream.emit_progress(10, f"Starting {tool_name} execution...")
            
            # Execute tool
            result = await execute_tool_async(
                tool_name=tool_name,
                kwargs=kwargs,
                priority=ToolPriority.HIGH,
                timeout_seconds=timeout_seconds - 10  # Leave buffer for streaming
            )
            
            await stream.emit_progress(90, "Tool execution completed, processing results...")
            
            # Stream the result
            await stream.emit_data({
                "tool_name": tool_name,
                "result": result.result,
                "execution_time": result.execution_time,
                "success": result.success
            })
            
            await stream.emit_progress(100, "Execution completed successfully")
            
        except Exception as e:
            await stream.emit_error(f"Tool execution failed: {str(e)}")
        finally:
            await stream.stop()
    
    # Start execution in background
    asyncio.create_task(_execute())
    
    return stream
