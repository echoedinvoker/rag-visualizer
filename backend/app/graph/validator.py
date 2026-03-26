"""Pre-compilation graph config validator using networkx.

Catches structural problems that LangGraph's ``compile()`` does not check:
- Unreachable nodes (not reachable from START)
- Dead-end nodes (no path to END)
- Unknown node types
- Invalid conditional edge mappings
- Unbounded cycles (cycles without a retry-limited node)
"""
from __future__ import annotations

import networkx as nx

from app.graph.registry import NODE_REGISTRY


def validate_graph(config: dict) -> list[str]:
    """Return a list of error/warning strings.  Empty list = valid."""
    errors: list[str] = []
    nodes_cfg = config.get("nodes", {})
    edges_cfg = config.get("edges", [])
    cond_edges_cfg = config.get("conditional_edges", [])

    if not nodes_cfg:
        errors.append("Graph has no nodes.")
        return errors

    # --- Check node types exist in registry ---
    for node_id, node_def in nodes_cfg.items():
        ntype = node_def.get("type")
        if ntype not in NODE_REGISTRY:
            errors.append(f"Node '{node_id}' has unknown type '{ntype}'. "
                          f"Available: {list(NODE_REGISTRY.keys())}")

    # --- Build networkx digraph ---
    G = nx.DiGraph()
    G.add_node("__START__")
    G.add_node("__END__")
    for node_id in nodes_cfg:
        G.add_node(node_id)

    all_node_ids = set(nodes_cfg.keys()) | {"__START__", "__END__"}

    # Regular edges
    for edge in edges_cfg:
        src = edge.get("source", "").replace("START", "__START__")
        tgt = edge.get("target", "").replace("END", "__END__")
        if src not in all_node_ids:
            errors.append(f"Edge source '{edge.get('source')}' is not a defined node.")
        if tgt not in all_node_ids:
            errors.append(f"Edge target '{edge.get('target')}' is not a defined node.")
        G.add_edge(src, tgt)

    # Conditional edges
    for cond in cond_edges_cfg:
        src = cond.get("source", "").replace("START", "__START__")
        if src not in all_node_ids:
            errors.append(f"Conditional edge source '{cond.get('source')}' is not a defined node.")
        mapping = cond.get("mapping", {})
        for value, tgt_id in mapping.items():
            tgt = tgt_id.replace("END", "__END__")
            if tgt not in all_node_ids:
                errors.append(
                    f"Conditional edge from '{cond.get('source')}' maps "
                    f"'{value}' to unknown node '{tgt_id}'."
                )
            G.add_edge(src, tgt)

    # --- Check START has at least one outgoing edge ---
    if G.out_degree("__START__") == 0:
        errors.append("No edge from START. Add an edge with source 'START'.")

    # --- Reachability from START ---
    reachable = set(nx.descendants(G, "__START__")) | {"__START__"}
    for node_id in nodes_cfg:
        if node_id not in reachable:
            errors.append(f"Node '{node_id}' is not reachable from START.")

    # --- Path to END ---
    ancestors_of_end = set(nx.ancestors(G, "__END__")) | {"__END__"}
    for node_id in nodes_cfg:
        if node_id in reachable and node_id not in ancestors_of_end:
            errors.append(f"Node '{node_id}' has no path to END.")

    # --- Cycle detection with retry safety check ---
    cycles = list(nx.simple_cycles(G))
    for cycle in cycles:
        cycle_nodes = [n for n in cycle if n not in ("__START__", "__END__")]
        if not cycle_nodes:
            continue
        # Check if at least one node in the cycle has max_retries config
        has_retry_limit = False
        for cn in cycle_nodes:
            node_def = nodes_cfg.get(cn, {})
            node_cfg = node_def.get("config", {})
            if "max_retries" in node_cfg:
                has_retry_limit = True
                break
        if not has_retry_limit:
            errors.append(
                f"Cycle detected: {' → '.join(cycle_nodes)}. "
                f"Add 'max_retries' config to at least one node in the cycle "
                f"to prevent infinite loops."
            )

    return errors
