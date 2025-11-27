from __future__ import annotations

from psygnal import Signal
from qtpy.QtCore import QObject


class NodeSelectionList(QObject):
    """Efficient selection list for nodes with signals on updates."""

    list_updated = Signal()

    def __init__(self):
        super().__init__()
        self._set = set()  # Use a set for O(1) membership
        self._prev_set = set()

    def add(self, item, append: bool | None = False):
        """Append or replace an item to the list, depending on the number of items
        present and the keyboard modifiers used. Emit update signal"""
        self._prev_set = self._set.copy()

        if item in self._set:
            self._set.remove(item)
        elif append:
            self._set.add(item)
        else:
            self._set = {item}

        self.list_updated.emit()

    def add_list(self, items: list, append: bool | None = False):
        """Add multiple items to the selection."""
        self._prev_set = self._set.copy()

        items_set = set(items)
        if append:
            # Remove items already present, add the rest
            self._set.symmetric_difference_update(items_set)
        else:
            self._set = items_set

        self.list_updated.emit()

    def reset(self):
        """Clear all elements in the set"""
        self._prev_set = self._set.copy()
        self._set.clear()
        self.list_updated.emit()

    def restore(self):
        """Restore the previous set of nodes"""
        self._set = self._prev_set.copy()
        self.list_updated.emit()

    def __contains__(self, item):
        return item in self._set

    def __len__(self):
        return len(self._set)

    def __iter__(self):
        return iter(self._set)

    def __getitem__(self, index):
        """Convert to list on demand for indexing"""
        return list(self._set)[index]

    @property
    def as_list(self) -> list:
        """Return the selected nodes as a list (arbitrary order)."""
        return list(self._set)
