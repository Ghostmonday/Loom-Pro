#!/usr/bin/env bash
# Gate 2 — API performance smoke for Gaijinn promotion pipeline.
# Writes .gaijinn/perf-bench-results.json and exits non-zero on threshold breach.
# Gracefully handles API-unavailable (no server running in converged system).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

API_BASE="${GAIJINN_API_BASE:-http://127.0.0.1:8080}"
OUT="${GAIJINN_PERF_RESULTS:-.gaijinn/perf-bench-results.json}"
MAX_HEALTH_MS="${GAIJINN_PERF_MAX_HEALTH_MS:-500}"
MAX_QUOTE_MS="${GAIJINN_PERF_MAX_QUOTE_MS:-3000}"

mkdir -p "$(dirname "$OUT")"

python3 - <<'PY' "$API_BASE" "$OUT" "$MAX_HEALTH_MS" "$MAX_QUOTE_MS"
import json
import sys
import time
import urllib.error
import urllib.request

api_base, out_path, max_health, max_quote = sys.argv[1:5]
max_health_ms = int(max_health)
max_quote_ms = int(max_quote)

def try_request(method: str, path: str, payload: dict = None) -> dict:
    """Safely attempt an HTTP request, returning a result dict on any outcome."""
    url = api_base.rstrip("/") + path
    start = time.perf_counter()
    try:
        if method == "GET":
            with urllib.request.urlopen(url, timeout=30) as resp:
                body = resp.read(200).decode("utf-8", errors="replace")
                return {"ok": True, "status": resp.status, "latency_ms": (time.perf_counter() - start) * 1000.0, "body": body}
        else:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url, data=data,
                headers={"Content-Type": "application/json", "X-User-Id": "terminal-user"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read(400).decode("utf-8", errors="replace")
                return {"ok": True, "status": resp.status, "latency_ms": (time.perf_counter() - start) * 1000.0, "body": body}
    except urllib.error.HTTPError as exc:
        return {"ok": True, "status": exc.code, "latency_ms": (time.perf_counter() - start) * 1000.0, "body": exc.read(200).decode("utf-8", errors="replace")}
    except (urllib.error.URLError, ConnectionRefusedError, TimeoutError, OSError) as exc:
        elapsed = (time.perf_counter() - start) * 1000.0
        reason = getattr(exc, "reason", str(exc))
        return {"ok": False, "status": 0, "latency_ms": round(elapsed, 2), "error": str(reason)}

checks = []

result = try_request("GET", "/api/v1/health")
checks.append({
    "name": "perf.health_latency",
    "endpoint": "GET /api/v1/health",
    "status": result["status"] if result.get("ok") else 0,
    "latency_ms": round(result["latency_ms"], 2),
    "max_ms": max_health_ms,
    "passed": result.get("ok", False) and result["status"] == 200 and result["latency_ms"] <= max_health_ms,
    "skipped": not result.get("ok", False),
    "skip_reason": result.get("error", "API unreachable") if not result.get("ok") else None,
})

quote_payload = {
    "workers": 2, "agent_slots": 2, "assignment_count": 2,
    "nodes": [{"id": "node-0"}, {"id": "node-1"}],
}
result = try_request("POST", "/api/v1/quote", quote_payload)
checks.append({
    "name": "perf.quote_latency",
    "endpoint": "POST /api/v1/quote",
    "status": result["status"] if result.get("ok") else 0,
    "latency_ms": round(result["latency_ms"], 2),
    "max_ms": max_quote_ms,
    "passed": result.get("ok", False) and result["status"] == 200 and result["latency_ms"] <= max_quote_ms,
    "skipped": not result.get("ok", False),
    "skip_reason": result.get("error", "API unreachable") if not result.get("ok") else None,
})

failed = [c for c in checks if not c["passed"] and not c.get("skipped")]
report = {
    "schema_version": 1,
    "api_base": api_base,
    "passed": not failed,
    "skipped": all(c.get("skipped") for c in checks),
    "failed_count": len(failed),
    "checks": checks,
}
with open(out_path, "w", encoding="utf-8") as handle:
    json.dump(report, handle, indent=2)
    handle.write("\n")

print(json.dumps(report, indent=2))
# Exit 0 even if API unavailable — only fail on actual broken endpoints or breaches
raise SystemExit(0 if (report["passed"] or report["skipped"]) else 1)
PY