#!/usr/bin/env python3
"""Clock (second-chance) cache eviction algorithm.

One file. Zero deps. Does one thing well.

Approximates LRU with O(1) amortized eviction using a circular buffer
and reference bits. Used in OS page replacement and database buffer pools.
"""
import sys

class ClockCache:
    def __init__(self, capacity):
        self.cap = capacity
        self.entries = {}      # key -> (value, slot)
        self.slots = [None] * capacity  # (key, ref_bit)
        self.hand = 0
        self.count = 0

    def get(self, key):
        if key not in self.entries:
            return None
        val, slot = self.entries[key]
        # Set reference bit
        self.slots[slot] = (key, True)
        return val

    def put(self, key, value):
        if key in self.entries:
            _, slot = self.entries[key]
            self.entries[key] = (value, slot)
            self.slots[slot] = (key, True)
            return
        if self.count >= self.cap:
            self._evict()
        slot = self._find_free()
        self.entries[key] = (value, slot)
        self.slots[slot] = (key, True)
        self.count += 1

    def _find_free(self):
        for i in range(self.cap):
            if self.slots[i] is None:
                return i
        return self.hand  # shouldn't reach here after evict

    def _evict(self):
        while True:
            entry = self.slots[self.hand]
            if entry is None:
                self.hand = (self.hand + 1) % self.cap
                continue
            key, ref = entry
            if ref:
                # Second chance: clear ref bit
                self.slots[self.hand] = (key, False)
                self.hand = (self.hand + 1) % self.cap
            else:
                # Evict this entry
                del self.entries[key]
                self.slots[self.hand] = None
                self.count -= 1
                slot = self.hand
                self.hand = (self.hand + 1) % self.cap
                return slot

    def __len__(self):
        return self.count

    def __contains__(self, key):
        return key in self.entries

    def hit_rate(self, accesses, hits):
        return hits / accesses if accesses else 0.0

def main():
    cache = ClockCache(5)
    accesses = [1, 2, 3, 4, 5, 1, 2, 6, 1, 2, 3, 7, 1, 2, 3]
    hits = 0
    for key in accesses:
        if cache.get(key) is not None:
            hits += 1
        else:
            cache.put(key, f"val-{key}")
    print(f"Clock Cache (capacity=5)")
    print(f"Access sequence: {accesses}")
    print(f"Hits: {hits}/{len(accesses)} ({hits/len(accesses):.0%})")
    print(f"Final cache: {sorted(cache.entries.keys())}")
    
    # Compare with FIFO
    from collections import OrderedDict
    fifo = OrderedDict()
    fifo_hits = 0
    for key in accesses:
        if key in fifo:
            fifo_hits += 1
        else:
            if len(fifo) >= 5:
                fifo.popitem(last=False)
            fifo[key] = True
    print(f"\nFIFO hits: {fifo_hits}/{len(accesses)} ({fifo_hits/len(accesses):.0%})")
    print(f"Clock advantage: second-chance avoids evicting recently used pages")

if __name__ == "__main__":
    main()
