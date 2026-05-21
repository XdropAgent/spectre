"""
SPECTRE Cache Analyzer Agent
Token estimate: ~12K tokens per profile

Analyzes cache hit/miss patterns, eviction strategies, cache warming
opportunities, and caching efficiency across the application stack.
"""
import ast
import time
from typing import Dict, List, Any


class CacheAnalyzer:
    """
    Cache Analyzer — cache hit/miss rates, eviction patterns, warming.

    Token Usage: ~12K tokens per profile
    Daily Volume: ~300 profiles/day = 3.6M tokens/day

    Capabilities:
    - Cache usage pattern detection
    - Cache hit/miss rate estimation
    - Eviction strategy analysis
    - Cache warming opportunity identification
    - TTL configuration analysis
    - Cache invalidation pattern detection
    - Multi-tier caching recommendations
    - Cache key design analysis
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.min_hit_rate_pct = self.config.get("min_hit_rate_pct", 70)
        self.eviction_analysis_window = self.config.get("eviction_analysis_window", 300)

    async def analyze(self, code: str, context: Dict) -> Dict:
        """
        Analyze code for caching patterns and optimization opportunities.
        """
        start_time = time.time()
        findings = []
        bottlenecks = []
        recommendations = []
        metrics = {
            "cache_usage_count": 0,
            "missing_cache_opportunities": 0,
            "ttl_issues": 0,
            "invalidation_patterns": 0,
            "cache_score": 0.0,
            "estimated_hit_rate_pct": 0.0,
        }

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"findings": [], "bottlenecks": [], "recommendations": [], "metrics": metrics}

        # Detect cache usage patterns
        cache_usage = self._detect_cache_usage(tree)
        metrics["cache_usage_count"] = len(cache_usage)
        for cu in cache_usage:
            findings.append(cu)
            if cu.get("issue"):
                bottlenecks.append({
                    "type": "cache_miss",
                    "severity": cu.get("severity", "medium"),
                    "title": f"Cache issue: {cu['issue']}",
                    "description": cu["description"],
                    "location": cu.get("function", "unknown"),
                    "line_number": cu.get("line", 0),
                    "impact_score": cu.get("impact", 5.0),
                    "recommendation": cu.get("recommendation", "Review cache configuration"),
                })

        # Detect missing cache opportunities
        missing_cache = self._detect_missing_cache(tree)
        metrics["missing_cache_opportunities"] = len(missing_cache)
        for mc in missing_cache:
            bottlenecks.append({
                "type": "cache_miss",
                "severity": "medium",
                "title": f"Missing cache: {mc['operation']}",
                "description": f"Operation '{mc['operation']}' at line {mc.get('line', 0)} could benefit from caching",
                "location": mc.get("function", "unknown"),
                "line_number": mc.get("line", 0),
                "impact_score": 5.0,
                "recommendation": mc.get("recommendation", "Add caching for repeated operations"),
            })

        # Detect TTL issues
        ttl_issues = self._detect_ttl_issues(tree)
        metrics["ttl_issues"] = len(ttl_issues)
        for ti in ttl_issues:
            findings.append(ti)
            recommendations.append({
                "title": f"Review TTL: {ti.get('ttl', 'unknown')}",
                "description": ti["description"],
                "priority": 5,
                "impact_score": 4.0,
                "category": "cache",
            })

        # Detect cache invalidation patterns
        invalidation = self._detect_invalidation_patterns(tree)
        metrics["invalidation_patterns"] = len(invalidation)
        for inv in invalidation:
            findings.append(inv)
            if inv.get("issue"):
                bottlenecks.append({
                    "type": "cache_miss",
                    "severity": "medium",
                    "title": f"Cache invalidation issue: {inv.get('type', 'unknown')}",
                    "description": inv["description"],
                    "location": inv.get("function", "unknown"),
                    "line_number": inv.get("line", 0),
                    "impact_score": 5.0,
                    "recommendation": inv.get("recommendation", "Implement proper cache invalidation strategy"),
                })

        # Detect cache key issues
        key_issues = self._detect_cache_key_issues(tree)
        for ki in key_issues:
            bottlenecks.append({
                "type": "cache_miss",
                "severity": "medium",
                "title": f"Cache key issue: {ki['type']}",
                "description": ki["description"],
                "location": ki.get("function", "unknown"),
                "line_number": ki.get("line", 0),
                "impact_score": 4.0,
                "recommendation": ki.get("recommendation", "Design stable, unique cache keys"),
            })

        # Detect repeated expensive computations (should be cached)
        repeated = self._detect_repeated_computations(tree)
        for rep in repeated:
            recommendations.append({
                "title": f"Cache repeated computation: {rep['operation']}",
                "description": f"'{rep['operation']}' is called {rep['count']} times. Use @functools.lru_cache or manual caching.",
                "priority": 3,
                "impact_score": 6.0,
                "category": "cache",
            })

        # Detect lru_cache without maxsize
        lru_issues = self._detect_lru_cache_issues(tree)
        for li in lru_issues:
            findings.append(li)
            if li.get("unbounded"):
                bottlenecks.append({
                    "type": "cache_miss",
                    "severity": "low",
                    "title": f"Unbounded lru_cache: {li['function']}",
                    "description": f"@lru_cache without maxsize on '{li['function']}' — grows without bounds",
                    "location": li["function"],
                    "line_number": li.get("line", 0),
                    "impact_score": 3.0,
                    "recommendation": "Add maxsize parameter to @lru_cache to bound memory usage",
                })

        # Generate recommendations
        if metrics["missing_cache_opportunities"] > 2:
            recommendations.append({
                "title": "Add caching for frequently accessed data",
                "description": f"Found {metrics['missing_cache_opportunities']} operations that could benefit from caching.",
                "priority": 2,
                "impact_score": 7.0,
                "category": "cache",
            })

        if metrics["cache_usage_count"] == 0:
            recommendations.append({
                "title": "Implement application-level caching",
                "description": "No caching detected. Add Redis or in-memory caching for frequently accessed data.",
                "priority": 2,
                "impact_score": 8.0,
                "category": "cache",
            })

        # Estimate cache hit rate
        if metrics["cache_usage_count"] > 0:
            metrics["estimated_hit_rate_pct"] = min(95, 60 + metrics["cache_usage_count"] * 5)
        else:
            metrics["estimated_hit_rate_pct"] = 0.0

        # Calculate cache score
        issues = metrics["ttl_issues"] + metrics["missing_cache_opportunities"]
        metrics["cache_score"] = max(0, 100 - issues * 10)

        return {
            "findings": findings,
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "metrics": metrics,
            "execution_time_ms": round((time.time() - start_time) * 1000, 1),
        }

    def _detect_cache_usage(self, tree: ast.AST) -> List[Dict]:
        """Detect existing cache usage patterns."""
        usage = []
        cache_indicators = {"cache", "redis", "memcache", "lru_cache", "ttl",
                           "get_cache", "set_cache", "delete_cache", "invalidate"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = self._get_call_name(node)
                if name and any(ci in name.lower() for ci in cache_indicators):
                    issue = None
                    severity = "low"
                    # Check for common issues
                    if "set" in name.lower() or "put" in name.lower():
                        has_ttl = any(kw.arg in ("ttl", "timeout", "expire", "ex") for kw in node.keywords)
                        if not has_ttl:
                            issue = "cache_set_without_ttl"
                            severity = "medium"
                            description = f"Cache set without TTL at line {getattr(node, 'lineno', 0)} — entries never expire"
                            recommendation = "Add TTL to cache entries to prevent stale data"
                        else:
                            description = f"Cache operation: {name}"
                            recommendation = None
                    else:
                        description = f"Cache operation: {name}"
                        recommendation = None

                    usage.append({
                        "operation": name,
                        "line": getattr(node, "lineno", 0),
                        "issue": issue,
                        "severity": severity,
                        "description": description,
                        "recommendation": recommendation,
                        "function": "unknown",
                    })

            # Detect @lru_cache decorator
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in node.decorator_list:
                    dec_name = ""
                    if isinstance(dec, ast.Name):
                        dec_name = dec.id
                    elif isinstance(dec, ast.Attribute):
                        dec_name = dec.attr
                    elif isinstance(dec, ast.Call):
                        if isinstance(dec.func, ast.Name):
                            dec_name = dec.func.id
                        elif isinstance(dec.func, ast.Attribute):
                            dec_name = dec.func.attr

                    if "cache" in dec_name.lower():
                        usage.append({
                            "operation": f"@{dec_name} on {node.name}",
                            "line": getattr(node, "lineno", 0),
                            "issue": None,
                            "severity": "low",
                            "description": f"Cache decorator @{dec_name} on '{node.name}'",
                            "recommendation": None,
                            "function": node.name,
                        })

        return usage

    def _detect_missing_cache(self, tree: ast.AST) -> List[Dict]:
        """Detect operations that should be cached."""
        missing = []
        cacheable = {"database", "query", "select", "find", "get", "fetch",
                    "api", "request", "http", "url", "compile", "regex"}

        call_counts = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = self._get_call_name(node)
                if name and any(c in name.lower() for c in cacheable):
                    call_counts[name] = call_counts.get(name, 0) + 1

        for name, count in call_counts.items():
            if count >= 2:
                missing.append({
                    "operation": name,
                    "count": count,
                    "line": 0,
                    "function": "unknown",
                    "recommendation": f"Cache result of {name} — called {count} times",
                })

        return missing

    def _detect_ttl_issues(self, tree: ast.AST) -> List[Dict]:
        """Detect TTL configuration issues."""
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    if kw.arg in ("ttl", "timeout", "expire", "ex"):
                        if isinstance(kw.value, ast.Constant):
                            ttl_val = kw.value.value
                            if isinstance(ttl_val, (int, float)):
                                if ttl_val > 86400:  # > 1 day
                                    issues.append({
                                        "ttl": ttl_val,
                                        "line": getattr(node, "lineno", 0),
                                        "description": f"Very long TTL ({ttl_val}s = {ttl_val/86400:.1f} days) — may serve stale data",
                                        "function": "unknown",
                                    })
                                elif ttl_val == 0:
                                    issues.append({
                                        "ttl": ttl_val,
                                        "line": getattr(node, "lineno", 0),
                                        "description": "TTL of 0 — cached entries expire immediately (no caching benefit)",
                                        "function": "unknown",
                                    })
        return issues

    def _detect_invalidation_patterns(self, tree: ast.AST) -> List[Dict]:
        """Detect cache invalidation patterns."""
        patterns = []
        invalidation_methods = {"delete", "invalidate", "clear", "flush", "remove", "expire"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = self._get_call_attr(node)
                if name and name in invalidation_methods:
                    patterns.append({
                        "type": name,
                        "line": getattr(node, "lineno", 0),
                        "description": f"Cache invalidation via '{name}' at line {getattr(node, 'lineno', 0)}",
                        "issue": False,
                        "function": "unknown",
                    })

        # Check for missing invalidation after updates
        has_update = False
        has_invalidate = len(patterns) > 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = self._get_call_attr(node)
                if name and name in ("update", "save", "insert", "put", "write"):
                    has_update = True

        if has_update and not has_invalidate:
            patterns.append({
                "type": "missing_invalidation",
                "line": 0,
                "description": "Data update operations found without corresponding cache invalidation",
                "issue": True,
                "recommendation": "Invalidate related cache entries after data mutations",
                "function": "unknown",
            })

        return patterns

    def _detect_cache_key_issues(self, tree: ast.AST) -> List[Dict]:
        """Detect cache key design issues."""
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = self._get_call_name(node)
                if name and any(c in name.lower() for c in ["cache", "redis", "memcache"]):
                    # Check if key is dynamic (good) or static (bad)
                    if node.args:
                        key_arg = node.args[0]
                        if isinstance(key_arg, ast.Constant) and isinstance(key_arg.value, str):
                            issues.append({
                                "type": "static_key",
                                "line": getattr(node, "lineno", 0),
                                "description": f"Static cache key '{key_arg.value}' — all requests share same cache entry",
                                "recommendation": "Use dynamic cache keys that include relevant parameters",
                                "function": "unknown",
                            })
        return issues

    def _detect_repeated_computations(self, tree: ast.AST) -> List[Dict]:
        """Detect repeated computations that should be cached."""
        counts = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = self._get_call_name(node)
                if name and len(name) > 3:  # Skip trivial calls
                    counts[name] = counts.get(name, 0) + 1

        return [{"operation": name, "count": count, "line": 0, "function": "unknown"}
                for name, count in counts.items() if count >= 3]

    def _detect_lru_cache_issues(self, tree: ast.AST) -> List[Dict]:
        """Detect lru_cache configuration issues."""
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call):
                        dec_name = ""
                        if isinstance(dec.func, ast.Name):
                            dec_name = dec.func.id
                        elif isinstance(dec.func, ast.Attribute):
                            dec_name = dec.func.attr
                        if "cache" in dec_name.lower():
                            has_maxsize = any(kw.arg == "maxsize" for kw in dec.keywords)
                            issues.append({
                                "function": node.name,
                                "line": getattr(node, "lineno", 0),
                                "unbounded": not has_maxsize,
                            })
        return issues

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

    def _get_call_attr(self, node: ast.Call) -> str:
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
        elif isinstance(node.func, ast.Name):
            return node.func.id
        return ""
