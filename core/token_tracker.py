"""SPECTRE Token Tracker — monitors and records token consumption across all agents."""
import time
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class TokenUsage:
    """Token usage record for a single agent invocation."""
    agent_name: str
    tokens_used: int
    timestamp: float = field(default_factory=time.time)
    profile_id: str = ""
    duration_ms: float = 0.0
    success: bool = True


class TokenTracker:
    """
    Tracks token consumption across all SPECTRE agents.

    Provides real-time monitoring, daily budget tracking, and
    per-agent consumption analytics. SPECTRE processes 76M+ tokens
    daily across 10 specialized agents.

    Token Estimates per Profile:
    - Execution Tracer: ~18K tokens
    - Memory Profiler: ~20K tokens
    - Bottleneck Detector: ~22K tokens
    - Concurrency Profiler: ~18K tokens
    - CPU Analyzer: ~16K tokens
    - Latency Analyzer: ~16K tokens
    - Optimization Advisor: ~15K tokens
    - Resource Monitor: ~14K tokens
    - IO Profiler: ~14K tokens
    - Cache Analyzer: ~12K tokens
    """

    def __init__(self, daily_budget: int = 80_000_000):
        self.daily_budget = daily_budget
        self._usage_log: List[TokenUsage] = []
        self._daily_totals: Dict[str, int] = defaultdict(int)  # date_str -> total
        self._agent_totals: Dict[str, int] = defaultdict(int)  # agent_name -> total
        self._agent_counts: Dict[str, int] = defaultdict(int)  # agent_name -> count
        self._hourly_totals: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        self._start_time = time.time()

    def record_usage(self, agent_name: str, tokens_used: int,
                     profile_id: str = "", duration_ms: float = 0.0,
                     success: bool = True) -> TokenUsage:
        """Record token usage for an agent invocation."""
        usage = TokenUsage(
            agent_name=agent_name,
            tokens_used=tokens_used,
            profile_id=profile_id,
            duration_ms=duration_ms,
            success=success
        )
        self._usage_log.append(usage)

        date_str = datetime.now().strftime("%Y-%m-%d")
        hour = datetime.now().hour

        self._daily_totals[date_str] += tokens_used
        self._agent_totals[agent_name] += tokens_used
        self._agent_counts[agent_name] += 1
        self._hourly_totals[date_str][hour] += tokens_used

        return usage

    def get_daily_usage(self, date: Optional[str] = None) -> int:
        """Get total tokens used for a specific date."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        return self._daily_totals.get(date, 0)

    def get_daily_remaining(self) -> int:
        """Get remaining tokens in today's budget."""
        used = self.get_daily_usage()
        return max(0, self.daily_budget - used)

    def get_budget_utilization_pct(self) -> float:
        """Get budget utilization as a percentage."""
        used = self.get_daily_usage()
        return (used / self.daily_budget * 100) if self.daily_budget > 0 else 0.0

    def get_agent_stats(self) -> Dict[str, Dict]:
        """Get per-agent token consumption statistics."""
        stats = {}
        for agent_name in self._agent_totals:
            total = self._agent_totals[agent_name]
            count = self._agent_counts[agent_name]
            avg = total / count if count > 0 else 0

            recent = [u for u in self._usage_log[-100:] if u.agent_name == agent_name]
            recent_avg = sum(u.tokens_used for u in recent) / len(recent) if recent else avg

            stats[agent_name] = {
                "total_tokens": total,
                "profile_count": count,
                "avg_tokens_per_profile": round(avg),
                "recent_avg_tokens": round(recent_avg),
                "daily_estimate": round(recent_avg * (count / max(1, self._days_running()))),
            }
        return stats

    def get_hourly_breakdown(self, date: Optional[str] = None) -> Dict[int, int]:
        """Get hourly token usage breakdown."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        return dict(self._hourly_totals.get(date, {}))

    def get_total_tokens(self) -> int:
        """Get total tokens used across all time."""
        return sum(self._agent_totals.values())

    def get_total_profiles(self) -> int:
        """Get total number of profiles analyzed."""
        return sum(self._agent_counts.values())

    def _days_running(self) -> float:
        elapsed = time.time() - self._start_time
        return max(elapsed / 86400, 1.0)

    def get_summary(self) -> Dict:
        """Get comprehensive token tracking summary."""
        daily_used = self.get_daily_usage()
        return {
            "daily_budget": self.daily_budget,
            "daily_used": daily_used,
            "daily_remaining": self.get_daily_remaining(),
            "budget_utilization_pct": round(self.get_budget_utilization_pct(), 1),
            "total_tokens": self.get_total_tokens(),
            "total_profiles": self.get_total_profiles(),
            "agent_stats": self.get_agent_stats(),
            "uptime_hours": round((time.time() - self._start_time) / 3600, 1),
        }
