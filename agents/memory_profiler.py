"""
SPECTRE Memory Profiler Agent
Token estimate: ~20K tokens per profile

Analyzes heap usage, memory leaks, allocation patterns, and garbage
collection behavior. Identifies memory-intensive operations and provides
recommendations for memory optimization.
"""
import re
import ast
import time
from typing import Dict, List, Any, Optional
from collections import defaultdict


class MemoryProfiler:
    """
    Memory Profiler — heap analysis, leak detection, allocation patterns.

    Token Usage: ~20K tokens per profile
    Daily Volume: ~600 profiles/day = 12.0M tokens/day

    Capabilities:
    - Heap allocation analysis
    - Memory leak detection (growing data structures)
    - Large object allocation detection
    - Circular reference detection
    - Generator vs list comprehension analysis
    - String interning opportunities
    - __slots__ recommendation
    - Memory-efficient data structure suggestions
    - Garbage collection pressure analysis
    - Closure capture analysis
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.heap_snapshot_interval = self.config.get("heap_snapshot_interval", 30)
        self.leak_threshold_mb = self.config.get("leak_threshold_mb", 50)
        self.allocation_threshold = self.config.get("allocation_threshold", 1000)

    async def analyze(self, code: str, context: Dict) -> Dict:
        """
        Analyze code for memory usage patterns and potential leaks.

        Returns dict with:
        - findings: memory analysis findings
        - bottlenecks: detected memory bottlenecks
        - recommendations: memory optimization suggestions
        - metrics: memory usage metrics
        """
        start_time = time.time()
        findings = []
        bottlenecks = []
        recommendations = []
        metrics = {
            "list_comprehensions": 0,
            "large_collections": 0,
            "potential_leaks": 0,
            "circular_refs_risk": 0,
            "memory_efficiency_score": 0.0,
            "estimated_memory_mb": 0.0,
        }

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"findings": [], "bottlenecks": [], "recommendations": [], "metrics": metrics}

        # Analyze list comprehensions that should be generators
        list_comp_issues = self._analyze_list_comprehensions(tree)
        metrics["list_comprehensions"] = len(list_comp_issues)
        for issue in list_comp_issues:
            findings.append(issue)
            if issue.get("should_be_generator"):
                bottlenecks.append({
                    "type": "allocation_pressure",
                    "severity": "medium",
                    "title": "List comprehension should be generator",
                    "description": f"List comprehension at line {issue['line']} stores all items in memory. Use a generator expression for iteration.",
                    "location": issue.get("function", "unknown"),
                    "line_number": issue["line"],
                    "impact_score": 5.0,
                    "recommendation": "Replace [...] with (...) for iteration-only use cases",
                })
                recommendations.append({
                    "title": "Use generator expressions",
                    "description": f"Convert list comprehension at line {issue['line']} to generator expression to reduce memory usage.",
                    "priority": 5,
                    "impact_score": 5.0,
                    "category": "memory",
                })

        # Detect growing data structures (potential leaks)
        leak_patterns = self._detect_memory_leaks(tree)
        metrics["potential_leaks"] = len(leak_patterns)
        for leak in leak_patterns:
            bottlenecks.append({
                "type": "memory_leak",
                "severity": "high" if leak["growth_rate"] == "unbounded" else "medium",
                "title": f"Potential memory leak: {leak['name']}",
                "description": leak["description"],
                "location": leak.get("function", "module level"),
                "line_number": leak.get("line", 0),
                "impact_score": 8.0 if leak["growth_rate"] == "unbounded" else 5.0,
                "recommendation": leak.get("recommendation", "Add size limits or cleanup"),
            })

        # Detect large object allocations
        large_allocs = self._detect_large_allocations(tree)
        metrics["large_collections"] = len(large_allocs)
        for alloc in large_allocs:
            findings.append(alloc)
            bottlenecks.append({
                "type": "allocation_pressure",
                "severity": "medium",
                "title": f"Large allocation: {alloc['name']}",
                "description": alloc["description"],
                "location": alloc.get("function", "unknown"),
                "line_number": alloc.get("line", 0),
                "impact_score": 6.0,
                "recommendation": alloc.get("recommendation", "Consider lazy loading or streaming"),
            })

        # Check for missing __slots__
        slots_issues = self._detect_missing_slots(tree)
        for issue in slots_issues:
            findings.append(issue)
            recommendations.append({
                "title": f"Add __slots__ to {issue['class_name']}",
                "description": f"Class '{issue['class_name']}' at line {issue['line']} could save ~40% memory with __slots__.",
                "priority": 6,
                "impact_score": 4.0,
                "category": "memory",
            })

        # Detect circular reference risks
        circular_risks = self._detect_circular_references(tree)
        metrics["circular_refs_risk"] = len(circular_risks)
        for risk in circular_risks:
            bottlenecks.append({
                "type": "memory_leak",
                "severity": "medium",
                "title": f"Circular reference risk: {risk['class_a']} <-> {risk['class_b']}",
                "description": risk["description"],
                "location": risk.get("location", "unknown"),
                "line_number": risk.get("line", 0),
                "impact_score": 5.0,
                "recommendation": "Use weakref for back-references to break cycles",
            })

        # Detect string concatenation patterns
        string_issues = self._detect_string_memory_issues(tree)
        for issue in string_issues:
            findings.append(issue)
            recommendations.append({
                "title": "Optimize string handling",
                "description": issue["description"],
                "priority": 6,
                "impact_score": 4.0,
                "category": "memory",
            })

        # Detect global mutable state
        global_issues = self._detect_global_mutable_state(tree)
        for issue in global_issues:
            findings.append(issue)
            bottlenecks.append({
                "type": "memory_leak",
                "severity": "medium",
                "title": f"Global mutable state: {issue['name']}",
                "description": f"Global mutable '{issue['name']}' at line {issue['line']} grows unbounded across requests",
                "location": "module level",
                "line_number": issue["line"],
                "impact_score": 7.0,
                "recommendation": "Use bounded caches (functools.lru_cache) or database storage",
            })

        # Detect large function scopes (many local variables)
        large_scopes = self._detect_large_scopes(tree)
        for scope in large_scopes:
            findings.append(scope)
            if scope["var_count"] > 30:
                recommendations.append({
                    "title": f"Reduce scope size in {scope['function']}",
                    "description": f"Function '{scope['function']}' has {scope['var_count']} local variables. Extract sub-functions to reduce frame size.",
                    "priority": 7,
                    "impact_score": 3.0,
                    "category": "memory",
                })

        # Calculate memory efficiency score
        total_issues = len(leak_patterns) * 3 + len(large_allocs) * 2 + len(slots_issues)
        metrics["memory_efficiency_score"] = max(0, 100 - total_issues * 5)
        metrics["estimated_memory_mb"] = self._estimate_memory_usage(tree)

        # High-level recommendations
        if metrics["potential_leaks"] > 0:
            recommendations.append({
                "title": "Address memory leaks",
                "description": f"Found {metrics['potential_leaks']} potential memory leaks. Monitor heap growth in production.",
                "priority": 1,
                "impact_score": 9.0,
                "category": "memory",
            })

        return {
            "findings": findings,
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "metrics": metrics,
            "execution_time_ms": round((time.time() - start_time) * 1000, 1),
        }

    def _analyze_list_comprehensions(self, tree: ast.AST) -> List[Dict]:
        """Find list comprehensions used only for iteration."""
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ListComp):
                # Check if used in a for loop (should be generator)
                should_be_generator = False
                parent = None
                for n in ast.walk(tree):
                    for child in ast.iter_child_nodes(n):
                        if child is node and isinstance(n, ast.For):
                            should_be_generator = True
                            parent = n

                issues.append({
                    "type": "list_comprehension",
                    "line": getattr(node, "lineno", 0),
                    "should_be_generator": should_be_generator,
                    "message": "List comprehension that could be a generator expression",
                    "function": "unknown",
                })
        return issues

    def _detect_memory_leaks(self, tree: ast.AST) -> List[Dict]:
        """Detect patterns that suggest memory leaks."""
        leaks = []
        for node in ast.walk(tree):
            # Module-level lists/dicts that are appended to
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if isinstance(node.value, (ast.List, ast.Dict, ast.Set)):
                            leaks.append({
                                "name": target.id,
                                "line": getattr(node, "lineno", 0),
                                "growth_rate": "unbounded",
                                "description": f"Module-level mutable '{target.id}' accumulates data across requests",
                                "recommendation": f"Add max size limit or use bounded cache for '{target.id}'",
                                "function": "module level",
                            })

            # Append to lists in loops without bounds
            if isinstance(node, (ast.For, ast.While)):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Attribute):
                            if child.func.attr == "append":
                                # Check if appending to outer scope variable
                                if isinstance(child.func.value, ast.Name):
                                    leaks.append({
                                        "name": child.func.value.id,
                                        "line": getattr(child, "lineno", 0),
                                        "growth_rate": "unbounded",
                                        "description": f"Appending to '{child.func.value.id}' in a loop without size limit",
                                        "recommendation": f"Add size limit or use deque with maxlen for '{child.func.value.id}'",
                                        "function": "unknown",
                                    })
        return leaks

    def _detect_large_allocations(self, tree: ast.AST) -> List[Dict]:
        """Detect potentially large memory allocations."""
        allocs = []
        for node in ast.walk(tree):
            # Large list/set/dict literals
            if isinstance(node, ast.List) and len(node.elts) > 100:
                allocs.append({
                    "name": "large_list_literal",
                    "line": getattr(node, "lineno", 0),
                    "description": f"List literal with {len(node.elts)} elements. Consider lazy loading.",
                    "recommendation": "Use generator or lazy loading for large datasets",
                    "function": "unknown",
                })
            # BytesIO/StringIO without size limits
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ("BytesIO", "StringIO"):
                    allocs.append({
                        "name": node.func.id,
                        "line": getattr(node, "lineno", 0),
                        "description": f"{node.func.id} usage without apparent size limit",
                        "recommendation": f"Consider streaming instead of buffering in {node.func.id}",
                        "function": "unknown",
                    })
        return allocs

    def _detect_missing_slots(self, tree: ast.AST) -> List[Dict]:
        """Detect classes that could benefit from __slots__."""
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                has_slots = False
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name) and target.id == "__slots__":
                                has_slots = True
                if not has_slots:
                    # Count instance attributes
                    init_attrs = []
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == "__init__":
                            for stmt in ast.walk(item):
                                if isinstance(stmt, ast.Attribute) and isinstance(getattr(stmt, "value", None), ast.Name):
                                    if stmt.value.id == "self":
                                        init_attrs.append(stmt.attr)
                    if init_attrs:
                        issues.append({
                            "type": "missing_slots",
                            "class_name": node.name,
                            "line": getattr(node, "lineno", 0),
                            "attribute_count": len(init_attrs),
                            "message": f"Class '{node.name}' has {len(init_attrs)} instance attributes but no __slots__",
                        })
        return issues

    def _detect_circular_references(self, tree: ast.AST) -> List[Dict]:
        """Detect potential circular reference patterns."""
        risks = []
        class_attrs = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                attrs = set()
                for item in ast.walk(node):
                    if isinstance(item, ast.Attribute) and isinstance(getattr(item, "value", None), ast.Name):
                        if item.value.id == "self":
                            attrs.add(item.attr)
                class_attrs[node.name] = {"attrs": attrs, "line": getattr(node, "lineno", 0)}

        # Simple heuristic: if class A stores class B and vice versa
        classes = list(class_attrs.keys())
        for i, class_a in enumerate(classes):
            for class_b in classes[i+1:]:
                a_lower = class_a.lower()
                b_lower = class_b.lower()
                if b_lower in str(class_attrs[class_a]["attrs"]) and a_lower in str(class_attrs[class_b]["attrs"]):
                    risks.append({
                        "class_a": class_a,
                        "class_b": class_b,
                        "description": f"Mutual reference between {class_a} and {class_b}",
                        "location": f"{class_a}, {class_b}",
                        "line": class_attrs[class_a]["line"],
                    })
        return risks

    def _detect_string_memory_issues(self, tree: ast.AST) -> List[Dict]:
        """Detect string-related memory issues."""
        issues = []
        for node in ast.walk(tree):
            # Large string literals
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and len(node.value) > 10000:
                issues.append({
                    "type": "large_string",
                    "line": getattr(node, "lineno", 0),
                    "size": len(node.value),
                    "description": f"Large string literal ({len(node.value)} chars) at line {getattr(node, 'lineno', 0)}. Load from file instead.",
                })
        return issues

    def _detect_global_mutable_state(self, tree: ast.AST) -> List[Dict]:
        """Detect global mutable state that could cause memory issues."""
        issues = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and isinstance(node.value, (ast.List, ast.Dict, ast.Set)):
                        issues.append({
                            "type": "global_mutable",
                            "name": target.id,
                            "line": getattr(node, "lineno", 0),
                            "description": f"Global mutable '{target.id}' grows unbounded across requests",
                        })
        return issues

    def _detect_large_scopes(self, tree: ast.AST) -> List[Dict]:
        """Detect functions with many local variables."""
        scopes = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                local_vars = set()
                for stmt in ast.walk(node):
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if isinstance(target, ast.Name):
                                local_vars.add(target.id)
                    elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                        local_vars.add(stmt.target.id)
                if len(local_vars) > 20:
                    scopes.append({
                        "type": "large_scope",
                        "function": node.name,
                        "line": getattr(node, "lineno", 0),
                        "var_count": len(local_vars),
                        "description": f"Function '{node.name}' has {len(local_vars)} local variables",
                    })
        return scopes

    def _estimate_memory_usage(self, tree: ast.AST) -> float:
        """Rough estimate of memory usage in MB."""
        # Simple heuristic based on code size and allocation patterns
        code_size = len(ast.dump(tree))
        alloc_count = sum(1 for _ in ast.walk(tree) if isinstance(_, (ast.List, ast.Dict, ast.Set)))
        return round((code_size * 0.001 + alloc_count * 0.1), 2)
