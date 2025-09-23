"""
BMAD Advanced Analytics System

This module provides comprehensive analytics for BMAD operations including:
- Usage analytics and metrics
- Performance analytics
- User behavior analytics
- Workflow execution analytics
- Provider performance analytics
- Business intelligence metrics
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


class AnalyticsEventType(Enum):
    """Types of analytics events."""
    WORKFLOW_START = "workflow_start"
    WORKFLOW_COMPLETE = "workflow_complete"
    WORKFLOW_FAIL = "workflow_fail"
    TOOL_EXECUTION = "tool_execution"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    API_REQUEST = "api_request"
    PROVIDER_REQUEST = "provider_request"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    RATE_LIMIT_HIT = "rate_limit_hit"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class AnalyticsEvent:
    """Analytics event data structure."""
    event_type: AnalyticsEventType
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    workflow_id: Optional[str] = None
    tool_name: Optional[str] = None
    provider_name: Optional[str] = None
    duration_ms: Optional[float] = None
    success: Optional[bool] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserAnalytics:
    """User analytics data."""
    user_id: str
    total_sessions: int = 0
    total_workflows: int = 0
    total_tools_executed: int = 0
    avg_session_duration: float = 0.0
    favorite_tools: List[str] = field(default_factory=list)
    last_active: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WorkflowAnalytics:
    """Workflow analytics data."""
    workflow_name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    avg_execution_time: float = 0.0
    avg_tools_per_execution: float = 0.0
    unique_users: set = field(default_factory=set)
    last_execution: Optional[datetime] = None


@dataclass
class ProviderAnalytics:
    """Provider analytics data."""
    provider_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    avg_tokens_per_request: float = 0.0
    total_cost: float = 0.0
    last_request: Optional[datetime] = None


class BMADAnalyticsEngine:
    """
    Advanced analytics engine for BMAD operations.
    
    Provides comprehensive analytics including usage patterns,
    performance metrics, user behavior, and business intelligence.
    """
    
    def __init__(self, 
                 db_path: str = "/tmp/bmad_analytics.db",
                 retention_days: int = 90,
                 batch_size: int = 1000,
                 flush_interval: int = 60):
        """Initialize the analytics engine."""
        self.db_path = db_path
        self.retention_days = retention_days
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        # In-memory analytics data
        self._events_buffer: deque = deque(maxlen=batch_size * 2)
        self._user_analytics: Dict[str, UserAnalytics] = {}
        self._workflow_analytics: Dict[str, WorkflowAnalytics] = {}
        self._provider_analytics: Dict[str, ProviderAnalytics] = {}
        
        # Real-time metrics
        self._real_time_metrics = {
            'requests_per_minute': deque(maxlen=60),
            'active_users': set(),
            'active_workflows': set(),
            'error_rate': deque(maxlen=100),
            'avg_response_time': deque(maxlen=100)
        }
        
        # Initialize database
        self._init_database()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _init_database(self):
        """Initialize SQLite database for analytics."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analytics_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    session_id TEXT,
                    workflow_id TEXT,
                    tool_name TEXT,
                    provider_name TEXT,
                    duration_ms REAL,
                    success BOOLEAN,
                    error_message TEXT,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_timestamp 
                ON analytics_events(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_user_id 
                ON analytics_events(user_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_workflow_id 
                ON analytics_events(workflow_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_event_type 
                ON analytics_events(event_type)
            """)
    
    def track_event(self, event: AnalyticsEvent):
        """Track an analytics event."""
        self._events_buffer.append(event)
        
        # Update real-time metrics
        self._update_real_time_metrics(event)
        
        # Update in-memory analytics
        self._update_in_memory_analytics(event)
        
        # Flush if buffer is full
        if len(self._events_buffer) >= self.batch_size:
            asyncio.create_task(self._flush_events())
    
    def _update_real_time_metrics(self, event: AnalyticsEvent):
        """Update real-time metrics."""
        now = datetime.utcnow()
        
        # Requests per minute
        if event.event_type == AnalyticsEventType.API_REQUEST:
            self._real_time_metrics['requests_per_minute'].append(now)
        
        # Active users
        if event.user_id:
            if event.event_type in [AnalyticsEventType.USER_LOGIN, AnalyticsEventType.API_REQUEST]:
                self._real_time_metrics['active_users'].add(event.user_id)
            elif event.event_type == AnalyticsEventType.USER_LOGOUT:
                self._real_time_metrics['active_users'].discard(event.user_id)
        
        # Active workflows
        if event.workflow_id:
            if event.event_type == AnalyticsEventType.WORKFLOW_START:
                self._real_time_metrics['active_workflows'].add(event.workflow_id)
            elif event.event_type in [AnalyticsEventType.WORKFLOW_COMPLETE, AnalyticsEventType.WORKFLOW_FAIL]:
                self._real_time_metrics['active_workflows'].discard(event.workflow_id)
        
        # Error rate
        if event.success is not None:
            self._real_time_metrics['error_rate'].append(not event.success)
        
        # Response time
        if event.duration_ms is not None:
            self._real_time_metrics['avg_response_time'].append(event.duration_ms)
    
    def _update_in_memory_analytics(self, event: AnalyticsEvent):
        """Update in-memory analytics data."""
        # User analytics
        if event.user_id:
            if event.user_id not in self._user_analytics:
                self._user_analytics[event.user_id] = UserAnalytics(user_id=event.user_id)
            
            user_analytics = self._user_analytics[event.user_id]
            
            if event.event_type == AnalyticsEventType.USER_LOGIN:
                user_analytics.total_sessions += 1
            elif event.event_type == AnalyticsEventType.WORKFLOW_START:
                user_analytics.total_workflows += 1
            elif event.event_type == AnalyticsEventType.TOOL_EXECUTION:
                user_analytics.total_tools_executed += 1
                if event.tool_name and event.tool_name not in user_analytics.favorite_tools:
                    user_analytics.favorite_tools.append(event.tool_name)
            
            user_analytics.last_active = event.timestamp
        
        # Workflow analytics
        if event.workflow_id:
            workflow_name = event.metadata.get('workflow_name', 'unknown')
            if workflow_name not in self._workflow_analytics:
                self._workflow_analytics[workflow_name] = WorkflowAnalytics(workflow_name=workflow_name)
            
            workflow_analytics = self._workflow_analytics[workflow_name]
            
            if event.event_type == AnalyticsEventType.WORKFLOW_START:
                workflow_analytics.total_executions += 1
                if event.user_id:
                    workflow_analytics.unique_users.add(event.user_id)
            elif event.event_type == AnalyticsEventType.WORKFLOW_COMPLETE:
                workflow_analytics.successful_executions += 1
                if event.duration_ms:
                    workflow_analytics.avg_execution_time = (
                        (workflow_analytics.avg_execution_time * 
                         (workflow_analytics.successful_executions - 1) + event.duration_ms) /
                        workflow_analytics.successful_executions
                    )
            elif event.event_type == AnalyticsEventType.WORKFLOW_FAIL:
                workflow_analytics.failed_executions += 1
            
            workflow_analytics.last_execution = event.timestamp
        
        # Provider analytics
        if event.provider_name:
            if event.provider_name not in self._provider_analytics:
                self._provider_analytics[event.provider_name] = ProviderAnalytics(provider_name=event.provider_name)
            
            provider_analytics = self._provider_analytics[event.provider_name]
            
            if event.event_type == AnalyticsEventType.PROVIDER_REQUEST:
                provider_analytics.total_requests += 1
                if event.success:
                    provider_analytics.successful_requests += 1
                else:
                    provider_analytics.failed_requests += 1
                
                if event.duration_ms:
                    provider_analytics.avg_response_time = (
                        (provider_analytics.avg_response_time * 
                         (provider_analytics.total_requests - 1) + event.duration_ms) /
                        provider_analytics.total_requests
                    )
                
                provider_analytics.last_request = event.timestamp
    
    async def _flush_events(self):
        """Flush events to database."""
        if not self._events_buffer:
            return
        
        events_to_flush = []
        while self._events_buffer:
            events_to_flush.append(self._events_buffer.popleft())
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.executemany("""
                    INSERT INTO analytics_events 
                    (event_type, timestamp, user_id, session_id, workflow_id, 
                     tool_name, provider_name, duration_ms, success, error_message, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    (
                        event.event_type.value,
                        event.timestamp.isoformat(),
                        event.user_id,
                        event.session_id,
                        event.workflow_id,
                        event.tool_name,
                        event.provider_name,
                        event.duration_ms,
                        event.success,
                        event.error_message,
                        json.dumps(event.metadata)
                    )
                    for event in events_to_flush
                ])
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to flush events to database: {e}")
            # Re-add events to buffer for retry
            for event in events_to_flush:
                self._events_buffer.appendleft(event)
    
    def _start_background_tasks(self):
        """Start background analytics tasks."""
        async def periodic_flush():
            while True:
                try:
                    await asyncio.sleep(self.flush_interval)
                    await self._flush_events()
                except Exception as e:
                    logger.error(f"Periodic flush error: {e}")
        
        async def cleanup_old_data():
            while True:
                try:
                    await asyncio.sleep(3600)  # Run every hour
                    await self._cleanup_old_data()
                except Exception as e:
                    logger.error(f"Cleanup error: {e}")
        
        # Start background tasks
        asyncio.create_task(periodic_flush())
        asyncio.create_task(cleanup_old_data())
    
    async def _cleanup_old_data(self):
        """Clean up old analytics data."""
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "DELETE FROM analytics_events WHERE timestamp < ?",
                    (cutoff_date.isoformat(),)
                )
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics."""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Calculate requests per minute
        recent_requests = [
            req_time for req_time in self._real_time_metrics['requests_per_minute']
            if req_time > minute_ago
        ]
        requests_per_minute = len(recent_requests)
        
        # Calculate error rate
        error_rate = 0.0
        if self._real_time_metrics['error_rate']:
            error_rate = sum(self._real_time_metrics['error_rate']) / len(self._real_time_metrics['error_rate'])
        
        # Calculate average response time
        avg_response_time = 0.0
        if self._real_time_metrics['avg_response_time']:
            avg_response_time = sum(self._real_time_metrics['avg_response_time']) / len(self._real_time_metrics['avg_response_time'])
        
        return {
            'timestamp': now.isoformat(),
            'requests_per_minute': requests_per_minute,
            'active_users': len(self._real_time_metrics['active_users']),
            'active_workflows': len(self._real_time_metrics['active_workflows']),
            'error_rate': error_rate,
            'avg_response_time_ms': avg_response_time
        }
    
    def get_user_analytics(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics for a specific user."""
        if user_id not in self._user_analytics:
            return None
        
        user_analytics = self._user_analytics[user_id]
        return {
            'user_id': user_analytics.user_id,
            'total_sessions': user_analytics.total_sessions,
            'total_workflows': user_analytics.total_workflows,
            'total_tools_executed': user_analytics.total_tools_executed,
            'avg_session_duration': user_analytics.avg_session_duration,
            'favorite_tools': user_analytics.favorite_tools[:10],  # Top 10
            'last_active': user_analytics.last_active.isoformat() if user_analytics.last_active else None,
            'created_at': user_analytics.created_at.isoformat()
        }
    
    def get_workflow_analytics(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """Get analytics for a specific workflow."""
        if workflow_name not in self._workflow_analytics:
            return None
        
        workflow_analytics = self._workflow_analytics[workflow_name]
        success_rate = 0.0
        if workflow_analytics.total_executions > 0:
            success_rate = workflow_analytics.successful_executions / workflow_analytics.total_executions
        
        return {
            'workflow_name': workflow_analytics.workflow_name,
            'total_executions': workflow_analytics.total_executions,
            'successful_executions': workflow_analytics.successful_executions,
            'failed_executions': workflow_analytics.failed_executions,
            'success_rate': success_rate,
            'avg_execution_time_ms': workflow_analytics.avg_execution_time,
            'unique_users': len(workflow_analytics.unique_users),
            'last_execution': workflow_analytics.last_execution.isoformat() if workflow_analytics.last_execution else None
        }
    
    def get_provider_analytics(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """Get analytics for a specific provider."""
        if provider_name not in self._provider_analytics:
            return None
        
        provider_analytics = self._provider_analytics[provider_name]
        success_rate = 0.0
        if provider_analytics.total_requests > 0:
            success_rate = provider_analytics.successful_requests / provider_analytics.total_requests
        
        return {
            'provider_name': provider_analytics.provider_name,
            'total_requests': provider_analytics.total_requests,
            'successful_requests': provider_analytics.successful_requests,
            'failed_requests': provider_analytics.failed_requests,
            'success_rate': success_rate,
            'avg_response_time_ms': provider_analytics.avg_response_time,
            'total_cost': provider_analytics.total_cost,
            'last_request': provider_analytics.last_request.isoformat() if provider_analytics.last_request else None
        }
    
    def get_business_intelligence_metrics(self) -> Dict[str, Any]:
        """Get business intelligence metrics."""
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        
        # Calculate metrics from database
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Daily active users
                dau_query = """
                    SELECT COUNT(DISTINCT user_id) 
                    FROM analytics_events 
                    WHERE timestamp > ? AND user_id IS NOT NULL
                """
                dau_24h = conn.execute(dau_query, (last_24h.isoformat(),)).fetchone()[0]
                dau_7d = conn.execute(dau_query, (last_7d.isoformat(),)).fetchone()[0]
                dau_30d = conn.execute(dau_query, (last_30d.isoformat(),)).fetchone()[0]
                
                # Workflow execution trends
                workflow_trends_query = """
                    SELECT event_type, COUNT(*) 
                    FROM analytics_events 
                    WHERE timestamp > ? AND workflow_id IS NOT NULL
                    GROUP BY event_type
                """
                workflow_trends_24h = dict(conn.execute(workflow_trends_query, (last_24h.isoformat(),)).fetchall())
                workflow_trends_7d = dict(conn.execute(workflow_trends_query, (last_7d.isoformat(),)).fetchall())
                
                # Tool usage statistics
                tool_usage_query = """
                    SELECT tool_name, COUNT(*) 
                    FROM analytics_events 
                    WHERE timestamp > ? AND tool_name IS NOT NULL
                    GROUP BY tool_name 
                    ORDER BY COUNT(*) DESC 
                    LIMIT 10
                """
                top_tools_24h = conn.execute(tool_usage_query, (last_24h.isoformat(),)).fetchall()
                top_tools_7d = conn.execute(tool_usage_query, (last_7d.isoformat(),)).fetchall()
                
                # Error analysis
                error_query = """
                    SELECT error_message, COUNT(*) 
                    FROM analytics_events 
                    WHERE timestamp > ? AND success = 0 AND error_message IS NOT NULL
                    GROUP BY error_message 
                    ORDER BY COUNT(*) DESC 
                    LIMIT 5
                """
                top_errors_24h = conn.execute(error_query, (last_24h.isoformat(),)).fetchall()
                
        except Exception as e:
            logger.error(f"Failed to calculate BI metrics: {e}")
            return {}
        
        return {
            'timestamp': now.isoformat(),
            'daily_active_users': {
                'last_24h': dau_24h,
                'last_7d': dau_7d,
                'last_30d': dau_30d
            },
            'workflow_trends': {
                'last_24h': workflow_trends_24h,
                'last_7d': workflow_trends_7d
            },
            'top_tools': {
                'last_24h': top_tools_24h,
                'last_7d': top_tools_7d
            },
            'top_errors': {
                'last_24h': top_errors_24h
            },
            'in_memory_stats': {
                'total_users': len(self._user_analytics),
                'total_workflows': len(self._workflow_analytics),
                'total_providers': len(self._provider_analytics)
            }
        }
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive analytics report."""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'real_time_metrics': self.get_real_time_metrics(),
            'business_intelligence': self.get_business_intelligence_metrics(),
            'user_analytics_summary': {
                'total_users': len(self._user_analytics),
                'top_users': sorted(
                    [(user_id, analytics.total_workflows) for user_id, analytics in self._user_analytics.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            },
            'workflow_analytics_summary': {
                'total_workflows': len(self._workflow_analytics),
                'top_workflows': sorted(
                    [(name, analytics.total_executions) for name, analytics in self._workflow_analytics.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            },
            'provider_analytics_summary': {
                'total_providers': len(self._provider_analytics),
                'provider_performance': [
                    {
                        'name': analytics.provider_name,
                        'success_rate': analytics.successful_requests / analytics.total_requests if analytics.total_requests > 0 else 0,
                        'avg_response_time': analytics.avg_response_time,
                        'total_requests': analytics.total_requests
                    }
                    for analytics in self._provider_analytics.values()
                ]
            }
        }


# Global analytics engine instance
analytics_engine = BMADAnalyticsEngine()


# Convenience functions for tracking events
def track_workflow_start(workflow_id: str, workflow_name: str, user_id: str, session_id: str):
    """Track workflow start event."""
    event = AnalyticsEvent(
        event_type=AnalyticsEventType.WORKFLOW_START,
        timestamp=datetime.utcnow(),
        user_id=user_id,
        session_id=session_id,
        workflow_id=workflow_id,
        metadata={'workflow_name': workflow_name}
    )
    analytics_engine.track_event(event)


def track_workflow_complete(workflow_id: str, workflow_name: str, user_id: str, session_id: str, duration_ms: float):
    """Track workflow completion event."""
    event = AnalyticsEvent(
        event_type=AnalyticsEventType.WORKFLOW_COMPLETE,
        timestamp=datetime.utcnow(),
        user_id=user_id,
        session_id=session_id,
        workflow_id=workflow_id,
        duration_ms=duration_ms,
        success=True,
        metadata={'workflow_name': workflow_name}
    )
    analytics_engine.track_event(event)


def track_workflow_fail(workflow_id: str, workflow_name: str, user_id: str, session_id: str, error_message: str):
    """Track workflow failure event."""
    event = AnalyticsEvent(
        event_type=AnalyticsEventType.WORKFLOW_FAIL,
        timestamp=datetime.utcnow(),
        user_id=user_id,
        session_id=session_id,
        workflow_id=workflow_id,
        success=False,
        error_message=error_message,
        metadata={'workflow_name': workflow_name}
    )
    analytics_engine.track_event(event)


def track_tool_execution(tool_name: str, user_id: str, session_id: str, duration_ms: float, success: bool):
    """Track tool execution event."""
    event = AnalyticsEvent(
        event_type=AnalyticsEventType.TOOL_EXECUTION,
        timestamp=datetime.utcnow(),
        user_id=user_id,
        session_id=session_id,
        tool_name=tool_name,
        duration_ms=duration_ms,
        success=success
    )
    analytics_engine.track_event(event)


def track_provider_request(provider_name: str, duration_ms: float, success: bool, tokens_used: int = 0):
    """Track provider request event."""
    event = AnalyticsEvent(
        event_type=AnalyticsEventType.PROVIDER_REQUEST,
        timestamp=datetime.utcnow(),
        provider_name=provider_name,
        duration_ms=duration_ms,
        success=success,
        metadata={'tokens_used': tokens_used}
    )
    analytics_engine.track_event(event)


def track_api_request(user_id: str, session_id: str, endpoint: str, duration_ms: float, success: bool):
    """Track API request event."""
    event = AnalyticsEvent(
        event_type=AnalyticsEventType.API_REQUEST,
        timestamp=datetime.utcnow(),
        user_id=user_id,
        session_id=session_id,
        duration_ms=duration_ms,
        success=success,
        metadata={'endpoint': endpoint}
    )
    analytics_engine.track_event(event)
