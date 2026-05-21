"""
SPECTRE Optimization Advisor Agent
Token estimate: ~15K tokens per profile

Synthesizes findings from all other agents to provide actionable
optimization recommendations with priority scoring, effort estimates,
and expected impact. The final agent in the SPECTRE pipeline.
"""
import ast
import time
from typing import Dict, List, Any
from collections import defaultdict


class OptimizationAdvisor:
    """
    Optimization Advisor — actionable recommendations, priority scoring.

    Token Usage: ~15K tokens per profile
    Daily Volume: ~400 profiles/day = 6.0M tokens/day

    Capabilities:
    - Cross-agent finding synthesis
    - Priority scoring (impact vs effort)
    - Code-specific optimization suggestions
    - Architecture-level recommendations
    - Quick wins identification
    - Technical debt assessment
    - Performance regression risk analysis
    - Scaling bottleneck identification
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.min_impact_score = self.config.get("min_impact_score", 3)
        self.max_recommendations = self.config.get("max_recommendations", 20)

    async def analyze(self, code: str, context: Dict) -> Dict:
        """
        Analyze code and synthesize findings from other agents to provide
        prioritized optimization recommendations.
        """
        start_time = time.time()
        findings = []
        bottlenecks = []
        recommendations = []
        metrics = {
            "total_bottlenecks": 0,
            "critical_count": 0,
            "quick_wins": 0,
            "technical_debt_score": 0.0,
            "optimization_score": 0.0,
        }

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"findings": [], "bottlenecks": [], "recommendations": [], "metrics": metrics}

        # Analyze code structure for optimization opportunities
        structure = self._analyze_code_structure(tree)
        findings.extend(structure["findings"])

        # Identify quick wins
        quick_wins = self._identify_quick_wins(tree)
        metrics["quick_wins"] = len(quick_wins)
        for qw in quick_wins:
            recommendations.append({
                "title": qw["title"],
                "description": qw["description"],
                "priority": 1,  # Quick wins get high priority
                "impact_score": qw.get("impact", 6.0),
                "category": "quick_win",
                "effort": "low",
            })

        # Analyze error handling patterns
        error_patterns = self._analyze_error_handling(tree)
        for ep in error_patterns:
            findings.append(ep)
            if ep.get("severity") in ("high", "medium"):
                recommendations.append({
                    "title": f"Improve error handling: {ep['type']}",
                    "description": ep["description"],
                    "priority": ep.get("priority", 4),
                    "impact_score": ep.get("impact", 5.0),
                    "category": "reliability",
                })

        # Detect technical debt indicators
        tech_debt = self._assess_technical_debt(tree)
        metrics["technical_debt_score"] = tech_debt["score"]
        for debt in tech_debt["issues"]:
            findings.append(debt)
            recommendations.append({
                "title": f"Technical debt: {debt['type']}",
                "description": debt["description"],
                "priority": debt.get("priority", 5),
                "impact_score": debt.get("impact", 4.0),
                "category": "technical_debt",
            })

        # Analyze import patterns for optimization
        import_analysis = self._analyze_imports(tree)
        for ia in import_analysis:
            findings.append(ia)
            if ia.get("issue"):
                recommendations.append({
                    "title": f"Optimize imports: {ia['type']}",
                    "description": ia["description"],
                    "priority": 7,
                    "impact_score": 3.0,
                    "category": "optimization",
                })

        # Detect naming patterns suggesting performance concerns
        perf_indicators = self._detect_performance_indicators(tree)
        for pi in perf_indicators:
            findings.append(pi)

        # Analyze string handling
        string_opts = self._analyze_string_handling(tree)
        for so in string_opts:
            recommendations.append({
                "title": so["title"],
                "description": so["description"],
                "priority": so.get("priority", 6),
                "impact_score": so.get("impact", 3.0),
                "category": "optimization",
            })

        # Synthesize previous agent results
        if context and "previous_results" in context:
            synthesis = self._synthesize_previous_results(context["previous_results"])
            metrics["total_bottlenecks"] = synthesis["total_bottlenecks"]
            metrics["critical_count"] = synthesis["critical_count"]

            # Add synthesized recommendations
            for rec in synthesis["top_recommendations"]:
                if not any(r["title"] == rec["title"] for r in recommendations):
                    recommendations.append(rec)

        # Detect scaling patterns
        scaling = self._analyze_scaling_patterns(tree)
        for s in scaling:
            bottlenecks.append({
                "type": "resource_exhaustion",
                "severity": s.get("severity", "medium"),
                "title": f"Scaling concern: {s['pattern']}",
                "description": s["description"],
                "location": s.get("function", "unknown"),
                "line_number": s.get("line", 0),
                "impact_score": s.get("impact", 5.0),
                "recommendation": s.get("recommendation", "Design for horizontal scaling"),
            })

        # Analyze data processing patterns
        data_patterns = self._analyze_data_patterns(tree)
        for dp in data_patterns:
            recommendations.append({
                "title": dp["title"],
                "description": dp["description"],
                "priority": dp.get("priority", 4),
                "impact_score": dp.get("impact", 5.0),
                "category": "optimization",
            })

        # Sort recommendations by priority and impact
        recommendations.sort(key=lambda r: (r.get("priority", 5), -r.get("impact_score", 0)))
        recommendations = recommendations[:self.max_recommendations]

        # Calculate scores
        total_issues = len(findings) + len(bottlenecks)
        critical_weight = metrics["critical_count"] * 3
        metrics["optimization_score"] = max(0, 100 - total_issues * 3 - critical_weight)

        # Generate architecture recommendations
        arch_recs = self._generate_architecture_recommendations(tree, findings)
        recommendations.extend(arch_recs)

        return {
            "findings": findings,
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "metrics": metrics,
            "execution_time_ms": round((time.time() - start_time) * 1000, 1),
        }

    def _analyze_code_structure(self, tree: ast.AST) -> Dict:
        """Analyze overall code structure for optimization opportunities."""
        findings = []
        func_count = 0
        class_count = 0
        total_lines = 0

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_count += 1
                # Check function length
                end_line = getattr(node, "end_lineno", getattr(node, "lineno", 0) + 10)
                length = end_line - getattr(node, "lineno", 0)
                total_lines += length
                if length > 50:
                    findings.append({
                        "type": "long_function",
                        "function": node.name,
                        "line": getattr(node, "lineno", 0),
                        "length": length,
                        "message": f"Function '{node.name}' is {length} lines long — consider splitting",
                        "severity": "medium",
                    })
            elif isinstance(node, ast.ClassDef):
                class_count += 1

        # Check for god modules
        if func_count > 30:
            findings.append({
                "type": "god_module",
                "function_count": func_count,
                "message": f"Module has {func_count} functions — consider splitting into smaller modules",
                "severity": "low",
            })

        return {"findings": findings}

    def _identify_quick_wins(self, tree: ast.AST) -> List[Dict]:
        """Identify quick optimization wins (low effort, high impact)."""
        wins = []

        for node in ast.walk(tree):
            # isinstance() instead of type()
            if isinstance(node, ast.Compare):
                for op in node.ops:
                    if isinstance(op, ast.Is):
                        if isinstance(node.comparators[0], ast.Call):
                            if isinstance(node.comparators[0].func, ast.Name):
                                if node.comparators[0].func.id == "type":
                                    wins.append({
                                        "title": "Use isinstance() instead of type() comparison",
                                        "description": "type() == comparison is slower and doesn't handle inheritance",
                                        "impact": 3.0,
                                    })

            # in operator on list (should be set)
            if isinstance(node, ast.Compare):
                for op in node.ops:
                    if isinstance(op, ast.In):
                        for comp in node.comparators:
                            if isinstance(comp, ast.List):
                                wins.append({
                                    "title": "Use set instead of list for membership testing",
                                    "description": "in-list is O(n), in-set is O(1). Convert constant lists to sets.",
                                    "impact": 5.0,
                                })

            # dict.get() with default vs try/except KeyError
            if isinstance(node, ast.Try):
                if (len(node.handlers) == 1 and
                    isinstance(node.handlers[0].type, ast.Name) and
                    node.handlers[0].type.id == "KeyError"):
                    wins.append({
                        "title": "Use dict.get() instead of try/except KeyError",
                        "description": "dict.get(key, default) is faster and more readable than try/except",
                        "impact": 3.0,
                    })

            # String formatting optimization
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
                if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                    wins.append({
                        "title": "Use f-strings instead of % formatting",
                        "description": "f-strings are faster than %-formatting and str.format()",
                        "impact": 2.0,
                    })

        return wins

    def _analyze_error_handling(self, tree: ast.AST) -> List[Dict]:
        """Analyze error handling patterns."""
        patterns = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                # Bare except
                for handler in node.handlers:
                    if handler.type is None:
                        patterns.append({
                            "type": "bare_except",
                            "line": getattr(handler, "lineno", 0),
                            "severity": "high",
                            "description": "Bare except clause catches all exceptions including SystemExit and KeyboardInterrupt",
                            "priority": 2,
                            "impact": 6.0,
                        })

                    # except Exception as e: pass
                    if (handler.type and isinstance(handler.type, ast.Name) and
                        handler.type.id == "Exception"):
                        if len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
                            patterns.append({
                                "type": "swallowed_exception",
                                "line": getattr(handler, "lineno", 0),
                                "severity": "high",
                                "description": "Exception silently swallowed — makes debugging impossible",
                                "priority": 2,
                                "impact": 7.0,
                            })

                # Too broad try block
                if len(node.body) > 10:
                    patterns.append({
                        "type": "broad_try",
                        "line": getattr(node, "lineno", 0),
                        "severity": "low",
                        "description": f"Try block with {len(node.body)} statements — narrow the scope",
                        "priority": 6,
                        "impact": 3.0,
                    })

        return patterns

    def _assess_technical_debt(self, tree: ast.AST) -> Dict:
        """Assess technical debt in the codebase."""
        issues = []
        score = 0

        # TODO/FIXME/HACK comments
        for node in ast.walk(tree):
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                if isinstance(node.value.value, str):
                    text = node.value.value.lower()
                    if any(marker in text for marker in ["todo", "fixme", "hack", "xxx", "workaround"]):
                        issues.append({
                            "type": "todo_comment",
                            "line": getattr(node, "lineno", 0),
                            "message": f"Technical debt marker: {node.value.value[:60]}",
                            "severity": "low",
                            "priority": 8,
                            "impact": 2.0,
                        })
                        score += 1

        # Magic numbers
        magic_count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                if node.value not in (0, 1, -1, 2, 10, 100, 1000):
                    # Check if it's in a comparison or assignment (not a constant def)
                    magic_count += 1

        if magic_count > 10:
            issues.append({
                "type": "magic_numbers",
                "count": magic_count,
                "message": f"{magic_count} magic numbers found — extract to named constants",
                "severity": "low",
                "priority": 7,
                "impact": 2.0,
            })
            score += 2

        # Very long functions
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end = getattr(node, "end_lineno", getattr(node, "lineno", 0) + 10)
                length = end - getattr(node, "lineno", 0)
                if length > 100:
                    issues.append({
                        "type": "long_function",
                        "function": node.name,
                        "line": getattr(node, "lineno", 0),
                        "length": length,
                        "message": f"Function '{node.name}' is {length} lines — refactor into smaller functions",
                        "severity": "medium",
                        "priority": 4,
                        "impact": 4.0,
                    })
                    score += 3

        return {"score": min(100, score), "issues": issues}

    def _analyze_imports(self, tree: ast.AST) -> List[Dict]:
        """Analyze import patterns for optimization."""
        results = []
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        # Check for heavy imports
        heavy = {"pandas", "numpy", "tensorflow", "torch", "scipy", "sklearn",
                "matplotlib", "PIL", "cv2"}
        for imp in imports:
            if any(h in imp for h in heavy):
                results.append({
                    "type": "heavy_import",
                    "module": imp,
                    "issue": True,
                    "description": f"Heavy import '{imp}' adds significant startup time",
                })

        # Check for wildcard imports
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "*":
                        results.append({
                            "type": "wildcard_import",
                            "module": node.module or "unknown",
                            "issue": True,
                            "description": f"Wildcard import 'from {node.module} import *' — import only what you need",
                        })

        return results

    def _detect_performance_indicators(self, tree: ast.AST) -> List[Dict]:
        """Detect function/variable names suggesting performance concerns."""
        indicators = []
        perf_names = {"slow", "expensive", "heavy", "batch", "bulk", "legacy",
                     "deprecated", "temporary", "temp", "workaround"}

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name_lower = node.name.lower()
                if any(p in name_lower for p in perf_names):
                    indicators.append({
                        "type": "performance_indicator_name",
                        "function": node.name,
                        "line": getattr(node, "lineno", 0),
                        "message": f"Function '{node.name}' name suggests performance concern",
                        "severity": "info",
                    })
        return indicators

    def _analyze_string_handling(self, tree: ast.AST) -> List[Dict]:
        """Analyze string handling for optimization opportunities."""
        opts = []

        # String concatenation in loops
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                for child in ast.walk(node):
                    if isinstance(child, ast.AugAssign) and isinstance(child.op, ast.Add):
                        opts.append({
                            "title": "Use join() for string building in loops",
                            "description": "String concatenation with += in loops is O(n²). Use ''.join() for O(n).",
                            "priority": 4,
                            "impact": 5.0,
                        })
                        break

        return opts

    def _analyze_scaling_patterns(self, tree: ast.AST) -> List[Dict]:
        """Analyze patterns that affect scalability."""
        patterns = []

        # Global state
        global_count = 0
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                global_count += 1

        if global_count > 5:
            patterns.append({
                "pattern": "heavy_global_state",
                "line": 0,
                "severity": "medium",
                "description": f"{global_count} module-level variables — global state limits horizontal scaling",
                "impact": 5.0,
                "recommendation": "Move state to database/cache for multi-instance deployment",
                "function": "module",
            })

        # Synchronous single-threaded patterns
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check for sequential I/O
                io_count = 0
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        name = ""
                        if isinstance(child.func, ast.Attribute):
                            name = child.func.attr
                        if name in ("execute", "query", "fetch", "send", "recv", "read", "write"):
                            io_count += 1
                if io_count > 3:
                    patterns.append({
                        "pattern": "sequential_io",
                        "function": node.name,
                        "line": getattr(node, "lineno", 0),
                        "severity": "medium",
                        "description": f"{io_count} sequential I/O operations in '{node.name}' limit throughput",
                        "impact": 6.0,
                        "recommendation": "Parallelize independent I/O operations",
                    })

        return patterns

    def _analyze_data_patterns(self, tree: ast.AST) -> List[Dict]:
        """Analyze data processing patterns."""
        opts = []

        for node in ast.walk(tree):
            # Nested list comprehensions
            if isinstance(node, ast.ListComp):
                for generator in node.generators:
                    for inner_gen in generator.iter:
                        if isinstance(inner_gen, ast.ListComp):
                            opts.append({
                                "title": "Simplify nested list comprehension",
                                "description": "Nested list comprehension creates intermediate lists. Use itertools or flatten.",
                                "priority": 5,
                                "impact": 4.0,
                            })

            # Manual map/filter patterns
            if isinstance(node, ast.ListComp):
                if len(node.generators) == 1 and node.generators[0].ifs:
                    opts.append({
                        "title": "Consider using filter() for complex filtering",
                        "description": "Complex list comprehension filters may be clearer as filter() calls.",
                        "priority": 7,
                        "impact": 2.0,
                    })

        return opts

    def _synthesize_previous_results(self, previous: Dict) -> Dict:
        """Synthesize findings from all previous agents."""
        total = 0
        critical = 0
        top_recs = []

        for agent_name, result in previous.items():
            if isinstance(result, dict):
                bottlenecks = result.get("bottlenecks", [])
                total += len(bottlenecks)
                for b in bottlenecks:
                    if isinstance(b, dict) and b.get("severity") == "critical":
                        critical += 1

                for rec in result.get("recommendations", [])[:3]:
                    if isinstance(rec, dict):
                        rec["source_agent"] = agent_name
                        top_recs.append(rec)

        # Sort by impact
        top_recs.sort(key=lambda r: r.get("impact_score", 0), reverse=True)

        return {
            "total_bottlenecks": total,
            "critical_count": critical,
            "top_recommendations": top_recs[:10],
        }

    def _generate_architecture_recommendations(self, tree: ast.AST, findings: List) -> List[Dict]:
        """Generate architecture-level recommendations."""
        recs = []

        # Check for monolithic patterns
        func_count = sum(1 for _ in ast.walk(tree) if isinstance(_, (ast.FunctionDef, ast.AsyncFunctionDef)))
        if func_count > 20:
            recs.append({
                "title": "Consider modular architecture",
                "description": f"Module has {func_count} functions. Split into domain-specific modules for better maintainability.",
                "priority": 6,
                "impact_score": 4.0,
                "category": "architecture",
                "effort": "high",
            })

        # Check for missing type hints
        typed = 0
        untyped = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.returns:
                    typed += 1
                else:
                    untyped += 1

        if untyped > typed and untyped > 5:
            recs.append({
                "title": "Add type hints for better performance tooling",
                "description": f"{untyped}/{typed+untyped} functions lack return type hints. Type hints enable better optimization tooling.",
                "priority": 7,
                "impact_score": 3.0,
                "category": "architecture",
                "effort": "medium",
            })

        return recs
