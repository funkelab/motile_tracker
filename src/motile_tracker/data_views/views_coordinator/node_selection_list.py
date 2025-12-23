from __future__ import annotations

from psygnal import Signal
from qtpy.QtCore import QObject


class NodeSelectionList(QObject):
    """Efficient selection list for nodes with signals on updates,
    with support for iterating through the selection."""

    list_updated = Signal()

    def __init__(self):
        super().__init__()
        self._set = set()  # Use a set for O(1) membership
        self._prev_set = set()
        self._iter_index = 0  # Track position for "next/previous node"

    def _reset_iterator(self) -> None:
        """Reset iteration pointer whenever selection changes."""
        self._iter_index = 0

    def add(self, item: int, append: bool = False) -> None:
        """Append or replace an item in the selection.

        Args:
            item: The node ID to add or toggle.
            append: If True, add to existing selection (or remove if already present).
                If False, replace selection with just this item.
        """
        self._prev_set = self._set.copy()
        if item in self._set:
            self._set.remove(item)
        elif append:
            self._set.add(item)
        else:
            self._set = {item}
        self._reset_iterator()
        self.list_updated.emit()

    def add_list(self, items: list[int], append: bool = False) -> None:
        """Add multiple items to the selection.

        Args:
            items: List of node IDs to add.
            append: If True, toggle items in existing selection.
                If False, replace selection with these items.
        """
        self._prev_set = self._set.copy()
        items_set = set(items)
        if append:
            self._set.symmetric_difference_update(items_set)
        else:
            self._set = items_set
        self._reset_iterator()
        self.list_updated.emit()

    def reset(self) -> None:
        """Clear all elements from the selection."""
        self._prev_set = self._set.copy()
        self._set.clear()
        self._reset_iterator()
        self.list_updated.emit()

    def restore(self) -> None:
        """Restore the previous selection."""
        self._set = self._prev_set.copy()
        self._reset_iterator()
        self.list_updated.emit()

    def __contains__(self, item: int) -> bool:
        return item in self._set

    def __len__(self) -> int:
        return len(self._set)

    def __iter__(self):
        return iter(self._set)

    def __getitem__(self, index: int) -> int:
        """Convert to list on demand for indexing."""
        return list(self._set)[index]

    @property
    def as_list(self) -> list[int]:
        """Return the selected nodes as a list (arbitrary order)."""
        return list(self._set)

    def next_node(self, forward: bool = True) -> int | None:
        """Advance/regress the pointer and return the next/previous node.

        Args:
            forward: If True, move to next node; if False, move to previous.

        Returns:
            The node ID, or None if selection is empty.
        """
        nodes = sorted(self._set)
        if not nodes:
            return None
        if forward:
            self._iter_index = (self._iter_index + 1) % len(nodes)
        else:
            self._iter_index = (self._iter_index - 1) % len(nodes)
        return nodes[self._iter_index]
