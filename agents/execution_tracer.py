"""
SPECTRE Execution Tracer Agent
Token estimate: ~18K tokens per profile

Analyzes execution paths, call stacks, and hot paths in application code.
Identifies frequently executed code paths, deep call chains, and
execution bottlenecks that impact runtime performance.
"""
import re
import ast
import time
from typing import Dict, List, Any, Optional
from collections import defaultdict


class ExecutionTracer:
    """
    Execution Tracer — analyzes call stacks, execution paths, and hot paths.

    Token Usage: ~18K tokens per profile
    Daily Volume: ~700 profiles/day = 12.6M tokens/day

    Capabilities:
    - Call stack depth analysis
    - Hot path detection (frequently executed code paths)
    - Execution flow tracing
    - Recursive call detection
    - Cyclomatic complexity analysis
    - Function call frequency estimation
    - Dead code detection
    - Entry point identification
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.trace_depth = self.config.get("trace_depth", 50)
        self.hot_path_threshold_ms = self.config.get("hot_path_threshold_ms", 10)
        self.complexity_threshold = self.config.get("complexity_threshold", 10)
        self._call_graph = defaultdict(set)
        self._function_registry = {}

    async def analyze(self, code: str, context: Dict) -> Dict:
        """
        Analyze code for execution path patterns and hot paths.

        Returns dict with:
        - findings: list of execution path findings
        - bottlenecks: list of detected bottlenecks
        - recommendations: optimization suggestions
        - metrics: execution path metrics
        """
        start_time = time.time()
        findings = []
        bottlenecks = []
        recommendations = []
        metrics = {
            "total_functions": 0,
            "max_call_depth": 0,
            "avg_complexity": 0.0,
            "hot_paths": [],
            "recursive_functions": [],
            "dead_code_candidates": [],
        }

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {
                "findings": [{"type": "error", "message": "Unable to parse code"}],
                "bottlenecks": [],
                "recommendations": [],
                "metrics": metrics,
            }

        # Extract all function definitions
        functions = self._extract_functions(tree)
        metrics["total_functions"] = len(functions)

        # Build call graph
        self._build_call_graph(tree)

        # Analyze each function
        complexities = []
        for func_name, func_node in functions.items():
            # Cyclomatic complexity
            complexity = self._calculate_complexity(func_node)
            complexities.append(complexity)

            # Call depth analysis
            depth = self._estimate_call_depth(func_node)
            metrics["max_call_depth"] = max(metrics["max_call_depth"], depth)

            # Hot path detection
            is_hot = self._is_hot_path(func_node, code)
            if is_hot:
                metrics["hot_paths"].append({
                    "function": func_name,
                    "line": func_node.lineno,
                    "complexity": complexity,
                    "estimated_calls_per_request": self._estimate_call_frequency(func_node),
                })

            # Recursive detection
            if self._is_recursive(func_name, func_node):
                metrics["recursive_functions"].append({
                    "function": func_name,
                    "line": func_node.lineno,
                    "depth_estimate": depth,
                })

            # High complexity finding
            if complexity > self.complexity_threshold:
                findings.append({
                    "type": "high_complexity",
                    "function": func_name,
                    "line": func_node.lineno,
                    "complexity": complexity,
                    "message": f"Function '{func_name}' has cyclomatic complexity {complexity} (threshold: {self.complexity_threshold})",
                })
                bottlenecks.append({
                    "type": "blocking_call",
                    "severity": "high" if complexity > 20 else "medium",
                    "title": f"High complexity: {func_name}",
                    "description": f"Cyclomatic complexity of {complexity} indicates complex execution path",
                    "location": func_name,
                    "line_number": func_node.lineno,
                    "impact_score": min(10, complexity / 3),
                    "recommendation": f"Refactor '{func_name}' into smaller functions to reduce complexity",
                })

            # Deep call chain
            if depth > self.trace_depth:
                findings.append({
                    "type": "deep_call_chain",
                    "function": func_name,
                    "depth": depth,
                    "message": f"Deep call chain detected: {depth} levels in '{func_name}'",
                })
                bottlenecks.append({
                    "type": "blocking_call",
                    "severity": "medium",
                    "title": f"Deep call chain: {func_name}",
                    "description": f"Call depth of {depth} may cause stack issues and performance degradation",
                    "location": func_name,
                    "line_number": func_node.lineno,
                    "impact_score": min(8, depth / 5),
                    "recommendation": f"Flatten call hierarchy in '{func_name}' or use iterative approach",
                })

        # Detect potential dead code
        dead_code = self._detect_dead_code(tree, functions)
        metrics["dead_code_candidates"] = dead_code
        if dead_code:
            findings.append({
                "type": "dead_code",
                "count": len(dead_code),
                "functions": [d["name"] for d in dead_code],
                "message": f"{len(dead_code)} potentially unused functions detected",
            })

        # Detect string concatenation in loops
        string_concat_issues = self._detect_string_concat_in_loops(tree)
        for issue in string_concat_issues:
            bottlenecks.append({
                "type": "blocking_call",
                "severity": "medium",
                "title": f"String concatenation in loop",
                "description": issue["message"],
                "location": issue.get("function", "unknown"),
                "line_number": issue.get("line", 0),
                "impact_score": 6.0,
                "recommendation": "Use join() or f-strings for string building in loops",
            })

        # Detect nested loops
        nested_loops = self._detect_nested_loops(tree)
        for loop in nested_loops:
            if loop["depth"] >= 3:
                bottlenecks.append({
                    "type": "blocking_call",
                    "severity": "high",
                    "title": f"Deeply nested loop (depth {loop['depth']})",
                    "description": f"O(n^{loop['depth']}) complexity at line {loop['line']}",
                    "location": loop.get("function", "unknown"),
                    "line_number": loop["line"],
                    "impact_score": min(10, loop["depth"] * 2.5),
                    "recommendation": "Consider algorithmic optimization or data structure changes",
                })

        # Calculate average complexity
        if complexities:
            metrics["avg_complexity"] = round(sum(complexities) / len(complexities), 1)

        # Generate recommendations
        if metrics["avg_complexity"] > 8:
            recommendations.append({
                "title": "Reduce overall code complexity",
                "description": f"Average cyclomatic complexity is {metrics['avg_complexity']}. Consider applying the Single Responsibility Principle.",
                "priority": 3,
                "impact_score": 7.0,
                "category": "execution",
            })

        if metrics["recursive_functions"]:
            recommendations.append({
                "title": "Review recursive functions for memoization",
                "description": f"Found {len(metrics['recursive_functions'])} recursive functions that may benefit from memoization or iteration.",
                "priority": 4,
                "impact_score": 6.0,
                "category": "execution",
            })

        if dead_code:
            recommendations.append({
                "title": "Remove dead code",
                "description": f"{len(dead_code)} potentially unused functions found. Removing them reduces codebase size and improves maintainability.",
                "priority": 7,
                "impact_score": 3.0,
                "category": "execution",
            })

        return {
            "findings": findings,
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "metrics": metrics,
            "execution_time_ms": round((time.time() - start_time) * 1000, 1),
        }

    def _extract_functions(self, tree: ast.AST) -> Dict[str, ast.AST]:
        """Extract all function/method definitions from AST."""
        functions = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions[node.name] = node
        return functions

    def _build_call_graph(self, tree: ast.AST):
        """Build a call graph from the AST."""
        self._call_graph.clear()
        current_func = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                current_func = node.name
                self._call_graph[current_func] = set()
            elif isinstance(node, ast.Call) and current_func:
                if isinstance(node.func, ast.Name):
                    self._call_graph[current_func].add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    self._call_graph[current_func].add(node.func.attr)

    def _calculate_complexity(self, func_node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                complexity += 1
            elif isinstance(node, ast.Assert):
                complexity += 1
            elif isinstance(node, ast.comprehension):
                if node.ifs:
                    complexity += len(node.ifs)
        return complexity

    def _estimate_call_depth(self, func_node: ast.AST, visited: set = None) -> int:
        """Estimate maximum call depth."""
        if visited is None:
            visited = set()
        if func_node.name in visited:
            return 0
        visited.add(func_node.name)

        max_depth = 0
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                callee = None
                if isinstance(node.func, ast.Name):
                    callee = node.func.id
                if callee and callee in self._call_graph:
                    depth = 1 + self._estimate_call_depth_by_name(callee, visited)
                    max_depth = max(max_depth, depth)
        return max_depth

    def _estimate_call_depth_by_name(self, func_name: str, visited: set) -> int:
        """Estimate call depth by function name."""
        if func_name in visited:
            return 0
        visited.add(func_name)
        if func_name in self._call_graph:
            return 1 + max(
                (self._estimate_call_depth_by_name(c, visited) for c in self._call_graph[func_name]),
                default=0
            )
        return 0

    def _is_hot_path(self, func_node: ast.AST, code: str) -> bool:
        """Determine if a function is likely on a hot path."""
        indicators = 0
        # Called in loops
        for node in ast.walk(func_node):
            if isinstance(node, (ast.For, ast.While)):
                indicators += 2
        # Has many calls
        call_count = sum(1 for node in ast.walk(func_node) if isinstance(node, ast.Call))
        if call_count > 5:
            indicators += 1
        # Name suggests hot path
        name = func_node.name.lower()
        hot_names = ["process", "handle", "execute", "run", "tick", "update", "render", "compute", "calculate"]
        if any(h in name for h in hot_names):
            indicators += 1
        return indicators >= 2

    def _estimate_call_frequency(self, func_node: ast.AST) -> int:
        """Estimate how many times a function might be called per request."""
        freq = 1
        for node in ast.walk(func_node):
            if isinstance(node, (ast.For, ast.While)):
                freq *= 10
            if isinstance(node, ast.Call):
                freq += 1
        return freq

    def _is_recursive(self, func_name: str, func_node: ast.AST) -> bool:
        """Check if a function is recursive."""
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == func_name:
                    return True
        return False

    def _detect_dead_code(self, tree: ast.AST, functions: Dict) -> List[Dict]:
        """Detect potentially unused functions."""
        all_calls = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    all_calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    all_calls.add(node.func.attr)

        dead = []
        for name in functions:
            if name.startswith("_") or name.startswith("test_"):
                continue
            if name not in all_calls and name != "main":
                dead.append({"name": name, "line": functions[name].lineno})
        return dead

    def _detect_string_concat_in_loops(self, tree: ast.AST) -> List[Dict]:
        """Detect string concatenation inside loops."""
        issues = []
        loop_stack = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                loop_stack.append(node)
                for child in ast.walk(node):
                    if isinstance(child, ast.AugAssign) and isinstance(child.op, ast.Add):
                        issues.append({
                            "message": "String concatenation with += inside a loop (use join instead)",
                            "line": getattr(child, "lineno", 0),
                            "function": "unknown",
                        })
                loop_stack.pop()
        return issues

    def _detect_nested_loops(self, tree: ast.AST) -> List[Dict]:
        """Detect nested loops."""
        results = []
        loops = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                depth = 1
                for inner in ast.walk(node):
                    if inner is not node and isinstance(inner, (ast.For, ast.While)):
                        depth += 1
                if depth >= 2:
                    results.append({
                        "depth": depth,
                        "line": getattr(node, "lineno", 0),
                        "function": "unknown",
                    })
        return results
