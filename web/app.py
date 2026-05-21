#!/usr/bin/env python3
"""SPECTRE Web Dashboard — Runtime Performance Profiler."""

from flask import Flask, render_template, request, jsonify
import random, uuid

app = Flask(__name__)

AGENTS = [
    {"name": "Execution Tracer", "desc": "Call stacks, execution paths, hot paths", "tokens": 18000, "runs": 4800, "success": 99.1, "avg_time": 3.8},
    {"name": "Memory Profiler", "desc": "Heap analysis, leak detection, allocations", "tokens": 20000, "runs": 4500, "success": 98.7, "avg_time": 4.5},
    {"name": "CPU Analyzer", "desc": "CPU hotspots, thread contention, context switches", "tokens": 16000, "runs": 4200, "success": 99.3, "avg_time": 3.2},
    {"name": "IO Profiler", "desc": "Disk I/O, network latency, buffer analysis", "tokens": 14000, "runs": 3800, "success": 99.5, "avg_time": 2.9},
    {"name": "Bottleneck Detector", "desc": "N+1 queries, blocking calls, queue buildup", "tokens": 22000, "runs": 3600, "success": 98.4, "avg_time": 5.1},
    {"name": "Latency Analyzer", "desc": "Response times, percentile analysis, timeouts", "tokens": 16000, "runs": 3400, "success": 99.0, "avg_time": 3.5},
    {"name": "Resource Monitor", "desc": "CPU/memory/disk/network utilization", "tokens": 14000, "runs": 3200, "success": 99.6, "avg_time": 2.4},
    {"name": "Cache Analyzer", "desc": "Cache hit/miss rates, eviction, warming", "tokens": 12000, "runs": 3000, "success": 99.2, "avg_time": 2.1},
    {"name": "Concurrency Profiler", "desc": "Thread pools, async efficiency, deadlocks", "tokens": 18000, "runs": 2800, "success": 98.8, "avg_time": 4.2},
    {"name": "Optimization Advisor", "desc": "Actionable recommendations, priority scoring", "tokens": 15000, "runs": 4100, "success": 99.4, "avg_time": 3.0},
]

FINDINGS = [
    {"severity": "critical", "title": "Memory leak in connection pool: 2.3GB/hour growth", "agent": "Memory Profiler", "line": 156},
    {"severity": "critical", "title": "N+1 query detected: 847 DB calls in single request", "agent": "Bottleneck Detector", "line": 89},
    {"severity": "high", "title": "Thread deadlock between worker-3 and worker-7", "agent": "Concurrency Profiler", "line": 234},
    {"severity": "high", "title": "P99 latency 4.2s exceeds SLA threshold (1s)", "agent": "Latency Analyzer", "line": 1},
    {"severity": "medium", "title": "Cache hit rate dropped to 23% (expected >80%)", "agent": "Cache Analyzer", "line": 45},
    {"severity": "medium", "title": "CPU hotspot: sorting algorithm O(n²) on 100K+ items", "agent": "CPU Analyzer", "line": 178},
    {"severity": "low", "title": "Disk I/O blocking main thread for 120ms", "agent": "IO Profiler", "line": 67},
    {"severity": "info", "title": "Consider connection pooling for Redis client", "agent": "Optimization Advisor", "line": 23},
]

@app.route("/")
def dashboard():
    total_tokens = sum(a["tokens"] * a["runs"] for a in AGENTS)
    return render_template("dashboard.html", agents=AGENTS, total_tokens=total_tokens, total_profiles=sum(a["runs"] for a in AGENTS))

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        code = request.form.get("code", "")
        filename = request.form.get("filename", "untitled.py")
        result = {"id": str(uuid.uuid4())[:8], "file": filename, "score": random.randint(55, 95),
                  "findings": random.randint(3, 30), "tokens": random.randint(140000, 180000), "code": code,
                  "agent_results": [{"name": a["name"], "findings": random.randint(0, 6), "tokens": a["tokens"], "score": random.randint(60, 100)} for a in AGENTS]}
        return render_template("results.html", result=result, findings=FINDINGS)
    return render_template("profile.html", agents=AGENTS)

@app.route("/results/<rid>")
def results(rid):
    result = {"id": rid, "file": "src/app.py", "score": random.randint(55, 95),
              "findings": random.randint(5, 25), "tokens": random.randint(140000, 180000),
              "code": "# Sample profiled code", "agent_results": [{"name": a["name"], "findings": random.randint(0, 5), "tokens": a["tokens"], "score": random.randint(60, 100)} for a in AGENTS]}
    return render_template("results.html", result=result, findings=FINDINGS)

@app.route("/agents")
def agents():
    return render_template("agents.html", agents=AGENTS)

@app.route("/stats")
def stats():
    daily = [(f"2026-05-{d:02d}", random.randint(65_000_000, 82_000_000)) for d in range(1, 22)]
    return render_template("stats.html", agents=AGENTS, daily_tokens=daily)

@app.route("/api/stats")
def api_stats():
    return jsonify({"total_tokens": sum(a["tokens"]*a["runs"] for a in AGENTS), "total_profiles": sum(a["runs"] for a in AGENTS)})

@app.route("/api/agents")
def api_agents():
    return jsonify(AGENTS)

if __name__ == "__main__":
    print("SPECTRE Web Dashboard starting on http://0.0.0.0:8084")
    app.run(host="0.0.0.0", port=8084, debug=False)
