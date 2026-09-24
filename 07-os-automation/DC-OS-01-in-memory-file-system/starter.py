"""DC-OS-01 In-Memory File System — your attempt.

Run your code against the tests:
    make try CHIP=07-os-automation/DC-OS-01-in-memory-file-system
"""
from __future__ import annotations


class FileSystem:
    def __init__(self) -> None:
        # TODO: choose a structure for directories and files.
        pass

    def ls(self, path: str) -> list[str]:
        """If `path` is a file, return [its name]. If it is a directory, return the
        names of its direct children in lexicographic order."""
        # TODO
        raise NotImplementedError

    def mkdir(self, path: str) -> None:
        """Create the directory, and any missing parent directories."""
        # TODO
        raise NotImplementedError

    def write(self, path: str, content: str) -> None:
        """Append `content` to the file at `path`, creating it (and missing parents) first."""
        # TODO
        raise NotImplementedError

    def read(self, path: str) -> str:
        """Return the full content of the file at `path`."""
        # TODO
        raise NotImplementedError
