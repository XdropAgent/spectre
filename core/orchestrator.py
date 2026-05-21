"""SPECTRE Orchestrator — coordinates agent pipeline execution and result aggregation."""
import time
import asyncio
import logging
from typing import Dict, List, Optional, Type
from .config import SPECTREConfig
from .token_tracker import TokenTracker
from .models import ProfileResult, AgentResult, Bottleneck, OptimizationRecommendation, Severity

logger = logging.getLogger("spectre.orchestrator")


class Orchestrator:
    """
    Orchestrates the SPECTRE agent pipeline.

    Coordinates execution of 10 specialized profiling agents,
    tracks token consumption, and aggregates results into a
    unified performance profile.
    """

    def __init__(self, config: Optional[SPECTREConfig] = None):
        self.config = config or SPECTREConfig.from_env()
        self.token_tracker = TokenTracker(daily_budget=self.config.daily_token_budget)
        self._agents: Dict[str, object] = {}
        self._results: Dict[str, ProfileResult] = {}
        self._register_default_agents()

    def _register_default_agents(self):
        """Register all 10 default SPECTRE agents."""
        try:
            from agents import (
                ExecutionTracer, MemoryProfiler, CPUAnalyzer, IOProfiler,
                BottleneckDetector, LatencyAnalyzer, ResourceMonitor,
                CacheAnalyzer, ConcurrencyProfiler, OptimizationAdvisor
            )
            agent_classes = {
                "execution_tracer": ExecutionTracer,
                "memory_profiler": MemoryProfiler,
                "cpu_analyzer": CPUAnalyzer,
                "io_profiler": IOProfiler,
                "bottleneck_detector": BottleneckDetector,
                "latency_analyzer": LatencyAnalyzer,
                "resource_monitor": ResourceMonitor,
                "cache_analyzer": CacheAnalyzer,
                "concurrency_profiler": ConcurrencyProfiler,
                "optimization_advisor": OptimizationAdvisor,
            }
            for name, cls in agent_classes.items():
                agent_config = self.config.agents.get(name)
                if agent_config and agent_config.enabled:
                    self._agents[name] = cls(agent_config.__dict__)
                    logger.info(f"Registered agent: {name}")
        except ImportError as e:
            logger.warning(f"Could not import agents: {e}. Running with empty agent set.")

    def register_agent(self, name: str, agent):
        """Register a custom agent."""
        self._agents[name] = agent

    def get_agent(self, name: str):
        """Get a registered agent by name."""
        return self._agents.get(name)

    def list_agents(self) -> List[Dict]:
        """List all registered agents with their config."""
        agents = []
        for name, agent in self._agents.items():
            config = self.config.agents.get(name)
            agents.append({
                "name": name,
                "display_name": config.name if config else name,
                "enabled": config.enabled if config else True,
                "tokens_per_profile": config.tokens_per_profile if config else 0,
                "profiles_per_day": config.profiles_per_day if config else 0,
                "priority": config.priority if config else 5,
            })
        return agents

    async def run_profile(self, target: str, code: str = "",
                          agent_filter: Optional[List[str]] = None) -> ProfileResult:
        """Run the full profiling pipeline on a target."""
        result = ProfileResult(target=target, status="running")
        start_time = time.time()

        try:
            agents_to_run = self._agents
            if agent_filter:
                agents_to_run = {k: v for k, v in self._agents.items() if k in agent_filter}

            context = {
                "target": target,
                "code": code,
                "profile_id": result.id,
                "previous_results": {},
            }

            # Run agents in priority order
            sorted_agents = sorted(
                agents_to_run.items(),
                key=lambda x: self.config.agents.get(x[0], type("", (), {"priority": 5})()).priority
            )

            for agent_name, agent in sorted_agents:
                agent_start = time.time()
                try:
                    agent_config = self.config.agents.get(agent_name)
                    tokens_estimate = agent_config.tokens_per_profile if agent_config else 15000

                    agent_result = await asyncio.wait_for(
                        agent.analyze(code, context),
                        timeout=agent_config.timeout_seconds if agent_config else 120
                    )

                    duration_ms = (time.time() - agent_start) * 1000

                    ar = AgentResult(
                        agent_name=agent_name,
                        execution_time_ms=duration_ms,
                        tokens_used=tokens_estimate,
                        success=True,
                        findings=agent_result.get("findings", []),
                        metrics=agent_result.get("metrics", {}),
                        raw_output=agent_result,
                    )

                    # Extract bottlenecks
                    for b in agent_result.get("bottlenecks", []):
                        bottleneck = Bottleneck(
                            type=b.get("type", "blocking_call"),
                            severity=b.get("severity", "medium"),
                            title=b.get("title", ""),
                            description=b.get("description", ""),
                            location=b.get("location", ""),
                            impact_score=b.get("impact_score", 5.0),
                            recommendation=b.get("recommendation", ""),
                            detected_by=agent_name,
                        )
                        ar.bottlenecks.append(bottleneck)
                        result.bottlenecks.append(bottleneck)

                    # Extract recommendations
                    for r in agent_result.get("recommendations", []):
                        rec = OptimizationRecommendation(
                            title=r.get("title", ""),
                            description=r.get("description", ""),
                            priority=r.get("priority", 5),
                            impact_score=r.get("impact_score", 5.0),
                            category=r.get("category", agent_name),
                        )
                        ar.recommendations.append(rec)
                        result.recommendations.append(rec)

                    result.agent_results[agent_name] = ar
                    result.agents_run.append(agent_name)
                    result.total_tokens += tokens_estimate

                    self.token_tracker.record_usage(
                        agent_name=agent_name,
                        tokens_used=tokens_estimate,
                        profile_id=result.id,
                        duration_ms=duration_ms,
                    )

                    context["previous_results"][agent_name] = agent_result

                except asyncio.TimeoutError:
                    result.agent_results[agent_name] = AgentResult(
                        agent_name=agent_name,
                        execution_time_ms=(time.time() - agent_start) * 1000,
                        success=False,
                        error_message=f"Agent {agent_name} timed out",
                    )
                except Exception as e:
                    logger.error(f"Agent {agent_name} failed: {e}")
                    result.agent_results[agent_name] = AgentResult(
                        agent_name=agent_name,
                        execution_time_ms=(time.time() - agent_start) * 1000,
                        success=False,
                        error_message=str(e),
                    )

            # Calculate overall score
            result.overall_score = self._calculate_score(result)
            result.duration_ms = (time.time() - start_time) * 1000
            result.status = "completed"

        except Exception as e:
            result.status = "failed"
            result.error_message = str(e)
            logger.error(f"Profile failed: {e}")

        self._results[result.id] = result
        return result

    def _calculate_score(self, result: ProfileResult) -> float:
        """Calculate an overall performance score (0-100)."""
        score = 100.0
        for b in result.bottlenecks:
            if b.severity.value == "critical":
                score -= min(20, b.impact_score * 2)
            elif b.severity.value == "high":
                score -= min(10, b.impact_score * 1.5)
            elif b.severity.value == "medium":
                score -= min(5, b.impact_score)
            elif b.severity.value == "low":
                score -= min(2, b.impact_score * 0.5)
        return max(0, min(100, score))

    def get_result(self, profile_id: str) -> Optional[ProfileResult]:
        """Get a profile result by ID."""
        return self._results.get(profile_id)

    def get_all_results(self) -> List[ProfileResult]:
        """Get all stored profile results."""
        return sorted(self._results.values(), key=lambda r: r.timestamp, reverse=True)

    def get_stats(self) -> Dict:
        """Get comprehensive orchestration statistics."""
        return {
            "agents_registered": len(self._agents),
            "profiles_completed": len([r for r in self._results.values() if r.status == "completed"]),
            "profiles_failed": len([r for r in self._results.values() if r.status == "failed"]),
            "total_results": len(self._results),
            "token_tracker": self.token_tracker.get_summary(),
            "config": self.config.to_dict(),
        }
