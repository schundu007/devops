"""Tests for DC-SEC-01 Path Traversal Guard."""
from __future__ import annotations

import posixpath
import random

import pytest
from chip import load_impl

impl = load_impl(__file__)


@pytest.mark.parametrize(
    "path,expected",
    [
        ("/srv/app/", "/srv/app"),
        ("/srv//app/./config/", "/srv/app/config"),
        ("/srv/app/../../etc/passwd", "/etc/passwd"),
        ("/../../..", "/"),
        ("/a/.../b", "/a/.../b"),  # "..." is an ordinary name
    ],
)
def test_normalize_normal_cases(path, expected):
    assert impl.normalize_path(path) == expected


def test_empty_and_root():
    assert impl.normalize_path("") == "/"
    assert impl.normalize_path("/") == "/"
    assert impl.normalize_path("////") == "/"


def test_traversal_is_blocked():
    root = "/srv/app/uploads"
    assert impl.is_within_root(root, "avatars/u-1042.png")
    assert not impl.is_within_root(root, "../../../etc/passwd")
    assert not impl.is_within_root(root, "/etc/shadow")
    assert impl.is_within_root(root, "a/b/../../c.txt")  # wanders but ends inside


def test_prefix_boundary_is_by_segment():
    # Boundary: a sibling directory that shares the text prefix must fail.
    assert not impl.is_within_root("/srv/app", "/srv/app2/secret.env")
    assert not impl.is_within_root("/srv/app", "../app2/secret.env")
    assert impl.is_within_root("/srv/app", "/srv/app")        # the root itself
    assert impl.is_within_root("/srv/app/", "/srv/app/x")     # trailing slash on root


def test_production_static_file_handler():
    # A request to GET /static/<name> on 10.0.4.12 maps names under /var/www/static.
    root = "/var/www/static"
    attacks = [
        "../../../../etc/passwd",
        "css/../../../../root/.ssh/id_rsa",
        "..//..//..//proc/self/environ",
        "./.././../www/static/../../../etc/hosts",
    ]
    assert not any(impl.is_within_root(root, a) for a in attacks)
    assert impl.is_within_root(root, "css/site.css")
    assert impl.is_within_root(root, "js/./vendor/../app.js")


def test_large_random_matches_posixpath():
    rng = random.Random(71)
    parts = ["a", "b", "etc", ".", "..", "...", "", "srv"]
    for _ in range(3_000):
        p = "/" + "/".join(rng.choice(parts) for _ in range(rng.randint(0, 40)))
        # Independent reference: the standard library, with the leading slashes
        # squashed first (POSIX keeps exactly two leading slashes as special).
        expected = posixpath.normpath("/" + p.lstrip("/"))
        assert impl.normalize_path(p) == expected, p
    long_path = "/" + "/".join(["x", ".."] * 50_000 + ["final"])
    assert impl.normalize_path(long_path) == "/final"
