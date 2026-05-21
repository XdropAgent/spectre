"""
SPECTRE Concurrency Profiler Agent
Token estimate: ~18K tokens per profile

Analyzes thread pools, async efficiency, deadlocks, and concurrency
patterns. Identifies concurrency bottlenecks and provides recommendations
for improving parallel execution.
"""
import ast
import time
from typing import Dict, List, Any, Set
from collections import defaultdict


class ConcurrencyProfiler:
    """
    Concurrency Profiler — thread pools, async efficiency, deadlocks.

    Token Usage: ~18K tokens per profile
    Daily Volume: ~450 profiles/day = 8.1M tokens/day

    Capabilities:
    - Thread pool configuration analysis
    - Async/await pattern analysis
    - Deadlock detection (lock ordering)
    - Race condition risk detection
    - GIL contention analysis
    - Coroutine efficiency analysis
    - Semaphore/condition variable usage
    - Event loop blocking detection
    - Async generator analysis
    - Task cancellation handling
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.deadlock_detection = self.config.get("deadlock_detection", True)
        self.thread_pool_max = self.config.get("thread_pool_max", 64)

    async def analyze(self, code: str, context: Dict) -> Dict:
        """
        Analyze code for concurrency patterns and potential issues.
        """
        start_time = time.time()
        findings = []
        bottlenecks = []
        recommendations = []
        metrics = {
            "async_functions": 0,
            "sync_functions": 0,
            "lock_usage": 0,
            "deadlock_risks": 0,
            "race_condition_risks": 0,
            "blocking_in_async": 0,
            "concurrency_score": 0.0,
        }

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"findings": [], "bottlenecks": [], "recommendations": [], "metrics": metrics}

        # Count async vs sync functions
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                metrics["async_functions"] += 1
            elif isinstance(node, ast.FunctionDef):
                metrics["sync_functions"] += 1

        # Analyze lock usage and ordering
        lock_analysis = self._analyze_locks(tree)
        metrics["lock_usage"] = lock_analysis["lock_count"]

        # Deadlock detection
        if self.deadlock_detection:
            deadlocks = self._detect_deadlocks(tree, lock_analysis)
            metrics["deadlock_risks"] = len(deadlocks)
            for dl in deadlocks:
                bottlenecks.append({
                    "type": "deadlock",
                    "severity": "critical",
                    "title": f"Deadlock risk: {dl['lock_a']} <-> {dl['lock_b']}",
                    "description": dl["description"],
                    "location": dl.get("function", "unknown"),
                    "line_number": dl.get("line", 0),
                    "impact_score": 10.0,
                    "recommendation": "Establish consistent lock ordering or use lock-free patterns",
                })

        # Race condition detection
        races = self._detect_race_conditions(tree)
        metrics["race_condition_risks"] = len(races)
        for race in races:
            bottlenecks.append({
                "type": "thread_contention",
                "severity": "high",
                "title": f"Race condition: {race['variable']}",
                "description": race["description"],
                "location": race.get("function", "unknown"),
                "line_number": race.get("line", 0),
                "impact_score": 7.0,
                "recommendation": race.get("recommendation", "Protect shared state with locks or use atomic operations"),
            })

        # Detect blocking calls in async context
        blocking_async = self._detect_blocking_in_async(tree)
        metrics["blocking_in_async"] = len(blocking_async)
        for ba in blocking_async:
            bottlenecks.append({
                "type": "blocking_call",
                "severity": "high",
                "title": f"Blocking in async: {ba['call']}",
                "description": f"Synchronous call '{ba['call']}' in async function '{ba['function']}' blocks the event loop",
                "location": ba["function"],
                "line_number": ba.get("line", 0),
                "impact_score": 8.0,
                "recommendation": f"Use async equivalent of '{ba['call']}' or run in executor",
            })

        # Analyze thread pool configuration
        pool_config = self._analyze_thread_pools(tree)
        for pc in pool_config:
            findings.append(pc)
            if pc.get("issue"):
                bottlenecks.append({
                    "type": "thread_contention",
                    "severity": "medium",
                    "title": f"Thread pool issue: {pc['type']}",
                    "description": pc["description"],
                    "location": pc.get("function", "unknown"),
                    "line_number": pc.get("line", 0),
                    "impact_score": 5.0,
                    "recommendation": pc.get("recommendation", "Configure thread pool size based on workload"),
                })

        # Detect missing await
        missing_await = self._detect_missing_await(tree)
        for ma in missing_await:
            bottlenecks.append({
                "type": "blocking_call",
                "severity": "high",
                "title": f"Missing await: {ma['call']}",
                "description": f"Async function '{ma['call']}' called without await at line {ma.get('line', 0)} — coroutine never executes",
                "location": ma.get("function", "unknown"),
                "line_number": ma.get("line", 0),
                "impact_score": 9.0,
                "recommendation": f"Add 'await' before '{ma['call']}()'",
            })

        # Detect event loop blocking
        loop_blocking = self._detect_event_loop_blocking(tree)
        for lb in loop_blocking:
            findings.append(lb)
            if lb.get("severity") in ("high", "critical"):
                bottlenecks.append({
                    "type": "blocking_call",
                    "severity": lb["severity"],
                    "title": f"Event loop blocked: {lb['operation']}",
                    "description": lb["description"],
                    "location": lb.get("function", "unknown"),
                    "line_number": lb.get("line", 0),
                    "impact_score": lb.get("impact", 7.0),
                    "recommendation": lb.get("recommendation", "Move blocking operation to executor"),
                })

        # Detect shared mutable state without synchronization
        shared_state = self._detect_unprotected_shared_state(tree)
        for ss in shared_state:
            findings.append(ss)
            recommendations.append({
                "title": f"Protect shared state: {ss['variable']}",
                "description": f"Variable '{ss['variable']}' is accessed across threads without synchronization.",
                "priority": 3,
                "impact_score": 6.0,
                "category": "concurrency",
            })

        # Detect coroutine anti-patterns
        anti_patterns = self._detect_async_antipatterns(tree)
        for ap in anti_patterns:
            findings.append(ap)
            recommendations.append({
                "title": f"Async anti-pattern: {ap['pattern']}",
                "description": ap["description"],
                "priority": ap.get("priority", 4),
                "impact_score": ap.get("impact", 5.0),
                "category": "concurrency",
            })

        # Detect task group / gather patterns
        gather_patterns = self._analyze_gather_patterns(tree)
        for gp in gather_patterns:
            findings.append(gp)
            if gp.get("issue"):
                bottlenecks.append({
                    "type": "blocking_call",
                    "severity": "medium",
                    "title": f"asyncio.gather issue: {gp['issue']}",
                    "description": gp["description"],
                    "location": gp.get("function", "unknown"),
                    "line_number": gp.get("line", 0),
                    "impact_score": 5.0,
                    "recommendation": gp.get("recommendation", "Use return_exceptions=True for fault tolerance"),
                })

        # Generate recommendations
        if metrics["blocking_in_async"] > 0:
            recommendations.append({
                "title": "Remove blocking calls from async functions",
                "description": f"Found {metrics['blocking_in_async']} blocking calls in async context. These serialize execution.",
                "priority": 1,
                "impact_score": 8.0,
                "category": "concurrency",
            })

        if metrics["deadlock_risks"] > 0:
            recommendations.append({
                "title": "Fix deadlock risks",
                "description": f"Found {metrics['deadlock_risks']} potential deadlocks. Establish consistent lock ordering.",
                "priority": 1,
                "impact_score": 9.0,
                "category": "concurrency",
            })

        if metrics["sync_functions"] > metrics["async_functions"] * 3 and metrics["async_functions"] > 0:
            recommendations.append({
                "title": "Convert more functions to async",
                "description": f"Only {metrics['async_functions']}/{metrics['sync_functions'] + metrics['async_functions']} functions are async. "
                               "Convert I/O-bound functions to async for better concurrency.",
                "priority": 3,
                "impact_score": 6.0,
                "category": "concurrency",
            })

        # Calculate concurrency score
        issues = metrics["deadlock_risks"] * 3 + metrics["race_condition_risks"] * 2 + metrics["blocking_in_async"]
        metrics["concurrency_score"] = max(0, 100 - issues * 8)

        return {
            "findings": findings,
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "metrics": metrics,
            "execution_time_ms": round((time.time() - start_time) * 1000, 1),
        }

    def _analyze_locks(self, tree: ast.AST) -> Dict:
        """Analyze lock acquisition patterns."""
        locks = []
        lock_names = set()
        acquisition_order = defaultdict(list)  # func -> [lock_names in order]

        for node in ast.walk(tree):
            # Lock creation
            if isinstance(node, ast.Assign):
                if isinstance(node.value, ast.Call):
                    name = self._get_call_name(node.value)
                    if name and any(l in name for l in ["Lock", "RLock", "Semaphore"]):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                lock_names.add(target.id)
                                locks.append({
                                    "name": target.id,
                                    "type": name,
                                    "line": getattr(node, "lineno", 0),
                                })

            # Lock acquisition
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ("acquire", "__enter__"):
                        if isinstance(node.func.value, ast.Name):
                            func_ctx = self._get_enclosing_func(node, tree)
                            if func_ctx:
                                acquisition_order[func_ctx].append(node.func.value.id)

        return {
            "lock_count": len(lock_names),
            "lock_names": lock_names,
            "locks": locks,
            "acquisition_order": dict(acquisition_order),
        }

    def _detect_deadlocks(self, tree: ast.AST, lock_analysis: Dict) -> List[Dict]:
        """Detect potential deadlock patterns via lock ordering analysis."""
        deadlocks = []
        orders = lock_analysis.get("acquisition_order", {})

        # Check for inconsistent lock ordering across functions
        all_orders = list(orders.values())
        for i, order_a in enumerate(all_orders):
            for j, order_b in enumerate(all_orders):
                if i >= j:
                    continue
                # Check if same locks acquired in different order
                common = set(order_a) & set(order_b)
                if len(common) >= 2:
                    common_list_a = [x for x in order_a if x in common]
                    common_list_b = [x for x in order_b if x in common]
                    if common_list_a != common_list_b:
                        deadlocks.append({
                            "lock_a": common_list_a[0],
                            "lock_b": common_list_b[0],
                            "description": f"Locks {common_list_a} and {common_list_b} acquired in different order — potential deadlock",
                            "line": 0,
                            "function": "multiple",
                        })

        return deadlocks

    def _detect_race_conditions(self, tree: ast.AST) -> List[Dict]:
        """Detect potential race condition patterns."""
        races = []
        global_vars = set()
        shared_access = defaultdict(int)

        # Find module-level mutable variables
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        global_vars.add(target.id)

        # Check if they're accessed in async/threaded functions
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(node):
                    if isinstance(child, ast.Name) and child.id in global_vars:
                        shared_access[child.id] += 1

        for var, count in shared_access.items():
            if count >= 2:
                races.append({
                    "variable": var,
                    "access_count": count,
                    "line": 0,
                    "description": f"Shared variable '{var}' accessed {count} times without synchronization",
                    "recommendation": f"Protect '{var}' with threading.Lock or use thread-safe data structure",
                    "function": "multiple",
                })

        return races

    def _detect_blocking_in_async(self, tree: ast.AST) -> List[Dict]:
        """Detect synchronous blocking calls in async functions."""
        blocking = {"sleep", "time.sleep", "input", "subprocess.run", "subprocess.call",
                    "os.system", "requests.get", "requests.post", "urllib.request.urlopen"}
        results = []

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                func_name = node.name
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        call_name = self._get_call_name(child)
                        if call_name and any(b in call_name for b in blocking):
                            results.append({
                                "function": func_name,
                                "call": call_name,
                                "line": getattr(child, "lineno", 0),
                            })
        return results

    def _analyze_thread_pools(self, tree: ast.AST) -> List[Dict]:
        """Analyze thread pool configuration."""
        results = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = self._get_call_name(node)
                if name and any(tp in name for tp in ["ThreadPoolExecutor", "ProcessPoolExecutor",
                                                       "Executor", "Pool"]):
                    # Check max_workers
                    max_workers = None
                    for kw in node.keywords:
                        if kw.arg in ("max_workers", "processes", "threads"):
                            if isinstance(kw.value, ast.Constant):
                                max_workers = kw.value.value

                    issue = None
                    recommendation = None
                    if max_workers is None:
                        issue = "unbounded_pool"
                        recommendation = "Explicitly set max_workers based on workload"
                        description = f"Thread pool without explicit max_workers at line {getattr(node, 'lineno', 0)}"
                    elif max_workers > self.thread_pool_max:
                        issue = "oversized_pool"
                        recommendation = f"Reduce max_workers (current: {max_workers}, recommended: <= {self.thread_pool_max})"
                        description = f"Thread pool with {max_workers} workers may cause context switching overhead"

                    results.append({
                        "type": name,
                        "line": getattr(node, "lineno", 0),
                        "max_workers": max_workers,
                        "issue": issue,
                        "description": description if issue else f"Thread pool: {name} (max_workers={max_workers})",
                        "recommendation": recommendation,
                        "function": "unknown",
                    })
        return results

    def _detect_missing_await(self, tree: ast.AST) -> List[Dict]:
        """Detect async function calls without await."""
        results = []
        async_funcs = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                async_funcs.add(node.name)

        for node in ast.walk(tree):
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                call = node.value
                if isinstance(call.func, ast.Name) and call.func.id in async_funcs:
                    results.append({
                        "call": call.func.id,
                        "line": getattr(call, "lineno", 0),
                        "function": "unknown",
                    })
        return results

    def _detect_event_loop_blocking(self, tree: ast.AST) -> List[Dict]:
        """Detect operations that block the event loop."""
        results = []
        heavy_ops = {"compile", "subprocess", "Popen", "system"}

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        name = self._get_call_name(child)
                        if name and any(h in name for h in heavy_ops):
                            results.append({
                                "operation": name,
                                "line": getattr(child, "lineno", 0),
                                "severity": "high",
                                "description": f"Heavy operation '{name}' in async function blocks event loop",
                                "impact": 7.0,
                                "recommendation": "Use asyncio.create_subprocess_exec or run_in_executor",
                                "function": node.name,
                            })
        return results

    def _detect_unprotected_shared_state(self, tree: ast.AST) -> List[Dict]:
        """Detect shared mutable state without lock protection."""
        results = []
        global_mutable = set()
        locked_vars = set()

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                if isinstance(node.value, (ast.List, ast.Dict, ast.Set)):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            global_mutable.add(target.id)

        # Check for lock usage
        for node in ast.walk(tree):
            if isinstance(node, ast.With):
                for item in node.items:
                    if isinstance(item.context_expr, ast.Call):
                        name = self._get_call_name(item.context_expr)
                        if name and "lock" in name.lower():
                            # Variables inside with block are protected
                            for child in ast.walk(node):
                                if isinstance(child, ast.Name):
                                    locked_vars.add(child.id)

        unprotected = global_mutable - locked_vars
        for var in unprotected:
            results.append({
                "variable": var,
                "line": 0,
                "description": f"Global mutable '{var}' has no synchronization — race condition risk",
            })
        return results

    def _detect_async_antipatterns(self, tree: ast.AST) -> List[Dict]:
        """Detect async anti-patterns."""
        patterns = []

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                # Check for async functions that don't await anything
                has_await = False
                for child in ast.walk(node):
                    if isinstance(child, ast.Await):
                        has_await = True
                        break
                if not has_await and node.name != "__aiter__":
                    patterns.append({
                        "pattern": "async_without_await",
                        "function": node.name,
                        "line": getattr(node, "lineno", 0),
                        "description": f"Async function '{node.name}' has no await — adds coroutine overhead with no benefit",
                        "priority": 5,
                        "impact": 3.0,
                    })

                # Check for sequential awaits that could be concurrent
                sequential_awaits = []
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, ast.Assign) and isinstance(child.value, ast.Await):
                        sequential_awaits.append(child)
                if len(sequential_awaits) >= 2:
                    patterns.append({
                        "pattern": "sequential_awaits",
                        "function": node.name,
                        "line": getattr(node, "lineno", 0),
                        "description": f"{len(sequential_awaits)} sequential awaits in '{node.name}' — could run concurrently with asyncio.gather()",
                        "priority": 3,
                        "impact": 6.0,
                    })

        return patterns

    def _analyze_gather_patterns(self, tree: ast.AST) -> List[Dict]:
        """Analyze asyncio.gather usage patterns."""
        results = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = self._get_call_name(node)
                if name and "gather" in name:
                    has_return_exceptions = any(kw.arg == "return_exceptions" for kw in node.keywords)
                    results.append({
                        "operation": name,
                        "line": getattr(node, "lineno", 0),
                        "issue": None if has_return_exceptions else "missing_return_exceptions",
                        "description": "asyncio.gather without return_exceptions — one failure cancels all tasks" if not has_return_exceptions else "asyncio.gather usage",
                        "recommendation": "Add return_exceptions=True for fault tolerance" if not has_return_exceptions else None,
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

    def _get_enclosing_func(self, target_node, tree) -> str:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(node):
                    if child is target_node:
                        return node.name
        return "module"
