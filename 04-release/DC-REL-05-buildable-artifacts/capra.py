"""Capra Playground export for DC-REL-05 (see tools/export_capra.py). Any order is accepted."""
import random

SPEC = {"kind": "fn", "fn": "buildable", "params": ["artifacts", "inputs", "available"], "types": {}, "ret": "value", "cmp": "unordered"}


def case(artifacts, inputs, available):
    return {"artifacts": artifacts, "inputs": inputs, "available": available}


EXAMPLES = [
    {"args": case(["app-image", "wheel-cache", "docs-site"],
                  [["python-base", "wheel-cache"], ["python-base", "requirements.txt"], ["hugo", "wheel-cache"]],
                  ["python-base", "requirements.txt"]),
     "explanation": "wheel-cache needs only things we have. Once it is built, app-image can use it. docs-site also needs hugo, which nobody provides.",
     "why": {"t": "Chained artifacts", "d": "One built artifact feeds another."}},
    {"args": case(["hello-bin"], [["gcc"]], []),
     "explanation": "Nothing is available, so the only artifact cannot be built.",
     "why": {"t": "Nothing available", "d": "An empty toolbox builds nothing."}},
    {"args": case(["docs-site"], [[]], []),
     "explanation": "An artifact with no inputs can always be built.",
     "why": {"t": "No inputs", "d": "Zero requirements means buildable right away."}},
]


def _large():
    rng = random.Random(2115)
    base = [f"base-{i}" for i in range(20)]
    artifacts = [f"artifact-{i}" for i in range(250)]
    inputs = []
    for i in range(250):
        pool = base + artifacts[:i]
        need = rng.sample(pool, rng.randint(1, 3))
        if rng.random() < 0.05:
            need.append("missing-tool")
        inputs.append(need)
    return case(artifacts, inputs, base[:15])


TESTS = [
    {"args": case([], [], ["gcc"]), "why": {"t": "No artifacts", "d": "Nothing to build."}},
    {"args": case(["hello-bin"], [["gcc"]], ["gcc"]), "why": {"t": "Single artifact", "d": "One artifact with its one input available."}},
    {"args": case(["a", "b"], [["b"], ["a"]], ["base"]), "why": {"t": "Cycle", "d": "Two artifacts that need each other can never be built."}},
    {"args": case(["a", "b", "c"], [["base"], ["a"], ["b", "missing"]], ["base"]), "why": {"t": "Chain stops at a gap", "d": "a and b build; c also needs something nobody has."}},
    {"args": case(["svc"], [["libssl", "libssl"]], ["libssl"]), "why": {"t": "Duplicate input", "d": "The same input listed twice."}},
    {"args": case(["x", "y"], [["x"], []], []), "why": {"t": "Self-dependency", "d": "x needs itself and is never buildable; y has no inputs."}},
    {"args": case(["grpc-gen", "api-image", "api-chart"],
                  [["protoc", "api.proto"], ["distroless", "grpc-gen"], ["api-image", "helm"]],
                  ["distroless", "api.proto", "helm"]),
     "why": {"t": "No protoc", "d": "Without protoc the code generator cannot run, so nothing downstream builds."}},
    {"args": case(["lib", "app", "test"], [["gcc"], ["lib", "gcc"], ["app", "lib"]], ["gcc"]),
     "why": {"t": "Diamond", "d": "Two paths reach the same artifact."}},
    {"args": _large(), "why": {"t": "Large input", "d": "250 artifacts, each needing up to three earlier ones."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Topological sort from what you have (Optimal)",
     "description": "Count the missing inputs of each artifact and index which artifacts use each input. Start a queue with everything available; each item taken off the queue lowers the count of the artifacts that use it, and an artifact whose count reaches 0 is built and queued too.",
     "time": "O(A + I + V)", "space": "O(A + I + V)",
     "keyPoints": ["Kahn's algorithm seeded with the available items", "An artifact with no inputs is built at once", "Artifacts in a cycle never reach 0 missing inputs"]},
    {"name": "Repeat until nothing changes", "slow": True,
     "description": "Keep a set of what you have. Scan every artifact; build any whose inputs are all in the set. Repeat full scans until one scan builds nothing.",
     "time": "O(A · I) scans", "space": "O(A + V)",
     "keyPoints": ["Easy to get right", "Each pass may build only one new artifact, so it can take A passes"],
     "code": '''from __future__ import annotations


def buildable(artifacts: list[str], inputs: list[list[str]], available: list[str]) -> list[str]:
    have = set(available)
    built: list[str] = []
    done = [False] * len(artifacts)
    changed = True
    while changed:
        changed = False
        for i, name in enumerate(artifacts):
            if not done[i] and all(x in have for x in inputs[i]):
                done[i] = True
                built.append(name)
                have.add(name)
                changed = True
    return built
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Fixed-point iteration", "idea": "Scan all artifacts again and again, building what you can, until a pass builds nothing.",
     "time": "O(A · I)", "space": "O(A + V)", "use": "Small build graphs; simplest to explain."},
    {"name": "Kahn's algorithm", "idea": "Track missing-input counts and release an artifact the moment its last input arrives.",
     "time": "O(A + I + V)", "space": "O(A + I + V)", "use": "Large build graphs like Bazel or Make targets."},
]
