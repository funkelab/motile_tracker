from __future__ import annotations

from psygnal import Signal
from qtpy.QtCore import QObject


class NodeSelectionHistory(QObject):
    """History-aware selection list for nodes with signals on updates.

    Records each unique set of selected nodes and allows navigating backwards/forwards
    through the selection history.
    """

    list_updated = Signal()

    def __init__(self):
        super().__init__()
        self._history: list[set[int]] = [
            set()
        ]  # History of selection states (can include empty sets)
        self._pointer = 0  # Track position in history for sets of nodes
        self._iter_index = (
            0  # Track position for "next/previous node" (within selection) navigation
        )
        self._filtered_set: set[int] | None = (
            None  # Filtered view of current selection, if filtering is active (triggered by tracks_viewer, to filter out deleted nodes)
        )
        self._prev_set: set[int] = set()  # Previous selection for restore functionality

    def _reset_iterator(self) -> None:
        """Reset iteration pointer whenever selection changes."""
        self._iter_index = 0

    def _add_to_history(self, new_set: set[int]) -> None:
        """Add a new selection state to history if it is different from current.

        Args:
            new_set: The new selection set to potentially add to history (can be empty).
        """
        current = self._history[self._pointer]
        if new_set == current:
            return

        # If not at the end of history, truncate the redo stack
        if self._pointer < len(self._history) - 1:
            self._history = self._history[: self._pointer + 1]

        # Add the new set to history and update pointer
        self._history.append(new_set.copy())
        self._pointer = len(self._history) - 1

    @property
    def _current(self) -> set[int]:
        """Get the current selection set. Priority: filtered > history."""
        if self._filtered_set is not None:
            return self._filtered_set
        return self._history[self._pointer]

    def add(self, item: int, append: bool = False) -> None:
        """Append or replace an item in the selection.

        Args:
            item: The node ID to add or toggle.
            append: If True, add to existing selection (or remove if already present).
                If False, replace selection with just this item.
        """
        self._filtered_set = None  # Clear any active filter
        current = self._current.copy()
        if current:  # Only store non-empty previous selections
            self._prev_set = current
        new_set = current.copy()
        if item in new_set:
            new_set.remove(item)
        elif append:
            new_set.add(item)
        else:
            new_set = {item}

        self._add_to_history(new_set)
        self._reset_iterator()
        self.list_updated.emit()

    def add_list(self, items: list[int], append: bool = False) -> None:
        """Add multiple items to the selection.

        Args:
            items: List of node IDs to add.
            append: If True, toggle items in existing selection.
                If False, replace selection with these items.
        """
        self._filtered_set = None  # Clear any active filter
        current = self._current.copy()
        if current:  # Only store non-empty previous selections
            self._prev_set = current
        new_set = current.copy()
        items_set = set(items)
        if append:
            new_set.symmetric_difference_update(items_set)
        else:
            new_set = items_set.copy()

        self._add_to_history(new_set)
        self._reset_iterator()
        self.list_updated.emit()

    def reset(self) -> None:
        """Clear all elements from the selection without adding empty sets to restore."""
        self._filtered_set = None  # Clear any active filter
        current = self._current.copy()
        if current:  # Only store non-empty previous selections
            self._prev_set = current
        self._add_to_history(set())  # Add empty set to history
        self._reset_iterator()
        self.list_updated.emit()

    def restore(self) -> None:
        """Restore the previous selection, independent of where you are in history."""

        prev_set = self._current.copy()
        self._add_to_history(self._prev_set.copy())
        self._prev_set = prev_set
        self._filtered_set = None
        self._reset_iterator()
        self.list_updated.emit()

    def filter(self, valid_items: set[int]) -> None:
        """Silently filter the current selection to only keep items that are in valid_items,
        without modifying the history.

        Creates a filtered view of the current selection that persists until the next
        navigation, keeping the history intact, so that nodes that are put back via 'undo'
        actions can also be selected again.

        Args:
            valid_items: Set of existing node IDs.
        """
        unfiltered = self._history[self._pointer]
        self._filtered_set = unfiltered & valid_items  # Store the filtered view
        self._reset_iterator()

    def select_node_set_from_history(self, previous: bool) -> None:
        """Move forwards or backwards in selection history, skipping empty selections."""

        prev_set = self._current.copy()
        if previous and self._pointer > 0:
            self._pointer -= 1
            while (
                self._pointer > 0 and not self._history[self._pointer]
            ):  # Skip empty sets when navigating
                self._pointer -= 1
        elif not previous and self._pointer < len(self._history) - 1:
            self._pointer += 1
            while (
                self._pointer < len(self._history) - 1
                and not self._history[self._pointer]
            ):
                self._pointer += 1
        else:
            return

        self._filtered_set = None
        self._prev_set = (
            prev_set if prev_set else self._history[self._pointer]
        )  # only store non-empty sets as prev_set
        self._reset_iterator()
        self.list_updated.emit()

    def __contains__(self, item: int) -> bool:
        return item in self._current

    def __len__(self) -> int:
        return len(self._current)

    def __iter__(self):
        return iter(self._current)

    def __getitem__(self, index: int) -> int:
        """Convert to list on demand for indexing."""
        return list(self._current)[index]

    @property
    def as_list(self) -> list[int]:
        """Return the selected nodes as a list (arbitrary order)."""
        return list(self._current)

    def next_node(self, forward: bool = True) -> int | None:
        """Advance/regress the pointer and return the next/previous node.

        Args:
            forward: If True, move to next node; if False, move to previous.

        Returns:
            The node ID, or None if selection is empty.
        """
        nodes = sorted(self._current)
        if not nodes:
            return None
        if forward:
            self._iter_index = (self._iter_index + 1) % len(nodes)
        else:
            self._iter_index = (self._iter_index - 1) % len(nodes)
        return nodes[self._iter_index]
