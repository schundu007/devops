"""Tests for DC-OS-01 In-Memory File System."""
from __future__ import annotations

import random

import pytest
from chip import load_impl

impl = load_impl(__file__)


@pytest.fixture
def fs():
    return impl.FileSystem()


class FlatReference:
    """Independent reference: a flat set of directories and a dict of files."""

    def __init__(self) -> None:
        self.dirs: set[str] = {""}
        self.files: dict[str, str] = {}

    def _mk_parents(self, parts: list[str]) -> None:
        for i in range(1, len(parts) + 1):
            self.dirs.add("/".join(parts[:i]))

    def ls(self, path: str) -> list[str]:
        key = "/".join(p for p in path.split("/") if p)
        if key in self.files:
            return [key.split("/")[-1]]
        prefix = key + "/" if key else ""
        names = {k[len(prefix):].split("/")[0] for k in list(self.dirs) + list(self.files)
                 if k.startswith(prefix) and k != key}
        return sorted(n for n in names if n)

    def mkdir(self, path: str) -> None:
        self._mk_parents([p for p in path.split("/") if p])

    def write(self, path: str, content: str) -> None:
        parts = [p for p in path.split("/") if p]
        self._mk_parents(parts[:-1])
        key = "/".join(parts)
        self.files[key] = self.files.get(key, "") + content

    def read(self, path: str) -> str:
        return self.files.get("/".join(p for p in path.split("/") if p), "")

    def dirs_as_paths(self) -> set[str]:
        return {"/" + d for d in self.dirs if d}


def test_empty_root(fs):
    assert fs.ls("/") == []


def test_mkdir_creates_parents(fs):
    fs.mkdir("/a/b/c")
    assert fs.ls("/") == ["a"]
    assert fs.ls("/a") == ["b"]
    assert fs.ls("/a/b/c") == []


def test_write_append_and_read(fs):
    fs.write("/a/b/c/d", "hello")
    fs.write("/a/b/c/d", " world")
    assert fs.read("/a/b/c/d") == "hello world"
    assert fs.ls("/a/b/c") == ["d"]


def test_ls_on_a_file_returns_its_name(fs):
    fs.write("/etc/hosts", "127.0.0.1 localhost\n")
    assert fs.ls("/etc/hosts") == ["hosts"]


def test_ls_is_sorted_and_mixes_files_and_dirs(fs):
    fs.mkdir("/srv/zeta")
    fs.write("/srv/alpha.txt", "x")
    fs.mkdir("/srv/Beta")
    fs.write("/srv/mid", "y")
    assert fs.ls("/srv") == ["Beta", "alpha.txt", "mid", "zeta"]  # plain string order


def test_configmap_volume(fs):
    # Production flavour: a ConfigMap mounted at /etc/config with two keys,
    # plus a sidecar writing to a log file under /var/log/app.
    fs.write("/etc/config/app.yaml", "replicas: 3\n")
    fs.write("/etc/config/feature-flags.json", "{\"canary\": true}")
    fs.write("/var/log/app/sidecar.log", "10:00:01 start\n")
    fs.write("/var/log/app/sidecar.log", "10:00:02 ready\n")
    assert fs.ls("/etc/config") == ["app.yaml", "feature-flags.json"]
    assert fs.read("/var/log/app/sidecar.log") == "10:00:01 start\n10:00:02 ready\n"
    assert fs.ls("/") == ["etc", "var"]


def test_random_ops_match_flat_reference(fs):
    rng = random.Random(588)
    ref = FlatReference()
    names = ["a", "b", "c", "d"]
    files_made: set[str] = set()
    for _ in range(3_000):
        depth = rng.randint(1, 4)
        path = "/" + "/".join(rng.choice(names) for _ in range(depth))
        # Keep the input valid: never use an existing file as a directory, or the reverse.
        clash = any(path.startswith(f + "/") for f in files_made) or any(
            f.startswith(path + "/") for f in files_made)
        op = rng.random()
        if op < 0.3 and not clash and path not in files_made:
            fs.mkdir(path)
            ref.mkdir(path)
        elif op < 0.6 and not clash and path not in ref.dirs_as_paths():
            text = rng.choice(["x", "yz", ""])
            fs.write(path, text)
            ref.write(path, text)
            files_made.add(path)
        elif op < 0.8:
            assert fs.ls(path) == ref.ls(path), path
        elif path in files_made:
            assert fs.read(path) == ref.read(path), path
    assert fs.ls("/") == ref.ls("/")


def test_large_tree(fs):
    for i in range(2_000):
        fs.write(f"/data/shard-{i % 50:02d}/seg-{i:05d}.log", "ok")
    assert len(fs.ls("/data")) == 50
    assert len(fs.ls("/data/shard-07")) == 40
    assert fs.read("/data/shard-07/seg-00007.log") == "ok"
