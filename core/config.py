"""SPECTRE Configuration — manages settings, agent configs, and runtime parameters."""
import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AgentConfig:
    """Configuration for a single SPECTRE agent."""
    name: str
    enabled: bool = True
    tokens_per_profile: int = 0
    profiles_per_day: int = 0
    priority: int = 5
    timeout_seconds: int = 120
    max_retries: int = 3
    parameters: Dict = field(default_factory=dict)


@dataclass
class SPECTREConfig:
    """Main SPECTRE configuration."""
    app_name: str = "SPECTRE"
    version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8084
    secret_key: str = "spectre-dev-key-change-in-production"

    # Database
    data_dir: str = field(default_factory=lambda: str(Path.home() / "spectre" / "data"))
    max_results_stored: int = 10000

    # Token tracking
    daily_token_budget: int = 80_000_000  # 80M tokens/day
    alert_threshold_pct: float = 0.85  # Alert at 85% usage

    # Agent defaults
    default_timeout: int = 120
    max_concurrent_agents: int = 5
    pipeline_retry_count: int = 2

    # Agent configurations
    agents: Dict[str, AgentConfig] = field(default_factory=dict)

    def __post_init__(self):
        if not self.agents:
            self.agents = self._default_agent_configs()
        os.makedirs(self.data_dir, exist_ok=True)

    def _default_agent_configs(self) -> Dict[str, AgentConfig]:
        return {
            "execution_tracer": AgentConfig(
                name="Execution Tracer",
                tokens_per_profile=18000,
                profiles_per_day=700,
                priority=1,
                parameters={"trace_depth": 50, "hot_path_threshold_ms": 10}
            ),
            "memory_profiler": AgentConfig(
                name="Memory Profiler",
                tokens_per_profile=20000,
                profiles_per_day=600,
                priority=1,
                parameters={"heap_snapshot_interval": 30, "leak_threshold_mb": 50}
            ),
            "cpu_analyzer": AgentConfig(
                name="CPU Analyzer",
                tokens_per_profile=16000,
                profiles_per_day=450,
                priority=2,
                parameters={"sampling_rate_hz": 100, "hotspot_threshold_pct": 5}
            ),
            "io_profiler": AgentConfig(
                name="IO Profiler",
                tokens_per_profile=14000,
                profiles_per_day=300,
                priority=2,
                parameters={"disk_latency_threshold_ms": 10, "network_timeout_ms": 5000}
            ),
            "bottleneck_detector": AgentConfig(
                name="Bottleneck Detector",
                tokens_per_profile=22000,
                profiles_per_day=500,
                priority=1,
                parameters={"n_plus_one_threshold": 5, "blocking_call_timeout_ms": 100}
            ),
            "latency_analyzer": AgentConfig(
                name="Latency Analyzer",
                tokens_per_profile=16000,
                profiles_per_day=400,
                priority=2,
                parameters={"p99_threshold_ms": 500, "timeout_detection_window": 60}
            ),
            "resource_monitor": AgentConfig(
                name="Resource Monitor",
                tokens_per_profile=14000,
                profiles_per_day=350,
                priority=3,
                parameters={"cpu_threshold_pct": 80, "memory_threshold_pct": 85}
            ),
            "cache_analyzer": AgentConfig(
                name="Cache Analyzer",
                tokens_per_profile=12000,
                profiles_per_day=300,
                priority=3,
                parameters={"min_hit_rate_pct": 70, "eviction_analysis_window": 300}
            ),
            "concurrency_profiler": AgentConfig(
                name="Concurrency Profiler",
                tokens_per_profile=18000,
                profiles_per_day=450,
                priority=1,
                parameters={"deadlock_detection": True, "thread_pool_max": 64}
            ),
            "optimization_advisor": AgentConfig(
                name="Optimization Advisor",
                tokens_per_profile=15000,
                profiles_per_day=400,
                priority=1,
                parameters={"min_impact_score": 3, "max_recommendations": 20}
            ),
        }

    @classmethod
    def from_env(cls) -> "SPECTREConfig":
        """Load configuration from environment variables."""
        config = cls()
        config.debug = os.getenv("SPECTRE_DEBUG", "false").lower() == "true"
        config.port = int(os.getenv("SPECTRE_PORT", "8084"))
        config.host = os.getenv("SPECTRE_HOST", "0.0.0.0")
        config.secret_key = os.getenv("SPECTRE_SECRET_KEY", config.secret_key)
        config.daily_token_budget = int(os.getenv("SPECTRE_TOKEN_BUDGET", str(config.daily_token_budget)))
        config.log_level = os.getenv("SPECTRE_LOG_LEVEL", "INFO")
        return config

    def get_total_daily_tokens(self) -> int:
        return sum(a.tokens_per_profile * a.profiles_per_day for a in self.agents.values())

    def get_enabled_agents(self) -> List[str]:
        return [name for name, cfg in self.agents.items() if cfg.enabled]

    def to_dict(self) -> dict:
        return {
            "app_name": self.app_name,
            "version": self.version,
            "port": self.port,
            "daily_token_budget": self.daily_token_budget,
            "total_daily_tokens": self.get_total_daily_tokens(),
            "enabled_agents": len(self.get_enabled_agents()),
            "agents": {name: {"tokens_per_profile": a.tokens_per_profile,
                              "profiles_per_day": a.profiles_per_day,
                              "enabled": a.enabled}
                       for name, a in self.agents.items()}
        }
