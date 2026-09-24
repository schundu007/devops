"""Shared helpers for chip tests.

Every chip folder holds starter.py and solution.py. Tests run against
solution.py by default. Set CHIP_TARGET=starter to run the same tests
against your own attempt in starter.py (see `make try`).
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


def load_impl(test_file: str) -> ModuleType:
    """Load starter.py or solution.py from the folder that holds test_file."""
    target = os.environ.get("CHIP_TARGET", "solution")
    path = Path(test_file).parent / f"{target}.py"
    name = f"{Path(test_file).parent.name}_{target}".replace("-", "_")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    # Register before exec: @dataclass looks its module up in sys.modules.
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def handbook(test_file: str) -> dict[str, Any]:
    """Return the handbook entry copied unchanged into this chip (handbook.json)."""
    return json.loads((Path(test_file).parent / "handbook.json").read_text())


def handbook_solutions(test_file: str) -> list[tuple[str, ModuleType]]:
    """Every Python solution stored in handbook.json, each loaded as its own module.

    Used for the Step 3 check: the copied tests must pass on the copied code.
    """
    out = []
    for i, sol in enumerate(handbook(test_file)["solutions"]):
        module = ModuleType(f"handbook_solution_{i}")
        exec(sol["code"]["python"], module.__dict__)
        out.append((sol["name"], module))
    return out


def case_id(case: dict[str, Any]) -> str:
    return case.get("why", {}).get("t", "case")


def run_handbook_case(module: ModuleType, spec: dict[str, Any], args: dict[str, Any]) -> Any:
    """Run one handbook case the way the handbook's own runner does.

    spec["kind"] == "fn":     Solution().<fn>(*args in spec["params"] order)
    spec["kind"] == "design": args["ops"][0] is the class name; the rest are
                              method calls with args["vals"]; returns one result
                              per op (None for the constructor and void calls).
    """
    if spec["kind"] == "fn":
        fn = getattr(module.Solution(), spec["fn"])
        return fn(*[args[p] for p in spec["params"]])
    if spec["kind"] == "design":
        ops, vals = args["ops"], args["vals"]
        obj = getattr(module, ops[0])(*vals[0])
        out: list[Any] = [None]
        for op, v in zip(ops[1:], vals[1:]):
            out.append(getattr(obj, op)(*v))
        return out
    raise ValueError(f"unknown spec kind {spec['kind']!r}")
