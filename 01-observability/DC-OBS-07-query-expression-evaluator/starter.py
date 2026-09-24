"""DC-OBS-07 Query Expression Evaluator — your attempt.

Run your code against the tests:
    make try CHIP=01-observability/DC-OBS-07-query-expression-evaluator
"""
from __future__ import annotations


def evaluate(expr: str, values: dict[str, int]) -> int:
    """Evaluate an expression made of:

    - non-negative integers, e.g. 100
    - metric names ([A-Za-z_][A-Za-z0-9_]*), replaced by values[name]
    - binary + and -, parentheses, and spaces
    - unary minus, only at the very start or right after '('

    Raise KeyError for a metric name missing from `values`.
    """
    # TODO
    raise NotImplementedError
