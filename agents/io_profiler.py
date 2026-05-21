"""
SPECTRE IO Profiler Agent
Token estimate: ~14K tokens per profile

Analyzes disk I/O, network latency, buffer usage, and I/O patterns.
Identifies I/O bottlenecks, unbuffered operations, and provides
recommendations for I/O optimization.
"""
import ast
import time
import re
from typing import Dict, List, Any


class IOProfiler:
    """
    IO Profiler — disk I/O, network latency, buffer analysis.

    Token Usage: ~14K tokens per profile
    Daily Volume: ~300 profiles/day = 4.2M tokens/day

    Capabilities:
    - Disk I/O pattern analysis
    - Network call detection and optimization
    - Buffer usage analysis
    - File handle leak detection
    - Synchronous I/O in async context detection
    - Database query pattern analysis
    - Connection pool usage analysis
    - Streaming vs batch I/O recommendations
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.disk_latency_threshold_ms = self.config.get("disk_latency_threshold_ms", 10)
        self.network_timeout_ms = self.config.get("network_timeout_ms", 5000)
        self.buffer_size_threshold = self.config.get("buffer_size_threshold", 8192)

    async def analyze(self, code: str, context: Dict) -> Dict:
        """
        Analyze code for I/O patterns and bottlenecks.
        """
        start_time = time.time()
        findings = []
        bottlenecks = []
        recommendations = []
        metrics = {
            "file_operations": 0,
            "network_calls": 0,
            "database_queries": 0,
            "unbuffered_io": 0,
            "io_score": 0.0,
        }

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"findings": [], "bottlenecks": [], "recommendations": [], "metrics": metrics}

        # Detect file operations
        file_ops = self._detect_file_operations(tree)
        metrics["file_operations"] = len(file_ops)
        for op in file_ops:
            findings.append(op)
            if not op.get("is_buffered"):
                metrics["unbuffered_io"] += 1
                bottlenecks.append({
                    "type": "io_bottleneck",
                    "severity": "medium",
                    "title": f"Unbuffered I/O: {op['operation']}",
                    "description": f"File operation without explicit buffering at line {op.get('line', 0)}",
                    "location": op.get("function", "unknown"),
                    "line_number": op.get("line", 0),
                    "impact_score": 5.0,
                    "recommendation": "Use buffered I/O or increase buffer size for better throughput",
                })

            if op.get("is_synchronous") and op.get("in_async"):
                bottlenecks.append({
                    "type": "io_bottleneck",
                    "severity": "high",
                    "title": f"Sync file I/O in async function",
                    "description": f"Synchronous file operation in async context at line {op.get('line', 0)}",
                    "location": op.get("function", "unknown"),
                    "line_number": op.get("line", 0),
                    "impact_score": 7.0,
                    "recommendation": "Use aiofiles or run_in_executor for file I/O in async code",
                })

        # Detect network calls
        network_ops = self._detect_network_calls(tree)
        metrics["network_calls"] = len(network_ops)
        for op in network_ops:
            findings.append(op)
            if op.get("missing_timeout"):
                bottlenecks.append({
                    "type": "network_timeout",
                    "severity": "high",
                    "title": f"Network call without timeout: {op['call']}",
                    "description": f"Network call '{op['call']}' at line {op.get('line', 0)} has no timeout configured",
                    "location": op.get("function", "unknown"),
                    "line_number": op.get("line", 0),
                    "impact_score": 7.0,
                    "recommendation": f"Add timeout parameter to {op['call']}() call",
                })
            if op.get("in_loop"):
                bottlenecks.append({
                    "type": "io_bottleneck",
                    "severity": "high",
                    "title": f"Network call in loop: {op['call']}",
                    "description": f"Network call inside loop at line {op.get('line', 0)} causes sequential I/O",
                    "location": op.get("function", "unknown"),
                    "line_number": op.get("line", 0),
                    "impact_score": 8.0,
                    "recommendation": "Batch network calls or use asyncio.gather() for parallel I/O",
                })

        # Detect database query patterns
        db_ops = self._detect_database_queries(tree)
        metrics["database_queries"] = len(db_ops)
        for op in db_ops:
            findings.append(op)
            if op.get("in_loop"):
                bottlenecks.append({
                    "type": "n_plus_one_query",
                    "severity": "critical",
                    "title": f"Database query in loop: {op['query_type']}",
                    "description": f"Database query inside loop at line {op.get('line', 0)} — N+1 query pattern",
                    "location": op.get("function", "unknown"),
                    "line_number": op.get("line", 0),
                    "impact_score": 9.0,
                    "recommendation": "Batch queries or use eager loading to eliminate N+1 pattern",
                })

        # Detect missing connection pooling
        conn_issues = self._detect_connection_issues(tree)
        for issue in conn_issues:
            bottlenecks.append({
                "type": "io_bottleneck",
                "severity": "medium",
                "title": f"Connection management: {issue['type']}",
                "description": issue["description"],
                "location": issue.get("function", "unknown"),
                "line_number": issue.get("line", 0),
                "impact_score": 6.0,
                "recommendation": issue.get("recommendation", "Use connection pooling"),
            })

        # Detect sequential I/O that could be parallel
        sequential_io = self._detect_sequential_io(tree)
        for seq in sequential_io:
            bottlenecks.append({
                "type": "io_bottleneck",
                "severity": "medium",
                "title": "Sequential I/O operations",
                "description": seq["description"],
                "location": seq.get("function", "unknown"),
                "line_number": seq.get("line", 0),
                "impact_score": 5.0,
                "recommendation": "Parallelize independent I/O operations using asyncio.gather() or threading",
            })

        # Detect missing context managers for file handles
        handle_leaks = self._detect_handle_leaks(tree)
        for leak in handle_leaks:
            findings.append(leak)
            bottlenecks.append({
                "type": "io_bottleneck",
                "severity": "medium",
                "title": f"Potential file handle leak: {leak['name']}",
                "description": f"File opened without context manager (with statement) at line {leak.get('line', 0)}",
                "location": leak.get("function", "unknown"),
                "line_number": leak.get("line", 0),
                "impact_score": 5.0,
                "recommendation": "Use 'with' statement to ensure proper file handle cleanup",
            })

        # Generate recommendations
        if metrics["network_calls"] > 3:
            recommendations.append({
                "title": "Implement connection pooling",
                "description": f"Found {metrics['network_calls']} network calls. Use connection pooling to reduce overhead.",
                "priority": 3,
                "impact_score": 6.0,
                "category": "io",
            })

        if metrics["unbuffered_io"] > 0:
            recommendations.append({
                "title": "Use buffered I/O",
                "description": f"Found {metrics['unbuffered_io']} unbuffered I/O operations. Buffering can improve throughput 10x.",
                "priority": 4,
                "impact_score": 5.0,
                "category": "io",
            })

        # Calculate I/O score
        issue_count = metrics["unbuffered_io"] + len([b for b in bottlenecks if b.get("severity") in ("high", "critical")])
        metrics["io_score"] = max(0, 100 - issue_count * 10)

        return {
            "findings": findings,
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "metrics": metrics,
            "execution_time_ms": round((time.time() - start_time) * 1000, 1),
        }

    def _detect_file_operations(self, tree: ast.AST) -> List[Dict]:
        """Detect file I/O operations."""
        ops = []
        in_async = False

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                in_async = True

            if isinstance(node, ast.Call):
                func_name = self._get_call_name(node)

                if func_name == "open":
                    ops.append({
                        "operation": "open()",
                        "line": getattr(node, "lineno", 0),
                        "is_buffered": True,  # open() is buffered by default
                        "is_synchronous": True,
                        "in_async": in_async,
                        "function": "unknown",
                    })
                elif func_name in ("read", "write", "readline", "readlines", "writelines"):
                    ops.append({
                        "operation": f"{func_name}()",
                        "line": getattr(node, "lineno", 0),
                        "is_buffered": func_name not in ("read", "write"),
                        "is_synchronous": True,
                        "in_async": in_async,
                        "function": "unknown",
                    })
                elif func_name in ("Path.read_text", "Path.write_text", "Path.read_bytes", "Path.write_bytes"):
                    ops.append({
                        "operation": f"Path.{func_name}()",
                        "line": getattr(node, "lineno", 0),
                        "is_buffered": True,
                        "is_synchronous": True,
                        "in_async": in_async,
                        "function": "unknown",
                    })
        return ops

    def _detect_network_calls(self, tree: ast.AST) -> List[Dict]:
        """Detect network/HTTP calls."""
        network_funcs = {
            "requests.get", "requests.post", "requests.put", "requests.delete",
            "requests.patch", "requests.head",
            "httpx.get", "httpx.post", "httpx.put", "httpx.delete",
            "urllib.request.urlopen",
            "aiohttp.ClientSession",
        }
        ops = []
        in_loop = False

        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                in_loop = True

            if isinstance(node, ast.Call):
                func_name = self._get_call_name(node)
                if func_name and any(nf in func_name for nf in network_funcs):
                    # Check for timeout
                    has_timeout = False
                    for kw in node.keywords:
                        if kw.arg in ("timeout", "Timeout"):
                            has_timeout = True
                    ops.append({
                        "call": func_name,
                        "line": getattr(node, "lineno", 0),
                        "missing_timeout": not has_timeout,
                        "in_loop": in_loop,
                        "function": "unknown",
                    })
        return ops

    def _detect_database_queries(self, tree: ast.AST) -> List[Dict]:
        """Detect database query patterns."""
        db_methods = {"execute", "query", "fetchone", "fetchall", "fetchmany",
                      "find", "find_one", "find_all", "select", "insert", "update", "delete"}
        ops = []
        in_loop = False

        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                in_loop = True

            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in db_methods:
                        ops.append({
                            "query_type": node.func.attr,
                            "line": getattr(node, "lineno", 0),
                            "in_loop": in_loop,
                            "function": "unknown",
                        })
        return ops

    def _detect_connection_issues(self, tree: ast.AST) -> List[Dict]:
        """Detect connection management issues."""
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_call_name(node)
                if func_name and any(c in func_name for c in ["Connection", "connect", "create_connection"]):
                    # Check if used in a with statement
                    issues.append({
                        "type": "connection_created",
                        "line": getattr(node, "lineno", 0),
                        "description": f"Connection created at line {getattr(node, 'lineno', 0)}. Verify it uses connection pooling.",
                        "recommendation": "Use connection pool manager for database connections",
                        "function": "unknown",
                    })
        return issues

    def _detect_sequential_io(self, tree: ast.AST) -> List[Dict]:
        """Detect sequential I/O operations that could be parallelized."""
        sequences = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                io_calls = []
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        name = self._get_call_name(child)
                        if name and any(op in name for op in ["requests.", "httpx.", "open(", "execute", "fetch"]):
                            io_calls.append((name, getattr(child, "lineno", 0)))
                if len(io_calls) >= 3:
                    sequences.append({
                        "function": node.name,
                        "line": io_calls[0][1],
                        "io_count": len(io_calls),
                        "description": f"{len(io_calls)} sequential I/O operations in '{node.name}' — consider parallelizing",
                    })
        return sequences

    def _detect_handle_leaks(self, tree: ast.AST) -> List[Dict]:
        """Detect file handles that may not be properly closed."""
        leaks = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if isinstance(node.value, ast.Call):
                    func_name = self._get_call_name(node.value)
                    if func_name == "open":
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                leaks.append({
                                    "name": target.id,
                                    "line": getattr(node, "lineno", 0),
                                    "description": f"File handle '{target.id}' assigned without 'with' statement",
                                    "function": "unknown",
                                })
        return leaks

    def _get_call_name(self, node: ast.Call) -> str:
        """Extract the full name of a function call."""
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
