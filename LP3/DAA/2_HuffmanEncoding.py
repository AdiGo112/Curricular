import heapq
from collections import Counter


def build_tree(text):
    heap = [(freq, i, ch) for i, (ch, freq) in enumerate(Counter(text).items())]
    heapq.heapify(heap)
    next_id = len(heap)
    while len(heap) > 1:
        freq1, _, left = heapq.heappop(heap)
        freq2, _, right = heapq.heappop(heap)
        heapq.heappush(heap, (freq1 + freq2, next_id, (left, right)))
        next_id += 1
    return heap[0][2]


def print_codes(node, code=""):
    if isinstance(node, str):
        print(f"{node} : {code or '0'}")
        return
    print_codes(node[0], code + "0")
    print_codes(node[1], code + "1")


text = input("Enter text: ")
if text:
    print_codes(build_tree(text))
