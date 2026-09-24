"""DC-OS-01 In-Memory File System — reference solution (tree of path segments)."""
from __future__ import annotations


class _Node:
    __slots__ = ("children", "is_file", "content")

    def __init__(self) -> None:
        self.children: dict[str, _Node] = {}
        self.is_file = False
        self.content: list[str] = []  # appended chunks, joined on read


class FileSystem:
    def __init__(self) -> None:
        self._root = _Node()

    @staticmethod
    def _parts(path: str) -> list[str]:
        # "/a/b/c" -> ["a", "b", "c"]; "/" -> []
        return [p for p in path.split("/") if p]

    def _walk(self, path: str, create: bool) -> _Node | None:
        node = self._root
        for part in self._parts(path):
            nxt = node.children.get(part)
            if nxt is None:
                if not create:
                    return None
                nxt = node.children[part] = _Node()
            node = nxt
        return node

    def ls(self, path: str) -> list[str]:
        """A file lists as its own name; a directory lists its children, sorted."""
        node = self._walk(path, create=False)
        if node is None:
            return []
        if node.is_file:
            return [self._parts(path)[-1]]
        return sorted(node.children)

    def mkdir(self, path: str) -> None:
        """Create the directory and any missing parents (like `mkdir -p`)."""
        self._walk(path, create=True)

    def write(self, path: str, content: str) -> None:
        """Append to the file, creating it (and missing parents) if needed."""
        node = self._walk(path, create=True)
        node.is_file = True
        node.content.append(content)

    def read(self, path: str) -> str:
        """Return the whole content of the file."""
        node = self._walk(path, create=False)
        return "".join(node.content) if node is not None and node.is_file else ""
