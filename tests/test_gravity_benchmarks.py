import time

from aoc_cli.gravity import compute_gravity_and_curvature


def test_gravity_engine_benchmark() -> None:
    # Generate a synthetic star/wheel graph of 50 nodes
    nodes = []
    edges = []

    # Core hub node
    nodes.append({"id": "node-hub", "capability_level": 5, "side_effect_score": 3.0})

    # Outer nodes
    for i in range(50):
        node_id = f"node-{i}"
        nodes.append({"id": node_id, "capability_level": 1 + (i % 4), "side_effect_score": 0.1 * (i % 5)})
        edges.append(("node-hub", node_id))
        if i > 0:
            edges.append((f"node-{i - 1}", node_id))

    graph_data = {"nodes": nodes, "edges": edges}

    start_time = time.perf_counter()
    metrics = compute_gravity_and_curvature(graph_data)
    end_time = time.perf_counter()

    duration = end_time - start_time
    print(f"\nGravity and curvature computation took {duration:.4f} seconds for 51 nodes.")

    assert "gravity_meta" in metrics
    assert "curvature_meta" in metrics
    assert duration < 1.0
