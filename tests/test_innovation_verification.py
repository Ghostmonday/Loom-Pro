import asyncio
import os

import pytest
from aoc_cli.blueprint import GIV, generate_blueprint
from aoc_supervisor.api import app, get_broadcaster
from fastapi.testclient import TestClient


@pytest.fixture
def api_client():
    return TestClient(app)


def test_ring_buffer_pruning_and_replay():
    sprint_id = "test-innovation-pruning"
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def run():
        broadcaster = await get_broadcaster(sprint_id)
        broadcaster.capacity = 5
        for i in range(10):
            await broadcaster.broadcast("log", "worker-001", f"line {i}")

        last_id = broadcaster.ring_buffer[0]["id"]
        q = await broadcaster.subscribe(last_event_id=last_id)
        results = []
        while not q.empty():
            results.append(await q.get())
        assert len(results) == 4
        assert results[0]["payload"] == "line 6"

        q2 = await broadcaster.subscribe(last_event_id="non-existent")
        results2 = []
        while not q2.empty():
            results2.append(await q2.get())
        assert len(results2) == 5
        assert results2[0]["payload"] == "line 5"

    loop.run_until_complete(run())
    loop.close()


def test_cycle_aware_partitioning():
    nodes = {f"f{i}.py": {"language": "python", "capability_level": 1.0} for i in range(15)}
    edges = [{"source": f"f{i}.py", "target": f"f{(i + 1) % 15}.py"} for i in range(15)]
    graph = {"nodes": [{"id": p, **n} for p, n in nodes.items()], "edges": edges}
    metrics = {"gravity_meta": {"nodes": {p: {"gravity": 0.5} for p in nodes}}, "curvature_meta": {"edges": {}}}
    giv = GIV(worker_id="w1", capabilities=("test",), allowed_paths=tuple(nodes.keys()))

    os.environ["GAIJINN_CONVEX_HULL_THRESHOLD"] = "10"
    try:
        blueprint = generate_blueprint(graph, metrics, giv)
        python_units = [u for u in blueprint.work_units if "python" in u.title.lower()]
        assert len(python_units) == 1
        assert len(python_units[0].allowed_paths) == 15
    finally:
        if "GAIJINN_CONVEX_HULL_THRESHOLD" in os.environ:
            del os.environ["GAIJINN_CONVEX_HULL_THRESHOLD"]


def test_sprint_council_event_promotion(api_client):
    sprint_id = "test-council-promo"
    response = api_client.get(f"/api/v1/sprint/{sprint_id}/council?message=TX-HT-SIGNATURE&worker_id=w1")
    assert response.status_code == 200

    loop = asyncio.new_event_loop()

    async def run():
        broadcaster = await get_broadcaster(sprint_id)
        assert len(broadcaster.ring_buffer) == 1
        assert broadcaster.ring_buffer[0]["event"] == "council_transaction"

    loop.run_until_complete(run())
    loop.close()


def test_high_velocity_burst_resilience():
    sprint_id = "test-burst-resilience"
    loop = asyncio.new_event_loop()

    async def run():
        broadcaster = await get_broadcaster(sprint_id)
        broadcaster.capacity = 100
        tasks = [broadcaster.broadcast("log", "w1", f"Burst {i}") for i in range(1000)]
        await asyncio.gather(*tasks)
        assert len(broadcaster.ring_buffer) == 100

    loop.run_until_complete(run())
    loop.close()


def test_sse_endpoint_stream_termination():
    sprint_id = "test-sse-term"
    loop = asyncio.new_event_loop()

    async def run():
        broadcaster = await get_broadcaster(sprint_id)
        q = await broadcaster.subscribe()
        assert len(broadcaster.listeners) == 1
        await broadcaster.unsubscribe(q)
        assert len(broadcaster.listeners) == 0

    loop.run_until_complete(run())
    loop.close()


def test_scc_deterministic_containment():
    nodes = {f"n{i}": {"language": "js", "capability_level": 1.0} for i in range(8)}
    edges = [
        {"source": "n0", "target": "n1"},
        {"source": "n1", "target": "n2"},
        {"source": "n2", "target": "n0"},
        {"source": "n2", "target": "n3"},
        {"source": "n3", "target": "n4"},
        {"source": "n4", "target": "n2"},
        {"source": "n4", "target": "n5"},
        {"source": "n5", "target": "n6"},
        {"source": "n6", "target": "n7"},
        {"source": "n7", "target": "n4"},
    ]
    graph = {"nodes": [{"id": p, **n} for p, n in nodes.items()], "edges": edges}
    metrics = {"gravity_meta": {"nodes": {p: {"gravity": 0.5} for p in nodes}}, "curvature_meta": {"edges": {}}}
    giv = GIV(worker_id="w1", capabilities=("test",), allowed_paths=tuple(nodes.keys()))

    os.environ["GAIJINN_CONVEX_HULL_THRESHOLD"] = "3"
    try:
        blueprint = generate_blueprint(graph, metrics, giv)
        js_units = [u for u in blueprint.work_units if "js" in u.title.lower()]
        assert len(js_units) == 1
        assert len(js_units[0].allowed_paths) == 8
    finally:
        if "GAIJINN_CONVEX_HULL_THRESHOLD" in os.environ:
            del os.environ["GAIJINN_CONVEX_HULL_THRESHOLD"]
