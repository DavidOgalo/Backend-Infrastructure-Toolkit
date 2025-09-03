"""
A generic, production-ready hash table implementation for fast lookups, insertions, and deletions.
Suitable for use as a utility in backend systems (caching, session management, etc).
"""

from typing import Generic, Hashable, Iterator, List, Optional, Tuple, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


class HashTable(Generic[K, V]):
    """
    Generic hash table for caching and fast lookups.
    Supports any hashable key type and provides Pythonic dunder methods.
    """

    def __init__(self, initial_size: int = 16, load_factor_threshold: float = 0.75):
        self._size = initial_size
        self._count = 0
        self._buckets: List[List[Tuple[K, V]]] = [[] for _ in range(self._size)]
        self._load_factor_threshold = load_factor_threshold

    def _hash(self, key: K) -> int:
        return hash(key) % self._size

    def _resize(self) -> None:
        old_buckets = self._buckets
        self._size *= 2
        self._count = 0
        self._buckets = [[] for _ in range(self._size)]
        for bucket in old_buckets:
            for key, value in bucket:
                self[key] = value

    def __setitem__(self, key: K, value: V) -> None:
        if self._count >= self._size * self._load_factor_threshold:
            self._resize()
        hash_index = self._hash(key)
        bucket = self._buckets[hash_index]
        for idx, (k, _) in enumerate(bucket):
            if k == key:
                bucket[idx] = (key, value)
                return
        bucket.append((key, value))
        self._count += 1

    def __getitem__(self, key: K) -> V:
        hash_index = self._hash(key)
        bucket = self._buckets[hash_index]
        for k, v in bucket:
            if k == key:
                return v
        raise KeyError(key)

    def __delitem__(self, key: K) -> None:
        hash_index = self._hash(key)
        bucket = self._buckets[hash_index]
        for idx, (k, _) in enumerate(bucket):
            if k == key:
                del bucket[idx]
                self._count -= 1
                return
        raise KeyError(key)

    def __contains__(self, key: K) -> bool:
        hash_index = self._hash(key)
        bucket = self._buckets[hash_index]
        return any(k == key for k, _ in bucket)

    def __len__(self) -> int:
        return self._count

    def __iter__(self) -> Iterator[K]:
        for bucket in self._buckets:
            for k, _ in bucket:
                yield k

    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        try:
            return self[key]
        except KeyError:
            return default

    def set(self, key: K, value: V) -> None:
        self[key] = value

    def delete(self, key: K) -> bool:
        try:
            del self[key]
            return True
        except KeyError:
            return False
