"""DC-OBS-14 Multi-Node Log Timeline Merge — your attempt.  (added: the handbook has no stored starter)

Signature matches Source: Handbook #24 Merge K Sorted Lists: a top-level
`mergeKLists(lists)`. The test runner provides ListNode, just like the handbook does;
the class below is only here so your editor knows its shape.
Run your code against the tests:
    make try CHIP=01-observability/DC-OBS-14-log-timeline-merge
"""
from typing import List, Optional


class ListNode:
    def __init__(self, val: int = 0, next: "Optional[ListNode]" = None):
        self.val = val
        self.next = next


def mergeKLists(lists: List[Optional[ListNode]]) -> Optional[ListNode]:
    """Merge k sorted linked lists into one sorted linked list and return its head."""
    # TODO
    raise NotImplementedError
