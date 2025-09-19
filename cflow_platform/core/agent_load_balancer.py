"""
BMAD Agent Load Balancer

Phase 3.4: Dynamic agent resource allocation system.
"""

import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")


class AgentState(Enum):
    """Agent state enumeration."""
    IDLE = "idle"
    BUSY = "busy"
    OVERLOADED = "overloaded"
    ERROR = "error"
    OFFLINE = "offline"


class LoadBalancingStrategy(Enum):
    """Load balancing strategies."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_RESPONSE_TIME = "least_response_time"
    RESOURCE_BASED = "resource_based"


@dataclass
class AgentMetrics:
    """Agent performance metrics."""
    agent_id: str = ""
    agent_type: str = ""
    state: AgentState = AgentState.IDLE
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_response_time: float = 0.0
    last_heartbeat: datetime = None
    total_uptime: float = 0.0
    error_rate: float = 0.0

    def __post_init__(self):
        if self.last_heartbeat is None:
            self.last_heartbeat = datetime.utcnow()


@dataclass
class LoadBalancingDecision:
    """Load balancing decision result."""
    agent_id: str
    agent_type: str
    confidence: float
    reasoning: str
    estimated_wait_time: float
    resource_availability: Dict[str, float]


class BMADAgentLoadBalancer:
    """Dynamic agent load balancing system for BMAD."""
    
    def __init__(self):
        self.supabase_client = None
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        self.agent_weights: Dict[str, float] = {}
        self.load_balancing_strategy = LoadBalancingStrategy.RESOURCE_BASED
        self.max_cpu_threshold = 80.0
        self.max_memory_threshold = 85.0
        self.max_response_time_threshold = 5.0
        self.heartbeat_timeout = 30.0
        self.metrics_history: List[AgentMetrics] = []
        self.decision_history: List[LoadBalancingDecision] = []
        self._ensure_supabase()
    
    def _ensure_supabase(self) -> None:
        """Create Supabase client."""
        try:
            from supabase import create_client
            from .config.supabase_config import get_api_key, get_rest_url
            
            url = get_rest_url()
            key = get_api_key(secure=True)
            
            if url and key:
                self.supabase_client = create_client(url, key)
                print("[INFO] Load Balancer: Supabase client created")
            else:
                print("[INFO][INFO] Load Balancer: Supabase not available")
                
        except Exception as e:
            print(f"[INFO][INFO] Load Balancer: Supabase setup failed: {e}")
    
    def register_agent(self, agent_id: str, agent_type: str, initial_weight: float = 1.0) -> bool:
        """Register a new agent for load balancing."""
        try:
            metrics = AgentMetrics(
                agent_id=agent_id,
                agent_type=agent_type,
                state=AgentState.IDLE,
                cpu_usage=0.0,
                memory_usage=0.0,
                active_tasks=0,
                completed_tasks=0,
                failed_tasks=0,
                average_response_time=0.0,
                total_uptime=0.0,
                error_rate=0.0
            )
            
            self.agent_metrics[agent_id] = metrics
            self.agent_weights[agent_id] = initial_weight
            
            print(f"[INFO] Load Balancer: Registered agent {agent_id} ({agent_type}) with weight {initial_weight}")
            return True
            
        except Exception as e:
            print(f"[INFO] Load Balancer: Failed to register agent: {e}")
            return False
    
    def update_agent_metrics(self, agent_id: str, metrics_data: Dict[str, Any]) -> bool:
        """Update agent performance metrics."""
        try:
            if agent_id not in self.agent_metrics:
                print(f"[INFO] Load Balancer: Agent {agent_id} not registered")
                return False
            
            metrics = self.agent_metrics[agent_id]
            
            # Update metrics
            metrics.cpu_usage = metrics_data.get("cpu_usage", metrics.cpu_usage)
            metrics.memory_usage = metrics_data.get("memory_usage", metrics.memory_usage)
            metrics.active_tasks = metrics_data.get("active_tasks", metrics.active_tasks)
            metrics.completed_tasks = metrics_data.get("completed_tasks", metrics.completed_tasks)
            metrics.failed_tasks = metrics_data.get("failed_tasks", metrics.failed_tasks)
            metrics.average_response_time = metrics_data.get("average_response_time", metrics.average_response_time)
            metrics.last_heartbeat = datetime.utcnow()
            
            # Calculate error rate
            total_tasks = metrics.completed_tasks + metrics.failed_tasks
            if total_tasks > 0:
                metrics.error_rate = (metrics.failed_tasks / total_tasks) * 100
            
            # Determine agent state
            metrics.state = self._determine_agent_state(metrics)
            
            # Store in history
            self.metrics_history.append(metrics)
            
            # Keep only last 1000 metrics
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]
            
            print(f"[INFO] Load Balancer: Updated metrics for agent {agent_id}")
            return True
            
        except Exception as e:
            print(f"[INFO] Load Balancer: Failed to update metrics: {e}")
            return False
    
    def _determine_agent_state(self, metrics: AgentMetrics) -> AgentState:
        """Determine agent state based on metrics."""
        try:
            # Check if agent is offline (no heartbeat)
            if (datetime.utcnow() - metrics.last_heartbeat).total_seconds() > self.heartbeat_timeout:
                return AgentState.OFFLINE
            
            # Check for errors
            if metrics.error_rate > 20.0:  # 20% error rate threshold
                return AgentState.ERROR
            
            # Check for overload
            if (metrics.cpu_usage > self.max_cpu_threshold or 
                metrics.memory_usage > self.max_memory_threshold or
                metrics.average_response_time > self.max_response_time_threshold):
                return AgentState.OVERLOADED
            
            # Check if busy
            if metrics.active_tasks > 0:
                return AgentState.BUSY
            
            return AgentState.IDLE
            
        except Exception as e:
            print(f"[INFO] Load Balancer: Failed to determine agent state: {e}")
            return AgentState.ERROR
    
    def select_agent(self, agent_type: str, task_complexity: str = "normal") -> LoadBalancingDecision:
        """Select the best agent for a task using load balancing strategy."""
        try:
            # Filter agents by type and availability
            available_agents = [
                metrics for metrics in self.agent_metrics.values()
                if (metrics.agent_type == agent_type and 
                    metrics.state in [AgentState.IDLE, AgentState.BUSY])
            ]
            
            if not available_agents:
                return LoadBalancingDecision(
                    agent_id="",
                    agent_type=agent_type,
                    confidence=0.0,
                    reasoning="No available agents found",
                    estimated_wait_time=float('inf'),
                    resource_availability={}
                )
            
            # Apply load balancing strategy
            if self.load_balancing_strategy == LoadBalancingStrategy.ROUND_ROBIN:
                selected_agent = self._round_robin_selection(available_agents)
            elif self.load_balancing_strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
                selected_agent = self._least_connections_selection(available_agents)
            elif self.load_balancing_strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
                selected_agent = self._weighted_round_robin_selection(available_agents)
            elif self.load_balancing_strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
                selected_agent = self._least_response_time_selection(available_agents)
            else:  # RESOURCE_BASED
                selected_agent = self._resource_based_selection(available_agents, task_complexity)
            
            # Calculate decision metrics
            confidence = self._calculate_confidence(selected_agent, task_complexity)
            wait_time = self._estimate_wait_time(selected_agent)
            resource_availability = self._calculate_resource_availability(selected_agent)
            
            decision = LoadBalancingDecision(
                agent_id=selected_agent.agent_id,
                agent_type=agent_type,
                confidence=confidence,
                reasoning=f"Selected using {self.load_balancing_strategy.value} strategy",
                estimated_wait_time=wait_time,
                resource_availability=resource_availability
            )
            
            # Store decision
            self.decision_history.append(decision)
            
            print(f"[INFO] Load Balancer: Selected agent {selected_agent.agent_id} with confidence {confidence:.2f}")
            return decision
            
        except Exception as e:
            print(f"[INFO] Load Balancer: Agent selection failed: {e}")
            return LoadBalancingDecision(
                agent_id="",
                agent_type=agent_type,
                confidence=0.0,
                reasoning=f"Selection failed: {e}",
                estimated_wait_time=float('inf'),
                resource_availability={}
            )
    
    def _round_robin_selection(self, agents: List[AgentMetrics]) -> AgentMetrics:
        """Round robin agent selection."""
        # Simple round robin - select first available agent
        return agents[0]
    
    def _least_connections_selection(self, agents: List[AgentMetrics]) -> AgentMetrics:
        """Select agent with least active connections."""
        return min(agents, key=lambda a: a.active_tasks)
    
    def _weighted_round_robin_selection(self, agents: List[AgentMetrics]) -> AgentMetrics:
        """Weighted round robin selection."""
        # Select agent with highest weight and lowest load
        best_agent = None
        best_score = -1
        
        for agent in agents:
            weight = self.agent_weights.get(agent.agent_id, 1.0)
            load_factor = (agent.cpu_usage + agent.memory_usage) / 200.0  # Normalize to 0-1
            score = weight / (1.0 + load_factor)
            
            if score > best_score:
                best_score = score
                best_agent = agent
        
        return best_agent or agents[0]
    
    def _least_response_time_selection(self, agents: List[AgentMetrics]) -> AgentMetrics:
        """Select agent with least response time."""
        return min(agents, key=lambda a: a.average_response_time)
    
    def _resource_based_selection(self, agents: List[AgentMetrics], task_complexity: str) -> AgentMetrics:
        """Resource-based agent selection."""
        best_agent = None
        best_score = -1
        
        for agent in agents:
            # Calculate resource score
            cpu_score = max(0, 100 - agent.cpu_usage) / 100.0
            memory_score = max(0, 100 - agent.memory_usage) / 100.0
            response_score = max(0, 10 - agent.average_response_time) / 10.0
            error_score = max(0, 100 - agent.error_rate) / 100.0
            
            # Weight based on task complexity
            complexity_weight = {"low": 0.8, "normal": 1.0, "high": 1.2}.get(task_complexity, 1.0)
            
            # Calculate overall score
            score = (cpu_score * 0.3 + memory_score * 0.3 + response_score * 0.2 + error_score * 0.2) * complexity_weight
            
            if score > best_score:
                best_score = score
                best_agent = agent
        
        return best_agent or agents[0]
    
    def _calculate_confidence(self, agent: AgentMetrics, task_complexity: str) -> float:
        """Calculate confidence in agent selection."""
        try:
            # Base confidence on agent health
            cpu_health = max(0, 100 - agent.cpu_usage) / 100.0
            memory_health = max(0, 100 - agent.memory_usage) / 100.0
            response_health = max(0, 10 - agent.average_response_time) / 10.0
            error_health = max(0, 100 - agent.error_rate) / 100.0
            
            # Weight by task complexity
            complexity_factor = {"low": 1.0, "normal": 0.9, "high": 0.8}.get(task_complexity, 0.9)
            
            confidence = (cpu_health * 0.25 + memory_health * 0.25 + 
                         response_health * 0.25 + error_health * 0.25) * complexity_factor
            
            return min(1.0, max(0.0, confidence))
            
        except Exception as e:
            print(f"[INFO] Load Balancer: Confidence calculation failed: {e}")
            return 0.5
    
    def _estimate_wait_time(self, agent: AgentMetrics) -> float:
        """Estimate wait time for agent."""
        try:
            # Base wait time on current load
            base_wait = agent.active_tasks * 2.0  # 2 seconds per active task
            
            # Adjust for response time
            response_adjustment = agent.average_response_time * 0.5
            
            # Adjust for resource usage
            resource_adjustment = (agent.cpu_usage + agent.memory_usage) / 100.0 * 5.0
            
            total_wait = base_wait + response_adjustment + resource_adjustment
            return max(0.0, total_wait)
            
        except Exception as e:
            print(f"[INFO] Load Balancer: Wait time estimation failed: {e}")
            return 5.0
    
    def _calculate_resource_availability(self, agent: AgentMetrics) -> Dict[str, float]:
        """Calculate resource availability for agent."""
        return {
            "cpu_available": max(0, 100 - agent.cpu_usage),
            "memory_available": max(0, 100 - agent.memory_usage),
            "response_capacity": max(0, 10 - agent.average_response_time),
            "error_tolerance": max(0, 100 - agent.error_rate)
        }
    
    def get_load_balancing_status(self) -> Dict[str, Any]:
        """Get load balancer status."""
        try:
            total_agents = len(self.agent_metrics)
            idle_agents = len([m for m in self.agent_metrics.values() if m.state == AgentState.IDLE])
            busy_agents = len([m for m in self.agent_metrics.values() if m.state == AgentState.BUSY])
            overloaded_agents = len([m for m in self.agent_metrics.values() if m.state == AgentState.OVERLOADED])
            error_agents = len([m for m in self.agent_metrics.values() if m.state == AgentState.ERROR])
            offline_agents = len([m for m in self.agent_metrics.values() if m.state == AgentState.OFFLINE])
            
            return {
                "total_agents": total_agents,
                "idle_agents": idle_agents,
                "busy_agents": busy_agents,
                "overloaded_agents": overloaded_agents,
                "error_agents": error_agents,
                "offline_agents": offline_agents,
                "strategy": self.load_balancing_strategy.value,
                "metrics_history_size": len(self.metrics_history),
                "decision_history_size": len(self.decision_history),
                "status": "operational"
            }
            
        except Exception as e:
            print(f"[INFO] Load Balancer: Status calculation failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def set_load_balancing_strategy(self, strategy: LoadBalancingStrategy) -> bool:
        """Set the load balancing strategy."""
        try:
            self.load_balancing_strategy = strategy
            print(f"[INFO] Load Balancer: Strategy changed to {strategy.value}")
            return True
            
        except Exception as e:
            print(f"[INFO] Load Balancer: Failed to set strategy: {e}")
            return False
    
    async def monitor_agents(self) -> None:
        """Monitor agent health and performance."""
        try:
            print("[INFO] Load Balancer: Starting agent monitoring...")
            
            while True:
                # Check for offline agents
                current_time = datetime.utcnow()
                for agent_id, metrics in self.agent_metrics.items():
                    if (current_time - metrics.last_heartbeat).total_seconds() > self.heartbeat_timeout:
                        if metrics.state != AgentState.OFFLINE:
                            print(f"[INFO][INFO] Load Balancer: Agent {agent_id} marked as offline")
                            metrics.state = AgentState.OFFLINE
                
                # Update agent weights based on performance
                for agent_id, metrics in self.agent_metrics.items():
                    if metrics.state == AgentState.IDLE:
                        # Increase weight for idle agents
                        self.agent_weights[agent_id] = min(2.0, self.agent_weights.get(agent_id, 1.0) + 0.1)
                    elif metrics.state == AgentState.OVERLOADED:
                        # Decrease weight for overloaded agents
                        self.agent_weights[agent_id] = max(0.1, self.agent_weights.get(agent_id, 1.0) - 0.1)
                
                await asyncio.sleep(10)  # Monitor every 10 seconds
                
        except Exception as e:
            print(f"[INFO] Load Balancer: Agent monitoring failed: {e}")


# Global load balancer instance
agent_load_balancer = BMADAgentLoadBalancer()


def get_agent_load_balancer() -> BMADAgentLoadBalancer:
    """Get global agent load balancer instance."""
    return agent_load_balancer


# Test function
async def test_agent_load_balancer():
    """Test agent load balancer."""
    print("[INFO] Load Balancer: Testing Agent Load Balancer...")
    
    balancer = get_agent_load_balancer()
    
    # Register test agents
    balancer.register_agent("analyst_1", "analyst", 1.0)
    balancer.register_agent("analyst_2", "analyst", 1.2)
    balancer.register_agent("pm_1", "pm", 1.0)
    balancer.register_agent("architect_1", "architect", 1.5)
    
    # Update metrics for agents
    balancer.update_agent_metrics("analyst_1", {
        "cpu_usage": 30.0,
        "memory_usage": 40.0,
        "active_tasks": 1,
        "completed_tasks": 10,
        "failed_tasks": 1,
        "average_response_time": 2.5
    })
    
    balancer.update_agent_metrics("analyst_2", {
        "cpu_usage": 60.0,
        "memory_usage": 70.0,
        "active_tasks": 3,
        "completed_tasks": 15,
        "failed_tasks": 0,
        "average_response_time": 1.8
    })
    
    # Test agent selection
    decision = balancer.select_agent("analyst", "normal")
    print(f"Selected agent: {decision.agent_id} with confidence {decision.confidence:.2f}")
    
    # Test different strategies
    balancer.set_load_balancing_strategy(LoadBalancingStrategy.LEAST_CONNECTIONS)
    decision2 = balancer.select_agent("analyst", "high")
    print(f"Least connections selection: {decision2.agent_id}")
    
    # Get status
    status = balancer.get_load_balancing_status()
    print(f"Load balancer status: {status}")
    
    print("[INFO] Load Balancer: Agent load balancer test complete!")


if __name__ == "__main__":
    asyncio.run(test_agent_load_balancer())
