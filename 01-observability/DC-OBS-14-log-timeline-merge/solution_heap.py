# (added) Min-heap k-way merge — DevOps layer, not from the handbook.
# The handbook's hints describe this approach; its stored solutions use a
# linear scan and divide-and-conquer instead. ListNode is provided by the
# runner, the same way the handbook's own code expects it.
import heapq


def mergeKLists(lists):
    heap = []
    for i, node in enumerate(lists):
        if node:
            heap.append((node.val, i, node))  # i breaks ties so nodes are never compared
    heapq.heapify(heap)
    dummy = tail = ListNode(0)
    while heap:
        _, i, node = heapq.heappop(heap)
        tail.next = node
        tail = node
        if node.next:
            heapq.heappush(heap, (node.next.val, i, node.next))
    return dummy.next
