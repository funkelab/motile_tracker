import zarr
from qtpy.QtWidgets import (
    QLayout,
)


def find_geff_group(group: zarr.Group) -> zarr.Group | None:
    """Recursively search for a Zarr group with 'geff' in its .zattrs.
    Args:
        group (zarr.Group): The Zarr group to search within.
    Returns:
        zarr.Group | None: The first group found with 'geff' in its .zattrs, or None if
        not found.
    """

    if "geff" in group.attrs:
        return group

    for key in group.group_keys():
        subgroup = group[key]
        if isinstance(subgroup, zarr.Group):
            found = find_geff_group(subgroup)
            if found:
                return found
    return None


def clear_layout(layout: QLayout) -> None:
    """Recursively clear all widgets and layouts in a QLayout.
    Args:
        layout (QLayout): The layout to clear.
    """
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
        # If the item is a layout itself, clear it recursively
        elif item.layout() is not None:
            clear_layout(item.layout())
