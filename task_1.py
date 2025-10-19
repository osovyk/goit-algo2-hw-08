#!/usr/bin/env python3
from __future__ import annotations
import argparse
import random
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import List, Tuple

class LRUCache:
    def __init__(self, capacity: int = 1000) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._od: OrderedDict = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key):
        if key in self._od:
            self._od.move_to_end(key)
            self.hits += 1
            return self._od[key]
        self.misses += 1
        return -1

    def put(self, key, value) -> None:
        if key in self._od:
            self._od.move_to_end(key)
        self._od[key] = value
        if len(self._od) > self.capacity:
            self._od.popitem(last=False)

    def keys(self):
        return self._od.keys()

Query = Tuple[str, int, int]

def make_queries(n: int, q: int, hot_pool: int = 30, p_hot: float = 0.95, p_update: float = 0.03) -> List[Query]:
    hot = [(random.randint(0, n // 2), random.randint(n // 2, n - 1)) for _ in range(hot_pool)]
    queries: List[Query] = []
    for _ in range(q):
        if random.random() < p_update:
            idx = random.randint(0, n - 1)
            val = random.randint(1, 100)
            queries.append(("Update", idx, val))
        else:
            if random.random() < p_hot:
                left, right = random.choice(hot)
            else:
                left = random.randint(0, n - 1)
                right = random.randint(left, n - 1)
            queries.append(("Range", left, right))
    return queries

def range_sum_no_cache(array: List[int], left: int, right: int) -> int:
    return sum(array[left:right + 1])

def update_no_cache(array: List[int], index: int, value: int) -> None:
    array[index] = value

def range_sum_with_cache(array: List[int], left: int, right: int, cache: LRUCache) -> int:
    key = (left, right)
    cached = cache.get(key)
    if cached != -1:
        return cached
    total = sum(array[left:right + 1])
    cache.put(key, total)
    return total

def update_with_cache(array: List[int], index: int, value: int, cache: LRUCache) -> None:
    array[index] = value
    to_delete: List[Tuple[int, int]] = []
    for (l, r) in list(cache.keys()):
        if l <= index <= r:
            to_delete.append((l, r))
    for k in to_delete:
        if k in cache._od:
            del cache._od[k]

@dataclass
class RunStats:
    seconds: float
    hits: int = 0
    misses: int = 0

def run_no_cache(array: List[int], queries: List[Query]) -> RunStats:
    start = time.perf_counter()
    total_sink = 0
    for typ, a, b in queries:
        if typ == "Range":
            total_sink ^= range_sum_no_cache(array, a, b)
        else:
            update_no_cache(array, a, b)
    elapsed = time.perf_counter() - start
    return RunStats(seconds=elapsed)

def run_with_cache(array: List[int], queries: List[Query], k_capacity: int) -> RunStats:
    cache = LRUCache(capacity=k_capacity)
    start = time.perf_counter()
    total_sink = 0
    for typ, a, b in queries:
        if typ == "Range":
            total_sink ^= range_sum_with_cache(array, a, b, cache)
        else:
            update_with_cache(array, a, b, cache)
    elapsed = time.perf_counter() - start
    return RunStats(seconds=elapsed, hits=cache.hits, misses=cache.misses)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=100_000)
    parser.add_argument("--q", type=int, default=50_000)
    parser.add_argument("--k", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    N, Q, K = args.n, args.q, args.k
    random.seed(args.seed)
    base_array = [random.randint(1, 100) for _ in range(N)]
    queries = make_queries(N, Q, hot_pool=30, p_hot=0.95, p_update=0.03)
    arr_no_cache = base_array.copy()
    arr_with_cache = base_array.copy()
    stats_no = run_no_cache(arr_no_cache, queries)
    stats_lru = run_with_cache(arr_with_cache, queries, k_capacity=K)
    accel = (stats_no.seconds / stats_lru.seconds) if stats_lru.seconds > 0 else float("inf")
    print(f"Без кешу : {stats_no.seconds:7.2f} c")
    print(f"LRU-кеш  : {stats_lru.seconds:7.2f} c  (прискорення ×{accel:0.1f})")
    total_lookups = stats_lru.hits + stats_lru.misses
    hit_rate = (stats_lru.hits / total_lookups * 100.0) if total_lookups else 0.0
    print(f"  Влучень у кеш: {stats_lru.hits:,}")
    print(f"  Промахів     : {stats_lru.misses:,}")
    print(f"  Hit-rate     : {hit_rate:0.1f}%")

if __name__ == "__main__":
    main()
