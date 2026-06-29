
def replace_block(path, start_marker, end_marker, replacement):
    content = open(path).read()
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print(f"Start marker not found in {path}")
        return False
    end_idx = content.find(end_marker, start_idx)
    if end_idx == -1:
        print(f"End marker not found in {path}")
        return False
    # Move end_idx to the end of the end_marker line
    end_idx = content.find("\n", end_idx) + 1
    new_content = content[:start_idx] + replacement + content[end_idx:]
    with open(path, "w") as f: f.write(new_content)
    return True

# 1. api.py grid_spawn loop
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
                    )\n"""

replace_block("aoc_supervisor/aoc_supervisor/api.py",
    "            with log_path.open(\"a\", encoding=\"utf-8\") as stdout_file:",
    "                cwd=str(worker_dir.resolve()),",
    new_spawn)

# 2. Add broadcaster logic to api.py
content = open("aoc_supervisor/aoc_supervisor/api.py").read()
if "class SprintBroadcaster" not in content:
    insertion_point = content.rfind("if __name__ == \"__main__\":")
    patch = """
async def _read_stream(sprint_id, worker_id, domain, stream, log_file):
    broadcaster = await get_broadcaster(sprint_id)
    while True:
        line = await stream.readline()
        if not line: break
        try:
            text = line.decode("utf-8").rstrip()
        except:
            text = line.decode("latin-1", errors="replace").rstrip()
        if text:
            log_file.write(text + "\\n")
            log_file.flush()
            event_type = "log"
            if "TX-HT-" in text: event_type = "council_transaction"
            await broadcaster.broadcast(event_type, worker_id, text, domain)

class SprintBroadcaster:
    def __init__(self, sprint_id, capacity=1000):
        self.sprint_id = sprint_id
        self.ring_buffer = []
        self.capacity = capacity
        self.listeners = set()
        self.lock = asyncio.Lock()
        self.counter = 0
    async def broadcast(self, event_type, worker_id, payload, domain=None):
        self.counter += 1
        event = {"id": f"{self.sprint_id}-{self.counter}", "event": event_type, "worker_id": worker_id, "domain": domain, "timestamp": time.time(), "payload": payload}
        async with self.lock:
            self.ring_buffer.append(event)
            if len(self.ring_buffer) > self.capacity: self.ring_buffer.pop(0)
            for q in self.listeners: await q.put(event)
    async def subscribe(self, last_event_id=None):
        q = asyncio.Queue()
        async with self.lock:
            if last_event_id:
                replay = False
                found = False
                for e in self.ring_buffer:
                    if e["id"] == last_event_id:
                        found = True
                        replay = True
                        continue
                    if replay: await q.put(e)
                if not found:
                    for e in self.ring_buffer: await q.put(e)
            self.listeners.add(q)
        return q
    async def unsubscribe(self, q):
        async with self.lock: self.listeners.discard(q)

_broadcasters = {}
_broadcaster_lock = asyncio.Lock()
async def get_broadcaster(sprint_id):
    async with _broadcaster_lock:
        if sprint_id not in _broadcasters: _broadcasters[sprint_id] = SprintBroadcaster(sprint_id)
        return _broadcasters[sprint_id]

@app.get("/api/v1/sprint/{sprint_id}/stream")
async def sprint_aggregate_stream(sprint_id, request: Request):
    last_id = request.headers.get("Last-Event-ID")
    b = await get_broadcaster(sprint_id)
    q = await b.subscribe(last_id)
    async def gen():
        try:
            while True:
                e = await q.get()
                yield f"id: {e['id']}\\nevent: {e['event']}\\ndata: {json.dumps(e)}\\n\\n"
        except asyncio.CancelledError:
            await b.unsubscribe(q)
    from fastapi.responses import StreamingResponse
    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})

@app.get("/api/v1/sprint/{sprint_id}/council")
async def sprint_council_event(sprint_id, message, worker_id=None, domain=None):
    b = await get_broadcaster(sprint_id)
    await b.broadcast("council_transaction", worker_id, message, domain)
    return {"status": "broadcasted"}

"""
    content = content[:insertion_point] + patch + content[insertion_point:]
    with open("aoc_supervisor/aoc_supervisor/api.py", "w") as f: f.write(content)
