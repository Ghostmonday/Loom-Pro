import re

# 1. complexity.py
path = "aoc_supervisor/aoc_supervisor/complexity.py"
content = open(path).read()
if "import os" not in content:
    content = content.replace("import math", "import math\nimport os")
if "def max_active_workers" not in content:
    content += """
def max_active_workers() -> int:
    return int(os.environ.get("GAIJINN_MAX_ACTIVE_WORKERS", "32"))

def max_concurrent_sprints() -> int:
    return int(os.environ.get("GAIJINN_MAX_CONCURRENT_SPRINTS", "8"))

def max_spawn_timeout() -> int:
    return int(os.environ.get("GAIJINN_MAX_SPAWN_TIMEOUT", "7200"))

def max_workers_per_session() -> int:
    return int(os.environ.get("GAIJINN_MAX_WORKERS_PER_SESSION", "16"))
"""
with open(path, "w") as f: f.write(content)

# 2. spawn_governance.py
path = "aoc_supervisor/aoc_supervisor/spawn_governance.py"
content = open(path).read()
new_resolve = """def resolve_process_group_id(proc: Any) -> int | None:
    if proc is None or os.name != "posix":
        return None
    pid = getattr(proc, "pid", None)
    if not isinstance(pid, int):
        return None
    try:
        return os.getpgid(pid)
    except (ProcessLookupError, OSError):
        return pid"""
content = re.sub(r"def resolve_process_group_id\(proc: Any\) -> int \| None:.*?return pid", new_resolve, content, flags=re.DOTALL)

new_running = """def _process_is_running(entry: Mapping[str, Any]) -> bool:
    if not isinstance(entry, dict):
        return False
    process_group_id = entry.get("process_group_id")
    if isinstance(process_group_id, int) and process_group_alive(process_group_id):
        return True
    proc = entry.get("proc")
    if proc is None:
        return False
    poll = getattr(proc, "poll", None)
    if callable(poll):
        return poll() is None
    returncode = getattr(proc, "returncode", None)
    return returncode is None"""
content = re.sub(r"def _process_is_running\(entry: Mapping\[str, Any\]\) -> bool:.*?return status in {\"running\", \"spawned\"}", new_running, content, flags=re.DOTALL)
with open(path, "w") as f: f.write(content)

# 3. blueprint.py
path = "aoc-cli/aoc_cli/blueprint.py"
content = open(path).read()
insertion_point = content.find("def _group_work_unit(")
patch = """
def _convex_hull_welding_threshold() -> int:
    return int(os.environ.get("GAIJINN_CONVEX_HULL_THRESHOLD", "12"))


def _refine_grouped_blocks(
    grouped: dict[tuple[str, str, str], list[str]],
    graph: Mapping[str, Any]
) -> list[tuple[tuple[str, str, str], list[str]]]:
    \"\"\"Prevent Cascading Convex Hull Over-Welding by capping parallel group sizes while preserving cycles.\"\"\"
    import networkx as nx

    refined: list[tuple[tuple[str, str, str], list[str]]] = []
    threshold = _convex_hull_welding_threshold()

    # Build a dependency graph of only the files in the current group
    group_edges = []
    for raw_edge in graph.get("edges", []):
        source, target = _edge_pair(raw_edge)
        if source and target:
            group_edges.append((source, target))

    for key, paths in sorted(grouped.items()):
        if len(paths) <= threshold:
            refined.append((key, paths))
            continue

        # Find Strongly Connected Components (SCCs) to avoid slicing cycles
        sub_g = nx.DiGraph()
        sub_g.add_nodes_from(paths)
        sub_g.add_edges_from([(s, t) for s, t in group_edges if s in paths and t in paths])

        # Deterministic SCC order: sort by the first node in each component
        sccs_raw = list(nx.strongly_connected_components(sub_g))
        sccs = sorted([sorted(list(scc)) for scc in sccs_raw], key=lambda x: x[0])

        current_chunk = []
        for scc in sccs:
            if len(current_chunk) + len(scc) > threshold and current_chunk:
                refined.append((key, current_chunk))
                current_chunk = list(scc)
            else:
                current_chunk.extend(scc)

        if current_chunk:
            refined.append((key, current_chunk))
    return refined

"""
if "_refine_grouped_blocks" not in content:
    content = content[:insertion_point] + patch + content[insertion_point:]
    old_loop = r"    for key in sorted\(grouped\):.*?work_units\.append\(_group_work_unit\(len\(work_units\) \+ 1, directory, language, risk, paths, giv_profile\)\)"
    new_loop = """    for key, paths_list in _refine_grouped_blocks(grouped, graph):
        directory, language, risk = key
        paths = tuple(sorted(paths_list))
        work_units.append(_group_work_unit(len(work_units) + 1, directory, language, risk, paths, giv_profile))"""
    content = re.sub(old_loop, new_loop, content, flags=re.DOTALL)
with open(path, "w") as f: f.write(content)

# 4. api.py
path = "aoc_supervisor/aoc_supervisor/api.py"
content = open(path).read()

# Update _worker_runtime_status
new_status = """def _worker_runtime_status(
    proc: Any,
    entry: Mapping[str, Any] | None = None,
) -> tuple[str, int | None]:
    if entry is not None and str(entry.get("status", "")) == "timed_out":
        exit_code = entry.get("exit_code")
        return "timed_out", int(exit_code) if isinstance(exit_code, int) else -9

    # Handle both subprocess.Popen and asyncio.subprocess.Process
    poll = getattr(proc, "poll", None)
    exit_code = poll() if callable(poll) else getattr(proc, "returncode", None)

    if exit_code is None:
        return "running", None
    if exit_code == 0:
        return "completed", exit_code
    return "failed", exit_code"""
content = re.sub(r"def _worker_runtime_status\(.*?return \"failed\", exit_code", new_status, content, flags=re.DOTALL)

# Refactor grid_spawn loop
target_marker = "            with log_path.open(\"a\", encoding=\"utf-8\") as stdout_file:"
if target_marker in content:
    start_idx = content.find(target_marker)
    # The block to replace ends exactly before processes.append
    end_marker = "            processes.append("
    end_idx = content.find(end_marker, start_idx)

    new_spawn = """            if mock_grid:
                with log_path.open("a", encoding="utf-8") as stdout_file:
                    proc = popen_worker_process(
                        cmd,
                        stdout=stdout_file,
                        stderr=subprocess.STDOUT,
                        text=True,
                        cwd=str(worker_dir.resolve()),
                    )
            else:
                stdout_file = log_path.open("a", encoding="utf-8")
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    cwd=str(worker_dir.resolve()),
                )
                if proc.stdout:
                    asyncio.create_task(
                        _read_stream(sprint_id, worker_name, manifest_detail.get("domain"), proc.stdout, stdout_file)
                    )\n\n"""
    content = content[:start_idx] + new_spawn + content[end_idx:]

# Broadcaster infrastructure
if "class SprintBroadcaster" not in content:
    insertion_point = content.rfind("if __name__ == \"__main__\":")
    patch = """
async def _read_stream(
    sprint_id: str,
    worker_id: str,
    domain: str | None,
    stream: asyncio.StreamReader,
    log_file: Any
):
    \"\"\"Read a subprocess stream, write to log file, and broadcast lines to the sprint aggregate.\"\"\"
    broadcaster = await get_broadcaster(sprint_id)
    while True:
        line = await stream.readline()
        if not line:
            break
        try:
            text = line.decode("utf-8").rstrip()
        except UnicodeDecodeError:
            text = line.decode("latin-1", errors="replace").rstrip()

        if text:
            log_file.write(text + "\\n")
            log_file.flush()
            event_type = "log"
            if "TX-HT-" in text:
                event_type = "council_transaction"
            await broadcaster.broadcast(
                event_type=event_type,
                worker_id=worker_id,
                domain=domain,
                payload=text
            )


class SprintBroadcaster:
    \"\"\"Multiplexes worker logs and council events into a single async stream.\"\"\"
    def __init__(self, sprint_id: str, capacity: int = 1000):
        self.sprint_id = sprint_id
        self.ring_buffer = []
        self.capacity = capacity
        self.listeners = set()
        self.lock = asyncio.Lock()
        self.counter = 0

    async def broadcast(self, event_type, worker_id, payload, domain=None):
        self.counter += 1
        event = {
            "id": f"{self.sprint_id}-{self.counter}",
            "event": event_type,
            "worker_id": worker_id,
            "domain": domain,
            "timestamp": time.time(),
            "payload": payload,
        }
        async with self.lock:
            self.ring_buffer.append(event)
            if len(self.ring_buffer) > self.capacity:
                self.ring_buffer.pop(0)
            for q in self.listeners:
                await q.put(event)

    async def subscribe(self, last_event_id=None):
        q = asyncio.Queue()
        async with self.lock:
            if last_event_id:
                replay_started = False
                found_id = False
                for event in self.ring_buffer:
                    if event["id"] == last_event_id:
                        found_id = True
                        replay_started = True
                        continue
                    if replay_started:
                        await q.put(event)
                if not found_id:
                    for event in self.ring_buffer:
                        await q.put(event)
            self.listeners.add(q)
        return q

    async def unsubscribe(self, q):
        async with self.lock:
            self.listeners.discard(q)

_broadcasters = {}
_broadcaster_lock = asyncio.Lock()

async def get_broadcaster(sprint_id):
    async with _broadcaster_lock:
        if sprint_id not in _broadcasters:
            _broadcasters[sprint_id] = SprintBroadcaster(sprint_id)
        return _broadcasters[sprint_id]

@app.get("/api/v1/sprint/{sprint_id}/stream")
async def sprint_aggregate_stream(sprint_id: str, request: Request):
    \"\"\"Aggregate SSE endpoint multiplexing all worker logs for a sprint.\"\"\"
    last_event_id = request.headers.get("Last-Event-ID")
    broadcaster = await get_broadcaster(sprint_id)
    q = await broadcaster.subscribe(last_event_id)

    async def event_generator():
        try:
            while True:
                event = await q.get()
                yield f"id: {event.get('id')}\\nevent: {event.get('event')}\\ndata: {json.dumps(event)}\\n\\n"
        except asyncio.CancelledError:
            await broadcaster.unsubscribe(q)

    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

@app.get("/api/v1/sprint/{sprint_id}/council")
async def sprint_council_event(sprint_id: str, message: str, worker_id: str = None, domain: str = None):
    \"\"\"External hook to inject council transaction events into the sprint stream.\"\"\"
    broadcaster = await get_broadcaster(sprint_id)
    await broadcaster.broadcast(
        event_type="council_transaction",
        worker_id=worker_id,
        domain=domain,
        payload=message
    )
    return {"status": "broadcasted"}

"""
    content = content[:insertion_point] + patch + content[insertion_point:]

with open(path, "w") as f: f.write(content)
