"""
BMAD Redis Cluster Messaging

Production-ready Redis cluster integration for multi-agent messaging.
"""

import asyncio
import json
import uuid
import time
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Awaitable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv
import redis
import redis.asyncio as aioredis

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")


class MessageType(Enum):
    """Agent message types."""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    STATUS_UPDATE = "status_update"
    DATA_SHARE = "data_share"
    COORDINATION = "coordination"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    AGENT_DISCOVERY = "agent_discovery"
    STATE_SYNC = "state_sync"


class MessagePriority(Enum):
    """Message priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class RedisMessage:
    """Redis-based agent message."""
    id: str = ""
    sender_id: str = ""
    receiver_id: str = ""
    message_type: MessageType = MessageType.TASK_REQUEST
    priority: MessagePriority = MessagePriority.NORMAL
    content: Dict[str, Any] = None
    timestamp: datetime = None
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    expires_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    delivered: bool = False
    acknowledged: bool = False

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.utcnow()
        if not self.content:
            self.content = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for Redis storage."""
        data = asdict(self)
        data['message_type'] = self.message_type.value
        data['priority'] = self.priority.value
        data['timestamp'] = self.timestamp.isoformat()
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RedisMessage':
        """Create message from Redis data."""
        data['message_type'] = MessageType(data['message_type'])
        data['priority'] = MessagePriority(data['priority'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if data.get('expires_at'):
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        return cls(**data)


class BMADRedisClusterMessaging:
    """Production-ready Redis cluster messaging for BMAD."""
    
    def __init__(self):
        self.redis_client = None
        self.redis_cluster = None
        self.message_handlers: Dict[MessageType, List[Callable]] = {}
        self.agent_channels: Dict[str, str] = {}  # agent_id -> channel_name
        self.running = False
        self.message_ttl = 3600  # 1 hour default TTL
        self.heartbeat_interval = 30  # 30 seconds
        self._ensure_redis()
    
    def _ensure_redis(self) -> None:
        """Create Redis cluster client for cerebral infrastructure."""
        try:
            # Production: Connect to cerebral Redis cluster
            # External access: redis.cerebral.baerautotech.com:6380 (TLS)
            # Internal cluster access: redis.cerebral-messaging.svc.cluster.local:6379
            redis_host = os.getenv("REDIS_HOST", "redis.cerebral-messaging.svc.cluster.local")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_username = "default"  # Development token username
            redis_password = "Lo1dy8mg9gBm6GwKXbu5JXSMqFtMZCJAMawuq4TBsjs="  # Development token password
            
            print(f"[INFO] Redis Cluster: Attempting connection to cerebral Redis at {redis_host}:{redis_port}")
            
            # Connect to cerebral Redis cluster with proper authentication
            # Use TLS only for external access (redis.cerebral.baerautotech.com)
            use_ssl = redis_host.endswith("baerautotech.com")
            
            redis_config = {
                "host": redis_host,
                "port": redis_port,
                "decode_responses": True,
                "socket_timeout": 10,
                "socket_connect_timeout": 10
            }
            
            # Add authentication for external access
            if use_ssl:
                redis_config.update({
                    "username": redis_username,
                    "password": redis_password,
                    "ssl": True,
                    "ssl_cert_reqs": 'required',
                    "ssl_check_hostname": True
                })
            
            self.redis_client = redis.Redis(**redis_config)
            
            # Test connection
            self.redis_client.ping()
            print(f"[INFO] Redis Cluster: Connected to cerebral Redis at {redis_host}:{redis_port}")
            
        except redis.ConnectionError as e:
            print(f"[INFO] Redis Cluster: CONNECTION FAILED - {e}")
            print(" SERVICE UNAVAILABLE: Cerebral Redis cluster is not accessible")
            print("   Possible causes:")
            print("   - DNS not propagated yet")
            print("   - Network connectivity issues")
            print("   - Redis service down")
            print("   - Authentication token invalid")
            self.redis_client = None
            self.redis_cluster = None
            raise RuntimeError("Cerebral Redis cluster is unavailable")
            
        except Exception as e:
            print(f"[INFO] Redis Cluster: SETUP FAILED - {e}")
            print(" SERVICE UNAVAILABLE: Cannot initialize Redis connection")
            self.redis_client = None
            self.redis_cluster = None
            raise RuntimeError("Redis cluster initialization failed")
    
    def _get_redis_client(self):
        """Get Redis client (cluster or single instance)."""
        if not self.redis_client and not self.redis_cluster:
            raise RuntimeError("Redis cluster is unavailable - service not accessible")
        return self.redis_cluster or self.redis_client
    
    async def register_agent(self, agent_id: str, agent_type: str) -> bool:
        """Register agent in Redis cluster."""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                print(f"[INFO][INFO] Redis Cluster: Mock registration of agent {agent_id}")
                return True
            
            # Register agent in Redis
            agent_data = {
                "agent_id": agent_id,
                "agent_type": agent_type,
                "status": "online",
                "last_heartbeat": datetime.utcnow().isoformat(),
                "capabilities": []
            }
            
            # Store agent info (convert to strings for Redis)
            agent_data_str = {k: str(v) for k, v in agent_data.items()}
            redis_client.hset(f"agent:{agent_id}", mapping=agent_data_str)
            redis_client.expire(f"agent:{agent_id}", self.message_ttl)
            
            # Add to agent set
            redis_client.sadd("agents:online", agent_id)
            redis_client.sadd(f"agents:type:{agent_type}", agent_id)
            
            # Create agent message channel
            channel_name = f"agent:{agent_id}:messages"
            self.agent_channels[agent_id] = channel_name
            
            print(f"[INFO] Redis Cluster: Registered agent {agent_id} ({agent_type})")
            return True
            
        except Exception as e:
            print(f"[INFO] Redis Cluster: Failed to register agent: {e}")
            return False
    
    async def send_message(self, sender_id: str, receiver_id: str, message_type: MessageType,
                          content: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL,
                          correlation_id: Optional[str] = None, reply_to: Optional[str] = None,
                          expires_at: Optional[datetime] = None) -> str:
        """Send message via Redis cluster."""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                print(f"[INFO][INFO] Redis Cluster: Mock message from {sender_id} to {receiver_id}")
                return str(uuid.uuid4())
            
            # Create message
            message = RedisMessage(
                id=str(uuid.uuid4()),
                sender_id=sender_id,
                receiver_id=receiver_id,
                message_type=message_type,
                priority=priority,
                content=content,
                correlation_id=correlation_id,
                reply_to=reply_to,
                expires_at=expires_at
            )
            
            # Store message in Redis (as JSON string)
            message_key = f"message:{message.id}"
            message_json = json.dumps(message.to_dict())
            redis_client.set(message_key, message_json)
            
            # Set TTL
            ttl = self.message_ttl
            if expires_at:
                ttl = int((expires_at - datetime.utcnow()).total_seconds())
            redis_client.expire(message_key, max(ttl, 60))  # Minimum 1 minute
            
            # Add to receiver's message queue
            receiver_queue = f"queue:{receiver_id}"
            redis_client.lpush(receiver_queue, message.id)
            redis_client.expire(receiver_queue, self.message_ttl)
            
            # Add to priority queue for critical messages
            if priority == MessagePriority.CRITICAL:
                critical_queue = "queue:critical"
                redis_client.lpush(critical_queue, message.id)
                redis_client.expire(critical_queue, self.message_ttl)
            
            print(f"[INFO] Redis Cluster: Sent {message_type.value} message {message.id} from {sender_id} to {receiver_id}")
            return message.id
            
        except Exception as e:
            print(f"[INFO] Redis Cluster: Failed to send message: {e}")
            return None
    
    async def broadcast_message(self, sender_id: str, agent_type: str, message_type: MessageType,
                              content: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL) -> List[str]:
        """Broadcast message to all agents of a type."""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                print(f"[INFO][INFO] Redis Cluster: Mock broadcast to {agent_type}")
                return [str(uuid.uuid4())]
            
            # Get all agents of the specified type
            agent_ids = redis_client.smembers(f"agents:type:{agent_type}")
            
            message_ids = []
            for agent_id in agent_ids:
                if agent_id != sender_id:  # Don't send to self
                    message_id = await self.send_message(
                        sender_id=sender_id,
                        receiver_id=agent_id,
                        message_type=message_type,
                        content=content,
                        priority=priority
                    )
                    if message_id:
                        message_ids.append(message_id)
            
            print(f"[INFO] Redis Cluster: Broadcasted {message_type.value} message to {len(message_ids)} {agent_type} agents")
            return message_ids
            
        except Exception as e:
            print(f"[INFO] Redis Cluster: Failed to broadcast message: {e}")
            return []
    
    async def get_messages_for_agent(self, agent_id: str, message_type: Optional[MessageType] = None) -> List[RedisMessage]:
        """Get messages for a specific agent."""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                print(f"[INFO][INFO] Redis Cluster: Mock messages for agent {agent_id}")
                return []
            
            # Get message IDs from agent's queue
            receiver_queue = f"queue:{agent_id}"
            message_ids = redis_client.lrange(receiver_queue, 0, -1)
            
            messages = []
            for message_id in message_ids:
                try:
                    message_key = f"message:{message_id}"
                    message_json = redis_client.get(message_key)
                    
                    if message_json:
                        message_data = json.loads(message_json)
                        message = RedisMessage.from_dict(message_data)
                        
                        # Check if message has expired
                        if message.expires_at and message.expires_at < datetime.utcnow():
                            redis_client.delete(message_key)
                            redis_client.lrem(receiver_queue, 1, message_id)
                            continue
                        
                        # Filter by message type if specified
                        if message_type is None or message.message_type == message_type:
                            messages.append(message)
                            
                except Exception as e:
                    print(f"[INFO][INFO] Redis Cluster: Failed to load message {message_id}: {e}")
                    continue
            
            # Sort by priority and timestamp
            messages.sort(key=lambda m: (m.priority.value, m.timestamp), reverse=True)
            
            return messages
            
        except Exception as e:
            print(f"[INFO] Redis Cluster: Failed to get messages: {e}")
            return []
    
    async def acknowledge_message(self, message_id: str, agent_id: str) -> bool:
        """Acknowledge receipt of a message."""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                print(f"[INFO][INFO] Redis Cluster: Mock acknowledgment of message {message_id}")
                return True
            
            message_key = f"message:{message_id}"
            
            # Get message, update acknowledgment, and store back
            message_json = redis_client.get(message_key)
            if message_json:
                message_data = json.loads(message_json)
                message_data["acknowledged"] = True
                message_data["delivered"] = True
                redis_client.set(message_key, json.dumps(message_data))
            
            # Remove from agent's queue
            receiver_queue = f"queue:{agent_id}"
            redis_client.lrem(receiver_queue, 1, message_id)
            
            print(f"[INFO] Redis Cluster: Message {message_id} acknowledged by {agent_id}")
            return True
            
        except Exception as e:
            print(f"[INFO] Redis Cluster: Failed to acknowledge message: {e}")
            return False
    
    async def send_heartbeat(self, agent_id: str, status: str = "online") -> bool:
        """Send agent heartbeat."""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                return True
            
            # Update agent heartbeat
            redis_client.hset(f"agent:{agent_id}", "last_heartbeat", datetime.utcnow().isoformat())
            redis_client.hset(f"agent:{agent_id}", "status", status)
            
            # Send heartbeat message
            await self.broadcast_message(
                sender_id=agent_id,
                agent_type="all",
                message_type=MessageType.HEARTBEAT,
                content={"agent_id": agent_id, "status": status},
                priority=MessagePriority.LOW
            )
            
            return True
            
        except Exception as e:
            print(f"[INFO] Redis Cluster: Failed to send heartbeat: {e}")
            return False
    
    async def discover_agents(self, agent_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Discover agents in the cluster."""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                print("[INFO][INFO] Redis Cluster: Mock agent discovery")
                return []
            
            if agent_type:
                agent_ids = redis_client.smembers(f"agents:type:{agent_type}")
            else:
                agent_ids = redis_client.smembers("agents:online")
            
            agents = []
            for agent_id in agent_ids:
                agent_data = redis_client.hgetall(f"agent:{agent_id}")
                if agent_data:
                    agents.append(agent_data)
            
            return agents
            
        except Exception as e:
            print(f"[INFO] Redis Cluster: Failed to discover agents: {e}")
            return []
    
    async def start_message_processing(self) -> None:
        """Start Redis message processing service."""
        try:
            self.running = True
            print("[INFO] Redis Cluster: Starting message processing service...")
            
            while self.running:
                # Process critical messages first
                await self._process_critical_messages()
                
                # Process normal messages
                await self._process_normal_messages()
                
                # Clean up expired messages
                await self._cleanup_expired_messages()
                
                await asyncio.sleep(0.1)  # Small delay
                
        except Exception as e:
            print(f"[INFO] Redis Cluster: Message processing failed: {e}")
    
    async def _process_critical_messages(self) -> None:
        """Process critical priority messages."""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                return
            
            critical_queue = "queue:critical"
            message_ids = redis_client.lrange(critical_queue, 0, 9)  # Process up to 10 messages
            
            for message_id in message_ids:
                await self._process_message(message_id)
                redis_client.lrem(critical_queue, 1, message_id)
                
        except Exception as e:
            print(f"[INFO] Redis Cluster: Critical message processing failed: {e}")
    
    async def _process_normal_messages(self) -> None:
        """Process normal priority messages."""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                return
            
            # Get all online agents
            agent_ids = redis_client.smembers("agents:online")
            
            for agent_id in agent_ids:
                receiver_queue = f"queue:{agent_id}"
                message_ids = redis_client.lrange(receiver_queue, 0, 4)  # Process up to 5 messages per agent
                
                for message_id in message_ids:
                    await self._process_message(message_id)
                    redis_client.lrem(receiver_queue, 1, message_id)
                    
        except Exception as e:
            print(f"[INFO] Redis Cluster: Normal message processing failed: {e}")
    
    async def _process_message(self, message_id: str) -> None:
        """Process a single message."""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                return
            
            message_key = f"message:{message_id}"
            message_json = redis_client.get(message_key)
            
            if not message_json:
                return
            
            message_data = json.loads(message_json)
            message = RedisMessage.from_dict(message_data)
            
            # Check if message has expired
            if message.expires_at and message.expires_at < datetime.utcnow():
                redis_client.delete(message_key)
                return
            
            # Call registered handlers
            handlers = self.message_handlers.get(message.message_type, [])
            for handler in handlers:
                try:
                    await handler(message)
                except Exception as e:
                    print(f"[INFO] Redis Cluster: Handler failed for message {message_id}: {e}")
            
            # Mark as processed
            message_data["delivered"] = True
            redis_client.set(message_key, json.dumps(message_data))
            
        except Exception as e:
            print(f"[INFO] Redis Cluster: Message processing failed: {e}")
    
    async def _cleanup_expired_messages(self) -> None:
        """Clean up expired messages."""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                return
            
            # This would be implemented with Redis TTL and background cleanup
            # For now, we rely on Redis TTL expiration
            
        except Exception as e:
            print(f"[INFO] Redis Cluster: Cleanup failed: {e}")
    
    def stop_message_processing(self) -> None:
        """Stop message processing service."""
        self.running = False
        print("🛑 Redis Cluster: Message processing service stopped")
    
    def get_cluster_status(self) -> Dict[str, Any]:
        """Get Redis cluster status."""
        try:
            redis_client = self._get_redis_client()
            
            # Test connection
            redis_client.ping()
            
            # Get cluster info
            info = redis_client.info()
            
            return {
                "status": "connected",
                "connected": True,
                "redis_version": info.get("redis_version", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "unknown"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "host": "redis.cerebral.baerautotech.com:6380"
            }
            
        except RuntimeError as e:
            return {
                "status": "unavailable", 
                "connected": False, 
                "error": str(e),
                "host": "redis.cerebral.baerautotech.com:6380",
                "message": "Cerebral Redis cluster is not accessible"
            }
        except Exception as e:
            return {
                "status": "error", 
                "connected": False, 
                "error": str(e),
                "host": "redis.cerebral.baerautotech.com:6380"
            }


# Global Redis messaging instance
redis_cluster_messaging = BMADRedisClusterMessaging()


def get_redis_cluster_messaging() -> BMADRedisClusterMessaging:
    """Get global Redis cluster messaging instance."""
    return redis_cluster_messaging


# Test function
async def test_redis_cluster_messaging():
    """Test Redis cluster messaging."""
    print("[INFO] Redis Cluster: Testing Redis Cluster Messaging...")
    
    messaging = get_redis_cluster_messaging()
    
    # Test connection
    status = messaging.get_cluster_status()
    print(f"Redis status: {status}")
    
    # Register test agents
    await messaging.register_agent("test_agent_1", "analyst")
    await messaging.register_agent("test_agent_2", "pm")
    
    # Send test message
    message_id = await messaging.send_message(
        sender_id="test_agent_1",
        receiver_id="test_agent_2",
        message_type=MessageType.TASK_REQUEST,
        content={"task": "test_task", "data": "test_data"},
        priority=MessagePriority.HIGH
    )
    print(f"Sent message: {message_id}")
    
    # Get messages
    messages = await messaging.get_messages_for_agent("test_agent_2")
    print(f"Received {len(messages)} messages")
    
    # Test broadcast
    broadcast_ids = await messaging.broadcast_message(
        sender_id="test_agent_1",
        agent_type="pm",
        message_type=MessageType.STATUS_UPDATE,
        content={"status": "testing"}
    )
    print(f"Broadcasted {len(broadcast_ids)} messages")
    
    # Test agent discovery
    agents = await messaging.discover_agents("analyst")
    print(f"Discovered {len(agents)} analyst agents")
    
    print("[INFO] Redis Cluster: Redis cluster messaging test complete!")


if __name__ == "__main__":
    asyncio.run(test_redis_cluster_messaging())
