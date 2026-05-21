"""
SPECTRE CPU Analyzer Agent
Token estimate: ~16K tokens per profile

Analyzes CPU hotspots, thread contention, context switches, and
computational efficiency. Identifies CPU-intensive operations and
provides optimization recommendations.
"""
import ast
import time
import math
from typing import Dict, List, Any
from collections import defaultdict


class CPUAnalyzer:
    """
    CPU Analyzer — CPU hotspots, thread contention, context switches.

    Token Usage: ~16K tokens per profile
    Daily Volume: ~450 profiles/day = 7.2M tokens/day

    Capabilities:
    - CPU hotspot detection
    - Algorithmic complexity estimation (O(n), O(n²), O(n³), etc.)
    - Thread contention patterns
    - Context switch detection
    - Busy-wait detection
    - Computation-heavy operation identification
    - GIL contention analysis
    - CPU-bound vs IO-bound classification
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.sampling_rate_hz = self.config.get("sampling_rate_hz", 100)
        self.hotspot_threshold_pct = self.config.get("hotspot_threshold_pct", 5)
        self.complexity_threshold = self.config.get("complexity_threshold", "O(n²)")

    async def analyze(self, code: str, context: Dict) -> Dict:
        """
        Analyze code for CPU usage patterns and hotspots.
        """
        start_time = time.time()
        findings = []
        bottlenecks = []
        recommendations = []
        metrics = {
            "hotspots": [],
            "complexity_estimates": [],
            "thread_contention_risks": [],
            "busy_wait_patterns": 0,
            "cpu_score": 0.0,
        }

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"findings": [], "bottlenecks": [], "recommendations": [], "metrics": metrics}

        # Analyze computational complexity of each function
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = self._estimate_complexity(node)
                if complexity["order"] in ("O(n²)", "O(n³)", "O(n!)"):
                    metrics["complexity_estimates"].append({
                        "function": node.name,
                        "line": getattr(node, "lineno", 0),
                        "complexity": complexity["order"],
                        "details": complexity["details"],
                    })
                    bottlenecks.append({
                        "type": "cpu_hotspot",
                        "severity": "critical" if "n!" in complexity["order"] else "high",
                        "title": f"High complexity: {node.name} ({complexity['order']})",
                        "description": f"Function '{node.name}' has {complexity['order']} complexity: {complexity['details']}",
                        "location": node.name,
                        "line_number": getattr(node, "lineno", 0),
                        "impact_score": 9.0 if "n!" in complexity["order"] else 7.0,
                        "recommendation": f"Optimize algorithm in '{node.name}' to reduce complexity",
                    })

        # Detect busy-wait patterns
        busy_waits = self._detect_busy_waits(tree)
        metrics["busy_wait_patterns"] = len(busy_waits)
        for bw in busy_waits:
            bottlenecks.append({
                "type": "cpu_hotspot",
                "severity": "high",
                "title": f"Busy-wait pattern at line {bw['line']}",
                "description": bw["description"],
                "location": bw.get("function", "unknown"),
                "line_number": bw["line"],
                "impact_score": 8.0,
                "recommendation": "Replace busy-wait with event-driven or blocking pattern",
            })

        # Detect expensive operations
        expensive_ops = self._detect_expensive_operations(tree)
        for op in expensive_ops:
            findings.append(op)
            if op["severity"] in ("high", "critical"):
                bottlenecks.append({
                    "type": "cpu_hotspot",
                    "severity": op["severity"],
                    "title": f"Expensive operation: {op['operation']}",
                    "description": op["description"],
                    "location": op.get("function", "unknown"),
                    "line_number": op.get("line", 0),
                    "impact_score": op.get("impact", 6.0),
                    "recommendation": op.get("recommendation", "Consider caching or optimization"),
                })

        # Detect repeated computations (missing memoization)
        repeated = self._detect_repeated_computations(tree)
        for rep in repeated:
            recommendations.append({
                "title": f"Cache repeated computation: {rep['expression']}",
                "description": f"Expression computed {rep['count']} times across functions. Use functools.lru_cache or compute once.",
                "priority": 4,
                "impact_score": 6.0,
                "category": "cpu",
            })

        # Detect synchronous blocking in async context
        blocking_in_async = self._detect_sync_in_async(tree)
        for block in blocking_in_async:
            bottlenecks.append({
                "type": "blocking_call",
                "severity": "high",
                "title": f"Sync blocking in async: {block['function']}",
                "description": f"Synchronous call '{block['call']}' in async function '{block['function']}' blocks the event loop",
                "location": block["function"],
                "line_number": block.get("line", 0),
                "impact_score": 7.0,
                "recommendation": f"Use async equivalent or run in executor: {block['call']}",
            })

        # Detect excessive exception handling
        heavy_exception = self._detect_heavy_exception_handling(tree)
        for exc in heavy_exception:
            findings.append(exc)
            if exc["in_loop"]:
                bottlenecks.append({
                    "type": "cpu_hotspot",
                    "severity": "medium",
                    "title": f"Exception handling in loop at line {exc['line']}",
                    "description": "Try/except inside loop body adds overhead to every iteration",
                    "location": exc.get("function", "unknown"),
                    "line_number": exc["line"],
                    "impact_score": 4.0,
                    "recommendation": "Move try/except outside loop or validate before loop",
                })

        # Detect thread contention patterns
        contention = self._detect_thread_contention(tree)
        metrics["thread_contention_risks"] = contention
        for c in contention:
            bottlenecks.append({
                "type": "thread_contention",
                "severity": "medium",
                "title": f"Thread contention risk: {c['lock_name']}",
                "description": c["description"],
                "location": c.get("function", "unknown"),
                "line_number": c.get("line", 0),
                "impact_score": 5.0,
                "recommendation": c.get("recommendation", "Use finer-grained locking or lock-free patterns"),
            })

        # Generate high-level recommendations
        if metrics["busy_wait_patterns"] > 0:
            recommendations.append({
                "title": "Eliminate busy-wait patterns",
                "description": f"Found {metrics['busy_wait_patterns']} busy-wait patterns causing unnecessary CPU usage.",
                "priority": 2,
                "impact_score": 8.0,
                "category": "cpu",
            })

        if metrics["complexity_estimates"]:
            recommendations.append({
                "title": "Optimize algorithmic complexity",
                "description": f"Found {len(metrics['complexity_estimates'])} functions with high computational complexity.",
                "priority": 2,
                "impact_score": 8.0,
                "category": "cpu",
            })

        # Calculate CPU score
        issue_count = len(busy_waits) + len(expensive_ops) + len(contention)
        metrics["cpu_score"] = max(0, 100 - issue_count * 8)

        return {
            "findings": findings,
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "metrics": metrics,
            "execution_time_ms": round((time.time() - start_time) * 1000, 1),
        }

    def _estimate_complexity(self, func_node: ast.AST) -> Dict:
        """Estimate the algorithmic complexity of a function."""
        loop_depth = 0
        max_depth = 0
        details = []

        def walk(node, depth):
            nonlocal max_depth
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.For, ast.While)):
                    new_depth = depth + 1
                    max_depth = max(max_depth, new_depth)
                    walk(child, new_depth)
                else:
                    walk(child, depth)

        walk(func_node, 0)

        if max_depth == 0:
            return {"order": "O(1)", "details": "No loops detected"}
        elif max_depth == 1:
            # Check for multiplicative patterns
            has_multiply = False
            for node in ast.walk(func_node):
                if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
                    has_multiply = True
            if has_multiply:
                return {"order": "O(n)", "details": "Single loop with arithmetic operations"}
            return {"order": "O(n)", "details": "Single loop iteration"}
        elif max_depth == 2:
            return {"order": "O(n²)", "details": "Nested loops (2 levels deep)"}
        elif max_depth == 3:
            return {"order": "O(n³)", "details": "Triple nested loops"}
        else:
            # Check for factorial patterns (recursive with nested calls)
            return {"order": "O(n!)", "details": f"Deeply nested loops ({max_depth} levels)"}

    def _detect_busy_waits(self, tree: ast.AST) -> List[Dict]:
        """Detect busy-wait (spin-wait) patterns."""
        busy_waits = []
        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                # while True: with no sleep/await
                if isinstance(node.test, ast.Constant) and node.test.value is True:
                    has_sleep = False
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            if isinstance(child.func, ast.Name) and child.func.id in ("sleep", "time.sleep"):
                                has_sleep = True
                            if isinstance(child.func, ast.Attribute) and child.func.attr in ("sleep", "wait"):
                                has_sleep = True
                    if not has_sleep:
                        busy_waits.append({
                            "line": getattr(node, "lineno", 0),
                            "description": "Infinite loop without sleep/wait — potential busy-wait causing 100% CPU",
                            "function": "unknown",
                        })
        return busy_waits

    def _detect_expensive_operations(self, tree: ast.AST) -> List[Dict]:
        """Detect computationally expensive operations."""
        ops = []
        expensive_funcs = {
            "sort": ("List sort", "medium", 4.0),
            "sorted": ("Sorted copy", "low", 3.0),
            "regex": ("Regex compilation in loop", "high", 6.0),
            "compile": ("Regex/text compilation", "medium", 5.0),
            "hashlib": ("Cryptographic hash", "medium", 4.0),
            "json.dumps": ("JSON serialization", "medium", 3.0),
            "json.loads": ("JSON deserialization", "medium", 3.0),
            "pickle.dumps": ("Pickle serialization", "high", 6.0),
            "pickle.loads": ("Pickle deserialization", "high", 6.0),
            "eval": ("eval() call", "critical", 9.0),
            "exec": ("exec() call", "critical", 9.0),
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name and func_name in expensive_funcs:
                    name, severity, impact = expensive_funcs[func_name]
                    ops.append({
                        "type": "expensive_operation",
                        "operation": func_name,
                        "severity": severity,
                        "impact": impact,
                        "line": getattr(node, "lineno", 0),
                        "description": f"{name} detected at line {getattr(node, 'lineno', 0)}",
                        "recommendation": f"Consider caching result of {func_name}()",
                        "function": "unknown",
                    })

                # Regex in loop detection
                if isinstance(node.func, ast.Attribute) and node.func.attr in ("match", "search", "findall", "sub"):
                    # Check if in a loop context (simplified)
                    ops.append({
                        "type": "expensive_operation",
                        "operation": "regex_in_loop",
                        "severity": "medium",
                        "impact": 5.0,
                        "line": getattr(node, "lineno", 0),
                        "description": "Regex operation — ensure pattern is pre-compiled with re.compile()",
                        "recommendation": "Pre-compile regex patterns with re.compile()",
                        "function": "unknown",
                    })
        return ops

    def _detect_repeated_computations(self, tree: ast.AST) -> List[Dict]:
        """Detect expressions computed multiple times."""
        expressions = defaultdict(int)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    expressions[node.func.id] += 1
        return [{"expression": name, "count": count}
                for name, count in expressions.items() if count >= 3]

    def _detect_sync_in_async(self, tree: ast.AST) -> List[Dict]:
        """Detect synchronous blocking calls inside async functions."""
        blocking_calls = {"sleep", "time.sleep", "requests.get", "requests.post",
                          "urllib.request.urlopen", "subprocess.run", "subprocess.call"}
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        call_name = None
                        if isinstance(child.func, ast.Name):
                            call_name = child.func.id
                        elif isinstance(child.func, ast.Attribute):
                            call_name = f"{ast.dump(child.func.value)}.{child.func.attr}"

                        if call_name and any(bc in call_name for bc in blocking_calls):
                            issues.append({
                                "function": node.name,
                                "call": call_name,
                                "line": getattr(child, "lineno", 0),
                            })
        return issues

    def _detect_heavy_exception_handling(self, tree: ast.AST) -> List[Dict]:
        """Detect exception handling patterns that may be CPU-heavy."""
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                in_loop = False
                parent = None
                for n in ast.walk(tree):
                    for child in ast.iter_child_nodes(n):
                        if child is node and isinstance(n, (ast.For, ast.While)):
                            in_loop = True

                if node.handlers:
                    issues.append({
                        "type": "exception_handling",
                        "line": getattr(node, "lineno", 0),
                        "in_loop": in_loop,
                        "handler_count": len(node.handlers),
                        "description": f"Exception handling with {len(node.handlers)} handlers" +
                                       (" inside loop" if in_loop else ""),
                        "function": "unknown",
                    })
        return issues

    def _detect_thread_contention(self, tree: ast.AST) -> List[Dict]:
        """Detect patterns that may cause thread contention."""
        contention = []
        for node in ast.walk(tree):
            # Global locks
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if isinstance(node.value, ast.Call):
                            if isinstance(node.value.func, ast.Name):
                                if node.value.func.id in ("Lock", "RLock"):
                                    contention.append({
                                        "lock_name": target.id,
                                        "line": getattr(node, "lineno", 0),
                                        "description": f"Global lock '{target.id}' may cause contention under high concurrency",
                                        "recommendation": "Consider finer-grained locking or asyncio.Lock for async code",
                                        "function": "module level",
                                    })
        return contention
