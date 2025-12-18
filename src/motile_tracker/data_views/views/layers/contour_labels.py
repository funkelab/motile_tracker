from __future__ import annotations

import napari
import numpy as np
from napari.layers.labels._labels_utils import (
    expand_slice,
)
from napari.utils import DirectLabelColormap
from napari.utils.events import Event
from scipy import ndimage as ndi


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
