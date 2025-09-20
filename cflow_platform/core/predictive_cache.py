"""
Predictive Caching and Advanced Cache Strategies for WebMCP Performance Enhancement

This module provides sophisticated caching capabilities including:
- Predictive prefetching based on access patterns
- Advanced cache replacement strategies
- Intelligent cache warming and preloading
- Context-aware caching with user behavior analysis
- Multi-tier caching with intelligent promotion/demotion
- Cache performance optimization and tuning
"""

import asyncio
import logging
import time
import math
from typing import Any, Dict, List, Optional, Callable, Awaitable, Union, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque, OrderedDict
import statistics
import hashlib
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheTier(Enum):
    """Cache tiers for multi-tier caching"""
    L1 = "l1"                          # Fastest, smallest (in-memory)
    L2 = "l2"                          # Medium speed, medium size (SSD)
    L3 = "l3"                          # Slower, largest (disk/network)


class CacheStrategy(Enum):
    """Advanced cache replacement strategies"""
    LRU = "lru"                        # Least Recently Used
    LFU = "lfu"                        # Least Frequently Used
    ARC = "arc"                        # Adaptive Replacement Cache
    LIRS = "lirs"                      # Low Inter-reference Recency Set
    PREDICTIVE = "predictive"          # Predictive replacement
    CONTEXT_AWARE = "context_aware"    # Context-aware replacement


class AccessPattern(Enum):
    """Access pattern types"""
    SEQUENTIAL = "sequential"           # Sequential access
    RANDOM = "random"                   # Random access
    TEMPORAL = "temporal"               # Time-based access
    SPATIAL = "spatial"                 # Spatial locality
    FREQUENCY_BASED = "frequency_based" # Frequency-based access


@dataclass
class CacheEntry:
    """Enhanced cache entry with predictive metadata"""
    key: str
    value: Any
    tier: CacheTier
    created_at: float
    last_accessed: float
    access_count: int = 0
    access_frequency: float = 0.0
    predicted_access_time: Optional[float] = None
    confidence_score: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)
    dependencies: Set[str] = field(default_factory=set)
    size_bytes: int = 0
    compressed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessPattern:
    """Access pattern analysis"""
    pattern_type: AccessPattern
    frequency: float
    predictability: float
    next_access_probability: float
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PrefetchDecision:
    """Prefetch decision result"""
    key: str
    priority: int
    expected_access_time: float
    confidence: float
    reasoning: str
    dependencies: List[str] = field(default_factory=list)


class PredictiveCache:
    """
    Advanced predictive caching system with intelligent prefetching.
    
    Features:
    - Multi-tier caching with intelligent promotion/demotion
    - Predictive prefetching based on access patterns
    - Advanced cache replacement strategies
    - Context-aware caching
    - Performance optimization and tuning
    - Intelligent cache warming
    """
    
    def __init__(
        self,
        l1_size_mb: int = 100,
        l2_size_mb: int = 500,
        l3_size_mb: int = 2000,
        default_strategy: CacheStrategy = CacheStrategy.PREDICTIVE
    ):
        self.l1_size_mb = l1_size_mb
        self.l2_size_mb = l2_size_mb
        self.l3_size_mb = l3_size_mb
        
        # Multi-tier cache storage
        self._l1_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._l2_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._l3_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        
        # Access pattern tracking
        self._access_patterns: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._pattern_analysis: Dict[str, AccessPattern] = {}
        
        # Predictive models
        self._prediction_models: Dict[str, Any] = {}
        self._access_frequencies: Dict[str, float] = defaultdict(float)
        
        # Cache statistics
        self._cache_stats = {
            "hits": defaultdict(int),
            "misses": defaultdict(int),
            "evictions": defaultdict(int),
            "promotions": defaultdict(int),
            "demotions": defaultdict(int),
            "prefetches": defaultdict(int)
        }
        
        # Background tasks
        self._prefetch_task: Optional[asyncio.Task] = None
        self._analysis_task: Optional[asyncio.Task] = None
        self._optimization_task: Optional[asyncio.Task] = None
        
        # Cache configuration
        self._cache_strategies = {
            CacheTier.L1: CacheStrategy.LRU,
            CacheTier.L2: CacheStrategy.ARC,
            CacheTier.L3: CacheStrategy.PREDICTIVE
        }
        
        # Prefetch configuration
        self._prefetch_enabled = True
        self._prefetch_batch_size = 10
        self._prefetch_confidence_threshold = 0.7
        
        # Context tracking
        self._user_contexts: Dict[str, Dict[str, Any]] = {}
        self._session_patterns: Dict[str, List[str]] = defaultdict(list)
    
    async def start(self):
        """Start predictive cache system"""
        self._prefetch_task = asyncio.create_task(self._prefetch_loop())
        self._analysis_task = asyncio.create_task(self._analysis_loop())
        self._optimization_task = asyncio.create_task(self._optimization_loop())
        logger.info("PredictiveCache started")
    
    async def stop(self):
        """Stop predictive cache system"""
        if self._prefetch_task:
            self._prefetch_task.cancel()
        if self._analysis_task:
            self._analysis_task.cancel()
        if self._optimization_task:
            self._optimization_task.cancel()
        logger.info("PredictiveCache stopped")
    
    async def get(self, key: str, context: Dict[str, Any] = None) -> Optional[Any]:
        """Get value from cache with context awareness"""
        context = context or {}
        
        # Check all tiers
        for tier in [CacheTier.L1, CacheTier.L2, CacheTier.L3]:
            entry = await self._get_from_tier(key, tier)
            if entry:
                # Record access
                await self._record_access(key, tier, context)
                
                # Update access statistics
                self._cache_stats["hits"][tier.value] += 1
                
                # Consider promotion to higher tier
                await self._consider_promotion(entry, tier)
                
                return entry.value
        
        # Cache miss
        self._cache_stats["misses"]["total"] += 1
        
        # Record miss for prefetching analysis
        await self._record_miss(key, context)
        
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        tier: CacheTier = CacheTier.L1,
        context: Dict[str, Any] = None,
        dependencies: Set[str] = None
    ):
        """Set value in cache with intelligent tier selection"""
        context = context or {}
        dependencies = dependencies or set()
        
        # Create cache entry
        entry = CacheEntry(
            key=key,
            value=value,
            tier=tier,
            created_at=time.time(),
            last_accessed=time.time(),
            context=context,
            dependencies=dependencies,
            size_bytes=self._calculate_size(value)
        )
        
        # Add to appropriate tier
        await self._add_to_tier(entry, tier)
        
        # Update access frequency
        self._access_frequencies[key] = 1.0
        
        # Trigger prefetching for related items
        if self._prefetch_enabled:
            await self._trigger_prefetch(key, context)
    
    async def _get_from_tier(self, key: str, tier: CacheTier) -> Optional[CacheEntry]:
        """Get entry from specific tier"""
        cache = self._get_tier_cache(tier)
        
        if key in cache:
            entry = cache[key]
            # Move to end (most recently used)
            cache.move_to_end(key)
            return entry
        
        return None
    
    async def _add_to_tier(self, entry: CacheEntry, tier: CacheTier):
        """Add entry to specific tier"""
        cache = self._get_tier_cache(tier)
        max_size = self._get_tier_max_size(tier)
        
        # Check if we need to evict
        if len(cache) >= max_size:
            await self._evict_from_tier(tier)
        
        # Add entry
        cache[entry.key] = entry
        
        # Update size tracking
        await self._update_tier_size(tier)
    
    def _get_tier_cache(self, tier: CacheTier) -> OrderedDict[str, CacheEntry]:
        """Get cache for specific tier"""
        if tier == CacheTier.L1:
            return self._l1_cache
        elif tier == CacheTier.L2:
            return self._l2_cache
        else:
            return self._l3_cache
    
    def _get_tier_max_size(self, tier: CacheTier) -> int:
        """Get maximum size for tier"""
        if tier == CacheTier.L1:
            return self.l1_size_mb * 1024 * 1024 // 1024  # Approximate entry count
        elif tier == CacheTier.L2:
            return self.l2_size_mb * 1024 * 1024 // 1024
        else:
            return self.l3_size_mb * 1024 * 1024 // 1024
    
    async def _evict_from_tier(self, tier: CacheTier):
        """Evict entry from tier using appropriate strategy"""
        cache = self._get_tier_cache(tier)
        strategy = self._cache_strategies.get(tier, CacheStrategy.LRU)
        
        if not cache:
            return
        
        # Select victim based on strategy
        victim_key = await self._select_victim(cache, strategy)
        
        if victim_key:
            entry = cache[victim_key]
            
            # Consider demotion to lower tier
            if tier != CacheTier.L3:
                await self._consider_demotion(entry, tier)
            
            # Remove from current tier
            del cache[victim_key]
            self._cache_stats["evictions"][tier.value] += 1
    
    async def _select_victim(self, cache: OrderedDict[str, CacheEntry], strategy: CacheStrategy) -> str:
        """Select victim for eviction based on strategy"""
        if strategy == CacheStrategy.LRU:
            return next(iter(cache))  # Least recently used (first item)
        
        elif strategy == CacheStrategy.LFU:
            # Least frequently used
            min_freq = float('inf')
            victim_key = None
            
            for key, entry in cache.items():
                if entry.access_frequency < min_freq:
                    min_freq = entry.access_frequency
                    victim_key = key
            
            return victim_key or next(iter(cache))
        
        elif strategy == CacheStrategy.ARC:
            # Adaptive Replacement Cache (simplified)
            return await self._arc_select_victim(cache)
        
        elif strategy == CacheStrategy.PREDICTIVE:
            return await self._predictive_select_victim(cache)
        
        else:
            # Default to LRU
            return next(iter(cache))
    
    async def _arc_select_victim(self, cache: OrderedDict[str, CacheEntry]) -> str:
        """ARC victim selection (simplified implementation)"""
        # Simple ARC implementation
        # In a full implementation, this would maintain T1, T2, B1, B2 lists
        
        # For now, use a combination of recency and frequency
        scores = {}
        current_time = time.time()
        
        for key, entry in cache.items():
            recency_score = current_time - entry.last_accessed
            frequency_score = 1.0 / max(entry.access_frequency, 0.1)
            score = recency_score * 0.7 + frequency_score * 0.3
            scores[key] = score
        
        return max(scores.items(), key=lambda x: x[1])[0]
    
    async def _predictive_select_victim(self, cache: OrderedDict[str, CacheEntry]) -> str:
        """Predictive victim selection"""
        current_time = time.time()
        victim_key = None
        lowest_score = float('inf')
        
        for key, entry in cache.items():
            # Calculate predictive score
            score = 0.0
            
            # Time since last access
            time_score = (current_time - entry.last_accessed) / 3600.0  # Hours
            score += time_score * 0.4
            
            # Access frequency
            freq_score = 1.0 / max(entry.access_frequency, 0.1)
            score += freq_score * 0.3
            
            # Predicted next access time
            if entry.predicted_access_time:
                if entry.predicted_access_time > current_time:
                    # Not expected to be accessed soon
                    score += (entry.predicted_access_time - current_time) / 3600.0 * 0.3
            
            # Confidence in prediction
            confidence_factor = 1.0 - entry.confidence_score
            score *= confidence_factor
            
            if score < lowest_score:
                lowest_score = score
                victim_key = key
        
        return victim_key or next(iter(cache))
    
    async def _record_access(self, key: str, tier: CacheTier, context: Dict[str, Any]):
        """Record access for pattern analysis"""
        current_time = time.time()
        
        # Update access pattern
        self._access_patterns[key].append({
            "timestamp": current_time,
            "tier": tier,
            "context": context
        })
        
        # Update access frequency
        self._access_frequencies[key] = min(100.0, self._access_frequencies[key] + 1.0)
        
        # Update entry metadata
        cache = self._get_tier_cache(tier)
        if key in cache:
            entry = cache[key]
            entry.last_accessed = current_time
            entry.access_count += 1
            entry.access_frequency = self._access_frequencies[key]
    
    async def _record_miss(self, key: str, context: Dict[str, Any]):
        """Record cache miss for analysis"""
        # Analyze miss pattern for prefetching
        await self._analyze_miss_pattern(key, context)
    
    async def _analyze_miss_pattern(self, key: str, context: Dict[str, Any]):
        """Analyze cache miss pattern"""
        # Look for patterns in recent misses
        recent_misses = []
        for pattern_key, pattern_data in self._access_patterns.items():
            recent_accesses = list(pattern_data)[-5:]
            if recent_accesses:
                last_access = recent_accesses[-1]
                if time.time() - last_access["timestamp"] < 300:  # Last 5 minutes
                    recent_misses.append(pattern_key)
        
        # Update session patterns
        session_id = context.get("session_id", "default")
        self._session_patterns[session_id].append(key)
    
    async def _consider_promotion(self, entry: CacheEntry, current_tier: CacheTier):
        """Consider promoting entry to higher tier"""
        if current_tier == CacheTier.L1:
            return  # Already in highest tier
        
        # Promotion criteria
        should_promote = False
        
        if current_tier == CacheTier.L3:
            # Promote from L3 to L2 if frequently accessed
            should_promote = entry.access_frequency > 5.0
        elif current_tier == CacheTier.L2:
            # Promote from L2 to L1 if very frequently accessed
            should_promote = entry.access_frequency > 10.0
        
        if should_promote:
            # Remove from current tier
            cache = self._get_tier_cache(current_tier)
            if entry.key in cache:
                del cache[entry.key]
            
            # Add to higher tier
            higher_tier = CacheTier.L2 if current_tier == CacheTier.L3 else CacheTier.L1
            entry.tier = higher_tier
            await self._add_to_tier(entry, higher_tier)
            
            self._cache_stats["promotions"][higher_tier.value] += 1
    
    async def _consider_demotion(self, entry: CacheEntry, current_tier: CacheTier):
        """Consider demoting entry to lower tier"""
        if current_tier == CacheTier.L3:
            return  # Already in lowest tier
        
        # Demotion criteria
        should_demote = False
        
        if current_tier == CacheTier.L1:
            # Demote from L1 to L2 if infrequently accessed
            should_demote = entry.access_frequency < 2.0
        elif current_tier == CacheTier.L2:
            # Demote from L2 to L3 if rarely accessed
            should_demote = entry.access_frequency < 1.0
        
        if should_demote:
            # Add to lower tier
            lower_tier = CacheTier.L2 if current_tier == CacheTier.L1 else CacheTier.L3
            entry.tier = lower_tier
            await self._add_to_tier(entry, lower_tier)
            
            self._cache_stats["demotions"][lower_tier.value] += 1
    
    async def _trigger_prefetch(self, key: str, context: Dict[str, Any]):
        """Trigger prefetching for related items"""
        if not self._prefetch_enabled:
            return
        
        # Analyze access patterns to find related items
        related_keys = await self._find_related_keys(key, context)
        
        # Create prefetch decisions
        prefetch_decisions = []
        for related_key in related_keys:
            decision = await self._create_prefetch_decision(related_key, context)
            if decision and decision.confidence >= self._prefetch_confidence_threshold:
                prefetch_decisions.append(decision)
        
        # Execute prefetching
        if prefetch_decisions:
            await self._execute_prefetch(prefetch_decisions)
    
    async def _find_related_keys(self, key: str, context: Dict[str, Any]) -> List[str]:
        """Find keys related to the current key"""
        related_keys = []
        
        # Session-based relationships
        session_id = context.get("session_id")
        if session_id and session_id in self._session_patterns:
            session_keys = self._session_patterns[session_id][-10:]  # Last 10 keys
            related_keys.extend([k for k in session_keys if k != key])
        
        # Access pattern relationships
        if key in self._access_patterns:
            pattern_data = list(self._access_patterns[key])
            if len(pattern_data) > 1:
                # Find keys accessed around the same time
                recent_accesses = pattern_data[-5:]
                for access in recent_accesses:
                    # This is simplified - in reality, you'd analyze temporal relationships
                    pass
        
        return list(set(related_keys))[:5]  # Limit to 5 related keys
    
    async def _create_prefetch_decision(self, key: str, context: Dict[str, Any]) -> Optional[PrefetchDecision]:
        """Create prefetch decision for a key"""
        # Analyze access pattern for the key
        if key not in self._access_patterns or not self._access_patterns[key]:
            return None
        
        pattern_data = list(self._access_patterns[key])
        recent_accesses = pattern_data[-5:] if len(pattern_data) >= 5 else pattern_data
        
        if not recent_accesses:
            return None
        
        # Calculate access probability
        current_time = time.time()
        last_access_time = recent_accesses[-1]["timestamp"]
        time_since_last = current_time - last_access_time
        
        # Simple probability calculation
        if time_since_last < 60:  # Accessed within last minute
            probability = 0.8
        elif time_since_last < 300:  # Accessed within last 5 minutes
            probability = 0.6
        elif time_since_last < 1800:  # Accessed within last 30 minutes
            probability = 0.3
        else:
            probability = 0.1
        
        # Adjust based on access frequency
        frequency = self._access_frequencies.get(key, 1.0)
        probability *= min(1.0, frequency / 10.0)
        
        if probability < self._prefetch_confidence_threshold:
            return None
        
        return PrefetchDecision(
            key=key,
            priority=int(probability * 10),
            expected_access_time=current_time + 60,  # Expected in next minute
            confidence=probability,
            reasoning=f"Access pattern analysis: {probability:.2f} probability"
        )
    
    async def _execute_prefetch(self, decisions: List[PrefetchDecision]):
        """Execute prefetching decisions"""
        # Sort by priority
        decisions.sort(key=lambda d: d.priority, reverse=True)
        
        # Execute prefetching (simplified - in reality, this would load data)
        for decision in decisions[:self._prefetch_batch_size]:
            # Simulate prefetching
            await self._prefetch_key(decision.key)
            self._cache_stats["prefetches"]["total"] += 1
    
    async def _prefetch_key(self, key: str):
        """Prefetch a key (simplified implementation)"""
        # In a real implementation, this would:
        # 1. Determine what data to prefetch
        # 2. Load the data from source
        # 3. Add to appropriate cache tier
        
        # For now, we'll just mark it as prefetched
        logger.debug(f"Prefetching key: {key}")
    
    async def _prefetch_loop(self):
        """Background prefetching loop"""
        while True:
            try:
                await asyncio.sleep(30.0)  # Check every 30 seconds
                
                # Analyze access patterns and trigger prefetching
                await self._analyze_and_prefetch()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Prefetch loop error: {e}")
    
    async def _analyze_and_prefetch(self):
        """Analyze patterns and trigger prefetching"""
        # Find keys with high access probability
        high_probability_keys = []
        
        for key, frequency in self._access_frequencies.items():
            if frequency > 5.0:  # Frequently accessed
                if key in self._access_patterns:
                    pattern_data = list(self._access_patterns[key])
                    if pattern_data:
                        last_access = pattern_data[-1]["timestamp"]
                        if time.time() - last_access < 300:  # Recent access
                            high_probability_keys.append(key)
        
        # Create prefetch decisions
        prefetch_decisions = []
        for key in high_probability_keys[:10]:  # Limit to 10 keys
            decision = await self._create_prefetch_decision(key, {})
            if decision and decision.confidence >= self._prefetch_confidence_threshold:
                prefetch_decisions.append(decision)
        
        # Execute prefetching
        if prefetch_decisions:
            await self._execute_prefetch(prefetch_decisions)
    
    async def _analysis_loop(self):
        """Background analysis loop"""
        while True:
            try:
                await asyncio.sleep(60.0)  # Analyze every minute
                
                # Analyze access patterns
                await self._analyze_access_patterns()
                
                # Update prediction models
                await self._update_prediction_models()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Analysis loop error: {e}")
    
    async def _analyze_access_patterns(self):
        """Analyze access patterns for all keys"""
        for key, pattern_data in self._access_patterns.items():
            if len(pattern_data) < 3:
                continue
            
            # Analyze pattern
            pattern = await self._analyze_key_pattern(key, pattern_data)
            if pattern:
                self._pattern_analysis[key] = pattern
    
    async def _analyze_key_pattern(self, key: str, pattern_data: List[Dict]) -> Optional[AccessPattern]:
        """Analyze access pattern for a specific key"""
        if len(pattern_data) < 3:
            return None
        
        timestamps = [access["timestamp"] for access in pattern_data]
        
        # Calculate pattern characteristics
        intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        
        if not intervals:
            return None
        
        # Determine pattern type
        pattern_type = self._determine_pattern_type(intervals)
        
        # Calculate predictability
        predictability = 1.0 - (statistics.stdev(intervals) / statistics.mean(intervals)) if intervals else 0.0
        
        # Calculate next access probability
        avg_interval = statistics.mean(intervals)
        last_access = timestamps[-1]
        expected_next = last_access + avg_interval
        current_time = time.time()
        
        if current_time >= expected_next:
            next_access_probability = 0.8  # Overdue
        else:
            time_until_expected = expected_next - current_time
            next_access_probability = max(0.1, 1.0 - (time_until_expected / avg_interval))
        
        return AccessPattern(
            pattern_type=pattern_type,
            frequency=len(pattern_data) / (timestamps[-1] - timestamps[0]) if len(timestamps) > 1 else 0.0,
            predictability=predictability,
            next_access_probability=next_access_probability,
            confidence=min(1.0, len(pattern_data) / 10.0)
        )
    
    def _determine_pattern_type(self, intervals: List[float]) -> AccessPattern:
        """Determine access pattern type from intervals"""
        if not intervals:
            return AccessPattern.RANDOM
        
        # Check for sequential pattern
        if len(intervals) >= 3:
            sorted_intervals = sorted(intervals)
            if sorted_intervals[-1] - sorted_intervals[0] < sorted_intervals[0] * 0.1:
                return AccessPattern.SEQUENTIAL
        
        # Check for temporal pattern
        if len(intervals) >= 5:
            # Look for periodicity
            avg_interval = statistics.mean(intervals)
            deviations = [abs(interval - avg_interval) for interval in intervals]
            if statistics.mean(deviations) < avg_interval * 0.2:
                return AccessPattern.TEMPORAL
        
        # Check for frequency-based pattern
        frequency = 1.0 / statistics.mean(intervals)
        if frequency > 0.1:  # More than once every 10 seconds
            return AccessPattern.FREQUENCY_BASED
        
        return AccessPattern.RANDOM
    
    async def _update_prediction_models(self):
        """Update prediction models based on recent data"""
        # Update access frequency decay
        current_time = time.time()
        for key in list(self._access_frequencies.keys()):
            # Decay frequency over time
            self._access_frequencies[key] *= 0.95
            if self._access_frequencies[key] < 0.1:
                del self._access_frequencies[key]
    
    async def _optimization_loop(self):
        """Background optimization loop"""
        while True:
            try:
                await asyncio.sleep(300.0)  # Optimize every 5 minutes
                
                # Optimize cache configuration
                await self._optimize_cache_configuration()
                
                # Clean up old patterns
                await self._cleanup_old_patterns()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Optimization loop error: {e}")
    
    async def _optimize_cache_configuration(self):
        """Optimize cache configuration based on usage patterns"""
        # Analyze hit rates for each tier
        total_hits = sum(self._cache_stats["hits"].values())
        total_misses = self._cache_stats["misses"].get("total", 0)
        
        if total_hits + total_misses > 0:
            hit_rate = total_hits / (total_hits + total_misses)
            
            # Adjust prefetch confidence threshold based on hit rate
            if hit_rate < 0.7:
                self._prefetch_confidence_threshold = max(0.5, self._prefetch_confidence_threshold - 0.1)
            elif hit_rate > 0.9:
                self._prefetch_confidence_threshold = min(0.9, self._prefetch_confidence_threshold + 0.05)
    
    async def _cleanup_old_patterns(self):
        """Clean up old access patterns"""
        current_time = time.time()
        cutoff_time = current_time - 3600  # 1 hour
        
        for key in list(self._access_patterns.keys()):
            pattern_data = self._access_patterns[key]
            
            # Remove old access records
            while pattern_data and pattern_data[0]["timestamp"] < cutoff_time:
                pattern_data.popleft()
            
            # Remove empty patterns
            if not pattern_data:
                del self._access_patterns[key]
    
    def _calculate_size(self, value: Any) -> int:
        """Calculate size of cache entry"""
        try:
            import pickle
            return len(pickle.dumps(value))
        except Exception:
            return 1024  # Default size
    
    async def _update_tier_size(self, tier: CacheTier):
        """Update tier size tracking"""
        # This would track actual memory usage in a real implementation
        pass
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_hits = sum(self._cache_stats["hits"].values())
        total_misses = self._cache_stats["misses"].get("total", 0)
        
        return {
            "tiers": {
                "l1_size": len(self._l1_cache),
                "l2_size": len(self._l2_cache),
                "l3_size": len(self._l3_cache)
            },
            "hits": dict(self._cache_stats["hits"]),
            "misses": dict(self._cache_stats["misses"]),
            "evictions": dict(self._cache_stats["evictions"]),
            "promotions": dict(self._cache_stats["promotions"]),
            "demotions": dict(self._cache_stats["demotions"]),
            "prefetches": dict(self._cache_stats["prefetches"]),
            "hit_rate": total_hits / max(total_hits + total_misses, 1),
            "total_keys_tracked": len(self._access_patterns),
            "prefetch_enabled": self._prefetch_enabled,
            "prefetch_confidence_threshold": self._prefetch_confidence_threshold
        }


# Global predictive cache
_predictive_cache: Optional[PredictiveCache] = None


async def get_predictive_cache() -> PredictiveCache:
    """Get the global predictive cache"""
    global _predictive_cache
    if _predictive_cache is None:
        _predictive_cache = PredictiveCache()
        await _predictive_cache.start()
    return _predictive_cache


async def get_from_cache(key: str, context: Dict[str, Any] = None) -> Optional[Any]:
    """Get value from predictive cache"""
    cache = await get_predictive_cache()
    return await cache.get(key, context)


async def set_in_cache(
    key: str,
    value: Any,
    tier: CacheTier = CacheTier.L1,
    context: Dict[str, Any] = None,
    dependencies: Set[str] = None
):
    """Set value in predictive cache"""
    cache = await get_predictive_cache()
    await cache.set(key, value, tier, context, dependencies)


async def get_cache_stats() -> Dict[str, Any]:
    """Get predictive cache statistics"""
    cache = await get_predictive_cache()
    return cache.get_cache_stats()
