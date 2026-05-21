"""SPECTRE Data Models — defines the data structures for profiling results."""
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class Severity(Enum):
    """Bottleneck severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class BottleneckType(Enum):
    """Types of performance bottlenecks."""
    N_PLUS_ONE_QUERY = "n_plus_one_query"
    BLOCKING_CALL = "blocking_call"
    MEMORY_LEAK = "memory_leak"
    CPU_HOTSPOT = "cpu_hotspot"
    IO_BOTTLENECK = "io_bottleneck"
    CACHE_MISS = "cache_miss"
    DEADLOCK = "deadlock"
    THREAD_CONTENTION = "thread_contention"
    QUEUE_BUILDUP = "queue_buildup"
    LATENCY_SPIKE = "latency_spike"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    NETWORK_TIMEOUT = "network_timeout"
    CONTEXT_SWITCH_STORM = "context_switch_storm"
    ALLOCATION_PRESSURE = "allocation_pressure"


@dataclass
class Bottleneck:
    """A detected performance bottleneck."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: BottleneckType = BottleneckType.BLOCKING_CALL
    severity: Severity = Severity.MEDIUM
    title: str = ""
    description: str = ""
    location: str = ""
    line_number: int = 0
    impact_score: float = 0.0  # 1-10
    estimated_time_saved_ms: float = 0.0
    recommendation: str = ""
    detected_by: str = ""  # agent name
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "line_number": self.line_number,
            "impact_score": self.impact_score,
            "estimated_time_saved_ms": self.estimated_time_saved_ms,
            "recommendation": self.recommendation,
            "detected_by": self.detected_by,
        }


@dataclass
class OptimizationRecommendation:
    """An actionable optimization recommendation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    description: str = ""
    priority: int = 5  # 1=highest, 10=lowest
    impact_score: float = 0.0  # 1-10
    effort_estimate: str = "medium"  # low, medium, high
    category: str = ""
    code_before: str = ""
    code_after: str = ""
    expected_improvement: str = ""
    related_bottlenecks: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "impact_score": self.impact_score,
            "effort_estimate": self.effort_estimate,
            "category": self.category,
            "code_before": self.code_before,
            "code_after": self.code_after,
            "expected_improvement": self.expected_improvement,
        }


@dataclass
class AgentResult:
    """Result from a single agent's analysis."""
    agent_name: str
    execution_time_ms: float = 0.0
    tokens_used: int = 0
    success: bool = True
    error_message: str = ""
    findings: List[Dict] = field(default_factory=list)
    bottlenecks: List[Bottleneck] = field(default_factory=list)
    recommendations: List[OptimizationRecommendation] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    raw_output: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "execution_time_ms": self.execution_time_ms,
            "tokens_used": self.tokens_used,
            "success": self.success,
            "error_message": self.error_message,
            "findings_count": len(self.findings),
            "bottlenecks_count": len(self.bottlenecks),
            "recommendations_count": len(self.recommendations),
            "metrics": self.metrics,
        }


@dataclass
class ProfileResult:
    """Complete profiling result from all agents."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    target: str = ""
    timestamp: float = field(default_factory=time.time)
    duration_ms: float = 0.0
    total_tokens: int = 0
    agents_run: List[str] = field(default_factory=list)
    agent_results: Dict[str, AgentResult] = field(default_factory=dict)
    bottlenecks: List[Bottleneck] = field(default_factory=list)
    recommendations: List[OptimizationRecommendation] = field(default_factory=list)
    overall_score: float = 0.0  # 0-100
    status: str = "pending"
    error_message: str = ""

    @property
    def timestamp_iso(self) -> str:
        from datetime import datetime
        return datetime.fromtimestamp(self.timestamp).isoformat()

    @property
    def critical_bottlenecks(self) -> List[Bottleneck]:
        return [b for b in self.bottlenecks if b.severity == Severity.CRITICAL]

    @property
    def top_recommendations(self) -> List[OptimizationRecommendation]:
        return sorted(self.recommendations, key=lambda r: r.priority)[:10]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "target": self.target,
            "timestamp": self.timestamp_iso,
            "duration_ms": round(self.duration_ms, 1),
            "total_tokens": self.total_tokens,
            "agents_run": self.agents_run,
            "agents_count": len(self.agents_run),
            "bottlenecks_count": len(self.bottlenecks),
            "critical_count": len(self.critical_bottlenecks),
            "recommendations_count": len(self.recommendations),
            "overall_score": round(self.overall_score, 1),
            "status": self.status,
            "agent_results": {name: r.to_dict() for name, r in self.agent_results.items()},
            "top_bottlenecks": [b.to_dict() for b in sorted(self.bottlenecks, key=lambda x: x.impact_score, reverse=True)[:5]],
            "top_recommendations": [r.to_dict() for r in self.top_recommendations],
        }
