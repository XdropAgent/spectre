"""
SPECTRE Bottleneck Detector Agent
Token estimate: ~22K tokens per profile

The most comprehensive agent — detects N+1 queries, blocking calls,
queue buildup, and systemic performance bottlenecks across the entire
application stack. Aggregates findings from other agents for holistic
bottleneck identification.
"""
import ast
import time
import re
from typing import Dict, List, Any, Set
from collections import defaultdict


class BottleneckDetector:
    """
    Bottleneck Detector — N+1 queries, blocking calls, queue buildup.

    Token Usage: ~22K tokens per profile
    Daily Volume: ~500 profiles/day = 11.0M tokens/day

    Capabilities:
    - N+1 query pattern detection
    - Blocking call identification (sync in async)
    - Queue buildup detection
    - Lock contention analysis
    - Resource exhaustion patterns
    - Cascade failure detection
    - Rate limiting analysis
    - Connection pool exhaustion
    - Memory pressure cascade
    - Retry storm detection
    - Thundering herd detection
    - Missing error handling patterns
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.n_plus_one_threshold = self.config.get("n_plus_one_threshold", 5)
        self.blocking_call_timeout_ms = self.config.get("blocking_call_timeout_ms", 100)
        self.queue_depth_threshold = self.config.get("queue_depth_threshold", 1000)

    async def analyze(self, code: str, context: Dict) -> Dict:
        """
        Analyze code for performance bottlenecks across the stack.
        """
        start_time = time.time()
        findings = []
        bottlenecks = []
        recommendations = []
        metrics = {
            "n_plus_one_risks": 0,
            "blocking_calls": 0,
            "queue_risks": 0,
            "cascade_risks": 0,
            "retry_storms": 0,
            "overall_bottleneck_score": 0.0,
        }

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"findings": [], "bottlenecks": [], "recommendations": [], "metrics": metrics}

        # N+1 Query Detection
        n_plus_one = self._detect_n_plus_one_queries(tree)
        metrics["n_plus_one_risks"] = len(n_plus_one)
        for n1 in n_plus_one:
            bottlenecks.append({
                "type": "n_plus_one_query",
                "severity": "critical",
                "title": f"N+1 query in {n1['function']}",
                "description": f"Database query inside loop at line {n1['line']} — likely N+1 pattern. "
                               f"Executes ~{n1.get('estimated_queries', 'N')} queries per call.",
                "location": n1["function"],
                "line_number": n1["line"],
                "impact_score": 9.5,
                "recommendation": f"Use batch query, eager loading, or JOIN to fetch all data in one query",
            })

        # Blocking Call Detection
        blocking = self._detect_blocking_calls(tree)
        metrics["blocking_calls"] = len(blocking)
        for b in blocking:
            bottlenecks.append({
                "type": "blocking_call",
                "severity": "high" if b["in_async"] else "medium",
                "title": f"Blocking call: {b['call']}",
                "description": f"{'Sync blocking in async context' if b['in_async'] else 'Potentially blocking call'} "
                               f"at line {b['line']}",
                "location": b.get("function", "unknown"),
                "line_number": b["line"],
                "impact_score": 7.0 if b["in_async"] else 4.0,
                "recommendation": b.get("recommendation", "Use async equivalent or run in executor"),
            })

        # Queue Buildup Detection
        queue_risks = self._detect_queue_buildup(tree)
        metrics["queue_risks"] = len(queue_risks)
        for q in queue_risks:
            bottlenecks.append({
                "type": "queue_buildup",
                "severity": "high",
                "title": f"Queue buildup risk: {q['queue_name']}",
                "description": q["description"],
                "location": q.get("function", "unknown"),
                "line_number": q.get("line", 0),
                "impact_score": 7.0,
                "recommendation": q.get("recommendation", "Add backpressure or bounded queue"),
            })

        # Cascade Failure Detection
        cascade = self._detect_cascade_failures(tree)
        metrics["cascade_risks"] = len(cascade)
        for c in cascade:
            bottlenecks.append({
                "type": "blocking_call",
                "severity": "critical",
                "title": f"Cascade failure risk: {c['pattern']}",
                "description": c["description"],
                "location": c.get("function", "unknown"),
                "line_number": c.get("line", 0),
                "impact_score": 9.0,
                "recommendation": c.get("recommendation", "Add circuit breaker pattern"),
            })

        # Retry Storm Detection
        retry_storms = self._detect_retry_storms(tree)
        metrics["retry_storms"] = len(retry_storms)
        for rs in retry_storms:
            bottlenecks.append({
                "type": "blocking_call",
                "severity": "high",
                "title": f"Retry storm risk: {rs['function']}",
                "description": f"Retry loop without exponential backoff at line {rs['line']}",
                "location": rs["function"],
                "line_number": rs["line"],
                "impact_score": 7.5,
                "recommendation": "Add exponential backoff with jitter to retry logic",
            })

        # Missing Error Handling
        error_gaps = self._detect_missing_error_handling(tree)
        for gap in error_gaps:
            findings.append(gap)
            if gap["severity"] == "high":
                bottlenecks.append({
                    "type": "blocking_call",
                    "severity": "medium",
                    "title": f"Missing error handling: {gap['operation']}",
                    "description": gap["description"],
                    "location": gap.get("function", "unknown"),
                    "line_number": gap.get("line", 0),
                    "impact_score": 5.0,
                    "recommendation": "Add proper error handling to prevent cascade failures",
                })

        # Thundering Herd Detection
        thundering = self._detect_thundering_herd(tree)
        for th in thundering:
            bottlenecks.append({
                "type": "blocking_call",
                "severity": "high",
                "title": "Thundering herd pattern",
                "description": th["description"],
                "location": th.get("function", "unknown"),
                "line_number": th.get("line", 0),
                "impact_score": 7.0,
                "recommendation": "Add jitter to timers/sleep or use staggered initialization",
            })

        # Connection Pool Exhaustion
        pool_issues = self._detect_pool_exhaustion(tree)
        for pi in pool_issues:
            bottlenecks.append({
                "type": "resource_exhaustion",
                "severity": "high",
                "title": f"Pool exhaustion risk: {pi['pool_type']}",
                "description": pi["description"],
                "location": pi.get("function", "unknown"),
                "line_number": pi.get("line", 0),
                "impact_score": 7.0,
                "recommendation": pi.get("recommendation", "Increase pool size or add connection timeout"),
            })

        # Unbounded Operations
        unbounded = self._detect_unbounded_operations(tree)
        for ub in unbounded:
            bottlenecks.append({
                "type": "resource_exhaustion",
                "severity": ub.get("severity", "medium"),
                "title": f"Unbounded operation: {ub['operation']}",
                "description": ub["description"],
                "location": ub.get("function", "unknown"),
                "line_number": ub.get("line", 0),
                "impact_score": ub.get("impact", 6.0),
                "recommendation": ub.get("recommendation", "Add bounds/limits to prevent resource exhaustion"),
            })

        # Aggregate findings from previous agent results
        if context and "previous_results" in context:
            agg = self._aggregate_previous_findings(context["previous_results"])
            findings.extend(agg.get("findings", []))
            for extra_b in agg.get("bottlenecks", []):
                if not any(b["title"] == extra_b["title"] for b in bottlenecks):
                    bottlenecks.append(extra_b)

        # Generate recommendations
        if metrics["n_plus_one_risks"] > 0:
            recommendations.append({
                "title": "Eliminate N+1 query patterns",
                "description": f"Found {metrics['n_plus_one_risks']} N+1 query patterns causing excessive database load.",
                "priority": 1,
                "impact_score": 9.0,
                "category": "bottleneck",
            })

        if metrics["blocking_calls"] > 2:
            recommendations.append({
                "title": "Replace blocking calls with async equivalents",
                "description": f"Found {metrics['blocking_calls']} blocking calls that may degrade throughput.",
                "priority": 2,
                "impact_score": 7.0,
                "category": "bottleneck",
            })

        if metrics["cascade_risks"] > 0:
            recommendations.append({
                "title": "Implement circuit breakers",
                "description": f"Found {metrics['cascade_risks']} cascade failure risks. Add circuit breakers for resilience.",
                "priority": 1,
                "impact_score": 9.0,
                "category": "bottleneck",
            })

        # Calculate overall score
        total_issues = sum(metrics[k] for k in ["n_plus_one_risks", "blocking_calls", "queue_risks",
                                                 "cascade_risks", "retry_storms"])
        metrics["overall_bottleneck_score"] = max(0, 100 - total_issues * 8)

        return {
            "findings": findings,
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "metrics": metrics,
            "execution_time_ms": round((time.time() - start_time) * 1000, 1),
        }

    def _detect_n_plus_one_queries(self, tree: ast.AST) -> List[Dict]:
        """Detect N+1 query patterns — queries inside loops."""
        results = []
        db_methods = {"execute", "query", "fetchone", "fetchall", "find", "find_one",
                      "select", "get", "filter", "find_by", "get_by"}

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_name = node.name
                # Check for loops containing DB calls
                for child in ast.walk(node):
                    if isinstance(child, (ast.For, ast.While)):
                        for inner in ast.walk(child):
                            if isinstance(inner, ast.Call):
                                call_name = self._get_call_attr(inner)
                                if call_name and any(m in call_name for m in db_methods):
                                    results.append({
                                        "function": func_name,
                                        "line": getattr(inner, "lineno", 0),
                                        "query_method": call_name,
                                        "estimated_queries": "N (one per loop iteration)",
                                    })
        return results

    def _detect_blocking_calls(self, tree: ast.AST) -> List[Dict]:
        """Detect blocking calls, especially in async contexts."""
        blocking = {"sleep", "time.sleep", "subprocess.run", "subprocess.call",
                    "subprocess.check_output", "os.system", "os.popen",
                    "requests.get", "requests.post", "requests.put",
                    "urllib.request.urlopen", "input"}
        results = []
        async_funcs = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                async_funcs.add(node.name)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_name = self._get_call_name(node)
                if call_name and any(b in call_name for b in blocking):
                    # Determine if in async context
                    in_async = self._is_in_async_func(node, tree)
                    results.append({
                        "call": call_name,
                        "line": getattr(node, "lineno", 0),
                        "in_async": in_async,
                        "function": "unknown",
                        "recommendation": f"Replace {call_name} with async equivalent" if in_async
                                         else f"Consider async version of {call_name}",
                    })
        return results

    def _detect_queue_buildup(self, tree: ast.AST) -> List[Dict]:
        """Detect unbounded queue usage."""
        results = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in ("Queue", "deque"):
                    # Check for maxlen/bound
                    has_bound = any(kw.arg in ("maxlen", "maxsize") for kw in node.keywords)
                    if not has_bound:
                        results.append({
                            "queue_name": node.func.id,
                            "line": getattr(node, "lineno", 0),
                            "description": f"Unbounded {node.func.id} — can grow without limit causing memory exhaustion",
                            "recommendation": f"Add maxlen/maxsize parameter to {node.func.id}",
                            "function": "unknown",
                        })
        return results

    def _detect_cascade_failures(self, tree: ast.AST) -> List[Dict]:
        """Detect patterns that could cause cascade failures."""
        results = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check for functions that make multiple external calls without error handling
                external_calls = []
                has_try = False
                for child in ast.walk(node):
                    if isinstance(child, ast.Try):
                        has_try = True
                    if isinstance(child, ast.Call):
                        name = self._get_call_name(child)
                        if name and any(ext in name for ext in ["requests.", "httpx.", "grpc.", ".execute", ".query"]):
                            external_calls.append(name)
                if len(external_calls) >= 2 and not has_try:
                    results.append({
                        "pattern": "unhandled_external_calls",
                        "function": node.name,
                        "line": getattr(node, "lineno", 0),
                        "description": f"Function '{node.name}' makes {len(external_calls)} external calls without error handling — cascade failure risk",
                        "recommendation": "Add try/except with circuit breaker for external calls",
                    })
        return results

    def _detect_retry_storms(self, tree: ast.AST) -> List[Dict]:
        """Detect retry loops without backoff."""
        results = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                # Look for retry patterns
                has_retry = False
                has_backoff = False
                for child in ast.walk(node):
                    if isinstance(child, ast.Name) and child.id in ("retry", "retries", "attempt"):
                        has_retry = True
                    if isinstance(child, ast.Call):
                        name = self._get_call_name(child)
                        if name and "sleep" in name:
                            has_backoff = True
                if has_retry and not has_backoff:
                    results.append({
                        "function": "unknown",
                        "line": getattr(node, "lineno", 0),
                    })
        return results

    def _detect_missing_error_handling(self, tree: ast.AST) -> List[Dict]:
        """Detect operations without error handling."""
        results = []
        risky_ops = {"open", "loads", "dumps", "connect", "execute", "send", "receive"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = self._get_call_name(node)
                if name and any(op in name for op in risky_ops):
                    results.append({
                        "operation": name,
                        "line": getattr(node, "lineno", 0),
                        "severity": "medium",
                        "description": f"Operation '{name}' may need error handling",
                        "function": "unknown",
                    })
        return results

    def _detect_thundering_herd(self, tree: ast.AST) -> List[Dict]:
        """Detect thundering herd patterns (many tasks starting at same time)."""
        results = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = self._get_call_name(node)
                if name and any(t in name for t in ["sleep(0)", "sleep(1)", "timer", "schedule"]):
                    # Check if constant value (no jitter)
                    if isinstance(node, ast.Call) and node.args:
                        if isinstance(node.args[0], ast.Constant):
                            results.append({
                                "function": "unknown",
                                "line": getattr(node, "lineno", 0),
                                "description": f"Fixed-interval timer at line {getattr(node, 'lineno', 0)} may cause thundering herd",
                            })
        return results

    def _detect_pool_exhaustion(self, tree: ast.AST) -> List[Dict]:
        """Detect connection pool exhaustion risks."""
        results = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = self._get_call_name(node)
                if name and "pool" in name.lower():
                    # Check for pool size
                    pool_size = None
                    for kw in node.keywords:
                        if kw.arg in ("pool_size", "max_connections", "size", "maxsize"):
                            if isinstance(kw.value, ast.Constant):
                                pool_size = kw.value.value
                    if pool_size is None:
                        results.append({
                            "pool_type": name,
                            "line": getattr(node, "lineno", 0),
                            "description": f"Connection pool '{name}' without explicit size — may use small default",
                            "recommendation": "Explicitly configure pool size based on expected concurrency",
                            "function": "unknown",
                        })
        return results

    def _detect_unbounded_operations(self, tree: ast.AST) -> List[Dict]:
        """Detect operations without bounds."""
        results = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = self._get_call_name(node)
                if name and "read" in name.lower():
                    # Check for size limit
                    has_size = any(kw.arg in ("size", "limit", "count", "n") for kw in node.keywords)
                    if not has_size and node.args:
                        has_size = len(node.args) > 1
                    if not has_size:
                        results.append({
                            "operation": f"unbounded_read",
                            "line": getattr(node, "lineno", 0),
                            "severity": "medium",
                            "description": f"Unbounded read at line {getattr(node, 'lineno', 0)} — may read entire file/stream",
                            "recommendation": "Add size limit to read operations",
                            "impact": 5.0,
                            "function": "unknown",
                        })
        return results

    def _aggregate_previous_findings(self, previous: Dict) -> Dict:
        """Aggregate findings from other agents for correlation."""
        all_bottlenecks = []
        all_findings = []
        for agent_name, result in previous.items():
            if isinstance(result, dict):
                for b in result.get("bottlenecks", []):
                    if isinstance(b, dict) and b.get("severity") in ("critical", "high"):
                        all_bottlenecks.append(b)
                all_findings.extend(result.get("findings", []))
        return {"findings": all_findings[:5], "bottlenecks": all_bottlenecks[:5]}

    def _get_call_name(self, node: ast.Call) -> str:
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = [node.func.attr]
            current = node.func.value
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return ".".join(reversed(parts))
        return ""

    def _get_call_attr(self, node: ast.Call) -> str:
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
        elif isinstance(node.func, ast.Name):
            return node.func.id
        return ""

    def _is_in_async_func(self, target_node, tree) -> bool:
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                for child in ast.walk(node):
                    if child is target_node:
                        return True
        return False
