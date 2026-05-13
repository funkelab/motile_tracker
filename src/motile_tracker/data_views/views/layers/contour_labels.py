from __future__ import annotations

import napari
import numpy as np
from napari.layers.labels._labels_constants import (
    Mode,
)
from napari.layers.labels._labels_mouse_bindings import draw, pick
from napari.layers.labels._labels_utils import (
    expand_slice,
    indices_in_shape,
)
from napari.layers.labels.labels import _coerce_indices_for_vectorization
from napari.utils import DirectLabelColormap
from napari.utils._indexing import elements_in_slice, index_in_slice
from napari.utils.events import Event
from scipy import ndimage as ndi


def left_only_draw(layer, event):
    if event.button != 1:
        return  # skip non‑left
    yield from draw(layer, event)


def left_only_pick(layer, event):
    if event.button != 1:
        return
    pick(layer, event)


def get_contours(
    labels: np.ndarray,
    thickness: int,
    background_label: int,
    filled_labels: list[int] | None = None,
):
    """Computes the contours of a 2D label image.

    Parameters
    ----------
    labels : array of integers
        An input labels image.
    thickness : int
        It controls the thickness of the inner boundaries. The outside thickness is always 1.
        The final thickness of the contours will be `thickness + 1`.
    background_label : int
        That label is used to fill everything outside the boundaries.

    Returns
    -------
    A new label image in which only the boundaries of the input image are kept.
    """
    struct_elem = ndi.generate_binary_structure(labels.ndim, 1)

    thick_struct_elem = ndi.iterate_structure(struct_elem, thickness).astype(bool)

    dilated_labels = ndi.grey_dilation(labels, footprint=struct_elem)
    eroded_labels = ndi.grey_erosion(labels, footprint=thick_struct_elem)
    not_boundaries = dilated_labels == eroded_labels

    contours = labels.copy()
    contours[not_boundaries] = background_label

    # instead of filling with background label, fill the group label with their normal color
    if filled_labels is not None and len(filled_labels) > 0:
        group_mask = np.isin(labels, filled_labels)
        combined_mask = not_boundaries & group_mask
        contours = np.where(combined_mask, labels, contours)

    return contours


class ContourLabels(napari.layers.Labels):
    """Extended labels layer that allows to show contours and filled labels simultaneously"""

    @property
    def _type_string(self) -> str:
        return "labels"  # to make sure that the layer is treated as labels layer for saving

    def __init__(
        self,
        data: np.array,
        name: str,
        opacity: float,
        scale: tuple,
        colormap: DirectLabelColormap,
    ):
        super().__init__(
            data=data,
            name=name,
            opacity=opacity,
            scale=scale,
            colormap=colormap,
        )

        self._filled_labels = []
        self.events.add(filled_labels=Event)
        self._drag_modes[Mode.PAINT] = left_only_draw
        self._drag_modes[Mode.FILL] = left_only_draw
        self._drag_modes[Mode.ERASE] = left_only_draw
        self._drag_modes[Mode.PICK] = left_only_pick

    @property
    def filled_labels(self) -> list[int] | None:
        """List of labels in a group"""
        return self._filled_labels

    @filled_labels.setter
    def filled_labels(self, filled_labels: list[int] | None = None) -> None:
        self._filled_labels = filled_labels
        self.events.filled_labels()

    def _calculate_contour(
        self, labels: np.ndarray, data_slice: tuple[slice, ...]
    ) -> np.ndarray | None:
        """Calculate the contour of a given label array within the specified data slice.

        Parameters
        ----------
        labels : np.ndarray
            The label array.
        data_slice : Tuple[slice, ...]
            The slice of the label array on which to calculate the contour.

        Returns
        -------
        Optional[np.ndarray]
            The calculated contour as a boolean mask array.
            Returns None if the contour parameter is less than 1,
            or if the label array has more than 2 dimensions.
        """

        if self.contour < 1:
            return None
        if labels.ndim > 2:
            return None

        expanded_slice = expand_slice(data_slice, labels.shape, 1)
        sliced_labels = get_contours(
            labels[expanded_slice],
            self.contour,
            self.colormap.background_value,
            self.filled_labels,
        )

        # Remove the latest one-pixel border from the result
        delta_slice = tuple(
            slice(s1.start - s2.start, s1.stop - s2.start)
            for s1, s2 in zip(data_slice, expanded_slice, strict=False)
        )
        return sliced_labels[delta_slice]

    def set_opacity(
        self,
        labels: list[int],
        value: float,
    ) -> None:
        """Helper function to set the opacity of multiple labels to the same value.
        Args:
            labels (list[int]): list of labels to set the value for.
            value (float): float alpha value to set.
        """

        color_dict = self.colormap.color_dict
        for label in labels:
            if label is None or label == 0:
                continue
            color = color_dict.get(label)
            if color is not None:
                color[3] = value

    def refresh_colormap(self):
        """Refresh the label colormap by setting its dictionary"""

        self.colormap = DirectLabelColormap(color_dict=self.colormap.color_dict)

    def _paint_indices(
        self,
        mask_indices,
        new_label,
        shape,
        dims_to_paint,
        slice_coord=None,
        refresh=True,
    ):
        """Paint variant that supports read-only data (e.g. GraphArrayView).

        Only diverges from napari's default for the one case it can't handle:
        a read-only array with `preserve_labels=True`, where the upstream
        path does fancy indexing (`self.data[slice_coord]`) that tracksdata's
        lazy view doesn't support. In that case we materialize per-time-frame
        via `_read_old_values`. All other cases delegate to super.
        """
        if hasattr(self.data, "__setitem__") or not self.preserve_labels:
            return super()._paint_indices(
                mask_indices, new_label, shape, dims_to_paint, slice_coord, refresh
            )

        # Read-only + preserve_labels: mirror napari's setup, then build
        # keep_coords from materialized frame values instead of fancy-indexing
        # self.data.
        dims_not_painted = sorted(self._slice_input.order[: -self.n_edit_dimensions])
        mask_indices = indices_in_shape(mask_indices, shape)

        slice_coord_temp = list(mask_indices.T)
        if self.n_edit_dimensions < self.ndim:
            for j, i in enumerate(dims_to_paint):
                slice_coord[i] = slice_coord_temp[j]
            for i in dims_not_painted:
                slice_coord[i] = slice_coord[i] * np.ones(
                    mask_indices.shape[0], dtype=int
                )
        else:
            slice_coord = slice_coord_temp

        slice_coord = _coerce_indices_for_vectorization(self.data, slice_coord)

        current_values = self._read_old_values(slice_coord)
        if new_label == self.colormap.background_value:
            keep_coords = current_values == (
                self._prev_selected_label
                if self._prev_selected_label
                else self.selected_label
            )
        else:
            keep_coords = current_values == self.colormap.background_value
        slice_coord = tuple(sc[keep_coords] for sc in slice_coord)

        self.data_setitem(slice_coord, new_label, refresh)

    def data_setitem(self, indices, value, refresh=True):
        """Override to handle read-only data (e.g. GraphArrayView).

        When the underlying data does not support __setitem__ (read-only),
        accumulate paint atoms during a drag (respecting napari's block_history
        mechanism) and only fire events.paint once when the drag completes.
        For writable arrays (numpy), fall back to the default implementation.
        """
        if not hasattr(self.data, "__setitem__"):
            old_values = self._read_old_values(indices)
            atom = (indices, old_values, value)
            if self._block_history:
                # During a drag, accumulate atoms; events.paint fires once on release
                self._staged_history.append(atom)
                # Update the display buffer directly for live visual feedback,
                # without going through UserUpdateSegmentation.
                pt_not_disp = self._get_pt_not_disp()
                displayed_indices = index_in_slice(
                    indices, pt_not_disp, self._slice.slice_input.order
                )
                if isinstance(value, np.ndarray):
                    visible_values = value[elements_in_slice(indices, pt_not_disp)]
                elif isinstance(value, np.integer):
                    visible_values = value
                else:
                    visible_values = np.intp(value)
                self._slice.image.raw[displayed_indices] = visible_values
                if any(len(ax) == 0 for ax in indices):
                    return
                updated_slice = tuple(
                    slice(int(min(ax)), int(max(ax)) + 1) for ax in indices
                )
                if self.contour > 0:
                    updated_slice = expand_slice(updated_slice, self.data.shape, 1)
                else:
                    # For no-contour mode, _partial_labels_refresh reads from
                    # _slice.image.view, so we must update it here too.
                    self._slice.image.view[displayed_indices] = (
                        self.colormap._data_to_texture(visible_values)
                    )
                if self._updated_slice is None:
                    self._updated_slice = updated_slice
                else:
                    self._updated_slice = tuple(
                        slice(min(s1.start, s2.start), max(s1.stop, s2.stop))
                        for s1, s2 in zip(
                            updated_slice, self._updated_slice, strict=False
                        )
                    )
                if refresh:
                    self._partial_labels_refresh()
            else:
                # Single-click or fill operation: fire immediately
                self.events.paint(value=[atom])
            return
        super().data_setitem(indices, value, refresh)

    def undo(self):
        """Override undo for read-only data (e.g. GraphArrayView).

        napari's default Labels.undo() calls data_setitem() to restore old
        values. For read-only data, ContourLabels.data_setitem() cannot write
        to the underlying array and instead fires events.paint as a signal for
        upstream code to handle the change. Firing events.paint during an undo
        triggers the same paint-event callbacks that initiated the undo in the
        first place, causing a recursive loop and a TypeError.

        This override breaks the loop by restoring the display buffer directly
        from the undo history atoms, without going through data_setitem or
        emitting any paint event.

        This method is called (via super().undo()) from TrackLabels in three
        situations: reverting a failed paint on the main layer, reverting a
        failed paint on an ortho-view copy of the layer, and rolling back an
        invalid action inside _on_paint error handling.
        """
        if not hasattr(self.data, "__setitem__"):
            if not self._undo_history:
                return
            item = self._undo_history.pop()
            self._redo_history.append(item)
            pt_not_disp = self._get_pt_not_disp()
            for indices, old_values, _new_value in item:
                displayed_indices = index_in_slice(
                    indices, pt_not_disp, self._slice.slice_input.order
                )
                if isinstance(old_values, np.ndarray):
                    vis_vals = old_values[elements_in_slice(indices, pt_not_disp)]
                else:
                    vis_vals = np.intp(old_values)
                self._slice.image.raw[displayed_indices] = vis_vals
            self.refresh()
        else:
            super().undo()

    def _read_old_values(self, indices):
        """Read current values at indices from a read-only array,
        materializing one timepoint at a time (the only supported access pattern)."""
        t_indices = indices[0]
        spatial_indices = indices[1:]
        old_values = np.zeros(len(t_indices), dtype=np.int64)
        for t in np.unique(t_indices):
            mask = t_indices == t
            frame = np.asarray(self.data[int(t)])
            old_values[mask] = frame[tuple(s[mask] for s in spatial_indices)]
        return old_values
