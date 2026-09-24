"""DC-NET-03 Capacity & Traffic Ratio Calculator — reference solution."""
from __future__ import annotations

from collections import defaultdict, deque


def calc_ratios(
    facts: list[tuple[str, str]],
    values: list[float],
    queries: list[tuple[str, str]],
) -> list[float]:
    """facts[i] = (a, b) with values[i] = v means "one a holds v of b".

    For each query (x, y) return how many y one x holds, or -1.0 if it cannot be derived.
    """
    # Weighted directed graph: edge a -> b with weight v, and b -> a with 1/v.
    graph: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for (a, b), v in zip(facts, values):
        graph[a].append((b, v))
        graph[b].append((a, 1.0 / v))

    def ratio(x: str, y: str) -> float:
        if x not in graph or y not in graph:
            return -1.0
        # BFS from x, carrying the product of edge weights along the path.
        seen = {x}
        queue = deque([(x, 1.0)])
        while queue:
            node, acc = queue.popleft()
            if node == y:
                return acc
            for nxt, w in graph[node]:
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, acc * w))  # ratios multiply along a chain
        return -1.0

    return [ratio(x, y) for x, y in queries]
