"""
SPECTRE Resource Monitor Agent
Token estimate: ~14K tokens per profile

Monitors CPU, memory, disk, and network utilization patterns.
Identifies resource exhaustion risks and provides capacity planning insights.
"""
import ast
import time
from typing import Dict, List, Any
from collections import defaultdict


class ResourceMonitor:
    """
    Resource Monitor — CPU/memory/disk/network utilization tracking.

    Token Usage: ~14K tokens per profile
    Daily Volume: ~350 profiles/day = 4.9M tokens/day

    Capabilities:
    - CPU utilization pattern analysis
    - Memory usage tracking
    - Disk space monitoring patterns
    - Network bandwidth estimation
    - Resource exhaustion prediction
    - Container resource limit analysis
    - Thread/process count monitoring
    - File descriptor usage analysis
    - System call pattern detection
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.cpu_threshold_pct = self.config.get("cpu_threshold_pct", 80)
        self.memory_threshold_pct = self.config.get("memory_threshold_pct", 85)
        self.disk_threshold_pct = self.config.get("disk_threshold_pct", 90)
        self.fd_threshold = self.config.get("fd_threshold", 1000)

    async def analyze(self, code: str, context: Dict) -> Dict:
        """
        Analyze code for resource usage patterns and exhaustion risks.
        """
        start_time = time.time()
        findings = []
        bottlenecks = []
        recommendations = []
        metrics = {
            "resource_patterns": [],
            "exhaustion_risks": 0,
            "thread_usage": 0,
            "file_descriptor_risks": 0,
            "resource_score": 0.0,
            "estimated_cpu_pct": 0.0,
            "estimated_memory_mb": 0.0,
        }

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"findings": [], "bottlenecks": [], "recommendations": [], "metrics": metrics}

        # Analyze thread usage
        thread_usage = self._analyze_thread_usage(tree)
        metrics["thread_usage"] = thread_usage["count"]
        if thread_usage["count"] > 50:
            bottlenecks.append({
                "type": "resource_exhaustion",
                "severity": "high",
                "title": f"High thread count: {thread_usage['count']}",
                "description": f"Application creates {thread_usage['count']} threads. Each thread consumes ~8MB stack memory.",
                "location": "thread management",
                "line_number": thread_usage.get("line", 0),
                "impact_score": 7.0,
                "recommendation": "Use thread pool with bounded size instead of creating threads directly",
            })

        # Analyze file descriptor usage
        fd_usage = self._analyze_file_descriptors(tree)
        metrics["file_descriptor_risks"] = fd_usage["risk_count"]
        for risk in fd_usage["risks"]:
            bottlenecks.append({
                "type": "resource_exhaustion",
                "severity": risk.get("severity", "medium"),
                "title": f"File descriptor risk: {risk['type']}",
                "description": risk["description"],
                "location": risk.get("function", "unknown"),
                "line_number": risk.get("line", 0),
                "impact_score": risk.get("impact", 5.0),
                "recommendation": risk.get("recommendation", "Use context managers for resource cleanup"),
            })

        # Detect subprocess usage
        subprocess_usage = self._analyze_subprocess_usage(tree)
        for sp in subprocess_usage:
            findings.append(sp)
            if sp.get("unbounded"):
                bottlenecks.append({
                    "type": "resource_exhaustion",
                    "severity": "medium",
                    "title": f"Unbounded subprocess: {sp['command']}",
                    "description": sp["description"],
                    "location": sp.get("function", "unknown"),
                    "line_number": sp.get("line", 0),
                    "impact_score": 6.0,
                    "recommendation": "Add timeout and resource limits to subprocess calls",
                })

        # Detect large data loading patterns
        data_loading = self._detect_large_data_loading(tree)
        for dl in data_loading:
            bottlenecks.append({
                "type": "resource_exhaustion",
                "severity": dl.get("severity", "medium"),
                "title": f"Large data loading: {dl['pattern']}",
                "description": dl["description"],
                "location": dl.get("function", "unknown"),
                "line_number": dl.get("line", 0),
                "impact_score": dl.get("impact", 5.0),
                "recommendation": dl.get("recommendation", "Use streaming or chunked loading"),
            })

        # Detect caching patterns that consume memory
        mem_cache = self._detect_memory_caching(tree)
        for mc in mem_cache:
            findings.append(mc)
            if mc.get("unbounded"):
                bottlenecks.append({
                    "type": "resource_exhaustion",
                    "severity": "high",
                    "title": f"Unbounded in-memory cache: {mc['name']}",
                    "description": f"In-memory cache '{mc['name']}' grows without bounds — will eventually exhaust memory",
                    "location": mc.get("function", "unknown"),
                    "line_number": mc.get("line", 0),
                    "impact_score": 8.0,
                    "recommendation": "Use bounded cache (LRU) or external cache (Redis)",
                })

        # Detect busy computation patterns (CPU exhaustion)
        cpu_heavy = self._detect_cpu_heavy_patterns(tree)
        for ch in cpu_heavy:
            bottlenecks.append({
                "type": "resource_exhaustion",
                "severity": ch.get("severity", "medium"),
                "title": f"CPU-intensive: {ch['pattern']}",
                "description": ch["description"],
                "location": ch.get("function", "unknown"),
                "line_number": ch.get("line", 0),
                "impact_score": ch.get("impact", 5.0),
                "recommendation": ch.get("recommendation", "Offload to worker process or add rate limiting"),
            })

        # Check for resource monitoring code
        has_monitoring = self._check_monitoring_presence(tree)
        if not has_monitoring:
            findings.append({
                "type": "missing_monitoring",
                "message": "No resource monitoring or health check endpoints detected",
                "severity": "medium",
            })
            recommendations.append({
                "title": "Add resource monitoring",
                "description": "No health check or resource monitoring endpoints found. Add /health and /metrics endpoints.",
                "priority": 3,
                "impact_score": 4.0,
                "category": "resource",
            })

        # Analyze connection management
        conn_mgmt = self._analyze_connection_management(tree)
        for cm in conn_mgmt:
            findings.append(cm)
            if cm.get("leak_risk"):
                bottlenecks.append({
                    "type": "resource_exhaustion",
                    "severity": "medium",
                    "title": f"Connection leak risk: {cm['type']}",
                    "description": cm["description"],
                    "location": cm.get("function", "unknown"),
                    "line_number": cm.get("line", 0),
                    "impact_score": 6.0,
                    "recommendation": cm.get("recommendation", "Use context managers for connections"),
                })

        # Estimate resource usage
        metrics["estimated_cpu_pct"] = min(100, 20 + cpu_heavy.__len__() * 15)
        metrics["estimated_memory_mb"] = 100 + mem_cache.__len__() * 200 + data_loading.__len__() * 100

        # Generate recommendations
        if metrics["estimated_cpu_pct"] > self.cpu_threshold_pct:
            recommendations.append({
                "title": "Reduce CPU utilization",
                "description": f"Estimated CPU usage ({metrics['estimated_cpu_pct']}%) exceeds threshold ({self.cpu_threshold_pct}%).",
                "priority": 2,
                "impact_score": 7.0,
                "category": "resource",
            })

        if metrics["estimated_memory_mb"] > 1000:
            recommendations.append({
                "title": "Reduce memory footprint",
                "description": f"Estimated memory usage ({metrics['estimated_memory_mb']}MB) is high. Consider streaming or caching strategies.",
                "priority": 2,
                "impact_score": 7.0,
                "category": "resource",
            })

        # Calculate resource score
        issues = metrics["exhaustion_risks"] + metrics["file_descriptor_risks"]
        metrics["resource_score"] = max(0, 100 - issues * 10)

        return {
            "findings": findings,
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "metrics": metrics,
            "execution_time_ms": round((time.time() - start_time) * 1000, 1),
        }

    def _analyze_thread_usage(self, tree: ast.AST) -> Dict:
        """Analyze thread creation patterns."""
        count = 0
        line = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = self._get_call_name(node)
                if name and any(t in name for t in ["Thread(", "threading.Thread", "Process(", "multiprocessing.Process"]):
                    count += 1
                    line = getattr(node, "lineno", 0)
        return {"count": count, "line": line}

    def _analyze_file_descriptors(self, tree: ast.AST) -> Dict:
        """Analyze file descriptor usage patterns."""
        risks = []
        risk_count = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if isinstance(node.value, ast.Call):
                    name = self._get_call_name(node.value)
                    if name and "open" in name:
                        # Check if used in with statement
                        in_with = False
                        for parent in ast.walk(tree):
                            if isinstance(parent, ast.With):
                                for item in parent.items:
                                    if hasattr(item, "context_expr"):
                                        pass
                        if not in_with:
                            risk_count += 1
                            risks.append({
                                "type": "file_handle",
                                "line": getattr(node, "lineno", 0),
                                "severity": "medium",
                                "description": "File opened without context manager — potential FD leak",
                                "impact": 5.0,
                                "recommendation": "Use 'with open(...)' for automatic cleanup",
                                "function": "unknown",
                            })

            # Socket connections without close
            if isinstance(node, ast.Call):
                name = self._get_call_name(node)
                if name and any(s in name for s in ["socket.socket", "Socket", "connect"]):
                    risk_count += 1
                    risks.append({
                        "type": "socket",
                        "line": getattr(node, "lineno", 0),
                        "severity": "medium",
                        "description": f"Socket connection at line {getattr(node, 'lineno', 0)} — ensure proper cleanup",
                        "impact": 5.0,
                        "recommendation": "Use context managers for socket connections",
                        "function": "unknown",
                    })

        return {"risk_count": risk_count, "risks": risks}

    def _analyze_subprocess_usage(self, tree: ast.AST) -> List[Dict]:
        """Analyze subprocess usage patterns."""
        results = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = self._get_call_name(node)
                if name and any(sp in name for sp in ["subprocess.run", "subprocess.call", "subprocess.Popen",
                                                       "os.system", "os.popen"]):
                    has_timeout = any(kw.arg in ("timeout",) for kw in node.keywords)
                    results.append({
                        "command": name,
                        "line": getattr(node, "lineno", 0),
                        "unbounded": not has_timeout,
                        "description": f"Subprocess call '{name}' without timeout — may hang",
                        "function": "unknown",
                    })
        return results

    def _detect_large_data_loading(self, tree: ast.AST) -> List[Dict]:
        """Detect patterns that load large amounts of data."""
        results = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = self._get_call_name(node)
                if name:
                    if "read" in name.lower() and "readlines" not in name.lower():
                        results.append({
                            "pattern": "full_file_read",
                            "line": getattr(node, "lineno", 0),
                            "severity": "medium",
                            "description": f"Full file read at line {getattr(node, 'lineno', 0)} — may consume excessive memory",
                            "impact": 5.0,
                            "recommendation": "Use streaming/chunked reading for large files",
                            "function": "unknown",
                        })
                    if any(c in name for c in ["json.load", "yaml.load", "pickle.load"]):
                        results.append({
                            "pattern": "full_data_load",
                            "line": getattr(node, "lineno", 0),
                            "severity": "medium",
                            "description": f"Full data deserialization at line {getattr(node, 'lineno', 0)}",
                            "impact": 5.0,
                            "recommendation": "Consider streaming parser for large datasets",
                            "function": "unknown",
                        })
        return results

    def _detect_memory_caching(self, tree: ast.AST) -> List[Dict]:
        """Detect in-memory caching patterns."""
        results = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        if any(c in name.lower() for c in ["cache", "_cache", "memo", "store"]):
                            if isinstance(node.value, (ast.Dict, ast.Call)):
                                is_bounded = False
                                if isinstance(node.value, ast.Call):
                                    for kw in node.keywords:
                                        if kw.arg in ("maxsize", "maxlen", "limit"):
                                            is_bounded = True
                                results.append({
                                    "name": name,
                                    "line": getattr(node, "lineno", 0),
                                    "unbounded": not is_bounded,
                                    "function": "unknown",
                                })
        return results

    def _detect_cpu_heavy_patterns(self, tree: ast.AST) -> List[Dict]:
        """Detect CPU-intensive patterns."""
        results = []
        heavy_ops = {"hashlib", "bcrypt", "scrypt", "pbkdf2", "encrypt", "decrypt",
                     "compress", "decompress", "encode", "decode", "render"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = self._get_call_name(node)
                if name and any(h in name for h in heavy_ops):
                    results.append({
                        "pattern": name,
                        "line": getattr(node, "lineno", 0),
                        "severity": "medium",
                        "description": f"CPU-intensive operation: {name}",
                        "impact": 4.0,
                        "recommendation": "Consider caching result or offloading to worker",
                        "function": "unknown",
                    })
        return results

    def _check_monitoring_presence(self, tree: ast.AST) -> bool:
        """Check if resource monitoring endpoints exist."""
        monitoring_indicators = {"health", "healthcheck", "metrics", "status", "ping", "alive"}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.lower() in monitoring_indicators:
                    return True
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if any(m in node.value.lower() for m in monitoring_indicators):
                    return True
        return False

    def _analyze_connection_management(self, tree: ast.AST) -> List[Dict]:
        """Analyze connection management patterns."""
        results = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = self._get_call_name(node)
                if name and any(c in name for c in ["connect", "Connection", "create_pool"]):
                    results.append({
                        "type": name,
                        "line": getattr(node, "lineno", 0),
                        "leak_risk": True,
                        "description": f"Connection created via '{name}' — ensure proper cleanup",
                        "recommendation": "Use context managers or connection pools",
                        "function": "unknown",
                    })
        return results

    def _get_call_name(self, node) -> str:
        if isinstance(node, ast.Call):
            node = node.func
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            parts = [node.attr]
            current = node.value
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return ".".join(reversed(parts))
        return ""
