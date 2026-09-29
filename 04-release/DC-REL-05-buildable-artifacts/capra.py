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

VARIANT_TITLE = "What can we build?"
VARIANT_APPROACH = "Kahn's algorithm seeded with what you have · O(A + I + V) · O(A + I + V)"

_WAVES_FAST = '''from __future__ import annotations

from collections import defaultdict


def build_waves(artifacts: list[str], inputs: list[list[str]], available: list[str]) -> list[list[str]]:
    missing = [len(ins) for ins in inputs]
    used_by: dict[str, list[int]] = defaultdict(list)
    for i, ins in enumerate(inputs):
        for name in ins:
            used_by[name].append(i)
    current = [i for i, m in enumerate(missing) if m == 0]
    for name in available:
        for i in used_by[name]:
            missing[i] -= 1
            if missing[i] == 0:
                current.append(i)
    waves = []
    while current:
        waves.append(sorted(artifacts[i] for i in current))
        nxt = []
        for i in current:
            for j in used_by[artifacts[i]]:
                missing[j] -= 1
                if missing[j] == 0:
                    nxt.append(j)
        current = nxt
    return waves
'''

_WAVES_SLOW = '''from __future__ import annotations


def build_waves(artifacts: list[str], inputs: list[list[str]], available: list[str]) -> list[list[str]]:
    have = set(available)
    done = [False] * len(artifacts)
    waves = []
    while True:
        wave = [i for i, name in enumerate(artifacts) if not done[i] and all(x in have for x in inputs[i])]
        if not wave:
            return waves
        for i in wave:
            done[i] = True
            have.add(artifacts[i])
        waves.append(sorted(artifacts[i] for i in wave))
'''

_FINISH_FAST = '''from __future__ import annotations

from collections import defaultdict, deque


def earliest_finish(artifacts: list[str], inputs: list[list[str]], durations: list[int], available: list[str]) -> list[int]:
    n = len(artifacts)
    missing = [len(ins) for ins in inputs]
    used_by: dict[str, list[int]] = defaultdict(list)
    for i, ins in enumerate(inputs):
        for name in ins:
            used_by[name].append(i)
    start = [0] * n
    finish = [-1] * n
    ready: deque[tuple[str, int]] = deque((name, 0) for name in available)
    for i in range(n):
        if missing[i] == 0:
            finish[i] = durations[i]
            ready.append((artifacts[i], finish[i]))
    while ready:
        name, t = ready.popleft()
        for i in used_by[name]:
            start[i] = max(start[i], t)
            missing[i] -= 1
            if missing[i] == 0:
                finish[i] = start[i] + durations[i]
                ready.append((artifacts[i], finish[i]))
    return finish
'''

_FINISH_SLOW = '''from __future__ import annotations


def earliest_finish(artifacts: list[str], inputs: list[list[str]], durations: list[int], available: list[str]) -> list[int]:
    ready_at = {name: 0 for name in available}
    finish = [-1] * len(artifacts)
    changed = True
    while changed:
        changed = False
        for i, name in enumerate(artifacts):
            if finish[i] == -1 and all(x in ready_at for x in inputs[i]):
                start = max((ready_at[x] for x in inputs[i]), default=0)
                finish[i] = start + durations[i]
                ready_at[name] = finish[i]
                changed = True
    return finish
'''


def _wcase(artifacts, inputs, available):
    return {"artifacts": artifacts, "inputs": inputs, "available": available}


def _fcase(artifacts, inputs, durations, available):
    return {"artifacts": artifacts, "inputs": inputs, "durations": durations, "available": available}


def _graph(seed, n):
    rng = random.Random(seed)
    base = [f"base-{i}" for i in range(10)]
    artifacts = [f"target-{i}" for i in range(n)]
    inputs = []
    for i in range(n):
        need = rng.sample(base + artifacts[:i], rng.randint(0, 3))
        if rng.random() < 0.05:
            need.append("missing-sdk")
        inputs.append(need)
    order = list(range(n))
    rng.shuffle(order)
    return [artifacts[i] for i in order], [inputs[i] for i in order], base[:8], rng


def _waves_large():
    a, ins, avail, _ = _graph(1301, 120)
    return _wcase(a, ins, avail)


def _finish_large():
    a, ins, avail, rng = _graph(1302, 120)
    return _fcase(a, ins, [rng.randint(1, 30) for _ in a], avail)


VARIANTS = [
    {
        "key": "build-waves",
        "title": "Parallel build stages",
        "approach": "Kahn's algorithm level by level · O(A + I + V + A log A) · O(A + I + V)",
        "spec": {"kind": "fn", "fn": "build_waves", "params": ["artifacts", "inputs", "available"]},
        "statement": (
            "The CI system runs builds in **stages**: every artifact in a stage builds in parallel, and a stage starts only when the previous one is done. Group the buildable artifacts into the fewest stages.\n"
            "\n"
            "### Input\n"
            "- `artifacts`, `inputs`, `available`: as in the main problem\n"
            "\n"
            "### Output\n"
            "- The stages in order, each sorted by name\n"
            "\n"
            "### Rules\n"
            "- Stage 1 holds every artifact whose inputs are all in `available` (or that has no inputs)\n"
            "- Stage k + 1 holds every artifact not built yet whose inputs are all in `available` or built in stages 1..k\n"
            "- Artifacts that can never be built do not appear"
        ),
        "examples": [
            {"args": _wcase(["app-image", "wheel-cache", "lint", "chart"],
                            [["python-base", "wheel-cache"], ["python-base"], [], ["app-image", "helm"]],
                            ["python-base", "helm"]),
             "explanation": "lint and wheel-cache need nothing new, app-image needs wheel-cache, and chart needs app-image: three stages.",
             "why": {"t": "Three stages", "d": "Each stage unlocks the next."}},
        ],
        "constraints": ["0 ≤ artifacts.length ≤ 200", "0 ≤ inputs[i].length ≤ 5", "artifact names are unique and never in available"],
        "hints": [
            "Seed the missing-input counts with everything in `available`, exactly like the main problem.",
            "Process the queue one level at a time: the artifacts released while handling stage k form stage k + 1.",
            "Sort each stage before adding it; the order inside a stage does not matter to CI.",
        ],
        "tests": [
            {"args": _wcase([], [], ["gcc"]), "why": {"t": "No artifacts", "d": "No stages."}},
            {"args": _wcase(["a"], [["gcc"]], []), "why": {"t": "Nothing buildable", "d": "No stages when nothing can start."}},
            {"args": _wcase(["c", "b", "a"], [[], [], []], []), "why": {"t": "One wide stage", "d": "Independent artifacts share stage 1, sorted."}},
            {"args": _wcase(["a", "b", "c", "d"], [["base"], ["a"], ["b"], ["c"]], ["base"]), "why": {"t": "Long chain", "d": "A chain needs one stage per link."}},
            {"args": _wcase(["x", "y", "z"], [["y"], ["x"], ["base", "base"]], ["base"]), "why": {"t": "Cycle and duplicate input", "d": "x and y wait on each other forever; z lists base twice."}},
            {"args": _wcase(["lib", "app", "test", "docs"], [["gcc"], ["lib", "gcc"], ["app", "lib"], []], ["gcc"]),
             "why": {"t": "Diamond", "d": "test needs both lib and app, so it waits for the later one."}},
            {"args": _waves_large(), "why": {"t": "Larger input", "d": "120 artifacts in shuffled order."}},
        ],
        "solutions": [
            {"name": "Level-by-level Kahn (Optimal)",
             "description": "Count missing inputs, release artifacts as inputs arrive, and process the released artifacts one level at a time so each level is a stage.",
             "time": "O(A + I + V + A log A)", "space": "O(A + I + V)",
             "keyPoints": ["Available items release stage 1", "Items released by stage k form stage k + 1", "Sort within each stage"],
             "code": _WAVES_FAST},
            {"name": "Scan all artifacts per stage", "slow": True,
             "description": "Each pass collects every unbuilt artifact whose inputs are all in hand, then adds the whole pass to the set at once as one stage.",
             "time": "O(S · (A + I)) for S stages", "space": "O(A + V)",
             "keyPoints": ["Add a stage's outputs only after the scan", "A long chain means many passes"],
             "code": _WAVES_SLOW},
        ],
        "starter": "def build_waves(artifacts: list[str], inputs: list[list[str]], available: list[str]) -> list[list[str]]:\n    pass\n",
    },
    {
        "key": "earliest-finish",
        "title": "Earliest finish with unlimited runners",
        "approach": "Kahn's algorithm carrying ready times · O(A + I + V) · O(A + I + V)",
        "spec": {"kind": "fn", "fn": "earliest_finish", "params": ["artifacts", "inputs", "durations", "available"]},
        "statement": (
            "With enough CI runners, find the minute each artifact's build finishes.\n"
            "\n"
            "### Input\n"
            "- `artifacts`, `inputs`, `available`: as in the main problem\n"
            "- `durations[i]`: minutes `artifacts[i]` takes to build\n"
            "\n"
            "### Output\n"
            "- For each artifact in the given order, the minute its build finishes, or `-1` if it can never be built\n"
            "- The largest value is the pipeline's critical path\n"
            "\n"
            "### Rules\n"
            "- An artifact starts the moment its **last** input is ready\n"
            "- Everything in `available` is ready at minute 0"
        ),
        "examples": [
            {"args": _fcase(["deps", "compile", "test", "image"], [["lockfile"], ["deps"], ["compile"], ["compile", "base-image"]],
                            [5, 10, 7, 3], ["lockfile", "base-image"]),
             "explanation": "deps 0 to 5, compile 5 to 15, then test (15 to 22) and image (15 to 18) run side by side.",
             "why": {"t": "Critical path", "d": "The finish time follows the slowest chain of inputs."}},
        ],
        "constraints": ["0 ≤ artifacts.length ≤ 200", "1 ≤ durations[i] ≤ 100", "artifact names are unique and never in available"],
        "hints": [
            "Run the main problem's Kahn queue, but carry each item's ready time with it.",
            "When an input reaches an artifact, raise that artifact's start to the input's ready time.",
            "When the last input arrives, finish = start + duration; queue the artifact with that time.",
        ],
        "tests": [
            {"args": _fcase([], [], [], []), "why": {"t": "No artifacts", "d": "An empty pipeline."}},
            {"args": _fcase(["solo"], [[]], [4], []), "why": {"t": "No inputs", "d": "Starts at minute 0."}},
            {"args": _fcase(["a", "b"], [["b"], ["a"]], [1, 1], []), "why": {"t": "Cycle", "d": "Neither can start: both -1."}},
            {"args": _fcase(["slow", "fast", "join"], [[], [], ["slow", "fast"]], [30, 2, 1], []),
             "why": {"t": "Waits for the slowest", "d": "join starts only when slow finishes at 30."}},
            {"args": _fcase(["x", "y"], [["gcc", "gcc"], ["x", "missing"]], [3, 3], ["gcc"]),
             "why": {"t": "Duplicate and missing inputs", "d": "x lists gcc twice; y never gets its missing input."}},
            {"args": _fcase(["c", "b", "a"], [["b"], ["a"], []], [1, 2, 3], []),
             "why": {"t": "Listed in reverse", "d": "Output follows the input order, not the build order."}},
            {"args": _finish_large(), "why": {"t": "Larger input", "d": "120 artifacts with random durations."}},
        ],
        "solutions": [
            {"name": "Kahn with ready times (Optimal)",
             "description": "Queue (name, ready time) pairs, starting with the available items at 0. Each arrival raises the artifact's start time; the last one sets finish = start + duration and queues it.",
             "time": "O(A + I + V)", "space": "O(A + I + V)",
             "keyPoints": ["start = max of the inputs' ready times", "Queue order does not matter for the max", "Unreleased artifacts stay -1"],
             "code": _FINISH_FAST},
            {"name": "Repeat until nothing changes", "slow": True,
             "description": "Scan every artifact again and again; once all its inputs have ready times, set its finish from the latest one. Stop when a pass changes nothing.",
             "time": "O(A · (A + I))", "space": "O(A + V)",
             "keyPoints": ["Simple fixed point", "May need one pass per chain link"],
             "code": _FINISH_SLOW},
        ],
        "starter": "def earliest_finish(artifacts: list[str], inputs: list[list[str]], durations: list[int], available: list[str]) -> list[int]:\n    pass\n",
    },
]
