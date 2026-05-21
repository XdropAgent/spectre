"""
SPECTRE Latency Analyzer Agent
Token estimate: ~16K tokens per profile

Analyzes response times, percentile distributions, timeout patterns,
and latency bottlenecks. Identifies slow operations and provides
recommendations for latency optimization.
"""
import ast
import time
import math
from typing import Dict, List, Any
from collections import defaultdict


class LatencyAnalyzer:
    """
    Latency Analyzer — response times, percentile analysis, timeout detection.

    Token Usage: ~16K tokens per profile
    Daily Volume: ~400 profiles/day = 6.4M tokens/day

    Capabilities:
    - Response time analysis
    - Percentile estimation (P50, P95, P99)
    - Timeout detection and configuration
    - Slow path identification
    - External service latency analysis
    - Database query latency estimation
    - Serialization overhead detection
    - Middleware chain analysis
    - Header processing overhead
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.p99_threshold_ms = self.config.get("p99_threshold_ms", 500)
        self.timeout_detection_window = self.config.get("timeout_detection_window", 60)

    async def analyze(self, code: str, context: Dict) -> Dict:
        """
        Analyze code for latency patterns and timeout risks.
        """
        start_time = time.time()
        findings = []
        bottlenecks = []
        recommendations = []
        metrics = {
            "timeout_risks": 0,
            "slow_operations": [],
            "external_calls": 0,
            "estimated_p50_ms": 0.0,
            "estimated_p95_ms": 0.0,
            "estimated_p99_ms": 0.0,
            "latency_score": 0.0,
        }

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"findings": [], "bottlenecks": [], "recommendations": [], "metrics": metrics}

        # Detect timeout configuration
        timeout_issues = self._detect_timeout_issues(tree)
        metrics["timeout_risks"] = len(timeout_issues)
        for issue in timeout_issues:
            bottlenecks.append({
                "type": "latency_spike",
                "severity": issue.get("severity", "high"),
                "title": f"Timeout issue: {issue['type']}",
                "description": issue["description"],
                "location": issue.get("function", "unknown"),
                "line_number": issue.get("line", 0),
                "impact_score": issue.get("impact", 7.0),
                "recommendation": issue.get("recommendation", "Configure appropriate timeouts"),
            })

        # Detect slow operations
        slow_ops = self._detect_slow_operations(tree)
        metrics["slow_operations"] = slow_ops
        for op in slow_ops:
            bottlenecks.append({
                "type": "latency_spike",
                "severity": op.get("severity", "medium"),
                "title": f"Slow operation: {op['operation']}",
                "description": op["description"],
                "location": op.get("function", "unknown"),
                "line_number": op.get("line", 0),
                "impact_score": op.get("impact", 5.0),
                "recommendation": op.get("recommendation", "Cache result or optimize operation"),
            })

        # Analyze external service calls
        ext_calls = self._analyze_external_calls(tree)
        metrics["external_calls"] = len(ext_calls)
        for call in ext_calls:
            findings.append(call)
            if call.get("missing_timeout"):
                bottlenecks.append({
                    "type": "latency_spike",
                    "severity": "high",
                    "title": f"External call without timeout: {call['call']}",
                    "description": f"External service call '{call['call']}' at line {call.get('line', 0)} has no timeout — can hang indefinitely",
                    "location": call.get("function", "unknown"),
                    "line_number": call.get("line", 0),
                    "impact_score": 8.0,
                    "recommendation": "Add connection and read timeouts to all external calls",
                })
            if call.get("is_synchronous"):
                bottlenecks.append({
                    "type": "latency_spike",
                    "severity": "medium",
                    "title": f"Synchronous external call: {call['call']}",
                    "description": f"Blocking external call at line {call.get('line', 0)} adds latency to response",
                    "location": call.get("function", "unknown"),
                    "line_number": call.get("line", 0),
                    "impact_score": 5.0,
                    "recommendation": "Use async HTTP client or cache responses",
                })

        # Detect serialization overhead
        serial_issues = self._detect_serialization_overhead(tree)
        for issue in serial_issues:
            findings.append(issue)
            if issue.get("in_hot_path"):
                bottlenecks.append({
                    "type": "latency_spike",
                    "severity": "medium",
                    "title": f"Serialization overhead: {issue['type']}",
                    "description": issue["description"],
                    "location": issue.get("function", "unknown"),
                    "line_number": issue.get("line", 0),
                    "impact_score": 5.0,
                    "recommendation": issue.get("recommendation", "Cache serialized results"),
                })

        # Detect middleware chain issues
        middleware_issues = self._detect_middleware_overhead(tree)
        for issue in middleware_issues:
            findings.append(issue)

        # Detect retry without backoff (latency multiplier)
        retry_latency = self._detect_retry_latency(tree)
        for rl in retry_latency:
            bottlenecks.append({
                "type": "latency_spike",
                "severity": "high",
                "title": f"Retry latency multiplier: {rl['function']}",
                "description": f"Retry loop at line {rl['line']} can multiply latency by {rl.get('max_retries', 'N')}x",
                "location": rl["function"],
                "line_number": rl["line"],
                "impact_score": 7.0,
                "recommendation": "Add exponential backoff and max retry limit",
            })

        # Detect sleep/delay in request path
        sleep_issues = self._detect_sleep_in_request_path(tree)
        for si in sleep_issues:
            bottlenecks.append({
                "type": "latency_spike",
                "severity": "medium",
                "title": f"Sleep in request path: {si['duration']}s",
                "description": f"Hard-coded sleep at line {si['line']} adds {si['duration']}s to response time",
                "location": si.get("function", "unknown"),
                "line_number": si["line"],
                "impact_score": min(10, si["duration"] * 2),
                "recommendation": "Remove sleep or make it configurable/async",
            })

        # Estimate latency percentiles
        base_latency = 5.0  # 5ms base
        op_count = len(slow_ops) + len(ext_calls) * 10
        metrics["estimated_p50_ms"] = round(base_latency + op_count * 0.5, 1)
        metrics["estimated_p95_ms"] = round(base_latency + op_count * 2.0, 1)
        metrics["estimated_p99_ms"] = round(base_latency + op_count * 5.0, 1)

        # Recommendations
        if metrics["timeout_risks"] > 0:
            recommendations.append({
                "title": "Configure timeouts on all external calls",
                "description": f"Found {metrics['timeout_risks']} timeout risks. Unbounded waits cause cascading latency.",
                "priority": 1,
                "impact_score": 8.0,
                "category": "latency",
            })

        if metrics["estimated_p99_ms"] > self.p99_threshold_ms:
            recommendations.append({
                "title": "Reduce P99 latency",
                "description": f"Estimated P99 latency ({metrics['estimated_p99_ms']}ms) exceeds threshold ({self.p99_threshold_ms}ms).",
                "priority": 2,
                "impact_score": 7.0,
                "category": "latency",
            })

        if metrics["external_calls"] > 5:
            recommendations.append({
                "title": "Reduce external service dependencies",
                "description": f"Found {metrics['external_calls']} external calls. Each adds latency variance.",
                "priority": 3,
                "impact_score": 6.0,
                "category": "latency",
            })

        # Calculate latency score
        issues = metrics["timeout_risks"] + len(slow_ops) + len(retry_latency) + len(sleep_issues)
        metrics["latency_score"] = max(0, 100 - issues * 8)

        return {
            "findings": findings,
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "metrics": metrics,
            "execution_time_ms": round((time.time() - start_time) * 1000, 1),
        }

    def _detect_timeout_issues(self, tree: ast.AST) -> List[Dict]:
        """Detect missing or misconfigured timeouts."""
        issues = []
        timeout_sensitive = {"requests", "httpx", "aiohttp", "urllib", "socket",
                            "grpc", "redis", "pymongo", "psycopg", "mysql"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_full_name(node)
                if func_name and any(ts in func_name for ts in timeout_sensitive):
                    has_timeout = False
                    for kw in node.keywords:
                        if kw.arg in ("timeout", "Timeout", "connect_timeout", "read_timeout",
                                     "socket_timeout", "request_timeout"):
                            has_timeout = True
                    if not has_timeout:
                        issues.append({
                            "type": "missing_timeout",
                            "call": func_name,
                            "line": getattr(node, "lineno", 0),
                            "severity": "high",
                            "description": f"No timeout configured for '{func_name}' at line {getattr(node, 'lineno', 0)}",
                            "impact": 8.0,
                            "recommendation": "Add explicit timeout (connect + read) to prevent indefinite blocking",
                            "function": "unknown",
                        })

        # Detect overly long timeouts
        for node in ast.walk(tree):
            for kw in getattr(node, "keywords", []):
                if kw.arg in ("timeout", "Timeout") and isinstance(kw.value, ast.Constant):
                    if isinstance(kw.value.value, (int, float)) and kw.value.value > 30:
                        issues.append({
                            "type": "long_timeout",
                            "line": getattr(node, "lineno", 0),
                            "severity": "medium",
                            "description": f"Timeout of {kw.value.value}s is very long — may cause slow failure detection",
                            "impact": 5.0,
                            "recommendation": "Consider shorter timeout (5-10s) with retry logic",
                            "function": "unknown",
                        })
        return issues

    def _detect_slow_operations(self, tree: ast.AST) -> List[Dict]:
        """Detect operations known to be slow."""
        slow_ops_db = {"aggregate", "count", "distinct", "group_by", "order_by",
                       "full_text_search", "regex", "like"}
        slow_ops_compute = {"sort", "sorted", "compile", "dumps", "loads",
                           "render_template", "render", "encode", "decode"}
        results = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                attr = self._get_attr(node)
                if attr:
                    if attr in slow_ops_db:
                        results.append({
                            "operation": f"db.{attr}",
                            "line": getattr(node, "lineno", 0),
                            "severity": "medium",
                            "description": f"Potentially slow database operation: {attr}",
                            "impact": 5.0,
                            "recommendation": "Add indexing or cache results",
                            "function": "unknown",
                        })
                    elif attr in slow_ops_compute:
                        results.append({
                            "operation": attr,
                            "line": getattr(node, "lineno", 0),
                            "severity": "low",
                            "description": f"Potentially slow operation: {attr}",
                            "impact": 3.0,
                            "recommendation": f"Cache result of {attr} if called frequently",
                            "function": "unknown",
                        })
        return results

    def _analyze_external_calls(self, tree: ast.AST) -> List[Dict]:
        """Analyze external service calls for latency risks."""
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = self._get_full_name(node)
                if name and any(ext in name for ext in ["requests.", "httpx.", "urllib.", "grpc."]):
                    has_timeout = any(kw.arg in ("timeout",) for kw in node.keywords)
                    calls.append({
                        "call": name,
                        "line": getattr(node, "lineno", 0),
                        "missing_timeout": not has_timeout,
                        "is_synchronous": "async" not in name.lower(),
                        "function": "unknown",
                    })
        return calls

    def _detect_serialization_overhead(self, tree: ast.AST) -> List[Dict]:
        """Detect serialization that may add latency."""
        issues = []
        serial_funcs = {"json.dumps", "json.loads", "pickle.dumps", "pickle.loads",
                       "marshal.dumps", "marshal.loads", "yaml.dump", "yaml.load"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = self._get_full_name(node)
                if name and any(sf in name for sf in serial_funcs):
                    issues.append({
                        "type": "serialization",
                        "operation": name,
                        "line": getattr(node, "lineno", 0),
                        "in_hot_path": True,
                        "description": f"Serialization operation '{name}' at line {getattr(node, 'lineno', 0)}",
                        "recommendation": "Cache serialized results or use faster serializer (orjson, msgpack)",
                        "function": "unknown",
                    })
        return issues

    def _detect_middleware_overhead(self, tree: ast.AST) -> List[Dict]:
        """Detect middleware that may add latency."""
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                decorators = []
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Name):
                        decorators.append(dec.id)
                    elif isinstance(dec, ast.Attribute):
                        decorators.append(dec.attr)
                    elif isinstance(dec, ast.Call):
                        if isinstance(dec.func, ast.Name):
                            decorators.append(dec.func.id)
                if any(d in str(decorators).lower() for d in ["middleware", "before_request", "after_request"]):
                    issues.append({
                        "type": "middleware",
                        "function": node.name,
                        "line": getattr(node, "lineno", 0),
                        "description": f"Middleware '{node.name}' adds latency to every request",
                    })
        return issues

    def _detect_retry_latency(self, tree: ast.AST) -> List[Dict]:
        """Detect retry patterns that multiply latency."""
        results = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_name = node.name
                for child in ast.walk(node):
                    if isinstance(child, (ast.For, ast.While)):
                        # Check for retry-like patterns
                        has_try = False
                        for inner in ast.walk(child):
                            if isinstance(inner, ast.Try):
                                has_try = True
                        if has_try:
                            max_retries = 3  # default assumption
                            results.append({
                                "function": func_name,
                                "line": getattr(child, "lineno", 0),
                                "max_retries": max_retries,
                            })
        return results

    def _detect_sleep_in_request_path(self, tree: ast.AST) -> List[Dict]:
        """Detect hard-coded sleeps in request handling."""
        results = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = self._get_full_name(node)
                if name and "sleep" in name:
                    duration = 0
                    if node.args and isinstance(node.args[0], ast.Constant):
                        duration = node.args[0].value
                    results.append({
                        "line": getattr(node, "lineno", 0),
                        "duration": duration,
                        "function": "unknown",
                    })
        return results

    def _get_full_name(self, node) -> str:
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

    def _get_attr(self, node: ast.Call) -> str:
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
        elif isinstance(node.func, ast.Name):
            return node.func.id
        return ""
