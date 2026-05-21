"""SPECTRE Agents — 10 specialized performance profiling agents."""
from .execution_tracer import ExecutionTracer
from .memory_profiler import MemoryProfiler
from .cpu_analyzer import CPUAnalyzer
from .io_profiler import IOProfiler
from .bottleneck_detector import BottleneckDetector
from .latency_analyzer import LatencyAnalyzer
from .resource_monitor import ResourceMonitor
from .cache_analyzer import CacheAnalyzer
from .concurrency_profiler import ConcurrencyProfiler
from .optimization_advisor import OptimizationAdvisor

__all__ = [
    "ExecutionTracer", "MemoryProfiler", "CPUAnalyzer", "IOProfiler",
    "BottleneckDetector", "LatencyAnalyzer", "ResourceMonitor",
    "CacheAnalyzer", "ConcurrencyProfiler", "OptimizationAdvisor",
]

AGENT_REGISTRY = {
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
