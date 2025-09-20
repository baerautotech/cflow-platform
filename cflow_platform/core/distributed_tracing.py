"""
Distributed Tracing and Observability System for WebMCP Performance Enhancement

This module provides comprehensive observability capabilities including:
- Distributed tracing with span creation and correlation
- Performance metrics collection and aggregation
- Request/response logging with structured data
- Service dependency mapping
- Error tracking and analysis
- Real-time monitoring dashboards
"""

import asyncio
import logging
import time
import uuid
import json
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import threading
import traceback
from datetime import datetime
import contextvars

logger = logging.getLogger(__name__)


class SpanStatus(Enum):
    """Span status types"""
    OK = "ok"
    ERROR = "error"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class SpanKind(Enum):
    """Span kinds for different operation types"""
    CLIENT = "client"
    SERVER = "server"
    INTERNAL = "internal"
    PRODUCER = "producer"
    CONSUMER = "consumer"


@dataclass
class SpanContext:
    """Span context for distributed tracing"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    baggage: Dict[str, str] = field(default_factory=dict)


@dataclass
class Span:
    """Distributed tracing span"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    name: str = ""
    kind: SpanKind = SpanKind.INTERNAL
    start_time: float = 0.0
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    status: SpanStatus = SpanStatus.OK
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    links: List[Dict[str, str]] = field(default_factory=list)
    error_message: Optional[str] = None
    error_stack_trace: Optional[str] = None
    service_name: str = "unknown"
    operation_name: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Trace:
    """Complete trace with multiple spans"""
    trace_id: str
    spans: List[Span] = field(default_factory=list)
    start_time: float = 0.0
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    root_span: Optional[Span] = None
    service_count: int = 0
    error_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceMetrics:
    """Trace performance metrics"""
    trace_id: str
    total_spans: int = 0
    error_spans: int = 0
    total_duration_ms: float = 0.0
    average_span_duration_ms: float = 0.0
    max_span_duration_ms: float = 0.0
    min_span_duration_ms: float = 0.0
    service_count: int = 0
    critical_path_duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class Tracer:
    """
    Distributed tracer for creating and managing spans.
    
    Features:
    - Span creation and management
    - Trace context propagation
    - Performance metrics collection
    - Error tracking and analysis
    - Service dependency mapping
    """
    
    def __init__(self, service_name: str = "webmcp"):
        self.service_name = service_name
        self._active_spans: Dict[str, Span] = {}
        self._completed_spans: deque = deque(maxlen=10000)
        self._traces: Dict[str, Trace] = {}
        self._span_context_var = contextvars.ContextVar('span_context', default=None)
        
        # Metrics
        self._span_count = 0
        self._error_count = 0
        self._total_duration = 0.0
        
        # Lock for thread safety
        self._lock = threading.RLock()
    
    def start_span(
        self,
        name: str,
        parent_span_id: Optional[str] = None,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None,
        service_name: Optional[str] = None
    ) -> Span:
        """Start a new span"""
        with self._lock:
            # Generate IDs
            span_id = str(uuid.uuid4())
            
            # Get or create trace ID
            current_context = self._span_context_var.get()
            if current_context:
                trace_id = current_context.trace_id
                if not parent_span_id:
                    parent_span_id = current_context.span_id
            else:
                trace_id = str(uuid.uuid4())
            
            # Create span
            span = Span(
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                name=name,
                kind=kind,
                start_time=time.time(),
                attributes=attributes or {},
                service_name=service_name or self.service_name,
                operation_name=name
            )
            
            # Store active span
            self._active_spans[span_id] = span
            
            # Update context
            new_context = SpanContext(
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id
            )
            self._span_context_var.set(new_context)
            
            # Update metrics
            self._span_count += 1
            
            logger.debug(f"Started span {span_id} in trace {trace_id}: {name}")
            
            return span
    
    def end_span(
        self,
        span_id: str,
        status: SpanStatus = SpanStatus.OK,
        error_message: Optional[str] = None,
        error_stack_trace: Optional[str] = None
    ):
        """End a span"""
        with self._lock:
            if span_id not in self._active_spans:
                logger.warning(f"Attempted to end non-existent span: {span_id}")
                return
            
            span = self._active_spans[span_id]
            span.end_time = time.time()
            span.duration_ms = (span.end_time - span.start_time) * 1000
            span.status = status
            span.error_message = error_message
            span.error_stack_trace = error_stack_trace
            
            # Update metrics
            self._total_duration += span.duration_ms
            if status == SpanStatus.ERROR:
                self._error_count += 1
            
            # Move to completed spans
            self._completed_spans.append(span)
            del self._active_spans[span_id]
            
            # Update trace
            self._update_trace(span)
            
            # Clear context if this was the root span
            current_context = self._span_context_var.get()
            if current_context and current_context.span_id == span_id:
                # Find parent context or clear
                parent_context = None
                if span.parent_span_id:
                    # Find parent span to restore context
                    for completed_span in self._completed_spans:
                        if completed_span.span_id == span.parent_span_id:
                            parent_context = SpanContext(
                                trace_id=completed_span.trace_id,
                                span_id=completed_span.span_id,
                                parent_span_id=completed_span.parent_span_id
                            )
                            break
                
                self._span_context_var.set(parent_context)
            
            logger.debug(f"Ended span {span_id}: {span.duration_ms:.2f}ms, status: {status.value}")
    
    def add_span_event(self, span_id: str, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add an event to a span"""
        with self._lock:
            if span_id not in self._active_spans:
                logger.warning(f"Attempted to add event to non-existent span: {span_id}")
                return
            
            span = self._active_spans[span_id]
            event = {
                "name": name,
                "timestamp": time.time(),
                "attributes": attributes or {}
            }
            span.events.append(event)
    
    def add_span_attribute(self, span_id: str, key: str, value: Any):
        """Add an attribute to a span"""
        with self._lock:
            if span_id not in self._active_spans:
                logger.warning(f"Attempted to add attribute to non-existent span: {span_id}")
                return
            
            span = self._active_spans[span_id]
            span.attributes[key] = value
    
    def _update_trace(self, span: Span):
        """Update trace with completed span"""
        trace_id = span.trace_id
        
        if trace_id not in self._traces:
            self._traces[trace_id] = Trace(
                trace_id=trace_id,
                start_time=span.start_time
            )
        
        trace = self._traces[trace_id]
        trace.spans.append(span)
        
        # Update trace timing
        if not trace.end_time or span.end_time > trace.end_time:
            trace.end_time = span.end_time
        
        trace.duration_ms = (trace.end_time - trace.start_time) * 1000
        
        # Update root span
        if not span.parent_span_id:
            trace.root_span = span
        
        # Update counts
        trace.service_count = len(set(s.service_name for s in trace.spans))
        trace.error_count = sum(1 for s in trace.spans if s.status == SpanStatus.ERROR)
    
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a complete trace by ID"""
        return self._traces.get(trace_id)
    
    def get_trace_metrics(self, trace_id: str) -> Optional[TraceMetrics]:
        """Get metrics for a trace"""
        trace = self.get_trace(trace_id)
        if not trace:
            return None
        
        if not trace.spans:
            return TraceMetrics(trace_id=trace_id)
        
        durations = [span.duration_ms for span in trace.spans]
        
        return TraceMetrics(
            trace_id=trace_id,
            total_spans=len(trace.spans),
            error_spans=trace.error_count,
            total_duration_ms=trace.duration_ms,
            average_span_duration_ms=sum(durations) / len(durations),
            max_span_duration_ms=max(durations),
            min_span_duration_ms=min(durations),
            service_count=trace.service_count,
            critical_path_duration_ms=self._calculate_critical_path(trace)
        )
    
    def _calculate_critical_path(self, trace: Trace) -> float:
        """Calculate critical path duration for a trace"""
        # Simple critical path calculation - longest path from root to leaf
        # This is a simplified version; a full implementation would use
        # topological sort and longest path algorithm
        
        if not trace.spans:
            return 0.0
        
        # Find root spans (no parent)
        root_spans = [span for span in trace.spans if not span.parent_span_id]
        
        if not root_spans:
            # No root spans, return max duration
            return max(span.duration_ms for span in trace.spans)
        
        max_path_duration = 0.0
        
        for root_span in root_spans:
            path_duration = self._calculate_path_duration(root_span, trace.spans)
            max_path_duration = max(max_path_duration, path_duration)
        
        return max_path_duration
    
    def _calculate_path_duration(self, span: Span, all_spans: List[Span]) -> float:
        """Calculate duration of path starting from a span"""
        # Find child spans
        child_spans = [s for s in all_spans if s.parent_span_id == span.span_id]
        
        if not child_spans:
            return span.duration_ms
        
        max_child_duration = 0.0
        for child in child_spans:
            child_duration = self._calculate_path_duration(child, all_spans)
            max_child_duration = max(max_child_duration, child_duration)
        
        return span.duration_ms + max_child_duration
    
    def get_tracer_stats(self) -> Dict[str, Any]:
        """Get tracer statistics"""
        with self._lock:
            return {
                "active_spans": len(self._active_spans),
                "completed_spans": len(self._completed_spans),
                "total_traces": len(self._traces),
                "total_spans_created": self._span_count,
                "total_errors": self._error_count,
                "total_duration_ms": self._total_duration,
                "average_duration_ms": self._total_duration / max(self._span_count, 1),
                "error_rate": self._error_count / max(self._span_count, 1)
            }


class TraceCollector:
    """
    Collects and manages trace data for analysis and export.
    
    Features:
    - Trace collection and storage
    - Trace filtering and search
    - Performance analysis
    - Export to external systems
    """
    
    def __init__(self, max_traces: int = 1000):
        self.max_traces = max_traces
        self._traces: Dict[str, Trace] = {}
        self._trace_metrics: Dict[str, TraceMetrics] = {}
        self._service_dependencies: Dict[str, set] = defaultdict(set)
        
    def add_trace(self, trace: Trace):
        """Add a trace to the collector"""
        self._traces[trace.trace_id] = trace
        
        # Calculate and store metrics
        metrics = self._calculate_trace_metrics(trace)
        self._trace_metrics[trace.trace_id] = metrics
        
        # Update service dependencies
        self._update_service_dependencies(trace)
        
        # Maintain size limit
        if len(self._traces) > self.max_traces:
            # Remove oldest trace
            oldest_trace_id = min(
                self._traces.keys(),
                key=lambda tid: self._traces[tid].start_time
            )
            del self._traces[oldest_trace_id]
            del self._trace_metrics[oldest_trace_id]
    
    def _calculate_trace_metrics(self, trace: Trace) -> TraceMetrics:
        """Calculate metrics for a trace"""
        if not trace.spans:
            return TraceMetrics(trace_id=trace.trace_id)
        
        durations = [span.duration_ms for span in trace.spans]
        
        return TraceMetrics(
            trace_id=trace.trace_id,
            total_spans=len(trace.spans),
            error_spans=trace.error_count,
            total_duration_ms=trace.duration_ms,
            average_span_duration_ms=sum(durations) / len(durations),
            max_span_duration_ms=max(durations),
            min_span_duration_ms=min(durations),
            service_count=trace.service_count,
            critical_path_duration_ms=self._calculate_critical_path(trace)
        )
    
    def _calculate_critical_path(self, trace: Trace) -> float:
        """Calculate critical path for trace metrics"""
        # Simplified critical path calculation
        if not trace.spans:
            return 0.0
        
        root_spans = [span for span in trace.spans if not span.parent_span_id]
        if not root_spans:
            return max(span.duration_ms for span in trace.spans)
        
        max_duration = 0.0
        for root in root_spans:
            duration = self._calculate_path_duration(root, trace.spans)
            max_duration = max(max_duration, duration)
        
        return max_duration
    
    def _calculate_path_duration(self, span: Span, all_spans: List[Span]) -> float:
        """Calculate path duration from span"""
        children = [s for s in all_spans if s.parent_span_id == span.span_id]
        if not children:
            return span.duration_ms
        
        max_child_duration = max(
            self._calculate_path_duration(child, all_spans) for child in children
        )
        return span.duration_ms + max_child_duration
    
    def _update_service_dependencies(self, trace: Trace):
        """Update service dependency mapping"""
        services = set(span.service_name for span in trace.spans)
        
        for service in services:
            other_services = services - {service}
            self._service_dependencies[service].update(other_services)
    
    def get_traces_by_service(self, service_name: str, limit: int = 100) -> List[Trace]:
        """Get traces involving a specific service"""
        traces = []
        for trace in self._traces.values():
            if any(span.service_name == service_name for span in trace.spans):
                traces.append(trace)
                if len(traces) >= limit:
                    break
        
        return sorted(traces, key=lambda t: t.start_time, reverse=True)
    
    def get_traces_by_duration(self, min_duration_ms: float, limit: int = 100) -> List[Trace]:
        """Get traces with duration above threshold"""
        traces = [
            trace for trace in self._traces.values()
            if trace.duration_ms >= min_duration_ms
        ]
        return sorted(traces, key=lambda t: t.duration_ms, reverse=True)[:limit]
    
    def get_error_traces(self, limit: int = 100) -> List[Trace]:
        """Get traces with errors"""
        error_traces = [
            trace for trace in self._traces.values()
            if trace.error_count > 0
        ]
        return sorted(error_traces, key=lambda t: t.start_time, reverse=True)[:limit]
    
    def get_service_dependencies(self) -> Dict[str, List[str]]:
        """Get service dependency graph"""
        return {
            service: list(dependencies)
            for service, dependencies in self._service_dependencies.items()
        }
    
    def get_trace_statistics(self) -> Dict[str, Any]:
        """Get overall trace statistics"""
        if not self._traces:
            return {}
        
        all_metrics = list(self._trace_metrics.values())
        
        return {
            "total_traces": len(self._traces),
            "total_spans": sum(m.total_spans for m in all_metrics),
            "error_traces": sum(1 for m in all_metrics if m.error_spans > 0),
            "average_duration_ms": sum(m.total_duration_ms for m in all_metrics) / len(all_metrics),
            "max_duration_ms": max(m.total_duration_ms for m in all_metrics),
            "min_duration_ms": min(m.total_duration_ms for m in all_metrics),
            "average_spans_per_trace": sum(m.total_spans for m in all_metrics) / len(all_metrics),
            "services_involved": len(self._service_dependencies),
            "error_rate": sum(1 for m in all_metrics if m.error_spans > 0) / len(all_metrics)
        }


class TraceExporter:
    """
    Exports trace data to external systems.
    
    Features:
    - Multiple export formats (JSON, OpenTelemetry)
    - Batch export with buffering
    - Export filtering and sampling
    - Error handling and retry logic
    """
    
    def __init__(self, batch_size: int = 100, flush_interval_seconds: float = 30.0):
        self.batch_size = batch_size
        self.flush_interval_seconds = flush_interval_seconds
        self._export_buffer: List[Trace] = []
        self._export_callbacks: List[Callable[[List[Trace]], Awaitable[None]]] = []
        self._flush_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the trace exporter"""
        self._flush_task = asyncio.create_task(self._flush_loop())
        logger.info("TraceExporter started")
    
    async def stop(self):
        """Stop the trace exporter"""
        if self._flush_task:
            self._flush_task.cancel()
        
        # Flush remaining traces
        if self._export_buffer:
            await self._flush_buffer()
        
        logger.info("TraceExporter stopped")
    
    def add_export_callback(self, callback: Callable[[List[Trace]], Awaitable[None]]):
        """Add an export callback"""
        self._export_callbacks.append(callback)
    
    async def export_trace(self, trace: Trace):
        """Export a single trace"""
        self._export_buffer.append(trace)
        
        if len(self._export_buffer) >= self.batch_size:
            await self._flush_buffer()
    
    async def export_traces(self, traces: List[Trace]):
        """Export multiple traces"""
        for trace in traces:
            await self.export_trace(trace)
    
    async def _flush_buffer(self):
        """Flush export buffer"""
        if not self._export_buffer:
            return
        
        traces_to_export = self._export_buffer.copy()
        self._export_buffer.clear()
        
        # Export to all callbacks
        for callback in self._export_callbacks:
            try:
                await callback(traces_to_export)
            except Exception as e:
                logger.error(f"Trace export callback failed: {e}")
    
    async def _flush_loop(self):
        """Background flush loop"""
        while True:
            try:
                await asyncio.sleep(self.flush_interval_seconds)
                await self._flush_buffer()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Trace export flush error: {e}")
    
    def to_json(self, trace: Trace) -> str:
        """Convert trace to JSON format"""
        return json.dumps(asdict(trace), default=str, indent=2)
    
    def to_opentelemetry(self, trace: Trace) -> Dict[str, Any]:
        """Convert trace to OpenTelemetry format"""
        return {
            "traceId": trace.trace_id,
            "spans": [
                {
                    "traceId": span.trace_id,
                    "spanId": span.span_id,
                    "parentSpanId": span.parent_span_id,
                    "name": span.name,
                    "kind": span.kind.value,
                    "startTime": int(span.start_time * 1_000_000_000),  # Convert to nanoseconds
                    "endTime": int((span.end_time or span.start_time) * 1_000_000_000),
                    "attributes": span.attributes,
                    "events": span.events,
                    "status": {
                        "code": 1 if span.status == SpanStatus.ERROR else 2,
                        "message": span.error_message or ""
                    }
                }
                for span in trace.spans
            ]
        }


# Global tracer and collector
_tracer: Optional[Tracer] = None
_trace_collector: Optional[TraceCollector] = None
_trace_exporter: Optional[TraceExporter] = None


def get_tracer(service_name: str = "webmcp") -> Tracer:
    """Get the global tracer"""
    global _tracer
    if _tracer is None:
        _tracer = Tracer(service_name)
    return _tracer


def get_trace_collector() -> TraceCollector:
    """Get the global trace collector"""
    global _trace_collector
    if _trace_collector is None:
        _trace_collector = TraceCollector()
    return _trace_collector


async def get_trace_exporter() -> TraceExporter:
    """Get the global trace exporter"""
    global _trace_exporter
    if _trace_exporter is None:
        _trace_exporter = TraceExporter()
        await _trace_exporter.start()
    return _trace_exporter


# Context manager for spans
class TraceSpan:
    """Context manager for automatic span management"""
    
    def __init__(
        self,
        name: str,
        service_name: Optional[str] = None,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.service_name = service_name
        self.kind = kind
        self.attributes = attributes
        self.tracer = get_tracer()
        self.span: Optional[Span] = None
    
    def __enter__(self) -> Span:
        self.span = self.tracer.start_span(
            self.name,
            kind=self.kind,
            attributes=self.attributes,
            service_name=self.service_name
        )
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_type:
                # Error occurred
                error_message = str(exc_val) if exc_val else str(exc_type)
                error_stack_trace = traceback.format_exc()
                self.tracer.end_span(
                    self.span.span_id,
                    status=SpanStatus.ERROR,
                    error_message=error_message,
                    error_stack_trace=error_stack_trace
                )
            else:
                # Success
                self.tracer.end_span(self.span.span_id, status=SpanStatus.OK)


# Decorator for automatic tracing
def trace_function(
    name: Optional[str] = None,
    service_name: Optional[str] = None,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[Dict[str, Any]] = None
):
    """Decorator to automatically trace function execution"""
    def decorator(func: Callable[..., Awaitable[Any]]):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            span_name = name or f"{func.__module__}.{func.__name__}"
            
            with TraceSpan(
                name=span_name,
                service_name=service_name,
                kind=kind,
                attributes=attributes
            ) as span:
                # Add function arguments as span attributes
                if span:
                    span.attributes.update({
                        "function.args_count": len(args),
                        "function.kwargs_count": len(kwargs),
                        "function.name": func.__name__,
                        "function.module": func.__module__
                    })
                
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Utility functions
def get_current_span() -> Optional[Span]:
    """Get the current active span from context"""
    tracer = get_tracer()
    context = tracer._span_context_var.get()
    if context:
        return tracer._active_spans.get(context.span_id)
    return None


def add_span_attribute(key: str, value: Any):
    """Add attribute to current span"""
    span = get_current_span()
    if span:
        tracer = get_tracer()
        tracer.add_span_attribute(span.span_id, key, value)


def add_span_event(name: str, attributes: Optional[Dict[str, Any]] = None):
    """Add event to current span"""
    span = get_current_span()
    if span:
        tracer = get_tracer()
        tracer.add_span_event(span.span_id, name, attributes)
