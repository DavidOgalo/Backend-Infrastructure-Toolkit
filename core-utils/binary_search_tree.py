"""
A generic, production-ready Binary Search Tree (BST) implementation for ordered data access, range queries, and indexing.
Supports any comparable key type and is suitable for use as a utility in backend systems.
"""
from typing import Optional, TypeVar, Generic, List, Tuple, Iterator

K = TypeVar('K')  # Key type (must be comparable)
V = TypeVar('V')  # Value type

class TreeNode(Generic[K, V]):
    """Node for a generic binary search tree."""
    def __init__(self, key: K, value: V):
        self.key: K = key
        self.value: V = value
        self.left: Optional['TreeNode[K, V]'] = None
        self.right: Optional['TreeNode[K, V]'] = None
        self.height: int = 1  # For AVL balancing (future use)

class BinarySearchTree(Generic[K, V]):
    """
    Generic BST for maintaining sorted data with O(log n) operations.
    Supports insertion, search, range queries, and in-order traversal.
    """
    def __init__(self):
        self.root: Optional[TreeNode[K, V]] = None
        self._size: int = 0

    def insert(self, key: K, value: V) -> None:
        """Insert or update a key-value pair."""
        self.root, inserted = self._insert_recursive(self.root, key, value)
        if inserted:
            self._size += 1

    def _insert_recursive(self, node: Optional[TreeNode[K, V]], key: K, value: V) -> Tuple[Optional[TreeNode[K, V]], bool]:
        if node is None:
            return TreeNode(key, value), True
        if key < node.key:
            node.left, inserted = self._insert_recursive(node.left, key, value)
        elif key > node.key:
            node.right, inserted = self._insert_recursive(node.right, key, value)
        else:
            node.value = value
            return node, False
        node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))
        return node, inserted

    def _get_height(self, node: Optional[TreeNode[K, V]]) -> int:
        return node.height if node else 0

    def search(self, key: K) -> Optional[V]:
        """Search for a key and return its value, or None if not found."""
        node = self._search_recursive(self.root, key)
        return node.value if node else None

    def _search_recursive(self, node: Optional[TreeNode[K, V]], key: K) -> Optional[TreeNode[K, V]]:
        if node is None:
            return None
        if key == node.key:
            return node
        elif key < node.key:
            return self._search_recursive(node.left, key)
        else:
            return self._search_recursive(node.right, key)

    def __contains__(self, key: K) -> bool:
        return self.search(key) is not None

    def __len__(self) -> int:
        return self._size

    def inorder(self) -> List[Tuple[K, V]]:
        """Return all key-value pairs in sorted order."""
        result: List[Tuple[K, V]] = []
        self._inorder_recursive(self.root, result)
        return result

    def _inorder_recursive(self, node: Optional[TreeNode[K, V]], result: List[Tuple[K, V]]):
        if node:
            self._inorder_recursive(node.left, result)
            result.append((node.key, node.value))
            self._inorder_recursive(node.right, result)

    def __iter__(self) -> Iterator[Tuple[K, V]]:
        return iter(self.inorder())

    def range_query(self, start_key: K, end_key: K) -> List[Tuple[K, V]]:
        """
        Find all key-value pairs in range [start_key, end_key].
        Efficient for time-based queries, price ranges, or date filtering.
        """
        result: List[Tuple[K, V]] = []
        self._range_query_recursive(self.root, start_key, end_key, result)
        return result

    def _range_query_recursive(self, node: Optional[TreeNode[K, V]], start: K, end: K, result: List[Tuple[K, V]]):
        if node is None:
            return
        if start <= node.key <= end:
            result.append((node.key, node.value))
        if node.key > start:
            self._range_query_recursive(node.left, start, end, result)
        if node.key < end:
            self._range_query_recursive(node.right, start, end, result)